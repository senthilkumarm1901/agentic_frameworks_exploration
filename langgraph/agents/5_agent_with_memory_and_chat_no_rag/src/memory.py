"""Conversation summary manager — Hermes-inspired bounded memory.

Maintains a structured summary of the conversation that gets
injected into the system prompt as a frozen snapshot.

Key design principles (borrowed from Hermes):
1. Frozen snapshot — memory is loaded at session start, stays immutable during turn
2. Structured summarization — specific template with Topics, Facts, Preferences
3. Bounded — character limits force curation, not hoarding
"""

import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent.parent / "memory_store"
SESSION_FILE = MEMORY_DIR / "session.json"
MAX_SUMMARY_CHARS = 1500  # Bounded, like Hermes's 2200 char limit

# Structured summary template (inspired by Hermes ContextCompressor)
SUMMARY_TEMPLATE = """Summarize the conversation so far into this EXACT format.
Be concise. Stay under {max_chars} characters total.

## Conversation Summary

### Topics Discussed
[List the main topics/countries discussed, max 5 bullet points]

### Key Facts Retrieved
[List the most important numeric facts and qualitative insights discovered, max 5]

### User Preferences
[Any patterns in what the user asks about — regions, metrics, comparison style]

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
            return json.loads(SESSION_FILE.read_text())
        except json.JSONDecodeError:
            return _empty_summary()
    return _empty_summary()


def _empty_summary() -> dict:
    """Return an empty summary structure."""
    return {
        "summary": "",
        "turn_count": 0,
        "last_updated": None,
    }


def save_summary(summary_text: str, turn_count: int):
    """Persist session summary to disk."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "summary": summary_text[:MAX_SUMMARY_CHARS],
        "turn_count": turn_count,
        "last_updated": datetime.now().isoformat(),
    }
    SESSION_FILE.write_text(json.dumps(data, indent=2))


def clear_summary():
    """Clear the persisted summary (for --reset)."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def format_memory_block(summary_data: dict) -> str:
    """Format summary for injection into system prompt."""
    if not summary_data.get("summary"):
        return "[No prior conversation history]"

    return (
        f"═══ CONVERSATION MEMORY (Turn {summary_data['turn_count']}) ═══\n"
        f"{summary_data['summary']}\n"
        f"═══ END MEMORY ═══"
    )


def build_summarization_prompt(messages: list, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Build the prompt to ask the LLM to summarize conversation.
    
    Args:
        messages: List of LangChain message objects from the conversation
        max_chars: Maximum characters for the summary
        
    Returns:
        Formatted summarization prompt
    """
    # Convert messages to readable format
    lines = []
    for msg in messages:
        msg_type = getattr(msg, "type", type(msg).__name__.lower())
        content = getattr(msg, "content", "")
        
        if msg_type == "human":
            lines.append(f"User: {content}")
        elif msg_type == "ai" and content:
            lines.append(f"Agent: {content[:300]}...")
        elif msg_type == "tool":
            tool_name = getattr(msg, "name", "tool")
            lines.append(f"[{tool_name} result]: {content[:100]}...")
    
    conversation_text = "\n".join(lines[-20:])  # Last 20 messages max
    
    return SUMMARY_TEMPLATE.format(
        max_chars=max_chars,
        conversation=conversation_text
    )
