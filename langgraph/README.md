# LangGraph Patterns

Structured agent patterns using LangGraph `StateGraph`, Ollama, and MCP tools. Each sub-project is self-contained.

## Setup (per sub-project)

```bash
cd langgraph/<category>/<pattern>
uv sync
```

Requires Ollama running with `qwen3.5:35b-a3b-coding-nvfp4` model and the shared `_shared/` package.

## Foundation

| Pattern | Description | Command |
|---------|-------------|---------|
| Augmented LLM | RAG + tool use via MCP ReAct agent | `cd langgraph/foundation/augmented_llm && uv run python -m src.main --task augmented_llm` |
| AWS Learning Agent | AWS docs lookup via MCP server | `cd langgraph/foundation/aws_learning_agent && uv run python -m src.main` |

## Workflow

| Pattern | Description | Command |
|---------|-------------|---------|
| Prompt Chaining | Sequential pipeline: summarize → translate | `cd langgraph/workflow/prompt_chaining && uv run python -m src.main --task prompt_chaining` |
| Routing | Classify message → route to specialized handler | `cd langgraph/workflow/routing && uv run python -m src.main --task routing` |
| Parallelization | Fan-out 3 code reviewers → merge findings | `cd langgraph/workflow/parallelization && uv run python -m src.main --task parallelization` |
| Orchestrator Workers | Dynamic subtopic delegation + synthesis | `cd langgraph/workflow/orchestrator_workers && uv run python -m src.main --task orchestrator_workers` |
| Evaluator Optimizer | Iterative haiku refinement loop with eval | `cd langgraph/workflow/evaluator_optimizer && uv run python -m src.main --task evaluator_optimizer` |

## Agent

| Pattern | Description | Command |
|---------|-------------|---------|
| Coding Agent | Iterative code-fixing with MCP test runner | `cd langgraph/agent/coding_agent && uv run python -m src.main --task coding_agent` |
| Customer Support | Autonomous support with order/refund/KB tools | `cd langgraph/agent/customer_support && uv run python -m src.main --task customer_support` |
