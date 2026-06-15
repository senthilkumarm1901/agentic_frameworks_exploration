# LangGraph Patterns

LangGraph implementation of 6 agentic patterns for the "6 Patterns × 3 Frameworks × 1 LLM" evaluation.

## Taxonomy

```text
langgraph/
    agents/
        1_agent_with_multiple_mcp_tools/
        2_agent_with_rag_mcp_tool/
        3_agent_with_mcp_tools_and_skills/
    workflows/
        4_workflow_2_layer_sequential/
        5_workflow_3_layer_routing/
        6_workflow_2_layer_parallelization/
```

## Status

| Path | Status | Notes |
|------|--------|-------|
| `agents/1_agent_with_multiple_mcp_tools` | Implemented | ReAct agent with MCP tools |
| `agents/2_agent_with_rag_mcp_tool` | Placeholder | README only |
| `agents/3_agent_with_mcp_tools_and_skills` | Placeholder | README only |
| `workflows/4_workflow_2_layer_sequential` | Placeholder | README only |
| `workflows/5_workflow_3_layer_routing` | Placeholder | README only |
| `workflows/6_workflow_2_layer_parallelization` | Placeholder | README only |

## Pattern Index

### Agents

- `1_agent_with_multiple_mcp_tools`: ReAct agent with multiple MCP-backed tools for country-data question answering.
- `2_agent_with_rag_mcp_tool`: Extending Pattern 1 with a RAG MCP Tool.
- `3_agent_with_mcp_tools_and_skills`: Extending Pattern 2 with Skills.

### Workflows

- `4_workflow_2_layer_sequential`: Two-layer sequential workflow.
- `5_workflow_3_layer_routing`: Three-layer routing workflow.
- `6_workflow_2_layer_parallelization`: Two-layer parallelization workflow.

