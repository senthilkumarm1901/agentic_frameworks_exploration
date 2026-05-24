"""Customer Support Agent — autonomous agent with system prompt (Hermes)."""
import argparse
import sys
import time

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS

SYSTEM_PROMPT = (
    "You are a customer support agent. You have access to web tools to look up information. "
    "When a customer reports an issue with an order, you should: "
    "1) Acknowledge the issue empathetically, "
    "2) Investigate by looking up order details and tracking information, "
    "3) Offer a concrete resolution (refund, replacement, escalation). "
    "Always be helpful and professional."
)


def main():
    parser = argparse.ArgumentParser(description="Customer Support Agent (Hermes)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    message = task["input"]["message"]
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
        enabled_toolsets=["web"],
        skip_context_files=True,
        skip_memory=True,
    )

    print(f"Customer: {message}", file=sys.stderr)
    t0 = time.perf_counter()
    response = agent.chat(message)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = str(response)
    print(f"Agent: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
