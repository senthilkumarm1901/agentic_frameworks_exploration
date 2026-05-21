# Strands Patterns

**Directory:** `strands/` (at workspace root)

---

## Directory Structure

```
strands/
├── _ollama_adapter/
│   ├── pyproject.toml
│   └── src/ollama_adapter/__init__.py
├── agent/
│   ├── coding_agent/
│   │   ├── pyproject.toml
│   │   └── src/main.py
│   └── customer_support/
│       ├── pyproject.toml
│       └── src/main.py
├── foundation/
│   ├── augmented_llm/
│   │   ├── pyproject.toml
│   │   └── src/main.py
│   └── aws_learning_agent/
│       ├── pyproject.toml
│       └── src/main.py
└── workflow/
    ├── evaluator_optimizer/
    │   ├── pyproject.toml
    │   └── src/main.py
    ├── orchestrator_workers/
    │   ├── pyproject.toml
    │   └── src/main.py
    ├── parallelization/
    │   ├── pyproject.toml
    │   └── src/main.py
    ├── prompt_chaining/
    │   ├── pyproject.toml
    │   └── src/main.py
    └── routing/
        ├── pyproject.toml
        └── src/main.py
```

---

## How to Set Up the Project

**Prerequisites:**

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Ollama running locally at `http://localhost:11434`
- Model: `qwen3.5:35b-a3b-coding-nvfp4` (configurable via `.env`)

**Setup steps** (per sub-project):

```bash
# From any sub-project directory, e.g.:
cd strands/workflow/prompt_chaining

# Install dependencies (pulls in shared lib from _shared/ and _ollama_adapter/)
uv sync

# Or run directly:
uv run python -m src.main --task prompt_chaining
```

**Environment config** (root `.env` or `.env.example`):

```
OLLAMA_MODEL=qwen3.5:35b-a3b-coding-nvfp4
OLLAMA_BASE_URL=http://localhost:11434
```

Each sub-project depends on:
- `shared` package at `_shared/` (editable install via `tool.uv.sources`)
- `ollama-adapter` package at `_ollama_adapter/` (OpenAI-compatible Ollama model adapter)

---

## Patterns & Agents — Descriptions + Run Commands

### Foundation

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Augmented LLM** | Basic tool-augmented LLM: answers a weather query using MCP tools. Uses Strands `Agent` with MCP tool stubs. | `cd strands/foundation/augmented_llm && uv run python -m src.main --task augmented_llm` |
| **AWS Learning Agent** | Documentation lookup agent using the real AWS Documentation MCP Server (`awslabs.aws-documentation-mcp-server`). Answers AWS questions with up-to-date docs. | `cd strands/foundation/aws_learning_agent && uv run python -m src.main` |

### Workflow

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Prompt Chaining** | Fixed sequential pipeline: summarize text → translate to target language. Chains two Strands `Agent` calls sequentially. | `cd strands/workflow/prompt_chaining && uv run python -m src.main --task prompt_chaining` |
| **Routing** | Classifies customer messages into categories (billing/technical/general) then routes to a specialized handler agent. | `cd strands/workflow/routing && uv run python -m src.main --task routing` |
| **Parallelization** | Fan-out/fan-in code review: 3 parallel reviewers (correctness, performance, style) run simultaneously via `ThreadPoolExecutor`, then a synthesizer merges findings. | `cd strands/workflow/parallelization && uv run python -m src.main --task parallelization` |
| **Orchestrator Workers** | Dynamic delegation: orchestrator plans subtopics, fans out to worker agents (with MCP tools for web search) via `ThreadPoolExecutor`, then synthesizes a research report. | `cd strands/workflow/orchestrator_workers && uv run python -m src.main --task orchestrator_workers` |
| **Evaluator Optimizer** | Iterative refinement loop: generates a haiku, evaluates for 5-7-5 correctness, loops back with feedback until accepted or max iterations reached. | `cd strands/workflow/evaluator_optimizer && uv run python -m src.main --task evaluator_optimizer` |

### Agent

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Coding Agent** | Iterative code-fixing agent: given buggy code + failing test, uses MCP `run_python_code` tool to test fixes in a loop until tests pass. | `cd strands/agent/coding_agent && uv run python -m src.main --task coding_agent` |
| **Customer Support** | Autonomous support agent with MCP tools (order lookup, tracking, refund, escalation, KB search). Investigates and resolves customer issues autonomously. | `cd strands/agent/customer_support && uv run python -m src.main --task customer_support` |

---

## How Tests Are Run

**No tests exist** within the `strands/` directory. There are no `test_*.py` files, `tests/` directories, or test configurations in any of the 9 sub-projects.

---

## Architecture Notes

- All patterns use the **Strands Agents SDK** (`strands-agents[mcp]`)
- LLM: **Ollama** via `_ollama_adapter/` — a thin wrapper creating a `strands.models.openai.OpenAIModel` pointing at Ollama's OpenAI-compatible `/v1` endpoint
- Tool access: **MCP** (Model Context Protocol) via `StdioServerParameters` connecting to tool stubs in `_shared/src/shared/mcp_server.py`
- Parallelism: `parallelization` and `orchestrator_workers` use `ThreadPoolExecutor` for fan-out concurrency
- No shared state between agents — each `Agent(model=model)` is stateless; multi-step patterns reuse the same agent instance for conversation continuity
- Metrics: Every pattern emits structured JSON metrics (timing, LLM call counts) to stdout via `shared.metrics`
- Task inputs: Canonical task definitions in `_shared/src/shared/tasks.py` ensure identical inputs across all frameworks (langgraph, strands, rig)
