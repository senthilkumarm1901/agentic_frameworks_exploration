# Hermes Agent — Learning Notes

## What is Hermes Agent?

A self-improving AI agent by [Nous Research](https://nousresearch.com) (Python, MIT license). Tagline: "The agent that grows with you." It features a closed learning loop — it creates skills from experience, improves them during use, persists knowledge across sessions, and builds a deepening user model.

**Key distinction**: Hermes is a **standalone agent binary/product**, not a composable library like LangGraph or Strands. You interact with it, not import it.

## Core Architecture

### Execution Loop
- Standard agentic loop: LLM generates tool calls → tools execute → results feed back
- Supports interrupt-and-redirect, streaming output, and context compression
- Tool calls use XML format: `<tool_call>` tags parsed from model output

### System Prompt + Personalities
- Configurable via `/personality`
- Project-level context files shape every conversation

### Tool Calling
- 40+ built-in tools
- Toolset system lets you enable/disable groups
- Supports MCP (Model Context Protocol) for extensibility
- Function calling via `<tool_call>` XML tags (Hermes-3 native format)

### Terminal Backends (7)
Local, Docker, SSH, Singularity, Modal, Daytona, Vercel Sandbox — agent can run code in isolated environments.

### Subagents
Spawns isolated subagents for parallel workstreams; can write Python scripts that call tools via RPC.

## Key Patterns

| Pattern | Implementation |
|---------|---------------|
| **Skills (procedural memory)** | Agent autonomously creates reusable skills after complex tasks; skills self-improve during use. Compatible with agentskills.io standard. |
| **Persistent memory** | Agent-curated memory with periodic nudges. FTS5 session search + LLM summarization for cross-session recall. |
| **User modeling** | Honcho dialectic user modeling — builds understanding of the user over time. |
| **Scheduled automations** | Built-in cron scheduler with delivery to any platform (daily reports, backups, audits). |
| **Delegation/parallelization** | Subagents for parallel work; zero-context-cost RPC pipelines. |

## Setup Requirements

- **Install:** One-liner (`curl | bash` on Linux/macOS/WSL2; PowerShell on Windows)
- **Dependencies:** uv, Python 3.11, Node.js, ripgrep, ffmpeg (installer handles all)
- **Models:** Provider-agnostic — Nous Portal, OpenRouter (200+ models), NVIDIA NIM, OpenAI, HuggingFace, or any custom endpoint. Switch with `hermes model`.
- **Interfaces:** CLI (TUI), Telegram, Discord, Slack, WhatsApp, Signal, Email — single gateway process.
- **Infra:** Runs on $5 VPS, GPU cluster, or serverless (Modal/Daytona hibernate when idle).

## Comparison with Other Frameworks

| vs. | Hermes Difference |
|-----|-------------------|
| **LangGraph/CrewAI/Strands** | Not a library — it's a standalone agent binary with its own CLI, gateway, and persistence. You interact with it, not import it. |
| **Claude Code / Codex CLI** | Similar terminal UX but adds: self-improving skills, multi-platform messaging, cron scheduling, subagent delegation, and 7 sandbox backends. |
| **AutoGPT/AgentGPT** | Hermes has a tighter learning loop (skills + memory + user modeling) and is model-agnostic with no lock-in. |

## Hermes-3 Model Function Calling Format

The Hermes-3 model (available on Ollama) uses a specific XML-based function calling format:

```xml
<tool_call>
{"name": "function_name", "arguments": {"arg1": "value1"}}
</tool_call>
```

This is the native format we'll use in our exploration to build a custom execution loop — parsing these XML tags from model output and dispatching to MCP tools.

## References

- GitHub: https://github.com/nousresearch/hermes-agent
- Masterclass: https://www.dailydoseofds.com/p/hermes-agent-masterclass/
- Hermes-3 Model: Available via Ollama (`ollama pull hermes3`)
