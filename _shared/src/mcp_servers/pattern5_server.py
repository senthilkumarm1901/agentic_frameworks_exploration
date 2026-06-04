"""MCP Server for Pattern 5: Agent with LLM Wiki (No RAG).

Replaces vector RAG with compiled LLM Wiki pages.

Run standalone:
    python _shared/src/mcp_servers/pattern5_server.py

Tools:
    - country_lookup_tool: Look up country statistics (GDP, population, area)
    - calculator_tool: Evaluate mathematical expressions
    - wiki_read_tool: Read wiki pages (replaces kb_search)
"""

import logging
import sys
from pathlib import Path

# Suppress verbose MCP server logging
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("mcp.server").setLevel(logging.WARNING)

# Add parent directory to path for tools package access
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from tools.country_lookup import country_lookup
from tools.calculator import calculator
from tools.wiki_read import wiki_read, list_wiki_pages

mcp = FastMCP("country-tools-pattern5")


@mcp.tool()
def country_lookup_tool(
    country: str | None = None,
    metric: str | None = None,
    gdp_trillion: float | None = None,
    population_million: float | None = None,
    area_sq_km: float | None = None,
) -> str:
    """Look up a country statistic (GDP, population, or area).

    Use this tool for NUMERIC data about countries:
    - GDP (in trillions USD)
    - Population (in millions)
    - Area (in square kilometers)

    Args:
        country: Country name (e.g., "United States", "India", "Japan")
        metric: One of "gdp_trillion", "population_million", "area_sq_km"
    """
    if not country or not metric:
        return (
            "Error: country_lookup_tool requires exactly two arguments: "
            "country (string) and metric (one of gdp_trillion, population_million, area_sq_km). "
            "Do not pass pre-computed values like gdp_trillion/population_million as inputs."
        )
    return country_lookup(country, metric)


@mcp.tool()
def calculator_tool(expression: str | None = None) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Arithmetic expression (e.g., "25.46 / 3.42", "331.9 * 1000000")
    """
    if not expression:
        return "Error: calculator_tool requires one argument: expression (string)."
    return calculator(expression)


@mcp.tool()
def wiki_read_tool(page_or_query: str) -> str:
    """Read information from the country knowledge wiki.

    The wiki contains compiled knowledge about 20 countries, organized as:
    - Entity pages: Individual country profiles (japan, india, brazil, etc.)
    - Concept pages: Cross-cutting topics (demographics, trade_and_economy, geography)
    - Comparisons: Multi-country analysis and rankings

    Use this tool when you need qualitative information about countries,
    such as cultural facts, historical context, political systems,
    geographic features, or notable achievements.

    For NUMERIC data (GDP, population, area), use country_lookup_tool instead.

    Lookup supports:
    - Exact page name: "japan", "demographics"
    - Keywords: "bullet train", "aging population"
    - Topics: "trade", "geography", "comparisons"

    Args:
        page_or_query: Page name, topic keyword, or search phrase
        
    Returns:
        Wiki page content or suggestions if page not found
    """
    return wiki_read(page_or_query)


@mcp.tool()
def wiki_index_tool() -> str:
    """List all available wiki pages and their topics.
    
    Use this to discover what information is available in the wiki
    before reading specific pages.
    
    Returns:
        Index of all wiki pages with keywords
    """
    return list_wiki_pages()


if __name__ == "__main__":
    mcp.run(transport="stdio")
