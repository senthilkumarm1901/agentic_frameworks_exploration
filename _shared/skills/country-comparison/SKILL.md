---
name: country-comparison
description: Compare two or more countries across metrics
---

## When to Use
- User asks to compare countries
- Questions about which country is larger/richer/etc.

## Steps
1. Get GDP, population, area for each country via `country_lookup_tool`
2. Compute ratios (GDP per capita, density) via `calculator_tool`
3. Call `country_kb_search_tool` ONCE with a combined query (e.g., "Japan Germany comparison"). Do NOT call it multiple times.
4. Present comparison table + key insight

**IMPORTANT: Only call `country_kb_search_tool` ONCE per turn. Combine your information needs into a single query.**

## Output
- Markdown table (countries as columns)
- 1-2 sentence takeaway with qualitative context
