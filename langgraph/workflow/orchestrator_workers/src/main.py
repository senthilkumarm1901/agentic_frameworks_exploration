"""Orchestrator-Workers pattern — dynamic subtopic delegation via LangGraph."""
import argparse
import asyncio
import os
import re
import sys
import time
from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.constants import Send
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector
from shared.tasks import TASKS

_SHARED_PROJECT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "_shared")


class OrchestratorState(TypedDict):
    topic: str
    subtopics: list[str]
    research_results: Annotated[list[str], lambda a, b: a + b]
    report: str


class WorkerState(TypedDict):
    subtopic: str
    topic: str
    research_results: Annotated[list[str], lambda a, b: a + b]


async def run(task_input: dict, config: dict, metrics: MetricsCollector):
    llm = ChatOllama(model=config["model"], base_url=config["base_url"])

    async with MultiServerMCPClient(
        {
            "tool-stubs": {
                "command": "uv",
                "args": ["run", "--project", _SHARED_PROJECT, "python", "-m", "shared.mcp_server"],
                "transport": "stdio",
            }
        }
    ) as client:
        tools = client.get_tools()

        async def plan(state: OrchestratorState) -> dict:
            prompt = (
                f"Break the following research topic into 3-5 specific subtopics to investigate. "
                f"Output ONLY a numbered list, one subtopic per line.\n\nTopic: {state['topic']}"
            )
            print("Planning subtopics...", file=sys.stderr)
            t0 = time.perf_counter()
            resp = await llm.ainvoke(prompt)
            metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
            lines = [re.sub(r"^\d+[\.\)]\s*", "", l.strip()) for l in resp.content.strip().splitlines() if l.strip()]
            subtopics = [l for l in lines if len(l) > 5][:5]
            print(f"Subtopics: {subtopics}", file=sys.stderr)
            return {"subtopics": subtopics}

        def route_to_workers(state: OrchestratorState):
            return [
                Send("research_worker", {"subtopic": s, "topic": state["topic"], "research_results": []})
                for s in state["subtopics"]
            ]

        async def research_worker(state: WorkerState) -> dict:
            worker_agent = create_react_agent(llm, tools=tools)
            prompt = (
                f"Research the following subtopic using the web_search tool. "
                f"Provide a concise 2-3 paragraph summary.\n\n"
                f"Main topic: {state['topic']}\nSubtopic: {state['subtopic']}"
            )
            print(f"Researching: {state['subtopic']}", file=sys.stderr)
            t0 = time.perf_counter()
            result = await worker_agent.ainvoke({"messages": [("user", prompt)]})
            metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
            content = result["messages"][-1].content
            return {"research_results": [f"## {state['subtopic']}\n{content}"]}

        async def synthesize(state: OrchestratorState) -> dict:
            combined = "\n\n".join(state["research_results"])
            prompt = (
                f"Write a cohesive research report on '{state['topic']}' using the research below. "
                f"Include an introduction, findings per subtopic, and a conclusion.\n\n{combined}"
            )
            print("Synthesizing report...", file=sys.stderr)
            t0 = time.perf_counter()
            resp = await llm.ainvoke(prompt)
            metrics.record_llm_call(duration_ms=(time.perf_counter() - t0) * 1000)
            return {"report": resp.content}

        graph = StateGraph(OrchestratorState)
        graph.add_node("plan", plan)
        graph.add_node("research_worker", research_worker)
        graph.add_node("synthesize", synthesize)

        graph.add_edge(START, "plan")
        graph.add_conditional_edges("plan", route_to_workers, ["research_worker"])
        graph.add_edge("research_worker", "synthesize")
        graph.add_edge("synthesize", END)

        app = graph.compile()
        result = await app.ainvoke({
            "topic": task_input["topic"],
            "subtopics": [],
            "research_results": [],
            "report": "",
        })
        return result["report"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task = TASKS[args.task]
    config = get_ollama_config()

    metrics = MetricsCollector(framework="langgraph", pattern=args.task)
    metrics.start_timer()

    answer = asyncio.run(run(task["input"], config, metrics))
    print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
