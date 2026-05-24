"""Prompt Chaining pattern — fixed sequence of LLM steps (Hermes)."""
import argparse
import sys
import time

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS


def main():
    parser = argparse.ArgumentParser(description="Prompt Chaining pattern (Hermes)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    text = task["input"]["text"]
    target_language = task["input"]["target_language"]
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

    # Step 1: Summarize
    print("Summarizing...", file=sys.stderr)
    t0 = time.perf_counter()
    summary = agent.chat(
        f"Summarize the following text in exactly 2 sentences:\n\n{text}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    # Step 2: Translate
    print(f"Translating to {target_language}...", file=sys.stderr)
    t0 = time.perf_counter()
    translation = agent.chat(
        f"Translate the following text to {target_language}. "
        f"Output ONLY the translation, nothing else:\n\n{summary}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = f"Summary: {summary}\n\nTranslation: {translation}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
