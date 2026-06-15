## 📊 Pattern 1: Agent with Multiple MCP Tools — Evaluation Report

---

#### Experiment Setup

| Parameter        | Value                                                                  |
| ---------------- | ---------------------------------------------------------------------- |
| **Pattern**      | `1_agent_with_multiple_mcp_tools`                                      |
| **Task**         | Country Analysis (population, GDP, area lookups + calculations)        |
| **Model**        | `qwen3.5:35b-a3b-coding-nvfp4` (local Ollama — identical across all 3) |
| **MCP Tools**    | `country_lookup_tool`, `calculator_tool`                               |
| **Experiments**  | 4 questions × 3 frameworks = **12 total runs**                         |
| **All statuses** | `SUCCESS`                                                              |
| **Note**         | Strands was re-run after an `agent.py` bug fix (see Section 5)         |

###### Questions & Complexity

|##|Question|Complexity|
|---|---|---|
|E##1|What is the population density of Japan in people per square kilometer?|Medium (3 tools, 1 calc)|
|E##2|What is the ratio of GDP per capita between the United States and Japan? Calculate it precisely|Hard (6–7 tools, multi-calc)|
|E##3|What is the GDP per capita of Germany in trillion USD per million people?|Medium (3 tools, 1 calc)|
|E##4|Which country has a larger population, India or China?|Easy (2 lookups, no calc)|

---

#### 1. Static Metrics (Framework Footprint)

|Metric|LangGraph|Strands|Hermes|🏆 Winner|
|---|---|---|---|---|
|Packaging Size (MB)|76.94|72.80|**49.34**|Hermes|
|Lines of Code|355|358|389|—|
|Dependency Count|175|142|**101**|Hermes|

> **Hermes** has the lightest footprint — **36% smaller** than LangGraph in packaging size and **42% fewer dependencies** (101 vs 175). Lines of Code is comparable across all three (~355–389 LOC).

---

#### 2. Per-Experiment Results (All 12 Runs)

###### Experiment ##1: Japan Population Density

**Question:** _What is the population density of Japan in people per square kilometer?_ **Complexity:** Medium (3 tools, 1 calc)

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|21,499|19,454|**8,065**|Hermes|
|LLM Calls|3|3|3|Tie|
|Tool Calls|3|3|3|Tie|
|Total Tokens|2,943|3,058|3,253|LangGraph|
|Cold Start (ms)|6,950|5,721|**1,854**|Hermes|
|Peak Memory (MB)|58.50|**41.04**|51.17|Strands|
|Answer Quality|✅ Well-formatted NL|✅ Well-formatted NL 🔧|✅ Well-formatted NL|—|

> 🔧 **Strands E##1 now produces proper NL after the `agent.py` fix.** Hermes is **2.7× faster** than LangGraph and **2.4× faster** than Strands on this task.

---

###### Experiment ##2: US/Japan GDP Ratio

**Question:** _What is the ratio of GDP per capita between the United States and Japan? Calculate it precisely_ **Complexity:** Hard (6–7 tools, multi-calc)

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|14,211|**13,804**|15,783|Strands|
|LLM Calls|3|**5**|3|LangGraph / Hermes|
|Tool Calls|6|**7**|6|LangGraph / Hermes|
|Total Tokens|4,177|**6,247**|**3,958**|Hermes|
|Cold Start (ms)|1,959|1,979|**1,854**|Hermes|
|Peak Memory (MB)|58.59|**41.11**|51.18|Strands|
|Answer Quality|✅ Well-formatted NL|⚠️ **Raw tool output**|✅ Excellent structured NL|—|

> ⚡ **Hardest task** — Strands needed 5 LLM calls and 7 tool calls. Despite the fix, E##2 **still shows raw tool output**: the model's last cycle was a `tool_use` block (calculator), so the synthesis suffix couldn't trigger. Hermes used only 3 LLM calls for 6 tools and produced the best-formatted answer.

---

###### Experiment ##3: Germany GDP per Capita

**Question:** _What is the GDP per capita of Germany in trillion USD per million people?_ **Complexity:** Medium (3 tools, 1 calc)

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|8,349|**7,609**|7,885|Strands|
|LLM Calls|3|3|3|Tie|
|Tool Calls|3|3|3|Tie|
|Total Tokens|3,680|**3,066**|3,177|Strands|
|Cold Start (ms)|2,059|1,967|**1,877**|Hermes|
|Peak Memory (MB)|58.56|**41.04**|50.95|Strands|
|Answer Quality|✅ Well-formatted NL|⚠️ **Raw tool dump**|❌ **Empty answer**|—|

