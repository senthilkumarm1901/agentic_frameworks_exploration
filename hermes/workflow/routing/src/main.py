"""Routing pattern — classify input and route to specialized handler (Hermes)."""
import argparse
import sys
import time

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS

HANDLER_PROMPTS = {
    "billing": (
        "You are a billing support specialist. Help the customer with their billing issue. "
        "Be empathetic and offer concrete solutions like refunds or credits.\n\nCustomer message: {message}"
    ),
    "technical": (
        "You are a technical support engineer. Help the customer with their technical issue. "
        "Provide clear troubleshooting steps.\n\nCustomer message: {message}"
    ),
    "general": (
        "You are a general customer support agent. Help the customer with their inquiry. "
        "Be helpful and direct.\n\nCustomer message: {message}"
    ),
}


def main():
    parser = argparse.ArgumentParser(description="Routing pattern (Hermes)")
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
        skip_context_files=True,
        skip_memory=True,
    )

    # Step 1: Classify
    print("Classifying...", file=sys.stderr)
    t0 = time.perf_counter()
    classify_resp = agent.chat(
        "Classify the following customer message into exactly one category: "
        "billing, technical, or general. Output ONLY the category word, nothing else.\n\n"
        f"Message: {message}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    category = str(classify_resp).strip().lower()
    if category not in HANDLER_PROMPTS:
        category = "general"
    print(f"Category: {category}", file=sys.stderr)

    # Step 2: Handle with category-specific prompt
    print(f"Handling as {category}...", file=sys.stderr)
    t0 = time.perf_counter()
    handle_resp = agent.chat(HANDLER_PROMPTS[category].format(message=message))
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = f"[{category}] {str(handle_resp)}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
