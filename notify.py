"""Send new reports to n8n.  Owner: Person 4 (n8n)"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_to_n8n(report: dict) -> None:
    """Send the report to the n8n webhook. Never raises."""
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        print("[notify] N8N_WEBHOOK_URL is not set in .env, skipping")
        return
    try:
        response = requests.post(url, json=report, timeout=5)
        response.raise_for_status()
        print(f"[notify] sent {report.get('id')} to n8n")
    except Exception as e:
        print(f"[notify] could not send {report.get('id')} to n8n: {e}")


if __name__ == "__main__":
    send_to_n8n({
        "id": "RPT-TEST",
        "text": "فيه حفرة كبيرة قريب المدرسة",
        "department": "الطرق والأرصفة",
        "neighborhood": "حطين",
        "street": "شارع رابغ",
        "facility": "",
        "priority": "عاجلة",
        "status": "جديد",
        "created_at": "2026-11-18 19:30",
    })