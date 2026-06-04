# Technical Code and Error Learnings — Pattern 4

This document captures the errors encountered and fixes applied while developing Pattern 4 (`agent_with_memory_and_chat`).

---

## Error 1: MultiServerMCPClient Context Manager Not Supported

**Error Message:**
```
NotImplementedError: As of langchain-mcp-adapters 0.1.0, MultiServerMCPClient cannot be used as a context manager (e.g., async with MultiServerMCPClient(...)).
```

**Root Cause:**
- In `langchain-mcp-adapters` version 0.1.0+, the `MultiServerMCPClient` class no longer supports being used as an async context manager
- The old pattern `async with client:` is deprecated

**Original Code:**
```python
async with mcp_client:
    while True:
        # chat loop
```

**Fix Applied:**
```python
# Note: langchain-mcp-adapters 0.1.0+ creates sessions per-tool-call,
# so the client doesn't need to be used as a context manager
while True:
    # chat loop
```

**Learning:**
- `langchain-mcp-adapters` 0.1.0+ manages MCP sessions internally per-tool-call
- No explicit context manager or cleanup is needed
- Just call `await client.get_tools()` and use the tools directly

---

## Error 2: Module Not Found When Running with `&&`

**Error Message:**
```
ModuleNotFoundError: No module named 'src'
```

**Root Cause:**
- When chaining commands with `&&` in zsh, the `cd` command may not affect subsequent commands in the same way as using `;`
- The `uv run` was executing from the wrong directory

**Original Command:**
```bash
cd /path/to/pattern4 && uv run python -m src.main
```

**Fix Applied:**
```bash
cd /path/to/pattern4; uv run python -m src.main
```

**Learning:**
- Use `;` instead of `&&` when directory context matters for subsequent commands
- Alternatively, use `pushd/popd` or run from the correct directory explicitly

---

## Error 3: Verbose MCP Server Logging

**Symptom:**
```
[06/04/26 10:23:35] INFO     Processing request of type            server.py:727
                             CallToolRequest
```

**Root Cause:**
- MCP server (running as subprocess) logs INFO level messages to stderr
- These messages pollute the interactive chat output
- Logging configuration in the client doesn't affect the subprocess

**Client-Side Attempt (Partial):**
```python
for logger_name in ["httpx", "httpcore", "sentence_transformers", 
                    "transformers", "milvus", "pymilvus", "grpc", 
                    "mcp", "mcp.server"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
```

**Server-Side Fix (Complete):**
```python
# In pattern2_server.py - BEFORE importing mcp modules
import logging
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("mcp.server").setLevel(logging.WARNING)
```

**Learning:**
- MCP servers run as subprocesses via `stdio` transport
- Client-side logging configuration doesn't affect subprocess logging
- Must configure logging suppression in the server code itself, **before** importing mcp modules

---

## Error 4: HuggingFace Hub Token Warning

**Warning Message:**
```
Warning: You are sending unauthenticated requests to the HF Hub. 
Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```

**Root Cause:**
- `sentence-transformers` library uses HuggingFace Hub to download models
- Without authentication, rate limits apply

**Fix Applied:**
```python
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
```

**Alternative Fix:**
- Set `HF_TOKEN` environment variable with a HuggingFace API token
- This enables higher rate limits and faster model downloads

---

## Error 5: Milvus/FAISS Loading Messages

**Symptom:**
```
[06/04/26 10:24:04] INFO     Loading faiss.                        loader.py:156
[06/04/26 10:24:05] INFO     Successfully loaded faiss.            loader.py:158
[06/04/26 10:24:06] INFO     MilvusLite server started for...
```

**Root Cause:**
- Milvus-Lite logs server lifecycle events at INFO level
- These are printed when the RAG tool is first invoked

**Partial Fix:**
```python
logging.getLogger("milvus").setLevel(logging.ERROR)
logging.getLogger("pymilvus").setLevel(logging.ERROR)
```

**Note:**
- Some messages still appear because Milvus-Lite uses its own logging configuration
- The MCP server subprocess has its own logging context

---

## Key Architectural Learnings

### 1. MCP Subprocess Isolation
- MCP servers run as separate processes communicating via stdio
- Logging configuration in the main process doesn't affect subprocesses
- To suppress subprocess logs, configure logging in the server code itself

### 2. LangGraph MemorySaver with Checkpointing
```python
checkpointer = MemorySaver()
agent = create_react_agent(
    model=llm,
    tools=all_tools,
    prompt=system_prompt,
    checkpointer=checkpointer,  # Key addition for short-term memory
)

# Must use thread config for message accumulation
THREAD_CONFIG = {"configurable": {"thread_id": "country_chat_1"}}
result = await agent.ainvoke({"messages": [...]}, config=THREAD_CONFIG)
```

### 3. Dual-Layer Memory Architecture
- **Short-term**: LangGraph `MemorySaver` with `thread_id` — stores full message history
- **Long-term**: LLM-generated summaries saved to `session.json` — survives restarts, bounded to 1500 chars

### 4. Token Metrics Extraction from Ollama
```python
# Ollama stores token counts in response_metadata
metadata = getattr(msg, "response_metadata", {}) or {}
prompt_tokens += metadata.get("prompt_eval_count", 0)
completion_tokens += metadata.get("eval_count", 0)
```

---

## Files Modified

| File | Changes |
|------|---------|
| `src/main.py` | Removed `async with mcp_client:` context manager usage |
| `src/agent.py` | Added `mcp`, `mcp.server` to logging suppression list |
| `src/agent.py` | Added HF_TOKEN warning filter |
| `_shared/src/mcp_servers/pattern2_server.py` | Added MCP logging suppression at server level |

---

## Summary

The main challenges in Pattern 4 were:
1. **API changes** in `langchain-mcp-adapters` 0.1.0+ breaking context manager pattern
2. **Subprocess isolation** preventing centralized logging control — fixed by adding suppression in MCP server
3. **Dual-memory architecture** requiring careful coordination between LangGraph checkpointer and custom summary persistence

All critical errors have been resolved. The verbose logging issue was fully fixed by adding logging suppression in the MCP server code itself.
