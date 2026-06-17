## 📊 Pattern 3: Agent with MCP Tools & Skills — Evaluation Report

---

#### Experiment Setup

| Parameter        | Value                                                                                |
| ---------------- | ------------------------------------------------------------------------------------ |
| **Pattern**      | `3_agent_with_mcp_tools_and_skills`                                                  |
| **Task**         | Country Analysis with **RAG + Skills** (skill-guided multi-tool orchestration)       |
| **Model**        | `qwen3.5:35b-a3b-coding-nvfp4` (local Ollama — identical across all 3)               |
| **RAG Stack**    | MilvusLite + `sentence-transformers/all-MiniLM-L6-v2` + FAISS                        |
| **MCP Tools**    | `activate_skill`, `country_lookup_tool`, `calculator_tool`, `country_kb_search_tool` |
| **Skills**       | `country-comparison`, `country-profile`, `regional-analysis`, `report-formatting`    |
| **Experiments**  | 4 questions × 3 frameworks = **12 total runs**                                       |
| **All statuses** | `SUCCESS`                                                                            |
| **All answers**  | ✅ Well-formatted NL (12/12 = **100% synthesis rate**)                                |

###### Common Questions

|##|Question|Expected Skill|Complexity|
|---|---|---|---|
|E##1|Compare GDP & population of Japan vs Germany — which has higher GDP per capita?|`country-comparison`|Hard (8 tools, calc, KB)|
|E##2|Comprehensive profile of Brazil including key statistics|`country-profile`|Medium (7 tools, calc, KB)|
|E##3|European GDP analysis — highest + regional total|`regional-analysis`|Hard (8–11 tools, multi-lookup)|
|E##4|Professional formatted report comparing US and China across all metrics|`report-formatting`|Very Hard (12–18 tools, multi-skill)|



---

#### 1. Static Metrics (Framework Footprint)

|Metric|LangGraph †|Strands|Hermes|🏆 Winner|
|---|---|---|---|---|
|Packaging Size (MB)|~984.79|989.21|**966.39**|Hermes|
|Lines of Code|~373|431|417|LangGraph †|
|Dependency Count|~318|304|**267**|Hermes|

###### 📈 Packaging Size Across All Patterns

|Framework|P1 (MB)|P2 (MB)|P3 (MB)|P2→P3 Delta|
|---|:-:|:-:|:-:|:-:|
|LangGraph|76.94|984.79|~984.79|**~0** (skills = markdown, not deps)|
|Strands|72.80|996.81|989.21|**−7.6** (minor cleanup)|
|Hermes|49.34|967.18|966.39|**−0.8** (negligible)|

> **Key insight**: Adding skills added **zero packaging overhead**. Skills are markdown template files, not library dependencies. 

---

#### 2. Per-Experiment Results (All 12 Runs)

###### E##1: Japan vs Germany Comparison

**Expected Skill:** `country-comparison` | **Complexity:** Hard

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|59,897|**42,870**|68,782|Strands|
|LLM Calls|**4**|6|5|LangGraph|
|Tool Calls|8|8|8|Tie|
|Skill Activations|1|1|1|Tie|
|Total Tokens|**6,205**|9,945|8,170|LangGraph|
|Cold Start (ms)|9,461|**5,512**|7,003|Strands|
|Peak Memory (MB)|134.45|**49.94**|54.83|Strands|
|Answer Quality|✅ Table + analysis + KB context|✅ Table + key insight|✅ Table + key insight|—|

> Hermes was **slowest** (68.8s — includes first-run `uv` build overhead). LangGraph used fewest LLM calls (4 vs 6) for same 8 tool calls. 

---

###### E##2: Brazil Country Profile

**Expected Skill:** `country-profile` | **Complexity:** Medium

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|**25,330**|28,237|28,155|LangGraph|
|LLM Calls|4|6|**4**|LG / Hermes|
|Tool Calls|7|7|7|Tie|
|Skill Activations|1|1|1|Tie|
|Total Tokens|**5,997**|9,863|6,305|LangGraph|
|Cold Start (ms)|7,851|2,178|**2,060**|Hermes|
|Peak Memory (MB)|134.40|**44.16**|54.25|Strands|
|Answer Quality|✅ Table + facts + summary|✅ Stats + facts + summary|✅ Stats + facts + summary|—|

> **Closest race** — all three within 3s of each other (25.3s–28.2s). Hermes most LLM-efficient (4 calls vs 6 Strands). 

---

###### E##3: European GDP Analysis

