from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    ollama_base_url: str
    llm_model: str
    embed_model: str
    temperature: float
    reasoning: bool
    pdf_path: Path
    chroma_dir: Path
    chroma_collection: str


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[2]
    return Settings(
        base_dir=base_dir,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        llm_model=os.getenv("OLLAMA_LLM_MODEL", "qwen3.5:35b-a3b-coding-nvfp4"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0")),
        reasoning=_as_bool(os.getenv("OLLAMA_REASONING"), default=False),
        pdf_path=(base_dir / os.getenv("PDF_PATH", "data/Stock_Market_Performance_2024.pdf")).resolve(),
        chroma_dir=(base_dir / os.getenv("CHROMA_DIR", "data/chroma_stock_market")).resolve(),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "stock_market"),
    )