"""Coding Agent — iterative code fixing with MCP tools (Strands)."""
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
    "You are a coding agent. You are given buggy Python code and failing tests. "
    "Fix the code so all tests pass. Use the run_python_code tool to test your fixes. "
    "Return the corrected code."
)


def main():
    parser = argparse.ArgumentParser(description="Coding Agent (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    task_input = task["input"]
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

        prompt = (
            f"Here is buggy Python code:\n```python\n{task_input['buggy_code']}```\n\n"
            f"Here is the failing test:\n```python\n{task_input['test_code']}```\n\n"
            f"Hint: {task_input['expected_fix']}\n\n"
            f"Fix the code so all tests pass. Use run_python_code to verify your fix."
        )
        print("Sending code to agent...", file=sys.stderr)
        t0 = time.perf_counter()
        response = agent(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

        answer = str(response)
        print(f"Agent: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
