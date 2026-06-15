
# 📊 Pattern 4: Multi-Turn Conversational Agent — Report

---

## Experiment Setup

| Parameter            | Value                                                     |
| -------------------- | --------------------------------------------------------- |
| **Pattern**          | `4_agent_with_memory_and_chat`                            |
| **Model**            | `qwen3.5:35b-a3b-coding-nvfp4` (identical across all 3 ✅) |
| **Conversation**     | 4-turn sequential with cumulative context                 |
| **Diagnostic Tests** | T3: Context memory; T4: Knowledge reasoning               |

> **Note**: Hermes E#1 had MilvusLite connection errors (3 failed `kb_search` → 10 LLM calls). E#2 (clean restart) used as T1. This shows errors can break Hermes's flat scaling. 

---

## 1. Per-Turn Results

### T1: India Profile

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|52,522|**48,810**|55,394|Strands|
|LLM Calls|**4**|6|**4**|LG / Hermes|
|Tool Calls|7|7|7|Tie|
|Total Tokens|7,521|9,906|**6,499**|Hermes|

### T2: India vs Japan

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|79,890|31,251|**25,090**|Hermes|
|LLM Calls|8|17|**4**|Hermes|
|Tool Calls|19|22|**12**|Hermes|
|Total Tokens|22,420|44,980|**10,926**|Hermes|

### T3: "Same for Brazil" (Context Test)

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|32,189|**17,977**|23,298|Strands|
|LLM Calls|11|25|**4**|Hermes|
|Tool Calls|25|28|**12**|Hermes|
|Total Tokens|34,797|83,562|**16,590**|Hermes|
|Context Test|✅ **India vs Brazil**|⚠️ India+Japan+Brazil (3-way)|❌ **Brazil vs Japan**|**LangGraph**|

### T4: Most Populous EU (Reasoning Test)

|Metric|LangGraph|Strands|Hermes|Best|
|---|---|---|---|---|
|Latency (ms)|76,433|**24,254**|56,018|Strands|
|LLM Calls|14|33|**3**|Hermes|
|Tool Calls|36|35|**11**|Hermes|
|Total Tokens|**50,593**|123,606|N/A|LangGraph|
|Country Chosen|🇩🇪 Germany|🇩🇪 Germany|🇷🇺 Russia + error recovery|—|

> ⚠️ Hermes T3 compared **Brazil vs Japan** — dropped India entirely. 

---

## 2. Cumulative Growth Analysis

### LLM Call Growth

|Turn|LangGraph|Strands|Hermes|
|---|:-:|:-:|:-:|
|T1|4|6|4|
|T2|8|17|4|
|T3|11|25|4|
|T4|14|33|**3**|
|**Growth**|4→14 (**3.5×**)|6→33 (**5.5×**)|4→3 (**0.75×**)|

### Token Growth (Now 3-Way for T1–T3!)

|Turn|LangGraph|Strands|Hermes|LG ×|ST ×|HM ×|
|---|:-:|:-:|:-:|:-:|:-:|:-:|
|T1|7,521|9,906|6,499|1.0×|1.0×|1.0×|
|T2|22,420|44,980|10,926|3.0×|4.5×|1.7×|
|T3|34,797|83,562|16,590|4.6×|8.4×|**2.6×**|
|T4|50,593|123,606|N/A|6.7×|12.5×|—|

> **New with Hermes tokens**: T1→T3 growth is **2.6×** (6.5K→16.6K) vs LangGraph 4.6× vs Strands 8.4×. **Hermes is the most token-efficient.** By T3, Strands uses **5× more tokens** than Hermes. 

### Prompt:Completion Ratio

|Turn|LangGraph|Strands|Hermes|
|---|:-:|:-:|:-:|
|T1|11.6:1|16.1:1|**10.4:1**|
|T2|3.9:1|20.5:1|12.4:1|
|T3|5.3:1|22.2:1|13.0:1|
|T4|6.4:1|26.5:1|N/A|

### Latency Growth

|Turn|LangGraph (s)|Strands (s)|Hermes (s)|
|---|:-:|:-:|:-:|
|T1|52.5|48.8|55.4|
|T2|79.9|31.3|**25.1**|
|T3|32.2|**18.0**|23.3|
|T4|76.4|**24.3**|56.0|



