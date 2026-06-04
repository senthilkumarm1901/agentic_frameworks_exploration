#!/usr/bin/env python
"""Compile LLM Wiki from raw country knowledge base.

This script processes the raw country markdown files and generates
a structured wiki with entity pages, concept pages, and an index.

Usage:
    cd _shared
    uv run python scripts/compile_wiki.py           # Compile all pages
    uv run python scripts/compile_wiki.py --force   # Overwrite existing
    uv run python scripts/compile_wiki.py --dry-run # Preview without writing

Wiki structure created:
    data/llm_wiki/
    ├── index.md              # Page catalog with keywords
    ├── entities/             # Individual country pages
    │   ├── india.md
    │   ├── japan.md
    │   └── ...
    ├── concepts/             # Cross-cutting topic pages
    │   ├── demographics.md
    │   ├── trade_and_economy.md
    │   └── geography.md
    └── comparisons.md        # Rankings and comparisons
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from _shared directory
_SHARED_ROOT = Path(__file__).parent.parent
load_dotenv(_SHARED_ROOT / ".env")

# Paths
RAW_KB_DIR = _SHARED_ROOT / "data" / "country_kb"
COUNTRIES_JSON = _SHARED_ROOT / "data" / "countries.json"
WIKI_DIR = _SHARED_ROOT / "data" / "llm_wiki"
ENTITIES_DIR = WIKI_DIR / "entities"
CONCEPTS_DIR = WIKI_DIR / "concepts"


def get_llm():
    """Create ChatOllama instance from environment."""
    from langchain_ollama import ChatOllama
    
    model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return ChatOllama(model=model, base_url=base_url)


def load_raw_sources() -> tuple[dict[str, str], dict]:
    """Load raw country markdown files and JSON data.
    
    Returns:
        Tuple of (markdown_dict, json_data)
        - markdown_dict: {country_name: markdown_content}
        - json_data: Full countries.json content
    """
    markdown_data = {}
    
    if RAW_KB_DIR.exists():
        for md_file in RAW_KB_DIR.glob("*.md"):
            country_name = md_file.stem.replace("_", " ").title()
            markdown_data[country_name] = md_file.read_text(encoding="utf-8")
    
    json_data = {}
    if COUNTRIES_JSON.exists():
        with open(COUNTRIES_JSON) as f:
            json_data = json.load(f)
    
    return markdown_data, json_data


def compile_entity_page(country_name: str, md_content: str, json_data: dict, llm) -> str:
    """Compile a single country entity page.
    
    Args:
        country_name: Display name (e.g., "Japan")
        md_content: Raw markdown bullet points
        json_data: Full countries.json for quantitative data (keyed by country slug)
        
    Returns:
        Compiled wiki page content
    """
    # Find country in JSON data (keys are like "japan", "united_states")
    country_key = country_name.lower().replace(" ", "_")
    country_stats = json_data.get(country_key, {})
    
    stats_block = ""
    if country_stats:
        stats_block = f"""
## Quick Stats
- **GDP**: ${country_stats.get('gdp_trillion', 'N/A')} trillion
- **Population**: {country_stats.get('population_million', 'N/A')} million
- **Area**: {country_stats.get('area_sq_km', 'N/A'):,} km²
- **Region**: {country_stats.get('region', 'N/A')}
- **Capital**: {country_stats.get('capital', 'N/A')}
"""
    
    prompt = f"""You are compiling a wiki page for {country_name}.

Raw facts (bullet points):
{md_content}

{f"Statistics:{stats_block}" if stats_block else ""}

Create a well-structured wiki page with:
1. A brief 2-3 sentence introduction
2. Key sections organizing the facts (Geography, Culture, Economy, etc.)
3. Each section should have 2-4 bullet points maximum

