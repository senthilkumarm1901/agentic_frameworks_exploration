---
name: regional-analysis
description: Analyze countries by geographic region
---

## When to Use
- Questions about a region (Europe, Asia, etc.)
- Regional totals, averages, or outliers

## Regions
- East Asia & Pacific: Australia, China, Indonesia, Japan, South Korea
- Europe: France, Germany, Italy, Spain, UK, Russia
- North America: Canada, Mexico, United States
- Middle East & Africa: Egypt, Nigeria, Saudi Arabia, South Africa
- South America: Brazil
- South Asia: India

## Steps
1. Identify countries in the region
2. Get requested metric for all via `country_lookup_tool`
3. Compute total, average, min, max via `calculator_tool`
4. If qualitative context is needed, call `country_kb_search_tool` ONCE with a combined query (e.g., "East Asia economic overview"). Do NOT call it multiple times.
5. Present sorted table with aggregates

**IMPORTANT: Only call `country_kb_search_tool` ONCE per turn. Combine your information needs into a single query.**

## Output
- Sorted table (descending by metric)
- Aggregates row
- Top/bottom outlier note
