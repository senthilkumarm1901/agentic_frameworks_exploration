from pathlib import Path

from langchain_core.messages import AIMessage

from lang_graph_exploration.agents.drafter_agent import execute_tools


def test_save_uses_latest_draft_content(tmp_path: Path) -> None:
    output_path = tmp_path / "draft.txt"
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "save",
                        "args": {"filename": str(output_path)},
                        "id": "tool-call-1",
                        "type": "tool_call",
                    }
                ],
            )
        ],
        "document_content": "",
        "draft_content": "Generated draft content",
        "saved_path": None,
        "finished": False,
    }

    result = execute_tools(state)

    assert output_path.read_text(encoding="utf-8") == "Generated draft content"
    assert result["document_content"] == "Generated draft content"
    assert result["saved_path"] == str(output_path)