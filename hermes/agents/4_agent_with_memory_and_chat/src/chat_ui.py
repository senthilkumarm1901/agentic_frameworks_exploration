"""Terminal UI helpers for Hermes Pattern 4."""

from __future__ import annotations

import sys


def print_welcome(turn_count: int) -> None:
    print("\n══════════════════════════════════════════════════════════════")
    print("  🌍 Hermes Country Analysis Agent — Interactive Chat")
    print("  Tools: country_lookup · calculator · kb_search")
    print("  Skills: comparison · profile · regional · report")
    if turn_count:
        print(f"  🧠 Restored session with {turn_count} prior turns")
    else:
        print("  📝 New session")
    print("══════════════════════════════════════════════════════════════")
    print("  Type 'quit' to exit · 'memory' to view summary · 'clear' to reset\n")


def get_user_input() -> str:
    try:
        return input("  You: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"


def print_thinking() -> None:
    print("\n  🤔 Thinking...", flush=True)


def clear_thinking() -> None:
    print("", flush=True)


def print_skill_activation(skill_name: str) -> None:
    print(f"  📋 Activating skill: {skill_name}")


def print_tool_call(tool_name: str, args: dict) -> None:
    formatted_args = ", ".join(f'{key}="{value}"' for key, value in args.items())
    if formatted_args:
        print(f"  🔍 {tool_name}({formatted_args})")
    else:
        print(f"  🔍 {tool_name}()")


def print_tool_result(tool_name: str, result_text: str) -> None:
    print(f"     → {result_text}")


def print_answer(answer: str) -> None:
    print("\n  💬 Answer:")
    print(f"  {answer}\n")


def print_metrics(llm_calls: int, tool_calls: int, duration_ms: int, skill_activations: int = 0) -> None:
    extras = f" · {skill_activations} skill activations" if skill_activations else ""
    print(f"  ⏱ {duration_ms}ms · {llm_calls} LLM calls · {tool_calls} tool calls{extras}\n")


def print_memory_summary(summary: str, turn_count: int) -> None:
    print("\n──────────────────────────────────────────────────")
    print(f"  📝 Memory (Turn {turn_count}):")
    print(summary or "[No prior conversation history]")
    print("──────────────────────────────────────────────────\n")


def print_memory_cleared() -> None:
    print("  🗑️  Memory cleared.\n")


def print_error(message: str) -> None:
    print(f"  ❌ Error: {message}", file=sys.stderr)
