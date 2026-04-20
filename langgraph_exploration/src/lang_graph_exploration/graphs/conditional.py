from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.cli import print_header


class AgentState(TypedDict):
    number1: int
    operation: str
    number2: int
    finalNumber: int


def adder(state: AgentState) -> AgentState:
    state["finalNumber"] = state["number1"] + state["number2"]
    return state


def subtractor(state: AgentState) -> AgentState:
    state["finalNumber"] = state["number1"] - state["number2"]
    return state


def router(state: AgentState) -> AgentState:
    return state


def decide_next_node(state: AgentState) -> Literal["addition_operation", "subtraction_operation"]:
    if state["operation"] == "+":
        return "addition_operation"
    return "subtraction_operation"


def build_app():
    graph = StateGraph(AgentState)
    graph.add_node("router", router)
    graph.add_node("add_node", adder)
    graph.add_node("subtract_node", subtractor)
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        decide_next_node,
        {
            "addition_operation": "add_node",
            "subtraction_operation": "subtract_node",
        },
    )
    graph.add_edge("add_node", END)
    graph.add_edge("subtract_node", END)
    return graph.compile()


def run_sample() -> AgentState:
    app = build_app()
    return app.invoke({"number1": 10, "operation": "-", "number2": 5, "finalNumber": 0})


def main() -> None:
    print_header("Graph 4 - Conditional")
    print(run_sample())


if __name__ == "__main__":
    main()