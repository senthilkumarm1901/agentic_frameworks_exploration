"""Routing pattern — classify input and route to specialized handler via LangGraph."""
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
    message: str
    category: str
    response: str


HANDLER_PROMPTS = {
    "billing": "You are a billing support specialist. Help the customer with their billing issue. Be empathetic and offer concrete solutions like refunds or credits.\n\nCustomer message: {message}",
    "technical": "You are a technical support engineer. Help the customer with their technical issue. Provide clear troubleshooting steps.\n\nCustomer message: {message}",
    "general": "You are a general customer support agent. Help the customer with their inquiry. Be helpful and direct.\n\nCustomer message: {message}",
}


def make_graph(llm, metrics):
    def classify(state: State) -> dict:
        prompt = (
            "Classify the following customer message into exactly one category: "
            "billing, technical, or general. Output ONLY the category word, nothing else.\n\n"
            f"Message: {state['message']}"
        )
        print("Classifying...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        category = resp.content.strip().lower()
        if category not in HANDLER_PROMPTS:
            category = "general"
        print(f"Category: {category}", file=sys.stderr)
        return {"category": category}

    def handle_billing(state: State) -> dict:
        return _handle(state, "billing")

    def handle_technical(state: State) -> dict:
        return _handle(state, "technical")

    def handle_general(state: State) -> dict:
        return _handle(state, "general")

    def _handle(state: State, category: str) -> dict:
        prompt = HANDLER_PROMPTS[category].format(message=state["message"])
        print(f"Handling as {category}...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"response": resp.content}

    def route(state: State) -> str:
        return f"handle_{state['category']}"

    graph = StateGraph(State)
    graph.add_node("classify", classify)
    graph.add_node("handle_billing", handle_billing)
    graph.add_node("handle_technical", handle_technical)
    graph.add_node("handle_general", handle_general)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route)
    graph.add_edge("handle_billing", END)
    graph.add_edge("handle_technical", END)
    graph.add_edge("handle_general", END)
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
        "message": task["input"]["message"],
        "category": "",
        "response": "",
    })

    answer = f"[{result['category']}] {result['response']}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