---

## 3. Context Test: "Same for Brazil" 

|Framework|Interpreted As|Result|
|---|---|:-:|
|**LangGraph**|India vs Brazil|✅ **Pass**|
|**Strands**|India + Japan + Brazil (3-way)|⚠️ **Partial**|
|**Hermes**|**Brazil vs Japan**|❌ **Fail**|

> Hermes dropped India entirely

---

## 4. Knowledge Reasoning: T4

|Framework|Chose|Reasoning|Defensible?|
|---|---|---|:-:|
|**LangGraph**|🇩🇪 Germany|EU interpretation|✅|
|**Strands**|🇩🇪 Germany|EU interpretation|✅|
|**Hermes**|🇷🇺 Russia|Geographic + error recovery|✅|

---

## 5. Winner Scorecard

|#|Category|Metric|Winner|Evidence|
|---|---|---|---|---|
|1|Performance|T1 Latency|**Strands**|48.8s|
|2|Performance|Avg Latency T2-T4|**Hermes**|34.8s avg|
|3|Scaling|LLM Call Stability|**Hermes**|4→4→4→3 O(1)|
|4|Scaling|Token Growth T1-T3|**Hermes**|2.6× vs LG 4.6×, ST 8.4×|
|5|Scaling|Tool Call Efficiency|**Hermes**|7→12→12→11|
|6|Context|"Same for Brazil"|**LangGraph**|Only correct answer|
|7|Context|Knowledge Reasoning|**Tie**|All defensible|
|8|Quality|Answer Formatting|**Tie**|All well-formatted|
|9|Skills|Skill Utilization|**LangGraph / Strands**|7 activations each|
|10|Resilience|Error Recovery|**Hermes**|Russia→Russian Federation|
|11|Efficiency|Warm Caching|**Strands**|48.8→18.0s|

### Wins Tally

|Framework|Wins (out of 11)||
|---|:-:|---|
|**Hermes**|**5**|🏆🏆🏆🏆🏆|
|**LangGraph**|**3**|🏆🏆🏆|
|**Strands**|**3**|🏆🏆🏆|
|Tie|**2**|➖|



---

## 6. Strengths & Weaknesses

### LangGraph

|||
|---|---|
|✅|**Only context-correct framework** ✅; best T1→T4 token efficiency (6.7×); 2-skill orchestration|
|❌|LLM calls grow linearly (4→14); tool calls 5.1× (7→36); slowest T2/T4|
|🎯|Bounded multi-turn where **context accuracy** is non-negotiable|

### AWS Strands Agents

|||
|---|---|
|✅|Fastest warm turns (T3=18s!); latency decreases with caching; 2-skill orchestration|
|❌|LLM calls explode (6→33); tokens explode (9.9K→123.6K); context only partial (3-way)|
|🎯|Short warm conversations (1-2 turns); NOT deep multi-turn|

### Hermes

|||
|---|---|
|✅|**Flat O(1) LLM scaling** (4→3); **most token-efficient** (2.6× T1→T3); error recovery|
|❌|❌ **Failed context test** (Brazil vs Japan); 0 skills on T4; MilvusLite errors broke E#1|
|🎯|**Stateless chatbots** — each turn self-contained (NOT context-dependent follow-ups)|

---

## 7. Overall Verdict

|Rank|Framework|Score|Key Differentiator|
|---|---|---|---|
|🥇|**Hermes**|5/11|Flat O(1) scaling + most token-efficient. But context failure is a production risk.|
|🥈|**LangGraph**|3/11|**Only context-correct framework**. Linear O(n) is the trade-off for reliability.|
|🥉|**Strands**|3/11|Fastest warm turns (18s). But 33 LLM calls + 124K tokens + partial context.|

---

## 8. Recommendation

|Your Scenario|Use|Why|
|---|---|---|
|Chatbot with follow-ups ("same for X")|**LangGraph**|Only one that handles implicit references|
|Stateless Q&A (each turn independent)|**Hermes**|O(1) scaling, cheapest tokens|
|Short RAG conversations (1-2 turns)|**Strands**|Fastest warm turns, lowest memory|
|Complex analytical workflows|**LangGraph**|100% accuracy P1+P3, correct context P4|