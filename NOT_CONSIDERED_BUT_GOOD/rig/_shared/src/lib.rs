use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::env;
use std::time::Instant;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};

// ---- Config ----

pub struct OllamaConfig {
    pub model: String,
    pub base_url: String,
}

impl OllamaConfig {
    pub fn from_env() -> Self {
        Self {
            model: env::var("OLLAMA_MODEL")
                .unwrap_or_else(|_| "qwen3.5:35b-a3b-coding-nvfp4".to_string()),
            base_url: env::var("OLLAMA_BASE_URL")
                .unwrap_or_else(|_| "http://localhost:11434".to_string()),
        }
    }
}

// ---- Metrics ----

#[derive(Serialize, Clone)]
pub struct LlmCall {
    pub duration_ms: f64,
    pub prompt_tokens: i64,
    pub completion_tokens: i64,
}

#[derive(Serialize)]
pub struct MetricsOutput {
    pub answer: String,
    pub llm_calls: Vec<LlmCall>,
    pub total_duration_ms: f64,
    pub framework: String,
    pub pattern: String,
}

pub struct MetricsCollector {
    pub framework: String,
    pub pattern: String,
    pub answer: String,
    pub llm_calls: Vec<LlmCall>,
    pub total_duration_ms: f64,
    start: Option<Instant>,
}

impl MetricsCollector {
    pub fn new(framework: &str, pattern: &str) -> Self {
        Self {
            framework: framework.to_string(),
            pattern: pattern.to_string(),
            answer: String::new(),
            llm_calls: Vec::new(),
            total_duration_ms: 0.0,
            start: None,
        }
    }

    pub fn start_timer(&mut self) {
        self.start = Some(Instant::now());
    }

    pub fn stop_timer(&mut self) {
        if let Some(start) = self.start {
            self.total_duration_ms = start.elapsed().as_secs_f64() * 1000.0;
        }
    }

    pub fn record_llm_call(
        &mut self,
        duration_ms: f64,
        prompt_tokens: i64,
        completion_tokens: i64,
    ) {
        self.llm_calls.push(LlmCall {
            duration_ms,
            prompt_tokens,
            completion_tokens,
        });
    }

    pub fn emit(&self) {
        let output = MetricsOutput {
            answer: self.answer.clone(),
            llm_calls: self.llm_calls.clone(),
            total_duration_ms: self.total_duration_ms,
            framework: self.framework.clone(),
            pattern: self.pattern.clone(),
        };
        let json = serde_json::to_string_pretty(&output).unwrap();
        println!("{json}");
    }
}

// ---- Tasks ----

#[derive(Deserialize, Serialize, Clone)]
pub struct Task {
    pub description: String,
    pub input: serde_json::Value,
    pub tools_required: Vec<String>,
    pub grading: String,
}

pub fn get_task(name: &str) -> Task {
    match name {
        "augmented_llm" => Task {
            description: "Q&A with tool use: weather query requiring tool call + recommendation"
                .into(),
            input: serde_json::json!({
                "query": "What is the current weather in Tokyo and what should I wear?"
            }),
            tools_required: vec!["get_weather".into()],
            grading: "Must call get_weather tool AND produce clothing recommendation".into(),
        },
        "prompt_chaining" => Task {
            description:
                "Summarize an English paragraph to 2 sentences, then translate to Spanish".into(),
            input: serde_json::json!({
                "text": "WebAssembly, often abbreviated as Wasm, is a binary instruction format designed for a stack-based virtual machine. It serves as a portable compilation target for programming languages, enabling deployment on the web for client and server applications. Wasm is designed to maintain the security properties of the web while being fast, compact, and platform-independent. Major browsers including Chrome, Firefox, Safari, and Edge all support WebAssembly natively. Beyond the browser, projects like WASI are extending WebAssembly to server-side and edge computing environments, opening new possibilities for portable, sandboxed execution of code across diverse platforms.",
                "target_language": "Spanish"
            }),
            tools_required: vec![],
            grading: "Output must contain a 2-sentence English summary AND a Spanish translation"
                .into(),
        },
        "routing" => Task {
            description: "Classify a support ticket and route to specialized handler".into(),
            input: serde_json::json!({
                "message": "I was charged twice for my subscription last month"
            }),
            tools_required: vec![],
            grading: "Must classify as 'billing' and produce a billing-specific response".into(),
        },
        "parallelization" => Task {
            description: "Multi-aspect code review: correctness, performance, and style".into(),
            input: serde_json::json!({
                "code": "def find_duplicates(lst):\n    duplicates = []\n    for i in range(len(lst)):\n        for j in range(len(lst)):\n            if i != j and lst[i] == lst[j]:\n                if lst[i] not in duplicates:\n                    duplicates.append(lst[i])\n    return duplicates\n"
            }),
            tools_required: vec![],
            grading:
                "Must identify: O(n^2) inefficiency, duplicate detection bug, and style issues"
                    .into(),
        },
        "orchestrator_workers" => Task {
            description: "Research report on a topic with dynamic subtopic delegation".into(),
            input: serde_json::json!({
                "topic": "Impact of WebAssembly on server-side computing"
            }),
            tools_required: vec!["web_search".into()],
            grading:
                "Must cover >=3 subtopics, have intro + conclusion, cite specific technologies"
                    .into(),
        },
        "evaluator_optimizer" => Task {
            description: "Generate a haiku about autumn, iteratively refine until valid 5-7-5"
                .into(),
            input: serde_json::json!({"theme": "autumn", "max_iterations": 5}),
            tools_required: vec![],
            grading: "Valid 5-7-5 syllable structure + theme relevance. Fewer iterations = better"
                .into(),
        },
        "customer_support" => Task {
            description: "Order troubleshooting with tool access".into(),
            input: serde_json::json!({
                "message": "My order #12345 hasn't arrived and tracking shows stuck in transit for 5 days"
            }),
            tools_required: vec![
                "lookup_order".into(),
                "check_tracking".into(),
                "issue_refund".into(),
                "escalate".into(),
                "search_knowledge_base".into(),
            ],
            grading:
                "Must call lookup_order + check_tracking, offer resolution, not hallucinate order details"
                    .into(),
        },
        "coding_agent" => Task {
            description: "Fix a buggy Python function to pass the provided test".into(),
            input: serde_json::json!({
                "buggy_code": "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    return result\n",
                "test_code": "def test_merge_sorted():\n    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]\n    assert merge_sorted([1, 2], [3, 4, 5]) == [1, 2, 3, 4, 5]\n    assert merge_sorted([], [1, 2]) == [1, 2]\n    assert merge_sorted([1], []) == [1]\n",
                "expected_fix": "Append remaining elements from both lists after the while loop"
            }),
            tools_required: vec!["run_python_code".into()],
            grading: "Fix must pass all tests. Fewer lines changed = better".into(),
        },
        _ => panic!("Unknown task: {name}"),
    }
}

