## 📊 Pattern 2: Agent with RAG MCP Tool — Evaluation Report

---

#### Experiment Setup

| Parameter              | Value                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **Pattern**            | `2_agent_with_rag_mcp_tool`                                                              |
| **Task**               | Country Analysis with **RAG** (vector-search knowledge base)                             |
| **Model**              | `qwen3.5:35b-a3b-coding-nvfp4` (local Ollama — identical across all 3)                   |
| **RAG Stack**          | MilvusLite + `sentence-transformers/all-MiniLM-L6-v2` + FAISS                            |
| **MCP Tools**          | `country_kb_search_tool` (RAG) — also `country_lookup_tool`, `calculator_tool` available |
| **Common Experiments** | 2 questions × 3 frameworks = **6 comparable runs**                                       |
| **All statuses**       | `SUCCESS`                                                                                |
| **All answers**        | ✅ Well-formatted natural language (6/6 = **100%**)                                       |

###### Common Questions

|##|Question|Type|Complexity|
|---|---|---|---|
|Q1|What are the main geographic features of Australia?|RAG retrieval|Medium (KB search → synthesize)|
|Q2|Describe the political system of Germany.|RAG retrieval|Medium (KB search → synthesize)|

> Both questions are **RAG-only** — no `calculator_tool` involved. This means the Strands raw-dump bug and Hermes empty-answer bug from Pattern 1 **do not apply**. 

---

#### 1. Static Metrics (Framework Footprint)

|Metric|LangGraph|Strands|Hermes|🏆 Winner|
|---|---|---|---|---|
|Packaging Size (MB)|984.79|996.81|**967.18**|Hermes|
|Lines of Code|373|**368**|405|Strands|
|Dependency Count|318|304|**267**|Hermes|

> All three frameworks are **~1 GB** due to the shared RAG stack (`sentence-transformers`, `torch`, FAISS, MilvusLite). Hermes has **16% fewer dependencies** (267 vs 318).

###### 📈 Pattern 1 → Pattern 2: Packaging Size Explosion

|Framework|Pattern 1 (MB)|Pattern 2 (MB)|Growth|Root Cause|
|---|:-:|:-:|:-:|---|
|LangGraph|76.94|984.79|**12.8×**|+sentence-transformers, +torch, +FAISS, +MilvusLite|
|Strands|72.80|996.81|**13.7×**|Same RAG stack added|
|Hermes|49.34|967.18|**19.6×**|Same RAG stack; largest relative jump from smallest base|

> Adding RAG inflated all three by **~900+ MB**. The RAG stack dominates — framework-specific size differences are noise at this scale. 

---

#### 2. Per-Experiment Results

###### Q1: _"What are the main geographic features of Australia?"_

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|**34,298**|40,060|44,737|LangGraph|
|LLM Calls|2|**3**|2|LG / Hermes|
|Tool Calls|1|**2**|1|LG / Hermes|
|Prompt Tokens|~2,339 †|4,113|**2,561**|LangGraph †|
|Completion Tokens|~333 †|559|**329**|Hermes|
|Total Tokens|~2,672 †|4,672|**2,890**|LangGraph †|
|Cold Start (ms)|~10,996 †|**5,008**|6,697|Strands|
|Peak Memory (MB)|~133.64 †|**44.06**|54.17|Strands|
|Answer Quality|✅ 5 features, bold|✅ `####` headers + sub-bullets|✅ 5 features, bold|All excellent|

