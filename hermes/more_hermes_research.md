
Let me dig deeper into the Hermes Python library docs and architecture to pull out the pattern-specific syntax.Here's a comprehensive Hermes Agent cheat sheet, mapped to the **4 agentic patterns** you're evaluating for your Techceleration talk. 🎯

***

## 🔧 Hermes Agent — Agentic AI Patterns Cheat Sheet

### 📦 Installation & Setup

```bash
# Install via pip or uv
pip install git+https://github.com/NousResearch/hermes-agent.git
# or
uv pip install git+https://github.com/NousResearch/hermes-agent.git
```

```bash
# Required env vars (at minimum one)
export OPENROUTER_API_KEY="..."
# or
export OPENAI_API_KEY="..."
# or
export ANTHROPIC_API_KEY="..."
```

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### Pattern 1: Simple Tool-Calling Agent

The most basic agentic pattern — LLM decides which tool to call, executes it, observes, and responds. `chat()` handles the full ReAct loop internally (tool calls, retries, everything). [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

```python
from run_agent import AIAgent

agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,           # suppress CLI spinners
)

# One-shot: pass a message, get final text back
response = agent.chat("Search for recent Python 3.13 features")
print(response)
```

**With tool restrictions** (lock down which tools the agent can use):

```python
# Only web tools (browsing, search) — no terminal, no files
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    enabled_toolsets=["web"],
    quiet_mode=True,
)

# Everything EXCEPT terminal access
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    disabled_toolsets=["terminal"],
    quiet_mode=True,
)
```

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### Pattern 2: Full Conversation Control (ReAct with Observability)

When you need the **full execution trace** — messages, tool calls, metadata — use `run_conversation()`. This is the core ReAct loop exposed: **Thought → Action → Observation → Repeat** (up to 90 iterations by default). [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/), [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

result = agent.run_conversation(
    user_message="Search for recent Python 3.13 features",
    task_id="my-task-1",       # VM isolation per task
)

# Access results
print(result["final_response"])            # final text
print(f"Messages: {len(result['messages'])}")  # full trace
```

**With custom system prompt** (specialized agent persona):

```python
result = agent.run_conversation(
    user_message="Explain quicksort",
    system_message="You are a CS tutor. Use simple analogies.",
)
```

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### Pattern 3: Multi-Turn Memory-Enabled Chat Agent

Maintain **conversation state across turns** by passing message history back. This is how you build persistent, context-aware agents. [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

```python
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

# Turn 1
result1 = agent.run_conversation("My name is Alice")
history = result1["messages"]

# Turn 2 — agent remembers context
result2 = agent.run_conversation(
    "What's my name?",
    conversation_history=history,   # pass prior state
)
print(result2["final_response"])  # → "Your name is Alice."
```

**With persistent memory** (Hermes remembers across sessions via SQLite + FTS5):

```python
# Memory ON (default) — reads/writes ~/.hermes/ memory store
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
    # skip_memory=False  ← default, persistent memory active
)

# Memory OFF — stateless, ideal for API endpoints
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
    skip_memory=True,  # no persistent memory read/write
)
```

> ⚡ **Key Hermes differentiator**: 3-layer memory architecture — Honcho user modeling (dialectic Q\&A), Session search (SQLite + FTS5), Procedural memory (`MEMORY.md` + `SOUL.md`) [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### Pattern 4: Skill-Based Agent (Self-Improving)

Hermes's **killer feature** — the agent creates reusable `.md` skill files from experience, then reuses & improves them. Skills use the `agentskills.io` open standard. [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai), [\[fluxwise.tech\]](https://fluxwise.tech/en/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

```python
# Agent with skill creation enabled (default behavior)
agent = AIAgent(
    model="anthropic/claude-sonnet-4.6",
    quiet_mode=True,
)

# After solving a complex multi-step task, Hermes auto-creates
# a skill file in ~/.hermes/skills/ — e.g.:
# ~/.hermes/skills/pr_review_workflow.md

# Next time a similar task appears → skill is auto-loaded
response = agent.chat("Review this PR for security issues")
# ↑ Hermes searches skills, finds pr_review_workflow.md, uses it
```

**Skill file anatomy** (YAML frontmatter + Markdown):

```markdown
---
name: pr_review_workflow
description: Review pull requests for bugs and security issues
triggers:
  - "review PR"
  - "code review"
  - "security review"
---

