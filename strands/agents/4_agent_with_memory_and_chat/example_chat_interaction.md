
# Interactive chat (the main use case)
`uv run python -m src.main`

# Start fresh (wipe saved memory)
`uv run python -m src.main --reset`



# Example Chat Interaction — Strands Pattern 4

This document demonstrates a multi-turn conversation that tests the two-tier memory system and multiple skills.

## Session Overview

| Turn | Skill Tested | Purpose |
|------|--------------|---------|
| 1 | `country-profile` | Build a comprehensive profile for India |
| 2 | `country-comparison` | Compare India with Japan (short-term memory recalls India data) |
| 3 | (memory reference) | Ask "same for Brazil" — agent uses memory for continuity |
| 4 | `regional-analysis` | Analyze Asian economies (India, Japan, China) |
| 5 | `memory` command | View long-term conversation summary |

---

## Turn 1: Country Profile (India)

**Input:**
```
Build a comprehensive profile of India
```

**Expected flow:**
1. Agent activates `country-profile` skill
2. Fetches GDP, population, area via `country_lookup_tool`
3. Searches qualitative facts via `country_kb_search_tool`
4. Formats profile per skill template

**Expected metrics:**
```json
{
  "framework": "strands",
  "pattern": "agent_with_memory_and_chat",
  "turn_count": 1,
  "skill_activations": 1,
  "tools_used": ["activate_skill", "country_lookup_tool", "country_lookup_tool", "country_lookup_tool", "country_kb_search_tool"]
}
```

---

## Turn 2: Country Comparison (India vs Japan)

**Input:**
```
Compare India and Japan
```

**Expected flow:**
1. Agent activates `country-comparison` skill
2. May reuse India data from short-term memory (ConversationManager history)
3. Fetches Japan data
4. Calculates derived metrics via `calculator_tool`

**Expected metrics:**
```json
{
  "turn_count": 2,
  "skill_activations": 1,
  "tool_calls": "6-10"
}
```

---

## Turn 3: Memory Reference ("same for Brazil")

**Input:**
```
Same for Brazil
```

**Expected flow:**
1. Agent reads short-term memory to understand "same" means country profile
2. Builds Brazil profile without re-activating skill (may reuse from memory)
3. Demonstrates context continuity

---

## Turn 4: Regional Analysis

**Input:**
```
Analyze Asian economies: India, Japan, China
```

**Expected flow:**
1. Agent activates `regional-analysis` skill
2. Fetches data for all three countries
3. Computes per-capita metrics via `calculator_tool`
4. Produces regional summary table

---

## Turn 5: Memory Command

**Input:**
```
memory
```

**Expected output:**
```
  ──────────────────────────────────────────────────
  📝 Memory (Turn 4):
  ## Conversation Summary
  ### Topics Discussed
  - India country profile (GDP $3.55T, 1.44B population)
  - India vs Japan comparison
  - Brazil profile
  - Asian economies regional analysis

  ### Key Facts Retrieved
  - India GDP: $3.55T, Population: 1,438.1M
  - Japan GDP: $4.21T, Population: 124.5M
  - China GDP: $17.79T
  - Brazil: Amazon rainforest, ~215M population

  ### User Preferences
  - Prefers systematic skill-based analysis
  - Interested in Asia and South America

  ### Last Interaction
  User asked for regional analysis of Asian economies; agent compared India, Japan, China.
  ──────────────────────────────────────────────────
```

---

## Memory Architecture Demo

This session demonstrates:

1. **Short-term**: Turn 3 ("same for Brazil") only works because the Agent's `ConversationManager` holds the full history from Turn 1 in memory.
2. **Long-term**: After quitting and restarting (`uv run python -m src.main`), the session summary from `memory_store/session.json` is injected into the system prompt, letting the agent reference prior facts.
3. **Reset**: `uv run python -m src.main --reset` or typing `clear` wipes both memories for a clean start.
