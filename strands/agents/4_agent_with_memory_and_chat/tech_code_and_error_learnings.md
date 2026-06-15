# Tech, Code & Error Learnings — Strands Pattern 4

## Strands Short-Term Memory

**Pattern**: Reuse the same `Agent` instance across `agent(query)` calls.

Strands' `ConversationManager` appends each turn's messages to an internal list.
Calling `agent(query)` again sends the full accumulated history to the LLM.
No checkpointer or thread ID is needed — this is handled implicitly.

```python
# Correct: reuse the agent object
session.agent = Agent(model=..., tools=..., system_prompt=...)
result1 = session.agent("What is India's GDP?")
result2 = session.agent("Compare with Japan")  # has full history
```

## LLM Summarisation Without LangChain

In LangGraph Pattern 4, summarisation uses `await llm.ainvoke(prompt)` (LangChain ChatOllama).
In Strands, `OllamaModel` is called directly as a callable:

```python
summary_result = session.model(summarization_prompt)
summary_text = str(summary_result).strip()
```

`OllamaModel.__call__` returns an `AgentResult`-like object; `str()` gives the text.

## MCPClient Lifecycle in Long-Running Sessions

`MCPClient` must stay open for the entire chat session. Enter it once during
`ChatSession.initialize()` and exit on `ChatSession.close()`:

```python
self.mcp_client.__enter__()   # starts stdio subprocess
# ... many agent turns ...
self.mcp_client.__exit__(None, None, None)  # kills subprocess
```

Avoid using `with mcp_client:` in a per-turn function — it would kill and restart
the subprocess on every question (slow and error-prone).

## Frozen Snapshot Pattern

Long-term memory is injected at **session start only**. The system prompt is
fixed for the entire session; the live conversation history (short-term) provides
turn-level continuity. This prevents prompt bloat mid-session.

```
Session start:  load session.json → inject into system_prompt → create Agent
During session: Agent accumulates history in ConversationManager
After each turn: summarise → overwrite session.json
```

## gRPC ENHANCE_YOUR_CALM / too_many_pings

**Error:**
```
E0614 chttp2_transport.cc:1408] ipv4:127.0.0.1:65535: Received a GOAWAY with
error code ENHANCE_YOUR_CALM and debug data equal to "too_many_pings".
Current keepalive time (before throttling): 10000ms
```

**Cause:** Pattern 4 keeps `MCPClient` open for the whole session. The MCP
server connects to Milvus Lite (vector DB), which runs an embedded gRPC server.
During idle time between chat turns, the gRPC client sends keepalive pings.
Milvus Lite responds with `ENHANCE_YOUR_CALM` once the ping rate exceeds its
threshold, then throttles to 10 s intervals. The agent continues working normally.

**Why Pattern 3 doesn't show it:** MCPClient is opened/closed per-query, so the
gRPC connection never idles long enough to trigger the ping limit.

**Fix:** Set `GRPC_VERBOSITY=NONE` before the MCP subprocess is started so the
subprocess inherits it. The subprocess is where gRPC actually runs.

```python
os.environ.setdefault("GRPC_VERBOSITY", "NONE")  # must be before MCPClient
```

---

## `clear` vs `--reset`

- `--reset` CLI flag: clears `session.json` before the agent is created.
- `clear` chat command: calls `clear_summary()` then `session.reinitialize()`, which rebuilds the Agent with an empty memory block.

Both result in the same state: fresh Agent, empty system prompt memory block.