## Steps
1. Get the diff using `git diff main...HEAD`
2. Check for hardcoded secrets or credentials
3. Verify input validation on all endpoints
4. Flag any SQL injection or XSS vectors
5. Summarize findings with severity ratings
```

> 📁 Skills are stored in `~/.hermes/skills/` and follow progressive disclosure: metadata → full instructions → associated references. [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

***

### Pattern 5: Parallel Sub-Agents (Batch Processing)

Spawn **isolated agents per task** for parallel workstreams. Each gets its own conversation and tool session. [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

```python
import concurrent.futures
from run_agent import AIAgent

prompts = [
    "Explain recursion",
    "What is a hash table?",
    "How does garbage collection work?",
]

def process_prompt(prompt):
    # ⚠️ MUST create fresh agent per thread (not thread-safe)
    agent = AIAgent(
        model="anthropic/claude-sonnet-4",
        quiet_mode=True,
        skip_memory=True,
    )
    return agent.chat(prompt)

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_prompt, prompts))

for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

Or use the built-in batch runner:

```bash
python batch_runner.py --input prompts.jsonl --output results.jsonl
```

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### Pattern 6: Specialized Agent Personas

Use `ephemeral_system_prompt` for domain-locked agents — not saved to trajectory files (clean training data). [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

```python
# SQL Expert Agent
sql_agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a SQL expert. Only answer database questions.",
    quiet_mode=True,
)
response = sql_agent.chat("How do I write a JOIN query?")

# Code Reviewer Agent
reviewer = AIAgent(
    model="anthropic/claude-sonnet-4",
    ephemeral_system_prompt="You are a senior code reviewer. Focus on bugs, security, style.",
    disabled_toolsets=["terminal", "browser"],
    quiet_mode=True,
)
```

***

### 📊 Quick Reference: Key Constructor Parameters

| Parameter                 | Type        | Default | Use Case                             |
| ------------------------- | ----------- | ------- | ------------------------------------ |
| `model`                   | `str`       | `""`    | Model in OpenRouter format           |
| `quiet_mode`              | `bool`      | `False` | **Always `True`** when embedding     |
| `enabled_toolsets`        | `List[str]` | `None`  | Whitelist tools                      |
| `disabled_toolsets`       | `List[str]` | `None`  | Blacklist tools                      |
| `skip_memory`             | `bool`      | `False` | Stateless API endpoints              |
| `skip_context_files`      | `bool`      | `False` | Skip `AGENTS.md` loading             |
| `save_trajectories`       | `bool`      | `False` | Save to JSONL (training data)        |
| `ephemeral_system_prompt` | `str`       | `None`  | Custom persona (not in trajectories) |
| `max_iterations`          | `int`       | `90`    | Cap tool-calling loops               |
| `platform`                | `str`       | `None`  | `"discord"`, `"telegram"`, etc.      |

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/)

***

### 🏗️ Architecture at a Glance

```
Entry Points (CLI / Gateway / ACP / Python Library)
        │
        ▼
    AIAgent (run_agent.py) ← Core ReAct Loop (90 iter max)
    ├── Prompt Builder
    ├── Provider Resolution (OpenRouter / Direct / Local)
    ├── Tool Dispatch (70+ tools, 28 toolsets)
    ├── Context Compression (iterative LLM summarization)
    └── Smart Model Routing (auto-failover on rate limits)
        │
        ▼
    Persistence Layer
    ├── Session Storage (SQLite + FTS5)
    ├── Skills System (74 built-in + auto-created)
    └── Memory (Honcho + MEMORY.md + SOUL.md)
```

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/), [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

***

### ⚠️ Key Gotchas

* 🔒 **Thread safety**: One `AIAgent` per thread/task. Never share instances.
* 🧠 **No vector embeddings**: Memory uses FTS5 (keyword-based), not semantic search.
* 📦 **Single-process**: No distributed agent pool — one instance per VPS.
* 💰 **Cost control**: Lower `max_iterations` for simple Q\&A (e.g., `max_iterations=10`).

 [\[hermes-age...search.com\]](https://hermes-agent.nousresearch.com/docs/guides/python-library/), [\[fluxwise.tech\]](https://fluxwise.tech/resources/articles/2026-04-01-hermes-agent-self-improving-ai)

***

This maps directly to your **4 Patterns × 3 Frameworks** talk structure. The key Hermes differentiators vs LangGraph and Strands are the **closed-loop skill creation** (Pattern 4) and **3-layer persistent memory** (Pattern 3) — those are unique to Hermes. [\[Techcelera...26 Edition \| Teams\]](https://teams.microsoft.com/l/message/19:3e1d3a8d9e394fafb3ca6e6d554ea99c@thread.v2/1780031619866?context=%7B%22contextType%22:%22chat%22%7D)

Want me to generate the equivalent cheat sheets for LangGraph and Strands side-by-side, or create a comparison table across all three?
