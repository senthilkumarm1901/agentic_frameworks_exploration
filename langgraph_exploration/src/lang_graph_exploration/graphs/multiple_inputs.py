from __future__ import annotations

from typing import List, TypedDict

from langgraph.graph import StateGraph

from lang_graph_exploration.cli import print_header


class AgentState(TypedDict):
    values: List[int]
    name: str
    result: str


def process_values(state: AgentState) -> AgentState:
    state["result"] = f"Hi there {state['name']}, Your sum is {sum(state['values'])}"
    return state


def build_app():
    graph = StateGraph(AgentState)
    graph.add_node("processing_node", process_values)
    graph.set_entry_point("processing_node")
    graph.set_finish_point("processing_node")
    return graph.compile()


def run_sample() -> AgentState:
    app = build_app()
    return app.invoke({"name": "Senthil", "values": [0, 1, 1, 2, 3, 5], "result": ""})


def main() -> None:
    print_header("Graph 2 - Multiple Inputs")
    print(run_sample())


if __name__ == "__main__":
    main()