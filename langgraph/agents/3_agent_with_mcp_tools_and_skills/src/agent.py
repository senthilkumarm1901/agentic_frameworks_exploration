"""LangGraph ReAct agent with MCP tools and skill activation."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from .prompts import SYSTEM_PROMPT
from .skill_tools import activate_skill

load_dotenv()

# MCP server path (same as Pattern 2 - uses pattern2_server with 3 tools)
MCP_SERVER_PATH = Path(__file__).parent.parent.parent.parent.parent / "_shared" / "src" / "mcp_servers" / "pattern2_server.py"


def _get_mcp_config() -> dict:
    """Get the MCP server configuration."""
    return {
        "country_tools": {
            "command": "python",
            "args": [str(MCP_SERVER_PATH)],
            "transport": "stdio",
        }
    }


def _get_llm() -> ChatOllama:
    """Create a ChatOllama instance from environment configuration."""
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


async def run_agent(question: str) -> dict:
    """Run the agent and return structured results with metrics.
    
    Note: The MCP server handles concurrent tool calls by using thread-safe
    singleton patterns for Milvus database access.
    """
    start_time = time.perf_counter()
    
    llm_calls = 0
    tool_calls = 0
    skill_activations = 0
    tools_used = []
    prompt_tokens = 0
    completion_tokens = 0
    
    llm = _get_llm()
    
    # Create MCP client and get tools
    # Note: langchain-mcp-adapters 0.1.0+ creates sessions per-tool-call,
    # so the client doesn't need explicit cleanup
    client = MultiServerMCPClient(_get_mcp_config())
    mcp_tools = await client.get_tools()
    
    # Combine MCP tools with local skill activation tool
    all_tools = mcp_tools + [activate_skill]
    
    agent = create_react_agent(
        model=llm,
        tools=all_tools,
        prompt=SYSTEM_PROMPT,
    )
    
    result = await agent.ainvoke({"messages": [("user", question)]})
    
    # Extract metrics from message history
    for msg in result.get("messages", []):
        msg_type = type(msg).__name__
        
        if msg_type == "AIMessage":
            llm_calls += 1
            # Extract token counts from response_metadata (Ollama format)
            metadata = getattr(msg, "response_metadata", {}) or {}
            prompt_tokens += metadata.get("prompt_eval_count", 0)
            completion_tokens += metadata.get("eval_count", 0)
            # Count tool calls in this message
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls += 1
                    tool_name = tc.get("name", "unknown")
                    tools_used.append(tool_name)
                    if tool_name == "activate_skill":
                        skill_activations += 1
    
    total_duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    # Get final answer
    final_message = result["messages"][-1]
    answer = final_message.content if hasattr(final_message, "content") else str(final_message)
    
    return {
        "answer": answer,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "skill_activations": skill_activations,
        "tools_used": tools_used,
        "total_duration_ms": total_duration_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
