"""Deterministic tool stubs for fair cross-framework comparison.
All frameworks use these same stubs so tool responses are identical."""


def get_weather(city: str) -> dict:
    data = {
        "Tokyo": {"city": "Tokyo", "temp_c": 22, "condition": "partly cloudy", "humidity": 65},
        "London": {"city": "London", "temp_c": 14, "condition": "rainy", "humidity": 80},
        "New York": {"city": "New York", "temp_c": 28, "condition": "sunny", "humidity": 45},
    }
    return data.get(city, {"city": city, "temp_c": 20, "condition": "unknown", "humidity": 50})


def lookup_order(order_id: str) -> dict:
    return {
        "order_id": order_id,
        "status": "in_transit",
        "items": ["Wireless Headphones", "USB-C Cable"],
        "total": 89.99,
        "placed_date": "2026-04-10",
        "customer_name": "Jane Doe",
    }


def check_tracking(order_id: str) -> dict:
    return {
        "order_id": order_id,
        "carrier": "FastShip",
        "tracking_number": "FS-98765",
        "last_update": "2026-04-17",
        "location": "Regional Distribution Center",
        "status": "stuck_in_transit",
        "days_since_update": 5,
    }


def issue_refund(order_id: str, reason: str) -> dict:
    return {"order_id": order_id, "refund_status": "approved", "amount": 89.99, "reason": reason}


def escalate(order_id: str, priority: str) -> dict:
    return {"order_id": order_id, "ticket_id": "ESC-4421", "priority": priority, "status": "escalated"}


def search_knowledge_base(query: str) -> str:
    return (
        "Refund policy: Full refund within 30 days of purchase. "
        "For orders stuck in transit for more than 3 days, customers are eligible "
        "for a full refund or re-shipment at no additional cost."
    )


def run_python_code(code: str) -> dict:
    """Simulated code execution stub for coding agent pattern."""
    return {"stdout": "", "stderr": "", "exit_code": 0, "executed": True}


def web_search(query: str) -> list[dict]:
    return [
        {"title": f"Result 1 for: {query}", "snippet": "WebAssembly (Wasm) is a binary instruction format for a stack-based virtual machine.", "url": "https://example.com/1"},
        {"title": f"Result 2 for: {query}", "snippet": "Server-side Wasm enables near-native performance for compute-intensive workloads.", "url": "https://example.com/2"},
        {"title": f"Result 3 for: {query}", "snippet": "WASI provides a system interface for running Wasm outside the browser.", "url": "https://example.com/3"},
    ]


TOOL_STUBS = {
    "get_weather": get_weather,
    "lookup_order": lookup_order,
    "check_tracking": check_tracking,
    "issue_refund": issue_refund,
    "escalate": escalate,
    "search_knowledge_base": search_knowledge_base,
    "run_python_code": run_python_code,
    "web_search": web_search,
}
