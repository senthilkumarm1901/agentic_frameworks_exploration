

## 1_agent_with_mcp_tools

```mermaid
graph LR
    Q["❓ Question"] --> A["🤖 ReAct Agent<br/><i>LangGraph + Ollama</i>"]
    A <-->|"MCP stdio"| S["🔌 FastMCP Server\n(Tools Registry)"]
    S --> T1["🔍 country_lookup\n(tool 1)"]
    S --> T2["🧮 calculator\n(tool 2)"]
    T1 --> D[("📊 countries.json")]
    A --> R["✅ Answer + Metrics"]

    style A fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    style S fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    style D fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
```


---

## 2_agent_with_rag_mcp_tool

```mermaid
graph LR
    Q["❓ Question"] --> A["🤖 ReAct Agent<br/><i>LangGraph + Ollama</i>"]
    A <-->|"MCP stdio"| S["🔌 FastMCP Server<br/>(Tool Registry)"]
    S --> T1["🔍 country_lookup<br/>(structured data)"]
    S --> T2["🧮 calculator<br/>(arithmetic)"]
    S --> T3["📚 country_kb_search<br/>(semantic RAG)"]
    T1 --> D1["(📊 countries.json<br/><i>quantitative</i>)"]
    T3 --> EMB["🧠 all-MiniLM-L6-v2<br/>(384-dim embeddings)"]
    EMB --> D2["(🗄️ Milvus-Lite<br/>country_kb.db)"]
    D2 -.->|"indexed from"| MD["📝 20 × country .md<br/><i>qualitative facts</i>"]
    A --> R["✅ Answer + Metrics"]

    style A fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    style S fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    style D1 fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    style D2 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    style EMB fill:#FCE4EC,stroke:#C62828,stroke-width:2px
    style T3 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,stroke-dasharray: 0
    style MD fill:#FFF9C4,stroke:#F9A825,stroke-width:1px
```

---

### 3_agent_with_mcp_tools_and_skills

```mermaid
graph TB
    Q["User: Compare India and Japan"]
    subgraph PHASE1["Phase 1: Skill Discovery"]
        SP["First System Prompt includes (basic skill info):<br/><code>&lt;skills&gt;</code><br/><br/>- country-comparison: Compare countries<br/><br/>- country-profile: Build country brief<br/><br/>- regional-analysis: Regional patterns<br/><br/>- report-formatting: Format as report<br/><br/><code>&lt;/skills&gt;</code>"]
    end
    Q --> SP

    subgraph PHASE2["Phase 2: Specific Skill Activation"]
        LLM1["LLM reasons:<br/>'I need country-comparison skill'"]
        LOAD["activate_skill('country-comparison')<br/>→ returns full SKILL.md content"]
        LLM1 --> LOAD
    end

    subgraph PHASE3["Phase 3: Tool Execution via Skills Specified"]
        direction LR
        STEP1["Step 1: Identify dimensions"]
        STEP2["Step 2: country_lookup"]
        STEP3["Step 3: calculator"]
        STEP4["Step 4: country_kb_search"]
        STEP5["Step 5: Synthesize comparison"]
        STEP1 --> STEP2 --> STEP3 --> STEP4 --> STEP5
    end

    PHASE1 -.->|"User Question plus `Skill Discovery` System Prompt"| PHASE2
    PHASE2 -->|"User Question plus full instructions<br/>loaded on demand"| PHASE3
    PHASE3 -->|"tools called<br/>via MCP"| MCP["🔌 FastMCP Server<br/>(same 3 tools as Pattern 2)"]

    classDef phase1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    classDef phase2 fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef phase3 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px

    class SP phase1
    class Q,LLM1,LOAD phase2
    class STEP1,STEP2,STEP3,STEP4,STEP5 phase3

```




---

## 4_agent_with_memory_and_chat

```mermaid
graph LR
    subgraph CHAT["🖥️ Terminal Chat REPL"]
        USER["👤 User Input"]
        DISPLAY["📺 Chat Display<br/><i>skills · tools · answer</i>"]
    end

    subgraph MEMORY["🧠 Memory Layer"]
        SHORT["<b>Short-Term</b><br/>MemorySaver<br/><i>full message history</i><br/><code>thread_id</code>"]
        LONG["<b>Long-Term Summary</b><br/>LLM-compressed<br/><i>structured format</i>"]
        DISK[("session.json<br/><i>persists across restarts</i>")]
        LONG --> DISK
    end

    subgraph AGENT["🤖 ReAct Agent"]
        PROMPT["System Prompt<br/>+ Memory Block<br/>+ Skill Metadata"]
        REACT["LangGraph Agent<br/><code>checkpointer=MemorySaver</code>"]
    end

    USER -->|"question"| REACT
    LONG -.->|"frozen snapshot"| PROMPT
    PROMPT --> REACT
    REACT --> SHORT
    SHORT -->|"after turn"| LONG

    REACT -->|"activate_skill()"| SK["📋 Skills"]
    REACT <-->|"MCP stdio"| MCP["🔌 FastMCP<br/>(3 tools)"]

    REACT --> DISPLAY

    classDef chat fill:#ECEFF1,stroke:#455A64,stroke-width:2px
    classDef memory fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px

    class USER,DISPLAY chat
    class SHORT,LONG,DISK memory
    class PROMPT,REACT agent
```

---

## 5_agent_with_memory_and_chat_no_rag


