"""Wiki page reader tool for Pattern 5.

Replaces vector RAG (kb_search) with direct file reads from country_kb.
Supports exact page lookups with fuzzy fallback via index.

Wiki structure:
    _shared/data/llm_wiki/
    └── index.md           # Page catalog with keywords → points to country_kb/
    
    _shared/data/country_kb/
    ├── india.md
    ├── japan.md
    └── ... (20 countries)
"""

import re
from pathlib import Path
from difflib import get_close_matches

# Paths (relative to this file)
_DATA_ROOT = Path(__file__).parent.parent.parent / "data"
_WIKI_ROOT = _DATA_ROOT / "llm_wiki"
_COUNTRY_KB = _DATA_ROOT / "country_kb"


def _load_index() -> dict[str, list[str]]:
    """Load the wiki index mapping keywords to page paths.
    
    Returns:
        Dict mapping keywords (lowercased) to list of relative page paths.
        Example: {"japan": ["../country_kb/japan.md"], 
                  "east asia": ["../country_kb/japan.md", "../country_kb/china.md"]}
    """
    index_path = _WIKI_ROOT / "index.md"
    if not index_path.exists():
        return {}
    
    index_content = index_path.read_text(encoding="utf-8")
    keyword_map: dict[str, list[str]] = {}
    
    # Parse index format:
    # - [page_name](path/to/page.md): keyword1, keyword2, keyword3
    pattern = r'-\s*\[([^\]]+)\]\(([^)]+)\):\s*(.+)'
    
    for match in re.finditer(pattern, index_content):
        page_name, page_path, keywords_str = match.groups()
        keywords = [k.strip().lower() for k in keywords_str.split(',')]
        
        # Map page name and all keywords to the path
        for kw in [page_name.lower()] + keywords:
            if kw:
                if kw not in keyword_map:
                    keyword_map[kw] = []
                if page_path not in keyword_map[kw]:
                    keyword_map[kw].append(page_path)
    
    return keyword_map


def _resolve_path(relative_path: str) -> Path:
    """Resolve a relative path from index to absolute path."""
    # Paths in index are relative to llm_wiki/, e.g., "../country_kb/japan.md"
    return (_WIKI_ROOT / relative_path).resolve()


def _fuzzy_match(query: str, keywords: list[str], cutoff: float = 0.6) -> str | None:
    """Find closest matching keyword using fuzzy matching."""
    query_lower = query.lower()
    
    # First try exact prefix match
    for kw in keywords:
        if kw.startswith(query_lower) or query_lower.startswith(kw):
            return kw
    
    # Then try fuzzy match
    matches = get_close_matches(query_lower, keywords, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def wiki_read(page_or_query: str) -> str:
    """Read a wiki page by name or find the best match.
    
    Lookup strategy:
    1. Exact match on country name (e.g., "japan" → country_kb/japan.md)
    2. Keyword match from index (e.g., "east asia" → japan.md, china.md, south_korea.md)
    3. Fuzzy match on keywords (e.g., "japn" → japan)
    4. Return helpful error with available pages
    
    Args:
        page_or_query: Page name, topic keyword, or search phrase
        
    Returns:
        Page content or error message with suggestions
    """
    query = page_or_query.strip().lower()
    keyword_map = _load_index()
    
    if not keyword_map:
        # Fallback: try direct file read from country_kb
        direct_path = _COUNTRY_KB / f"{query.replace(' ', '_')}.md"
        if direct_path.exists():
            return direct_path.read_text(encoding="utf-8")
        return "Error: Wiki index not found. Check _shared/data/llm_wiki/index.md"
    
    # Strategy 1: Exact match on country name
    direct_path = _COUNTRY_KB / f"{query.replace(' ', '_')}.md"
    if direct_path.exists():
        return direct_path.read_text(encoding="utf-8")
    
    # Strategy 2: Keyword match from index
    if query in keyword_map:
        paths = keyword_map[query]
        results = []
        for rel_path in paths:
            abs_path = _resolve_path(rel_path)
            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                results.append(f"## {abs_path.stem.replace('_', ' ').title()}\n\n{content}")
        
        if results:
            if len(results) == 1:
                return results[0].split("\n\n", 1)[1]  # Remove header for single result
            return f"Found {len(results)} pages matching '{page_or_query}':\n\n" + "\n---\n".join(results)
    
    # Strategy 3: Partial keyword match
    for keyword, paths in keyword_map.items():
        if query in keyword or keyword in query:
            results = []
            for rel_path in paths:
                abs_path = _resolve_path(rel_path)
                if abs_path.exists():
                    content = abs_path.read_text(encoding="utf-8")
                    results.append(f"## {abs_path.stem.replace('_', ' ').title()}\n\n{content}")
            
            if results:
                if len(results) == 1:
                    return f"[Matched '{keyword}']\n\n{results[0].split(chr(10)*2, 1)[1]}"
                return f"Found {len(results)} pages matching '{keyword}':\n\n" + "\n---\n".join(results)
    
    # Strategy 4: Fuzzy match
    best_match = _fuzzy_match(query, list(keyword_map.keys()))
    if best_match:
        paths = keyword_map[best_match]
        abs_path = _resolve_path(paths[0])
        if abs_path.exists():
            content = abs_path.read_text(encoding="utf-8")
            return f"[Fuzzy matched '{best_match}' for '{page_or_query}']\n\n{content}"
    
    # Strategy 5: Return error with suggestions
    available = sorted(set(p.stem for p in _COUNTRY_KB.glob("*.md")))[:10]
    return (
        f"No wiki page found for '{page_or_query}'. "
        f"Available countries: {', '.join(available)}. "
        "Try a country name or region keyword."
    )


def list_wiki_pages() -> str:
    """List all available wiki pages from the index."""
    index_path = _WIKI_ROOT / "index.md"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    
    # Fallback: list country_kb files
    if _COUNTRY_KB.exists():
        countries = sorted(p.stem.replace('_', ' ').title() for p in _COUNTRY_KB.glob("*.md"))
        return f"Available countries ({len(countries)}):\n" + "\n".join(f"- {c}" for c in countries)
    
    return "Wiki not found."


# For direct testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(wiki_read(query))
    else:
        print(list_wiki_pages())
