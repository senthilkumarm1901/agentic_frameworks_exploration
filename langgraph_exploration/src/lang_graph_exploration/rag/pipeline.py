from __future__ import annotations

import shutil
from typing import TypedDict

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph

from lang_graph_exploration.config import get_settings
from lang_graph_exploration.models import create_chat_model, create_embeddings


class RAGState(TypedDict):
    messages: list[BaseMessage]


def _emit_verbose(enabled: bool, message: str) -> None:
    if enabled:
        print(f"[rag] {message}")


def build_vectorstore(rebuild: bool = False, verbose: bool = False) -> Chroma:
    settings = get_settings()
    if rebuild and settings.chroma_dir.exists():
        _emit_verbose(verbose, f"Removing existing Chroma directory: {settings.chroma_dir}")
        shutil.rmtree(settings.chroma_dir)

    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    embeddings = create_embeddings()

    if not settings.pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found at {settings.pdf_path}. Place the document there or override PDF_PATH in .env."
        )

    if any(settings.chroma_dir.iterdir()) and not rebuild:
        _emit_verbose(verbose, f"Using existing Chroma index from: {settings.chroma_dir}")
        return Chroma(
            persist_directory=str(settings.chroma_dir),
            collection_name=settings.chroma_collection,
            embedding_function=embeddings,
        )

    _emit_verbose(verbose, f"Loading PDF from: {settings.pdf_path}")
    pages = PyPDFLoader(str(settings.pdf_path)).load()
    _emit_verbose(verbose, f"Loaded {len(pages)} page(s) from PDF")
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(pages)
    _emit_verbose(verbose, f"Split PDF into {len(chunks)} chunk(s)")
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(settings.chroma_dir),
        collection_name=settings.chroma_collection,
    )


def create_retriever_tool(vectorstore: Chroma, verbose: bool = False):
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    @tool
    def retriever_tool(query: str) -> str:
        """Search the indexed stock market PDF and return the most relevant chunks."""
        _emit_verbose(verbose, f"Retriever query: {query}")
        docs = retriever.invoke(query)
        if not docs:
            _emit_verbose(verbose, "Retriever returned no documents")
            return "No relevant passages were found in the indexed PDF."

        lines: list[str] = []
        for index, doc in enumerate(docs, start=1):
            metadata = doc.metadata or {}
            page = metadata.get("page", "N/A")
            source = metadata.get("source", "PDF")
            preview = " ".join(doc.page_content.split())[:220]
            _emit_verbose(verbose, f"Retrieved doc {index}: source={source} page={page} preview={preview}")
            lines.append(
                f"Doc {index} | source: {source} | page: {page}\n{doc.page_content}"
            )
        return "\n\n".join(lines)

    return retriever_tool


def build_rag_agent(vectorstore: Chroma, verbose: bool = False):
    retriever_tool = create_retriever_tool(vectorstore, verbose=verbose)
    tools = [retriever_tool]
    tools_by_name = {tool_.name: tool_ for tool_ in tools}
    model = create_chat_model().bind_tools(tools)
    system_prompt = SystemMessage(
        content=(
            "You answer questions about the Stock Market Performance 2024 PDF. "
            "Use the retriever tool when document lookup is needed. "
            "Cite the retrieved document and page identifiers in your final answer. "
            "If the PDF does not support the answer, say so explicitly."
        )
    )

    def call_model(state: RAGState) -> RAGState:
        response = model.invoke([system_prompt] + state["messages"])
        _emit_verbose(verbose, f"Model response: {response.content}")
        if response.tool_calls:
            _emit_verbose(verbose, f"Model issued {len(response.tool_calls)} tool call(s): {response.tool_calls}")
        return {"messages": state["messages"] + [response]}

    def execute_tools(state: RAGState) -> RAGState:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return state

        tool_messages: list[ToolMessage] = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            _emit_verbose(verbose, f"Executing tool '{tool_name}' with args: {tool_args}")
            result = tools_by_name[tool_name].invoke(tool_args)
            _emit_verbose(verbose, f"Tool '{tool_name}' result length: {len(str(result))}")
            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )
        return {"messages": state["messages"] + tool_messages}

    def should_continue(state: RAGState) -> bool:
        last_message = state["messages"][-1]
        return isinstance(last_message, AIMessage) and bool(last_message.tool_calls)

    graph = StateGraph(RAGState)
    graph.add_node("llm", call_model)
    graph.add_node("tools", execute_tools)
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", should_continue, {True: "tools", False: END})
    graph.add_edge("tools", "llm")
    return graph.compile()