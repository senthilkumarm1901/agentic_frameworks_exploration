# Technical Evaluations

Deep-dive Q&A on implementation-level behaviour observed during the experiments.
Each question is anchored to exact code in the repository.

---

## Q1 — ReAct Loop as a Graph (LangGraph) vs. Model-Driven Runtime (Strands/Hermes)

> **Question:**
> Is the ReAct loop in LangGraph converted into a graphical structure? But not in Strands?
>
> References:
> - `langgraph/agents/1_agent_with_multiple_mcp_tools/README.md`
> - `strands/agents/1_agent_with_multiple_mcp_tools/README.md`
>
> How are LangGraph results more stable while model-driven autonomy in Strands/Hermes makes them
> return raw tool outputs instead of actual answers?
> Find the aspect of code that explains this.

---

### Part 1 — Is the ReAct loop a compiled graph in LangGraph, but not in Strands?

**Yes, explicitly so.** The two frameworks make fundamentally different choices about who owns the loop.

#### LangGraph — loop compiled into a state graph

`create_react_agent` (from `langgraph.prebuilt`) does not just call the LLM in a loop.
It **compiles a `StateGraph`** whose edges encode the ReAct logic:

```
START
  │
  ▼
┌──────────┐   has tool_calls?   ┌────────────┐
│  agent   │ ──── YES ─────────► │   tools    │
│  (LLM)   │                     │  (execute) │
└──────────┘ ◄───────────────────└────────────┘
  │
  │  no tool_calls?
  ▼
 END
```

The `agent_node → tools_node → agent_node` cycle is an explicit conditional edge
inside the compiled graph. The framework — not the model — decides when the loop continues.

```python
# langgraph/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 67-74)

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)

result = await agent.ainvoke({"messages": [("user", user_query)]})
```

`create_react_agent` internally produces a compiled graph equivalent to:

```python
# What create_react_agent does internally (LangGraph internals, simplified)
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,          # ← framework-owned routing function
    {"tools": "tools", END: END},
)
workflow.add_edge("tools", "agent")
graph = workflow.compile()
```

The routing function `should_continue` is deterministic Python code.
It checks whether the last AI message contains `tool_calls`. The model has no say in
whether the loop continues — the graph edge decides.

---

#### Strands — model-driven runtime (no explicit graph)

Strands uses a plain `Agent` object. The framework calls the LLM, executes whatever
tools the model requested, then calls the LLM again — and continues until the
model stops requesting tools. **There is no compiled graph; the model's own output
controls termination.**

```python
# strands/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 140-149)

agent = Agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    callback_handler=None,
)

result = agent(user_query)   # ← single call; Strands' runtime drives the loop internally
```

There are no explicit nodes, edges, or conditional routing. Strands' internal
`ConversationManager` replays the conversation on each cycle and trusts the model
to issue no more tool calls when it is done.

---

#### Hermes — explicit Python loop, not a graph

Hermes makes the loop visible in Python, but it is still a `for` loop with a `break`,
not a compiled graph:

```python
# hermes/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 147-179)

for _ in range(self.max_iterations):           # ← hard iteration cap of 10
    response = self._client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=openai_tools,
    )
    llm_calls += 1

    msg = response.choices[0].message
    final_response = msg.content or ""         # ← whatever the model wrote is the answer

    if not msg.tool_calls:
        break                                  # ← model-driven exit: model stops → loop stops

    # execute tools and append results to messages...
```

The break condition is identical to Strands in spirit: the model decides to stop
requesting tools, and the loop exits. The difference is that the loop is in plain sight
in your code rather than hidden inside a framework runtime.

---

### Comparison: who owns the loop exit?

| Framework  | Loop mechanism | Exit condition owned by |
|------------|---------------|------------------------|
| **LangGraph** | Compiled `StateGraph` conditional edge | **Framework** (`should_continue` function) |
| **Strands**   | Framework-internal runtime | **Model** (stops emitting tool calls) |
| **Hermes**    | Explicit `for` loop + `break` | **Model** (stops emitting tool calls) |

Both Strands and Hermes are *model-driven*: if the model issues a last tool call
without a follow-up synthesis response, the loop ends and whatever `msg.content` or
`result` contained at that point becomes the answer.
LangGraph's graph structure does not change this exit condition — the graph edge still
fires when `tool_calls` is empty — but the answer extraction and fallback path
(Part 2 below) is where the stability gap actually appears.

---

### Part 2 — Why LangGraph gives cleaner answers while Strands/Hermes can return raw tool output

All three frameworks share the **identical system prompt** (SYSTEM_PROMPT is copied
verbatim across all three `src/prompts.py` files), so the instruction "After getting
tool results, provide a clear natural language answer" is equally available to every
model invocation.

