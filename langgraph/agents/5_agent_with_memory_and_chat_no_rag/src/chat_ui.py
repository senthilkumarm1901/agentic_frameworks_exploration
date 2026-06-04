"""Terminal chat UI with activity indicators.

Provides colored output and clean formatting for the interactive chat experience.
Inspired by Hermes CLI's clean output.

Updated for Pattern 5:
- Changed tool icons for wiki tools
"""

import sys

# ANSI color codes
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RED = "\033[31m"


def print_welcome(turn_count: int):
    """Print welcome banner with session info."""
    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  🌍 Country Analysis Agent — Interactive Chat (No RAG){RESET}")
    print(f"{DIM}  Tools: country_lookup · calculator · wiki_read{RESET}")
    print(f"{DIM}  Skills: comparison · profile · regional · report{RESET}")
    if turn_count > 0:
        print(f"{CYAN}  📝 Resuming session (Turn {turn_count}){RESET}")
    else:
        print(f"{DIM}  📝 New session{RESET}")
    print(f"{BOLD}{'═' * 60}{RESET}")
    print(f"{DIM}  Type 'quit' to exit · 'memory' to view summary · 'clear' to reset{RESET}\n")


def print_thinking():
    """Show thinking indicator."""
    print(f"  {DIM}🤔 Thinking...{RESET}", end="", flush=True)


def clear_thinking():
    """Clear the thinking indicator line."""
    print("\r" + " " * 40 + "\r", end="", flush=True)


def print_skill_activation(skill_name: str):
    """Show skill activation."""
    clear_thinking()
    print(f"  {MAGENTA}📋 Activating skill: {skill_name}{RESET}")


def print_tool_call(tool_name: str, args: dict):
    """Show tool call."""
    args_str = ", ".join(f'{k}="{v}"' for k, v in args.items())
    icon = {
        "country_lookup_tool": "🔍",
        "calculator_tool": "🧮",
        "wiki_read_tool": "📖",
        "wiki_index_tool": "📑",
    }.get(tool_name, "🔧")
    print(f"  {YELLOW}{icon} {tool_name}({args_str}){RESET}")


def print_tool_result(tool_name: str, result: str):
    """Show tool result (truncated)."""
    short = result[:80] + "..." if len(result) > 80 else result
    print(f"  {DIM}   → {short}{RESET}")


def print_answer(answer: str):
    """Print the final answer."""
    print(f"\n  {GREEN}{BOLD}💬 Answer:{RESET}")
    # Indent each line of the answer
    for line in answer.split("\n"):
        print(f"  {GREEN}{line}{RESET}")
    print()


def print_error(error: str):
    """Print an error message."""
    print(f"\n  {RED}❌ Error: {error}{RESET}\n")


def print_memory_summary(summary: str, turn_count: int):
    """Display current memory state."""
    print(f"\n  {CYAN}{'─' * 50}{RESET}")
    print(f"  {CYAN}📝 Memory (Turn {turn_count}):{RESET}")
    if summary:
        for line in summary.split("\n"):
            print(f"  {DIM}{line}{RESET}")
    else:
        print(f"  {DIM}[Empty — no conversation history yet]{RESET}")
    print(f"  {CYAN}{'─' * 50}{RESET}\n")


def print_metrics(llm_calls: int, tool_calls: int, duration_ms: int, skill_activations: int = 0):
    """Show turn metrics."""
    skills_str = f" · {skill_activations} skills" if skill_activations > 0 else ""
    print(f"  {DIM}⏱ {duration_ms}ms · {llm_calls} LLM calls · "
          f"{tool_calls} tool calls{skills_str}{RESET}\n")


def print_memory_cleared():
    """Show memory cleared message."""
    print(f"  {CYAN}🗑️  Memory cleared. Starting fresh.{RESET}\n")


def get_user_input() -> str:
    """Get user input with prompt."""
    try:
        return input(f"  {BOLD}You:{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"
