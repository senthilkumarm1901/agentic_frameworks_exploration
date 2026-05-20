"""Prompt Chaining pattern — fixed sequence of LLM steps (Strands)."""
import argparse
import sys
import time

from strands import Agent

from shared.metrics import MetricsCollector
from shared.tasks import TASKS
from ollama_adapter import create_ollama_model


def main():
    parser = argparse.ArgumentParser(description="Prompt Chaining pattern (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    text = task["input"]["text"]
    target_language = task["input"]["target_language"]
    model = create_ollama_model()
    agent = Agent(model=model)

    metrics = MetricsCollector(framework="strands", pattern=args.task)
    metrics.start_timer()

    # Step 1: Summarize
    print("Summarizing...", file=sys.stderr)
    t0 = time.perf_counter()
    summary_resp = agent(
        f"Summarize the following text in exactly 2 sentences:\n\n{text}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    summary = str(summary_resp)

    # Step 2: Translate
    print(f"Translating to {target_language}...", file=sys.stderr)
    t0 = time.perf_counter()
    translation_resp = agent(
        f"Translate the following text to {target_language}. "
        f"Output ONLY the translation, nothing else:\n\n{summary}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    translation = str(translation_resp)

    answer = f"Summary: {summary}\n\nTranslation: {translation}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
