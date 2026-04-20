from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph

from lang_graph_exploration.cli import print_header


class AgentState(TypedDict):
    name: str
    age: int
    final: str


def first_node(state: AgentState) -> AgentState:
    state["final"] = f"Hi {state['name']}!"
    return state


def second_node(state: AgentState) -> AgentState:
    state["final"] = f"{state['final']} You are {state['age']} years old!"
    return state


def build_app():
    graph = StateGraph(AgentState)
    graph.add_node("first_node", first_node)
    graph.add_node("second_node", second_node)
    graph.set_entry_point("first_node")
    graph.add_edge("first_node", "second_node")
    graph.set_finish_point("second_node")
    return graph.compile()


def run_sample() -> AgentState:
    app = build_app()
    return app.invoke({"name": "Charlie", "age": 20, "final": ""})


def main() -> None:
    print_header("Graph 3 - Sequential")
    print(run_sample())


if __name__ == "__main__":
    main()