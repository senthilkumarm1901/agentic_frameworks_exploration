"""Country knowledge base search using Milvus-Lite + sentence-transformers.

Indexes markdown fact files about countries and performs semantic search.
"""

from pathlib import Path
from typing import Optional

# Paths relative to this file
_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "country_kb"
_DB_PATH = Path(__file__).parent.parent.parent / "vector_db" / "country_kb.db"
_COLLECTION = "country_facts"
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_DIMENSION = 384

# Lazy-loaded singletons
_model: Optional["SentenceTransformer"] = None
_client: Optional["MilvusClient"] = None
_indexed: bool = False


def _get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _get_client():
    """Lazy-load the Milvus-Lite client."""
    global _client
    if _client is None:
        from pymilvus import MilvusClient
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _client = MilvusClient(str(_DB_PATH))
    return _client


def _ensure_indexed():
    """Index all country markdown files into Milvus-Lite (idempotent)."""
    global _indexed
    if _indexed:
        return

    client = _get_client()
    model = _get_model()

    # Create collection if not exists
    if not client.has_collection(_COLLECTION):
        client.create_collection(
            collection_name=_COLLECTION,
            dimension=_DIMENSION,
        )

        # Read and chunk all markdown files
        data = []
        doc_id = 0
        for md_file in sorted(_DATA_DIR.glob("*.md")):
            country_name = md_file.stem.replace("_", " ").title()
            content = md_file.read_text(encoding="utf-8")

            # Split by bullet points - each fact becomes one vector
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    fact = line[2:].strip()
                    embedding = model.encode(fact).tolist()
                    data.append({
                        "id": doc_id,
                        "vector": embedding,
                        "text": fact,
                        "country": country_name,
                        "source_file": md_file.name,
                    })
                    doc_id += 1

        if data:
            client.insert(collection_name=_COLLECTION, data=data)
            print(f"[country_kb_search] Indexed {len(data)} facts from {len(list(_DATA_DIR.glob('*.md')))} countries", flush=True)

    _indexed = True


def country_kb_search(query: str, top_k: int = 3) -> str:
    """Search the country knowledge base for relevant facts.

    Use this for qualitative information about countries - cultural facts,
    historical context, political systems, geographic features, or notable
    achievements. NOT for numeric data like GDP, population, or area.

    Args:
        query: Natural language question about countries
        top_k: Maximum number of results to return (default: 3)

    Returns:
        Formatted string with matching facts and country attribution
    """
    _ensure_indexed()

    model = _get_model()
    client = _get_client()

    query_embedding = model.encode(query).tolist()

    # Load collection into memory before search (required by Milvus)
    client.load_collection(_COLLECTION)

    results = client.search(
        collection_name=_COLLECTION,
        data=[query_embedding],
        limit=top_k,
        output_fields=["text", "country", "source_file"],
    )

    if not results or not results[0]:
        return f"No relevant facts found for: {query}"

    formatted = []
    for hit in results[0]:
        entity = hit["entity"]
        score = hit["distance"]
        formatted.append(
            f"[{entity['country']}] (relevance: {score:.3f}) {entity['text']}"
        )

    return "\n".join(formatted)


# For testing
if __name__ == "__main__":
    print(country_kb_search("What is unique about Japan's demographics?"))
    print("---")
    print(country_kb_search("Which country has the Amazon rainforest?"))
