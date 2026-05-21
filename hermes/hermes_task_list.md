# Hermes Agent — Next Steps (Implementation Plan)

## Goal

Create a `hermes/` directory implementing the **same 5 workflow + 3 agent patterns** as `langgraph/` and `strands/` for a 3-way framework comparison. Uses Ollama with Hermes-3 model.

## Approach

Unlike LangGraph (graph DSL) and Strands (Agent SDK), the Hermes approach uses:
- **No framework SDK** — the "framework" is a custom execution loop
- **Hermes-3 model** on Ollama with native `<tool_call>` XML function calling
- **Direct XML parsing** of model responses to detect and dispatch tool calls
- **Same `_shared/` infrastructure** (MCP server, config, metrics, tasks)

---

## Task List

### Foundation (Tasks 1–4)

| # | Task | Description | Deps |
|---|------|-------------|------|
| 1 | **Scaffold `hermes/` directory** | Create hermes/ with README.md, mirroring langgraph/ and strands/ layout (`foundation/`, `workflow/`, `agent/` subdirs) | — |
| 2 | **Ollama adapter/client module** | Create `hermes/_ollama_client/` with pyproject.toml and src providing Hermes-3 chat completion with `<tool_call>` XML parsing | — |
| 3 | **Core execution loop** | Build `hermes/_core/` with tool-call detection, XML parsing, tool dispatch, and response assembly (the custom agentic loop) | 2 |
| 4 | **Shared integration layer** | Wire `_shared/` MCP tool stubs, config, and MetricsCollector into hermes core so all patterns report identical metrics | 3 |

### Workflow Patterns (Tasks 5–9)

| # | Task | Description | Deps |
|---|------|-------------|------|
| 5 | **workflow/prompt_chaining** | Multi-step prompt chain passing output of one call as input to next, with gate functions between steps | 4 |
| 6 | **workflow/routing** | Classifier-based routing that directs input to specialized prompts/tools based on Hermes-3 classification | 4 |
| 7 | **workflow/parallelization** | Fan-out/fan-in using `asyncio.gather` over parallel Hermes-3 calls with independent tool sets | 4 |
| 8 | **workflow/orchestrator_workers** | Orchestrator decomposes tasks, dispatches to worker agents, synthesizes results | 4 |
| 9 | **workflow/evaluator_optimizer** | Generate-then-evaluate loop where evaluator scores output and optimizer retries until threshold met | 4 |

### Agent Patterns (Tasks 10–12)

| # | Task | Description | Deps |
|---|------|-------------|------|
| 10 | **foundation/augmented_llm** | Single-turn tool-augmented LLM using Hermes-3 function calling with MCP tools | 4 |
| 11 | **agent/coding_agent** | Multi-tool coding agent with file read/write/exec tools, using iterative tool-call loop until task complete | 10 |
| 12 | **agent/customer_support** | Customer support agent with KB lookup, ticket creation, and escalation tools via MCP | 10 |

### Integration & Documentation (Tasks 13–14)

| # | Task | Description | Deps |
|---|------|-------------|------|
| 13 | **Shared task runner integration** | Ensure all hermes patterns are callable from `_shared/tasks.py` for unified eval harness | 5–12 |
| 14 | **README + comparison docs** | Document Hermes-3 approach, architecture diagram, and 3-way comparison notes | 13 |

---

## Key Design Decisions

- **Tasks 1–2 are parallelizable** (scaffolding + adapter can be done simultaneously)
- **Tasks 5–10 are parallelizable** once the core (Task 4) is complete
- **Hermes differentiator**: No framework SDK — the "framework" is a custom execution loop that parses `<tool_call>` XML from Hermes-3 model responses and dispatches to MCP tools
- **Same Ollama backend** as LangGraph (`ChatOllama`) and Strands (`ollama_adapter`) but using the Hermes-3 model's native function-calling format
- **Metrics parity** ensures fair eval across all three

---

## Dependency Graph

```
[1] Scaffold ──┐
               ├──► [4] Shared Integration ──► [5-10] All Patterns ──► [13] Task Runner ──► [14] README
[2] Adapter ──►[3] Core Loop ──┘
```

## Status

- [ ] Task 1: Scaffold hermes/ directory
- [ ] Task 2: Ollama adapter/client module
- [ ] Task 3: Core execution loop
- [ ] Task 4: Shared integration layer
- [ ] Task 5: workflow/prompt_chaining
- [ ] Task 6: workflow/routing
- [ ] Task 7: workflow/parallelization
- [ ] Task 8: workflow/orchestrator_workers
- [ ] Task 9: workflow/evaluator_optimizer
- [ ] Task 10: foundation/augmented_llm
- [ ] Task 11: agent/coding_agent
- [ ] Task 12: agent/customer_support
- [ ] Task 13: Shared task runner integration
- [ ] Task 14: README + comparison docs