> † LangGraph token/memory values from a prior run of the same question (no JSON block in this run's log).
> 
> **Strands made an extra KB search** (`"Great Barrier Reef deserts mountain ranges rivers"` as a follow-up query) — 2 tool calls and 3 LLM cycles vs 1 tool + 2 LLM for the others. This produced a **more thorough answer** but consumed **1.7× more tokens** (4,672 vs ~2,700). 

---

###### Q2: _"Describe the political system of Germany."_

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|29,218|**18,731**|20,960|Strands|
|LLM Calls|2|2|2|Tie|
|Tool Calls|1|1|1|Tie|
|Prompt Tokens|~2,238 †|**2,380**|2,534|LangGraph †|
|Completion Tokens|~344 †|**323**|372|Strands|
|Total Tokens|~2,582 †|**2,703**|2,906|LangGraph †|
|Cold Start (ms)|—|2,147|**2,080**|Hermes|
|Peak Memory (MB)|~133.64 †|**44.02**|54.17|Strands|
|Answer Quality|✅ Bullet points, bold|✅ Bold terms, structured|✅ Federal/Parl/Republic sections|All excellent|

> **Strands is fastest** at 18.7s — **1.6× faster** than LangGraph (29.2s). Same task shape (1 KB search, 2 LLM calls) — the speed difference is purely framework overhead.
> 
> All three produce the **same factual content** (federal parliamentary republic, Bundestag, Chancellor, Basic Law), but with different formatting styles. 

---

#### 3. Averaged Metrics (Across 2 Common Questions)

|Metric|LangGraph †|Strands|Hermes|🏆 Winner|Margin|
|---|---|---|---|---|---|
|**Avg Latency (ms)**|31,758|**29,396**|32,849|**Strands**|2,362 ms faster than LangGraph|
|**Avg LLM Calls**|**2.0**|2.5|**2.0**|**LG / Hermes**|0.5 fewer than Strands|
|**Avg Tool Calls**|**1.0**|1.5|**1.0**|**LG / Hermes**|0.5 fewer than Strands|
|**Avg Prompt Tokens**|**2,289**|3,247|2,548|**LangGraph**|259 fewer than Hermes|
|**Avg Completion Tokens**|**339**|441|351|**LangGraph**|12 fewer than Hermes|
|**Avg Total Tokens**|**2,627**|3,688|2,898|**LangGraph**|271 fewer than Hermes|
|**Avg Peak Memory (MB)**|133.64|**44.04**|54.17|**Strands**|10.13 MB less than Hermes|
|**Answer Quality**|100%|100%|100%|**Tie**|All 6/6 perfect|

> † LangGraph token and memory values estimated from prior runs of same questions. 

---

#### 4. Token Efficiency Breakdown

|Framework|Avg Prompt|Avg Completion|Avg Total|Prompt:Completion Ratio|
|---|---|---|---|---|
|LangGraph †|2,289|339|2,627|6.8:1|
|Strands|3,247|441|3,688|7.4:1|
|Hermes|2,548|351|2,898|7.3:1|

> **Strands** used the most tokens (3,688 avg) due to an extra KB search on Q1. **LangGraph** is the most token-efficient (2,627 avg) — minimal prompt accumulation. **Hermes** sits in the middle (2,898 avg) with the most balanced ratio.

---

#### 5. Memory & Cold Start Analysis

###### Peak Memory Comparison

|Framework|Pattern 1 Memory|Pattern 2 Memory|Growth|Architecture|
|---|:-:|:-:|:-:|---|
|LangGraph|58.55 MB|**133.64 MB**|**2.3×**|Embedding model loaded **in-process**|
|Strands|41.05 MB|**44.04 MB**|**1.07×**|Embedding model in **MCP subprocess**|
|Hermes|51.11 MB|**54.17 MB**|**1.06×**|Embedding model in **MCP subprocess**|

> 🔍 **Critical insight**: Both Strands and Hermes delegate the RAG stack to an MCP subprocess, keeping agent memory nearly flat (+3 MB). LangGraph loads sentence-transformers **in-process**, causing a **75 MB memory spike**. In serverless/Lambda contexts where memory = cost, this is a significant difference. 

###### Cold Start Comparison

|Framework|Q1 (First Run)|Q2 (Warm Run)|Delta|
|---|:-:|:-:|:-:|
|LangGraph|~10,996 ms †|—|—|
|Strands|5,008 ms|**2,147 ms**|−2,861 ms|
|Hermes|6,697 ms|**2,080 ms**|−4,617 ms|

> Cold start on Q2 (warm MCP server) drops dramatically for both Strands and Hermes. 

---

#### 6. Answer Quality Assessment

|Framework|Q1 (Australia)|Q2 (Germany)|Score|
|---|---|---|:-:|
|**LangGraph**|✅ 5 features, bold headings, source cite|✅ Bullet points, bold terms, structural analysis|**2/2 (100%)**|
|**Strands**|✅ `####` headers, sub-bullets, 4 features + reef detail|✅ Bold terms, structured with 5 key points|**2/2 (100%)**|
|**Hermes**|✅ 5 features with bold categories, closing summary|✅ Federal/Parliamentary/Republic breakdown|**2/2 (100%)**|

> 🎉 **All 3 frameworks achieve 100% answer quality on Pattern 2.** This is a major improvement over Pattern 1 (Strands 50%, Hermes 75%).
> 
> **Why?** Both questions are RAG-only (no `calculator_tool`). The Strands raw-dump bug and Hermes empty-answer bug both trigger on calculator-ending tasks, which don't appear here. 

---

#### 7. Winner Scorecard

|##|Category|Metric|Winner|Delta|
|---|---|---|---|---|
|1|Performance|Avg Latency|**Strands**|2,362 ms faster than LangGraph|
|2|Performance|Cold Start (Q2)|**Hermes**|67 ms faster than Strands (2,080 vs 2,147)|
|3|Efficiency|Avg LLM Calls|**LangGraph / Hermes**|0.5 fewer than Strands|
|4|Efficiency|Avg Tool Calls|**LangGraph / Hermes**|0.5 fewer than Strands|
|5|Efficiency|Avg Tokens|**LangGraph**|1,061 fewer than Strands|
|6|Resources|Peak Memory|**Strands**|10.13 MB less than Hermes|
|7|Quality|Answer Quality|**Tie**|All 6/6 perfect (100%)|
|8|Footprint|Packaging Size|**Hermes**|17.6 MB lighter than LangGraph|
|9|Footprint|Dependencies|**Hermes**|37 fewer than Strands|

###### Wins Tally

|Framework|Wins (out of 9)||
|---|:-:|---|
|**Hermes**|**5**|🏆🏆🏆🏆🏆|
|**LangGraph**|**4**|🏆🏆🏆🏆|
|**Strands**|**3**|🏆🏆🏆|
|Tie|**1**|➖|

---

#### 8. Framework Strengths & Weaknesses (Pattern 2)

###### LangGraph

|||
|---|---|
|✅ **Strengths**|Best token efficiency (2,627 avg); consistent answer formatting; fastest on Q1 (34.3s)|
|❌ **Weaknesses**|**Highest peak memory** (133.64 MB — 3× Strands); slowest on Q2 (29.2s — 1.6× slower than Strands); heaviest cold start (~11s)|
|🎯 **Best for**|RAG workloads where **token cost matters more than memory**|

###### AWS Strands Agents

|||
|---|---|
|✅ **Strengths**|**Fastest avg latency** (29,396 ms); **lowest peak memory** (44 MB — flat from Pattern 1!); excellent answer quality with richest formatting (`####` headers, sub-bullets)|
|❌ **Weaknesses**|Highest token usage (3,688 avg — extra KB search inflated Q1); extra LLM call on Q1 (3 vs 2)|
|🎯 **Best for**|**Memory-constrained** RAG deployments; production use where formatted output matters|

###### Hermes

|||
|---|---|
|✅ **Strengths**|**Lightest packaging** (967 MB, 267 deps); fastest warm cold start (2,080 ms); balanced token usage (2,898 avg); subprocess isolation keeps memory low (54 MB)|
|❌ **Weaknesses**|Slowest avg latency (32,849 ms); first-run includes `uv` build overhead|
|🎯 **Best for**|**Cost-optimized** RAG deployments; environments prioritizing minimal dependencies|

---

#### 9. Overall Verdict

|Rank|Framework|Score|Key Differentiator|
|---|---|---|---|
|🥇|**Strands**|3/9 wins|**Fastest + lowest memory** — 29.4s avg latency, 44 MB peak. The extra KB search on Q1 is actually a feature (richer answers). **Biggest glow-up from Pattern 1** (where it scored last).|
|🥈|**Hermes**|5/9 wins|**Lightest footprint** — 267 deps, 967 MB packaging, excellent cold start. Trades ~3s latency for simpler deployment. Most category wins overall.|
|🥉|**LangGraph**|4/9 wins|**Most token-efficient** — fewest tokens per answer. But 133 MB memory is 3× competitors. Best when token cost > memory cost.|

###### 🔄 Pattern 1 → Pattern 2: How the Rankings Shifted

|Metric|Pattern 1 Winner|Pattern 2 Winner|What Changed|
|---|:-:|:-:|---|
|Latency|**Hermes** (9.5s)|**Strands** (29.4s)|RAG startup costs leveled the field; Strands' lean runtime won|
|Peak Memory|**Strands** (41 MB)|**Strands** (44 MB)|Strands stays flat — subprocess isolation pays off|
|Answer Quality|**LangGraph** (100%)|**Tie** (100% all 3)|RAG-only questions avoid calculator bugs — all 3 now perfect|
|Tokens|**Hermes** (3,092)|**LangGraph** (2,627)|LangGraph's simpler RAG prompt uses fewer tokens|
|Packaging|**Hermes** (49 MB)|**Hermes** (967 MB)|All ~1 GB — RAG stack dominates; framework delta = noise|
|Cold Start|**Hermes** (1.9s)|**Hermes** (2.1s)|Hermes advantage persists on warm runs|
|**Overall**|🥇 Hermes, 🥈 LG, 🥉 Strands|🥇 Strands, 🥈 Hermes, 🥉 LG|**Complete reversal for Strands!**|

###### Pattern 2 Key Takeaway

> **Pattern 2 is where Strands redeemed itself.** After finishing last in Pattern 1 (raw tool dumps, highest latency, 1/9 wins), Strands takes first on **speed + memory** in Pattern 2.
> 
> **Why the reversal?** Two factors:
> 
> 1. **RAG-only questions** avoid the `calculator_tool` that triggers Strands' synthesis bug
> 2. Strands' **subprocess memory isolation** barely adds overhead (+3 MB from Pattern 1), while LangGraph's in-process approach adds +75 MB
> 
> **The real insight**: Framework performance is **pattern-dependent**. There is no universal winner — the right choice depends on your tool mix, memory constraints, and whether your tasks end with text or calculations.