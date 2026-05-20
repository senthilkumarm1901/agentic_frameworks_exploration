"""Coding Agent — iterative code fixing with MCP tools via LangGraph."""
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

SYSTEM_PROMPT = (
    "You are a coding agent. You are given buggy Python code and a failing test. "
    "Fix the code so the test passes. Use the run_python_code tool to test your fixes. "
    "Return the corrected code."
)


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
        agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)

        user_msg = (
            f"Here is buggy Python code:\n```python\n{task_input['buggy_code']}```\n\n"
            f"Here is the failing test:\n```python\n{task_input['test_code']}```\n\n"
            f"Fix the code so all tests pass. Use run_python_code to verify your fix."
        )
        print("Sending code to agent...", file=sys.stderr)
        t0 = time.perf_counter()
        result = await agent.ainvoke({"messages": [("user", user_msg)]})
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

        answer = result["messages"][-1].content
        print(f"Agent: {answer}", file=sys.stderr)
        return answer


def main():
    parser = argparse.ArgumentParser()
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
