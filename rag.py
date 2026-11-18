"""RAG over the department guidelines.  Owner: Person 1 (RAG)

STUB: returns fixed text so the others can work. Replace the function bodies
with the real vector-store retrieval. Do NOT change the function names or signatures.
"""
from pathlib import Path

GUIDELINES_DIR = Path(__file__).parent / "data" / "guidelines"

# department name (must match storage.DEPARTMENTS) -> guideline file
DEPARTMENT_FILES = {
    "الطرق والأرصفة": "roads.md",
    "صحة البيئة والمنشآت الغذائية": "food_health.md",
    "النظافة العامة": "cleaning.md",
}


def search_guidelines(query: str) -> str:
    """Return the text of the guideline(s) most relevant to the user's complaint.

    STUB: always returns the roads guideline.
    TODO: embed the 3 guideline files, store them in FAISS, return the top k=2 matches.
    """
    return (GUIDELINES_DIR / "roads.md").read_text(encoding="utf-8")


def get_guideline(department: str) -> str:
    """Return the full guideline text of one department (used by the admin page).

    This one is already real: it just reads the file. No need to change it.
    """
    filename = DEPARTMENT_FILES.get(department)
    if filename is None:
        return ""
    return (GUIDELINES_DIR / filename).read_text(encoding="utf-8")


if __name__ == "__main__":
    for q in ["فيه حفرة في شارعنا", "المطعم أكله خايس", "الحاوية مليانة"]:
        print(q, "->", search_guidelines(q).splitlines()[0])
