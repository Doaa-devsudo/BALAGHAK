# Person 2: Agent (`agent.py`)

## Your job
The agent talks to the user, collects the missing information, uses RAG to pick the department and
priority, and saves the report. It's the core of the project.

- **File you own:** `agent.py`
- **Branch:** `agent`
- **You depend on:** `rag.search_guidelines` (Person 1), `notify.send_to_n8n` (Person 4),
  `storage.add_report` (done). Until Checkpoint 1, the first two are stubs. That's fine:
  the stub RAG always returns the roads guideline, enough to build and test the whole flow.
- **Who depends on you:** Person 3 (UI) calls `run_agent`.

## Before you start
1. Setup in `docs/00_TEAM_WORKFLOW.md` → section 1.
2. `git checkout -b agent`
3. `.env` has `GOOGLE_API_KEY` and `GEMINI_MODEL`.
4. Read `storage.py` (`add_report` and the constants) and one guideline file in `data/guidelines/`.
5. Run the stub: `python agent.py` opens a terminal chat. Type `exit` to quit.

## What you need to know
- **Tool:** a Python function the LLM can decide to call. Its docstring is what the LLM reads
  to understand when to use it, so write it clearly.
- **Agent loop:** the LLM reads the conversation → decides to answer or call a tool → sees the tool
  result → repeats until it answers.
- **History:** the user answers questions over several messages («وين الموقع؟» → «حطين»), so you
  pass all previous messages every time.

## Your contract (don't change)
```python
run_agent(user_input: str, history: list[dict]) -> str
# history = [{"role": "user" | "assistant", "content": "..."}]  previous messages only
```

## Steps

### 1. The two tools
Use the `@tool` decorator (`from langchain_core.tools import tool`).

**`search_guidelines_tool(complaint: str) -> str`**
- Docstring: «ابحث في أدلة الإدارات لتحديد الإدارة المختصة والأولوية. استخدمها دائمًا قبل الحفظ.»
- Body: `return rag.search_guidelines(complaint)`

**`save_report(text, department, neighborhood, street, priority, facility="") -> str`**
- Docstring: explain each argument, and that `department` must be one of `storage.DEPARTMENTS`
  and `priority` one of `storage.PRIORITIES`.
- Body:
  1. `report = storage.add_report({...})` inside `try`.
  2. If it raises `ValueError`, **return the error message as a string** (don't crash).
     The LLM reads it and retries with the correct name.
  3. `notify.send_to_n8n(report)`
  4. Return `f"تم الحفظ. رقم البلاغ: {report['id']}"`

### 2. The system prompt
This is where most of the behavior comes from. It should say, in order:
1. أنت مساعد يستقبل البلاغات البلدية باللهجة السعودية وترد بالعربية بشكل مختصر ولطيف.
2. الإدارات المتاحة فقط: (list them from `storage.DEPARTMENTS`, inject with an f-string).
   إذا كان البلاغ خارجها (كهرباء، مياه، مرور...) اعتذر ولا تحفظه.
3. المعلومات المطلوبة: وصف المشكلة، الحي، الشارع أو أقرب معلم، واسم المنشأة إذا كان البلاغ عن مطعم أو محل.
   إذا نقصت معلومة، اسأل عنها **سؤال واحد في كل مرة**.
4. قبل تحديد الإدارة والأولوية، استخدم أداة البحث دائمًا واتبع «قواعد الأولوية» في الدليل. لا تخمّن.
5. عند اكتمال المعلومات، احفظ البلاغ.
6. بعد الحفظ، رد برقم البلاغ والإدارة والأولوية في رسالة واحدة قصيرة.

### 3. Create the agent
Use what your program taught you. Example with LangChain 1.x:
```python
from langchain.agents import create_agent
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), temperature=0)
_agent = create_agent(model=llm, tools=[search_guidelines_tool, save_report], system_prompt=SYSTEM_PROMPT)
```
- `temperature=0` so classification is stable.
- The model name comes from `.env` (`GEMINI_MODEL`), so you can switch models without touching code.
  If you get a "model not found" error, pick another name from the model list in Google AI Studio.
- Gemini's free tier has a per-minute request limit. Each user message can be 2–3 calls
  (search, save, answer), so don't spam tests; if you hit a 429 error, wait a minute.
- Gemini sometimes returns `content` as a list of parts instead of a string. In `run_agent`,
  if the content is a list, join the `text` of each part before returning it.
- Create the agent **once** at module level, not inside `run_agent`.
- If your program used LangGraph's `create_react_agent` or `AgentExecutor`, that's fine. Only `run_agent` must keep its contract.

### 4. Replace the body of `run_agent`
```python
messages = history + [{"role": "user", "content": user_input}]
result = _agent.invoke({"messages": messages})
return result["messages"][-1].content
```
Wrap it in `try/except` and return a polite Arabic error («صار خطأ، حاول مرة ثانية») instead of crashing the UI.

### 5. Test in the terminal
`python agent.py` (the loop at the bottom already passes the history).

## Done when
| You type | Expected |
|---|---|
| فيه حفرة كبيرة | asks for the location |
| في حطين شارع رابغ | saves, replies with `RPT-1091`, الطرق والأرصفة, a priority |
| المطعم اللي جنبنا أكله خايس | asks for the restaurant name and/or location |
| الكهرباء مقطوعة | says it's outside scope, saves nothing |
| فيه حفرة قريب مدرسة في النرجس شارع الثمامة | saves directly with priority عاجلة |

Check that `data/reports.json` got the new reports with correct fields, then
**reset**: `python generate_data.py`.

Note: before Checkpoint 1, RAG is a stub, so food/cleaning complaints may be classified wrongly.
That's expected. Test them again after you pull the real RAG.

## Push and merge
```bash
python generate_data.py                  # reset data before committing!
git add agent.py
git commit -m "Agent: tools + system prompt + history"
git push -u origin agent
```
- At **Checkpoint 1** (~hour 3): pull `main` into your branch (`00_TEAM_WORKFLOW.md` section 3)
  to get the real RAG and notify. Run all tests again.
- At **Checkpoint 2** (~hour 4): open a Pull Request into `main` and merge. Tell Person 3.
