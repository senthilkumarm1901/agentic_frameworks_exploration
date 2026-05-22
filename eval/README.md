# Evaluation Harness

## Overview

This is the evaluation harness for comparing **3 agentic frameworks** across **8 LLM patterns**, totalling 24 applications. The harness discovers each app, invokes it via a standardized CLI contract, collects structured JSON output, and generates comparison reports.

| Framework | Apps | Patterns |
|-----------|------|----------|
| LangGraph | 8 | All 8 |
| AWS Strands Agents | 8 | All 8 |
| Hermes | 8 | All 8 |

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
  "llm_calls": 3,
  "total_duration_ms": 1240,
  "framework": "langgraph",
  "pattern": "prompt_chaining"
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

| # | Pattern | Type | Description | Required Tools |
|---|---------|------|-------------|----------------|
| 1 | Augmented LLM | Foundation | LLM with tool access and retrieval | Web search, calculator |
| 2 | Prompt Chaining | Workflow | Sequential LLM calls with validation gates | Text processing |
| 3 | Routing | Workflow | Classify input and dispatch to specialist | Classification |
| 4 | Parallelization | Workflow | Fan-out tasks and aggregate results | Multiple tool calls |
| 5 | Orchestrator-Workers | Workflow | Dynamic task decomposition and delegation | Task-specific tools |
| 6 | Evaluator-Optimizer | Workflow | Generate-then-critique loop | Evaluation criteria |
| 7 | Coding Agent | Agent | Autonomous code generation and execution | Code interpreter, file I/O |
| 8 | Customer Support | Agent | Multi-turn conversation with tool use | Knowledge base, ticketing |

## Example Tasks

| Task Name | Pattern | Description |
|-----------|---------|-------------|
| `summarize_article` | Prompt Chaining | Summarize a given article in 3 bullet points |
| `route_support_ticket` | Routing | Classify and route a customer support ticket |
| `parallel_research` | Parallelization | Research 3 topics concurrently and merge |
| `plan_and_execute` | Orchestrator-Workers | Break down a complex task and delegate |
| `improve_essay` | Evaluator-Optimizer | Iteratively improve an essay draft |
| `generate_function` | Coding Agent | Generate a Python function from a spec |
| `handle_refund` | Customer Support | Process a refund request with tool calls |
| `augmented_qa` | Augmented LLM | Answer a question using retrieval + tools |
