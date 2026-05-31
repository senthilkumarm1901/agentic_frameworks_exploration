"""MCP Server for Pattern 2: Agent with RAG tool.

Extends Pattern 1 with semantic search over country knowledge base.

Run standalone:
    python _shared/src/mcp_servers/pattern2_server.py

Tools:
    - country_lookup_tool: Look up country statistics (GDP, population, area)
    - calculator_tool: Evaluate mathematical expressions
    - country_kb_search_tool: Search country knowledge base for qualitative facts
"""

import sys
from pathlib import Path

# Add parent directory to path for tools package access
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from tools.country_lookup import country_lookup
from tools.calculator import calculator
from tools.country_kb_search import country_kb_search

mcp = FastMCP("country-tools-pattern2")


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
def country_kb_search_tool(query: str, top_k: int = 3) -> str:
    """Search the country knowledge base for qualitative facts.

    Use this tool when you need non-numeric information about countries,
    such as cultural facts, historical context, political systems,
    geographic features, or notable achievements.

    Do NOT use this for numeric data like GDP, population, or area -
    use country_lookup_tool for those.

    Args:
        query: Natural language question about countries
        top_k: Maximum number of results to return (default: 3)
    """
    return country_kb_search(query, top_k)


if __name__ == "__main__":
    mcp.run(transport="stdio")
