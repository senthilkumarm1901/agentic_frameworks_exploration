# Strands Patterns

Structured agent patterns using [Strands Agents SDK](https://github.com/strands-agents/sdk-python), Ollama, and MCP tools. Each sub-project is self-contained.

## Setup (per sub-project)

```bash
cd strands/<category>/<pattern>
uv sync
```

Requires Ollama running with `qwen3.5:35b-a3b-coding-nvfp4` model and the shared `_shared/` + `_ollama_adapter/` packages.

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_MODEL` | `qwen3.5:35b-a3b-coding-nvfp4` | Model name served by Ollama |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server endpoint |

## Foundation

| Pattern | Description | Command |
|---------|-------------|---------|
| Augmented LLM | Tool-augmented LLM answering queries via MCP tools | `cd strands/foundation/augmented_llm && uv run python -m src.main --task augmented_llm` |
| AWS Learning Agent | AWS docs lookup via real AWS MCP server | `cd strands/foundation/aws_learning_agent && uv run python -m src.main` |

## Workflow

| Pattern | Description | Command |
|---------|-------------|---------|
| Prompt Chaining | Sequential pipeline: summarize → translate | `cd strands/workflow/prompt_chaining && uv run python -m src.main --task prompt_chaining` |
| Routing | Classify message → route to specialized handler | `cd strands/workflow/routing && uv run python -m src.main --task routing` |
| Parallelization | Fan-out 3 code reviewers → merge findings | `cd strands/workflow/parallelization && uv run python -m src.main --task parallelization` |
| Orchestrator Workers | Dynamic subtopic delegation + synthesis | `cd strands/workflow/orchestrator_workers && uv run python -m src.main --task orchestrator_workers` |
| Evaluator Optimizer | Iterative haiku refinement loop with eval | `cd strands/workflow/evaluator_optimizer && uv run python -m src.main --task evaluator_optimizer` |

## Agent

| Pattern | Description | Command |
|---------|-------------|---------|
| Coding Agent | Iterative code-fixing with MCP test runner | `cd strands/agent/coding_agent && uv run python -m src.main --task coding_agent` |
| Customer Support | Autonomous support with order/refund/KB tools | `cd strands/agent/customer_support && uv run python -m src.main --task customer_support` |

## Architecture Notes

- **Ollama Adapter** (`_ollama_adapter/`): Thin wrapper creating a `strands.models.openai.OpenAIModel` pointing at Ollama's `/v1` endpoint
- **MCP Tools**: Tool-using patterns launch the shared MCP server as a subprocess via `StdioServerParameters`
- **Parallelism**: `parallelization` and `orchestrator_workers` use `ThreadPoolExecutor` for fan-out
- **Metrics**: Every pattern emits structured JSON (framework, pattern, duration, LLM calls) to stdout
