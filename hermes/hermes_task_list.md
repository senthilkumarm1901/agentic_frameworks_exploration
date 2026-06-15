
## First Goal: Create Pattern 1 


Create a Hermes Codebase that does exactly like Strands/Langgraph (in terms of logs.txt) but incorporates the standard pracrtices of hermes library

to design pattern 1 

Read the docs thoroughly: 

```mermaid
graph LR
    Q["❓ Question"] --> A["🤖 ReAct Agent<br/><i>Framework + Ollama</i>"]
    A <-->|"MCP stdio"| S["🔌 FastMCP Server\n(Tools Registry)"]
    S --> T1["🔍 country_lookup\n(tool 1)"]
    S --> T2["🧮 calculator\n(tool 2)"]
    T1 --> D[("📊 countries.json")]
    A --> R["✅ Answer + Metrics"]

    style A fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    style S fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    style D fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
```



Output folder: hermes/agents/1_agent_with_multiple_mcp_tools

Inspiration from: 
- langgraph/agents/1_agent_with_multiple_mcp_tools
- strands/agents/1_agent_with_multiple_mcp_tools


Necessary file/folder structure (Add more codebase if hermes wants it)

```
./langgraph/agents/1_agent_with_multiple_mcp_tools
├── README.md
├── experiments.bash
├── logs.txt
├── pyproject.toml
├── src
│   ├── __init__.py
│   ├── __pycache__
│   ├── agent.py
│   ├── main.py
│   └── prompts.py
└── uv.lock
```

---
