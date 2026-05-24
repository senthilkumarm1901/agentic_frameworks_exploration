# LangGraph Patterns

**Directory:** `langgraph/` (at workspace root)

---

## Directory Structure

```
langgraph/
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
│       ├── llm_tool_use_with_custom_mcp/
│       │   ├── pyproject.toml
│       │   ├── README.md
│       │   └── src/
│       │       ├── __init__.py
│       │       ├── agent.py
│       │       ├── main.py
│       │       └── prompts.py
│       └── llm_tool_use_with_reference_mcp/
│           ├── pyproject.toml
│           └── src/
│               └── main.py
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

## How to Set Up the Project

**Prerequisites:**

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Ollama running locally at `http://localhost:11434`
- Model: `qwen3.5:35b-a3b-coding-nvfp4` (configurable via `.env`)

**Setup steps** (per sub-project):

```bash
# From any sub-project directory, e.g.:
cd langgraph/workflow/prompt_chaining

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

---

## Patterns & Agents — Descriptions + Run Commands

### Foundation

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **LLM Tool Use (Custom MCP)** | Country data Q&A via custom MCP. Uses a ReAct agent with MCP tools (`country_lookup_tool`, `calculator_tool`) to answer queries about GDP, population, and area. | `cd langgraph/foundation/augmented_llm/llm_tool_use_with_custom_mcp && uv run python -m src.main --task augmented_llm --question "What is the population density of Japan?"` |
| **LLM Tool Use (Reference MCP)** | Documentation lookup agent using the AWS Documentation MCP Server (`awslabs.aws-documentation-mcp-server`). Answers AWS questions with up-to-date docs. | `cd langgraph/foundation/augmented_llm/llm_tool_use_with_reference_mcp && uv run python -m src.main` |

### Workflow

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Prompt Chaining** | Fixed sequential pipeline: summarize text → translate to target language. Uses LangGraph `StateGraph` with linear edges. | `cd langgraph/workflow/prompt_chaining && uv run python -m src.main --task prompt_chaining` |
| **Routing** | Classifies customer messages into categories (billing/technical/general) then routes to a specialized handler node. Conditional edges based on classification. | `cd langgraph/workflow/routing && uv run python -m src.main --task routing` |
| **Parallelization** | Fan-out/fan-in code review: 3 parallel reviewers (correctness, performance, style) run simultaneously, then a merge node synthesizes findings. | `cd langgraph/workflow/parallelization && uv run python -m src.main --task parallelization` |
| **Orchestrator Workers** | Dynamic delegation: orchestrator plans subtopics, fans out to worker agents (with MCP tools for web search), then synthesizes a research report. Uses `Send` for dynamic parallelism. | `cd langgraph/workflow/orchestrator_workers && uv run python -m src.main --task orchestrator_workers` |
| **Evaluator Optimizer** | Iterative refinement loop: generates a haiku, evaluates for 5-7-5 correctness, loops back with feedback until accepted or max iterations reached. Uses conditional edges for the loop. | `cd langgraph/workflow/evaluator_optimizer && uv run python -m src.main --task evaluator_optimizer` |

### Agent

| Pattern | Description | Run Command |
|---------|-------------|-------------|
| **Coding Agent** | Iterative code-fixing agent: given buggy code + failing test, uses MCP `run_python_code` tool to test fixes in a ReAct loop until tests pass. | `cd langgraph/agent/coding_agent && uv run python -m src.main --task coding_agent` |
| **Customer Support** | Autonomous support agent with MCP tools (order lookup, tracking, refund, escalation, KB search). Investigates and resolves customer issues autonomously. | `cd langgraph/agent/customer_support && uv run python -m src.main --task customer_support` |

---

## How Tests Are Run

**No tests exist** within the `langgraph/` directory. There are no `test_*.py` files, `tests/` directories, or test configurations in any of the 9 sub-projects.

The only testing infrastructure is in the separate `langgraph_exploration/` project (which has `tests/test_*.py` files runnable via `uv run pytest`).

---

## Architecture Notes

- All patterns use **LangGraph** (`StateGraph` or `create_react_agent` from `langgraph.prebuilt`)
- LLM: **Ollama** with `langchain-ollama` (local inference)
- Tool access: **MCP** (Model Context Protocol) via `langchain-mcp-adapters` connecting to tool stubs in `_shared/src/shared/mcp_server.py`
- Metrics: Every pattern emits structured JSON metrics (timing, LLM call counts) to stdout via `shared.metrics`
- Task inputs: Canonical task definitions in `_shared/src/shared/tasks.py` ensure identical inputs across all frameworks (langgraph, strands, rig)
