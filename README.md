# Agentic Framework Evaluation — Patterns, Plan & Reference

## Overview

This project evaluates **3 agentic frameworks** across **8 LLM patterns** (from Anthropic's "Building Effective Agents" blog). Each pattern × framework = an independent, packaged CLI app. **24 apps total**.

**Goal**: Compare frameworks on latency, accuracy, packaging size, and other metrics using the same task and same LLM for each pattern — ensuring a fair, apples-to-apples evaluation.

**LLM**: Ollama (model configurable via `OLLAMA_MODEL` env var, default: `qwen3.5:35b-a3b-coding-nvfp4`)

---

## Frameworks Under Evaluation

| Framework | Language | Tool Consumption |
|-----------|----------|-----------------|
| **LangGraph** (+ LangChain, Deep Agents) | Python | MCP via `langchain-mcp-adapters` |
| **AWS Strands Agents** | Python | MCP via `strands-agents[mcp]` |
| **Rig** (rig-rs) | Rust | MCP via `rig-mcp` + `rmcp` |

---

## Patterns & Descriptions

### Hierarchy (from Anthropic's blog)

1. **Building Block** — The Augmented LLM: an LLM enhanced with retrieval, tools, and memory. This is the foundational unit.
2. **Workflows** — Predefined orchestrations of augmented LLMs (developer controls the flow).
3. **Agents** — Autonomous, loop-based systems where the LLM directs its own processes and tool usage.

### Pattern Catalog

| # | Pattern | Type | Description | Tools Required |
|---|---------|------|-------------|---------------|
| 1 | **Augmented LLM** | Foundation | Basic RAG + tool use. LLM enhanced with retrieval and tools. | `get_weather` |
| 2 | **Prompt Chaining** | Workflow | Fixed sequence of LLM steps with optional gates between steps. | None |
| 3 | **Routing** | Workflow | Classifies input and directs to a specialized handler/prompt. | None |
| 4 | **Parallelization** | Workflow | Multiple LLM calls work simultaneously (sectioning or voting). | None |
| 5 | **Orchestrator-Workers** | Workflow | Central LLM dynamically breaks down tasks, delegates to workers, synthesizes results. | `web_search` |
| 6 | **Evaluator-Optimizer** | Workflow | One LLM generates, another evaluates in an iterative feedback loop. | None |
| 7 | **Customer Support Agent** | Agent | Autonomous agent with access to order, tracking, refund, and knowledge base tools. | `lookup_order`, `check_tracking`, `issue_refund`, `escalate`, `search_knowledge_base` |
| 8 | **Coding Agent** | Agent | Agent that iterates on code using test execution feedback. | `run_python_code` |

### Workflows vs. Agents

| Dimension | Workflows | Agents |
|-----------|-----------|--------|
| Control flow | Predefined code paths | LLM dynamically directs its own flow |
| Path predictability | Fixed, hardcoded | Open-ended, unpredictable steps |
| Decision authority | Developer controls | Model controls |
| When to use | Well-defined tasks needing consistency | Open-ended problems needing flexibility |

---

## Example Tasks (Same Input Across All 3 Frameworks)

| # | Pattern | Task | Input Summary |
|---|---------|------|--------------|
| 1 | Augmented LLM | Q&A with tool use | "What is the current weather in Tokyo and what should I wear?" |
| 2 | Prompt Chaining | Summarize → translate | English paragraph about WebAssembly → 2-sentence summary → Spanish |
| 3 | Routing | Support ticket triage | "I was charged twice for my subscription last month" → classify + route |
| 4 | Parallelization | Multi-aspect code review | Python `find_duplicates` function → review correctness + performance + style |
| 5 | Orchestrator-Workers | Research report | "Impact of WebAssembly on server-side computing" → dynamic subtopics → report |
| 6 | Evaluator-Optimizer | Haiku refinement | Theme: "autumn" → generate → evaluate 5-7-5 → iterate (max 5) |
| 7 | Customer Support Agent | Order troubleshooting | "My order #12345 hasn't arrived, stuck in transit 5 days" |
| 8 | Coding Agent | Bug fix | Buggy `merge_sorted` function + failing tests → fix |

---

## Folder Structure

```
agentic_frameworks_exploration/
│
├── llm_and_agentic_app_patterns/        # Blog notes + this README
│   ├── building_effective_agents_anthropic_blog.md
│   └── README.md                        # ← You are here
│
├── _shared/                             # Cross-framework shared code
│   ├── pyproject.toml                   # deps: python-dotenv, mcp[cli]
│   └── src/shared/
│       ├── __init__.py
│       ├── config.py                    # get_ollama_config() from env vars
│       ├── metrics.py                   # MetricsCollector + LLMCall dataclasses
│       ├── tool_stubs.py                # Deterministic tool functions (8 tools)
│       ├── tasks.py                     # Canonical task definitions per pattern
│       └── mcp_server.py               # FastMCP server exposing tools over stdio
│
├── langgraph/
│   ├── foundation/
│   │   └── augmented_llm/              # Each leaf: pyproject.toml + .venv + src/main.py
│   ├── workflow/
│   │   ├── prompt_chaining/
│   │   ├── routing/
│   │   ├── parallelization/
│   │   ├── orchestrator_workers/
│   │   └── evaluator_optimizer/
│   └── agent/
│       ├── customer_support/
│       └── coding_agent/
│
├── strands/
│   ├── _ollama_adapter/                # Thin Strands → Ollama bridge (OpenAI-compat)
│   ├── foundation/
│   │   └── augmented_llm/
│   ├── workflow/
│   │   ├── prompt_chaining/
│   │   ├── routing/
│   │   ├── parallelization/
│   │   ├── orchestrator_workers/
│   │   └── evaluator_optimizer/
│   └── agent/
│       ├── customer_support/
│       └── coding_agent/
│
├── rig/
│   ├── Cargo.toml                      # Cargo workspace
│   ├── _shared/                        # Rust shared crate (OllamaConfig)
│   ├── _shared_mcp/                    # Rust MCP server binary (same stubs)
│   ├── foundation/
│   │   └── augmented_llm/
│   ├── workflow/
│   │   ├── prompt_chaining/
│   │   ├── routing/
│   │   ├── parallelization/
│   │   ├── orchestrator_workers/
│   │   └── evaluator_optimizer/
│   └── agent/
│       ├── customer_support/
│       └── coding_agent/
│
├── eval/                               # Evaluation harness
│   ├── pyproject.toml
│   └── src/eval/
│       ├── runner.py                   # Discovers & runs all apps, collects metrics
│       └── report.py                   # Generates comparison tables
│
├── .env.example                        # OLLAMA_MODEL, OLLAMA_BASE_URL
└── Makefile                            # setup, run, eval, report, build-rust, clean
```

Each leaf directory (`<framework>/<type>/<pattern>/`) is an **independently packaged app** with:
- Its own `pyproject.toml` (Python) or `Cargo.toml` (Rust)
- Its own `.venv` (Python) managed by `uv`
- `src/main.py` (or `src/main.rs`) as the CLI entry point

---

## CLI Contract (Every App Must Honor)

### Input

```bash
# Python
uv run python src/main.py --task <task_name>

# Rust
cargo run --release -- --task <task_name>
```

Where `<task_name>` matches a key in `shared.tasks.TASKS` (e.g., `augmented_llm`, `prompt_chaining`, `routing`, etc.)

### Output

**stdout** — strictly JSON:
```json
{
  "answer": "The weather in Tokyo is 22°C and partly cloudy. I'd recommend...",
  "llm_calls": [
    {"duration_ms": 1234.5, "prompt_tokens": 50, "completion_tokens": 120}
  ],
  "total_duration_ms": 2345.6,
  "framework": "langgraph",
  "pattern": "augmented_llm"
}
```

**stderr** — logs and debug output only.

This contract enables the evaluation harness to `subprocess.run()` + `json.loads(stdout)` uniformly across all 24 apps.

---

## MCP Tool Architecture

All tool access goes through MCP (Model Context Protocol) over **stdio transport** — no direct function imports in pattern apps.

```
┌─────────────────────┐     stdio      ┌──────────────────────────┐
│  Pattern App        │ ◄────────────► │  MCP Tool Server         │
│  (LangGraph/Strands)│                │  (shared/mcp_server.py)  │
└─────────────────────┘                │  8 deterministic stubs   │
                                       └──────────────────────────┘

┌─────────────────────┐     stdio      ┌──────────────────────────┐
│  Pattern App (Rig)  │ ◄────────────► │  Rust MCP Tool Server    │
│                     │                │  (rig/_shared_mcp/)      │
└─────────────────────┘                │  Same 8 stubs in Rust    │
                                       └──────────────────────────┘
```

**Why MCP?**
- Uniform tool interface across all frameworks
- Deterministic stubs ensure identical tool responses for fair comparison
- Realistic: MCP is the emerging standard for LLM tool connectivity

**Tool stubs** (deterministic — same output every time):
| Tool | Signature | Used By |
|------|-----------|---------|
| `get_weather` | `(city: str) → dict` | Augmented LLM |
| `lookup_order` | `(order_id: str) → dict` | Customer Support |
| `check_tracking` | `(order_id: str) → dict` | Customer Support |
| `issue_refund` | `(order_id: str, reason: str) → dict` | Customer Support |
| `escalate` | `(order_id: str, priority: str) → dict` | Customer Support |
| `search_knowledge_base` | `(query: str) → str` | Customer Support, Orchestrator-Workers |
| `run_python_code` | `(code: str) → dict` | Coding Agent |
| `web_search` | `(query: str) → list[dict]` | Orchestrator-Workers |

---

## Key Metrics

### Core Metrics

| Metric | Unit | Collection Method | Why |
|--------|------|-------------------|-----|
| **End-to-end latency** | ms | Wall clock from CLI invocation to exit | User-perceived speed |
| **LLM call latency** | ms | Per-call timing inside the app | Framework overhead vs model time |
| **Accuracy / correctness** | 0.0–1.0 | Task-specific grader function | Does it produce the right answer? |
| **Total tokens** | count | Prompt + completion tokens per run | Cost proxy |
| **Packaging size** | MB | `du -sh .venv` / binary size | Deployment footprint |

### Extended Metrics

| Metric | Unit | Collection Method | Why |
|--------|------|-------------------|-----|
| **LLM call count** | count | App self-reports in JSON | Framework chattiness |
| **Peak memory (RSS)** | MB | `/usr/bin/time -v` or `resource.getrusage` | Resource efficiency |
| **Lines of code** | count | `tokei` / `cloc` per leaf | Developer experience / verbosity |
| **Dependency count** | count | `uv pip list` / `cargo tree` | Supply chain surface |
| **Cold start time** | ms | Process start → first LLM call | CLI / serverless relevance |
| **Determinism score** | 0.0–1.0 | Variance across N runs (temperature=0) | Reproducibility |

### Scoring

Per-pattern score → per-framework aggregate score. Weights TBD:
```
pattern_score = w1 * correctness + w2 * norm(latency) + w3 * norm(tokens) + ...
framework_score = mean(pattern_scores across all 8 patterns)
```

---

## Phase-wise Build Plan

### Phase 0: Scaffolding ✅
- [x] Directory tree (24 leaves + shared + eval)
- [x] `_shared/` package (config, metrics, tool stubs, tasks, MCP server)
- [x] `.env.example` with `OLLAMA_MODEL`, `OLLAMA_BASE_URL`
- [x] `Makefile` with targets: setup, run, eval, report, build-rust, clean
- [x] `rig/Cargo.toml` workspace + `rig/_shared/` crate
- [x] `strands/_ollama_adapter/` package

### Phase 1: Task Definitions ✅
- [x] Canonical task inputs defined in `_shared/src/shared/tasks.py`
- [x] Same input for each pattern across all 3 frameworks

### Phase 2: LangGraph Implementation ✅
- [x] Augmented LLM — `create_react_agent` + MCP `get_weather`
- [x] Prompt Chaining — `StateGraph`: summarize → translate
- [x] Routing — `StateGraph` + conditional edges to 3 handlers
- [x] Parallelization — fan-out 3 reviewer nodes → merge
- [x] Orchestrator-Workers — plan → dynamic `Send` workers (MCP `web_search`) → synthesize
- [x] Evaluator-Optimizer — generate ↔ evaluate loop with conditional edge
- [x] Customer Support Agent — `create_react_agent` + 5 MCP tools
- [x] Coding Agent — `create_react_agent` + MCP `run_python_code`

### Phase 3: Strands Implementation ✅
- [x] Ollama adapter (`strands/_ollama_adapter/`) — `OpenAIModel` bridge to Ollama's OpenAI-compat endpoint
- [x] Augmented LLM — `Agent` + MCP `get_weather` via `MCPClient`
- [x] Prompt Chaining — sequential `Agent` calls: summarize → translate
- [x] Routing — classify category → route to specialized prompt
- [x] Parallelization — `ThreadPoolExecutor` with 3 concurrent `Agent` instances → merge
- [x] Orchestrator-Workers — planner `Agent` → parallel worker `Agent`s (MCP `web_search`) → synthesizer
- [x] Evaluator-Optimizer — generate/evaluate loop with max iterations
- [x] Customer Support Agent — `Agent` + 5 MCP tools + system prompt
- [x] Coding Agent — `Agent` + MCP `run_python_code` + system prompt

### Phase 4: Rig (Rust) Implementation 🔲
- [ ] Update `rig/Cargo.toml` workspace — add `_shared_mcp` member + workspace deps (`rig-core`, `rig-mcp`, `rmcp`, `clap`, `schemars`)
- [ ] Rust MCP tool server (`rig/_shared_mcp/`) — `rmcp` server binary replicating all 8 deterministic stubs
- [ ] Shared Rig crate (`rig/_shared/`) — Ollama client config, JSON metrics output helper, CLI arg parsing
- [ ] Augmented LLM — `rig-core` agent + MCP `get_weather` via `rig-mcp` `McpToolProvider`
- [ ] Prompt Chaining — 2 sequential Ollama completions: summarize → translate
- [ ] Routing — classify completion → match category → specialized completion
- [ ] Parallelization — `tokio::join!` 3 concurrent completions → merge completion
- [ ] Orchestrator-Workers — plan completion → dynamic `tokio::spawn` workers (MCP `web_search`) → synthesize
- [ ] Evaluator-Optimizer — generate/evaluate loop with conditional break
- [ ] Customer Support Agent — `rig-core` agent + 5 MCP tools via `McpToolProvider`
- [ ] Coding Agent — `rig-core` agent + MCP `run_python_code`
- [ ] Verify `cargo build --release --workspace` compiles all 8 crates + MCP server

### Phase 5: Evaluation Harness 🔲
- [ ] Runner (`eval/src/eval/runner.py`) — discover all leaf dirs, invoke CLI via `subprocess.run`, collect JSON stdout
- [ ] Configurable runs per pattern (default N=3), timeout handling, error capture
- [ ] Per-run metrics: latency, token count, LLM call count, correctness score
- [ ] Static metrics collection: packaging size (`du -sh`), dependency count, LOC (`tokei`/`cloc`)
- [ ] Task-specific grading functions — one per pattern, scoring answer correctness 0.0–1.0
- [ ] Aggregation: mean, p50, p95, stddev per metric per (framework × pattern)
- [ ] Per-framework scoring: weighted aggregate across all 8 patterns
- [ ] Report generator (`eval/src/eval/report.py`) — markdown comparison table + CSV export
- [ ] `Makefile` integration: `make eval`, `make eval FRAMEWORK=langgraph`, `make report`

---

## Prerequisites

- **Ollama** — running locally with desired model pulled (`ollama pull <model>`)
- **uv** (≥ 0.4) — Python project/package manager. Includes `uvx` for running tools.
  ```bash
  # Install or update uv (includes uvx)
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Or update existing installation:
  uv self update
  ```
- **Rust toolchain** — for Rig framework (Phase 4): `rustup`, `cargo`

---

## Packaging Strategy

### Python (LangGraph, Strands)

- **Tool**: `uv` — independent project per leaf (each has own `.venv`)
- **Shared code**: `_shared/` installed as editable path dependency via `[tool.uv.sources]`
- **No uv workspace** — true isolation per leaf directory

```toml
# Example leaf pyproject.toml
[project]
name = "langgraph-routing"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["langgraph>=0.4", "langchain-ollama>=0.3", "shared"]

[tool.uv.sources]
shared = { path = "../../../_shared", editable = true }
```

Setup any leaf:
```bash
cd langgraph/workflow/routing
uv venv && uv pip install -e .
```

### Rust (Rig)

- **Tool**: Cargo workspace at `rig/`
- **Shared code**: `rig/_shared/` crate as workspace dependency
- Each pattern is a workspace member with its own `Cargo.toml`

### Minimal Dependencies

| Framework | Core Deps |
|-----------|-----------|
| LangGraph | `langgraph`, `langchain-ollama`, `langchain-mcp-adapters` (for tool patterns) |
| Strands | `strands-agents[mcp]`, `openai` (for Ollama adapter) |
| Rig | `rig-core`, `rig-mcp`, `tokio`, `serde`, `clap`, `rmcp` |
| Shared | `python-dotenv`, `mcp[cli]` |

---

## Makefile Quick Reference

```bash
# Setup a specific leaf
make setup FRAMEWORK=langgraph TYPE=workflow PATTERN=routing

# Run a specific pattern
make run FRAMEWORK=langgraph TYPE=workflow PATTERN=routing

# Build all Rust crates
make build-rust

# Run full evaluation (all patterns × all frameworks × N runs)
make eval

# Generate comparison report
make report
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen3.5:35b-a3b-coding-nvfp4` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