// ---- MCP Client ----

/// A simple MCP client that spawns the `rig-mcp-tools` binary as a child
/// process and communicates via JSON-RPC 2.0 over stdio.
pub struct McpClient {
    child: Child,
    request_id: u64,
}

impl McpClient {
    /// Spawn the MCP tool server.
    /// Build it first with: `cargo build -p rig-mcp-tools`
    pub async fn new() -> Result<Self> {
        let mcp_bin = Self::find_mcp_binary()?;

        let child = Command::new(&mcp_bin)
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .spawn()
            .with_context(|| format!("Failed to spawn MCP server: {}", mcp_bin.display()))?;

        let mut client = Self {
            child,
            request_id: 0,
        };

        // Initialize the MCP session
        client
            .send_request(
                "initialize",
                serde_json::json!({
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "rig-pattern", "version": "0.1.0"}
                }),
            )
            .await?;

        // Send initialized notification (no response expected)
        client
            .send_notification("notifications/initialized", serde_json::json!({}))
            .await?;

        Ok(client)
    }

    fn find_mcp_binary() -> Result<std::path::PathBuf> {
        // Check env override first
        if let Ok(p) = env::var("RIG_MCP_BIN") {
            return Ok(std::path::PathBuf::from(p));
        }
        let candidates = [
            std::path::PathBuf::from("../../target/release/rig-mcp-tools"),
            std::path::PathBuf::from("../../target/debug/rig-mcp-tools"),
            std::path::PathBuf::from("../target/release/rig-mcp-tools"),
            std::path::PathBuf::from("../target/debug/rig-mcp-tools"),
            std::path::PathBuf::from("target/release/rig-mcp-tools"),
            std::path::PathBuf::from("target/debug/rig-mcp-tools"),
        ];
        for c in &candidates {
            if c.exists() {
                return Ok(c.clone());
            }
        }
        // Fallback: assume it's on PATH
        Ok(std::path::PathBuf::from("rig-mcp-tools"))
    }

    pub async fn call_tool(
        &mut self,
        name: &str,
        params: serde_json::Value,
    ) -> Result<serde_json::Value> {
        let result = self
            .send_request(
                "tools/call",
                serde_json::json!({
                    "name": name,
                    "arguments": params,
                }),
            )
            .await?;

        // Extract text content from MCP response envelope
        if let Some(content) = result.get("content") {
            if let Some(arr) = content.as_array() {
                if let Some(first) = arr.first() {
                    if let Some(text) = first.get("text").and_then(|t| t.as_str()) {
                        if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(text) {
                            return Ok(parsed);
                        }
                        return Ok(serde_json::Value::String(text.to_string()));
                    }
                }
            }
        }
        Ok(result)
    }

    pub async fn list_tools(&mut self) -> Result<serde_json::Value> {
        self.send_request("tools/list", serde_json::json!({}))
            .await
    }

    async fn send_request(
        &mut self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<serde_json::Value> {
        self.request_id += 1;
        let request = serde_json::json!({
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        });

        let stdin = self.child.stdin.as_mut().context("No stdin on MCP child")?;
        let msg = serde_json::to_string(&request)?;
        stdin.write_all(msg.as_bytes()).await?;
        stdin.write_all(b"\n").await?;
        stdin.flush().await?;

        let stdout = self
            .child
            .stdout
            .as_mut()
            .context("No stdout on MCP child")?;
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader.read_line(&mut line).await?;

        let response: serde_json::Value = serde_json::from_str(&line)
            .with_context(|| format!("Failed to parse MCP response: {line}"))?;

        if let Some(error) = response.get("error") {
            anyhow::bail!("MCP error: {error}");
        }
        Ok(response
            .get("result")
            .cloned()
            .unwrap_or(serde_json::Value::Null))
    }

    async fn send_notification(
        &mut self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<()> {
        let notification = serde_json::json!({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        });

        let stdin = self.child.stdin.as_mut().context("No stdin on MCP child")?;
        let msg = serde_json::to_string(&notification)?;
        stdin.write_all(msg.as_bytes()).await?;
        stdin.write_all(b"\n").await?;
        stdin.flush().await?;
        Ok(())
    }
}

impl Drop for McpClient {
    fn drop(&mut self) {
        let _ = self.child.start_kill();
    }
}
