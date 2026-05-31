"""LangGraph ReAct agent with MCP client for country data tools including RAG.

This module creates a single ReAct agent that connects to the MCP server
via langchain-mcp-adapters, allowing the LLM to call country_lookup,
calculator, and country_kb_search tools through the MCP protocol.

Pattern 2 extends Pattern 1 by adding a RAG-based knowledge base search tool
for qualitative country facts (culture, history, geography, politics).
"""

import os
import sys
import time
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from src.prompts import SYSTEM_PROMPT

def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"
        if candidate.exists():
            return parent
    raise FileNotFoundError("Could not locate _shared/src/mcp_servers/pattern2_server.py")


_PROJECT_ROOT = _find_project_root()
_MCP_SERVER_PATH = str(_PROJECT_ROOT / "_shared" / "src" / "mcp_servers" / "pattern2_server.py")


def _get_llm() -> ChatOllama:
    """Create a ChatOllama instance from environment configuration."""
    model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(model=model, base_url=base_url)


async def run_agent(user_query: str) -> dict:
    """Run the augmented LLM agent against a user query.

    Connects to the MCP server via stdio, creates a ReAct agent, and
    invokes it with the user's question.

    Args:
        user_query: The natural language question to answer.

    Returns:
        Dictionary with keys: answer, llm_calls, tool_calls, total_duration_ms
    """
    llm = _get_llm()
    start_time = time.perf_counter()

    # Connect to MCP server as a subprocess (stdio transport)
    client = MultiServerMCPClient(
        {
            "country-tools": {
                "command": "python",
                "args": [_MCP_SERVER_PATH],
                "transport": "stdio",
            }
        }
    )

    # Get tools from MCP server and create a ReAct agent
    tools = await client.get_tools()
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )

    # Invoke the agent with the user query
    result = await agent.ainvoke({"messages": [("user", user_query)]})

    # Extract metrics from the message history
    messages = result["messages"]
    total_duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Count tool calls and LLM calls from message history
    tool_calls_detail = []  # Detailed tool call info: name, args, result
    pending_tool_calls = {}  # Map tool_call_id -> {name, args}
    llm_calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    ai_contents = []  # Collect all non-empty AI message contents

    for msg in messages:
        # AI messages (LLM responses)
        if msg.type == "ai":
            # Count as LLM call if there's content OR tool calls
            if msg.content or (hasattr(msg, "tool_calls") and msg.tool_calls):
                llm_calls += 1
                # Extract token counts from response_metadata (Ollama format)
                metadata = getattr(msg, "response_metadata", {}) or {}
                prompt_tokens += metadata.get("prompt_eval_count", 0)
                completion_tokens += metadata.get("eval_count", 0)
            # Collect non-empty content for answer extraction
            if msg.content and isinstance(msg.content, str) and msg.content.strip():
                ai_contents.append(msg.content)
            # Track pending tool calls (requests)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    pending_tool_calls[tc["id"]] = {
                        "name": tc["name"],
                        "args": tc["args"],
                    }
                    args_str = ", ".join(f'"{v}"' for v in tc["args"].values())
                    print(f"[TOOL] {tc['name']}({args_str}) requested", file=sys.stderr)

        # Tool messages (tool responses)
        if msg.type == "tool":
            # Extract the result text from the content
            result_text = str(msg.content)
            if isinstance(msg.content, list) and len(msg.content) > 0:
                if isinstance(msg.content[0], dict) and "text" in msg.content[0]:
                    result_text = msg.content[0]["text"]
            
            # Match with pending tool call to get args
            tool_call_id = getattr(msg, "tool_call_id", None)
            tool_info = pending_tool_calls.get(tool_call_id, {})
            
            tool_calls_detail.append({
                "name": msg.name,
                "args": tool_info.get("args", {}),
                "result": result_text[:200],
            })
            print(f"[TOOL] {msg.name} → {result_text}", file=sys.stderr)

    # Get the final answer — prefer the last AI message with content.
    answer = ai_contents[-1] if ai_contents else ""

    # Some model/tool-calling runs can end with empty AI content blocks.
    # In that case, synthesize a final answer from tool outputs.
    if not answer.strip() and tool_calls_detail:
        try:
            tool_summary_lines = []
            for tc in tool_calls_detail:
                args_str = ", ".join(f"{k}={v}" for k, v in tc.get("args", {}).items())
                tool_summary_lines.append(
                    f"- {tc['name']}({args_str}) -> {tc['result']}"
                )

            fallback_prompt = (
                "You are a country data analyst assistant. "
                "Using ONLY the tool outputs below, provide a concise final answer to the user's question. "
                "Include key numbers and the final computed comparison/ratio where relevant.\n\n"
                f"User question: {user_query}\n\n"
                "Tool outputs:\n"
                + "\n".join(tool_summary_lines)
            )
            fallback_resp = await llm.ainvoke(fallback_prompt)
            fallback_text = getattr(fallback_resp, "content", "")
            if isinstance(fallback_text, str) and fallback_text.strip():
                answer = fallback_text.strip()
                llm_calls += 1
                # Capture tokens from fallback call
                fallback_metadata = getattr(fallback_resp, "response_metadata", {}) or {}
                prompt_tokens += fallback_metadata.get("prompt_eval_count", 0)
                completion_tokens += fallback_metadata.get("eval_count", 0)
                print("[INFO] Final answer generated via fallback synthesis", file=sys.stderr)
        except Exception as exc:
            print(f"[WARN] Fallback synthesis failed: {exc}", file=sys.stderr)

    # Last resort: expose tool evidence instead of returning an empty answer.
    if not answer.strip() and tool_calls_detail:
        answer = "; ".join(
            f"{tc['name']} -> {tc['result']}" for tc in tool_calls_detail
        )

    return {
        "answer": answer,
        "llm_calls": llm_calls,
        "tool_calls": len(tool_calls_detail),
        "tool_calls_detail": tool_calls_detail,
        "total_duration_ms": total_duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
