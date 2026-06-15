"""Hermes-style ReAct agent with MCP tools and skills for Pattern 3."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI

from src.prompts import SYSTEM_PROMPT
from src.skill_tools import activate_skill, build_activate_skill_tool, format_activate_skill_result


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
    """Hermes-pattern ReAct agent using Ollama + MCP tools + local skills."""

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
        self.system_prompt = ephemeral_system_prompt or SYSTEM_PROMPT
        self.max_iterations = max_iterations

        ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = OpenAI(
            base_url=base_url or f"{ollama_base}/v1",
            api_key=api_key or "ollama",
        )

    def chat(self, message: str) -> str:
        result = self.run_conversation(user_message=message)
        return result["final_response"]

    def run_conversation(
        self,
        user_message: str,
        system_message: str | None = None,
        task_id: str | None = None,
    ) -> dict:
        import asyncio

        return asyncio.run(self._run_async(user_message, system_message, task_id))

    async def _run_async(
        self,
        user_message: str,
        system_message: str | None,
        task_id: str | None,
    ) -> dict:
        system = system_message or self.system_prompt
        start = time.perf_counter()

        async with stdio_client(
            StdioServerParameters(command=sys.executable, args=[str(_MCP_SERVER_PATH)])
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                mcp_tools = (await session.list_tools()).tools
                openai_tools = [
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
                openai_tools.append(build_activate_skill_tool())

                messages: list[dict] = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ]

                llm_calls = 0
                prompt_tokens = 0
                completion_tokens = 0
                final_response = ""
                tool_calls_detail: list[dict] = []
                skill_activations = 0
                tools_used: list[str] = []
                activated_skill_names: list[str] = []

                for _ in range(self.max_iterations):
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=openai_tools,
                    )
                    llm_calls += 1

                    if response.usage:
                        prompt_tokens += response.usage.prompt_tokens or 0
                        completion_tokens += response.usage.completion_tokens or 0

                    msg = response.choices[0].message
                    final_response = msg.content or ""

                    assistant_entry: dict = {"role": "assistant", "content": final_response}
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
                    messages.append(assistant_entry)

                    if not msg.tool_calls:
                        break

                    for tool_call in msg.tool_calls:
                        fn_name = tool_call.function.name
                        fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                        tools_used.append(fn_name)

                        if fn_name == "activate_skill":
                            skill_name = fn_args.get("skill_name", "")
                            skill_text = activate_skill(skill_name)
                            result_text = format_activate_skill_result(skill_name, skill_text)
                            skill_activations += 1
                            activated_skill_names.append(skill_name)
                        else:
                            mcp_result = await session.call_tool(fn_name, fn_args)
                            result_text = "".join(
                                item.text for item in mcp_result.content if hasattr(item, "text")
                            )

                        tool_calls_detail.append(
                            {
                                "name": fn_name,
                                "args": fn_args,
                                "result": result_text[:200],
                            }
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_text,
                            }
                        )

        duration_ms = max(1, int((time.perf_counter() - start) * 1000))
        if not final_response and tool_calls_detail:
            final_response = tool_calls_detail[-1]["result"]

        return {
            "final_response": final_response,
            "messages": messages,
            "llm_calls": llm_calls,
            "tool_calls": len(tool_calls_detail),
            "skill_activations": skill_activations,
            "tools_used": tools_used,
            "activated_skill_names": activated_skill_names,
            "tool_calls_detail": tool_calls_detail,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "total_duration_ms": duration_ms,
        }