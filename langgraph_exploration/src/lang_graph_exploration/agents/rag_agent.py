from __future__ import annotations

import argparse

from langchain_core.messages import AIMessage, HumanMessage

from lang_graph_exploration.cli import print_header
from lang_graph_exploration.config import get_settings
from lang_graph_exploration.rag.pipeline import build_rag_agent, build_vectorstore


def run_question(question: str, rebuild: bool = False, verbose: bool = False) -> str:
    vectorstore = build_vectorstore(rebuild=rebuild, verbose=verbose)
    agent = build_rag_agent(vectorstore, verbose=verbose)
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    last_ai = next(
        (message for message in reversed(result["messages"]) if isinstance(message, AIMessage)),
        None,
    )
    return last_ai.content if last_ai is not None else "No final answer was produced."


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 5 - RAG")
    parser.add_argument("--question", help="Run a single question and exit.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the Chroma index from the PDF.")
    parser.add_argument("--verbose", action="store_true", help="Print retrieval and tool-calling diagnostics.")
    args = parser.parse_args()

    settings = get_settings()
    print_header("Agent 5 - RAG Agent")
    print(f"Using LLM: {settings.llm_model} | Embeddings: {settings.embed_model}")
    if args.verbose:
        print(f"PDF path: {settings.pdf_path}")
        print(f"Chroma dir: {settings.chroma_dir}")
        print(f"Collection: {settings.chroma_collection}")

    if args.question:
        print(run_question(args.question, rebuild=args.rebuild, verbose=args.verbose))
        return

    while True:
        user_input = input("What is your question (type 'exit' to quit): ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        print(run_question(user_input, rebuild=args.rebuild, verbose=args.verbose))


if __name__ == "__main__":
    main()