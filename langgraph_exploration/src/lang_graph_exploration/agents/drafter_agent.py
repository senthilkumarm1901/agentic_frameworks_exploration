from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.cli import print_header
from lang_graph_exploration.config import get_settings
from lang_graph_exploration.models import create_chat_model


class AgentState(TypedDict):
    messages: list[BaseMessage]
    document_content: str
    draft_content: str
    saved_path: str | None
    finished: bool


@tool
def update(content: str) -> str:
    """Update the current document with the complete new content."""
    return content


@tool
def save(filename: str) -> str:
    """Persist the current document to a text file using the provided filename."""
    return filename


TOOLS = [update, save]
TOOLS_BY_NAME = {tool_.name: tool_ for tool_ in TOOLS}
model = create_chat_model().bind_tools(TOOLS)


def call_model(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(
        content=(
            "You are Drafter, a writing assistant. Use the 'update' tool whenever you want to replace the entire document. "
            "Use the 'save' tool only when the user explicitly asks to save or finish. "
            f"Current document content:\n{state['document_content'] or '[empty document]'}"
        )
    )
    response = model.invoke([system_prompt] + state["messages"])
    draft_content = state["draft_content"]
    if response.content and not response.tool_calls:
        draft_content = response.content
    return {
        "messages": state["messages"] + [response],
        "document_content": state["document_content"],
        "draft_content": draft_content,
        "saved_path": state["saved_path"],
        "finished": state["finished"],
    }


def execute_tools(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return state

    document_content = state["document_content"]
    draft_content = state["draft_content"]
    saved_path = state["saved_path"]
    finished = state["finished"]
    tool_messages: list[ToolMessage] = []
    base_dir = get_settings().base_dir

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})

        if tool_name == "update":
            document_content = str(TOOLS_BY_NAME[tool_name].invoke(tool_args))
            draft_content = document_content
            result = f"Document updated successfully. Current content:\n{document_content}"
        elif tool_name == "save":
            file_name = str(TOOLS_BY_NAME[tool_name].invoke(tool_args))
            output_path = Path(file_name)
            if not output_path.is_absolute():
                output_path = base_dir / output_path
            if output_path.suffix != ".txt":
                output_path = output_path.with_suffix(".txt")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            content_to_save = document_content or draft_content
            output_path.write_text(content_to_save, encoding="utf-8")
            document_content = content_to_save
            draft_content = content_to_save
            saved_path = str(output_path)
            finished = True
            result = f"Document saved successfully to {output_path}"
        else:
            result = f"Unknown tool: {tool_name}"

        tool_messages.append(
            ToolMessage(content=result, tool_call_id=tool_call["id"], name=tool_name)
        )

    return {
        "messages": state["messages"] + tool_messages,
        "document_content": document_content,
        "draft_content": draft_content,
        "saved_path": saved_path,
        "finished": finished,
    }


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


def after_tools(state: AgentState) -> Literal["agent", "end"]:
    if state["finished"]:
        return "end"
    return "agent"


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
    graph.add_conditional_edges(
        "tools",
        after_tools,
        {"agent": "agent", "end": END},
    )
    return graph.compile()


def invoke_once(state: AgentState, prompt: str) -> AgentState:
    app = build_agent()
    next_state = {
        "messages": state["messages"] + [HumanMessage(content=prompt)],
        "document_content": state["document_content"],
        "draft_content": state["draft_content"],
        "saved_path": state["saved_path"],
        "finished": state["finished"],
    }
    return app.invoke(next_state)


def print_new_messages(before_count: int, state: AgentState) -> None:
    for message in state["messages"][before_count:]:
        if isinstance(message, AIMessage) and message.content:
            print(f"AI: {message.content}")
        elif isinstance(message, ToolMessage):
            print(f"TOOL {message.name}: {message.content}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 4 - Drafter")
    parser.add_argument("--prompt", help="Initial prompt for a non-interactive draft run.")
    parser.add_argument("--save-as", help="Optional follow-up save filename for non-interactive mode.")
    args = parser.parse_args()

    print_header("Agent 4 - Drafter Agent")
    state: AgentState = {
        "messages": [],
        "document_content": "",
        "draft_content": "",
        "saved_path": None,
        "finished": False,
    }

    if args.prompt:
        before = len(state["messages"])
        state = invoke_once(state, args.prompt)
        print_new_messages(before, state)
        if args.save_as and not state["finished"]:
            before = len(state["messages"])
            state = invoke_once(state, f"Save the document as {args.save_as}")
            print_new_messages(before, state)
        if state["saved_path"]:
            print(f"Saved to {state['saved_path']}")
        return

    while True:
        user_input = input("What would you like to do with the document? (type 'exit' to quit): ").strip()
        if user_input.lower() == "exit":
            break
        before = len(state["messages"])
        state = invoke_once(state, user_input)
        print_new_messages(before, state)
        if state["saved_path"]:
            print(f"Saved to {state['saved_path']}")


if __name__ == "__main__":
    main()