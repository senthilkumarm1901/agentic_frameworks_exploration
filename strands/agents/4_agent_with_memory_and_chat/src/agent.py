"""Strands agent with MCP tools, skills, and conversation memory — Pattern 4.

Key additions over Pattern 3:
- Short-term memory: full message history held by the Strands Agent across
  chat turns within a session (the Agent object is reused, so the Strands
  conversation_manager accumulates messages automatically).
- Long-term memory: after every turn the conversation is summarised by the
  LLM and persisted to memory_store/session.json, so it survives restarts.
- The frozen summary is injected into the system prompt at session start.

Strands note on short-term memory:
  Strands Agent objects accumulate conversation history internally via their
  ConversationManager.  Reusing the same Agent instance across turns gives us
  short-term (in-session) memory without any external checkpointer.  This is
  the Strands equivalent of LangGraph's MemorySaver + thread_id.
"""

import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any

# Suppress gRPC keepalive ping noise from the long-lived Milvus Lite connection.
# Pattern 4 keeps MCPClient open for the whole session; idle periods between
# turns cause gRPC to send keepalive pings, triggering ENHANCE_YOUR_CALM /
# too_many_pings from Milvus Lite's embedded gRPC server.  Setting NONE here
# propagates to the MCP stdio subprocess via inherited environment.
os.environ.setdefault("GRPC_VERBOSITY", "NONE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")

from mcp.client.stdio import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models.ollama import OllamaModel
from strands.tools.mcp.mcp_client import MCPClient

from .chat_ui import print_skill_activation, print_tool_call, print_tool_result, clear_thinking
from .memory import (
    build_summarization_prompt,
    format_memory_block,
    load_summary,
    save_summary,
)
from .prompts import build_system_prompt


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"
        if candidate.exists():
            return parent
    raise FileNotFoundError("Could not locate _shared/src/mcp_servers/pattern2_server.py")


_PROJECT_ROOT = _find_project_root()
_MCP_SERVER_PATH = _PROJECT_ROOT / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"
_SKILLS_DIR = _PROJECT_ROOT / "_shared" / "skills"


@tool
def activate_skill(skill_name: str) -> str:
    """
    Load full instructions for a skill by name.

    Available skills:
    - country-comparison: Compare countries across metrics
    - country-profile: Build comprehensive country brief
    - regional-analysis: Analyze regional patterns and aggregates
    - report-formatting: Format results as professional report

    Args:
        skill_name: Name of the skill to activate (e.g., 'country-comparison')

    Returns:
        Full skill methodology instructions to follow
    """
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        available = [d.name for d in _SKILLS_DIR.iterdir() if d.is_dir()]
        return f"Skill '{skill_name}' not found. Available: {available}"
    print_skill_activation(skill_name)
    return skill_path.read_text(encoding="utf-8")


def _build_ollama_model() -> OllamaModel:
    model_id = os.environ.get("OLLAMA_MODEL", "qwen3.5:35b-a3b-coding-nvfp4")
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


# ──────────────────────────────────────────────
# Session-level state (created once per process)
# ──────────────────────────────────────────────

class ChatSession:
    """Holds the Strands Agent and session state for the interactive chat loop.

    The Agent is created once and reused across turns so that Strands'
    ConversationManager accumulates the full message history (short-term memory).
    """

    def __init__(self):
        self.model: OllamaModel | None = None
        self.agent: Agent | None = None
        self.mcp_client: MCPClient | None = None
        self.turn_count: int = 0
        # In-session exchange list for long-term summarisation
        self._exchanges: list[tuple[str, str]] = []

    def initialize(self) -> None:
        """Build the Strands Agent with memory-injected system prompt."""
        summary_data = load_summary()
        self.turn_count = summary_data.get("turn_count", 0)
        memory_block = format_memory_block(summary_data)
        system_prompt = build_system_prompt(memory_block)

        self.model = _build_ollama_model()
        self.mcp_client = _build_mcp_client()

        # Enter MCP context — the client manages stdio process lifetime
        self.mcp_client.__enter__()
        mcp_tools = self.mcp_client.list_tools_sync()
        all_tools = mcp_tools + [activate_skill]

        self.agent = Agent(
            model=self.model,
            tools=all_tools,
            system_prompt=system_prompt,
            callback_handler=None,
        )

    def reinitialize(self) -> None:
        """Rebuild agent after a memory clear (--reset or 'clear' command)."""
        if self.mcp_client is not None:
            try:
                self.mcp_client.__exit__(None, None, None)
            except Exception:
                pass
        self._exchanges = []
        self.initialize()

    def close(self) -> None:
        """Clean up MCP client."""
        if self.mcp_client is not None:
            try:
                self.mcp_client.__exit__(None, None, None)
            except Exception:
                pass


# ──────────────────────────────────────────────
# Metrics helpers (shared with Pattern 3)
# ──────────────────────────────────────────────

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
            details.append({"name": tool_name, "args": tool_use_args.get(tool_use_id, {}), "result": result_text[:200]})
    return details


# ──────────────────────────────────────────────
# Chat turn execution
# ──────────────────────────────────────────────

def run_chat_turn(
    session: ChatSession,
    user_query: str,
) -> dict:
    """Run a single chat turn and return metrics.

    The session's Agent object is reused so Strands accumulates the full
    conversation history (short-term memory).

    After each turn the conversation so far is summarised and persisted to
    disk (long-term memory).
    """
    assert session.agent is not None, "ChatSession must be initialized before use"

    start_time = time.perf_counter()
    result = session.agent(user_query)
    duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))

    clear_thinking()

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
        tool_calls_detail = [{"name": n, "args": {}, "result": ""} for n in tools_used]

    skill_activations = tools_used.count("activate_skill")
    answer = _extract_answer(result)

    # Display real-time tool calls (skip activate_skill — already shown)
    for tc in tool_calls_detail:
        if tc["name"] != "activate_skill":
            print_tool_call(tc["name"], tc.get("args", {}))
            if tc.get("result"):
                print_tool_result(tc["name"], tc["result"])

    # Accumulate exchange for long-term memory
    session._exchanges.append((user_query, answer))

    # Build and persist long-term summary
    try:
        summarization_prompt = build_summarization_prompt(session._exchanges)
        summary_result = session.model(summarization_prompt)
        summary_text = _extract_answer(summary_result)
        save_summary(summary_text, session.turn_count)
    except Exception:
        pass  # Don't fail the turn on summarisation errors

    return {
        "answer": answer,
        "framework": "strands",
        "pattern": "agent_with_memory_and_chat",
        "turn_count": session.turn_count,
        "llm_calls": llm_calls,
        "total_duration_ms": duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "tool_calls": total_tool_calls,
        "skill_activations": skill_activations,
        "tools_used": tools_used,
        "status": "success",
    }
