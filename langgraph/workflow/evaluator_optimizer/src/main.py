"""Evaluator-Optimizer pattern — iterative generation and evaluation via LangGraph."""
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
    theme: str
    max_iterations: int
    current_haiku: str
    feedback: str
    iteration: int
    accepted: bool


def make_graph(llm, metrics):
    def generate(state: State) -> dict:
        if state["feedback"]:
            prompt = (
                f"Revise this haiku about '{state['theme']}' based on the feedback.\n\n"
                f"Current haiku:\n{state['current_haiku']}\n\nFeedback: {state['feedback']}\n\n"
                f"Output ONLY the revised haiku (three lines), nothing else."
            )
        else:
            prompt = (
                f"Write a haiku about '{state['theme']}'. "
                f"A haiku has exactly 3 lines with 5, 7, and 5 syllables respectively. "
                f"Output ONLY the haiku (three lines), nothing else."
            )
        print(f"Generating haiku (iteration {state['iteration'] + 1})...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        return {"current_haiku": resp.content.strip(), "iteration": state["iteration"] + 1}

    def evaluate(state: State) -> dict:
        prompt = (
            f"Evaluate this haiku about '{state['theme']}':\n\n{state['current_haiku']}\n\n"
            f"Check: 1) Does it have exactly 3 lines? 2) Is the syllable pattern 5-7-5? "
            f"3) Is it relevant to the theme '{state['theme']}'?\n\n"
            f"If the haiku is acceptable, respond with ONLY: ACCEPTED\n"
            f"Otherwise, respond with specific feedback for improvement."
        )
        print(f"Evaluating haiku...", file=sys.stderr)
        t0 = time.perf_counter()
        resp = llm.invoke(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        content = resp.content.strip()
        if "ACCEPTED" in content.upper():
            print("Haiku accepted!", file=sys.stderr)
            return {"accepted": True, "feedback": ""}
        print(f"Feedback: {content}", file=sys.stderr)
        return {"accepted": False, "feedback": content}

    def should_continue(state: State) -> str:
        if state["accepted"] or state["iteration"] >= state["max_iterations"]:
            return "done"
        return "revise"

    graph = StateGraph(State)
    graph.add_node("generate", generate)
    graph.add_node("evaluate", evaluate)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "evaluate")
    graph.add_conditional_edges("evaluate", should_continue, {"revise": "generate", "done": END})

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
        "theme": task["input"]["theme"],
        "max_iterations": task["input"]["max_iterations"],
        "current_haiku": "",
        "feedback": "",
        "iteration": 0,
        "accepted": False,
    })

    answer = f"Haiku ({result['iteration']} iterations, accepted={result['accepted']}):\n{result['current_haiku']}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
