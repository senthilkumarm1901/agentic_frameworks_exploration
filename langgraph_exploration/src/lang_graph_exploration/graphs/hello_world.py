from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph

from lang_graph_exploration.cli import print_header


class AgentState(TypedDict):
    message: str


def greeting_node(state: AgentState) -> AgentState:
    state["message"] = f"Hey {state['message']}, how is your day going?"
    return state


def build_app():
    graph = StateGraph(AgentState)
    graph.add_node("greeter", greeting_node)
    graph.set_entry_point("greeter")
    graph.set_finish_point("greeter")
    return graph.compile()


def run_sample(name: str = "Bob") -> AgentState:
    app = build_app()
    return app.invoke({"message": name})


def main() -> None:
    print_header("Graph 1 - Hello World")
    result = run_sample()
    print(result["message"])


if __name__ == "__main__":
    main()