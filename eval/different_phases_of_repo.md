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

- [x] `langgraph/agents/1_agent_with_multiple_mcp_tools/` — LangGraph augmented LLM with multiple MCP-backed tools
- [x] Verify conformant JSON output for `augmented_qa` task

Note: Strands and Hermes will implement the augmented LLM pattern as part of their respective 6-pattern implementations (Pattern 1 in Phases 3 and 4).

## Phase 2: LangGraph Workflow & Agent Patterns

- [ ] `langgraph/agents/2_agent_with_rag_mcp_tool/` — Placeholder README only in the current wave
- [ ] `langgraph/agents/3_agent_with_mcp_tools_and_skills/` — Placeholder README only in the current wave
- [ ] `langgraph/workflows/4_workflow_2_layer_sequential/` — Placeholder README only in the current wave
- [ ] `langgraph/workflows/5_workflow_3_layer_routing/` — Placeholder README only in the current wave
- [ ] `langgraph/workflows/6_workflow_2_layer_parallelization/` — Placeholder README only in the current wave
- [ ] Later waves will populate patterns 2-6 with migrated implementations and runnable scaffolding as separately approved work

## Phase 3: AWS Strands Agents Implementation

- [ ] `strands/agents/1_agent_with_multiple_mcp_tools/` — Agent with multiple MCP tools
- [ ] `strands/agents/2_agent_with_rag_mcp_tool/` — Extending Agent Pattern 1 with a RAG MCP Tool
- [ ] `strands/agents/3_agent_with_mcp_tools_and_skills/` — Extending Agent Pattern 2 with Skills
- [ ] `strands/workflows/4_workflow_2_layer_sequential/` — Two-layer sequential workflow
- [ ] `strands/workflows/5_workflow_3_layer_routing/` — Three-layer routing workflow
- [ ] `strands/workflows/6_workflow_2_layer_parallelization/` — Two-layer parallel workflow
- [x] `strands/_ollama_adapter/` — Custom Ollama model provider for Strands

## Phase 4: Hermes Implementation

- [ ] `hermes/agents/1_agent_with_multiple_mcp_tools/` — Agent with multiple MCP tools as Hermes CLI app
- [ ] `hermes/agents/2_agent_with_rag_mcp_tool/` — Agent with RAG MCP tool as Hermes CLI app
- [ ] `hermes/agents/3_agent_with_mcp_tools_and_skills/` — Agent with MCP tools and skills as Hermes CLI app
- [ ] `hermes/workflows/4_workflow_2_layer_sequential/` — Two-layer sequential workflow as Hermes CLI app
- [ ] `hermes/workflows/5_workflow_3_layer_routing/` — Three-layer routing workflow as Hermes CLI app
- [ ] `hermes/workflows/6_workflow_2_layer_parallelization/` — Two-layer parallel workflow as Hermes CLI app
- [ ] Define Hermes tool consumption approach (MCP, native, or hybrid — TBD)
- [ ] Ensure all 6 apps conform to the CLI contract (JSON on stdout)

## Phase 5: Evaluation Harness

- [x] `eval/src/eval/runner.py` — Discover leaf dirs, invoke CLI, collect JSON results
- [x] `eval/src/eval/report.py` — Generate comparison tables (Markdown + CSV)
- [x] `eval/pyproject.toml` — Harness dependencies
- [ ] Golden dataset with expected answers for accuracy scoring
- [ ] Makefile targets: `make eval`, `make eval FRAMEWORK=<name>`, `make report`
- [ ] Extended metrics collection (peak memory, cold start, determinism)
- [ ] Final comparison report across all 3 frameworks × 6 patterns (18 total apps)
