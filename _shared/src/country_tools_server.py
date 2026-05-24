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
def country_lookup_tool(country: str, metric: str) -> str:
    """Look up a country statistic (GDP, population, or area).

    Args:
        country: Country name (e.g., "United States", "India", "Japan")
        metric: One of "gdp_trillion", "population_million", "area_sq_km"
    """
    return country_lookup(country, metric)


@mcp.tool()
def calculator_tool(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Arithmetic expression (e.g., "25.46 / 3.42", "331.9 * 1000000")
    """
    return calculator(expression)


if __name__ == "__main__":
    mcp.run(transport="stdio")
