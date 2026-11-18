"""RAG over the department guidelines.  Owner: Person 1 (RAG)

Loads the three department guideline files as LangChain Documents, embeds them
once with Gemini (`gemini-embedding-001`), and stores them in a FAISS index
for semantic retrieval. Do NOT change the function names or signatures below
— Person 2 (agent) and Person 3 (UI) depend on this exact contract:

    search_guidelines(query: str) -> str
    get_guideline(department: str) -> str
"""
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

GUIDELINES_DIR = Path(__file__).parent / "data" / "guidelines"

# department name (must match storage.DEPARTMENTS) -> guideline file
DEPARTMENT_FILES = {
    "الطرق والأرصفة": "roads.md",
    "صحة البيئة والمنشآت الغذائية": "food_health.md",
    "النظافة العامة": "cleaning.md",
}

_vectorstore = None


def _load_documents() -> list[Document]:
    """Read every guideline file in DEPARTMENT_FILES into a Document."""
    documents = []
    for department, filename in DEPARTMENT_FILES.items():
        path = GUIDELINES_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing guideline file for department '{department}': {path}"
            )
        text = path.read_text(encoding="utf-8")
        documents.append(Document(page_content=text, metadata={"department": department}))
    return documents


def _get_vectorstore() -> FAISS:
    """Build the FAISS index once (calls the embeddings API), then reuse it."""
    global _vectorstore
    if _vectorstore is None:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
            _vectorstore = FAISS.from_documents(_load_documents(), embeddings)
        except Exception as exc:
            raise RuntimeError(
                "Failed to build the guidelines vector store. Make sure GOOGLE_API_KEY "
                "is set in .env and valid."
            ) from exc
    return _vectorstore


def search_guidelines(query: str) -> str:
    """Return the text of the guideline(s) most relevant to the user's complaint.

    Retrieves the top 2 matches so the agent can see both departments' scopes
    when a complaint sits between two of them.
    """
    if not query or not query.strip():
        return ""
    try:
        docs = _get_vectorstore().similarity_search(query, k=2)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Guideline retrieval failed.") from exc
    return "\n\n---\n\n".join(d.page_content for d in docs)


def get_guideline(department: str) -> str:
    """Return the full guideline text of one department (used by the admin page).

    This one is already real: it just reads the file. No need to change it.
    """
    filename = DEPARTMENT_FILES.get(department)
    if filename is None:
        return ""
    return (GUIDELINES_DIR / filename).read_text(encoding="utf-8")


def _top_department(query: str) -> str:
    """Helper for testing: department of the single best match."""
    docs = _get_vectorstore().similarity_search(query, k=1)
    return docs[0].metadata["department"]


if __name__ == "__main__":
    ROADS = "الطرق والأرصفة"
    FOOD = "صحة البيئة والمنشآت الغذائية"
    CLEANING = "النظافة العامة"

    test_cases = [
        # required cases from the spec
        ("فيه حفرة في شارعنا", ROADS),
        ("الشارع خربان عند الإشارة", ROADS),
        ("المطعم أكله خايس", FOOD),
        ("شفت صراصير في البوفية", FOOD),
        ("الحاوية مليانة", CLEANING),
        ("فيه قطة ميتة في الشارع", CLEANING),
        # additional Saudi-dialect cases
        ("الرصيف مكسور وصعب نمشي عليه", ROADS),
        ("فيه منهول بدون غطاء خطير على السيارات", ROADS),
        ("الزفلت متشقق من زمان ومحد صلحه", ROADS),
        ("لقيت فار في المخبز اللي جنبنا", FOOD),
        ("البقالة تبيع أكل منتهي الصلاحية", FOOD),
        ("تعبت من ريحة الزبالة المتكومة بجانب البيت", CLEANING),
        ("حاوية النفايات مكسورة ومحتاجين وحدة جديدة", CLEANING),
        ("فيه نفايات بناء مرمية في الأرض الفضا", CLEANING),
        # tricky: could involve two departments (trash outside a restaurant)
        ("فيه زبالة متكومة قدام مطعم وريحتها وحشة", FOOD),
        # tricky: missing location info
        ("فيه حفرة كبيرة وخطيرة", ROADS),
        # tricky: outside the scope of all three departments
        ("الكهرباء مقطوعة عندنا من الصبح", None),
    ]

    passed = 0
    for query, expected in test_cases:
        try:
            top = _top_department(query)
        except RuntimeError as exc:
            print(f"ERROR running tests: {exc}")
            break
        result = "PASS" if expected is None or top == expected else "FAIL"
        if result == "PASS":
            passed += 1
        print(f"البلاغ: {query}")
        print(f"  المتوقع: {expected or '(خارج اختصاص الإدارات الثلاث)'}")
        print(f"  النتيجة: {top}")
        print(f"  {result}")
        print()

    print(f"{passed}/{len(test_cases)} passed")
