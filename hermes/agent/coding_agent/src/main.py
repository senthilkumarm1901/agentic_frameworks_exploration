"""Coding Agent — iterative code fixing with terminal toolset (Hermes)."""
import argparse
import sys
import time

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS

SYSTEM_PROMPT = (
    "You are a coding agent. You are given buggy Python code and failing tests. "
    "Fix the code so all tests pass. Use the terminal to test your fixes. "
    "Return the corrected code."
)


def main():
    parser = argparse.ArgumentParser(description="Coding Agent (Hermes)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    task_input = task["input"]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="hermes", pattern=args.task)
    metrics.start_timer()

    agent = AIAgent(
        model=config["model"],
        base_url=f"{config['base_url']}/v1",
        api_key="ollama",
        quiet_mode=True,
        max_iterations=10,
        ephemeral_system_prompt=SYSTEM_PROMPT,
        enabled_toolsets=["terminal"],
        skip_context_files=True,
        skip_memory=True,
    )

    prompt = (
        f"Here is buggy Python code:\n```python\n{task_input['buggy_code']}```\n\n"
        f"Here is the failing test:\n```python\n{task_input['test_code']}```\n\n"
        f"Hint: {task_input['expected_fix']}\n\n"
        f"Fix the code so all tests pass. Use the terminal to verify your fix."
    )
    print("Sending code to agent...", file=sys.stderr)
    t0 = time.perf_counter()
    response = agent.chat(prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = str(response)
    print(f"Agent: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
