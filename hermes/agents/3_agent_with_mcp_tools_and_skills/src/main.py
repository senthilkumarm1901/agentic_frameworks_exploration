"""Hermes Pattern 3 CLI entry point."""

from __future__ import annotations

import argparse
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

from src.agent import HermesAgent

load_dotenv()

DEFAULT_QUESTION = "Compare the GDP and population of Japan and Germany. Which country has higher GDP per capita?"
LOG_FILE = Path(__file__).parent.parent / "logs.txt"
LOG_FILE_DISPLAY = LOG_FILE.name
SEPARATOR = "=" * 72


def log_stderr(message: str) -> None:
    print(message, file=sys.stderr)


def _next_experiment_number() -> int:
    if not LOG_FILE.exists():
        return 1
    return LOG_FILE.read_text().count("Experiment #") + 1


def append_to_log(result: dict, question: str, task: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model = os.environ.get("OLLAMA_MODEL", "hermes3:latest")
    experiment_number = _next_experiment_number()

    tool_calls_str = ""
    for tc in result.get("tool_calls_detail", []):
        args_formatted = ", ".join(f'{k}="{v}"' for k, v in tc.get("args", {}).items())
        call_sig = f"{tc['name']}({args_formatted})" if args_formatted else f"{tc['name']}()"
        tool_calls_str += f"  - {call_sig} -> {tc.get('result', '')}\n"

    if not tool_calls_str:
        tool_calls_str = "  (none)\n"

    log_entry = f"""
{SEPARATOR}
Experiment #{experiment_number} | {timestamp}
{SEPARATOR}
Task: {task}
Model: {model}
Question: {question}
Answer:
{result.get('answer', '')}
LLM Calls: {result['llm_calls']}
Tool Calls: {result['tool_calls']}
Skill Activations: {result['skill_activations']}
Tool Calls Detail:
{tool_calls_str}Duration: {result['total_duration_ms']}ms
Status: SUCCESS
{SEPARATOR}
"""

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def emit_result(result: dict, cold_start_ms: int) -> int:
    _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = round(peak_memory_bytes / (1024 * 1024), 2)

    output = {
        "answer": result.get("answer", ""),
        "framework": "hermes",
        "pattern": "agent_with_mcp_tools_and_skills",
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Hermes Pattern 3 — country data Q&A with MCP tools and skills"
    )
    parser.add_argument("--task", required=True)
    parser.add_argument("--question", required=False, default=DEFAULT_QUESTION)
    args = parser.parse_args(argv)

    log_stderr(f"[INFO] Task: {args.task}")
    log_stderr(f"[INFO] Question: {args.question}")

    cold_start_ms = int((time.perf_counter() - _SCRIPT_START_TIME) * 1000)

    agent = HermesAgent(
        quiet_mode=True,
        skip_memory=True,
        skip_context_files=True,
    )

    raw = agent.run_conversation(
        user_message=args.question,
        task_id=args.task,
    )
    result = {**raw, "answer": raw["final_response"]}

    append_to_log(result, args.question, args.task)
    log_stderr(f"[INFO] Result logged to {LOG_FILE_DISPLAY}")

    return emit_result(result, cold_start_ms=cold_start_ms)


if __name__ == "__main__":
    raise SystemExit(main())