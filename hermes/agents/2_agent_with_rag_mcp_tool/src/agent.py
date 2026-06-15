"""Hermes-style ReAct agent with MCP tools for country-data analysis, including RAG search.

Uses the hermes3 model (via Ollama) with standard OpenAI tool calling.
Connects to pattern2_server.py which exposes:
  - country_lookup_tool  (structured JSON data)
  - calculator_tool      (arithmetic)
  - country_kb_search_tool (semantic RAG over 20 country .md files via Milvus-Lite)

The API mirrors the hermes-agent library's AIAgent interface so switching to
the cloud-backed hermes-agent library later is a one-line import change:

    from run_agent import AIAgent as HermesAgent
"""

import json
import os
import sys
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from openai import OpenAI

from src.prompts import SYSTEM_PROMPT


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
    """Hermes-pattern ReAct agent using Ollama + MCP tools (with RAG).

    Constructor API mirrors hermes-agent's AIAgent so switching to the
    cloud library later is a one-line change::

        from run_agent import AIAgent as HermesAgent
    """

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

    # -------------------------------------------------------------------------
    # Public API matching hermes-agent AIAgent
    # -------------------------------------------------------------------------

    def chat(self, message: str) -> str:
        """One-shot: pass a message, get final text back.

        Mirrors ``AIAgent.chat()`` from the hermes-agent library.
        """
        result = self.run_conversation(user_message=message)
        return result["final_response"]

    def run_conversation(
        self,
        user_message: str,
        system_message: str | None = None,
        task_id: str | None = None,
    ) -> dict:
        """Run the full ReAct loop. Returns ``{final_response, messages, ...}``.

        Mirrors ``AIAgent.run_conversation()`` return structure:
          - final_response   — the agent's final text reply
          - messages         — full message history (system, user, assistant, tool)

        Additional keys carry per-run metrics:
          llm_calls, tool_calls, tool_calls_detail,
          prompt_tokens, completion_tokens, total_tokens, total_duration_ms.
        """
        import asyncio

        return asyncio.run(self._run_async(user_message, system_message))

    # -------------------------------------------------------------------------
    # Internal async ReAct implementation
    # -------------------------------------------------------------------------

    async def _run_async(
        self, user_message: str, system_message: str | None
    ) -> dict:
        system = system_message or self.system_prompt
        start = time.perf_counter()

        # pattern2_server.py must be launched with the same Python that has
        # the RAG dependencies (sentence-transformers, pymilvus) installed.
        # Use sys.executable so the .venv python is used, not a system python.
        async with stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=[str(_MCP_SERVER_PATH)],
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Discover tools from MCP server and map to OpenAI schema
                mcp_tools = (await session.list_tools()).tools
                openai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description or "",
                            "parameters": t.inputSchema,
                        },
                    }
                    for t in mcp_tools
                ]

                messages: list[dict] = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ]

                llm_calls = 0
                tool_calls_detail: list[dict] = []
                prompt_tokens = 0
                completion_tokens = 0
                final_response = ""

                # --- ReAct loop ---
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

                    # Build the assistant entry for history
                    assistant_entry: dict = {"role": "assistant", "content": final_response}
                    if msg.tool_calls:
                        assistant_entry["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ]
                    messages.append(assistant_entry)

                    if not msg.tool_calls:
                        break  # agent finished — no more tool calls

                    # Execute each tool via MCP and feed results back
                    for tc in msg.tool_calls:
                        fn_name = tc.function.name
                        fn_args = (
                            json.loads(tc.function.arguments)
                            if tc.function.arguments
                            else {}
                        )

                        mcp_result = await session.call_tool(fn_name, fn_args)
                        result_text = "".join(
                            item.text
                            for item in mcp_result.content
                            if hasattr(item, "text")
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
                                "tool_call_id": tc.id,
                                "content": result_text,
                            }
                        )

        duration_ms = max(1, int((time.perf_counter() - start) * 1000))
        return {
            "final_response": final_response,
            "messages": messages,
            "llm_calls": llm_calls,
            "tool_calls": len(tool_calls_detail),
            "tool_calls_detail": tool_calls_detail,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "total_duration_ms": duration_ms,
        }
