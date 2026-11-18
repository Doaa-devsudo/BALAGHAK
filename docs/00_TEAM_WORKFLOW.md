# Team Workflow (everyone reads this first)

## The project in one picture

```
User (Streamlit chat)  ──►  Agent (agent.py)  ──uses──►  RAG (rag.py)
                                 │
                                 ▼
                          storage.add_report  ──►  data/reports.json
                                 │
                                 ▼
                          notify.send_to_n8n  ──►  n8n  ──►  Telegram group of the right team

Admin (Streamlit dashboard)  ──►  reads data/reports.json, changes status, shows suggested action (RAG)
```

## Who does what

| Person | Role | Files you own | Branch | Your guide |
|---|---|---|---|---|
| 1 | RAG | `rag.py` | `rag` | `docs/01_RAG.md` |
| 2 | Agent | `agent.py` | `agent` | `docs/02_AGENT.md` |
| 3 | UI | `app.py`, `pages_/user_chat.py`, `pages_/admin_dashboard.py` | `ui` | `docs/03_UI.md` |
| 4 | n8n + integration | `notify.py`, n8n workflow, Telegram | `n8n` | `docs/04_N8N.md` |

**Everyone works in parallel from minute one.** Every file already exists as a *stub*: the real
function names with fake bodies. You replace the bodies of *your* functions. Because the names
don't change, everyone else's code keeps working.

## The contract (never change these without telling the team)

```python
# storage.py  (done)
load_reports() -> list[dict]
add_report(data: dict) -> dict          # raises ValueError on invalid department/priority
update_status(report_id: str, new_status: str) -> bool
DEPARTMENTS, PRIORITIES, STATUSES

# rag.py  (Person 1)
search_guidelines(query: str) -> str
get_guideline(department: str) -> str

# notify.py  (Person 4)
send_to_n8n(report: dict) -> None       # must never raise

# agent.py  (Person 2)
run_agent(user_input: str, history: list[dict]) -> str
# history = [{"role": "user" | "assistant", "content": "..."}]
```

Department names must match **exactly**:
`الطرق والأرصفة` · `صحة البيئة والمنشآت الغذائية` · `النظافة العامة`
Always import them from `storage.DEPARTMENTS` instead of typing them.

---

## 1. Setup (everyone, once)

```bash
git clone https://github.com/strgurl/BALAGHAK.git
cd BALAGHAK

python -m venv venv
source venv/bin/activate            # Mac/Linux
# source venv/Scripts/activate      # Windows (Git Bash)

pip install -r requirements.txt
cp .env.example .env
nano .env                           # put the real OPENAI_API_KEY (ask the team)
```

Check that everything runs:
```bash
python storage.py                   # prints "Reports: 90" and the test results
python generate_data.py             # resets the data after the test
streamlit run app.py                # opens the app in the browser (Ctrl+C to stop)
```

Then create **your** branch:
```bash
git checkout -b rag                 # or: agent / ui / n8n
```

## 2. While working

- Edit **only your own files**.
- Test your file alone: `python rag.py` (every file has a test block at the bottom).
- Save your work often:
  ```bash
  git add rag.py                    # only YOUR files, never "git add ."
  git commit -m "RAG: build FAISS index from guidelines"
  git push -u origin rag            # first push; afterwards just: git push
  ```
- Before committing, if you added test reports: `python generate_data.py` to reset the data.
- Need a new library? Tell the team. Only one person edits `requirements.txt`.

## 3. Getting other people's work into your branch

When someone's branch is merged into `main` and you need it:
```bash
git add <your files> && git commit -m "WIP"      # save your work first
git checkout main
git pull
git checkout rag                                 # your branch
git merge main
```

## 4. Merging (Pull Requests)

**Merge order:** `rag` + `n8n` → `agent` → `ui`
(Each part depends on the ones before it.)

When your part works and your tests pass:
1. Bring `main` into your branch (section 3) and run your tests again.
2. `git push`
3. On GitHub: open the repo → **"Compare & pull request"** (yellow bar) → base: `main`, compare: your branch.
4. Write what you did in one or two lines → **Create pull request**.
5. Tell the team. One other person looks at it quickly → **Merge pull request** → **Confirm merge**.
6. Everyone else: section 3 to get the new `main`.

### If GitHub says "This branch has conflicts"
Usually only happens in shared files (`requirements.txt`, `README.md`).
```bash
git checkout <your-branch>
git pull origin main                 # git shows which files conflict
nano requirements.txt                # keep BOTH sides, delete the <<<<<<< ======= >>>>>>> lines
git add requirements.txt
git commit -m "Resolve conflict with main"
git push
```

## 5. Timeline

| Time | What happens |
|---|---|
| 0:00 – 0:15 | Setup (section 1), everyone reads their guide |
| 0:15 – 3:00 | Parallel work |
| 3:00 | **Checkpoint 1:** merge `rag` and `n8n`. Person 2 pulls main → agent now uses real RAG + real notify |
| 4:00 | **Checkpoint 2:** merge `agent`. Person 3 pulls main → chat now talks to the real agent |
| 4:00 – 5:00 | Merge `ui`. Full-flow test together (Person 4 leads) |
| 5:00 – 6:00 | Fix bugs, rehearse the demo, slides |

## 6. Full-flow test (together, after all merges)

1. `python generate_data.py` (clean data)
2. `streamlit run app.py`
3. User page: «فيه حفرة كبيرة» → the agent asks for the location
4. Answer: «في حطين شارع رابغ» → you get a ticket number, e.g. `RPT-1091`
5. The Telegram group **فريق الطرق** receives it (and the supervisor group if it's urgent)
6. Admin page: the new report appears, the counts went up
7. Change its status to «مغلق» → the table updates

Repeat with one بلاغ for each department and one outside scope («الكهرباء مقطوعة»).
