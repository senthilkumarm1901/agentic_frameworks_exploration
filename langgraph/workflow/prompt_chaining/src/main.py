"""Prompt Chaining pattern — fixed sequence of LLM steps via LangGraph."""
import argparse
import sys
import time
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS


class State(TypedDict):
    text: str
    target_language: str
    summary: str
    translation: str


def make_graph(llm, metrics):
    def summarize(state: State) -> dict:
        prompt = (
            f"Summarize the following text in exactly 2 sentences:\n\n{state['text']}"
        )
        print(f"Summarizing...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"summary": resp.content}

    def translate(state: State) -> dict:
        prompt = (
            f"Translate the following text to {state['target_language']}. "
            f"Output ONLY the translation, nothing else:\n\n{state['summary']}"
        )
        print(f"Translating to {state['target_language']}...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"translation": resp.content}

    graph = StateGraph(State)
    graph.add_node("summarize", summarize)
    graph.add_node("translate", translate)
    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", "translate")
    graph.add_edge("translate", END)
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

    result = app.invoke({
        "text": task["input"]["text"],
        "target_language": task["input"]["target_language"],
        "summary": "",
        "translation": "",
    })

    answer = f"Summary: {result['summary']}\n\nTranslation: {result['translation']}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
