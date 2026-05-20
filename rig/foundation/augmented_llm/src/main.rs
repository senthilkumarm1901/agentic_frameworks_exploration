use anyhow::Result;
use clap::Parser;
use rig::providers::ollama;
use rig::completion::Prompt;
use rig_shared::{get_task, MetricsCollector, OllamaConfig};
use std::time::Instant;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    task: String,
}

/// Deterministic weather stub — identical to MCP server / Python stubs.
fn get_weather(city: &str) -> serde_json::Value {
    match city {
        "Tokyo" => serde_json::json!({
            "city": "Tokyo", "temp_c": 22,
            "condition": "partly cloudy", "humidity": 65
        }),
        "London" => serde_json::json!({
            "city": "London", "temp_c": 14,
            "condition": "rainy", "humidity": 80
        }),
        "New York" => serde_json::json!({
            "city": "New York", "temp_c": 28,
            "condition": "sunny", "humidity": 45
        }),
        _ => serde_json::json!({
            "city": city, "temp_c": 20,
            "condition": "unknown", "humidity": 50
        }),
    }
}

/// Extract city names from LLM text that match our known stubs.
fn extract_cities(text: &str) -> Vec<&'static str> {
    let mut cities = Vec::new();
    let lower = text.to_lowercase();
    for city in ["Tokyo", "London", "New York"] {
        if lower.contains(&city.to_lowercase()) {
            cities.push(city);
        }
    }
    cities
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let task = get_task(&args.task);
    let config = OllamaConfig::from_env();
    let mut metrics = MetricsCollector::new("rig", &args.task);
    metrics.start_timer();

    let client = ollama::Client::new(&config.base_url);
    let model = client.completion_model(&config.model);

    let query = task.input["query"].as_str().unwrap_or("");

    // Step 1: Ask LLM with tool awareness
    let system_prompt = "\
You are a helpful assistant with access to a weather tool.

Available tool:
  get_weather(city: string) -> {city, temp_c, condition, humidity}

When you need weather data, respond with EXACTLY this format on its own line:
  TOOL_CALL: get_weather(\"<city>\")

After receiving tool results you will be asked to give a final answer.";

    let initial_prompt = format!("{system_prompt}\n\nUser: {query}");

    let call_start = Instant::now();
    let response = model.prompt(&initial_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);

    eprintln!("LLM response (step 1): {response}");

    // Step 2: Detect tool call — either explicit TOOL_CALL format or city mention
    let cities = if response.contains("TOOL_CALL") || response.contains("get_weather") {
        extract_cities(&response)
    } else {
        // Fallback: extract cities from the original query
        extract_cities(query)
    };

    let answer = if !cities.is_empty() {
        // Gather weather for all detected cities
        let weather_results: Vec<String> = cities
            .iter()
            .map(|c| {
                let w = get_weather(c);
                format!("Weather for {c}: {w}")
            })
            .collect();
        let tool_output = weather_results.join("\n");

        let followup = format!(
            "The weather tool returned the following data:\n{tool_output}\n\n\
             Based on this weather data, answer the user's original question: {query}"
        );

        let call_start = Instant::now();
        let final_response = model.prompt(&followup).await?;
        metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
        eprintln!("LLM response (step 2): {final_response}");
        final_response
    } else {
        response
    };

    metrics.stop_timer();
    metrics.answer = answer;
    metrics.emit();
    Ok(())
}
