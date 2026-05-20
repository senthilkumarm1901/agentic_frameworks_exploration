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

fn review_prompt(aspect: &str, code: &str) -> String {
    match aspect {
        "correctness" => format!(
            "You are a code correctness reviewer. Analyze the following code for bugs, \
             off-by-one errors, missing edge cases, and logical errors. Be specific.\n\nCode:\n{code}"
        ),
        "performance" => format!(
            "You are a performance reviewer. Analyze the following code for time complexity, \
             space complexity, and optimization opportunities. Be specific.\n\nCode:\n{code}"
        ),
        "style" => format!(
            "You are a code style reviewer. Analyze the following code for readability, \
             naming conventions, Pythonic idioms, and maintainability. Be specific.\n\nCode:\n{code}"
        ),
        _ => unreachable!(),
    }
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

    let code = task.input["code"].as_str().unwrap_or("");

    let correctness_prompt = review_prompt("correctness", code);
    let performance_prompt = review_prompt("performance", code);
    let style_prompt = review_prompt("style", code);

    // Fan-out: 3 concurrent reviews via tokio::join!
    eprintln!("Starting parallel reviews (correctness, performance, style)...");
    let t_correctness = Instant::now();
    let t_performance = Instant::now();
    let t_style = Instant::now();

    let (r_correctness, r_performance, r_style) = tokio::join!(
        model.prompt(&correctness_prompt),
        model.prompt(&performance_prompt),
        model.prompt(&style_prompt),
    );

    let correctness_ms = t_correctness.elapsed().as_secs_f64() * 1000.0;
    let performance_ms = t_performance.elapsed().as_secs_f64() * 1000.0;
    let style_ms = t_style.elapsed().as_secs_f64() * 1000.0;

    let correctness_review = r_correctness?;
    let performance_review = r_performance?;
    let style_review = r_style?;

    metrics.record_llm_call(correctness_ms, 0, 0);
    metrics.record_llm_call(performance_ms, 0, 0);
    metrics.record_llm_call(style_ms, 0, 0);

    eprintln!("All reviews complete. Merging...");

    // Fan-in: merge reviews
    let combined = format!(
        "## Correctness Review\n{correctness_review}\n\n\
         ## Performance Review\n{performance_review}\n\n\
         ## Style Review\n{style_review}"
    );

    let merge_prompt = format!(
        "You are a senior engineer. Synthesize the following three code reviews into \
         a single, actionable summary. Highlight the most critical issues first.\n\n{combined}"
    );

    let call_start = Instant::now();
    let merged = model.prompt(&merge_prompt).await?;
    metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
    eprintln!("Merged review: {merged}");

    metrics.stop_timer();
    metrics.answer = merged;
    metrics.emit();
    Ok(())
}
