#!/usr/bin/env python3
"""Deterministically compile country wiki pages from country_kb facts.

Usage:
    cd _shared
    python scripts/compile_wiki.py
    python scripts/compile_wiki.py --force
    python scripts/compile_wiki.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

_SHARED_ROOT = Path(__file__).parent.parent
RAW_KB_DIR = _SHARED_ROOT / "data" / "country_kb"
WIKI_DIR = _SHARED_ROOT / "data" / "llm_wiki"
CONCEPTS_DIR = WIKI_DIR / "concepts"

TOPICS = [
    "governance_and_economy",
    "geography_and_environment",
    "culture_and_history",
]

REQUIRED_CONCEPTS = [
    "aging_and_demographics",
    "energy_and_resources",
    "ancient_civilizations",
    "biodiversity_and_rainforests",
    "constitutional_monarchies",
    "global_cultural_exports",
]

GOVERNANCE_ECONOMY_KEYWORDS = {
    "government",
    "governance",
    "democracy",
    "monarchy",
    "republic",
    "parliament",
    "president",
    "prime minister",
    "constitution",
    "constitutional",
    "federal",
    "voting",
    "election",
    "executive",
    "law",
    "gdp",
    "economy",
    "economic",
    "industry",
    "manufacturing",
    "export",
    "imports",
    "trade",
    "producer",
    "oil",
    "gas",
    "petroleum",
    "mining",
    "biofuel",
    "services",
    "opec",
    "high-speed rail",
    "rail",
    "highway",
    "military service",
}

GEOGRAPHY_ENVIRONMENT_KEYWORDS = {
    "geography",
    "continent",
    "island",
    "archipelago",
    "river",
    "sea",
    "ocean",
    "coast",
    "coastline",
    "mountain",
    "desert",
    "rainforest",
    "forest",
    "biodiversity",
    "species",
    "climate",
    "earthquake",
    "volcano",
    "ring of fire",
    "freshwater",
    "reef",
    "coral",
    "arid",
    "peninsula",
    "border",
    "largest",
    "longest river",
    "terrain",
    "located",
    "location",
    "wildlife",
}

CONCEPT_DEFS = {
    "aging_and_demographics": {
        "title": "Aging and Demographics",
        "keywords": [
            "population",
            "aged",
            "aging",
            "literacy",
            "language",
            "bilingual",
            "multicultural",
            "young",
            "oldest population",
        ],
    },
    "energy_and_resources": {
        "title": "Energy and Resources",
        "keywords": ["oil", "gas", "petroleum", "mining", "biofuel", "hydroelectric", "producer"],
    },
    "ancient_civilizations": {
        "title": "Ancient Civilizations",
        "keywords": [
            "ancient",
            "civilization",
            "pyramid",
            "great wall",
            "aztec",
            "maya",
            "roman",
            "empire",
            "hieroglyphics",
        ],
    },
    "biodiversity_and_rainforests": {
        "title": "Biodiversity and Rainforests",
        "keywords": ["biodiversity", "rainforest", "amazon", "species", "reef", "coral", "komodo"],
    },
    "constitutional_monarchies": {
        "title": "Constitutional Monarchies",
        "keywords": ["constitutional monarchy", "monarchy", "emperor", "british monarch", "king"],
    },
    "global_cultural_exports": {
        "title": "Global Cultural Exports",
        "keywords": [
            "k-pop",
            "hollywood",
            "nollywood",
            "cuisine",
            "carnival",
            "cinema",
            "music",
            "festival",
            "unesco",
        ],
    },
}


@dataclass
class CountryDoc:
    slug: str
    name: str
    source_file: Path
    facts: list[str]


def _normalize(text: str) -> str:
    return text.strip().lower()


def _country_name_from_slug(slug: str) -> str:
    return " ".join(token.capitalize() for token in slug.split("_"))


def _load_country_docs() -> list[CountryDoc]:
    docs: list[CountryDoc] = []
    for md_file in sorted(RAW_KB_DIR.glob("*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines()
        title_line = next((line for line in lines if line.startswith("# ")), "")
        name = title_line.replace("# ", "").strip() or _country_name_from_slug(md_file.stem)
        facts = [line[2:].strip() for line in lines if line.startswith("- ")]
        docs.append(CountryDoc(slug=md_file.stem, name=name, source_file=md_file, facts=facts))
    return docs


def _bucket_fact(fact: str) -> str:
    text = _normalize(fact)
    gov_score = sum(1 for kw in GOVERNANCE_ECONOMY_KEYWORDS if kw in text)
    geo_score = sum(1 for kw in GEOGRAPHY_ENVIRONMENT_KEYWORDS if kw in text)

    if gov_score > geo_score and gov_score > 0:
        return "governance_and_economy"
    if geo_score > gov_score and geo_score > 0:
        return "geography_and_environment"

    if any(kw in text for kw in ["gdp", "econom", "government", "parliament", "president", "prime minister"]):
        return "governance_and_economy"
    if any(kw in text for kw in ["river", "ocean", "sea", "rainforest", "biodiversity", "earthquake", "reef"]):
        return "geography_and_environment"
    return "culture_and_history"


def _topic_title(country_name: str, topic_slug: str) -> str:
    names = {
        "governance_and_economy": "Governance and Economy",
        "geography_and_environment": "Geography and Environment",
        "culture_and_history": "Culture and History",
    }
    return f"{country_name} - {names[topic_slug]}"


def _write_country_topic_page(doc: CountryDoc, topic_slug: str, facts: list[str], dry_run: bool) -> str:
    page_dir = WIKI_DIR / doc.slug
    page_path = page_dir / f"{topic_slug}.md"
    title = _topic_title(doc.name, topic_slug)
    provenance = f"_shared/data/country_kb/{doc.source_file.name}"

    lines = [f"# {title}", ""]
    if facts:
        lines.extend(f"- {fact}" for fact in facts)
    else:
        lines.append("- No source facts available for this topic yet.")
    lines.extend(["", f"Provenance: {provenance}", ""])

    if not dry_run:
        page_dir.mkdir(parents=True, exist_ok=True)
        page_path.write_text("\n".join(lines), encoding="utf-8")
    return f"{doc.slug}/{topic_slug}.md"


def _collect_concept_facts(country_docs: list[CountryDoc], concept_slug: str) -> tuple[list[str], list[str]]:
    keywords = CONCEPT_DEFS[concept_slug]["keywords"]
    rows: list[str] = []
    sources: list[str] = []

    for doc in country_docs:
        for fact in doc.facts:
            text = _normalize(fact)
            if any(kw in text for kw in keywords):
                rows.append(f"- {doc.name}: {fact}")
                source = f"_shared/data/country_kb/{doc.source_file.name}"
                if source not in sources:
                    sources.append(source)

    return rows, sources


def _write_concept_page(country_docs: list[CountryDoc], concept_slug: str, dry_run: bool) -> str:
    concept_path = CONCEPTS_DIR / f"{concept_slug}.md"
    title = CONCEPT_DEFS[concept_slug]["title"]
    rows, sources = _collect_concept_facts(country_docs, concept_slug)

    lines = [f"# {title}", ""]
    if rows:
        lines.extend(rows)
    else:
        lines.append("- No source facts available for this concept yet.")

    lines.extend(["", "Provenance:"])
    if sources:
        lines.extend(f"- {source}" for source in sources)
    else:
        lines.append("- _shared/data/country_kb/*.md (no matching facts)")
    lines.append("")

    if not dry_run:
        CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
        concept_path.write_text("\n".join(lines), encoding="utf-8")
    return f"concepts/{concept_slug}.md"


def _topic_keywords(topic_slug: str) -> str:
    if topic_slug == "governance_and_economy":
        return "governance, economy, government, policy"
    if topic_slug == "geography_and_environment":
        return "geography, environment, climate, terrain"
    return "culture, history, society, heritage"


def _concept_keywords(concept_slug: str) -> str:
    return ", ".join(CONCEPT_DEFS[concept_slug]["keywords"])


def _build_index(topic_pages: list[str], concept_pages: list[str]) -> str:
    lines = [
        "# Country Wiki Index",
        "",
        "Compiled pages for country-topic navigation and concept discovery.",
        "Use wiki_read with exact paths or keywords.",
        "",
        "## Discovery",
        "",
        "- [Index](index.md): index, catalog, discover, countries, concepts",
        "",
        "## Entity Topic Pages",
        "",
    ]

    for page in sorted(topic_pages):
        country_slug, topic_file = page.split("/")
        topic_slug = topic_file.replace(".md", "")
        country_name = _country_name_from_slug(country_slug)
        page_name = f"{country_name} {topic_slug.replace('_', ' ')}"
        keywords = ", ".join(
            [
                country_slug,
                country_name.lower(),
                page,
                topic_slug,
                _topic_keywords(topic_slug),
            ]
        )
        lines.append(f"- [{page_name}]({page}): {keywords}")

    lines.extend(["", "## Concept Pages", ""])

    for page in sorted(concept_pages):
        concept_slug = Path(page).stem
        page_name = CONCEPT_DEFS[concept_slug]["title"]
        keywords = ", ".join([concept_slug, page, _concept_keywords(concept_slug)])
        lines.append(f"- [{page_name}]({page}): {keywords}")

    lines.extend(
        [
            "",
            "## wiki_read Examples",
            "",
            "- [Example Exact](japan/governance_and_economy.md): wiki_read(\"japan/governance_and_economy\")",
            "- [Example Keyword](concepts/constitutional_monarchies.md): wiki_read(\"constitutional monarchy\")",
            "- [Example Fuzzy](japan/governance_and_economy.md): wiki_read(\"japn/governance\")",
            "",
        ]
    )

    return "\n".join(lines)


def compile_wiki(force: bool = False, dry_run: bool = False) -> None:
    if not RAW_KB_DIR.exists():
        raise FileNotFoundError(f"Missing source directory: {RAW_KB_DIR}")

    if force and WIKI_DIR.exists() and not dry_run:
        shutil.rmtree(WIKI_DIR)

    country_docs = _load_country_docs()
    if len(country_docs) != 20:
        print(f"Warning: expected 20 source files, found {len(country_docs)}")

    topic_pages: list[str] = []
    for doc in country_docs:
        buckets = {topic: [] for topic in TOPICS}
        for fact in doc.facts:
            buckets[_bucket_fact(fact)].append(fact)

        for topic in TOPICS:
            topic_pages.append(_write_country_topic_page(doc, topic, buckets[topic], dry_run=dry_run))

    concept_pages = [_write_concept_page(country_docs, concept, dry_run=dry_run) for concept in REQUIRED_CONCEPTS]

    index_content = _build_index(topic_pages, concept_pages)
    if not dry_run:
        WIKI_DIR.mkdir(parents=True, exist_ok=True)
        (WIKI_DIR / "index.md").write_text(index_content + "\n", encoding="utf-8")

    print(f"Compiled {len(topic_pages)} topic pages, {len(concept_pages)} concept pages, and index.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically compile llm_wiki from country_kb")
    parser.add_argument("--force", action="store_true", help="Delete and recreate _shared/data/llm_wiki")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = parser.parse_args()

    compile_wiki(force=args.force, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