**Expected Skill:** `regional-analysis` | **Complexity:** Hard

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|**16,445**|27,883|24,473|LangGraph|
|LLM Calls|**5**|7|5|LG / Hermes|
|Tool Calls|10|11|**8**|Hermes|
|Skill Activations|1|1|1|Tie|
|Total Tokens|**8,931**|13,783|8,363|Hermes|
|Cold Start (ms)|8,264|2,079|**2,041**|Hermes|
|Peak Memory (MB)|134.55|**44.20**|54.25|Strands|
|Factual Accuracy|✅ 6 countries, 17.05T|✅ 6 countries, 17.05T (self-corrected)|❌ **5 countries, 14.98T** (missed Russia)|—|

> 🐛 **Hermes factual error**: Missed Russian Federation — only 5 countries (14.98T) vs correct 6 countries (17.05T).
> 
> 🔧 **Strands self-recovery**: Tried `"UK"` and `"Russia"` (not found), then retried with `"United Kingdom"` and `"Russian Federation"` — 2 extra tool calls but **correct final answer**.
> 
> LangGraph was **fastest** (16.4s — nearly half Strands/Hermes time). 

---

###### Experiment 4: US vs China Formatted Report

- Question: Professional formatted report comparing US and China across all metrics
- **Expected Skills:** `country-comparison` & `report-formatting` | **Complexity:** Very Hard

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|58,698|39,744|**30,249**|Hermes|
|LLM Calls|8|11|**5**|Hermes|
|Tool Calls|**18**|15|**12**|Hermes|
|Skill Activations|**2**|**2**|1|LG / Strands|
|Total Tokens|16,861|**23,024**|**9,284**|Hermes|
|Cold Start (ms)|8,101|**2,051**|2,127|Strands|
|Peak Memory (MB)|134.91|**44.24**|54.28|Strands|
|Answer Quality|✅ Exec summary + table + insights + sources|✅ Summary + table + insights + sources|✅ Metrics table + insights (only 1 skill)|—|

> **Most complex task** 
> * LangGraph: 18 tools + 8 LLM + **2 skills**; 
> * Strands: 15 tools + 11 LLM + **2 skills**.
> * **Hermes used only 1 skill** (`country-comparison`) — didn't activate `report-formatting`

---

#### 3. Averaged Metrics (Across 4 Common Experiments)

|Metric|LangGraph|Strands|Hermes|🏆 Winner|Margin|
|---|---|---|---|---|---|
|**Avg Latency (ms)**|40,093|34,684|**37,915**|**Strands**|3,231 ms faster than Hermes|
|**Avg LLM Calls**|**5.25**|7.50|4.75|**Hermes**|0.50 fewer than LangGraph|
|**Avg Tool Calls**|10.75|10.25|**8.75**|**Hermes**|1.50 fewer than Strands|
|**Avg Skill Activations**|**1.25**|**1.25**|1.00|**LG / Strands**|0.25 more than Hermes|
|**Avg Prompt Tokens**|**8,675**|13,229|7,326|**Hermes**|1,349 fewer than LangGraph|
|**Avg Completion Tokens**|**823**|925|705|**Hermes**|119 fewer than LangGraph|
|**Avg Total Tokens**|9,499|14,154|**8,031**|**Hermes**|1,468 fewer than LangGraph|
|**Avg Cold Start (ms)**|8,419|2,955|**3,308**|**Strands**|353 ms faster than Hermes|
|**Avg Peak Memory (MB)**|134.58|**45.64**|54.40|**Strands**|8.77 MB less than Hermes|



---

#### 4. Skill Activation Analysis (New in Pattern 3)

|Experiment|Expected Skill|LangGraph|Strands|Hermes|
|---|---|---|---|---|
|E##1|`country-comparison`|✅ 1 (`comparison`)|✅ 1 (`comparison`)|✅ 1 (`comparison`)|
|E##2|`country-profile`|✅ 1 (`profile`)|✅ 1 (`profile`)|✅ 1 (`profile`)|
|E##3|`regional-analysis`|✅ 1 (`regional`)|✅ 1 (`regional`)|⚠️ 1 (`comparison` — **wrong skill**)|
|E##4|`report-formatting`|✅ **2** (`comparison` + `formatting`)|✅ **2** (`comparison` + `formatting`)|⚠️ **1** (`comparison` — missed `formatting`)|
|**Total**||**5 activations**|**5 activations**|**4 activations**|

> **LangGraph and Strands** both correctly identified E##4 as requiring **two skills**. **Hermes** consistently under-activated — used `country-comparison` for E##3 (should have been `regional-analysis`) and skipped `report-formatting` for E##4. The wrong skill choice in E##3 **directly caused the Russia omission**. 

---

#### 5. Factual Accuracy & Error Recovery

###### Accuracy Matrix

|Framework|E##1|E##2|E##3 (European GDP)|E##4|Score|
|---|:-:|:-:|:-:|:-:|:-:|
|**LangGraph**|✅|✅|✅ 6 countries, 17.05T|✅|**4/4 (100%)**|
|**Strands**|✅|✅|✅ 6 countries, 17.05T|✅|**4/4 (100%)**|
|**Hermes**|✅|✅|❌ **5 countries, 14.98T**|✅|**3/4 (75%)**|

