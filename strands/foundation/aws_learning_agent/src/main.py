"""AWS Learning Agent pattern — documentation lookup via MCP (Strands)."""
import sys
import time

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters

from shared.metrics import MetricsCollector
from ollama_adapter import create_ollama_model

SYSTEM_PROMPT = (
    "You are an AWS learning assistant. Your role is to help users understand AWS services, "
    "concepts, and architectures. Explain clearly with examples. Use the documentation tools "
    "to find accurate, up-to-date information. When explaining concepts, provide practical "
    "use cases and relate services to each other where relevant."
)

SAMPLE_QUESTION = "Explain how Amazon S3 storage classes work and when to use each one"


def main():
    model = create_ollama_model()
    metrics = MetricsCollector(framework="strands", pattern="aws_learning_agent")
    metrics.start_timer()

    mcp_client = MCPClient(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"],
            env={
                "FASTMCP_LOG_LEVEL": "ERROR",
                "AWS_DOCUMENTATION_PARTITION": "aws",
            },
        )
    )

    with mcp_client:
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=mcp_client.list_tools_sync(),
        )

        call_start = time.perf_counter()
        response = agent(SAMPLE_QUESTION)
        call_ms = (time.perf_counter() - call_start) * 1000
        metrics.record_llm_call(duration_ms=call_ms)

        answer = str(response)
        print(f"Answer: {answer}", file=sys.stderr)

    metrics.stop_timer()
    metrics.answer = answer
    metrics.emit()


if __name__ == "__main__":
    main()
