# Agent with Multiple MCP Tools

This is the retained LangGraph pattern 1 example in the approved six-path taxonomy.

## Status

- Active migrated example for the current LangGraph cleanup wave
- Located at `langgraph/agents/1_agent_with_multiple_mcp_tools`
- Backed by real package files and runnable scaffolding already present in this directory

## What It Demonstrates

- A LangGraph ReAct agent
- Multiple MCP-backed tools for country lookup and arithmetic
- Tool-mediated question answering over shared country data

## Core Files

| File | Purpose |
|------|---------|
| `src/agent.py` | Agent wiring and MCP tool orchestration |
| `src/prompts.py` | Prompt content for the agent |
| `src/main.py` | CLI entry point |
| `experiments.bash` | Local experiment script |
| `detailed_pattern_views.md` | Pattern diagrams |
| `notes_improvement_areas.md` | Design notes and observations |

## Setup

```bash
cd langgraph/agents/1_agent_with_multiple_mcp_tools
uv sync
uv run python -m src.main --task augmented_llm
```

## Scope Boundary

This wave does not add compatibility paths for the retired legacy LangGraph layout. Documentation and navigation should use this directory as the canonical location for pattern 1.