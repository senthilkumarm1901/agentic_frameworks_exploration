from __future__ import annotations

import random
from typing import List, Literal, TypedDict

from langgraph.graph import END, StateGraph

from lang_graph_exploration.cli import print_header


class AgentState(TypedDict):
    name: str
    number: List[int]
    counter: int


def greeting_node(state: AgentState) -> AgentState:
    state["name"] = f"Hi there, {state['name']}"
    state["counter"] = 0
    return state


def random_node(state: AgentState) -> AgentState:
    state["number"].append(random.randint(0, 10))
    state["counter"] += 1
    return state


def should_continue(state: AgentState) -> Literal["loop", "exit"]:
    if state["counter"] < 5:
        return "loop"
    return "exit"


def build_app():
    graph = StateGraph(AgentState)
    graph.add_node("greeting", greeting_node)
    graph.add_node("random", random_node)
    graph.add_edge("greeting", "random")
    graph.add_conditional_edges(
        "random",
        should_continue,
        {"loop": "random", "exit": END},
    )
    graph.set_entry_point("greeting")
    return graph.compile()


def run_sample(seed: int = 7) -> AgentState:
    random.seed(seed)
    app = build_app()
    return app.invoke({"name": "Vaibhav", "number": [], "counter": -100})


def main() -> None:
    print_header("Graph 5 - Looping")
    print(run_sample())


if __name__ == "__main__":
    main()