# Pattern 5: Agent with Memory and LLM Wiki (No RAG)

**Building on P4** — Replaces vector RAG with a compiled LLM Wiki for deterministic, inspectable knowledge retrieval.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PATTERN 5 ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────┐     ┌──────────────────────────────┐     │
│  │   Terminal Chat REPL         │     │   Memory Layer               │     │
│  │   👤 User Input              │     │   Short-Term: MemorySaver    │     │
│  │   📺 Display                 │     │   Long-Term: session.json    │     │
│  └──────────────────────────────┘     └──────────────────────────────┘     │
│              │                                    │                         │
│              ▼                                    ▼                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    ReAct Agent (LangGraph)                         │    │
│  │   System Prompt + Memory Block + Skill Metadata                    │    │
│  │   checkpointer=MemorySaver (short-term message history)            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│              │                              │                               │
│              ▼                              ▼                               │
│  ┌─────────────────────┐        ┌─────────────────────────────────────┐    │
│  │   📋 Skills         │        │   FastMCP Server (4 tools)          │    │
│  │   (loaded on demand)│        │   🔍 country_lookup  🧮 calculator  │    │
│  │   4 skill files     │        │   📖 wiki_read      📑 wiki_index   │    │
│  └─────────────────────┘        └─────────────────────────────────────┘    │
│                                              │                              │
│                                              ▼                              │
│                        ┌─────────────────────────────────────────────┐     │
│                        │           📚 LLM Wiki                        │     │
│                        │   ┌───────────────────────────────────┐     │     │
│                        │   │ index.md (page catalog)           │     │     │
│                        │   └───────────────────────────────────┘     │     │
│                        │   ┌────────────┐  ┌────────────────────┐    │     │
│                        │   │ entities/  │  │ concepts/          │    │     │
│                        │   │ 20 country │  │ demographics.md    │    │     │
│                        │   │ pages      │  │ trade_economy.md   │    │     │
│                        │   │            │  │ geography.md       │    │     │
│                        │   └────────────┘  └────────────────────┘    │     │
│                        │   comparisons.md                            │     │
│                        └─────────────────────────────────────────────┘     │
│                                              ▲                              │
│                        ┌─────────────────────┴───────────────────────┐     │
│                        │        Raw Sources (immutable)              │     │
│                        │   country_kb/*.md    countries.json         │     │
│                        └─────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## What's Different from Pattern 4?

| Aspect | Pattern 4 | Pattern 5 |
|--------|-----------|-----------|
| Knowledge retrieval | Milvus vector RAG | LLM Wiki (markdown) |
| Retrieval tool | `kb_search` (semantic) | `wiki_read` (exact + fuzzy) |
| Dependencies | sentence-transformers, pymilvus | None (pure markdown) |
| Compilation | Runtime embedding | One-time LLM generation |
| Inspectability | Opaque vectors | Human-readable pages |
| Discovery | Embedding similarity | Index + keyword matching |

## Why Replace RAG?

1. **Determinism** — Same query → same page (no embedding drift)
2. **Inspectability** — Read wiki pages directly to debug
3. **No ML dependencies** — Faster startup, smaller footprint
4. **Offline-first** — Works without embedding model
5. **Editable** — Human or LLM can update wiki content
6. **Lazy loading** — Files read on demand, no pre-compilation

## Getting Started

### 1. Run the Chat

```bash
cd langgraph/agents/5_agent_with_memory_and_chat_no_rag
uv sync
uv run python -m src.main
```

No wiki compilation needed — pages load directly from `_shared/data/country_kb/`.

### 2. Commands

| Command | Action |
|---------|--------|
| `quit` | Exit and save session |
| `memory` | View conversation summary |
| `clear` | Reset memory |
| `--reset` | Start fresh on launch |

## Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `country_lookup_tool` | Numeric data (GDP, population, area) | `country_lookup("Japan", "gdp_trillion")` |
| `calculator_tool` | Math expressions | `calculator("25.46 / 1.42")` |
| `wiki_read_tool` | Read wiki pages | `wiki_read("japan")`, `wiki_read("demographics")` |
| `wiki_index_tool` | List available pages | `wiki_index()` |

## Wiki Structure

Lazy loading from existing files:

```
_shared/data/
├── llm_wiki/
│   └── index.md              # Keyword → file mapping
└── country_kb/               # 20 country pages (raw source)
    ├── japan.md
    ├── india.md
    └── ...
```

The `wiki_read` tool:
1. Checks exact country name → `country_kb/{name}.md`
2. Keyword match via index → returns matching pages
3. Fuzzy match for typos → `"japn"` → `japan.md`

## Memory Architecture

Same dual-layer memory as Pattern 4:

- **Short-term**: `MemorySaver` keeps full message history within session
- **Long-term**: LLM-generated summaries persisted to `session.json`
- **Bounded**: 1500 character limit forces curation

## Progression Summary

| Pattern | Focus | Key Addition |
|---------|-------|--------------|
| P1 | Foundation | MCP tools (lookup, calculator) |
| P2 | Knowledge | + RAG tool (Milvus semantic search) |
| P3 | Methodology | + Skills layer (structured prompts) |
| P4 | Continuity | + Dual-layer memory (MemorySaver + session.json) |
| **P5** | **Determinism** | **Replace RAG → LLM Wiki (inspectable, no ML deps)** |

## Files

```
5_agent_with_memory_and_chat_no_rag/
├── src/
│   ├── __init__.py
│   ├── agent.py          # ReAct agent with MCP + skills + memory
│   ├── main.py           # Terminal REPL entry point
│   ├── memory.py         # Hermes-inspired summary manager
│   ├── prompts.py        # System prompt with wiki tool instructions
│   └── chat_ui.py        # Colored terminal output
├── memory_store/         # Long-term memory persistence
├── skills -> _shared/skills/
├── logs.txt              # Turn metrics (JSON)
├── pyproject.toml        # No RAG dependencies
└── README.md
```
