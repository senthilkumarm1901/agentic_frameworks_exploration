"""Augmented LLM pattern — tool use via built-in web toolset (Hermes)."""
import argparse
import sys
import time

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS


def main():
    parser = argparse.ArgumentParser(description="Augmented LLM pattern (Hermes)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="hermes", pattern=args.task)
    metrics.start_timer()

    agent = AIAgent(
        model=config["model"],
        base_url=f"{config['base_url']}/v1",
        api_key="ollama",
        quiet_mode=True,
        max_iterations=10,
        enabled_toolsets=["web"],
        skip_context_files=True,
        skip_memory=True,
    )

    print("Querying agent with web tools...", file=sys.stderr)
    t0 = time.perf_counter()
    response = agent.chat(task["input"]["query"])
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = str(response)
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
