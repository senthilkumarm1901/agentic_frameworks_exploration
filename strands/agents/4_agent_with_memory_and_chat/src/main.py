"""Interactive terminal chat with memory — Strands Pattern 4 entry point.

Usage:
    uv run python -m src.main              # Start interactive chat
    uv run python -m src.main --reset      # Clear memory and start fresh

Features:
- Short-term memory: Strands Agent reused across turns (ConversationManager
  accumulates the full message history automatically — no checkpointer needed)
- Long-term memory: LLM-generated summaries persisted to memory_store/session.json
- Multi-turn conversation with context continuity
- Skills and MCP tools from Pattern 3
- JSON metrics logging to logs.txt (same format as Pattern 3)
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .agent import ChatSession, run_chat_turn
from .chat_ui import (
    get_user_input,
    print_answer,
    print_error,
    print_memory_cleared,
    print_memory_summary,
    print_metrics,
    print_thinking,
    print_welcome,
)
from .memory import clear_summary, load_summary

LOGS_FILE = Path(__file__).parent.parent / "logs.txt"


def _get_model_name() -> str:
    return os.environ.get("OLLAMA_MODEL", "qwen3.5:35b-a3b-coding-nvfp4")


def _ensure_log_header():
    from datetime import datetime
    if not LOGS_FILE.exists() or LOGS_FILE.stat().st_size == 0:
        header = (
            f"# Pattern 4 (Strands): Agent with Memory and Chat — Chat Logs\n"
            f"# Started: {datetime.now().astimezone().isoformat()}\n"
            f"# Model: {_get_model_name()}\n\n"
        )
        LOGS_FILE.write_text(header, encoding="utf-8")


def log_turn_metrics(result: dict, user_query: str, turn_count: int):
    """Append turn metrics as JSON to logs.txt."""
    _ensure_log_header()
    entry = (
        f"## Turn {turn_count}\n"
        f"Question: {user_query}\n"
        f"Duration: {result.get('total_duration_ms', 0)}ms\n"
        f"```json\n{json.dumps(result, indent=4)}\n```\n\n"
    )
    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def chat_loop(reset: bool = False):
    """Main interactive chat loop."""
    if reset:
        clear_summary()
        print("  🗑️  Memory cleared.\n")

    session = ChatSession()
    try:
        session.initialize()
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        return

    print_welcome(session.turn_count)

    try:
        while True:
            user_input = get_user_input()

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
                session.reinitialize()
                continue

            if not user_input:
                continue

            session.turn_count += 1
            print_thinking()

            try:
                result = run_chat_turn(session, user_input)
                log_turn_metrics(result, user_input, session.turn_count)

                answer = result.get("answer", "")
                print_answer(answer if answer else "[No response generated]")
                print_metrics(
                    result["llm_calls"],
                    result["tool_calls"],
                    result["total_duration_ms"],
                    result.get("skill_activations", 0),
                )
            except Exception as e:
                print_error(str(e))
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Country Analysis Agent — Interactive Chat with Memory (Strands)"
    )
    parser.add_argument("--reset", action="store_true", help="Clear memory and start fresh")
    args = parser.parse_args()
    chat_loop(reset=args.reset)


if __name__ == "__main__":
    main()