The stability difference is entirely in **what happens after the loop exits**.

---

#### LangGraph — two-stage answer extraction with an active fallback LLM synthesis

```python
# langgraph/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 128-160)

# Stage 1: prefer the last non-empty AI content in the message list
answer = ai_contents[-1] if ai_contents else ""

# Stage 2: if the model left content empty, fire an extra LLM call to synthesise
if not answer.strip() and tool_calls_detail:
    tool_summary_lines = [
        f"- {tc['name']}({args_str}) -> {tc['result']}"
        for tc in tool_calls_detail
    ]
    fallback_prompt = (
        "You are a country data analyst assistant. "
        "Using ONLY the tool outputs below, provide a concise final answer to the user's question. "
        "Include key numbers and the final computed comparison/ratio where relevant.\n\n"
        f"User question: {user_query}\n\n"
        "Tool outputs:\n" + "\n".join(tool_summary_lines)
    )
    fallback_resp = await llm.ainvoke(fallback_prompt)   # ← extra LLM call guaranteed
    answer = fallback_resp.content.strip()
```

The fallback is a **dedicated synthesis call** with a tightly scoped prompt: no tools
available, only tool outputs as context, and an explicit instruction to produce a
natural-language answer. This is why LangGraph virtually always returns a polished sentence
even when the model forgets to synthesise at the end of the ReAct loop.

---

#### Strands — `str(result)` first, then raw tool-output string as last resort

```python
# strands/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 73-83, 170-174)

def _extract_answer(result: Any) -> str:
    answer = str(result).strip()        # ← cast the entire result object to string
    if answer:
        return answer
    # ... secondary attempt via result.message["content"]
    return ""

# in run_agent():
answer = _extract_answer(result)
if not answer.strip() and tool_calls_detail:
    answer = "; ".join(                 # ← raw tool evidence concatenated as a string
        f"{tc['name']}(...) -> {tc.get('result', '')}"
        for tc in tool_calls_detail
    )
```

`str(result)` on a Strands `AgentResult` object typically serialises the model's final
message, which can be a tool-use block or an intermediate reasoning token rather than a
synthesised prose answer. The fallback is not another LLM call — it is a Python string
join of `name -> raw_result` pairs. When the model terminates after a tool call without
writing a clean sentence, this fallback fires and the logged `answer` looks like:

```
country_lookup_tool(country=United States, metric=gdp_trillion) -> The gdp trillion of ...;
calculator_tool(expression=21.43/336.8*1000000) -> Result: 63633.01
```

---

#### Hermes — `msg.content or ""`, no synthesis fallback

```python
# hermes/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 161, 179-180)

final_response = msg.content or ""   # ← whatever the model wrote in this iteration

if not msg.tool_calls:
    break                             # ← exit immediately; no synthesis step
```

`final_response` is whatever the model wrote in the last iteration where it chose not
to call a tool. If the model writes a clean prose sentence, that becomes the answer.
If the model writes an empty string (common with smaller models using `<think>` tokens),
`final_response` stays `""` and there is no recovery path — no additional LLM call,
no tool-evidence fallback.

The Hermes `run_conversation` return value is:

```python
return {
    "final_response": final_response,   # ← could be ""
    ...
}
```

`main.py` then renames this to `answer`, so an empty answer is possible and has been
observed in the experiment logs.

---

### Root-cause summary

| | LangGraph | Strands | Hermes |
|---|---|---|---|
| **Loop control** | Graph edge (framework-owned) | Model-driven (framework runtime) | Model-driven (explicit `for`/`break`) |
| **Answer source** | Last non-empty `AIMessage.content` | `str(AgentResult)` | `msg.content or ""` at loop exit |
| **Empty-answer fallback** | ✅ Extra LLM synthesis call with clean prompt | ⚠️ Raw tool-output string join (`; `-separated) | ❌ Empty string returned |
| **Why it matters** | Forces a natural-language answer even if the model skips synthesis | Answer can be machine-readable evidence, not prose | Answer can be empty; no recovery |

**The single most impactful line** is in LangGraph's fallback:

```python
fallback_resp = await llm.ainvoke(fallback_prompt)
```

This extra LLM call — with a stripped-down prompt that contains only tool outputs and
an explicit "give me a sentence" instruction — is what converts tool evidence into a
human-readable answer when the primary ReAct loop fails to synthesise one.
Neither Strands nor Hermes has an equivalent step.

---

## Q2 — Do Local Models Work Better With a Structured Graph Framework Like LangGraph?

> **Question:**
> Do local models work well with a graph structure like LangGraph more than others — because
> more structured and modular orchestration is easier for local models?
> Find concrete evidence outside the repo.

