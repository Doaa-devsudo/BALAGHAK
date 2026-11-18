"""Storage layer: the only module that reads/writes data/reports.json."""
import json
from datetime import datetime
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "reports.json"

DEPARTMENTS = ["الطرق والأرصفة", "صحة البيئة والمنشآت الغذائية", "النظافة العامة"]
PRIORITIES = ["عاجلة", "متوسطة", "منخفضة"]
STATUSES = ["جديد", "قيد المعالجة", "مغلق"]


def load_reports() -> list[dict]:
    """Return all reports. Returns an empty list if the file doesn't exist yet."""
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_all(reports: list[dict]) -> None:
    """Overwrite the file with the given list of reports."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


def next_id(reports: list[dict]) -> str:
    """Return the next report ID, e.g. RPT-1091."""
    if not reports:
        return "RPT-1001"
    largest = max(int(r["id"].split("-")[1]) for r in reports)
    return f"RPT-{largest + 1}"


def add_report(data: dict) -> dict:
    """Validate, add id/status/created_at, save, and return the new report.

    `data` must contain: text, department, neighborhood, street, priority.
    `facility` is optional (restaurants/shops only).
    """
    required = ["text", "department", "neighborhood", "street", "priority"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    if data["department"] not in DEPARTMENTS:
        raise ValueError(f"Invalid department '{data['department']}'. Must be one of {DEPARTMENTS}")
    if data["priority"] not in PRIORITIES:
        raise ValueError(f"Invalid priority '{data['priority']}'. Must be one of {PRIORITIES}")

    reports = load_reports()
    report = {
        "id": next_id(reports),
        "text": data["text"].strip(),
        "department": data["department"],
        "neighborhood": data["neighborhood"].strip(),
        "street": data["street"].strip(),
        "facility": data.get("facility", "").strip(),
        "priority": data["priority"],
        "status": "جديد",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    reports.append(report)
    save_all(reports)
    return report


def update_status(report_id: str, new_status: str) -> bool:
    """Change a report's status. Returns False if the ID isn't found."""
    if new_status not in STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {STATUSES}")

    reports = load_reports()
    for r in reports:
        if r["id"] == report_id:
            r["status"] = new_status
            save_all(reports)
            return True
    return False


if __name__ == "__main__":
    # Quick manual test. Rerun generate_data.py afterwards to reset the data.
    print("Reports:", len(load_reports()))

    new = add_report({
        "text": "فيه حفرة كبيرة في شارع رابغ",
        "department": "الطرق والأرصفة",
        "neighborhood": "حطين",
        "street": "شارع رابغ",
        "priority": "عاجلة",
    })
    print("Added:", new)

    print("Update status:", update_status(new["id"], "قيد المعالجة"))
    print("Update unknown ID:", update_status("RPT-0000", "مغلق"))

    try:
        add_report({**new, "department": "الطرق"})
    except ValueError as e:
        print("Expected error:", e)
