# Agentic Frameworks Exploration

Comparing LLM agent patterns across frameworks (LangGraph, Strands, Rig).

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally with models:
  - `qwen3.5:35b-a3b-coding-nvfp4`
  - `nomic-embed-text`

---

## LangGraph Exploration

### Setup

```bash
cd langgraph_exploration
cp .env.example .env   # edit as needed
uv venv && uv pip install -e .
```

### Graph Patterns (pure logic, no LLM needed)

| Pattern | Description | Command |
|---------|-------------|---------|
| Hello World | Single-node greeting graph | `uv run python -m langgraph_exploration.graphs.hello_world` |
| Multiple Inputs | Processes list of ints + name, computes sum | `uv run python -m langgraph_exploration.graphs.multiple_inputs` |
| Sequential | Two-node linear chain | `uv run python -m langgraph_exploration.graphs.sequential` |
| Conditional | Router with conditional edges (add/subtract) | `uv run python -m langgraph_exploration.graphs.conditional` |
| Looping | Random numbers in loop until counter hits 5 | `uv run python -m langgraph_exploration.graphs.looping` |

### Agents (require Ollama running)

| Agent | Description | Command |
|-------|-------------|---------|
| Simple Bot | Single-turn LLM call | `uv run python -m langgraph_exploration.agents.simple_bot --prompt "Hello"` |
| Chatbot | Multi-turn conversational agent | `uv run python -m langgraph_exploration.agents.chatbot --prompts "Hi" "Tell me more"` |
| ReAct Agent | Tool-calling agent (add/subtract/multiply) | `uv run python -m langgraph_exploration.agents.react_agent --prompt "What is 5 + 3?"` |
| Drafter Agent | Writing assistant with update/save tools | `uv run python -m langgraph_exploration.agents.drafter_agent --prompt "Write a haiku"` |
| RAG Agent | PDF retrieval-augmented agent (ChromaDB) | `uv run python -m langgraph_exploration.agents.rag_agent --question "What were top stocks in 2024?"` |

**RAG Agent extras:**
- `--rebuild` to re-index the PDF
- `--verbose` for diagnostics
- Requires `data/Stock_Market_Performance_2024.pdf`

### Tests

```bash
uv run pytest                        # all tests
uv run pytest -m "not integration"   # unit only (no Ollama needed)
uv run pytest -m integration         # integration (requires Ollama)
```

---

## Langgraph Agents

_Coming soon._

---
## Strands Agents

_Coming soon._

---

## Rig (Rust)

_Coming soon._
