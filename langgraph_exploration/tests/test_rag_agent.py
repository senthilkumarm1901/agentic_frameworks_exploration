import json
from urllib import error, request

import pytest

from lang_graph_exploration.agents.rag_agent import run_question
from lang_graph_exploration.config import get_settings
from lang_graph_exploration.rag.pipeline import build_vectorstore


def _require_rag_prerequisites() -> None:
    settings = get_settings()
    if not settings.pdf_path.exists():
        pytest.skip(f"RAG PDF is missing at {settings.pdf_path}")

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
        model_name
        for model_name in (settings.llm_model, settings.embed_model)
        if model_name not in available_names and model_name not in normalized_names
    ]
    if missing_models:
        pytest.skip(f"Missing required Ollama models: {', '.join(missing_models)}")


def test_build_vectorstore_when_pdf_is_missing_raises_actionable_file_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    missing_pdf = tmp_path / "missing-source.pdf"
    isolated_chroma_dir = tmp_path / "chroma"

    monkeypatch.setenv("PDF_PATH", str(missing_pdf))
    monkeypatch.setenv("CHROMA_DIR", str(isolated_chroma_dir))

    with pytest.raises(FileNotFoundError) as exc_info:
        build_vectorstore(rebuild=True)

    assert str(missing_pdf) in str(exc_info.value)
    assert "override PDF_PATH" in str(exc_info.value)


@pytest.mark.integration
def test_run_question_when_rag_dependencies_are_available_returns_grounded_answer() -> None:
    _require_rag_prerequisites()

    answer = run_question("How did Tesla perform in the 2024 stock market?")
    normalized_answer = answer.lower()

    assert answer != "No final answer was produced."
    assert answer.strip()
    assert "tesla" in normalized_answer
    assert "page" in normalized_answer or "source" in normalized_answer