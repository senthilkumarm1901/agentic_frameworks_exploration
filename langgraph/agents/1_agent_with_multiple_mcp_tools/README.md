# Pattern 1: Agent with Multiple MCP Tools

**The Foundation** — A LangGraph ReAct agent that uses MCP (Model Context Protocol) to access external tools.

## Overview

Pattern 1 demonstrates the core building block of agentic AI: **tool use**. The agent can look up country statistics and perform calculations, but relies entirely on the LLM's reasoning to decide when and how to use these tools.

> **P1 Metaphor:** The agent has **hands** (tools).

## What This Pattern Teaches

- How to connect LangGraph agents to MCP servers
- The ReAct (Reasoning + Acting) pattern for tool-calling
- Structured metrics capture for agent evaluation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                       │
│  ┌─────────────────────────────────────────────────────┐│
│  │              ReAct Loop (LLM)                       ││
│  │   Question → Reason → Act → Observe → Repeat       ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│                    MCP Protocol (stdio)                  │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────────┐│
│  │              MCP Server (pattern1_server)           ││
│  │  ┌─────────────┐  ┌─────────────┐                   ││
│  │  │ country_    │  │ calculator_ │                   ││
│  │  │ lookup_tool │  │ tool        │                   ││
│  │  └─────────────┘  └─────────────┘                   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `country_lookup_tool` | Get GDP, population, or area for a country | `country="Japan", metric="gdp_trillion"` |
| `calculator_tool` | Evaluate mathematical expressions | `expression="27.29 / 336.8 * 1000000"` |

## Usage

```bash
cd langgraph/agents/1_agent_with_multiple_mcp_tools
uv sync
uv run python -m src.main --question "What is the GDP per capita of the United States?"
```

### Run Experiments
```bash
bash experiments.bash
```

## Directory Structure

```
1_agent_with_multiple_mcp_tools/
├── src/
│   ├── __init__.py
│   ├── agent.py         # ReAct agent with MCP client
│   ├── prompts.py       # System prompt
│   └── main.py          # CLI entry point
├── experiments.bash     # Automated experiment runner
├── logs.txt             # Experiment results
└── pyproject.toml
```

## Core Files

| File | Purpose |
|------|---------|
| `src/agent.py` | Creates MCP client, connects to server, runs ReAct agent |
| `src/prompts.py` | System prompt defining agent behavior |
| `src/main.py` | CLI interface with `--question` argument |

## Example Output

**Question:** "What is the GDP per capita of the United States?"

```json
{
    "answer": "The GDP per capita of the United States is approximately $81,024.",
    "framework": "langgraph",
    "pattern": "agent_with_multiple_mcp_tools",
    "llm_calls": 3,
    "total_duration_ms": 8542,
    "tool_calls": 3,
    "tools_used": ["country_lookup_tool", "country_lookup_tool", "calculator_tool"]
}
```

## Capabilities & Limitations

### ✅ What Pattern 1 Can Do
- Answer quantitative questions about countries
- Perform calculations with retrieved data
- Chain multiple tool calls in sequence

### ❌ What Pattern 1 Cannot Do
- Answer qualitative questions (culture, history, geography)
- Follow structured analysis methodologies
- Remember previous conversations
- Maintain context across sessions

## Key Technical Details

- **MCP Transport:** stdio (subprocess communication)
- **Agent Type:** LangGraph `create_react_agent`
- **LLM:** Configurable via `OLLAMA_MODEL` env var (default: `qwen3:8b`)
- **Data Source:** `_shared/data/countries.json` (20 countries)

## What's Next

**Pattern 2** adds a RAG-based knowledge base tool, giving the agent the ability to answer qualitative questions about countries using semantic search over a vector database.

---

## Progression Summary

| Pattern | Tools | Skills | Memory | Interface |
|---------|-------|--------|--------|-----------|
| **P1** | 2 MCP | ❌ | ❌ | CLI `--question` |
| P2 | 3 MCP (+RAG) | ❌ | ❌ | CLI `--question` |
| P3 | 3 MCP | 4 skills | ❌ | CLI `--question` |
| P4 | 3 MCP | 4 skills | ✅ Dual-layer | Interactive chat |