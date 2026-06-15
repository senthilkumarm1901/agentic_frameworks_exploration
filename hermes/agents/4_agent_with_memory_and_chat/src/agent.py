"""Hermes-style ReAct agent with MCP tools, skills, and session memory."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI

from .chat_ui import clear_thinking, print_skill_activation, print_tool_call, print_tool_result
from .memory import build_summarization_prompt, format_memory_block, load_summary, save_summary
from .prompts import SYSTEM_PROMPT
from .skill_tools import activate_skill, build_activate_skill_tool, format_activate_skill_result


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"
        if candidate.exists():
            return parent
    raise FileNotFoundError("Could not locate _shared/src/mcp_servers/pattern2_server.py")


_PROJECT_ROOT = _find_project_root()
_MCP_SERVER_PATH = _PROJECT_ROOT / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"


class HermesAgent:
    """Hermes-pattern ReAct agent with memory-aware chat state."""

    def __init__(
        self,
        model: str | None = None,
        quiet_mode: bool = False,
        ephemeral_system_prompt: str | None = None,
        max_iterations: int = 10,
        skip_memory: bool = True,
        skip_context_files: bool = True,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model = model or os.environ.get("OLLAMA_MODEL", "hermes3:latest")
        self.quiet_mode = quiet_mode
        self.system_prompt_template = ephemeral_system_prompt or SYSTEM_PROMPT
        self.max_iterations = max_iterations
        self.skip_memory = skip_memory
        self.skip_context_files = skip_context_files

        ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = OpenAI(
            base_url=base_url or f"{ollama_base}/v1",
            api_key=api_key or "ollama",
        )

        self.turn_count = 0
        self.messages: list[dict[str, Any]] = []
        self._exchanges: list[tuple[str, str]] = []
        self._summary_data = load_summary()
        self._stdio_cm = None
        self._mcp_session_cm = None
        self._session: ClientSession | None = None
        self._openai_tools: list[dict[str, Any]] = []
        self._initialized = False

    def chat(self, message: str) -> str:
        result = self.run_conversation(user_message=message)
        return result["final_response"]

    def run_conversation(
        self,
        user_message: str,
        system_message: str | None = None,
        task_id: str | None = None,
    ) -> dict:
        return asyncio.run(self._run_turn(user_message=user_message, system_message=system_message, task_id=task_id))

    async def initialize(self) -> None:
        if self._initialized:
            return

        memory_block = format_memory_block(self._summary_data)
        system_prompt = self.system_prompt_template.format(memory_block=memory_block)
        self.messages = [{"role": "system", "content": system_prompt}]
        self.turn_count = int(self._summary_data.get("turn_count", 0) or 0)
        self._exchanges = []

        self._stdio_cm = stdio_client(
            StdioServerParameters(command=sys.executable, args=[str(_MCP_SERVER_PATH)])
        )
        read, write = await self._stdio_cm.__aenter__()
        self._mcp_session_cm = ClientSession(read, write)
        self._session = await self._mcp_session_cm.__aenter__()
        await self._session.initialize()

        mcp_tools = (await self._session.list_tools()).tools
        self._openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools
        ]
        self._openai_tools.append(build_activate_skill_tool())
        self._initialized = True

    async def close(self) -> None:
        if self._mcp_session_cm is not None:
            try:
                await self._mcp_session_cm.__aexit__(None, None, None)
            finally:
                self._mcp_session_cm = None
                self._session = None
        if self._stdio_cm is not None:
            try:
                await self._stdio_cm.__aexit__(None, None, None)
            finally:
                self._stdio_cm = None
        self._initialized = False

    async def reinitialize(self) -> None:
        await self.close()
        self._summary_data = load_summary()
        await self.initialize()

    async def _run_turn(self, user_message: str, system_message: str | None, task_id: str | None) -> dict:
        if not self._initialized:
            await self.initialize()

        assert self._session is not None, "HermesAgent must be initialized before use"

        if system_message is not None:
            self.messages[0]["content"] = system_message

        start = time.perf_counter()
        self.turn_count += 1
        self.messages.append({"role": "user", "content": user_message})

        llm_calls = 0
        prompt_tokens = 0
        completion_tokens = 0
        final_response = ""
        tool_calls_detail: list[dict[str, Any]] = []
        skill_activations = 0
        tools_used: list[str] = []

        for _ in range(self.max_iterations):
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self._openai_tools,
            )
            llm_calls += 1

            if response.usage:
                prompt_tokens += response.usage.prompt_tokens or 0
                completion_tokens += response.usage.completion_tokens or 0

            msg = response.choices[0].message
            final_response = msg.content or ""

            assistant_entry: dict[str, Any] = {"role": "assistant", "content": final_response}
            if msg.tool_calls:
                assistant_entry["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in msg.tool_calls
                ]
            self.messages.append(assistant_entry)

            if not msg.tool_calls:
                break

            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                tools_used.append(fn_name)

                if fn_name == "activate_skill":
                    skill_name = fn_args.get("skill_name", "")
                    print_skill_activation(skill_name)
                    skill_text = activate_skill(skill_name)
                    result_text = format_activate_skill_result(skill_name, skill_text)
                    skill_activations += 1
                else:
                    print_tool_call(fn_name, fn_args)
                    mcp_result = await self._session.call_tool(fn_name, fn_args)
                    result_text = "".join(item.text for item in mcp_result.content if hasattr(item, "text"))
                    print_tool_result(fn_name, result_text[:200])

                tool_calls_detail.append(
                    {
                        "name": fn_name,
                        "args": fn_args,
                        "result": result_text[:200],
                    }
                )

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )

        duration_ms = max(1, int((time.perf_counter() - start) * 1000))
        if not final_response and tool_calls_detail:
            final_response = tool_calls_detail[-1]["result"]

        clear_thinking()

        self._exchanges.append((user_message, final_response))

        try:
            summary_prompt = build_summarization_prompt(self._exchanges)
            summary_response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You summarize conversation history."},
                    {"role": "user", "content": summary_prompt},
                ],
            )
            summary_text = summary_response.choices[0].message.content or ""
            save_summary(summary_text, self.turn_count)
        except Exception:
            pass

        return {
            "final_response": final_response,
            "messages": self.messages,
            "llm_calls": llm_calls,
            "tool_calls": len(tool_calls_detail),
            "tool_calls_detail": tool_calls_detail,
            "skill_activations": skill_activations,
            "tools_used": tools_used,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "total_duration_ms": duration_ms,
            "turn_count": self.turn_count,
            "framework": "hermes",
            "pattern": "agent_with_memory_and_chat",
            "status": "success",
        }
