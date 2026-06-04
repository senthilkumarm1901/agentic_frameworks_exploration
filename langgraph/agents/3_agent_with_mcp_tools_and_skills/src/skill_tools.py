"""Skill activation tool for Pattern 3."""

from pathlib import Path
from langchain_core.tools import tool

# Skills directory in _shared (4 levels up from src/)
SKILLS_DIR = Path(__file__).parent.parent.parent.parent.parent / "_shared" / "skills"

# Skill index for discovery (name -> one-liner description)
SKILL_INDEX = {
    "country-comparison": "Systematically compare two or more countries across metrics",
    "country-profile": "Build a comprehensive single-country profile",
    "regional-analysis": "Analyze countries by geographic region with aggregates",
    "report-formatting": "Format analysis results into a clean markdown report",
}


@tool
def activate_skill(skill_name: str) -> str:
    """
    Load full instructions for a skill by name.
    
    Available skills:
    - country-comparison: Compare countries across metrics
    - country-profile: Build comprehensive country brief
    - regional-analysis: Analyze regional patterns and aggregates
    - report-formatting: Format results as professional report
    
    Args:
        skill_name: Name of the skill to activate (e.g., 'country-comparison')
        
    Returns:
        Full skill methodology instructions to follow
    """
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    
    if not skill_path.exists():
        available = ", ".join(SKILL_INDEX.keys())
        return f"Error: Skill '{skill_name}' not found. Available skills: {available}"
    
    return skill_path.read_text()


def get_skill_index_prompt() -> str:
    """Generate the <skills> block for the system prompt."""
    lines = ["<skills>"]
    for name, description in SKILL_INDEX.items():
        lines.append(f"- {name}: {description}")
    lines.append("</skills>")
    return "\n".join(lines)
