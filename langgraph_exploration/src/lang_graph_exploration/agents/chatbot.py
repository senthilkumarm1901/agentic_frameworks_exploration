from __future__ import annotations

import argparse
from pathlib import Path
from typing import TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.cli import print_header
from lang_graph_exploration.models import create_chat_model


class AgentState(TypedDict):
    messages: list[BaseMessage]


llm = create_chat_model()


def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    state["messages"].append(AIMessage(content=response.content))
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("process", process)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)
    return graph.compile()


def save_conversation(messages: list[BaseMessage], log_file: Path) -> None:
    with log_file.open("w", encoding="utf-8") as handle:
        handle.write("Your Conversation Log:\n")
        for message in messages:
            if isinstance(message, HumanMessage):
                handle.write(f"You: {message.content}\n")
            elif isinstance(message, AIMessage):
                handle.write(f"AI: {message.content}\n\n")
        handle.write("End of Conversation\n")


def run_prompts(prompts: list[str], log_file: Path) -> list[BaseMessage]:
    agent = build_agent()
    conversation_history: list[BaseMessage] = []
    for prompt in prompts:
        conversation_history.append(HumanMessage(content=prompt))
        result = agent.invoke({"messages": conversation_history})
        conversation_history = result["messages"]
    save_conversation(conversation_history, log_file)
    return conversation_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 2 - Chatbot")
    parser.add_argument("--prompts", nargs="*", help="Run prompts non-interactively and exit.")
    parser.add_argument("--log-file", default="logging.txt", help="Conversation log path.")
    args = parser.parse_args()

    print_header("Agent 2 - Chatbot")
    log_file = Path(args.log_file)

    if args.prompts:
        messages = run_prompts(args.prompts, log_file)
        final_ai = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if final_ai is not None:
            print(final_ai.content)
        print(f"Conversation saved to {log_file}")
        return

    prompts: list[str] = []
    while True:
        user_input = input("Enter (type 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        prompts.append(user_input)
        messages = run_prompts(prompts, log_file)
        final_ai = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if final_ai is not None:
            print(final_ai.content)


if __name__ == "__main__":
    main()