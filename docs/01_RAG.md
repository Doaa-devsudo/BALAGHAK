# Person 1: RAG (`rag.py`)

## Your job
Given a complaint written by a user, return the department guideline(s) that match it.
The agent uses this to decide **which department** and **which priority**.

- **File you own:** `rag.py`
- **Branch:** `rag`
- **You depend on:** nothing. The guideline files are ready in `data/guidelines/`.
- **Who depends on you:** Person 2 (agent) uses `search_guidelines`, Person 3 (UI) uses `get_guideline`.

## Before you start
1. Do the setup in `docs/00_TEAM_WORKFLOW.md` → section 1.
2. `git checkout -b rag`
3. Make sure `.env` has `OPENAI_API_KEY` (the embeddings need it).
4. Read the 3 files in `data/guidelines/`. Notice they all have the same sections.
5. Run the stub: `python rag.py`. Right now every query returns the roads guideline. Your job is to fix that.

## What you need to know
- **Embedding:** turns text into a vector of numbers. Texts with similar meaning → close vectors.
- **Vector store (FAISS):** stores the vectors and finds the closest ones to a query.
- **Why one document per file (no chunking):** each guideline is short, and the agent needs the
  *whole* department (scope + priority rules + what's out of scope) to decide correctly.
  3 files = 3 documents.

## Your contract (don't change)
```python
search_guidelines(query: str) -> str      # text of the top matching guideline(s)
get_guideline(department: str) -> str     # already done in the stub, keep it
```

## Steps

### 1. Imports and API key
```python
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
```
(If your program used another provider, e.g. Google, use its embeddings class instead.
The rest stays the same.)

### 2. Load the guidelines as documents
Write `_load_documents() -> list[Document]`:
- Loop over `DEPARTMENT_FILES` (already in the stub: department name → file name).
- For each: read the file, create `Document(page_content=text, metadata={"department": department})`.

### 3. Build the vector store once
Building it calls the embeddings API, so do it **only once**, not on every message:
```python
_vectorstore = None

def _get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _vectorstore = FAISS.from_documents(_load_documents(), embeddings)
    return _vectorstore
```

### 4. Replace the body of `search_guidelines`
- `docs = _get_vectorstore().similarity_search(query, k=2)`
- Return the texts joined with a separator, e.g. `"\n\n---\n\n".join(d.page_content for d in docs)`.

Why `k=2`: some complaints sit between two departments (rubbish outside a restaurant).
Giving the agent the top 2 lets it read the «خارج الاختصاص» section and choose correctly.

### 5. Keep `get_guideline` as it is
It already reads the file directly. The admin page uses it to show «الإجراء المقترح».

### 6. Update the test block
At the bottom, for each query print the **department of the first result**.
Tip: add a helper `_top_department(query)` that returns `docs[0].metadata["department"]`,
useful for testing.

## Done when
`python rag.py` gives:

| Query | Expected first result |
|---|---|
| فيه حفرة في شارعنا | الطرق والأرصفة |
| الشارع خربان عند الإشارة | الطرق والأرصفة |
| المطعم أكله خايس | صحة البيئة والمنشآت الغذائية |
| شفت صراصير في البوفية | صحة البيئة والمنشآت الغذائية |
| الحاوية مليانة | النظافة العامة |
| فيه قطة ميتة في الشارع | النظافة العامة |

Test at least 10 queries in Saudi dialect. If one goes to the wrong department, the fix is usually
**adding keywords** to that department's guideline file (section «كلمات مفتاحية»), not changing code.
If you edit a guideline file, tell the team.

## Push and merge
```bash
git add rag.py data/guidelines/          # guidelines only if you changed them
git commit -m "RAG: FAISS retrieval over department guidelines"
git push -u origin rag
```
Then open a Pull Request into `main` (see `00_TEAM_WORKFLOW.md` section 4).
You merge at **Checkpoint 1** (~hour 3), together with `n8n`. Tell Person 2 when it's merged.

## After you're done
Help Person 2 test the agent: write 10 tricky بلاغات (two departments, missing location, outside scope).
