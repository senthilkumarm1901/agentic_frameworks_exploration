# Why Hermes Has Lower LLM Call Spikes — Root Cause Analysis

Source: [Github Repo](https://github.com/senthilkumarm1901/agentic_frameworks_exploration)

> Covers Pattern 4 (agent_with_memory_and_chat) across LangGraph, Strands, and Hermes.  
> All data sourced from the `logs.txt` files in each framework's agent directory.

---

## Raw Data: LLM Calls Per Turn

The table below maps each successive question in the four-turn sequence
that drove the comparison in the final evaluation report.

| Turn | Question | Hermes `llm_calls` | LangGraph `llm_calls` | Strands `llm_calls` |
|------|----------|-------------------:|----------------------:|--------------------:|
| 1 | Build a comprehensive profile of India | **4** | 2 | 6 |
| 2 | Compare India and Japan | **4** | 4 | 17 |
| 3 | Same for Brazil | **4** | 8 | 25 |
| 4 | India vs. most populous European country | **8** ¹ | 12 | 33 |

¹ Hermes Turn 4 is 8 (not 4) because the model had to probe five European
country names before discovering that Russia / "Russian Federation" was the
most populous, adding extra tool-error recovery iterations.

**Growth factor across the four turns:**
- Hermes: 4 → 8 = **2×** (driven by task ambiguity, not context size)
- LangGraph: 2 → 12 = **6×**
- Strands: 6 → 33 = **5.5×**

---

## Prompt Token Growth (the context-window cost)

| Turn | Hermes `prompt_tokens` | LangGraph `prompt_tokens` | Strands `prompt_tokens` |
|------|----------------------:|-------------------------:|------------------------:|
| 1 | 5,930 | 2,188 | 9,326 |
| 2 (India vs Japan) | 10,110 | 6,618 | 42,887 |
| 3 (+ Brazil) | 15,405 | 18,765 | 79,958 |
| 4 (+ European) | 43,541 | 36,093 | 119,107 |

> The Strands row for Turn 2 (42,887 tokens) is roughly **6.5× Hermes and
> 4.5× LangGraph** for the exact same question about India and Japan. That
> single turn already costs more than all four Hermes turns combined.

---

## Root Cause: Three Different Short-Term Memory Architectures

### How each framework carries conversation state into the next turn

```
Hermes (manual OpenAI loop)
───────────────────────────
Session start:
  [System prompt with frozen long-term summary injected once]

Each turn, self.messages grows by:
  + user message
  + assistant (with tool_calls)
  + tool results (one per tool)
  + assistant (final answer)

The LLM is called exactly once per ReAct iteration.
Loop exits as soon as the model returns a message with no tool_calls.
A hard cap of max_iterations=10 prevents runaway loops.

LangGraph (MemorySaver + thread_id)
────────────────────────────────────
Session start:
  [System prompt with frozen long-term summary injected once]

Each turn, the full LangGraph thread state grows:
  + all prior AIMessages (every LLM response ever)
  + all prior ToolMessages (every tool result ever)
  + the new HumanMessage

create_react_agent manages the internal loop.
No hard cap on iterations.

Strands (ConversationManager, agent reused across turns)
─────────────────────────────────────────────────────────
Session start:
  [System prompt with frozen long-term summary injected once]

Each turn, ConversationManager sends to the model:
  + the full conversation including all prior messages
  + ALL prior tool results at full length
  + the new user query

The Agent object's internal cycle counter (total_cycles) is the
LLM call count for that invocation.
No hard cap on cycles.
```

All three frameworks inject the same frozen long-term summary once at session
start. The key difference is **what happens to the live conversation history
on every subsequent call to the LLM within a turn**.

---

## The Three Mechanisms That Keep Hermes Flat

### Mechanism 1 — Explicit `max_iterations` cap

In [hermes/agents/4_agent_with_memory_and_chat/src/agent.py](../../../hermes/agents/4_agent_with_memory_and_chat/src/agent.py):

```python
for _ in range(self.max_iterations):          # hard cap of 10
    response = self._client.chat.completions.create(
        model=self.model,
        messages=self.messages,
        tools=self._openai_tools,
    )
    llm_calls += 1
    ...
    if not msg.tool_calls:
        break                                  # exits as soon as no tools called
```

Each pass through the loop is exactly one LLM API call. The loop exits the
moment the model stops requesting tools. For a clean country comparison task
the natural exit comes at iteration 4:

| Iteration | What the model does |
|-----------|---------------------|
| 1 | Decides to `activate_skill`; emits a tool call |
| 2 | Reads skill instructions; emits a batch of `country_lookup_tool` + `calculator_tool` calls |
| 3 | Processes results; may call `country_kb_search_tool` |
| 4 | Synthesises the answer; no tool calls → loop exits |

This pattern holds regardless of how many prior turns are in `self.messages`.
The task complexity — not the conversation length — determines the exit
iteration.

### Mechanism 2 — Batched parallel tool calls (OpenAI tool-use protocol)

The OpenAI-compatible API lets the model request multiple tool calls in a
**single response**. Hermes collects all of them, dispatches them, and then
makes one more LLM call with all results appended. This is why Turn 3 logged
**12 tool calls but only 4 LLM calls**:

```
LLM call 1 → emits activate_skill
LLM call 2 → emits [country_lookup×6, calculator×4] in one response
LLM call 3 → emits [country_kb_search]
LLM call 4 → emits final answer (no tools)
```

LangGraph's `create_react_agent` and Strands' `Agent` both process tool calls
one reasoning cycle at a time. Every tool batch that requires a new plan costs
another LLM cycle.

### Mechanism 3 — Context growth does not change the reasoning pattern

Hermes accumulates `self.messages` across turns: every prior exchange (user,
assistant, tool results, final answer) is in the prompt. But because the
**structure of each turn is the same** — activate skill → lookup → calculate
→ answer — the number of ReAct iterations needed stays constant. The model
finds the same four-step path through the problem whether this is Turn 1 or
Turn 10.

The long-term memory summary (max 1,500 characters, hard-capped in
[hermes/agents/4_agent_with_memory_and_chat/src/memory.py](../../../hermes/agents/4_agent_with_memory_and_chat/src/memory.py))
prevents the prior-turn knowledge from bloating the system prompt.

---

## Why Strands Explodes (6 → 33 Cycles)

The Strands `ConversationManager` automatically appends every message —
including all tool results at full length — to the context window every time
`session.agent(query)` is called. Looking at the Turn 2 prompt token count
(42,887) versus Hermes (10,110) for the **identical India-vs-Japan question**:

```
Strands Turn 2 prompt = Turn 1 full conversation (India profile)
                      + all Turn 1 tool results (3 lookups, 2 calcs, 1 KB search)
                      + the new "compare India and Japan" user message

≈ 42,887 tokens total
```

The model, seeing all prior tool calls and results in its window, responds by
re-verifying data and running more intermediate reasoning cycles. This is a
"context poisoning" effect: the model treats prior tool results as
starting-points rather than already-resolved facts, so it re-explores them.
Each re-exploration costs an additional `total_cycle`.

The effect compounds quadratically — each new turn adds the prior turn's
already-large context on top of the accumulated history.

---

## Why LangGraph Grows Moderately (2 → 12)

LangGraph's `MemorySaver` checkpointer stores the full thread state and
restores it on every `agent.ainvoke()` call with the same `thread_id`. The
`result["messages"]` returned by LangGraph contains the **entire accumulated
thread** — all prior AIMessages and ToolMessages, not just the current turn.

The `llm_calls` counter in
[langgraph/agents/4_agent_with_memory_and_chat/src/agent.py](../../../langgraph/agents/4_agent_with_memory_and_chat/src/agent.py)
iterates over `result["messages"]` and counts every AIMessage found:

```python
for msg in messages:
    if msg_type == "ai":
        if content or tool_calls_attr:
            llm_calls += 1
```

Because `messages` is the full accumulated thread, each turn's count
**includes the AIMessages from all prior turns**. The 2→4→8→12 growth almost
exactly tracks the accumulation:

| Turn | Prior AIMessages (approx.) | Current-turn new AIMessages | Reported `llm_calls` |
|------|---------------------------|----------------------------|---------------------|
| 1 | 0 | 2 | 2 |
| 2 | 2 | 2 | 4 |
| 3 | 4 | 4 | 8 |
| 4 | 8 | 4 | 12 |

This means LangGraph's `llm_calls` metric is **not purely per-turn** — it
accumulates historical counts. The real per-turn LLM call count for LangGraph
is closer to 2–4 per turn (matching Hermes), not the 12 seen at Turn 4.

---

## Side-by-side Architectural Summary

| Dimension | Hermes | LangGraph | Strands |
|-----------|--------|-----------|---------|
| **Short-term memory mechanism** | Manual `self.messages` list | MemorySaver checkpointer | ConversationManager (auto) |
| **What grows per turn in the prompt** | Messages + tool results for every prior turn | Same as Hermes | Same as Hermes |
| **LLM call loop control** | `for _ in range(max_iterations)` — explicit hard cap | `create_react_agent` internal — no hard cap | Agent `total_cycles` — no hard cap |
| **Tool call batching** | Multiple tool calls per LLM response | Multiple tool calls per LLM response | Depends on model; single tool per cycle in practice |
| **What drives the LLM call count** | Task complexity (steps to answer) | Task complexity + growing context | Grows with context size (re-verification loops) |
| **`llm_calls` metric measures** | Calls within the current turn only | All AIMessages in the full thread (historical + current) | Cycles within the current invocation (genuinely per-turn) |

---

## Key Takeaway

The "4 → 3 LLM calls" story in the comparison table is really a story about
**where the ceiling is**:

- **Hermes** has a hard ceiling (`max_iterations=10`) and a natural exit
  condition (`break` when no tools called). A standard comparison task
  consistently hits the same 4-step reasoning path.

- **Strands** has no ceiling. The growing ConversationManager context causes
  the model to make more and more intermediate reasoning cycles per turn as the
  conversation lengthens.

- **LangGraph's reported growth is partly a measurement artefact** — its
  `llm_calls` counter accumulates historical AIMessages from the full thread,
  not just the current turn.

Hermes's flat profile is therefore the result of **deliberate loop design**
(explicit `max_iterations` + early exit + batched tools), not a memory
compression trick. All three frameworks store the same full conversation
history. Only Hermes guarantees that history can't change *how many times the
model reasons per new question*.
