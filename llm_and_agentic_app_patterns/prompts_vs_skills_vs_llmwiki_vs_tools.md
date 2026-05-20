# Prompts vs Skills


```mermaid
flowchart TD
    subgraph "The Knowledge Placement Spectrum"
        direction LR
        PROMPT["📝 PROMPT\n\nWhat the agent always knows\n\nSmall, always loaded\n\n• Role identity\n• Behavioral rules\n• Capability awareness\n• Tone & guardrails"]

        SKILL["⭐ SKILL\n\nLoaded when the agent wants to know how to do\n\nMedium, loaded on-demand\n\n• Domain methodology\n• Tool orchestration\n• Decision frameworks\n• Version-controlled"]

        WIKI["📚 LLM WIKI\n\nWhen the agent needs to give personalized answers\n\nMedium-large, pre-compiled\n\n• Cross-referenced knowledge\n• Synthesized from sources\n• Incrementally maintained\n• Agent-written, human-curated"]

        RAG["🔍 RAG / KB SEARCH\n\nWhen the agents wants to know from scratch\n\nLarge, retrieved at query time\n\n• Unstructured corpus\n• Similarity-based retrieval\n• Re-derived every time\n• No accumulation"]
    end

    PROMPT -->|"always in\ncontext"| SKILL
    SKILL -->|"loaded when\nclassified"| WIKI
    WIKI -->|"read when\nneeded"| RAG

    style PROMPT fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style SKILL fill:#FCF3CF,stroke:#F9E79F,color:#7D6608
    style WIKI fill:#D6EAF8,stroke:#AED6F1,color:#2471A3
    style RAG fill:#FADBD8,stroke:#E6A9A4,color:#C0392B

```


| Dimension           | Prompt                 | Skill                                            | LLM Wiki                              | RAG                           |
| ------------------- | ---------------------- | ------------------------------------------------ | ------------------------------------- | ----------------------------- |
| **Size**            | ~200–500 tokens        | ~1K–5K tokens per skill                          | ~10K–100K tokens (whole wiki)         | Unbounded corpus              |
| **When loaded**     | Always                 | On classification match                          | Agent reads relevant pages            | At query time (similarity)    |
| **Who writes it**   | Human (you)            | Human (you)                                      | **Agent writes it**, human curates    | Raw source docs               |
| **Structure**       | Free-form instructions | Structured: context + instructions + constraints | Interlinked markdown pages with index | Chunks in vector DB           |
| **Versioned?**      | Implicitly (in code)   | ✅ Semver per skill                               | ✅ Git-tracked `.md` files             | ❌ Embeddings drift silently   |
| **Accumulates?**    | No                     | No (static until updated)                        | **Yes — compounds over time**         | No (re-derives every query)   |
| **What it answers** | _"Who are you?"_       | _"How do you handle THIS task?"_                 | _"What do you know about X?"_         | _"Find me something about X"_ |


---

# Prompts vs Skills vs Tools 

```mermaid
flowchart TD
    subgraph "The Knowledge Placement Spectrum"
        direction LR
        PROMPT["📝 PROMPT\n\nWhat the agent always knows\n\nSmall, always loaded\n\n• Role identity\n• Behavioral rules\n• Capability awareness\n• Tone & guardrails"]

        SKILL["⭐ SKILL\n\nLoaded when the agent wants to know how to do\n\nMedium, loaded on-demand\n\n• Domain methodology\n• Tool orchestration\n• Decision frameworks\n• Version-controlled"]

        %% WIKI["📚 LLM WIKI\n\nMedium-large, pre-compiled\n\n• Cross-referenced knowledge\n• Synthesized from sources\n• Incrementally maintained\n• Agent-written, human-curated"]

        RAG["🔍 RAG / KB SEARCH\n\nWhen the agents wants to know from scratch\n\nLarge, retrieved at query time\n\n• Unstructured corpus\n• Similarity-based retrieval\n• Re-derived every time\n• No accumulation"]
    end

    PROMPT --> SKILL
    %% SKILL --> WIKI
    %% WIKI --> RAG
    SKILL --> RAG

    style PROMPT fill:#D5F5E3,stroke:#A9DFBF,color:#27AE60
    style SKILL fill:#FCF3CF,stroke:#F9E79F,color:#7D6608
    %% style WIKI fill:#D6EAF8,stroke:#AED6F1,color:#2471A3
    style RAG fill:#FADBD8,stroke:#E6A9A4,color:#C0392B
```


| Dimension           | Prompt                 | Skill                                            | RAG                           |
| ------------------- | ---------------------- | ------------------------------------------------ | ----------------------------- |
| **Size**            | ~200–500 tokens        | ~1K–5K tokens per skill                          | Unbounded corpus              |
| **When loaded**     | Always                 | On classification match                          | At query time (similarity)    |
| **Who writes it**   | Human (you)            | Human (you)                                      | Raw source docs               |
| **Structure**       | Free-form instructions | Structured: context + instructions + constraints | Chunks in vector DB           |
| **Versioned?**      | Implicitly (in code)   | ✅ Semver per skill                               | ❌ Embeddings drift silently   |
| **Accumulates?**    | No                     | No (static until updated)                        | No (re-derives every query)   |
| **What it answers** | _"Who are you?"_       | _"How do you handle THIS task?"_                 | _"Find me something about X"_ |

