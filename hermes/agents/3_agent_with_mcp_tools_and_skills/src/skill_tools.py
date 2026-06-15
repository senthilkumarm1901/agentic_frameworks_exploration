"""Local skill discovery and activation tools for Hermes Pattern 3."""

from __future__ import annotations

from pathlib import Path


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "_shared" / "skills"
        if candidate.is_dir():
            return parent
    raise FileNotFoundError("Could not locate _shared/skills directory")


_PROJECT_ROOT = _find_project_root()
_SKILLS_DIR = _PROJECT_ROOT / "_shared" / "skills"

SKILL_INDEX = {
    "country-comparison": "Compare two or more countries across core metrics",
    "country-profile": "Build a comprehensive single-country profile",
    "regional-analysis": "Analyze countries by geographic region",
    "report-formatting": "Format analysis as a clean markdown report",
}


def get_skill_index_prompt() -> str:
    lines = ["<skills>"]
    for name, description in SKILL_INDEX.items():
        lines.append(f"- {name}: {description}")
    lines.append("</skills>")
    return "\n".join(lines)


def activate_skill(skill_name: str) -> str:
    skill_path = _SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        available = ", ".join(SKILL_INDEX)
        return f"Error: Skill '{skill_name}' not found. Available skills: {available}"
    return skill_path.read_text()


def build_activate_skill_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "activate_skill",
            "description": "Load full instructions for a named country-analysis skill",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Skill to load, such as country-comparison",
                    }
                },
                "required": ["skill_name"],
                "additionalProperties": False,
            },
        },
    }


def format_activate_skill_result(skill_name: str, skill_text: str) -> str:
    return f"Loaded skill: {skill_name}\n\n{skill_text}"