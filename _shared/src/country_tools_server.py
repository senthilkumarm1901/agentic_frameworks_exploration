"""MCP Server exposing country_lookup and calculator tools over stdio.

Run standalone:
    python _shared/src/country_tools_server.py

This file lives at _shared/src/ so that Python's sys.path[0] gives us
access to the 'tools' package without conflicting with the installed 'mcp' lib.
"""

from mcp.server.fastmcp import FastMCP
from tools.country_lookup import country_lookup
from tools.calculator import calculator

mcp = FastMCP("country-tools")


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
