"""MCP server exposing deterministic tool stubs over stdio."""
from mcp.server.fastmcp import FastMCP
from shared import tool_stubs

mcp = FastMCP("tool-stubs")


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return tool_stubs.get_weather(city)


@mcp.tool()
def lookup_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return tool_stubs.lookup_order(order_id)


@mcp.tool()
def check_tracking(order_id: str) -> dict:
    """Check shipping tracking for an order."""
    return tool_stubs.check_tracking(order_id)


@mcp.tool()
def issue_refund(order_id: str, reason: str) -> dict:
    """Issue a refund for an order."""
    return tool_stubs.issue_refund(order_id, reason)


@mcp.tool()
def escalate(order_id: str, priority: str) -> dict:
    """Escalate an order to support."""
    return tool_stubs.escalate(order_id, priority)


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base."""
    return tool_stubs.search_knowledge_base(query)


@mcp.tool()
def run_python_code(code: str) -> dict:
    """Execute Python code in a sandboxed environment."""
    return tool_stubs.run_python_code(code)


@mcp.tool()
def web_search(query: str) -> list[dict]:
    """Search the web for information."""
    return tool_stubs.web_search(query)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
