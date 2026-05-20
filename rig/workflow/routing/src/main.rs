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

const BILLING_PROMPT: &str = "\
You are a billing support specialist. Help the customer with their billing issue. \
Be empathetic and offer concrete solutions like refunds or credits.\n\nCustomer message: ";

const TECHNICAL_PROMPT: &str = "\
You are a technical support engineer. Help the customer with their technical issue. \
Provide clear troubleshooting steps.\n\nCustomer message: ";

const GENERAL_PROMPT: &str = "\
You are a general customer support agent. Help the customer with their inquiry. \
Be helpful and direct.\n\nCustomer message: ";

fn handler_prompt(category: &str, message: &str) -> String {
    let prefix = match category {
        "billing" => BILLING_PROMPT,
        "technical" => TECHNICAL_PROMPT,
        _ => GENERAL_PROMPT,
    };
    format!("{prefix}{message}")
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

    let message = task.input["message"].as_str().unwrap_or("");

    // Step 1: Classify
    let classify_prompt = format!(
        "Classify the following customer message into exactly one category: \
         billing, technical, or general. Output ONLY the category word, nothing else.\n\n\
         Message: {message}"
    );
    eprintln!("Classifying...");
    let call_start = Instant::now();
    let raw_category = model.prompt(&classify_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);

    let category = raw_category.trim().to_lowercase();
    let category = match category.as_str() {
        "billing" | "technical" | "general" => category.as_str(),
        _ => "general",
    }
    .to_string();
    eprintln!("Category: {category}");

    // Step 2: Route to specialized handler
    let handle_prompt = handler_prompt(&category, message);
    eprintln!("Handling as {category}...");
    let call_start = Instant::now();
    let response = model.prompt(&handle_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
    eprintln!("Response: {response}");

    let answer = format!("[{category}] {response}");

    metrics.stop_timer();
    metrics.answer = answer;
    metrics.emit();
    Ok(())
}
