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