---

### The hypothesis

Local/smaller models have less reasoning bandwidth than frontier models. If a framework
offloads orchestration decisions to deterministic code (graph edges, routing functions) instead
of leaving them to the model, the model only has to fill in structured JSON for the *current
step* — not plan the whole sequence. The hypothesis is that this reduced per-step burden
is what makes the difference.

The evidence — from this repo's own logs and from the broader community — strongly supports it.

---

### Evidence from this repository

The 4 Pattern 1 experiments are the clearest single datapoint. All three agents used the
**same model** (`qwen3.5:35b-a3b-coding-nvfp4`) and the **same system prompt**.

**Strands — Experiment 2 answer field** (`strands/agents/1_agent_with_multiple_mcp_tools/logs.txt`):

```
"answer": "country_lookup_tool(country=United States, metric=gdp_trillion) ->
The gdp trillion of United States is 27.29 trillion USD;
country_lookup_tool(country=United States, metric=population_million) ->
The population million of United States is 336.8 million people;
...
calculator_tool(expression=81027.3159 / 33815.261) -> Result: 2.3962"
```

The model ran all 7 tool calls successfully and had the correct numbers in its context.
It then produced no synthesis sentence. With no fallback LLM call (see Q1), Strands'
`_extract_answer` fell through to the raw `"; ".join(...)` path:

```python
# strands/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 171-174)

if not answer.strip() and tool_calls_detail:
    answer = "; ".join(                          # ← tool evidence, not prose
        f"{tc['name']}(...) -> {tc.get('result', '')}"
        for tc in tool_calls_detail
    )
```

**Hermes — Experiment 3 answer field** (`hermes/agents/1_agent_with_multiple_mcp_tools/logs.txt`):

```json
{
    "answer": "",
    "llm_calls": 3,
    "tool_calls": 3,
    "total_tokens": 3177
}
```

The model called `country_lookup_tool` twice and `calculator_tool` once, got back `0.0547`,
and then produced `msg.content = ""` — it forgot to write a sentence. Since Hermes assigns
`final_response = msg.content or ""` with no recovery:

```python
# hermes/agents/1_agent_with_multiple_mcp_tools/src/agent.py  (lines 161, 179)

final_response = msg.content or ""   # ← empty string if model didn't synthesise

if not msg.tool_calls:
    break                             # ← exits immediately with empty final_response
```

**Across 4 experiments per framework, with identical model and prompt:**

| Framework  | Clean prose answers | Raw tool output | Empty answer |
|------------|:-------------------:|:---------------:|:------------:|
| LangGraph  | **4 / 4 (100%)**   | 0               | 0            |
| Hermes     | 3 / 4 (75%)         | 0               | **1 / 4**    |
| Strands    | 2 / 4 (50%)         | **2 / 4**       | 0            |

LangGraph's 100% clean rate is not a model capability difference — it is the fallback
synthesis call (see Q1) that fires whenever the primary ReAct loop fails to produce prose.
The model's ability to synthesise is equally unreliable across all three; only LangGraph
adds a safety net.

---

### External evidence

#### 1. Docker — practical evaluation of local LLMs for tool calling (June 2025)

