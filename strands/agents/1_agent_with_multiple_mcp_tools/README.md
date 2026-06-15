# Pattern 1: Agent with Multiple MCP Tools

**The Foundation** - A Strands agent that uses MCP (Model Context Protocol) to access external tools.

## Overview

Pattern 1 demonstrates the core building block of agentic AI: **tool use**. The agent can look up country statistics and perform calculations, but relies entirely on the LLM's reasoning to decide when and how to use these tools.

> **P1 Metaphor:** The agent has **hands** (tools).

## What This Pattern Teaches

- How to connect Strands agents to MCP servers
- The ReAct-style Reasoning + Acting loop for tool-calling
- Structured metrics capture for agent evaluation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Strands Agent                        │
│  ┌─────────────────────────────────────────────────────┐│
│  │              ReAct-Style Loop (LLM)                 ││
│  │   Question -> Reason -> Act -> Observe -> Repeat    ││
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
cd strands/agents/1_agent_with_multiple_mcp_tools
uv sync
uv run python -m src.main --task "country_analysis" --question "What is the GDP per capita of the United States?"
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
│   ├── agent.py         # Strands agent wiring + MCP client setup
│   ├── prompts.py       # System prompt
│   └── main.py          # CLI entry point
├── experiments.bash     # Automated experiment runner
├── logs.txt             # Experiment results
├── plan.md              # Pattern implementation plan notes
├── pyproject.toml
└── uv.lock
```

## Core Files

| File | Purpose |
|------|---------|
| `src/agent.py` | Creates MCP client, connects to server, runs the Strands agent, and collects tool/LLM metrics |
| `src/prompts.py` | System prompt defining strict tool-use behavior |
| `src/main.py` | CLI interface with required `--task` and optional `--question`, plus JSON output/logging |

## Example Output

**Question:** "What is the GDP per capita of the United States?"

```json
{
  "answer": "The GDP per capita of the United States is approximately $81,024.",
  "framework": "strands",
  "pattern": "agent_with_multiple_mcp_tools",
  "llm_calls": 3,
  "total_duration_ms": 8542,
  "tool_calls": 3
}
```

## Capabilities & Limitations

### What Pattern 1 Can Do

- Answer quantitative questions about countries
- Perform calculations with retrieved data
- Chain multiple tool calls in sequence

### What Pattern 1 Cannot Do

- Answer qualitative questions (culture, history, geography)
- Follow structured analysis methodologies
- Remember previous conversations
- Maintain context across sessions

## Key Technical Details

- **MCP Transport:** stdio (subprocess communication)
- **Agent Runtime:** Strands `Agent` with `OllamaModel`
- **LLM:** Configurable via `OLLAMA_MODEL` env var (default: `qwen3:8b`)
- **Data Source:** `_shared/data/countries.json` (20 countries)

## What's Next

**Pattern 2** adds a RAG-based knowledge base tool, giving the agent the ability to answer qualitative questions about countries using semantic search over a vector database.

---

## Progression Summary

| Pattern | Tools | Skills | Memory | Interface |
|---------|-------|--------|--------|-----------|
| **P1** | 2 MCP | No | No | CLI `--task` + `--question` |
| P2 | 3 MCP (+RAG) | No | No | CLI `--task` + `--question` |
| P3 | 3 MCP | 4 skills | No | CLI `--task` + `--question` |
| P4 | 3 MCP | 4 skills | Yes Dual-layer | Interactive chat |