Format as clean markdown. Keep it concise (under 400 words).
Do not add information not in the source material.
Start with: # {country_name}
"""
    
    response = llm.invoke(prompt)
    return response.content


def compile_concept_page(concept: str, markdown_data: dict[str, str], llm) -> str:
    """Compile a cross-cutting concept page.
    
    Args:
        concept: Concept name (e.g., "demographics")
        markdown_data: All country markdown content
        
    Returns:
        Compiled concept page
    """
    # Combine relevant facts from all countries
    all_facts = []
    for country, content in markdown_data.items():
        all_facts.append(f"### {country}\n{content}")
    
    combined = "\n\n".join(all_facts)
    
    concept_prompts = {
        "demographics": "population, aging, urbanization, literacy, education, migration",
        "trade_and_economy": "GDP, exports, imports, industries, trade partners, economic features",
        "geography": "location, area, terrain, climate, natural features, borders",
    }
    
    keywords = concept_prompts.get(concept, concept)
    
    prompt = f"""You are compiling a wiki page about "{concept}" across 20 countries.

All country facts:
{combined[:8000]}  # Truncate if too long

Extract and organize ONLY facts related to: {keywords}

Create a wiki page with:
1. Brief introduction (2-3 sentences)
2. Group countries by interesting patterns or regions
3. Highlight notable contrasts and similarities

Format as clean markdown. Keep it concise (under 500 words).
Start with: # {concept.replace('_', ' ').title()}
"""
    
    response = llm.invoke(prompt)
    return response.content


def compile_comparisons_page(markdown_data: dict[str, str], json_data: dict, llm) -> str:
    """Compile the comparisons page with rankings and analysis."""
    
    # Get sorted lists from JSON
    countries = json_data.get("countries", [])
    
    by_gdp = sorted(countries, key=lambda x: x.get("gdp_trillion", 0), reverse=True)
    by_pop = sorted(countries, key=lambda x: x.get("population_million", 0), reverse=True)
    by_area = sorted(countries, key=lambda x: x.get("area_sq_km", 0), reverse=True)
    
    rankings = f"""
GDP Rankings (trillion USD):
{chr(10).join(f"{i+1}. {c['name']}: ${c['gdp_trillion']}" for i, c in enumerate(by_gdp[:10]))}

Population Rankings (million):
{chr(10).join(f"{i+1}. {c['name']}: {c['population_million']}" for i, c in enumerate(by_pop[:10]))}

Area Rankings (km²):
{chr(10).join(f"{i+1}. {c['name']}: {c['area_sq_km']:,}" for i, c in enumerate(by_area[:10]))}
"""
    
    prompt = f"""You are compiling a comparisons wiki page.

Rankings:
{rankings}

Create a wiki page with:
1. Brief introduction about the 20-country dataset
2. Top 10 tables for GDP, Population, Area
3. Interesting observations (density, GDP per capita, regional patterns)

