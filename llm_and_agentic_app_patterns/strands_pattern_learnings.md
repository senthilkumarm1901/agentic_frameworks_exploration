**1) Pattern 1 — Agent wraps the loop; MCP opened via context manager**

```mermaid
flowchart TD
    A["run_agent(user_query)"] --> B["MCPClient(stdio_client factory)
    pattern1_server.py"]
    B --> C["with mcp_client:
    list_tools_sync()"]
    C --> D["Agent(model, tools, system_prompt)
    Strands builds ReAct loop internally"]
    D --> E["agent(user_query)
    ── single call ──"]
    E --> F["Strands ConversationManager
    LLM + tool dispatch loop (hidden)"]
    F --> G["result.metrics / result.message"]
    G -->|answer empty| H["Fallback: Agent(tools=[])
    synthesis call"]
    H --> I["return result dict"]
    G -->|answer present| I
```

```python
# callback_handler=None suppresses streaming; answer extracted from nested
# result.message["content"] list; fallback synthesis Agent for empty answers
with mcp_client:
    agent = Agent(model=model, tools=mcp_client.list_tools_sync(),
                  system_prompt=SYSTEM_PROMPT, callback_handler=None)
    result = agent(user_query)
    answer = _extract_answer(result)    # walks result.message["content"] list

    if not answer.strip() and tool_calls_detail:
        # Fallback: new tool-free Agent to synthesise from tool evidence
        synthesis_agent = Agent(model=model, tools=[], system_prompt="...", callback_handler=None)
        answer = _extract_answer(synthesis_agent(fallback_prompt))
        llm_calls += 1
```

---

**2) Pattern 2 — same Agent call; sys.executable for venv-compat MCP launch**

```mermaid
flowchart TD
    A["run_agent(user_query)"] --> B["MCPClient(sys.executable, pattern2_server.py)
    venv python — has pymilvus/sentence-transformers"]
    B --> C["with mcp_client:
    list_tools_sync()
    country_lookup · calculator · country_kb_search"]
    C --> D["Agent(model, tools, system_prompt)"]
    D --> E["agent(user_query)
    ── single call ──"]
    E --> F["Strands ConversationManager
    routes all 3 tools uniformly"]
    F --> G["return result dict"]
```

```python
# sys.executable (not "python") so the .venv with pymilvus/sentence-transformers is used
mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command=sys.executable, args=[str(_MCP_SERVER_PATH)])))
# loop body identical to P1; country_kb_search_tool performs Milvus vector search
```

---

**3) Pattern 3 — `@tool` decorator unifies local fn + MCP; no dispatch branch**

```mermaid
flowchart TD
    A["run_agent(user_query)"] --> B["MCPClient(sys.executable, pattern2_server.py)"]
    B --> C["mcp_tools = list_tools_sync()"]
    C --> D["@tool activate_skill
    local Python fn — reads SKILL.md
    decorated as first-class Strands tool"]
    D --> E["all_tools = mcp_tools + [activate_skill]"]
    E --> F["Agent(model, all_tools, system_prompt)"]
    F --> G["agent(user_query)
    ── single call ──"]
    G --> H["Strands routes MCP tools and
    activate_skill uniformly — no if/else"]
    H --> I["return result dict"]
```

```python
# @tool-decorated local fn joins MCP tools as a peer — Strands dispatches both
# contrast with Hermes P3 which needed an explicit if fn_name == "activate_skill" branch
with mcp_client:
    mcp_tools = mcp_client.list_tools_sync()
    all_tools = mcp_tools + [activate_skill]           # activate_skill is @tool decorated
    agent = Agent(model=model, tools=all_tools, system_prompt=SYSTEM_PROMPT, callback_handler=None)
    result = agent(user_query)
    skill_activations = tools_used.count("activate_skill")   # counted post-hoc from metrics
```

---

**4) Pattern 4 — reused Agent = free short-term memory; explicit long-term summary**

```mermaid
flowchart TD
    INIT["ChatSession.initialize()
    (once per process)"] --> LM["load_summary() → format_memory_block()
    inject frozen summary into system prompt"]
    LM --> MC["mcp_client.__enter__()
    persistent MCP connection"]
    MC --> AG["Agent(model, all_tools, system_prompt)
    created ONCE — reused across turns"]

    AG --> T["run_chat_turn(session, user_query)
    per turn"]
    T --> R["session.agent(user_query)
    ConversationManager accumulates history
    — no self.messages list needed —"]
    R --> S["session.model(summarization_prompt)
    direct OllamaModel call — no tools"]
    S --> SV["save_summary() → session.json"]
    SV --> RET["return result dict"]
```

```python
# --- Session init (once) ---
summary_data = load_summary()                                   # reads session.json
system_prompt = build_system_prompt(format_memory_block(summary_data))
self.mcp_client.__enter__()                                     # persistent MCP connection
mcp_tools = self.mcp_client.list_tools_sync()
self.agent = Agent(model=self.model, tools=mcp_tools + [activate_skill],
                   system_prompt=system_prompt)                 # created once

# --- Each turn ---
# Agent reuse = short-term memory for free via Strands ConversationManager
# (contrast with Hermes P4 which manually appends to self.messages each turn)
result = session.agent(user_query)

# --- After turn: manual LLM summarization for cross-session persistence ---
# Strands has no built-in cross-session memory — this part is always manual
summary_result = session.model(summarization_prompt)   # OllamaModel called directly
save_summary(_extract_answer(summary_result), session.turn_count)   # writes session.json
```
