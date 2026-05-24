# Hermes Patterns

**Directory:** `hermes/` (at workspace root)

---

## Directory Structure

```
hermes/
├── agent/
│   ├── coding_agent/
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── __init__.py
│   │       └── main.py
│   └── customer_support/
│       ├── pyproject.toml
│       └── src/
│           ├── __init__.py
│           └── main.py
├── foundation/
│   └── augmented_llm/
│       ├── pyproject.toml
│       └── src/
│           ├── __init__.py
│           └── main.py
└── workflow/
    ├── evaluator_optimizer/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── main.py
    ├── orchestrator_workers/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── main.py
    ├── parallelization/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── main.py
    ├── prompt_chaining/
    │   ├── pyproject.toml
    │   └── src/
    │       ├── __init__.py
    │       └── main.py
    └── routing/
        ├── pyproject.toml
        └── src/
            ├── __init__.py
            └── main.py
```

---

## How to Set Up

**Prerequisites:**

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Ollama running locally at `http://localhost:11434`
- Model: `qwen3.5:35b-a3b-coding-nvfp4` (configurable via `.env`)

**Setup steps** (per sub-project):

```bash
# From any sub-project directory, e.g.:
cd hermes/workflow/prompt_chaining

# Install dependencies (pulls in shared lib from _shared/)
uv sync

# Or run directly:
uv run python -m src.main --task prompt_chaining
```

**Environment config** (root `.env` or `.env.example`):

```
OLLAMA_MODEL=qwen3.5:35b-a3b-coding-nvfp4
OLLAMA_BASE_URL=http://localhost:11434
```

Each sub-project depends on the `shared` package at `_shared/` (editable install via `tool.uv.sources`).

The `hermes-agent` package is installed from git: `git+https://github.com/NousResearch/hermes-agent.git`

---

## Patterns & Agents — Descriptions + Run Commands

### Foundation

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Augmented LLM** | Tool use via Hermes built-in web toolset. Agent answers queries that may require web access using `enabled_toolsets=["web"]`. | `cd hermes/foundation/augmented_llm && uv run python -m src.main --task augmented_llm` |

### Workflow

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Prompt Chaining** | Fixed sequential pipeline: summarize text → translate to target language. Two sequential `agent.chat()` calls. | `cd hermes/workflow/prompt_chaining && uv run python -m src.main --task prompt_chaining` |
| **Routing** | Classifies customer messages into categories (billing/technical/general) then routes to a specialized handler prompt. First call classifies, second handles. | `cd hermes/workflow/routing && uv run python -m src.main --task routing` |
| **Parallelization** | Fan-out/fan-in code review: 3 parallel reviewers (correctness, performance, style) via ThreadPoolExecutor, then a merge agent synthesizes findings. | `cd hermes/workflow/parallelization && uv run python -m src.main --task parallelization` |
| **Orchestrator Workers** | Dynamic delegation: planner breaks topic into subtopics, workers research in parallel (with web toolset), synthesizer merges into a report. | `cd hermes/workflow/orchestrator_workers && uv run python -m src.main --task orchestrator_workers` |
| **Evaluator Optimizer** | Iterative refinement loop: generates a haiku, evaluates for 5-7-5 correctness, loops back with feedback until accepted or max iterations reached. | `cd hermes/workflow/evaluator_optimizer && uv run python -m src.main --task evaluator_optimizer` |

### Agent

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Coding Agent** | Iterative code-fixing agent with terminal toolset. Given buggy code + failing test, uses terminal to verify fixes. | `cd hermes/agent/coding_agent && uv run python -m src.main --task coding_agent` |
| **Customer Support** | Autonomous support agent with custom system prompt and web toolset. Handles order issues with empathy and resolution offers. | `cd hermes/agent/customer_support && uv run python -m src.main --task customer_support` |

---

## Architecture Notes

- All patterns use **Hermes Agent** (`from run_agent import AIAgent`) — NousResearch's autonomous agent framework
- LLM: **Ollama** (local inference) accessed via OpenAI-compatible `/v1` endpoint
- Tool access: Built-in toolsets (`web`, `terminal`) — no custom MCP tool registration in library mode
- Metrics: Every pattern emits structured JSON metrics (timing, LLM call counts) to stdout via `shared.metrics`
- Task inputs: Canonical task definitions in `_shared/src/shared/tasks.py` ensure identical inputs across all frameworks (langgraph, strands, hermes)
- Thread safety: One `AIAgent` instance per thread for parallel patterns
- Stateless evaluation: `skip_context_files=True` and `skip_memory=True` disable persistent state for clean comparisons

---

## Comparison with Other Frameworks

| Aspect | LangGraph | Strands | Hermes |
|--------|-----------|---------|--------|
| Abstraction | StateGraph + nodes | Agent class + MCP | AIAgent + toolsets |
| Tool mechanism | MCP adapters | MCP client | Built-in toolsets |
| Parallelism | `Send` API | ThreadPoolExecutor | ThreadPoolExecutor |
| Loop control | Conditional edges | Python while | Python while |
| Complexity | High (graph DSL) | Medium (MCP wiring) | Low (single class) |
