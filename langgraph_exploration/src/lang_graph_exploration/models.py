from __future__ import annotations

from langchain_ollama import ChatOllama, OllamaEmbeddings

from lang_graph_exploration.config import get_settings


def create_chat_model() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
        reasoning=settings.reasoning,
    )


def create_embeddings() -> OllamaEmbeddings:
    settings = get_settings()
    return OllamaEmbeddings(
        model=settings.embed_model,
        base_url=settings.ollama_base_url,
    )