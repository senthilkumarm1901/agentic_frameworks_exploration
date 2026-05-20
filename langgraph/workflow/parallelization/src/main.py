"""Parallelization pattern — multi-aspect code review with fan-out/fan-in via LangGraph."""
import argparse
import sys
import time
from operator import add
from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS


class State(TypedDict):
    code: str
    reviews: Annotated[list[str], add]
    merged_review: str


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


def make_graph(llm, metrics):
    def _review(state: State, aspect: str) -> dict:
        prompt = REVIEW_PROMPTS[aspect].format(code=state["code"])
        print(f"Reviewing {aspect}...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"reviews": [f"## {aspect.title()} Review\n{resp.content}"]}

    def review_correctness(state: State) -> dict:
        return _review(state, "correctness")

    def review_performance(state: State) -> dict:
        return _review(state, "performance")

    def review_style(state: State) -> dict:
        return _review(state, "style")

    def merge_reviews(state: State) -> dict:
        combined = "\n\n".join(state["reviews"])
        prompt = (
            "You are a senior engineer. Synthesize the following three code reviews into "
            "a single, actionable summary. Highlight the most critical issues first.\n\n"
            f"{combined}"
        )
        print("Merging reviews...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"merged_review": resp.content}

    graph = StateGraph(State)
    graph.add_node("review_correctness", review_correctness)
    graph.add_node("review_performance", review_performance)
    graph.add_node("review_style", review_style)
    graph.add_node("merge", merge_reviews)

    graph.add_edge(START, "review_correctness")
    graph.add_edge(START, "review_performance")
    graph.add_edge(START, "review_style")

    graph.add_edge("review_correctness", "merge")
    graph.add_edge("review_performance", "merge")
    graph.add_edge("review_style", "merge")

    graph.add_edge("merge", END)
    return graph.compile()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="langgraph", pattern=args.task)
    metrics.start_timer()

    llm = ChatOllama(model=config["model"], base_url=config["base_url"])
    app = make_graph(llm, metrics)

    result = app.invoke({"code": task["input"]["code"], "reviews": [], "merged_review": ""})

    answer = result["merged_review"]
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
