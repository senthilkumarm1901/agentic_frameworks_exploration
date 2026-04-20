import json
from urllib import error, request

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from lang_graph_exploration.agents.react_agent import execute_tools, run_prompt, should_continue
from lang_graph_exploration.config import get_settings


def _require_ollama_models(*required_models: str) -> None:
    settings = get_settings()
    try:
        with request.urlopen(f"{settings.ollama_base_url}/api/tags", timeout=5) as response:
            payload = json.load(response)
    except error.URLError as exc:
        pytest.skip(f"Ollama is not reachable at {settings.ollama_base_url}: {exc}")

    available_names = {model.get("name", "") for model in payload.get("models", [])}
    normalized_names = {
        name.removesuffix(":latest") if name.endswith(":latest") else name
        for name in available_names
    }
    missing_models = [
        model_name for model_name in required_models if model_name not in available_names and model_name not in normalized_names
    ]
    if missing_models:
        pytest.skip(f"Missing required Ollama models: {', '.join(missing_models)}")


def test_execute_tools_when_ai_message_has_multiple_tool_calls_appends_results() -> None:
    state = {
        "messages": [
            HumanMessage(content="Calculate a few things."),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "add",
                        "args": {"a": 40, "b": 12},
                        "id": "tool-call-1",
                        "type": "tool_call",
                    },
                    {
                        "name": "multiply",
                        "args": {"a": 52, "b": 6},
                        "id": "tool-call-2",
                        "type": "tool_call",
                    },
                ],
            ),
        ]
    }

    result = execute_tools(state)
    tool_messages = [message for message in result["messages"] if isinstance(message, ToolMessage)]

    assert should_continue(state) == "tools"
    assert len(tool_messages) == 2
    assert [message.name for message in tool_messages] == ["add", "multiply"]
    assert [message.content for message in tool_messages] == ["52", "312"]
    assert [message.tool_call_id for message in tool_messages] == ["tool-call-1", "tool-call-2"]
    assert isinstance(result["messages"][0], HumanMessage)


@pytest.mark.integration
def test_run_prompt_when_ollama_is_available_returns_tool_backed_final_answer() -> None:
    settings = get_settings()
    _require_ollama_models(settings.llm_model)

    messages = run_prompt("Add 40 + 12 and then multiply the result by 6.")

    tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
    final_ai = next(
        (
            message
            for message in reversed(messages)
            if isinstance(message, AIMessage) and not message.tool_calls and bool(message.content.strip())
        ),
        None,
    )

    assert any(isinstance(message, HumanMessage) for message in messages)
    assert tool_messages
    assert final_ai is not None
    assert "312" in final_ai.content