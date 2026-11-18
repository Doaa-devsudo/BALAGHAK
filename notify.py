"""Send new reports to n8n.  Owner: Person 4 (n8n)

STUB: only prints. Replace the body with a real requests.post to N8N_WEBHOOK_URL.
Do NOT change the function name or signature.
"""


def send_to_n8n(report: dict) -> None:
    """Send the report to the n8n webhook.

    Must NEVER raise: if n8n is down, print a warning and return,
    so the report is still saved.

    STUB: prints only.
    TODO: load N8N_WEBHOOK_URL from .env (python-dotenv), requests.post(url, json=report, timeout=5)
          inside try/except.
    """
    print(f"[notify stub] would send {report.get('id')} to n8n")


if __name__ == "__main__":
    send_to_n8n({"id": "RPT-TEST", "department": "الطرق والأرصفة", "priority": "عاجلة",
                 "neighborhood": "حطين", "street": "شارع رابغ", "text": "بلاغ تجريبي"})
