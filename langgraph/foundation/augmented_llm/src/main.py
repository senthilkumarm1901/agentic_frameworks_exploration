"""Augmented LLM pattern — RAG + tool use via MCP."""
import argparse
import asyncio
import os
import sys
import time

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS

_SHARED_PROJECT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "_shared")


async def run(task_input: dict, config: dict, metrics: MetricsCollector):
    llm = ChatOllama(model=config["model"], base_url=config["base_url"])

    async with MultiServerMCPClient(
        {
            "tool-stubs": {
                "command": "uv",
                "args": ["run", "--project", _SHARED_PROJECT, "python", "-m", "shared.mcp_server"],
                "transport": "stdio",
            }
        }
    ) as client:
        tools = client.get_tools()
        agent = create_react_agent(llm, tools=tools)

        call_start = time.perf_counter()
        result = await agent.ainvoke({"messages": [("user", task_input["query"])]})
        call_ms = (time.perf_counter() - call_start) * 1000
        metrics.record_llm_call(duration_ms=call_ms)

        answer = result["messages"][-1].content
        print(f"Answer: {answer}", file=sys.stderr)
        return answer


def main():
    parser = argparse.ArgumentParser(description="Augmented LLM pattern (LangGraph)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="langgraph", pattern=args.task)
    metrics.start_timer()

    answer = asyncio.run(run(task["input"], config, metrics))

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
