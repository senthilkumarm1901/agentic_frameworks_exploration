"""Orchestrator-Workers pattern — dynamic subtopic delegation (Strands + MCP)."""
import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters

from shared.metrics import MetricsCollector
from shared.tasks import TASKS
from ollama_adapter import create_ollama_model

_SHARED_PROJECT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "_shared")
)


def _parse_subtopics(text: str) -> list[str]:
    """Extract subtopics from a numbered list produced by the planner."""
    lines = text.strip().splitlines()
    subtopics = []
    for line in lines:
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        if len(cleaned) > 5:
            subtopics.append(cleaned)
    return subtopics[:5]


def _research(subtopic: str, topic: str, model, tools, metrics: MetricsCollector) -> str:
    worker = Agent(model=model, tools=tools)
    prompt = (
        f"Research this subtopic using the web_search tool. "
        f"Provide a concise 2-3 paragraph summary.\n\n"
        f"Main topic: {topic}\nSubtopic: {subtopic}"
    )
    print(f"Researching: {subtopic}", file=sys.stderr)
    t0 = time.perf_counter()
    resp = worker(prompt)
    metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
    return f"## {subtopic}\n{str(resp)}"


def main():
    parser = argparse.ArgumentParser(description="Orchestrator-Workers pattern (Strands)")
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    topic = task["input"]["topic"]
    model = create_ollama_model()

    metrics = MetricsCollector(framework="strands", pattern=args.task)
    metrics.start_timer()

    mcp_client = MCPClient(
        StdioServerParameters(
            command="uv",
            args=["run", "--project", _SHARED_PROJECT, "python", "-m", "shared.mcp_server"],
        )
    )

    with mcp_client:
        tools = mcp_client.list_tools_sync()

        # Step 1 — Plan: break topic into subtopics
        planner = Agent(model=model)
        plan_prompt = (
            f"Break this topic into 3-5 research subtopics. "
            f"Return ONLY a numbered list.\n\nTopic: {topic}"
        )
        print("Planning subtopics...", file=sys.stderr)
        t0 = time.perf_counter()
        plan_resp = planner(plan_prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
        subtopics = _parse_subtopics(str(plan_resp))
        print(f"Subtopics: {subtopics}", file=sys.stderr)

        # Step 2 — Workers: research each subtopic with tool access
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(_research, st, topic, model, tools, metrics)
                for st in subtopics
            ]
            findings = [f.result() for f in futures]

        # Step 3 — Synthesize: combine findings into a report
        combined = "\n\n".join(findings)
        synthesizer = Agent(model=model)
        synth_prompt = (
            f"Write a cohesive research report on '{topic}' using the research below. "
            f"Include an introduction, findings per subtopic, and a conclusion.\n\n{combined}"
        )
        print("Synthesizing report...", file=sys.stderr)
        t0 = time.perf_counter()
        report_resp = synthesizer(synth_prompt)
        metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)

        answer = str(report_resp)
        print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
