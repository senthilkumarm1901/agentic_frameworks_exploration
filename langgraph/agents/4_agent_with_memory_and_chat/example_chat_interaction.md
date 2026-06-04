# Example Chat Interaction — Pattern 4

This document demonstrates a multi-turn conversation that tests the memory system and multiple skills.

## Session Overview

| Turn | Skill Tested | Purpose |
|------|--------------|---------|
| 1 | `country-profile` | Build a comprehensive profile for India |
| 2 | `country-comparison` | Compare India with Japan (memory should recall India data) |
| 3 | (memory reference) | Ask "same for Brazil" — agent should understand context |
| 4 | `regional-analysis` | Analyze Asian economies (India, Japan, China) |
| 5 | `memory` command | View conversation summary |

---

## Turn 1: Country Profile (India)

**User Input:**
```
Build a comprehensive profile of India
```

**Expected Behavior:**
1. Agent activates `country-profile` skill
2. Fetches GDP, population, area via `country_lookup_tool`
3. Searches qualitative facts via `country_kb_search_tool`
4. Formats output as a structured profile

**Expected Output (summary):**
- GDP: $3.55T
- Population: 1,438.1M
- Area: 2,973,190 km²
- Key facts: World's largest democracy, 22 official languages, major IT hub

**Expected Metrics:**
```json
{
  "pattern": "agent_with_memory_and_chat",
  "turn_count": 1,
  "llm_calls": 3-4,
  "tool_calls": 4-6,
  "skill_activations": 1,
  "tools_used": ["activate_skill", "country_lookup_tool", "country_lookup_tool", "country_lookup_tool", "country_kb_search_tool"]
}
```

---

## Turn 2: Country Comparison (India vs Japan)

**User Input:**
```
Compare India and Japan
```

**Expected Behavior:**
1. Agent activates `country-comparison` skill
2. May reuse India data from memory context (short-term)
3. Fetches Japan data via `country_lookup_tool`
4. Calculates derived metrics via `calculator_tool`
5. Produces comparison table

**Expected Output (summary):**
| Metric | India | Japan |
|--------|-------|-------|
| GDP | $3.55T | $4.21T |
| Population | 1,438.1M | 124.5M |
| GDP per Capita | ~$2,500 | ~$33,800 |

**Expected Metrics:**
```json
{
  "turn_count": 2,
  "skill_activations": 1,
  "tool_calls": 6-10
}
```

---

## Turn 3: Memory Reference ("same for Brazil")

**User Input:**
```
Now same for Brazil
```

**Expected Behavior:**
1. Agent uses memory to understand "same" = compare with India
2. Activates `country-comparison` skill
3. Fetches Brazil data
4. Produces India vs Brazil comparison

**Why This Tests Memory:**
- User doesn't explicitly say "compare India and Brazil"
- Agent must infer from conversation history that the pattern is comparison
- Short-term memory (MemorySaver) holds the previous turns

**Expected Output:**
| Metric | India | Brazil |
|--------|-------|--------|
| GDP | $3.55T | $2.17T |
| Population | 1,438.1M | 216.4M |

---

## Turn 4: Regional Analysis (Asian Economies)

**User Input:**
```
Give me a regional analysis of Asian economies: India, Japan, and China
```

**Expected Behavior:**
1. Agent activates `regional-analysis` skill
2. Fetches data for all 3 countries (may reuse some from memory)
3. Computes regional aggregates
4. Produces regional summary

**Expected Output (summary):**
- Total GDP: ~$26T (India $3.55T + Japan $4.21T + China $18.27T)
- Total Population: ~2.97B
- Regional characteristics

**Expected Metrics:**
```json
{
  "turn_count": 4,
  "skill_activations": 1,
  "tool_calls": 9-15
}
```

---

## Turn 5: View Memory Summary

**User Input:**
```
memory
```

**Expected Behavior:**
- Displays the LLM-generated conversation summary
- Shows topics discussed, key facts, user preferences

**Expected Output:**
```
──────────────────────────────────────────────────
📝 Memory (Turn 4):
## Conversation Summary

### Topics Discussed
- India country profile
- India vs Japan comparison
- India vs Brazil comparison
- Asian regional analysis (India, Japan, China)

### Key Facts Retrieved
- India: GDP $3.55T, Pop 1438.1M, world's largest democracy
- Japan: GDP $4.21T, Pop 124.5M, oldest population globally
- China: GDP $18.27T, Pop 1410.7M
- Brazil: GDP $2.17T, Pop 216.4M

### User Preferences
- Prefers structured comparison tables
- Uses "same for X" pattern for follow-up comparisons
- Interested in economic metrics and regional groupings

### Last Interaction
- User requested regional analysis of Asian economies
──────────────────────────────────────────────────
```

---

## Running This Interaction

```bash
cd langgraph/agents/4_agent_with_memory_and_chat
uv sync
uv run python -m src.main --reset  # Start with clean memory

# Then enter the prompts in order:
# 1. Build a comprehensive profile of India
# 2. Compare India and Japan
# 3. Now same for Brazil
# 4. Give me a regional analysis of Asian economies: India, Japan, and China
# 5. memory
# 6. quit
```

## Verifying Logs

After the interaction, check `logs.txt` for JSON metrics:

```bash
cat logs.txt | python -m json.tool
```

Each turn should have a complete metrics entry matching Pattern 3 format:
- `answer`: Full response text
- `framework`: "langgraph"
- `pattern`: "agent_with_memory_and_chat"
- `turn_count`: Sequential turn number
- `llm_calls`, `tool_calls`, `skill_activations`
- `tools_used`: List of tool names
- `total_duration_ms`
- `prompt_tokens`, `completion_tokens`, `total_tokens`

---

## Memory Persistence Test

To test that memory survives restarts:

```bash
# Run session 1
uv run python -m src.main
# Ask: "Build a profile of France"
# Type: quit

# Run session 2 (without --reset)
uv run python -m src.main
# Type: memory
# Should show France profile in summary
# Ask: "Same for Germany"
# Agent should understand to build Germany profile (from memory context)
```