> 🐛 **Hermes empty answer**: Tools executed correctly (3 calls, 360 completion tokens), but the final answer field was `""`. Silent synthesis failure. Strands also returns raw tool dump — same root cause (last cycle = calculator `tool_use`).

---

###### Experiment ##4: India vs China Population

**Question:** _Which country has a larger population, India or China?_ **Complexity:** Easy (2 lookups, no calc)

| Metric           | LangGraph           | Strands             | Hermes              | Best      |
| ---------------- | ------------------- | ------------------- | ------------------- | --------- |
| Latency (ms)     | 5,540               | **4,945**           | 6,138               | Strands   |
| LLM Calls        | 2                   | 2                   | 2                   | Tie       |
| Tool Calls       | 2                   | 2                   | 2                   | Tie       |
| Total Tokens     | **1,761**           | 1,866               | 1,979               | LangGraph |
| Cold Start (ms)  | 2,087               | 1,970               | **1,888**           | Hermes    |
| Peak Memory (MB) | 58.53               | **41.01**           | 51.15               | Strands   |
| Answer Quality   | ✅ Well-formatted NL | ✅ Well-formatted NL | ✅ Well-formatted NL | —         |

> ✅ **All three frameworks produce clean NL** on this simple task. No calculator needed — the model's final cycle is naturally a text response.

---

#### 3. Averaged Metrics (Across 4 Experiments)

| Metric                    | LangGraph | Strands   | Hermes    | 🏆 Winner   | Margin                       |
| ------------------------- | --------- | --------- | --------- | ----------- | ---------------------------- |
| **Avg Latency (ms)**      | 12,400    | 11,453    | **9,468** | Hermes      | 1,985 ms faster than Strands |
| **Avg LLM Calls**         | **2.75**  | 3.25      | **2.75**  | LG / Hermes | 0.50 fewer than Strands      |
| **Avg Tool Calls**        | **3.50**  | 3.75      | **3.50**  | LG / Hermes | 0.25 fewer than Strands      |
| **Avg Prompt Tokens**     | **1,977** | 3,152     | 2,650     | LangGraph   | 674 tokens vs Hermes         |
| **Avg Completion Tokens** | 1,164     | 407       | **442**   | Strands     | 35 tokens vs Hermes          |
| **Avg Total Tokens**      | 3,140     | 3,559     | **3,092** | Hermes      | 49 tokens vs LangGraph       |
| **Avg Cold Start (ms)**   | 3,264     | 2,909     | **1,868** | Hermes      | 1,041 ms faster than Strands |
| **Avg Peak Memory (MB)**  | 58.55     | **41.05** | 51.11     | Strands     | 10.06 MB less than Hermes    |
| **Answer Quality**        | **100%**  | 50%       | 75%       | LangGraph   | 25% higher than Hermes       |


---

#### 4. Token Efficiency Breakdown

|Framework|Avg Prompt|Avg Completion|Avg Total|Prompt:Completion Ratio|
|---|---|---|---|---|
|LangGraph|1,977|1,164|3,140|1.7:1|
|Strands|3,152|407|3,559|7.7:1|
|Hermes|2,650|442|3,092|6.0:1|

> **Strands** consumes the most tokens on average (3,559) due to verbose prompt accumulation in multi-step tasks. **LangGraph** has the highest completion tokens (1,164 avg) — its model produces longer, more detailed answers. **Hermes** has the most balanced token efficiency: lowest total (3,092) with moderate prompt and completion usage.

---

#### 5. Answer Quality Assessment

###### Results Matrix

| Framework     | E##1 (Japan Density) | E##2 (GDP Ratio)   | E##3 (Germany GDP/cap) | E##4 (India vs China) |     Score      |
| ------------- | ------------------- | ----------------- | --------------------- | -------------------- | :------------: |
| **LangGraph** | ✅ Structured NL     | ✅ Bullet points   | ✅ Calculation shown   | ✅ Clean comparison   | **4/4 (100%)** |
| **Strands**   | ✅ NL 🔧 _fixed_     | ⚠️ Raw tool dump  | ⚠️ Raw tool dump      | ✅ Clean comparison   | **2/4 (50%)**  |
| **Hermes**    | ✅ Detailed steps    | ✅ Structured data | ❌ Empty answer        | ✅ Population figures | **3/4 (75%)**  |

###### What Changed After the Strands `agent.py` Fix?



> **Diagnosis**: The `_SYNTHESIS_SUFFIX` system prompt fix could help in Strands giving NL answers instead of  `Raw tool dump` but that would add additional prompt
---

#### 6. Winner Scorecard