###### E##3 Deep Dive: The Russia Problem

|Framework|Countries Found|Russia?|Total GDP|Correct?|
|---|:-:|:-:|:-:|:-:|
|LangGraph|6 (DE, UK, FR, IT, RU, ES)|✅ Yes|17.05T|✅|
|Strands|6 (same set)|✅ Yes (self-corrected)|17.05T|✅|
|Hermes|**5** (DE, UK, FR, IT, ES)|❌ **No**|**14.98T**|❌|

###### 🔧 Strands Error Recovery (E##3)

```
1. country_lookup_tool(country="UK")     → ❌ "Country UK not found"
2. country_lookup_tool(country="Russia")  → ❌ "Country Russia not found"
3. country_lookup_tool(country="United Kingdom")       → ✅ 3.42T
4. country_lookup_tool(country="Russian Federation")   → ✅ 2.07T
```

> **Strands demonstrated resilient error recovery** — when short names failed, it retried with full official names. Cost: 2 extra tool calls + 1 extra LLM call. Result: **correct answer despite initial failures**.
> 
> **Hermes never tried Russia** — the wrong skill (`country-comparison` instead of `regional-analysis`) didn't guide it to enumerate all European countries. The `regional-analysis` skill (which explicitly lists European countries) would have caught this. 

---

#### 6. Token Efficiency Breakdown

|Framework|Avg Prompt|Avg Completion|Avg Total|Prompt:Completion|
|---|:-:|:-:|:-:|:-:|
|LangGraph|8,675|823|9,499|10.5:1|
|Strands|13,229|925|14,154|14.3:1|
|Hermes|7,326|705|8,031|10.4:1|

> **Strands** is most token-hungry (14,154 avg) — verbose prompt accumulation across 7.5 avg LLM calls. On E##4 alone: **23,024 tokens** (2.5× Hermes).
> 
> **Hermes** is cheapest (8,031 avg) — fewer LLM calls = less prompt re-injection.
> 
> **LangGraph** is middle-ground (9,499 avg) — graph-based orchestration compresses context efficiently even with 10.75 avg tool calls. 

---

#### 7. Memory & Cold Start: Cross-Pattern Evolution

###### Peak Memory Across All Patterns

|Framework|P1 (MB)|P2 (MB)|P3 (MB)|P1→P3 Growth|Architecture|
|---|:-:|:-:|:-:|:-:|---|
|LangGraph|58.55|133.64|**134.58**|**2.3×**|In-process embedding model|
|Strands|41.05|44.04|**45.64**|**1.11×**|MCP subprocess isolation|
|Hermes|51.11|54.17|**54.40**|**1.06×**|MCP subprocess isolation|

> P2→P3 memory delta is **< 1 MB** for all frameworks. Skills add **zero memory overhead**. LangGraph's 135 MB remains **2.9× higher** than Strands's 46 MB.

###### Cold Start Progression

|Framework|P1 Avg (ms)|P2 Warm (ms)|P3 Warm Avg (ms)|Trend|
|---|:-:|:-:|:-:|---|
|LangGraph|3,264|—|8,072|Gets **worse** with complexity|
|Strands|2,909|2,147|2,103|Stable ~2.1s warm|
|Hermes|1,868|2,080|2,076|Stable ~2.1s warm|



---

#### 8. Winner Scorecard

|##|Category|Metric|Winner|Delta|
|---|---|---|---|---|
|1|Performance|Avg Latency|**Strands**|3,231 ms faster than Hermes|
|2|Performance|Cold Start (warm)|**Hermes**|2,076 ms avg — fastest warm start|
|3|Efficiency|Avg LLM Calls|**Hermes**|0.50 fewer than LangGraph|
|4|Efficiency|Avg Tool Calls|**Hermes**|1.50 fewer than Strands|
|5|Efficiency|Avg Total Tokens|**Hermes**|1,468 fewer than LangGraph|
|6|Resources|Peak Memory|**Strands**|8.77 MB less than Hermes|
|7|Skills|Skill Utilization|**LangGraph / Strands**|5 activations + correct multi-skill on E##4|
|8|Quality|Answer Formatting|**Tie**|12/12 well-formatted NL (100% all three)|
|9|Quality|Factual Accuracy|**LangGraph / Strands**|4/4 correct vs Hermes 3/4 (missed Russia)|
|10|Resilience|Error Recovery|**Strands**|Self-corrected UK/Russia name failures|
|11|Footprint|Packaging + Deps|**Hermes**|966 MB, 267 deps — lightest|

###### Wins Tally

