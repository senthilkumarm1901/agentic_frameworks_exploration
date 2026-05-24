# LLM Tool Use with Custom MCP — Augmented LLM Pattern (LangGraph)

**The simplest agentic pattern:** a single LLM enhanced with tools via a custom MCP server.

No workflows, no loops, no routing, no multi-agent orchestration.

---

## Architecture

```
User Question (--question flag)
  from: src/main.py
     ↓
LangGraph ReAct Agent + MCP Client
  files: src/agent.py, src/prompts.py
  libs: langgraph.prebuilt + langchain-mcp-adapters
     ↓                              ↑
     ↓ tool_call request            ↑ tool_call result
     ↓                              ↑
Custom MCP Server (FastMCP over stdio subprocess)
  file: _shared/src/country_tools_server.py
  tools:
    ├── country_lookup_tool -> _shared/src/tools/country_lookup.py
    └── calculator_tool     -> _shared/src/tools/calculator.py
                                 ↓
                       _shared/data/countries.json
```

## How It Works

1. **User asks a question** about country data (GDP, population, area) via `--question` flag
2. **LangGraph ReAct agent** reasons about what tools to call
3. **MCP Client** (langchain-mcp-adapters) sends tool requests to the MCP server via stdio
4. **MCP Server** (FastMCP subprocess) executes the tools and returns results
5. **Agent synthesizes** a natural language answer from tool results

---

## Files

| File | Purpose |
|------|---------|
| `_shared/src/tools/country_lookup.py` | Pure Python: look up GDP, population, or area for a country |
| `_shared/src/tools/calculator.py` | Pure Python: safe arithmetic evaluation |
| `_shared/src/country_tools_server.py` | FastMCP server exposing both tools over stdio |
| `src/prompts.py` | System prompt for the agent |
| `src/agent.py` | LangGraph ReAct agent + MCP client connection |
| `src/main.py` | CLI entry point accepting `--task` and `--question` flags |

---

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Ollama running locally at `http://localhost:11434`
- Model: `qwen3:8b` (configurable via `.env` or env var)

---

## Setup

```bash
cd langgraph/foundation/augmented_llm/llm_tool_use_with_custom_mcp
uv sync
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |

Set these in a `.env` file at the workspace root or export them.

---

## Run Commands

```bash
cd langgraph/foundation/augmented_llm/llm_tool_use_with_custom_mcp

# GDP comparison (US vs India) — default question
uv run python -m src.main --task augmented_llm

# Population density of Japan
uv run python -m src.main --task augmented_llm --question "What is the population density of Japan in people per square kilometer?"

# GDP per capita of Germany
uv run python -m src.main --task augmented_llm --question "What is the GDP per capita of Germany in trillion USD per million people?"

# Any country data question
uv run python -m src.main --task augmented_llm --question "Which country has a larger population, India or China?"
```

---

## Output Contract

**stdout:** Valid JSON (consumed by eval harness)
```json
{
  "question": "What is the population density of Japan in people per square kilometer?",
  "answer": "The population density of Japan is approximately 341.5 people per square kilometer.",
  "llm_calls": 3,
  "tool_calls": 3,
  "total_duration_ms": 8500,
  "framework": "langgraph",
  "pattern": "augmented_llm"
}
```

**stderr:** Tool call logs + debug info
```
[INFO] Task: augmented_llm
[INFO] Question: What is the population density of Japan in people per square kilometer?
[TOOL] country_lookup_tool("Japan", "population_million") requested
[TOOL] country_lookup_tool("Japan", "area_sq_km") requested
[TOOL] country_lookup_tool → The population million of Japan is 124.5 million people
[TOOL] country_lookup_tool → The area sq km of Japan is 364569 square kilometers
[TOOL] calculator_tool("124.5 * 1000000 / 364569") requested
[TOOL] calculator_tool → Result: 341.4991
```

---

## Example Questions

| Question | Tools Used |
|----------|------------|
| "How many times larger is the GDP of the United States compared to India?" | country_lookup × 2, calculator × 1 |
| "What is the population density of Japan in people per square kilometer?" | country_lookup × 2, calculator × 1 |
| "What is the GDP per capita of Germany in trillion USD per million people?" | country_lookup × 2, calculator × 1 |
| "Which country has the largest area, Canada or Australia?" | country_lookup × 2 |

---

## Design Principles

1. **MCP is the star** — tool calls go through MCP protocol, not direct imports
2. **Simplicity** — this is the FOUNDATION pattern; minimal moving parts
3. **Observability** — every tool call logged to stderr
4. **Portability** — same MCP server reusable by Strands and Hermes frameworks
5. **Determinism** — fixed JSON data = reproducible answers

---

## What This Pattern Does NOT Include

- Prompt chaining / sequential workflows
- Routing logic
- Parallel execution
- Orchestrator-workers
- Evaluator-optimizer loops
- Memory / conversation history
- RAG / vector search
- Web search or external API calls

---

## Related Patterns

- **llm_tool_use_with_reference_mcp** — Same pattern using a reference MCP server (AWS Documentation MCP)
- RAG / vector search
- Web search or external API calls
