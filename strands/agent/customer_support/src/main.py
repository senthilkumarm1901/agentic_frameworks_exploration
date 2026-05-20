"""Customer Support Agent — autonomous agent with MCP tools (Strands)."""
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

SYSTEM_PROMPT = (
    "You are a customer support agent. You have access to tools to look up orders, "
    "check tracking, issue refunds, escalate issues, and search the knowledge base. "
    "Always look up the order and check tracking before making decisions. "
    "Help the customer resolve their issue."
)


def main():
    parser = argparse.ArgumentParser(description="Customer Support Agent (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    message = task["input"]["message"]
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
        tools = mcp_client.list_tools_sync()
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )

        print(f"Customer: {message}", file=sys.stderr)
        t0 = time.perf_counter()
        response = agent(message)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

        answer = str(response)
        print(f"Agent: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
