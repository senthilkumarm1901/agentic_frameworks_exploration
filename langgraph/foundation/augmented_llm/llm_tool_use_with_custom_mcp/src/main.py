"""Augmented LLM pattern — CLI entry point.

Runs a LangGraph ReAct agent connected to an MCP server for country data queries.

Usage:
    uv run python -m src.main --task augmented_llm --question "What is the population density of Japan?"
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.agent import run_agent

# Load .env from workspace root (for OLLAMA_MODEL, OLLAMA_BASE_URL)
load_dotenv()

# Default question if none provided
DEFAULT_QUESTION = "How many times larger is the GDP of the United States compared to India?"

# Log file path (in the same directory as this module's parent)
LOG_FILE = Path(__file__).parent.parent / "logs.txt"


def append_to_log(result: dict, question: str, task: str):
    """Append experiment result to logs.txt with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    answer_text = result.get("answer", "")
    
    # Format tool calls detail
    tool_calls_str = ""
    for tc in result.get("tool_calls_detail", []):
        args_formatted = ", ".join(f'{k}="{v}"' for k, v in tc["args"].items())
        tool_calls_str += f"  - {tc['name']}({args_formatted}) \u2192 {tc['result']}\n"
    
    if not tool_calls_str:
        tool_calls_str = "  (none)\n"
    
    # Build log entry
    log_entry = f"""
--- {timestamp} ---
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
        help="Task identifier (e.g., augmented_llm)",
    )
    parser.add_argument(
        "--question",
        required=False,
        default=DEFAULT_QUESTION,
        help="Natural language question about country data (GDP, population, area)",
    )
    args = parser.parse_args()

    print(f"[INFO] Task: {args.task}", file=sys.stderr)
    print(f"[INFO] Question: {args.question}", file=sys.stderr)

    # Run the agent
    result = asyncio.run(run_agent(args.question))

    # Log result to logs.txt
    append_to_log(result, args.question, args.task)
    print(f"[INFO] Result logged to {LOG_FILE}", file=sys.stderr)

    # Emit standardized JSON output to stdout (eval contract)
    output = {
        "question": args.question,
        "answer": result["answer"],
        "llm_calls": result["llm_calls"],
        "tool_calls": result["tool_calls"],
        "total_duration_ms": result["total_duration_ms"],
        "framework": "langgraph",
        "pattern": "augmented_llm",
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
