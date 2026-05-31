"""Augmented LLM pattern — CLI entry point.

Runs a LangGraph ReAct agent connected to an MCP server for country data queries.

Usage:
    uv run python -m src.main --task country_analysis --question "What is the population density of Japan?"
"""

import argparse
import asyncio
import json
import os
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

# Start memory tracking and record cold start time immediately
tracemalloc.start()
_SCRIPT_START_TIME = time.perf_counter()

from dotenv import load_dotenv

from src.agent import run_agent

# Load .env from workspace root (for OLLAMA_MODEL, OLLAMA_BASE_URL)
load_dotenv()

# Default question if none provided
DEFAULT_QUESTION = "How many times larger is the GDP of the United States compared to India?"

# Log file path (in the same directory as this module's parent)
LOG_FILE = Path(__file__).parent.parent / "logs.txt"
LOG_FILE_DISPLAY = LOG_FILE.name
SEPARATOR = "=" * 72


def log_stderr(message: str):
    """Write operational logs to stderr only (not to logs.txt)."""
    print(message, file=sys.stderr)


def _next_experiment_number() -> int:
    """Return the next experiment number based on existing logs."""
    if not LOG_FILE.exists():
        return 1
    content = LOG_FILE.read_text()
    return content.count("Experiment #") + 1



def append_to_log(result: dict, question: str, task: str):
    """Append experiment result to logs.txt with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    answer_text = result.get("answer", "")
    experiment_number = _next_experiment_number()
    
    # Format tool calls detail
    tool_calls_str = ""
    for tc in result.get("tool_calls_detail", []):
        args_formatted = ", ".join(f'{k}="{v}"' for k, v in tc["args"].items())
        tool_calls_str += f"  - {tc['name']}({args_formatted}) \u2192 {tc['result']}\n"
    
    if not tool_calls_str:
        tool_calls_str = "  (none)\n"
    
    # Build log entry
    log_entry = f"""
{SEPARATOR}
Experiment #{experiment_number} | {timestamp}
{SEPARATOR}
Task: {task}
Model: {model}
Question: {question}
Answer:
{answer_text}
LLM Calls: {result["llm_calls"]}
Tool Calls: {result["tool_calls"]}
Tool Calls Detail:
{tool_calls_str}Duration: {result["total_duration_ms"]}ms
Status: SUCCESS
{SEPARATOR}
"""
    
    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def main():
    parser = argparse.ArgumentParser(
        description="Augmented LLM pattern (LangGraph + MCP) — Country data Q&A"
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Task identifier (e.g., country_analysis)",
    )
    parser.add_argument(
        "--question",
        required=False,
        default=DEFAULT_QUESTION,
        help="Natural language question about country data (GDP, population, area)",
    )
    args = parser.parse_args()

    log_stderr(f"[INFO] Task: {args.task}")

    log_stderr(f"[INFO] Question: {args.question}")
    # print(f"[INFO] Question: {args.question}", file=sys.stderr)

    # Capture cold start time (time from script start to first LLM call)
    cold_start_ms = int((time.perf_counter() - _SCRIPT_START_TIME) * 1000)

    # Run the agent
    result = asyncio.run(run_agent(args.question))

    # Get peak memory usage
    _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_memory_mb = round(peak_memory_bytes / (1024 * 1024), 2)

    # Log result to logs.txt
    append_to_log(result, args.question, args.task)
    log_stderr(f"[INFO] Result logged to {LOG_FILE_DISPLAY}")

    # Emit standardized JSON output to stdout (eval contract)
    output = {
        "answer": result["answer"],
        "framework": "langgraph",
        "pattern": "agent_with_multiple_mcp_tools",
        "llm_calls": result["llm_calls"],
        "total_duration_ms": result["total_duration_ms"],
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
        "total_tokens": result["total_tokens"],
        "tool_calls": result["tool_calls"],
        "cold_start_ms": cold_start_ms,
        "peak_memory_mb": peak_memory_mb,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