Format as clean markdown. Keep it concise (under 400 words).
Start with: # Country Comparisons
"""
    
    response = llm.invoke(prompt)
    return response.content


def generate_index(entity_pages: list[str], concept_pages: list[str]) -> str:
    """Generate the wiki index with keywords.
    
    Index format (parsed by wiki_read):
    - [page_name](path/to/page.md): keyword1, keyword2, keyword3
    """
    lines = [
        "# LLM Wiki Index",
        "",
        "This index maps page names and keywords to wiki pages.",
        "Use `wiki_read('keyword')` to read a page.",
        "",
        "## Entity Pages (Countries)",
        ""
    ]
    
    for page in sorted(entity_pages):
        name = page.replace("_", " ").title()
        # Add common keywords for each country
        keywords = f"{page}, {name.lower()}"
        lines.append(f"- [{name}](entities/{page}.md): {keywords}")
    
    lines.extend([
        "",
        "## Concept Pages",
        ""
    ])
    
    concept_keywords = {
        "demographics": "demographics, population, aging, literacy, urbanization, education",
        "trade_and_economy": "economy, trade, gdp, exports, imports, industries, economic",
        "geography": "geography, location, area, terrain, climate, borders, landscape",
    }
    
    for page in sorted(concept_pages):
        name = page.replace("_", " ").title()
        keywords = concept_keywords.get(page, page)
        lines.append(f"- [{name}](concepts/{page}.md): {keywords}")
    
    lines.extend([
        "",
        "## Special Pages",
        "",
        "- [Comparisons](comparisons.md): comparisons, rankings, top 10, compare, versus, vs",
    ])
    
    return "\n".join(lines)


def compile_wiki(force: bool = False, dry_run: bool = False):
    """Main compilation function."""
    print("📚 LLM Wiki Compiler")
    print("=" * 50)
    
    # Check if wiki already exists
    if WIKI_DIR.exists() and not force:
        print(f"\n⚠️  Wiki already exists at {WIKI_DIR}")
        print("   Use --force to overwrite or --dry-run to preview.")
        return
    
    # Load raw sources
    print("\n📖 Loading raw sources...")
    markdown_data, json_data = load_raw_sources()
    print(f"   Found {len(markdown_data)} country markdown files")
    print(f"   Found {len(json_data)} countries in JSON")
    
    if not markdown_data:
        print("❌ No raw markdown files found in data/country_kb/")
        return
    
    if dry_run:
        print("\n🔍 Dry run - would create:")
        print(f"   - {len(markdown_data)} entity pages")
        print("   - 3 concept pages (demographics, trade_and_economy, geography)")
        print("   - 1 comparisons page")
        print("   - 1 index page")
        return
    
    # Create directories
    print("\n📁 Creating wiki structure...")
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    ENTITIES_DIR.mkdir(exist_ok=True)
    CONCEPTS_DIR.mkdir(exist_ok=True)
    
    # Initialize LLM
    print("\n🤖 Initializing LLM...")
    llm = get_llm()
    
    # Compile entity pages
    entity_pages = []
    print(f"\n📝 Compiling {len(markdown_data)} entity pages...")
    for i, (country_name, md_content) in enumerate(markdown_data.items(), 1):
        page_name = country_name.lower().replace(" ", "_")
        print(f"   [{i}/{len(markdown_data)}] {country_name}...", end=" ", flush=True)
        
        try:
            content = compile_entity_page(country_name, md_content, json_data, llm)
            output_path = ENTITIES_DIR / f"{page_name}.md"
            output_path.write_text(content, encoding="utf-8")
            entity_pages.append(page_name)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Compile concept pages
    concepts = ["demographics", "trade_and_economy", "geography"]
    concept_pages = []
    print(f"\n📝 Compiling {len(concepts)} concept pages...")
    for concept in concepts:
        print(f"   {concept}...", end=" ", flush=True)
        
        try:
            content = compile_concept_page(concept, markdown_data, llm)
            output_path = CONCEPTS_DIR / f"{concept}.md"
            output_path.write_text(content, encoding="utf-8")
            concept_pages.append(concept)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Compile comparisons
    print("\n📝 Compiling comparisons page...", end=" ", flush=True)
    try:
        content = compile_comparisons_page(markdown_data, json_data, llm)
        (WIKI_DIR / "comparisons.md").write_text(content, encoding="utf-8")
        print("✓")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Generate index
    print("\n📝 Generating index...", end=" ", flush=True)
    index_content = generate_index(entity_pages, concept_pages)
    (WIKI_DIR / "index.md").write_text(index_content, encoding="utf-8")
    print("✓")
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ Wiki compilation complete!")
    print(f"   📂 Location: {WIKI_DIR}")
    print(f"   📄 Entity pages: {len(entity_pages)}")
    print(f"   📄 Concept pages: {len(concept_pages)}")
    print("   📄 Special pages: comparisons, index")


def main():
    parser = argparse.ArgumentParser(description="Compile LLM Wiki from raw sources")
    parser.add_argument("--force", action="store_true", help="Overwrite existing wiki")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    
    compile_wiki(force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
