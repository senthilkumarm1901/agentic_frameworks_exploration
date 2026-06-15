# Pattern 3: Agent with MCP Tools and Skills

Hermes Pattern 3 adds a local skill-loading tool on top of Pattern 2's MCP tools and RAG search. The agent mirrors the LangGraph and Strands Pattern 3 behavior in `logs.txt` while keeping Hermes-style runtime conventions: `HermesAgent`, `quiet_mode=True`, `skip_memory=True`, `skip_context_files=True`, and `run_conversation()` as the primary execution path.

## What It Does

The agent:

1. Discovers available skills in the system prompt.
2. Activates the relevant skill on demand via `activate_skill(skill_name)`.
3. Uses the same MCP server as Pattern 2 for:
   - `country_lookup_tool`
   - `calculator_tool`
   - `country_kb_search_tool`
4. Emits a log payload that matches the existing Pattern 3 experiment structure.

## Skills

The available skills live in `_shared/skills`:

- `country-comparison`
- `country-profile`
- `regional-analysis`
- `report-formatting`

## Usage

```bash
cd hermes/agents/3_agent_with_mcp_tools_and_skills
uv sync
uv run python -m src.main --task country_analysis --question "Compare Japan and Germany by GDP and population"
```

To run the benchmark-style experiments:

```bash
bash experiments.bash
```

## Files

- `src/agent.py` implements the Hermes-style ReAct loop.
- `src/skill_tools.py` exposes the local skill loader and discovery prompt.
- `src/prompts.py` injects skill guidance into the system prompt.
- `src/main.py` writes `logs.txt` and emits JSON metrics.