|Framework|Wins (out of 11)||
|---|:-:|---|
|**Hermes**|**5**|🏆🏆🏆🏆🏆|
|**LangGraph**|**4**|🏆🏆🏆🏆|
|**Strands**|**4**|🏆🏆🏆🏆|
|Tie|**1**|➖|

---

#### 9. Framework Strengths & Weaknesses (Pattern 3)

###### LangGraph

|||
|---|---|
|✅ **Strengths**|Fewest LLM calls (5.25 avg); **100% factual accuracy**; correct multi-skill orchestration; fastest on E##3 (16.4s)|
|❌ **Weaknesses**|**Highest memory** (135 MB); slowest cold start (8.4s avg); slowest on E##1 & E##4|
|🎯 **Best for**|Complex multi-skill tasks where **accuracy and orchestration quality** are critical|

###### AWS Strands Agents

|||
|---|---|
|✅ **Strengths**|**Lowest memory** (46 MB); **100% factual accuracy**; **resilient error recovery** (self-corrected name failures); correct 2-skill orchestration|
|❌ **Weaknesses**|**Most token-hungry** (14,154 avg — 1.8× Hermes); most LLM calls (7.5 avg); E##4 consumed 23,024 tokens|
|🎯 **Best for**|**Memory-constrained** deployments needing **robust error handling** and guaranteed accuracy|

###### Hermes

|||
|---|---|
|✅ **Strengths**|**Fewest tokens** (8,031 avg); fewest tool calls (8.75 avg); lightest packaging (966 MB, 267 deps); fastest warm cold start|
|❌ **Weaknesses**|**Factual error** in E##3 (missed Russia — 14.98T vs 17.05T); **under-utilizes skills** (4/5, wrong skill on E##3); slowest on E##1 (68.8s)|
|🎯 **Best for**|**Speed-critical** tasks with well-defined scope (avoid multi-country enumeration risks)|

---

#### 10. Overall Verdict

|Rank|Framework|Score|Key Differentiator|
|---|---|---|---|
|🥇|**LangGraph**|4/11|**Most reliable**: 100% accuracy, fewest LLM calls, correct multi-skill orchestration. Trades memory (135 MB) for correctness.|
|🥈|**Hermes**|5/11|**Fastest + cheapest**: 37.9s avg, 8,031 tokens. But Russia miss and skill under-utilization are concerning for production.|
|🥉|**Strands**|4/11|**Most resilient**: 46 MB memory, 100% accuracy, self-healing error recovery. But 14,154 avg tokens make it the most expensive.|

###### 🔄 Cross-Pattern Ranking Evolution

||Pattern 1|Pattern 2|Pattern 3|Trend|
|---|:-:|:-:|:-:|---|
|🥇|**Hermes** (5/9)|**Strands** (3/9)|**LangGraph** (4/11)|LG rose steadily as complexity increased|
|🥈|**LangGraph** (3/9)|**Hermes** (5/9)|**Hermes** (5/11)|Hermes fast but accuracy gaps widen|
|🥉|**Strands** (1/9)|**LangGraph** (4/9)|**Strands** (4/11)|Strands: memory king, token spender|
|Answer Quality|LG 100%, H 75%, S 50%|All 100%|LG 100%, S 100%, **H 75%**|Hermes reliability plateaus|
|Memory King|Strands (41 MB)|Strands (44 MB)|Strands (46 MB)|Strands consistently lowest|
|Speed King|Hermes (9.5s)|Strands (29.4s)|Strands (34.7s)|Changes by pattern|
|Token King|Hermes (3,092)|LangGraph (2,627)|Hermes (8,031)|Hermes cheapest at scale|

###### Pattern 3 Key Takeaway

> **Skills changed the game — but not how you'd expect.**
> 
> Adding skills didn't change packaging, memory, or latency significantly. What it changed was **orchestration quality** — the ability to correctly identify which skill to use, when to use multiple skills, and how to follow skill-guided workflows.
> 
> **LangGraph and Strands** both correctly multi-skilled E##4 (2 activations) and found all European countries in E##3. **Hermes** was faster and cheaper, but chose the **wrong skill** for E##3 and missed a country as a result.
> 
> **The insight**: As pattern complexity grows from P1→P2→P3, **reliability and accuracy become more valuable than raw speed**. LangGraph's graph-based orchestration scales best with complexity — it went from 🥈 in P1 → 🥉 in P2 → **🥇 in P3**.
> 
> **There is no universal winner.** The right framework depends on your pattern:
> 
> |Need|Choose|
> |---|---|
> |Simple tool orchestration (P1)|**Hermes** — fastest, lightest|
> |RAG-only queries (P2)|**Strands** — fastest, lowest memory|
> |Complex multi-skill workflows (P3)|**LangGraph** — most accurate, best orchestration|
