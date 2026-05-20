import os
from dotenv import load_dotenv

load_dotenv()


def create_ollama_model():
    """Thin adapter: Strands -> Ollama via OpenAI-compatible endpoint."""
    from strands.models.openai import OpenAIModel

    model_name = os.environ.get("OLLAMA_MODEL", "qwen3.5:35b-a3b-coding-nvfp4")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    return OpenAIModel(
        client_args={
            "api_key": "ollama",
            "base_url": f"{base_url}/v1",
        },
        model_id=model_name,
    )
