# Building Effective Agents — Anthropic Blog

[original blog source](https://www.anthropic.com/engineering/building-effective-agents)

---

## What Are Agents?

Anthropic draws an important architectural distinction within _agentic systems_: 

- **Workflows** — Systems where LLMs and tools are orchestrated through **predefined code paths**.
- **Agents** — Systems where LLMs **dynamically direct their own processes** and tool usage, maintaining control over how they accomplish tasks.

---

## When (and When Not) to Use Agents

The recommendation is to find the **simplest solution possible**, and only increase complexity when needed. Agentic systems trade latency and cost for better task performance — you should consider when this tradeoff makes sense. 

- **Workflows** → predictability and consistency for well-defined tasks.
- **Agents** → flexibility and model-driven decision-making at scale.
- For many apps, **optimizing single LLM calls** with retrieval and in-context examples is enough.

---

## When and How to Use Frameworks

Frameworks (Claude Agent SDK, Strands Agents SDK, Rivet, Vellum, etc.) simplify low-level tasks but can create extra abstraction layers that obscure prompts/responses and make debugging harder. 

> **Recommendation**: Start by using LLM APIs directly. If you use a framework, ensure you understand the underlying code.

---

## Building Blocks, Workflows, and Agents

### 🧱 Building Block: The Augmented LLM

The foundational building block is an LLM enhanced with **retrieval**, **tools**, and **memory**. Current models can actively use these capabilities — generating search queries, selecting tools, and determining what information to retain. 

```mermaid
graph LR
    I["📥 Input"] --> LLM["🧠 LLM"]
    R["🔍 Retrieval"] --> LLM
    T["🛠️ Tools"] --> LLM
    M["💾 Memory"] --> LLM
    LLM --> O["📤 Output"]

    style LLM fill:#4A90D9,stroke:#333,color:#fff
    style R fill:#F5A623,stroke:#333,color:#fff
    style T fill:#7ED321,stroke:#333,color:#fff
    style M fill:#BD10E0,stroke:#333,color:#fff
    style O fill:#9B9B9B,stroke:#333,color:#fff

```
**Key implementation aspects:**

1. Tailor capabilities to your specific use case
2. Ensure an easy, well-documented interface for your LLM (e.g., via Model Context Protocol)

---

### ⛓️ Workflow: Prompt Chaining

Decomposes a task into a **sequence of steps**, where each LLM call processes the output of the previous one. Programmatic checks ("gates") can be added on intermediate steps to ensure the process stays on track. 

```mermaid
graph LR
    I["📥 Input"] --> LLM1["🧠 LLM\nCall 1"]
    LLM1 --> G{"🚦 Gate\n(Check)"}
    G -->|Pass| LLM2["🧠 LLM\nCall 2"]
    G -->|Fail| EXIT["🚫 Exit /\nRevise"]
    LLM2 --> LLM3["🧠 LLM\nCall 3"]
    LLM3 --> O["📤 Output"]

    style I fill:#9B9B9B,stroke:#333,color:#fff
    style LLM1 fill:#4A90D9,stroke:#333,color:#fff
    style LLM2 fill:#4A90D9,stroke:#333,color:#fff
    style LLM3 fill:#4A90D9,stroke:#333,color:#fff
    style G fill:#F5A623,stroke:#333,color:#000
    style EXIT fill:#D0021B,stroke:#333,color:#fff
    style O fill:#9B9B9B,stroke:#333,color:#fff
```

**When to use**: Tasks that can be easily decomposed into **fixed subtasks** — trading latency for higher accuracy.

**Examples**:

- Generate marketing copy → translate into a different language
- Write an outline → check criteria → write the document based on the outline

---

### 🔀 Workflow: Routing

Classifies an input and directs it to a **specialized follow-up task**. Allows separation of concerns and more specialized prompts. Without routing, optimizing for one kind of input can hurt performance on others. 

```mermaid
graph TD
    I["📥 Input"] --> R["🧠 LLM\nRouter /\nClassifier"]
    R -->|Category A| A["🧠 LLM\nSpecialized\nProcess A"]
    R -->|Category B| B["🧠 LLM\nSpecialized\nProcess B"]
    R -->|Category C| C["🧠 LLM\nSpecialized\nProcess C"]

    style I fill:#9B9B9B,stroke:#333,color:#fff
    style R fill:#F5A623,stroke:#333,color:#000
    style A fill:#4A90D9,stroke:#333,color:#fff
    style B fill:#7ED321,stroke:#333,color:#fff
    style C fill:#BD10E0,stroke:#333,color:#fff

```

**When to use**: Complex tasks with **distinct categories** better handled separately, where classification can be done accurately.

**Examples**:

- Directing customer service queries (general, refund, technical) into different downstream processes
- Routing easy questions to smaller models (Claude Haiku 4.5) and hard questions to more capable models (Claude Sonnet 4.5)

---

### ⚡ Workflow: Parallelization

LLMs work **simultaneously** on a task and have their outputs aggregated programmatically. Two key variations: 

- **Sectioning** — Breaking a task into independent subtasks run in parallel
- **Voting** — Running the same task multiple times to get diverse outputs

```mermaid
graph TD
    subgraph Sectioning
        I1["📥 Input"] --> LLM_A["🧠 LLM\nSubtask A"]
        I1 --> LLM_B["🧠 LLM\nSubtask B"]
        I1 --> LLM_C["🧠 LLM\nSubtask C"]
        LLM_A --> AGG1["🔗 Aggregator"]
        LLM_B --> AGG1
        LLM_C --> AGG1
        AGG1 --> O1["📤 Output"]
    end

    subgraph Voting
        I2["📥 Input"] --> V1["🧠 LLM\nAttempt 1"]
        I2 --> V2["🧠 LLM\nAttempt 2"]
        I2 --> V3["🧠 LLM\nAttempt 3"]
        V1 --> AGG2["🗳️ Vote\nAggregator"]
        V2 --> AGG2
        V3 --> AGG2
        AGG2 --> O2["📤 Output"]
    end

    style I1 fill:#9B9B9B,stroke:#333,color:#fff
    style I2 fill:#9B9B9B,stroke:#333,color:#fff
    style LLM_A fill:#4A90D9,stroke:#333,color:#fff
    style LLM_B fill:#4A90D9,stroke:#333,color:#fff
    style LLM_C fill:#4A90D9,stroke:#333,color:#fff
    style V1 fill:#7ED321,stroke:#333,color:#fff
    style V2 fill:#7ED321,stroke:#333,color:#fff
    style V3 fill:#7ED321,stroke:#333,color:#fff
    style AGG1 fill:#F5A623,stroke:#333,color:#000
    style AGG2 fill:#F5A623,stroke:#333,color:#000
    style O1 fill:#9B9B9B,stroke:#333,color:#fff
    style O2 fill:#9B9B9B,stroke:#333,color:#fff
```

**When to use**: Subtasks can be parallelized for speed, or multiple perspectives are needed for higher confidence.

**Examples**:

- **Sectioning**: Guardrails (one model handles queries, another screens for inappropriate content); automated evals
- **Voting**: Code vulnerability review with multiple prompts; content moderation with different vote thresholds

---

### 🎼 Workflow: Orchestrator-Workers

A **central LLM dynamically breaks down tasks**, delegates them to worker LLMs, and synthesizes their results. Key difference from parallelization: subtasks are **not pre-defined** but determined by the orchestrator based on the specific input. 

```mermaid
graph TD
    I["📥 Input"] --> O["🧠 Orchestrator\nLLM"]
    O -->|"Delegate\nTask 1"| W1["🧠 Worker\nLLM 1"]
    O -->|"Delegate\nTask 2"| W2["🧠 Worker\nLLM 2"]
    O -->|"Delegate\nTask N"| W3["🧠 Worker\nLLM N"]
    W1 -->|Result| S["🔗 Synthesizer\n(Orchestrator)"]
    W2 -->|Result| S
    W3 -->|Result| S
    S --> OUT["📤 Output"]

    style I fill:#9B9B9B,stroke:#333,color:#fff
    style O fill:#F5A623,stroke:#333,color:#000
    style W1 fill:#4A90D9,stroke:#333,color:#fff
    style W2 fill:#4A90D9,stroke:#333,color:#fff
    style W3 fill:#4A90D9,stroke:#333,color:#fff
    style S fill:#F5A623,stroke:#333,color:#000
    style OUT fill:#9B9B9B,stroke:#333,color:#fff
```

**When to use**: Complex tasks where you **can't predict** the subtasks needed.

**Examples**:

- Coding products that make complex changes to multiple files
- Search tasks gathering and analyzing information from multiple sources

---

### 🔄 Workflow: Evaluator-Optimizer

One LLM call **generates** a response while another **provides evaluation and feedback** in a loop. 

```mermaid
graph LR
    I["📥 Input"] --> G["🧠 Generator\nLLM"]
    G --> R["📄 Response"]
    R --> E["🧠 Evaluator\nLLM"]
    E -->|"Accepted ✅"| O["📤 Final\nOutput"]
    E -->|"Feedback 🔁"| G

    style I fill:#9B9B9B,stroke:#333,color:#fff
    style G fill:#4A90D9,stroke:#333,color:#fff
    style R fill:#D8D8D8,stroke:#333,color:#000
    style E fill:#7ED321,stroke:#333,color:#fff
    style O fill:#9B9B9B,stroke:#333,color:#fff
```


**When to use**: Clear evaluation criteria exist, and iterative refinement provides measurable value. Two signs of good fit: (1) LLM responses improve demonstrably with human-like feedback, (2) the LLM can provide such feedback. 

**Examples**:

- Literary translation where an evaluator LLM provides useful critiques
- Complex search tasks requiring multiple rounds of searching and analysis

---

### 🤖 Agents (Autonomous)

Agents begin with a command from (or interactive discussion with) the human user. Once the task is clear, they **plan and operate independently**, potentially returning to the human for further information or judgement. At each step, agents gain "ground truth" from the environment (tool call results, code execution) to assess progress. 

```mermaid
graph TD
    H["👤 Human"] -->|"Task / Command"| A["🧠 Agent\nLLM"]
    A -->|"Plan & Act"| T["🛠️ Tool /\nEnvironment"]
    T -->|"Result /\nFeedback"| A
    A -->|"Checkpoint /\nBlocker"| H
    A -->|"Task Complete\nor Stop Condition"| O["📤 Final\nOutput"]

    style H fill:#F5A623,stroke:#333,color:#000
    style A fill:#4A90D9,stroke:#333,color:#fff
    style T fill:#7ED321,stroke:#333,color:#fff
    style O fill:#9B9B9B,stroke:#333,color:#fff

```

> Agents are typically just **LLMs using tools based on environmental feedback in a loop**. It is therefore crucial to design toolsets and their documentation clearly and thoughtfully.

**When to use**: Open-ended problems where you can't predict the number of steps or hardcode a fixed path. Requires trust in the LLM's decision-making. 

**Examples**:

- A coding agent to resolve SWE-bench tasks
- "Computer use" reference implementation where Claude uses a computer to accomplish tasks

```mermaid
sequenceDiagram
    participant Human
    participant Interface
    participant LLM
    participant Environment

    Human->>Interface: Query

    rect rgb(245, 245, 245)
        Note over Interface,LLM: Until tasks clear
        Interface->>LLM: Clarify
        LLM-->>Interface: Refine
    end

    Interface->>LLM: Send context

    LLM->>Environment: Search files
    Environment-->>LLM: Return paths

    rect rgb(245, 245, 245)
        Note over LLM,Environment: Until tests pass
        LLM->>Environment: Write code
        Environment-->>LLM: Status
        LLM->>Environment: Test
        Environment-->>LLM: Results
    end

    LLM-->>Interface: Complete
    Interface-->>Human: Display

```

---

### 💻 High-Level Flow of a Coding Agent

```mermaid
graph TD
    TASK["📋 Task\nDescription"] --> PLAN["🧠 Agent:\nUnderstand &\nPlan"]
    PLAN --> EDIT["✏️ Edit\nCode Files"]
    EDIT --> RUN["▶️ Run\nTests"]
    RUN -->|"Tests Fail ❌"| DEBUG["🔍 Debug &\nAnalyze Errors"]
    DEBUG --> EDIT
    RUN -->|"Tests Pass ✅"| REVIEW["🔎 Final\nReview"]
    REVIEW -->|"Issues Found"| EDIT
    REVIEW -->|"All Good ✅"| DONE["✅ Submit\nSolution"]

    style TASK fill:#9B9B9B,stroke:#333,color:#fff
    style PLAN fill:#4A90D9,stroke:#333,color:#fff
    style EDIT fill:#F5A623,stroke:#333,color:#000
    style RUN fill:#7ED321,stroke:#333,color:#fff
    style DEBUG fill:#D0021B,stroke:#333,color:#fff
    style REVIEW fill:#BD10E0,stroke:#333,color:#fff
    style DONE fill:#417505,stroke:#333,color:#fff
```
---

## Combining and Customizing These Patterns

These building blocks aren't prescriptive — they're common patterns that developers can shape and combine to fit different use cases. The key to success is **measuring performance and iterating on implementations**. Add complexity only when it demonstrably improves outcomes. 

---

## Summary

Success in the LLM space isn't about building the most sophisticated system — it's about building the **right system** for your needs. 

**Three core principles for implementing agents:**

1. **Maintain simplicity** in your agent's design
2. **Prioritize transparency** by explicitly showing the agent's planning steps
3. **Carefully craft your agent-computer interface (ACI)** through thorough tool documentation and testing

---

## Appendix 1: Agents in Practice

### A. Customer Support

A natural fit for open-ended agents because support interactions follow a conversation flow while requiring access to external information/actions. Tools pull customer data, order history, knowledge base articles; actions like refunds or ticket updates are handled programmatically; success is clearly measurable. 

### B. Coding Agents

Particularly effective because code solutions are verifiable through automated tests, agents can iterate using test results as feedback, the problem space is well-defined, and output quality can be measured objectively. 

---

## Appendix 2: Prompt Engineering Your Tools

Tool definitions deserve as much prompt engineering attention as your overall prompts. Key suggestions: 

- **Give the model enough tokens to "think"** before it writes itself into a corner
- **Keep the format close to what the model has seen naturally** in internet text
- **Minimize formatting overhead** (e.g., don't require accurate line counts or excessive escaping)
- **Invest in Agent-Computer Interfaces (ACI)** as much as you would in Human-Computer Interfaces (HCI):
    - Put yourself in the model's shoes — is tool usage obvious from the description?
    - Include example usage, edge cases, input format requirements, and clear boundaries
    - Test extensively and iterate on tool definitions
    - **Poka-yoke your tools** — make it harder to make mistakes (e.g., require absolute filepaths instead of relative ones)

---

## Single-Agent System with Agent Skills — Architecture Overview

```mermaid
graph TD
    U["👤 User"] -.->|"Task"| AG["🤖 Single Agent"]

    subgraph "Agent Core"
        AG --> M["🧠 AI Model\n(Reasoning Engine)"]
        AG --> P["📝 Prompt\n(Role + Capabilities)"]
        AG --> TK["🧰 Toolkit\n(Integrations)"]
        AG --> SK["⭐ Skills\n(Domain Knowledge)"]
    end

    subgraph "Agent Loop"
        M -->|"1. Plan"| ACT["🎯 Execute\nAction"]
        ACT -->|"2. Observe"| OBS["👁️ Evaluate\nResults"]
        OBS -->|"3. Adjust"| M
    end

    OBS -.->|"Complete / Stop"| OUT["📤 Output"]
    OBS -.->|"Blocker / Review"| U

    style U fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
    style AG fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style M fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style P fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style TK fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
    style SK fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style ACT fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
    style OBS fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style OUT fill:#E8DAEF,stroke:#C39BD3,color:#6C3483
```


### Sequence Diagram of an example Single Agent System

```mermaid
sequenceDiagram
    participant User
    participant Agent as Research Agent
    participant Skills as Agent Skills
    participant Web as Web Search<br/>(via MCP)
    participant DB as SQL Database<br/>(via MCP)

    User->>Agent: "Research remote work productivity tools<br/>& correlate with internal metrics"

    rect rgb(213, 245, 227)
        Note over Agent,Skills: Initial Analysis & Skill Activation
        Agent->>Agent: Think: "Two distinct data sources needed.<br/>Decompose into parallel searches."
        Agent->>Skills: Activate Research Methodology
        Agent->>Skills: Activate Data Correlation
        Agent->>Skills: Activate Business Intelligence
        Skills-->>Agent: Frameworks & best practices loaded
    end

    rect rgb(250, 219, 216)
        Note over Agent,DB: Parallel Tool Execution (concurrent)
        par External Research
            Agent->>Web: Search productivity tool<br/>adoption trends
            Web-->>Agent: Tool adoption data &<br/>industry reports
        and Internal Data
            Agent->>DB: Query internal productivity<br/>metrics across teams
            DB-->>Agent: Productivity data by<br/>team & time period
        end
    end

    rect rgb(232, 218, 239)
        Note over Agent: Synthesis & Correlation
        Agent->>Agent: Cross-reference external trends<br/>with internal metrics
        Agent->>Agent: Apply correlation methodology<br/>from Skills
    end

    Agent-->>User: Comprehensive research report<br/>with correlations & insights

```

---

## Agent Skills - Composable Architecture 


```mermaid
graph TD
    A["🤖 Agent"] --> S1["📊 Financial\nAnalysis Skill"]
    A --> S2["📋 Research\nMethodology Skill"]
    A --> S3["🔗 Data\nCorrelation Skill"]
    A --> S4["💼 Business\nIntelligence Skill"]

    S1 --> S1a["Risk\nAssessment"]
    S1 --> S1b["Compliance\nChecks"]

    S1b -->|"invokes"| S5["📄 Document\nAnalysis Skill"]
    S5 -->|"invokes"| S6["🔍 Extraction\nSkill"]

    S3 -->|"feeds"| S2
    S2 -->|"feeds"| S4

    style A fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style S1 fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
    style S2 fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style S3 fill:#E8DAEF,stroke:#C39BD3,color:#6C3483
    style S4 fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
    style S1a fill:#FCF3CF,stroke:#F9E79F,color:#7D6608
    style S1b fill:#FCF3CF,stroke:#F9E79F,color:#7D6608
    style S5 fill:#D6EAF8,stroke:#AED6F1,color:#2471A3
    style S6 fill:#D6EAF8,stroke:#AED6F1,color:#2471A3
```

---
