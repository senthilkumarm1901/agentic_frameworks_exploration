import os
from dotenv import load_dotenv

load_dotenv()


def get_ollama_config() -> dict:
    return {
        "model": os.environ.get("OLLAMA_MODEL", "qwen3.5:35b-a3b-coding-nvfp4"),
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
    }
