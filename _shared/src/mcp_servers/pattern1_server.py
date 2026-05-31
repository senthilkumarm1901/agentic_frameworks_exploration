"""MCP Server for Pattern 1: Basic agent with multiple tools.

Exposes country_lookup and calculator tools over stdio.

Run standalone:
    python _shared/src/mcp_servers/pattern1_server.py

Tools:
    - country_lookup_tool: Look up country statistics (GDP, population, area)
    - calculator_tool: Evaluate mathematical expressions
"""

import sys
from pathlib import Path

# Add parent directory to path for tools package access
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from tools.country_lookup import country_lookup
from tools.calculator import calculator

mcp = FastMCP("country-tools-pattern1")


@mcp.tool()
def country_lookup_tool(
    country: str | None = None,
    metric: str | None = None,
    gdp_trillion: float | None = None,
    population_million: float | None = None,
    area_sq_km: float | None = None,
) -> str:
    """Look up a country statistic (GDP, population, or area).

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


if __name__ == "__main__":
    mcp.run(transport="stdio")
