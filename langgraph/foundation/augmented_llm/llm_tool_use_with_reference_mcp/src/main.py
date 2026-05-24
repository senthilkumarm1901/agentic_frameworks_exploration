"""AWS Learning Agent pattern — documentation lookup via MCP."""
import asyncio
import sys
import time

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from shared.config import get_ollama_config
from shared.metrics import MetricsCollector

SYSTEM_PROMPT = (
    "You are an AWS learning assistant. Your role is to help users understand AWS services, "
    "concepts, and architectures. Explain clearly with examples. Use the documentation tools "
    "to find accurate, up-to-date information. When explaining concepts, provide practical "
    "use cases and relate services to each other where relevant."
)

SAMPLE_QUESTION = "Explain how Amazon S3 storage classes work and when to use each one"


async def run(query: str, config: dict, metrics: MetricsCollector):
    llm = ChatOllama(model=config["model"], base_url=config["base_url"])

    async with MultiServerMCPClient(
        {
            "aws-docs": {
                "command": "uvx",
                "args": ["awslabs.aws-documentation-mcp-server@latest"],
                "transport": "stdio",
                "env": {
                    "FASTMCP_LOG_LEVEL": "ERROR",
                    "AWS_DOCUMENTATION_PARTITION": "aws",
                },
            }
        }
    ) as client:
        tools = client.get_tools()
        agent = create_react_agent(llm, tools=tools, prompt=SYSTEM_PROMPT)

        call_start = time.perf_counter()
        result = await agent.ainvoke({"messages": [("user", query)]})
        call_ms = (time.perf_counter() - call_start) * 1000
        metrics.record_llm_call(duration_ms=call_ms)

        answer = result["messages"][-1].content
        print(f"Answer: {answer}", file=sys.stderr)
        return answer


def main():
    config = get_ollama_config()
    metrics = MetricsCollector(framework="langgraph", pattern="aws_learning_agent")
    metrics.start_timer()

    answer = asyncio.run(run(SAMPLE_QUESTION, config, metrics))

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
