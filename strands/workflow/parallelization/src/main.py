"""Parallelization pattern — multi-aspect code review with fan-out/fan-in (Strands)."""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from strands import Agent

from shared.metrics import MetricsCollector
from shared.tasks import TASKS
from ollama_adapter import create_ollama_model

REVIEW_PROMPTS = {
    "correctness": (
        "You are a code correctness reviewer. Analyze the following code for bugs, "
        "off-by-one errors, missing edge cases, and logical errors. Be specific.\n\nCode:\n{code}"
    ),
    "performance": (
        "You are a performance reviewer. Analyze the following code for time complexity, "
        "space complexity, and optimization opportunities. Be specific.\n\nCode:\n{code}"
    ),
    "style": (
        "You are a code style reviewer. Analyze the following code for readability, "
        "naming conventions, Pythonic idioms, and maintainability. Be specific.\n\nCode:\n{code}"
    ),
}


def _review(aspect: str, code: str, model, metrics: MetricsCollector) -> str:
    agent = Agent(model=model)
    prompt = REVIEW_PROMPTS[aspect].format(code=code)
    print(f"Reviewing {aspect}...", file=sys.stderr)
    t0 = time.perf_counter()
    resp = agent(prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    return f"## {aspect.title()} Review\n{str(resp)}"


def main():
    parser = argparse.ArgumentParser(description="Parallelization pattern (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    code = task["input"]["code"]
    model = create_ollama_model()

    metrics = MetricsCollector(framework="strands", pattern=args.task)
    metrics.start_timer()

    # Fan-out: 3 parallel review threads
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            aspect: pool.submit(_review, aspect, code, model, metrics)
            for aspect in REVIEW_PROMPTS
        }
        reviews = [futures[aspect].result() for aspect in REVIEW_PROMPTS]

    # Fan-in: merge reviews
    combined = "\n\n".join(reviews)
    agent = Agent(model=model)
    print("Merging reviews...", file=sys.stderr)
    t0 = time.perf_counter()
    merge_resp = agent(
        "You are a senior engineer. Synthesize the following three code reviews into "
        "a single, actionable summary. Highlight the most critical issues first.\n\n"
        f"{combined}"
    )
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = str(merge_resp)
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
