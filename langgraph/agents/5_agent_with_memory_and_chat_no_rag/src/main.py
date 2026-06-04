"""Interactive terminal chat with memory — Pattern 5 entry point.

Usage:
    uv run python -m src.main              # Start interactive chat
    uv run python -m src.main --reset      # Clear memory and start fresh

Features:
- Short-term memory: Full message history via LangGraph MemorySaver
- Long-term memory: LLM-generated summaries persisted to session.json
- Multi-turn conversation with context continuity
- Skills and MCP tools (wiki-based, no vector RAG)
- JSON metrics logging to logs.txt

Key difference from Pattern 4:
- Replaces Milvus RAG with LLM Wiki
- No sentence-transformers or embedding dependencies
- Uses wiki_read_tool instead of country_kb_search_tool
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .agent import create_agent, run_chat_turn
from .memory import load_summary, clear_summary
from .chat_ui import (
    print_welcome, print_answer, print_thinking,
    print_metrics, print_memory_summary, get_user_input,
    print_memory_cleared, print_error,
)

# Log file path
LOGS_FILE = Path(__file__).parent.parent / "logs.txt"


def _get_model_name() -> str:
    """Get the configured model name."""
    import os
    return os.environ.get("OLLAMA_MODEL", "qwen3:8b")


def _ensure_log_header():
    """Write log file header if file doesn't exist or is empty."""
    from datetime import datetime
    if not LOGS_FILE.exists() or LOGS_FILE.stat().st_size == 0:
        header = f"""# Pattern 5: Agent with Memory and LLM Wiki (No RAG) - Chat Logs
# Started: {datetime.now().astimezone().isoformat()}
# Model: {_get_model_name()}

"""
        LOGS_FILE.write_text(header, encoding="utf-8")


def log_turn_metrics(result: dict, user_query: str, turn_count: int):
    """Append turn metrics as JSON to logs.txt with markdown formatting."""
    _ensure_log_header()
    
    # Create formatted entry like Pattern 3/4
    entry = f"""## Turn {turn_count}
Question: {user_query}
Duration: {result.get('total_duration_ms', 0)}ms
```json
{json.dumps(result, indent=4)}
```

"""
    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


async def chat_loop():
    """Main interactive chat loop."""
    try:
        # Initialize agent (loads memory, connects MCP, creates graph)
        # Note: langchain-mcp-adapters 0.1.0+ creates sessions per-tool-call,
        # so the client doesn't need to be used as a context manager
        llm, agent, mcp_client, turn_count = await create_agent()
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        return

    print_welcome(turn_count)

    while True:
        user_input = get_user_input()

        # Handle special commands
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  👋 Goodbye! Session saved.\n")
            break

        if user_input.lower() == "memory":
            summary_data = load_summary()
            print_memory_summary(
                summary_data.get("summary", ""),
                summary_data.get("turn_count", 0),
            )
            continue

        if user_input.lower() == "clear":
            clear_summary()
            print_memory_cleared()
            # Reinitialize agent with cleared memory
            llm, agent, mcp_client_new, turn_count = await create_agent()
            turn_count = 0
            continue

        if not user_input:
            continue

        # Run agent turn
        turn_count += 1
        print_thinking()

        try:
            result = await run_chat_turn(user_input, llm, agent, turn_count)

            # Log metrics to logs.txt (same format as Pattern 3/4)
            log_turn_metrics(result, user_input, turn_count)

            # Display results
            if result["answer"]:
                print_answer(result["answer"])
            else:
                print_answer("[No response generated]")
                
            print_metrics(
                result["llm_calls"],
                result["tool_calls"],
                result["total_duration_ms"],
                result.get("skill_activations", 0),
            )
        except Exception as e:
            print_error(str(e))


def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Country Analysis Agent — Interactive Chat with Memory (No RAG)"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Clear memory and start fresh"
    )
    args = parser.parse_args()

    if args.reset:
        clear_summary()
        print("  🗑️  Memory cleared.\n")

    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
