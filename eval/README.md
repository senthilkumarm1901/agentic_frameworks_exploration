# Evaluation Harness

## Overview

This is the evaluation harness for comparing **3 agentic frameworks** across **6 patterns**, totalling 18 applications. The harness discovers each app, invokes it via a standardized CLI contract, collects structured JSON output, and generates comparison reports.

| Framework | Apps | Patterns |
|-----------|------|----------|
| LangGraph | 6 | All 6 |
| AWS Strands Agents | 6 | All 6 |
| Hermes | 6 | All 6 |

## Frameworks Under Evaluation

| Framework | Language | Notes |
|-----------|----------|-------|
| LangGraph | Python | Graph-based orchestration via LangChain ecosystem |
| AWS Strands Agents | Python | AWS-native agent SDK |
| Hermes | Python | CLI app; tool consumption TBD |

All frameworks use **Ollama** as the LLM backend (model configurable via `OLLAMA_MODEL` env var, default: `qwen3.5:35b-a3b-coding-nvfp4`).

## CLI Contract

Every app must honor this standardized input/output contract:

**Input:**

```bash
uv run python src/main.py --task <task_name>
```

**Output:** JSON on stdout:

```json
{
  "answer": "...",
  "framework": "langgraph",
  "pattern": "agent_with_multiple_mcp_tools",
  "llm_calls": 3,
  "total_duration_ms": 1240,
  "prompt_tokens": 1542,
  "completion_tokens": 487,
  "total_tokens": 2029,
  "tool_calls": 3,
  "cold_start_ms": 2340,
  "peak_memory_mb": 312.5
}
```

## Key Metrics

### Core Metrics

| Metric | Unit | Description |
|--------|------|-------------|
| Latency | ms | End-to-end wall-clock time (`total_duration_ms`) |
| Accuracy | % | Correctness of `answer` against golden dataset |
| Tokens | count | Total tokens consumed (prompt + completion) |
| Packaging Size | MB | Installed size of framework + dependencies |

### Extended Metrics

| Metric | Unit | Description |
|--------|------|-------------|
| LLM Call Count | count | Number of LLM round-trips (`llm_calls`) |
| Peak Memory | MB | Max RSS during execution |
| Lines of Code | LOC | Implementation size (src only) |
| Dependency Count | count | Direct + transitive dependencies |
| Cold Start | ms | Time from process start to first LLM call |
| Determinism | % | Output consistency across repeated runs |

## Metric Collection Methodology

| Metric | Collection Method | Notes |
|--------|-------------------|-------|
| `total_duration_ms` | Agent code timer | Wall-clock from start to answer |
| `llm_calls` | Agent code counter | Incremented per LLM invocation |
| `prompt_tokens` | Ollama response `prompt_eval_count` | Summed across all LLM calls |
| `completion_tokens` | Ollama response `eval_count` | Summed across all LLM calls |
| `total_tokens` | `prompt_tokens + completion_tokens` | Computed |
| `cold_start_ms` | Agent code timer | Time from process start to first LLM call |
| `peak_memory_mb` | `tracemalloc` / `resource.getrusage()` | Max RSS during execution |
| `packaging_size_mb` | `du -sk .venv/` | Installed venv size |
| `loc` | `find src -name "*.py" -exec cat {} + \| wc -l` | Pattern's own src/ only; excludes `_shared/` |
| `dependency_count` | `grep -c 'name = ' uv.lock` | Total packages in lockfile (direct + transitive) |
| `determinism` | Compare answers across N runs | % identical answers |

## Scoring

Each metric is normalized to a 0–1 scale and weighted:

```
score = Σ (weight_i × normalized_metric_i)
```

Lower is better for: latency, tokens, packaging size, LLM call count, peak memory, LOC, dependency count, cold start.
Higher is better for: accuracy, determinism.

Final scores are reported per-framework, per-pattern, and as an aggregate.

## Evaluation Harness Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| `runner.py` | `src/eval/runner.py` | Discovers leaf directories matching the pattern structure, invokes the CLI contract, collects JSON results |
| `report.py` | `src/eval/report.py` | Generates comparison tables (Markdown) and CSV exports from collected results |

## Usage

```bash
# Run full evaluation (all frameworks, all patterns)
make eval

# Run evaluation for a single framework
make eval FRAMEWORK=langgraph

# Generate report from collected results
make report
```

## Pattern Catalog

| # | Pattern | Type | Description |
|---|---------|------|-------------|
| 1 | agent_with_multiple_mcp_tools | Agent | Agent using multiple MCP tools |
| 2 | agent_with_rag_mcp_tool | Agent | Extending Agent Pattern 1 (which already has multiple tools) with a RAG MCP Tool |
| 3 | agent_with_mcp_tools_and_skills | Agent | Extending Agent Pattern 2 with Skills |
| 4 | workflow_2_layer_sequential | Workflow | Two-layer sequential workflow |
| 5 | workflow_3_layer_routing | Workflow | Three-layer routing workflow |
| 6 | workflow_2_layer_parallelization | Workflow | Two-layer parallel workflow |

## Example Tasks

| Task Name | Pattern | Description |
|-----------|---------|-------------|
| country_analysis | agent_with_multiple_mcp_tools | Multi-tool orchestration questions using country_lookup_tool and calculator_tool (e.g., population density, GDP per capita comparisons) |
| TBD | agent_with_rag_mcp_tool | To be defined |
| TBD | agent_with_mcp_tools_and_skills | To be defined |
| TBD | workflow_2_layer_sequential | To be defined |
| TBD | workflow_3_layer_routing | To be defined |
| TBD | workflow_2_layer_parallelization | To be defined |
