from __future__ import annotations

import argparse
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.cli import print_header
from lang_graph_exploration.models import create_chat_model


class AgentState(TypedDict):
    messages: list[HumanMessage]
    response: str


llm = create_chat_model()


def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    state["response"] = response.content
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("process", process)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)
    return graph.compile()


def run_prompt(prompt: str) -> str:
    agent = build_agent()
    result = agent.invoke({"messages": [HumanMessage(content=prompt)], "response": ""})
    return result["response"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 1 - Simple Bot")
    parser.add_argument("--prompt", help="Run a single prompt and exit.")
    args = parser.parse_args()

    print_header("Agent 1 - Simple Bot")

    if args.prompt:
        print(run_prompt(args.prompt))
        return

    while True:
        user_input = input("Enter (type 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        print(run_prompt(user_input))


if __name__ == "__main__":
    main()