```mermaid
graph LR
    subgraph CHAT["🖥️ Terminal Chat REPL"]
        USER["👤 User Input"]
    end

    subgraph MEMORY["🧠 Memory"]
        SHORT["Short-Term<br/><i>MemorySaver</i>"]
        LONG["Long-Term<br/><i>session.json</i>"]
    end

    subgraph AGENT["🤖 ReAct Agent<br/><i>LangGraph + Ollama</i>"]
        PROMPT["System Prompt<br/>+ Memory + Skill Metadata"]
    end

    subgraph SKILLS["📋 Skills<br/><i>loaded on demand</i>"]
        S1["country-comparison"]
        S2["country-profile"]
        S3["regional-analysis"]
        S4["report-formatting"]
    end

    subgraph MCP["🔌 FastMCP Server<br/>(Tool Registry)"]
        T1["🔍 country_lookup"]
        T2["🧮 calculator"]
        T3["📖 wiki_read<br/><i>replaces kb_search</i>"]
    end

    subgraph WIKI_LAYER["📚 LLM Wiki<br/><i>replaces Milvus RAG</i>"]
        INDEX["index.md<br/><i>page catalog</i>"]
        subgraph ENTITIES["Entity Pages"]
            E1["india.md"]
            E2["japan.md"]
            E3["...18 more"]
        end
        subgraph CONCEPTS["Concept Pages"]
            C1["demographics.md"]
            C2["trade_and_economy.md"]
            C3["geography.md"]
        end
        COMP["comparisons.md"]
    end

    subgraph RAW["📝 Raw Sources<br/><i>immutable</i>"]
        RAW_MD["20 × country .md<br/><i>original facts</i>"]
        RAW_JSON[("countries.json<br/><i>quantitative</i>")]
    end

    USER --> AGENT
    LONG -.->|"frozen snapshot"| PROMPT
    PROMPT --> AGENT
    AGENT --> SHORT
    SHORT -->|"after turn"| LONG

    AGENT -->|"activate_skill()"| SKILLS
    AGENT <-->|"MCP stdio"| MCP
    T1 --> RAW_JSON
    T3 -->|"reads pages<br/>via index"| INDEX
    INDEX --> ENTITIES
    INDEX --> CONCEPTS
    INDEX --> COMP

    RAW_MD -.->|"compiled once<br/>by LLM"| WIKI_LAYER

    AGENT --> DISPLAY["✅ Structured Answer"]

    classDef chat fill:#ECEFF1,stroke:#455A64,stroke-width:2px
    classDef memory fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef agent fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef wiki fill:#D6EAF8,stroke:#2471A3,stroke-width:2px
    classDef raw fill:#FFF9C4,stroke:#F9A825,stroke-width:1px,stroke-dasharray: 5 5
    classDef mcp fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px

    class USER chat
    class SHORT,LONG memory
    class PROMPT,AGENT agent
    class INDEX,E1,E2,E3,C1,C2,C3,COMP wiki
    class RAW_MD,RAW_JSON raw
    class T1,T2,T3 mcp
```
---

## All 5 Patterns 


```mermaid
graph TB
    subgraph P1["Pattern 1: Agent + MCP Tools"]
        P1_A["🤖 ReAct Agent"]
        P1_T["🔌 MCP: country_lookup + calculator"]
        P1_D[("📊 countries.json")]
        P1_A <--> P1_T --> P1_D
    end

    subgraph P2["Pattern 2: + RAG MCP Tool"]
        P2_A["🤖 ReAct Agent"]
        P2_T["🔌 MCP: lookup + calc + <b>kb_search</b>"]
        P2_D[("📊 JSON + 🗄️ Milvus")]
        P2_A <--> P2_T --> P2_D
    end

    subgraph P3["Pattern 3: + Skills"]
        P3_A["🤖 ReAct Agent"]
        P3_S["📋 Skills<br/><i>progressive disclosure</i>"]
        P3_T["🔌 MCP: 3 tools"]
        P3_A --> P3_S
        P3_A <--> P3_T
    end

    subgraph P4["Pattern 4: + Memory & Chat"]
        P4_A["🤖 ReAct Agent"]
        P4_M["🧠 Memory<br/><i>short + long term</i>"]
        P4_S["📋 Skills"]
        P4_T["🔌 MCP: 3 tools"]
        P4_C["🖥️ Chat REPL"]
        P4_C --> P4_A
        P4_M -.-> P4_A
        P4_A --> P4_S
        P4_A <--> P4_T
    end

    subgraph P5["Pattern 5: + LLM Wiki (no RAG)"]
        P5_A["🤖 ReAct Agent"]
        P5_M["🧠 Memory"]
        P5_S["📋 Skills"]
        P5_T["🔌 MCP: lookup + calc + <b>wiki_read</b>"]
        P5_W["📚 LLM Wiki<br/><i>index + entities + concepts</i>"]
        P5_R["📝 Raw Sources<br/><i>immutable .md files</i>"]
        P5_C["🖥️ Chat REPL"]
        P5_C --> P5_A
        P5_M -.-> P5_A
        P5_A --> P5_S
        P5_A <--> P5_T
        P5_T --> P5_W
        P5_R -.->|"compiled once"| P5_W
    end

    P1 -->|"+RAG"| P2
    P2 -->|"+Skills"| P3
    P3 -->|"+Memory"| P4
    P4 -->|"RAG→Wiki"| P5

    classDef p1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    classDef p2 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef p3 fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef p4 fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    classDef p5 fill:#D6EAF8,stroke:#2471A3,stroke-width:2px

    class P1_A,P1_T,P1_D p1
    class P2_A,P2_T,P2_D p2
    class P3_A,P3_S,P3_T p3
    class P4_A,P4_M,P4_S,P4_T,P4_C p4
    class P5_A,P5_M,P5_S,P5_T,P5_W,P5_R,P5_C p5
```