Docker ran a systematic study of local LLMs as tool-calling agents and documented the
failure modes for unstructured loops [[docker.com]](https://www.docker.com/blog/local-llm-tool-calling-a-practical-evaluation/):

> *"OpenAI's GPT-4 or GPT-3.5 worked as expected... But the local models? That's where
> the challenges started to surface."*

Their documented failure patterns map directly to what was observed here:

| Docker failure mode | Observed in this repo |
|---|---|
| Eager invocation (calls tools for greetings) | — |
| Wrong tool selection | Hermes Pattern 3 (missed `report-formatting` skill) |
| **Ignored tool responses** (no synthesis sentence) | Strands raw tool output, Hermes empty answer |

The "ignored responses" failure — calling all the right tools but not writing the final
sentence — is exactly the failure Strands and Hermes exhibited in 25–50% of Pattern 1 runs.

---

#### 2. NVIDIA research — "Small Language Models are the Future of Agentic AI"

NVIDIA's position paper distinguishes two modes of agentic orchestration
[[research.nvidia.com]](https://research.nvidia.com/labs/lpr/slm-agents/index.html):

> *"Language model agency: the LLM drives all orchestration decisions."*  
> *"Code agency: a dedicated **controller code orchestrates all interactions** while the LLM
> fills in structured slots."*

They argue SLMs are only viable agents in the **code-agency** mode. In language-model-agency
mode, SLMs lack the reasoning bandwidth to both plan the sequence *and* synthesise the final
answer correctly.

This maps directly to the framework split in this repository:

| NVIDIA's taxonomy | This repo equivalent |
|---|---|
| **Code agency** (controller drives loop) | **LangGraph** — `should_continue` conditional edge, fallback synthesis call |
| **Language model agency** (LLM drives loop) | **Strands**, **Hermes** — model decides when to stop and what to write |

---

#### 3. LangGraph community (Reddit r/LangChain) — controllability is the cited reason

LangGraph users consistently cite per-node control over what information the model
receives as the reason it works reliably with smaller models
[[reddit.com]](https://www.reddit.com/r/LangChain/comments/1ashzgp/whats_your_take_on_langgraph/):

> *"The big selling point for LangGraph is **controllability**... I don't think any other
> agent frameworks give you the same level of controllability."* — Harrison Chase, LangChain founder
> [[reddit.com]](https://www.reddit.com/r/LangChain/comments/1db6evc/best_production_agent_framework_langraph_vs/)

> *"I like the idea to have control over each step and being able to select which information
> is passed to each node and how the response of the nodes are added to the state — it gives
> a lot of control of the token usage and to guide the node responses."*

---

#### 4. ReAct text parsing vs. structured tool calling — an architectural explanation

A widely cited DEV Community post explains why free-form ReAct loops are fragile for smaller
models [[dev.to]](https://dev.to/parth_sarthisharma_105e7/react-vs-tool-calling-why-your-llm-should-decide-but-never-execute-cp3):

> *"ReAct: The LLM outputs formatted text (Thought/Action/Action Input/Observation) and a
> parser extracts the tool calls. **Problems: Text parsing is brittle, hard to validate, easy
> to hallucinate actions, difficult to scale reliably.**"*
>
> *"Tool Calling: The model returns structured JSON for tool calls, not free-form text.
> **This is not a limitation. This is a feature.**"*

LangGraph's `create_react_agent` enforces structured tool calling — the model returns JSON,
the graph edge routes it to the tools node. There is no free-form text for the framework to
misparse. Hermes also uses structured JSON tool calling (OpenAI protocol), but without the
graph's final-answer safety net. Strands uses the same structured calls internally, but also
without an equivalent fallback.

The failure point in both Strands and Hermes is not in tool *calling* (both did that
correctly), but in the final *synthesis* turn — where the model is given no structure at all
and must produce a free-form sentence. That is the weakest point for a local model.

---

#### 5. DigitalOcean — LangGraph + Ollama as a documented production pattern

> *"LangGraph enables structured, multi-step agent workflows by modeling agent behavior as a
> graph, making complex decision paths easier to manage and debug."*
>
> *"By combining LangGraph for orchestrating agent logic with Ollama for hosting the LLM,
> developers can create fully local AI agents that perform tasks autonomously without requiring
> internet access or external cloud services."*
> [[digitalocean.com]](https://www.digitalocean.com/community/tutorials/local-ai-agents-with-langgraph-and-ollama)

The LangGraph + Ollama pairing is now a documented production pattern specifically because
the graph structure compensates for local model weaknesses.

---

### The underlying principle

The more decisions the framework makes for the model, the less the model can get wrong:

| Framework pattern | Decisions left to LLM | Local model performance |
|---|---|---|
| Free-form ReAct text loop | Reasoning format, tool selection, argument format, synthesis | ❌ Hallucinations, empty answers, wrong paths |
| Structured tool calls, model-driven loop | Tool selection and arguments only; synthesis is still free-form | ⚠️ Tool calls work; synthesis can fail (Strands/Hermes in P1) |
| Structured tool calls + graph-enforced synthesis fallback | Tool selection and arguments only; synthesis rescued by framework | ✅ LangGraph 100% clean answers in P1 |

The final row is what LangGraph's `fallback_resp = await llm.ainvoke(fallback_prompt)` provides —
the framework takes back control of synthesis when the model fails to do it, feeding the model
a tightly scoped prompt with no tools and an explicit "write one sentence" constraint.

---

### Caveat: the effect diminishes with frontier models

This benefit is model-size-dependent. With GPT-4o, Claude Sonnet, or similar frontier models,
all three frameworks would likely achieve 100% clean answers on Pattern 1 — because frontier
models reliably synthesise a final sentence after seeing tool results.

> **The smaller or more local the model, the more structure helps.**  
> **The larger or more capable the model, the more freedom is tolerable.**

The experiments in this repository used `qwen3.5:35b-a3b-coding-nvfp4` — a strong but
local model. The 50% Strands failure rate is a property of *this model + this framework
combination*, not of Strands itself. On a frontier model, Strands would likely produce the
same prose quality as LangGraph on every turn.

---

*Q3 to follow.*
