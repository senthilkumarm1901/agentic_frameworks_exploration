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

    let theme = task.input["theme"].as_str().unwrap_or("autumn");
    let max_iterations = task.input["max_iterations"].as_u64().unwrap_or(5) as usize;

    let mut current_haiku = String::new();
    let mut feedback = String::new();
    let mut accepted = false;

    for iteration in 0..max_iterations {
        // Generate
        let gen_prompt = if feedback.is_empty() {
            format!(
                "Write a haiku about '{theme}'. \
                 A haiku has exactly 3 lines with 5, 7, and 5 syllables respectively. \
                 Output ONLY the haiku (three lines), nothing else."
            )
        } else {
            format!(
                "Revise this haiku about '{theme}' based on the feedback.\n\n\
                 Current haiku:\n{current_haiku}\n\n\
                 Feedback: {feedback}\n\n\
                 Output ONLY the revised haiku (three lines), nothing else."
            )
        };

        eprintln!("Generating haiku (iteration {})...", iteration + 1);
        let call_start = Instant::now();
        current_haiku = model.prompt(&gen_prompt).await?.trim().to_string();
        metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);
        eprintln!("Haiku:\n{current_haiku}");

        // Evaluate
        let eval_prompt = format!(
            "Evaluate this haiku about '{theme}':\n\n{current_haiku}\n\n\
             Check: 1) Does it have exactly 3 lines? 2) Is the syllable pattern 5-7-5? \
             3) Is it relevant to the theme '{theme}'?\n\n\
             If the haiku is acceptable, respond with ONLY: ACCEPTED\n\
             Otherwise, respond with specific feedback for improvement."
        );

        eprintln!("Evaluating haiku...");
        let call_start = Instant::now();
        let eval_response = model.prompt(&eval_prompt).await?;
        metrics.record_llm_call(call_start.elapsed().as_secs_f64() * 1000.0, 0, 0);

        let content = eval_response.trim();
        if content.to_uppercase().contains("ACCEPTED") {
            eprintln!("Haiku accepted!");
            accepted = true;
            break;
        }
        eprintln!("Feedback: {content}");
        feedback = content.to_string();
    }

    let answer = format!(
        "Haiku ({} iterations, accepted={accepted}):\n{current_haiku}",
        metrics.llm_calls.len() / 2 // each iteration = 1 generate + 1 evaluate
    );
    eprintln!("Answer: {answer}");

    metrics.stop_timer();
    metrics.answer = answer;
    metrics.emit();
    Ok(())
}
