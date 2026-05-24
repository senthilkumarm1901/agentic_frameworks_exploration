"""Orchestrator-Workers pattern — dynamic subtopic delegation (Hermes)."""
import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from run_agent import AIAgent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS


def _parse_subtopics(text: str) -> list[str]:
    """Extract subtopics from a numbered list produced by the planner."""
    lines = text.strip().splitlines()
    subtopics = []
    for line in lines:
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        if len(cleaned) > 5:
            subtopics.append(cleaned)
    return subtopics[:5]


def _research(subtopic: str, topic: str, config: dict, metrics: MetricsCollector) -> str:
    worker = AIAgent(
        model=config["model"],
        base_url=f"{config['base_url']}/v1",
        api_key="ollama",
        quiet_mode=True,
        max_iterations=10,
        enabled_toolsets=["web"],
        skip_context_files=True,
        skip_memory=True,
    )
    prompt = (
        f"Research this subtopic. Provide a concise 2-3 paragraph summary.\n\n"
        f"Main topic: {topic}\nSubtopic: {subtopic}"
    )
    print(f"Researching: {subtopic}", file=sys.stderr)
    t0 = time.perf_counter()
    resp = worker.chat(prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    return f"## {subtopic}\n{str(resp)}"


def main():
    parser = argparse.ArgumentParser(description="Orchestrator-Workers pattern (Hermes)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    topic = task["input"]["topic"]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="hermes", pattern=args.task)
    metrics.start_timer()

    # Step 1 — Plan: break topic into subtopics
    planner = AIAgent(
        model=config["model"],
        base_url=f"{config['base_url']}/v1",
        api_key="ollama",
        quiet_mode=True,
        max_iterations=10,
        skip_context_files=True,
        skip_memory=True,
    )
    plan_prompt = (
        f"Break this topic into 3-5 research subtopics. "
        f"Return ONLY a numbered list.\n\nTopic: {topic}"
    )
    print("Planning subtopics...", file=sys.stderr)
    t0 = time.perf_counter()
    plan_resp = planner.chat(plan_prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    subtopics = _parse_subtopics(str(plan_resp))
    print(f"Subtopics: {subtopics}", file=sys.stderr)

    # Step 2 — Workers: research each subtopic in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(_research, st, topic, config, metrics)
            for st in subtopics
        ]
        findings = [f.result() for f in futures]

    # Step 3 — Synthesize: combine findings into a report
    combined = "\n\n".join(findings)
    synthesizer = AIAgent(
        model=config["model"],
        base_url=f"{config['base_url']}/v1",
        api_key="ollama",
        quiet_mode=True,
        max_iterations=10,
        skip_context_files=True,
        skip_memory=True,
    )
    synth_prompt = (
        f"Write a cohesive research report on '{topic}' using the research below. "
        f"Include an introduction, findings per subtopic, and a conclusion.\n\n{combined}"
    )
    print("Synthesizing report...", file=sys.stderr)
    t0 = time.perf_counter()
    report_resp = synthesizer.chat(synth_prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

    answer = str(report_resp)
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
