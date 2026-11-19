"""Serve the local municipal guidelines to the reporting agent."""

from pathlib import Path

GUIDELINES_DIR = Path(__file__).parent / "data" / "guidelines"

DEPARTMENT_FILES = {
    "الطرق والأرصفة": "roads.md",
    "صحة البيئة والمنشآت الغذائية": "food_health.md",
    "النظافة العامة": "cleaning.md",
}


def search_guidelines(query: str) -> str:
    """Give the agent all three short guides so it can compare their scopes."""
    if not query or not query.strip():
        return ""
    return "\n\n---\n\n".join(
        f"# {department}\n{get_guideline(department)}" for department in DEPARTMENT_FILES
    )


def get_guideline(department: str) -> str:
    """Return the full guideline for a department, or an empty string if unknown."""
    filename = DEPARTMENT_FILES.get(department)
    if filename is None:
        return ""
    return (GUIDELINES_DIR / filename).read_text(encoding="utf-8")
