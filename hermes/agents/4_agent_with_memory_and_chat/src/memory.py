"""Conversation summary manager for Hermes Pattern 4."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "memory_store"
SESSION_FILE = MEMORY_DIR / "session.json"
MAX_SUMMARY_CHARS = 1500

SUMMARY_TEMPLATE = """Summarize the conversation so far into this EXACT format.
Be concise. Stay under {max_chars} characters total.

## Conversation Summary

### Topics Discussed
[List the main topics/countries discussed, max 5 bullet points]

### Key Facts Retrieved
[List the most important numeric facts and qualitative insights discovered, max 5]

### User Preferences
[Any patterns in what the user asks about - regions, metrics, comparison style]

### Last Interaction
[One sentence: what the user last asked and what the agent answered]

---
Conversation to summarize:
{conversation}
"""


def load_summary() -> dict:
    """Load persisted session summary from disk."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return _empty_summary()
    return _empty_summary()


def _empty_summary() -> dict:
    return {
        "summary": "",
        "turn_count": 0,
        "last_updated": None,
    }


def save_summary(summary_text: str, turn_count: int) -> None:
    """Persist session summary to disk."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "summary": summary_text[:MAX_SUMMARY_CHARS],
        "turn_count": turn_count,
        "last_updated": datetime.now().isoformat(),
    }
    SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_summary() -> None:
    """Clear the persisted summary."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def format_memory_block(summary_data: dict) -> str:
    """Format summary for injection into the system prompt."""
    if not summary_data.get("summary"):
        return "[No prior conversation history]"

    return (
        f"═══ CONVERSATION MEMORY (Turn {summary_data['turn_count']}) ═══\n"
        f"{summary_data['summary']}\n"
        f"═══ END MEMORY ═══"
    )


def build_summarization_prompt(exchanges: list[tuple[str, str]], max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Build the prompt used to summarize the chat so far."""
    conversation_lines: list[str] = []
    for user_query, agent_answer in exchanges[-20:]:
        conversation_lines.append(f"User: {user_query}")
        truncated = agent_answer[:300] + "..." if len(agent_answer) > 300 else agent_answer
        conversation_lines.append(f"Agent: {truncated}")

    conversation = "\n".join(conversation_lines)
    return SUMMARY_TEMPLATE.format(max_chars=max_chars, conversation=conversation)
