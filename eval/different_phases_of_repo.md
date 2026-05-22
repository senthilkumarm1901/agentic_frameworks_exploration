# Phases of Building This Repository

## Phase 0: Shared Infrastructure & Project Scaffolding

- [x] Create top-level `README.md` with project overview
- [x] Create `_shared/` Python package with common utilities
  - [x] `_shared/src/shared/config.py` — Ollama configuration, env var handling (`OLLAMA_MODEL`)
  - [x] `_shared/src/shared/metrics.py` — Timing, token counting, structured output helpers
  - [x] `_shared/src/shared/tasks.py` — Task registry and golden dataset definitions
  - [x] `_shared/src/shared/tool_stubs.py` — Shared tool implementations (search, calculator, etc.)
  - [x] `_shared/src/shared/mcp_server.py` — MCP server stub for tool serving
  - [x] `_shared/pyproject.toml` — Package definition with dependencies
- [x] Create `hermes/` directory scaffolding
  - [ ] Define Hermes project structure and shared adapter configuration
- [x] Create top-level `Makefile` with targets: `eval`, `report`, `clean`
- [x] Establish CLI contract (input: `--task <name>`, output: JSON on stdout)

## Phase 1: Foundation Pattern — Augmented LLM

- [x] `langgraph/foundation/augmented_llm/` — LangGraph augmented LLM with tool use
- [x] `strands/foundation/augmented_llm/` — Strands Agents augmented LLM with tool use
- [ ] `hermes/foundation/augmented_llm/` — Hermes augmented LLM with tool use (TBD)
- [x] Verify all three produce conformant JSON output for `augmented_qa` task

## Phase 2: LangGraph Workflow & Agent Patterns

- [x] `langgraph/workflow/prompt_chaining/` — Sequential LLM calls with gates
- [x] `langgraph/workflow/routing/` — Input classification and dispatch
- [x] `langgraph/workflow/parallelization/` — Fan-out and aggregation
- [x] `langgraph/workflow/orchestrator_workers/` — Dynamic decomposition
- [x] `langgraph/workflow/evaluator_optimizer/` — Generate-critique loop
- [x] `langgraph/agent/coding_agent/` — Autonomous code generation
- [x] `langgraph/agent/customer_support/` — Multi-turn support with tools

## Phase 3: AWS Strands Agents Implementation

- [x] `strands/workflow/prompt_chaining/` — Sequential LLM calls with gates
- [x] `strands/workflow/routing/` — Input classification and dispatch
- [x] `strands/workflow/parallelization/` — Fan-out and aggregation
- [x] `strands/workflow/orchestrator_workers/` — Dynamic decomposition
- [x] `strands/workflow/evaluator_optimizer/` — Generate-critique loop
- [x] `strands/agent/coding_agent/` — Autonomous code generation
- [x] `strands/agent/customer_support/` — Multi-turn support with tools
- [x] `strands/_ollama_adapter/` — Custom Ollama model provider for Strands

## Phase 4: Hermes Implementation

- [ ] `hermes/foundation/augmented_llm/` — Augmented LLM pattern as Hermes CLI app
- [ ] `hermes/workflow/prompt_chaining/` — Prompt chaining pattern as Hermes CLI app
- [ ] `hermes/workflow/routing/` — Routing pattern as Hermes CLI app
- [ ] `hermes/workflow/parallelization/` — Parallelization pattern as Hermes CLI app
- [ ] `hermes/workflow/orchestrator_workers/` — Orchestrator-workers pattern as Hermes CLI app
- [ ] `hermes/workflow/evaluator_optimizer/` — Evaluator-optimizer pattern as Hermes CLI app
- [ ] `hermes/agent/coding_agent/` — Coding agent pattern as Hermes CLI app
- [ ] `hermes/agent/customer_support/` — Customer support pattern as Hermes CLI app
- [ ] Define Hermes tool consumption approach (MCP, native, or hybrid — TBD)
- [ ] Ensure all 8 apps conform to the CLI contract (JSON on stdout)

## Phase 5: Evaluation Harness

- [x] `eval/src/eval/runner.py` — Discover leaf dirs, invoke CLI, collect JSON results
- [x] `eval/src/eval/report.py` — Generate comparison tables (Markdown + CSV)
- [x] `eval/pyproject.toml` — Harness dependencies
- [ ] Golden dataset with expected answers for accuracy scoring
- [ ] Makefile targets: `make eval`, `make eval FRAMEWORK=<name>`, `make report`
- [ ] Extended metrics collection (peak memory, cold start, determinism)
- [ ] Final comparison report across all 3 frameworks × 8 patterns
