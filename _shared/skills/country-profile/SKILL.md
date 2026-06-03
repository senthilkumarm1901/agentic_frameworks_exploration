---
name: country-profile
description: Build a single-country profile with stats and facts
---

## When to Use
- "Tell me about [country]"
- Country overview or fact sheet requests

## Steps
1. Get all 3 metrics via `country_lookup_tool`
2. Compute GDP per capita and density via `calculator_tool`
3. Call `country_kb_search_tool` ONCE with a broad query about the country (e.g., "India culture economy history"). Do NOT make multiple kb_search calls.
4. Format as brief profile

**IMPORTANT: Only call `country_kb_search_tool` ONCE per turn. Combine your information needs into a single query.**

## Output
- Stats table (5 rows)
- 2 notable facts
- 1 sentence summary
