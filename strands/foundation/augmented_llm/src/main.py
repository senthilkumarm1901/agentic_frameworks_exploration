"""Augmented LLM pattern — tool use via MCP (Strands)."""
import argparse
import os
import sys
import time

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters

from shared.metrics import MetricsCollector
from shared.tasks import TASKS
from ollama_adapter import create_ollama_model

_SHARED_PROJECT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "_shared")
)


def main():
    parser = argparse.ArgumentParser(description="Augmented LLM pattern (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    model = create_ollama_model()

    metrics = MetricsCollector(framework="strands", pattern=args.task)
    metrics.start_timer()

    mcp_client = MCPClient(
        StdioServerParameters(
            command="uv",
            args=["run", "--project", _SHARED_PROJECT, "python", "-m", "shared.mcp_server"],
        )
    )

    with mcp_client:
        agent = Agent(
            model=model,
            tools=mcp_client.list_tools_sync(),
        )

        call_start = time.perf_counter()
        response = agent(task["input"]["query"])
        call_ms = (time.perf_counter() - call_start) * 1000
        metrics.record_llm_call(duration_ms=call_ms)

        answer = str(response)
        print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
