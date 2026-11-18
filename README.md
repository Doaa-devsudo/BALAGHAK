# BALAGHAK | بلاغك

Smart municipal reports (بلاغات) system: an AI agent collects and classifies citizen reports,
RAG over department guidelines decides the department and priority, n8n notifies the right team,
and a Streamlit dashboard lets the admin follow up.

> All reports in `data/reports.json` are simulated. Categories follow Balady 940; team names are fictional.

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows (Git Bash): source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env            # then put your real keys in .env
```

## Useful commands
```bash
python generate_data.py         # reset data/reports.json to the 90 simulated reports
python storage.py               # test the storage layer
```

## Departments
- الطرق والأرصفة
- صحة البيئة والمنشآت الغذائية
- النظافة العامة

## Run the app
```bash
streamlit run app.py
```

## Team split
| Person | Role | Files | Branch |
|---|---|---|---|
| 1 | RAG | `rag.py` | `rag` |
| 2 | Agent | `agent.py` | `agent` |
| 3 | UI | `app.py`, `pages_/user_chat.py`, `pages_/admin_dashboard.py` | `ui` |
| 4 | n8n + integration | `notify.py`, n8n workflow, Telegram, testing | `n8n` |

Every file starts as a **stub** (real function names, fake bodies), so everyone can work in parallel.
Replace the body of your functions; **never change the names or signatures** without telling the team.

**Merge order:** `rag` + `n8n` → `agent` → `ui`

## Contract
```python
# storage.py  (done)
load_reports() -> list[dict]
add_report(data: dict) -> dict
update_status(report_id: str, new_status: str) -> bool
DEPARTMENTS, PRIORITIES, STATUSES

# rag.py  (Person 1)
search_guidelines(query: str) -> str      # text of the top matching guideline(s)
get_guideline(department: str) -> str     # full guideline of one department (already real)

# notify.py  (Person 4)
send_to_n8n(report: dict) -> None         # must never raise

# agent.py  (Person 2)
run_agent(user_input: str, history: list[dict]) -> str
# history = [{"role": "user" | "assistant", "content": "..."}]
```

## Rules
- Copy department names from `storage.DEPARTMENTS`, never type them by hand.
- Edit only your own files; `git add <your files>`, not `git add .`
- Don't commit test reports: run `python generate_data.py` before committing.
- Need a new library? Tell the team; one person updates `requirements.txt`.
