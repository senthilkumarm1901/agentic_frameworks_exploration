from __future__ import annotations

import argparse
from typing import Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.cli import print_header
from lang_graph_exploration.models import create_chat_model


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@tool
def subtract(a: int, b: int) -> int:
    """Subtract two integers."""
    return a - b


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


TOOLS = [add, subtract, multiply]
TOOLS_BY_NAME = {tool_.name: tool_ for tool_ in TOOLS}
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are a ReAct-style assistant. Use the available arithmetic tools when a calculation is needed. "
        "After you receive tool results, provide a concise final answer to the user."
    )
)


class AgentState(TypedDict):
    messages: list[BaseMessage]


model = create_chat_model().bind_tools(TOOLS)


def call_model(state: AgentState) -> AgentState:
    response = model.invoke([SYSTEM_PROMPT] + state["messages"])
    return {"messages": state["messages"] + [response]}


def execute_tools(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return state

    tool_messages: list[ToolMessage] = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        result = TOOLS_BY_NAME[tool_name].invoke(tool_args)
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        )

    return {"messages": state["messages"] + tool_messages}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", execute_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    return graph.compile()


def print_trace(messages: list[BaseMessage], seen: int) -> int:
    for message in messages[seen:]:
        if isinstance(message, HumanMessage):
            print(f"USER: {message.content}")
        elif isinstance(message, AIMessage):
            if message.tool_calls:
                print(f"AI requested tools: {message.tool_calls}")
            elif message.content:
                print(f"AI: {message.content}")
        elif isinstance(message, ToolMessage):
            print(f"TOOL {message.name}: {message.content}")
    return len(messages)


def run_prompt(prompt: str) -> list[BaseMessage]:
    app = build_agent()
    seen = 0
    final_messages: list[BaseMessage] = []
    for step in app.stream({"messages": [HumanMessage(content=prompt)]}, stream_mode="values"):
        final_messages = step["messages"]
        seen = print_trace(final_messages, seen)
    return final_messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 3 - ReAct arithmetic agent")
    parser.add_argument("--prompt", help="Run a single prompt and exit.")
    args = parser.parse_args()

    print_header("Agent 3 - ReAct Agent")

    if args.prompt:
        run_prompt(args.prompt)
        return

    while True:
        user_input = input("Enter (type 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        run_prompt(user_input)


if __name__ == "__main__":
    main()