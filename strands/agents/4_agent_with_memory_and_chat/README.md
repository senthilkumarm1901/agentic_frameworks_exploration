# Pattern 4: Agent with Memory and Chat — Strands

Interactive terminal chat agent with **two-tier conversation memory**, built with the [Strands Agents](https://github.com/strands-agents/sdk-python) framework.

## Architecture

```
graph LR
    subgraph CHAT["🖥️ Terminal Chat REPL"]
        USER["👤 User Input"]
        DISPLAY["📺 Chat Display\nskills · tools · answer"]
    end

    subgraph MEMORY["🧠 Memory Layer"]
        SHORT["Short-Term\nStrands ConversationManager\nfull message history\n(in-session)"]
        LONG["Long-Term Summary\nLLM-compressed\nstructured format"]
        DISK[("memory_store/session.json\npersists across restarts")]
        LONG --> DISK
    end

    subgraph AGENT["🤖 ReAct Agent"]
        PROMPT["System Prompt\n+ Memory Block\n+ Skill Metadata"]
        REACT["Strands Agent\n(reused across turns)"]
    end

    USER -->|"question"| REACT
    LONG -.->|"frozen snapshot"| PROMPT
    PROMPT --> REACT
    REACT --> SHORT
    SHORT -->|"after turn"| LONG

    REACT -->|"activate_skill()"| SK["📋 Skills"]
    REACT -->|"MCP stdio"| MCP["🔌 FastMCP\n(3 tools)"]

    REACT --> DISPLAY
```

## Memory Design

### Short-Term Memory (in-session)

Strands' `Agent` object manages conversation history internally via its `ConversationManager`. By **reusing the same `Agent` instance** across multiple `agent(query)` calls, the full message history accumulates automatically — no external checkpointer needed.

This is the Strands equivalent of LangGraph's `MemorySaver` + `thread_id`.

### Long-Term Memory (cross-session)

After every turn, the agent asks the LLM to compress the conversation into a structured summary (≤ 1500 chars) and writes it to `memory_store/session.json`.

On the next session start, the summary is loaded and injected as a **frozen snapshot** into the system prompt's `## MEMORY` block.

Template:
```
## Conversation Summary
### Topics Discussed     [max 5 bullets]
### Key Facts Retrieved  [max 5 bullets]
### User Preferences     [patterns observed]
### Last Interaction     [one sentence]
```

## Tools

| Tool | Source | Purpose |
|------|--------|---------|
| `country_lookup_tool` | MCP (shared server) | GDP, population, area lookups |
| `calculator_tool` | MCP (shared server) | Arithmetic / derived metrics |
| `country_kb_search_tool` | MCP (shared server) | Qualitative facts from knowledge base |
| `activate_skill` | Local Strands `@tool` | Load skill methodology from SKILL.md |

## Skills

Skills live in `skills/` (symlink → `../../../_shared/skills`).

| Skill | Use Case |
|-------|----------|
| `country-comparison` | Compare 2+ countries systematically |
| `country-profile` | Comprehensive single-country brief |
| `regional-analysis` | Regional grouping and aggregates |
| `report-formatting` | Format as professional markdown report |

## Usage

```bash
# First time — install environment
uv sync

# Start interactive chat
uv run python -m src.main

# Start fresh (clear saved memory)
uv run python -m src.main --reset
```

### Chat Commands

| Command | Effect |
|---------|--------|
| `quit` / `exit` / `q` | Exit chat (memory auto-saved) |
| `memory` | Display current long-term summary |
| `clear` | Wipe memory and restart session |

### Environment Variables

```bash
OLLAMA_MODEL=qwen3:8b          # Default model
OLLAMA_BASE_URL=http://localhost:11434
```

## File Structure

```
4_agent_with_memory_and_chat/
├── src/
│   ├── agent.py       # ChatSession, run_chat_turn, metrics extraction
│   ├── chat_ui.py     # ANSI terminal output helpers
│   ├── main.py        # CLI entry point + chat loop
│   ├── memory.py      # Load/save/format conversation summary
│   └── prompts.py     # System prompt with {memory_block} slot
├── memory_store/
│   └── session.json   # Persisted long-term summary
├── skills -> ../../../_shared/skills  (symlink)
├── logs.txt           # Per-turn JSON metrics
├── pyproject.toml
├── example_chat_interaction.md
└── tech_code_and_error_learnings.md
```

## Strands vs LangGraph — Memory Comparison

| Aspect | LangGraph Pattern 4 | Strands Pattern 4 |
|--------|--------------------|--------------------|
| Short-term | `MemorySaver` checkpointer + `thread_id` | Agent `ConversationManager` (implicit) |
| Long-term | LLM summarisation → `session.json` | LLM summarisation → `session.json` |
| System prompt | `build_system_prompt(memory_block)` | `build_system_prompt(memory_block)` |
| Skills | Local `@tool activate_skill` | Local `@tool activate_skill` |
| MCP tools | `MultiServerMCPClient` (async) | `MCPClient` + `stdio_client` (sync) |
| Chat loop | `asyncio.run(chat_loop())` | Synchronous `chat_loop()` |

## Pattern Progression

| Pattern | What's Added |
|---------|-------------|
| 1 | MCP tools only |
| 2 | + RAG MCP tool |
| 3 | + Skills (activate_skill) |
| **4** | **+ Two-tier memory + Interactive chat REPL** |
