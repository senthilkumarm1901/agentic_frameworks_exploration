"""Evaluator-Optimizer pattern — iterative generation and evaluation (Strands)."""
import argparse
import sys
import time

from strands import Agent

from shared.metrics import MetricsCollector
from shared.tasks import TASKS
from ollama_adapter import create_ollama_model


def main():
    parser = argparse.ArgumentParser(description="Evaluator-Optimizer pattern (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    theme = task["input"]["theme"]
    max_iterations = task["input"]["max_iterations"]
    model = create_ollama_model()
    agent = Agent(model=model)

    metrics = MetricsCollector(framework="strands", pattern=args.task)
    metrics.start_timer()

    current_haiku = ""
    feedback = ""
    accepted = False

    for iteration in range(max_iterations):
        # Generate / revise
        if feedback:
            prompt = (
                f"Revise this haiku about '{theme}' based on the feedback.\n\n"
                f"Current haiku:\n{current_haiku}\n\nFeedback: {feedback}\n\n"
                f"Output ONLY the revised haiku (three lines), nothing else."
            )
        else:
            prompt = (
                f"Write a haiku about '{theme}'. "
                f"A haiku has exactly 3 lines with 5, 7, and 5 syllables respectively. "
                f"Output ONLY the haiku (three lines), nothing else."
            )

        print(f"Generating haiku (iteration {iteration + 1})...", file=sys.stderr)
        t0 = time.perf_counter()
        gen_resp = agent(prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        current_haiku = str(gen_resp).strip()

        # Evaluate
        eval_prompt = (
            f"Evaluate this haiku about '{theme}':\n\n{current_haiku}\n\n"
            f"Check: 1) Does it have exactly 3 lines? 2) Is the syllable pattern 5-7-5? "
            f"3) Is it relevant to the theme '{theme}'?\n\n"
            f"If the haiku is acceptable, respond with ONLY: ACCEPTED\n"
            f"Otherwise, respond with specific feedback for improvement."
        )
        print("Evaluating haiku...", file=sys.stderr)
        t0 = time.perf_counter()
        eval_resp = agent(eval_prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        eval_text = str(eval_resp).strip()

        if "ACCEPTED" in eval_text.upper():
            print("Haiku accepted!", file=sys.stderr)
            accepted = True
            break

        print(f"Feedback: {eval_text}", file=sys.stderr)
        feedback = eval_text

    iterations_done = iteration + 1
    answer = f"Haiku ({iterations_done} iterations, accepted={accepted}):\n{current_haiku}"
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
