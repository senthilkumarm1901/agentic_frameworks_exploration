"""LangGraph ReAct agent with MCP tools, skills, and conversation memory.

This module combines:
- MCP tools (country_lookup, calculator, kb_search)
- Skill activation for structured analysis methodology
- Short-term memory via LangGraph MemorySaver (full message history)
- Long-term memory via LLM-generated summaries (persisted across sessions)
"""

import os
import logging
import warnings
import time
from pathlib import Path

# Suppress verbose logging from dependencies
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

for logger_name in ["httpx", "httpcore", "sentence_transformers", "transformers", "milvus", "pymilvus", "grpc", "mcp", "mcp.server"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .prompts import build_system_prompt
from .memory import (
    load_summary, save_summary, format_memory_block,
    build_summarization_prompt,
)
from .chat_ui import (
    print_skill_activation, print_tool_call,
    print_tool_result, clear_thinking,
)

load_dotenv()

# Paths
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MCP_SERVER_PATH = str(_PROJECT_ROOT / "_shared" / "src" / "mcp_servers" / "pattern2_server.py")
_SKILLS_DIR = _PROJECT_ROOT / "_shared" / "skills"

# LangGraph checkpointer (short-term, in-session memory)
checkpointer = MemorySaver()

# Thread config (single session for interactive chat)
THREAD_CONFIG = {"configurable": {"thread_id": "country_chat_1"}}


@tool
def activate_skill(skill_name: str) -> str:
    """Load detailed instructions for a specific analysis skill.

    Available skills:
    - country-comparison: Compare 2+ countries systematically
    - country-profile: Build comprehensive single-country profile
    - regional-analysis: Group by region, compute aggregates
    - report-formatting: Format results as professional markdown
    
    Args:
        skill_name: Name of the skill to activate
        
    Returns:
        The skill's instruction content or an error message
    """
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        available = [d.name for d in _SKILLS_DIR.iterdir() if d.is_dir()]
        return f"Skill '{skill_name}' not found. Available: {available}"
    print_skill_activation(skill_name)
    return skill_path.read_text(encoding="utf-8")


def _get_llm() -> ChatOllama:
    """Create a ChatOllama instance from environment configuration."""
    model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    return ChatOllama(model=model, base_url=base_url)


def _get_mcp_config() -> dict:
    """Get MCP server configuration."""
    return {
        "country_tools": {
            "command": "python",
            "args": [_MCP_SERVER_PATH],
            "transport": "stdio",
        }
    }


async def create_agent() -> tuple:
    """Create the memory-aware agent with MCP tools + skills.
    
    Returns:
        Tuple of (llm, agent, mcp_client, turn_count)
    """
    llm = _get_llm()

    # Load conversation summary for system prompt injection
    summary_data = load_summary()
    memory_block = format_memory_block(summary_data)
    system_prompt = build_system_prompt(memory_block)

    # Connect to MCP server
    client = MultiServerMCPClient(_get_mcp_config())
    mcp_tools = await client.get_tools()
    
    # Combine MCP tools with local skill activation tool
    all_tools = mcp_tools + [activate_skill]

    agent = create_react_agent(
        model=llm,
        tools=all_tools,
        prompt=system_prompt,
        checkpointer=checkpointer,  # ← THE KEY ADDITION for short-term memory
    )

    return llm, agent, client, summary_data.get("turn_count", 0)


async def run_chat_turn(
    user_query: str,
    llm: ChatOllama,
    agent,
    turn_count: int,
) -> dict:
    """Run a single chat turn with memory-aware agent.
    
    Args:
        user_query: The user's question
        llm: ChatOllama instance for summarization
        agent: The LangGraph agent
        turn_count: Current turn number
        
    Returns:
        Dict with full metrics matching Pattern 3 format
    """
    start_time = time.perf_counter()

    # Invoke with thread config (checkpointer handles message accumulation)
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_query)]},
        config=THREAD_CONFIG,
    )

    messages = result["messages"]
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Clear the "Thinking..." indicator
    clear_thinking()

    # Extract metrics + answer (matching Pattern 3 format)
    tool_calls_detail = []
    tools_used = []
    llm_calls = 0
    skill_activations = 0
    prompt_tokens = 0
    completion_tokens = 0
    answer = ""

    for msg in messages:
        msg_type = getattr(msg, "type", type(msg).__name__.lower())
        
        if msg_type == "ai" or type(msg).__name__ == "AIMessage":
            content = getattr(msg, "content", "")
            tool_calls_attr = getattr(msg, "tool_calls", None)
            
            if content or tool_calls_attr:
                llm_calls += 1
                
            # Extract token counts from response_metadata (Ollama format)
            metadata = getattr(msg, "response_metadata", {}) or {}
            prompt_tokens += metadata.get("prompt_eval_count", 0)
            completion_tokens += metadata.get("eval_count", 0)
            
            if content and isinstance(content, str) and content.strip():
                answer = content

            # Print tool call requests in real-time and track metrics
            if tool_calls_attr:
                for tc in tool_calls_attr:
                    tool_name = tc.get("name", "unknown")
                    tools_used.append(tool_name)
                    if tool_name == "activate_skill":
                        skill_activations += 1
                    if tool_name != "activate_skill":
                        print_tool_call(tool_name, tc.get("args", {}))

        if msg_type == "tool" or type(msg).__name__ == "ToolMessage":
            result_text = str(getattr(msg, "content", ""))[:200]
            tool_name = getattr(msg, "name", "unknown")
            tool_calls_detail.append({
                "name": tool_name,
                "result": result_text,
            })
            if tool_name != "activate_skill":
                print_tool_result(tool_name, result_text)

    # Update conversation summary (every turn for long-term memory)
    try:
        summary_prompt = build_summarization_prompt(messages)
        summary_response = await llm.ainvoke(summary_prompt)
        summary_text = getattr(summary_response, "content", "")
        save_summary(summary_text, turn_count)
    except Exception as e:
        # Don't fail the turn if summarization fails
        pass

    return {
        "answer": answer,
        "framework": "langgraph",
        "pattern": "agent_with_memory_and_chat",
        "turn_count": turn_count,
        "llm_calls": llm_calls,
        "total_duration_ms": duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "tool_calls": len(tool_calls_detail),
        "skill_activations": skill_activations,
        "tools_used": tools_used,
        "status": "success",
    }
