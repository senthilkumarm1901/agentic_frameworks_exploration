"""CLI entry point for Pattern 3: Agent with MCP Tools and Skills."""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import tracemalloc
import warnings

# Suppress verbose logging from dependencies BEFORE importing them
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = ""

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")

for _logger_name in ["httpx", "httpcore", "sentence_transformers", "transformers", "milvus", "pymilvus", "grpc"]:
    logging.getLogger(_logger_name).setLevel(logging.ERROR)

# Start memory tracking and record cold start time immediately
tracemalloc.start()
_SCRIPT_START_TIME = time.perf_counter()

from .agent import run_agent


def main():
    parser = argparse.ArgumentParser(
        description="Run the country analysis agent with skills"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="country_analysis",
        help="Task name for logging",
    )
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="Question to ask the agent",
    )
    
    args = parser.parse_args()
    
    # Capture cold start time (time from script start to first LLM call)
    cold_start_ms = int((time.perf_counter() - _SCRIPT_START_TIME) * 1000)
    
    try:
        result = asyncio.run(run_agent(args.question))
        
        # Get peak memory usage
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = round(peak_memory_bytes / (1024 * 1024), 2)
        
        output = {
            "answer": result["answer"],
            "framework": "langgraph",
            "pattern": "agent_with_mcp_tools_and_skills",
            "llm_calls": result["llm_calls"],
            "total_duration_ms": result["total_duration_ms"],
            "prompt_tokens": result["prompt_tokens"],
            "completion_tokens": result["completion_tokens"],
            "total_tokens": result["total_tokens"],
            "tool_calls": result["tool_calls"],
            "skill_activations": result["skill_activations"],
            "tools_used": result["tools_used"],
            "cold_start_ms": cold_start_ms,
            "peak_memory_mb": peak_memory_mb,
            "status": "success",
        }
        
    except Exception as e:
        # Get peak memory usage even on error
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = round(peak_memory_bytes / (1024 * 1024), 2)
        
        output = {
            "answer": None,
            "framework": "langgraph",
            "pattern": "agent_with_mcp_tools_and_skills",
            "error": str(e),
            "llm_calls": 0,
            "total_duration_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "tool_calls": 0,
            "skill_activations": 0,
            "tools_used": [],
            "cold_start_ms": cold_start_ms,
            "peak_memory_mb": peak_memory_mb,
            "status": "error",
        }
    
    # Output JSON to stdout for eval capture
    print(json.dumps(output))
    
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
