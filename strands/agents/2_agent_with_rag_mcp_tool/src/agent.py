"""Strands agent with MCP tools for country-data analysis, including RAG search."""

import os
import sys
import time
from pathlib import Path
from typing import Any

from mcp.client.stdio import StdioServerParameters, stdio_client
from strands import Agent
from strands.models.ollama import OllamaModel
from strands.tools.mcp.mcp_client import MCPClient

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


def _build_ollama_model() -> OllamaModel:
    model_id = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    host = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaModel(host=host, model_id=model_id)


def _build_mcp_client() -> MCPClient:
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=[str(_MCP_SERVER_PATH)],
            )
        )
    )


def _extract_tool_usage(summary: dict[str, Any]) -> tuple[int, list[str]]:
    tool_usage = summary.get("tool_usage", {})
    total_tool_calls = 0
    tools_used: list[str] = []
    for tool_name, stats in tool_usage.items():
        execution_stats = stats.get("execution_stats", {}) if isinstance(stats, dict) else {}
        call_count = int(execution_stats.get("call_count", 0) or 0)
        total_tool_calls += call_count
        tools_used.extend([tool_name] * call_count)
    return total_tool_calls, tools_used


def _extract_tool_usage_from_metrics(metrics: Any, summary: dict[str, Any]) -> tuple[int, list[str]]:
    total_tool_calls, tools_used = _extract_tool_usage(summary)
    if total_tool_calls:
        return total_tool_calls, tools_used

    tool_metrics = getattr(metrics, "tool_metrics", {}) or {}
    for tool_name, stats in tool_metrics.items():
        execution_stats = getattr(stats, "execution_stats", None)
        call_count = int(getattr(execution_stats, "call_count", 0) or 0)
        total_tool_calls += call_count
        tools_used.extend([tool_name] * call_count)

    return total_tool_calls, tools_used


def _extract_answer(result: Any) -> str:
    answer = str(result).strip()
    if answer:
        return answer

    message = getattr(result, "message", {}) or {}
    content = message.get("content", []) if isinstance(message, dict) else []
    for item in content:
        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    return ""


def _extract_tool_calls_detail(summary: dict[str, Any]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    tool_use_args: dict[str, dict[str, Any]] = {}

    for trace in summary.get("traces", []) or []:
        for child in trace.get("children", []) or []:
            if not isinstance(child, dict):
                continue
            message = child.get("message", {})
            content = message.get("content", []) if isinstance(message, dict) else []
            for item in content:
                if not isinstance(item, dict):
                    continue
                tool_use = item.get("toolUse", {})
                tool_use_id = tool_use.get("toolUseId") if isinstance(tool_use, dict) else None
                if tool_use_id:
                    tool_use_args[tool_use_id] = tool_use.get("input", {}) or {}

    for trace in summary.get("traces", []) or []:
        for child in trace.get("children", []) or []:
            metadata = child.get("metadata", {}) if isinstance(child, dict) else {}
            tool_name = metadata.get("tool_name")
            if not tool_name:
                continue
            tool_use_id = metadata.get("toolUseId")

            msg = child.get("message", {}) if isinstance(child, dict) else {}
            content = msg.get("content", []) if isinstance(msg, dict) else []
            result_text = ""
            for item in content:
                if not isinstance(item, dict):
                    continue
                tool_result = item.get("toolResult", {})
                tr_content = tool_result.get("content", []) if isinstance(tool_result, dict) else []
                for c_item in tr_content:
                    if isinstance(c_item, dict) and isinstance(c_item.get("text"), str):
                        result_text = c_item["text"]
                        break
                if result_text:
                    break

            details.append(
                {
                    "name": tool_name,
                    "args": tool_use_args.get(tool_use_id, {}),
                    "result": result_text[:200],
                }
            )
    return details


async def run_agent(user_query: str) -> dict:
    """Run the Strands agent against a user query and return metrics payload."""
    model = _build_ollama_model()
    mcp_client = _build_mcp_client()
    start_time = time.perf_counter()

    with mcp_client:
        tools = mcp_client.list_tools_sync()

        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None,
        )

        result = agent(user_query)
        metrics = result.metrics
        summary = metrics.get_summary() if metrics else {}
        total_tool_calls, tools_used = _extract_tool_usage_from_metrics(metrics, summary)

        llm_usage = summary.get("accumulated_usage", {})
        prompt_tokens = int(llm_usage.get("inputTokens", 0) or 0)
        completion_tokens = int(llm_usage.get("outputTokens", 0) or 0)
        llm_calls = int(summary.get("total_cycles", 0) or 0)
        if llm_calls == 0 and metrics is not None:
            llm_calls = len(getattr(metrics, "cycle_durations", []) or [])

        tool_calls_detail = _extract_tool_calls_detail(summary)
        if not tool_calls_detail:
            tool_calls_detail = [{"name": name, "args": {}, "result": ""} for name in tools_used]

        answer = _extract_answer(result)
        if not answer.strip() and tool_calls_detail:
            answer = "; ".join(
                f"{tc['name']}({', '.join(f'{k}={v}' for k, v in tc.get('args', {}).items())}) -> {tc.get('result', '')}"
                for tc in tool_calls_detail
            )

    total_duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
    return {
        "answer": answer,
        "llm_calls": llm_calls,
        "tool_calls": total_tool_calls,
        "tool_calls_detail": tool_calls_detail,
        "total_duration_ms": total_duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
