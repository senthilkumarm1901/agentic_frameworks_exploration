# Pattern 4: Agent with Memory and Interactive Chat

**Building on P3** — Adds conversation memory (short-term + long-term) and an interactive chat interface.

## What's New in Pattern 4

| Feature | P3 | P4 |
|---------|----|----|
| Interface | CLI `--question` | **Interactive chat REPL** |
| Short-term memory | ❌ | **✅ LangGraph MemorySaver** |
| Long-term memory | ❌ | **✅ LLM-generated summaries** |
| Multi-turn | ❌ | **✅** |
| Session persistence | ❌ | **✅ (survives restart)** |

> **P4 Metaphor:** The agent has **hands, eyes, a playbook, and a memory** (tools + retrieval + methodology + continuity).

## Memory Architecture

Pattern 4 uses a **dual-layer memory system** inspired by [Hermes](https://medium.com/@maclarensg_50191/how-hermes-agent-solves-the-context-window-problem-and-what-every-agent-builder-should-borrow-bf90071f4757):

### Short-Term Memory (In-Session)
- Implemented via LangGraph's `MemorySaver` checkpointer
- Stores full message history within the current session
- Uses `thread_id` for conversation threading

### Long-Term Memory (Across Sessions)
- LLM-generated structured summary
- Persisted to `memory_store/session.json`
- Injected into system prompt as a "frozen snapshot"
- Bounded to 1500 characters (forces curation over hoarding)

```
┌─────────────────────────────────────────────────────────┐
│  System Prompt                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ MEMORY BLOCK (from session.json)                    ││
│  │ - Topics Discussed                                  ││
│  │ - Key Facts Retrieved                               ││
│  │ - User Preferences                                  ││
│  │ - Last Interaction                                  ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  + TOOLS + SKILLS + RULES                               │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Start Interactive Chat
```bash
cd langgraph/agents/4_agent_with_memory_and_chat
uv sync
uv run python -m src.main
```

### Clear Memory and Start Fresh
```bash
uv run python -m src.main --reset
```

### Chat Commands
| Command | Description |
|---------|-------------|
| `quit` / `exit` / `q` | Exit and save session |
| `memory` | View current conversation summary |
| `clear` | Clear memory and start fresh |

## Example Session

```
══════════════════════════════════════════════════════════════
  🌍 Country Analysis Agent — Interactive Chat
  Tools: country_lookup · calculator · kb_search
  Skills: comparison · profile · regional · report
  📝 New session
══════════════════════════════════════════════════════════════
  Type 'quit' to exit · 'memory' to view summary · 'clear' to reset

  You: Compare India and Japan

  🤔 Thinking...
  📋 Activating skill: country-comparison
  🔍 country_lookup_tool(country="India", metric="gdp_trillion")
     → The gdp trillion of India is 3.55 trillion USD
  🔍 country_lookup_tool(country="Japan", metric="gdp_trillion")
     → The gdp trillion of Japan is 4.21 trillion USD
  ...

  💬 Answer:
  ## India vs Japan — Comparison
  
  | Metric | India | Japan |
  |--------|-------|-------|
  | GDP | $3.55T | $4.21T |
  | Population | 1,438.1M | 124.5M |
  ...

  ⏱ 18420ms · 4 LLM calls · 10 tool calls

  You: Now same for Brazil

  🤔 Thinking...
  [Agent uses memory to understand "same" means "compare with India"]
  ...

  You: memory

  ──────────────────────────────────────────────────
  📝 Memory (Turn 2):
  ## Conversation Summary
  
  ### Topics Discussed
  - Country comparison: India vs Japan
  - Country comparison: India vs Brazil
  ...
  ──────────────────────────────────────────────────
```

## Directory Structure

```
4_agent_with_memory_and_chat/
├── src/
│   ├── __init__.py
│   ├── main.py          # Terminal chat REPL entry point
│   ├── agent.py         # Agent with MemorySaver + summary
│   ├── prompts.py       # System prompt with memory injection
│   ├── memory.py        # Conversation summary manager
│   └── chat_ui.py       # Terminal display helpers
├── memory_store/
│   └── session.json     # Persisted summary (auto-created)
├── pyproject.toml
└── README.md
```

## Key Design Decisions

1. **Frozen Snapshot**: Memory is loaded once at session start and stays immutable during the turn. This prevents "memory hallucination" during tool use.

2. **Structured Summarization**: Uses a specific template (Topics, Facts, Preferences, Last Interaction) rather than open-ended summarization.

3. **Bounded Memory**: 1500 character limit forces the LLM to curate important information, not hoard everything.

4. **Dual-Layer System**: 
   - Short-term: LangGraph handles full message history
   - Long-term: LLM compression handles context limits

## The P1 → P4 Progression

> **P1:** The agent has hands (tools).  
> **P2:** The agent has hands and eyes (tools + retrieval).  
> **P3:** The agent has hands, eyes, and a playbook (+ methodology).  
> **P4:** The agent has hands, eyes, a playbook, and a memory (+ continuity).

Memory doesn't give the agent new capabilities — it gives it the ability to **build on what it already knows**.

## Available Tools

| Tool | Purpose | Source |
|------|---------|--------|
| `country_lookup_tool` | Get GDP, population, or area | MCP (from P1) |
| `calculator_tool` | Evaluate math expressions | MCP (from P1) |
| `country_kb_search_tool` | Semantic search over facts | MCP (from P2) |
| `activate_skill` | Load analysis methodology | Local (from P3) |

## Capabilities & Limitations

### ✅ What Pattern 4 Can Do (New)
- Multi-turn conversations with context
- Reference previous exchanges ("same for Brazil")
- Remember user preferences across sessions
- Persist conversation summaries across restarts

### ✅ What Pattern 4 Keeps from P1/P2/P3
- Quantitative lookups and calculations
- Qualitative knowledge base search
- Structured analysis via skills
- Professional output formatting

### ❌ What Pattern 4 Cannot Do
- Learn new skills dynamically
- Connect to external APIs
- Handle multiple concurrent users
- Provide real-time data

## Key Technical Details

- **Short-term Memory:** LangGraph `MemorySaver` with `thread_id`
- **Long-term Memory:** LLM-generated summaries to `session.json`
- **Memory Limit:** 1500 characters (bounded, like Hermes)
- **LLM:** Configurable via `OLLAMA_MODEL` env var
- **Inspired by:** [Hermes Agent's memory architecture](https://medium.com/@maclarensg_50191/how-hermes-agent-solves-the-context-window-problem-and-what-every-agent-builder-should-borrow-bf90071f4757)

---

## Progression Summary

| Pattern | Tools | Skills | Memory | Interface |
|---------|-------|--------|--------|-----------|
| P1 | 2 MCP | ❌ | ❌ | CLI `--question` |
| P2 | 3 MCP (+RAG) | ❌ | ❌ | CLI `--question` |
| P3 | 3 MCP + 1 local | 4 skills | ❌ | CLI `--question` |
| **P4** | 3 MCP + 1 local | 4 skills | **✅ Dual-layer** | **Interactive chat** |

---

## What Each Pattern Teaches

| Pattern | Key Learning |
|---------|--------------|
| P1 | Tool use via MCP protocol |
| P2 | RAG integration with vector databases |
| P3 | Skills as reusable methodology templates |
| P4 | Memory architecture for multi-turn conversations |
