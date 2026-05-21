//! Rust MCP tool server — JSON-RPC 2.0 over stdio.
//!
//! Implements `initialize`, `tools/list`, and `tools/call` with the same
//! deterministic tool stubs used by the Python MCP server so that all
//! frameworks produce identical tool responses.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio::io::{self, AsyncBufReadExt, AsyncWriteExt, BufReader};

// ---- JSON-RPC types ----

#[derive(Deserialize)]
struct JsonRpcRequest {
    #[allow(dead_code)]
    jsonrpc: String,
    id: Option<Value>,
    method: String,
    params: Option<Value>,
}

#[derive(Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Value>,
}

// ---- MCP method handlers ----

fn handle_initialize(_params: &Value) -> Value {
    json!({
        "protocolVersion": "2024-11-05",
        "capabilities": { "tools": {} },
        "serverInfo": { "name": "rig-mcp-tools", "version": "0.1.0" }
    })
}

fn handle_tools_list() -> Value {
    json!({
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "inputSchema": {
                    "type": "object",
                    "properties": { "city": { "type": "string" } },
                    "required": ["city"]
                }
            },
            {
                "name": "lookup_order",
                "description": "Look up an order by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": { "order_id": { "type": "string" } },
                    "required": ["order_id"]
                }
            },
            {
                "name": "check_tracking",
                "description": "Check shipping tracking for an order",
                "inputSchema": {
                    "type": "object",
                    "properties": { "order_id": { "type": "string" } },
                    "required": ["order_id"]
                }
            },
            {
                "name": "issue_refund",
                "description": "Issue a refund for an order",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": { "type": "string" },
                        "reason": { "type": "string" }
                    },
                    "required": ["order_id", "reason"]
                }
            },
            {
                "name": "escalate",
                "description": "Escalate an order to support",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "order_id": { "type": "string" },
                        "priority": { "type": "string" }
                    },
                    "required": ["order_id", "priority"]
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Search the support knowledge base",
                "inputSchema": {
                    "type": "object",
                    "properties": { "query": { "type": "string" } },
                    "required": ["query"]
                }
            },
            {
                "name": "run_python_code",
                "description": "Execute Python code in a sandboxed environment",
                "inputSchema": {
                    "type": "object",
                    "properties": { "code": { "type": "string" } },
                    "required": ["code"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information",
                "inputSchema": {
                    "type": "object",
                    "properties": { "query": { "type": "string" } },
                    "required": ["query"]
                }
            }
        ]
    })
}

fn handle_tools_call(params: &Value) -> Value {
    let name = params["name"].as_str().unwrap_or("");
    let args = &params["arguments"];

    let result = match name {
        "get_weather" => {
            let city = args["city"].as_str().unwrap_or("Unknown");
            match city {
                "Tokyo" => json!({
                    "city": "Tokyo", "temp_c": 22,
                    "condition": "partly cloudy", "humidity": 65
                }),
                "London" => json!({
                    "city": "London", "temp_c": 14,
                    "condition": "rainy", "humidity": 80
                }),
                "New York" => json!({
                    "city": "New York", "temp_c": 28,
                    "condition": "sunny", "humidity": 45
                }),
                _ => json!({
                    "city": city, "temp_c": 20,
                    "condition": "unknown", "humidity": 50
                }),
            }
        }
        "lookup_order" => {
            let order_id = args["order_id"].as_str().unwrap_or("");
            json!({
                "order_id": order_id,
                "status": "in_transit",
                "items": ["Wireless Headphones", "USB-C Cable"],
                "total": 89.99,
                "placed_date": "2026-04-10",
                "customer_name": "Jane Doe"
            })
        }
        "check_tracking" => {
            let order_id = args["order_id"].as_str().unwrap_or("");
            json!({
                "order_id": order_id,
                "carrier": "FastShip",
                "tracking_number": "FS-98765",
                "last_update": "2026-04-17",
                "location": "Regional Distribution Center",
                "status": "stuck_in_transit",
                "days_since_update": 5
            })
        }
        "issue_refund" => {
            let order_id = args["order_id"].as_str().unwrap_or("");
            let reason = args["reason"].as_str().unwrap_or("");
            json!({
                "order_id": order_id,
                "refund_status": "approved",
                "amount": 89.99,
                "reason": reason
            })
        }
        "escalate" => {
            let order_id = args["order_id"].as_str().unwrap_or("");
            let priority = args["priority"].as_str().unwrap_or("");
            json!({
                "order_id": order_id,
                "ticket_id": "ESC-4421",
                "priority": priority,
                "status": "escalated"
            })
        }
        "search_knowledge_base" => {
            json!("Refund policy: Full refund within 30 days of purchase. For orders stuck in transit for more than 3 days, customers are eligible for a full refund or re-shipment at no additional cost.")
        }
        "run_python_code" => {
            json!({"stdout": "", "stderr": "", "exit_code": 0, "executed": true})
        }
        "web_search" => {
            let query = args["query"].as_str().unwrap_or("");
            json!([
                {
                    "title": format!("Result 1 for: {query}"),
                    "snippet": "WebAssembly (Wasm) is a binary instruction format for a stack-based virtual machine.",
                    "url": "https://example.com/1"
                },
                {
                    "title": format!("Result 2 for: {query}"),
                    "snippet": "Server-side Wasm enables near-native performance for compute-intensive workloads.",
                    "url": "https://example.com/2"
                },
                {
                    "title": format!("Result 3 for: {query}"),
                    "snippet": "WASI provides a system interface for running Wasm outside the browser.",
                    "url": "https://example.com/3"
                }
            ])
        }
        _ => json!({"error": format!("Unknown tool: {name}")}),
    };

    // Wrap in MCP content envelope
    json!({
        "content": [{
            "type": "text",
            "text": serde_json::to_string(&result).unwrap()
        }]
    })
}

// ---- Main loop ----

#[tokio::main]
async fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout();
    let reader = BufReader::new(stdin);
    let mut lines = reader.lines();

    while let Ok(Some(line)) = lines.next_line().await {
        if line.trim().is_empty() {
            continue;
        }

        let request: JsonRpcRequest = match serde_json::from_str(&line) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("Parse error: {e}");
                continue;
            }
        };

        // Notifications (no id) don't get a response
        if request.id.is_none() {
            continue;
        }

        let params = request.params.unwrap_or(json!({}));
        let result = match request.method.as_str() {
            "initialize" => handle_initialize(&params),
            "tools/list" => handle_tools_list(),
            "tools/call" => handle_tools_call(&params),
            _ => json!({"error": format!("Unknown method: {}", request.method)}),
        };

        let response = JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            id: request.id.unwrap_or(json!(null)),
            result: Some(result),
            error: None,
        };

        let msg = serde_json::to_string(&response).unwrap();
        stdout.write_all(msg.as_bytes()).await.unwrap();
        stdout.write_all(b"\n").await.unwrap();
        stdout.flush().await.unwrap();
    }
}
