"""Hermes Pattern 4 CLI entry point."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

tracemalloc.start()
_SCRIPT_START_TIME = time.perf_counter()

from dotenv import load_dotenv

from .agent import HermesAgent
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

load_dotenv()

LOG_FILE = Path(__file__).parent.parent / "logs.txt"
LOG_FILE_DISPLAY = LOG_FILE.name
SEPARATOR = "=" * 72


def _get_model_name() -> str:
    return os.environ.get("OLLAMA_MODEL", "hermes3:latest")


def _next_experiment_number() -> int:
    if not LOG_FILE.exists():
        return 1
    return LOG_FILE.read_text(encoding="utf-8").count("Experiment #") + 1


def _ensure_log_header() -> None:
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        header = (
            f"# Pattern 4: Agent with Memory and Chat Capability - Chat Logs\n"
            f"# Started: {datetime.now().astimezone().isoformat()}\n"
            f"# Model: {_get_model_name()}\n\n"
        )
        LOG_FILE.write_text(header, encoding="utf-8")


def append_to_log(result: dict, question: str, task: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    experiment_number = _next_experiment_number()

    tool_calls_str = ""
    for tc in result.get("tool_calls_detail", []):
        args_formatted = ", ".join(f'{key}="{value}"' for key, value in tc.get("args", {}).items())
        call_sig = f"{tc['name']}({args_formatted})" if args_formatted else f"{tc['name']}()"
        tool_calls_str += f"  - {call_sig} -> {tc.get('result', '')}\n"

    if not tool_calls_str:
        tool_calls_str = "  (none)\n"

    log_entry = f"""
{SEPARATOR}
Experiment #{experiment_number} | {timestamp}
{SEPARATOR}
Task: {task}
Model: {_get_model_name()}
Question: {question}
Answer:
{result.get('answer', '')}
LLM Calls: {result['llm_calls']}
Prompt Tokens: {result['prompt_tokens']}
Completion Tokens: {result['completion_tokens']}
Total Tokens: {result['total_tokens']}
Tool Calls: {result['tool_calls']}
Skill Activations: {result['skill_activations']}
Tool Calls Detail:
{tool_calls_str}Duration: {result['total_duration_ms']}ms
Status: SUCCESS
{SEPARATOR}
"""

    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(log_entry)


def emit_result(result: dict, cold_start_ms: int) -> int:
    _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = round(peak_memory_bytes / (1024 * 1024), 2)

    output = {
        "answer": result.get("answer", ""),
        "framework": "hermes",
        "pattern": "agent_with_memory_and_chat",
        "llm_calls": result["llm_calls"],
        "total_duration_ms": result["total_duration_ms"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
        "total_tokens": result["total_tokens"],
        "tool_calls": result["tool_calls"],
        "skill_activations": result["skill_activations"],
        "tools_used": result.get("tools_used", []),
        "cold_start_ms": cold_start_ms,
        "peak_memory_mb": peak_memory_mb,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


async def chat_loop(reset: bool = False) -> None:
    if reset:
        clear_summary()
        print("  🗑️  Memory cleared.\n")

    agent = HermesAgent(quiet_mode=True, skip_memory=False, skip_context_files=True)
    try:
        await agent.initialize()
    except Exception as exc:
        print_error(f"Failed to initialize agent: {exc}")
        return

    print_welcome(agent.turn_count)

    try:
        while True:
            user_input = get_user_input()

            if user_input.lower() in ("quit", "exit", "q"):
                print("\n  👋 Goodbye! Session saved.\n")
                break

            if user_input.lower() == "memory":
                summary_data = load_summary()
                print_memory_summary(summary_data.get("summary", ""), summary_data.get("turn_count", 0))
                continue

            if user_input.lower() == "clear":
                clear_summary()
                print_memory_cleared()
                await agent.reinitialize()
                continue

            if not user_input:
                continue

            print_thinking()

            try:
                result = await agent._run_turn(user_message=user_input, system_message=None, task_id=None)
                result["answer"] = result.get("final_response", "")
                append_to_log(result, user_input, "country_analysis_chat")

                print_answer(result["answer"] if result.get("answer") else "[No response generated]")
                print_metrics(
                    result["llm_calls"],
                    result["tool_calls"],
                    result["total_duration_ms"],
                    result.get("skill_activations", 0),
                )
            except Exception as exc:
                print_error(str(exc))
    finally:
        await agent.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Pattern 4 — country data chat with memory")
    parser.add_argument("--reset", action="store_true", help="Clear memory and start fresh")
    args = parser.parse_args()

    cold_start_ms = int((time.perf_counter() - _SCRIPT_START_TIME) * 1000)
    asyncio.run(chat_loop(reset=args.reset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
