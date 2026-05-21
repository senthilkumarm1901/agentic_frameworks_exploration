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

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let task = get_task(&args.task);
    let config = OllamaConfig::from_env();
    let mut metrics = MetricsCollector::new("rig", &args.task);
    metrics.start_timer();

    let client = ollama::Client::new(&config.base_url);
    let model = client.completion_model(&config.model);

    let text = task.input["text"].as_str().unwrap_or("");
    let target_lang = task.input["target_language"].as_str().unwrap_or("Spanish");

    // Chain step 1: Summarize
    let summarize_prompt = format!(
        "Summarize the following text in exactly 2 sentences:\n\n{text}"
    );
    eprintln!("Summarizing...");
    let call_start = Instant::now();
    let summary = model.prompt(&summarize_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
    eprintln!("Summary: {summary}");

    // Chain step 2: Translate
    let translate_prompt = format!(
        "Translate the following text to {target_lang}. \
         Output ONLY the translation, nothing else:\n\n{summary}"
    );
    eprintln!("Translating to {target_lang}...");
    let call_start = Instant::now();
    let translation = model.prompt(&translate_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
    eprintln!("Translation: {translation}");

    let answer = format!(
        "Summary: {summary}\n\nTranslation ({target_lang}): {translation}"
    );

    metrics.stop_timer();
    metrics.answer = answer;
    metrics.emit();
    Ok(())
}
