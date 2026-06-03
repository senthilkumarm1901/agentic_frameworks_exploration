---
name: report-formatting
description: Format analysis as a clean markdown report
---

## When to Use
- User asks for "formatted report" or "professional output"
- After completing analysis, needs clean presentation

## Steps
1. Review data already gathered (or gather if missing)
2. Apply report structure
3. Ensure all numbers come from tool calls

**IMPORTANT: If you need to call `country_kb_search_tool`, call it only ONCE per turn with a single combined query. Do NOT make multiple kb_search calls.**

## Output Template
```
# [Title]
> Generated from country dataset (20 countries)

## Summary
[1-2 sentences]

## Data
[Table]

## Sources
- countries.json (World Bank)
- Country knowledge base
```
