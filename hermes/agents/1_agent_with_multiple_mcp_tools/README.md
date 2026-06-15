# Pattern 1 — Agent with Multiple MCP Tools (Hermes)

A Hermes-style ReAct agent that answers country-data questions by calling tools exposed via an MCP stdio server.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     main.py                         │
│  CLI args → HermesAgent → logs.txt + JSON output    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               agent.py — HermesAgent                │
│                                                     │
│  Constructor mirrors hermes-agent AIAgent:          │
│    model, quiet_mode, ephemeral_system_prompt,      │
│    max_iterations, skip_memory, skip_context_files  │
│                                                     │
│  run_conversation() → {final_response, messages}    │
│  chat()             → str (one-shot convenience)    │
│                                                     │
│  Internally: OpenAI client → hermes3 via Ollama     │
│  ReAct loop: LLM call → parse tool_calls → MCP exec │
└──────────┬──────────────────────────────────────────┘
           │ MCP stdio
┌──────────▼──────────────────────────────────────────┐
│       _shared/src/mcp_servers/pattern1_server.py    │
│                                                     │
│  country_lookup_tool(country, metric)               │
│  calculator_tool(expression)                        │
└─────────────────────────────────────────────────────┘
```

## Hermes Library Practices Used

| Practice | Where |
|---|---|
| `HermesAgent(quiet_mode=True)` | Suppress output for programmatic use |
| `skip_memory=True` | Stateless per-request mode (no persistent memory) |
| `skip_context_files=True` | No AGENTS.md loading (clean slate) |
| `ephemeral_system_prompt` | Custom prompt not saved to trajectories |
| `run_conversation(task_id=...)` | Task isolation identifier |
| `result["final_response"]` | Standard return key from hermes-agent |
| `result["messages"]` | Full message history for debugging/training |

> **Why not `hermes-agent` library directly?**
> The `hermes-agent` library (`from run_agent import AIAgent`) requires a cloud
> provider key (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`)
> and manages its own built-in toolsets. It has no API to inject custom MCP tools
> programmatically. This implementation uses the same constructor interface and
> return structure, but routes through Ollama and our shared MCP server.
> Switching to the cloud library later is a one-line change in `agent.py`.

## Model

Uses **hermes3** — the Nous Research model that the Hermes agent framework is built around. It natively supports standard OpenAI-compatible tool calling when served via Ollama.

```bash
ollama pull hermes3:latest
```

## Setup

```bash
cd hermes/agents/1_agent_with_multiple_mcp_tools
uv sync
```

## Run

```bash
# Single question
OLLAMA_MODEL=hermes3:latest \
OLLAMA_BASE_URL=http://localhost:11434 \
uv run python -m src.main \
  --task country_analysis \
  --question "What is the population density of Japan?"

# All experiments
bash experiments.bash
```

## Output

`main.py` prints JSON to stdout and appends a human-readable entry to `logs.txt`:

```json
{
  "answer": "Japan's population density is approximately 341 people per km².",
  "framework": "hermes",
  "pattern": "agent_with_multiple_mcp_tools",
  "llm_calls": 3,
  "total_duration_ms": 4200,
  "prompt_tokens": 780,
  "completion_tokens": 95,
  "total_tokens": 875,
  "tool_calls": 2,
  "cold_start_ms": 120,
  "peak_memory_mb": 18.4
}
```

## Comparison: Hermes vs LangGraph vs Strands

| Aspect | LangGraph | Strands | Hermes |
|---|---|---|---|
| Agent abstraction | `create_react_agent` graph | `Agent` class | `HermesAgent` (custom, mirrors `AIAgent`) |
| Tool wiring | LangChain tools via `@tool` | `MCPClient.list_tools_sync()` | OpenAI tools schema from `session.list_tools()` |
| Model backend | ChatOllama | `OllamaModel` | OpenAI client → Ollama `/v1` |
| Tool format | LangChain `ToolMessage` | Strands content blocks | OpenAI `tool_calls` / `tool` role |
| Memory | `MemorySaver` checkpointer | Re-used `Agent` instance | In-request messages list |
| MCP client | `langchain_mcp_adapters` | `strands MCPClient` | Raw `mcp.ClientSession` |
| Cloud library switch | N/A | N/A | One-line import change |

## File Structure

```
hermes/agents/1_agent_with_multiple_mcp_tools/
├── README.md
├── experiments.bash
├── logs.txt          (generated on first run)
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── agent.py      ← HermesAgent class
│   ├── main.py       ← CLI entry point + logging
│   └── prompts.py    ← system prompt
└── uv.lock           (generated after uv sync)
```