| ##   | Category    | Metric         | Winner        | Margin                        |
| --- | ----------- | -------------- | ------------- | ----------------------------- |
| 1   | Performance | Latency        | **Hermes**    | 1,985 ms faster than Strands  |
| 2   | Performance | Cold Start     | **Hermes**    | 1,041 ms faster than Strands  |
| 3   | Efficiency  | LLM Calls      | **LangGraph** | 0.50 fewer than Strands       |
| 4   | Efficiency  | Tool Calls     | **LangGraph** | 0.25 fewer than Strands       |
| 5   | Efficiency  | Token Usage    | **Hermes**    | 49 fewer than LangGraph       |
| 6   | Resources   | Peak Memory    | **Strands**   | 10.06 MB less than Hermes     |
| 7   | Quality     | Answer Quality | **LangGraph** | 25% higher than Hermes        |
| 8   | Footprint   | Packaging Size | **Hermes**    | 23.46 MB lighter than Strands |
| 9   | Footprint   | Dependencies   | **Hermes**    | 41 fewer than Strands         |

###### Wins Tally

|Framework|Wins (out of 9)||
|---|:-:|---|
|**Hermes**|**5**|🏆🏆🏆🏆🏆|
|**LangGraph**|**3**|🏆🏆🏆|
|**Strands**|**1**|🏆|

---

#### 7. Framework Strengths & Weaknesses

###### LangGraph

|||
|---|---|
|✅ **Strengths**|Best answer quality (**100% NL synthesis** — never fails); lowest avg LLM calls (2.75); most reliable output formatting|
|❌ **Weaknesses**|Heaviest footprint (76.94 MB, 175 deps); highest peak memory (58.55 MB); worst first-run cold start (6,950 ms); slowest avg latency (12,400 ms)|
|🎯 **Best for**|Production apps where **output quality and reliability** are non-negotiable|

###### AWS Strands Agents

|||
|---|---|
|✅ **Strengths**|Lowest peak memory (**41.05 MB** — 30% less than LangGraph); fastest on simple tasks (E##4: 4,945 ms)|
|❌ **Weaknesses**|Answer quality issues persist (**50% NL** after fix); highest avg token consumption (3,559); most LLM calls on complex tasks (5 in E##2); synthesis fix only partial|
|🎯 **Best for**|**Memory-constrained** environments where you add your own formatting layer|

###### Hermes

|||
|---|---|
|✅ **Strengths**|**Fastest overall** (9,468 ms avg); lightest packaging (49.34 MB, 101 deps); lowest cold start (1,868 ms avg); good answer quality (75%); fewest tokens on hard tasks|
|❌ **Weaknesses**|One silent empty-answer failure in E##3 (synthesis bug — tools worked, answer didn't); slightly higher memory than Strands|
|🎯 **Best for**|**Speed-critical** pipelines and lightweight deployments where every millisecond counts|

---

#### 8. Overall Verdict

|Rank|Framework|Score|Key Differentiator|
|---|---|---|---|
|🥇|**Hermes**|5/9 wins|**Fastest** (9,468 ms avg — 1.3× faster than LangGraph), lightest footprint (49 MB), lowest cold start. One answer failure prevents a clean sweep.|
|🥈|**LangGraph**|3/9 wins|**Most reliable** (100% NL answer rate — never fails). Trades speed and size for polished, production-ready output.|
|🥉|**Strands**|1/9 wins|**Lowest memory** (41.05 MB — 1.4× lighter than LangGraph at runtime). But answer quality (50%) remains a significant gap even after the fix.|

###### The Nuanced Take

|If you care about...|Choose|Why|
|---|---|---|
|⚡ Speed + efficiency|**Hermes**|1.3× faster than next-best, fewest tokens, lowest cold start|
|✅ Output reliability|**LangGraph**|100% NL synthesis rate — never returns raw dumps or empty answers|
|💾 Memory constraints|**Strands**|41 MB peak — ideal for serverless/Lambda where memory = cost|
|📦 Minimal deps|**Hermes**|101 dependencies, 49 MB installed — smallest attack surface|
|🏗️ Production readiness|**LangGraph**|Mature ecosystem, reliable output, no silent failures|

###### Pattern 1 Key Takeaway

> **Same Prompt. Same LLM. Same MCP tools.  Same questions. Three different frameworks.**
> 
> The framework choice changed latency by **1.3×**, runtime memory by **1.4×**, packaging size by **1.6×**, and answer quality from **50% to 100%**.
> 
> The goal isn't to declare an absolute winner — **it's to show where each framework shines, struggles, and surprises.**
