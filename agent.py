
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

import rag
import storage
import notify

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("مفتاح Google API غير موجود في ملف .env")

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    google_api_key=api_key,
    temperature=0
)

DEPARTMENTS = [
    "الطرق والأرصفة",
    "صحة البيئة والمنشآت الغذائية",
    "النظافة العامة"
]

PRIORITIES = ["عاجلة", "متوسطة", "منخفضة"]


def run_agent(user_input: str, history: list) -> str:
    """Arabic municipal reports assistant."""

    try:
        guidelines = rag.search_guidelines(user_input)

        prompt = f"""
أنت مساعد بلاغك، تستقبل بلاغات المواطنين باللغة العربية.

معلومات البلاغ:
{user_input}

إرشادات الأقسام:
{guidelines}

استخرج المعلومات التالية بصيغة JSON فقط:
text, department, neighborhood, street, priority, facility

الأقسام المتاحة:
{DEPARTMENTS}

الأولويات:
{PRIORITIES}

إذا نقصت معلومة أساسية، اسأل المستخدم عنها ولا تحفظ البلاغ.
لا تخترع معلومات.
إذا اكتملت المعلومات أرجع JSON فقط.
"""

        messages = history + [
            {"role": "user", "content": prompt}
        ]

        response = llm.invoke(messages)
        answer = response.content

        if isinstance(answer, list):
            answer = "".join(
                item.get("text", "") if isinstance(item, dict)
                else str(item)
                for item in answer
            )

        answer = answer.strip().replace("```json", "").replace("```", "")

        if not answer.startswith("{"):
            return answer

        data = json.loads(answer)

        required = [
            "text", "department", "neighborhood",
            "street", "priority"
        ]

        missing = [
            field for field in required
            if not str(data.get(field, "")).strip()
        ]

        if missing:
            return "فضلاً أكمل معلومات البلاغ الناقصة."

        if data["department"] not in DEPARTMENTS:
            return "تعذر تحديد القسم الصحيح، فضلاً وضّح البلاغ."

        if data["priority"] not in PRIORITIES:
            return "تعذر تحديد الأولوية، فضلاً وضّح البلاغ."

        report = storage.add_report(data)

        try:
            notify.send_to_n8n(report)
        except Exception as error:
            print("Notification error:", error)

        return (
            "تم استلام بلاغك بنجاح!\n"
            f"رقم البلاغ: {report.get('id', 'تم الحفظ')}\n"
            f"القسم: {report.get('department')}\n"
            f"الأولوية: {report.get('priority')}"
        )

    except json.JSONDecodeError:
        return "ما قدرت أقرأ بيانات البلاغ، فضلاً أعد صياغته."
    except Exception as error:
        print("Agent error:", error)
        return "حدث خطأ أثناء معالجة البلاغ، حاول مرة ثانية."


if __name__ == "__main__":
    history = []

    print("مرحباً بك في مساعد بلاغك")
    print("اكتب خروج لإنهاء المحادثة")

    while True:
        msg = input("أنت: ").strip()

        if msg.lower() in ["exit", "خروج"]:
            print("تم إنهاء المحادثة.")
            break

        if not msg:
            continue

        reply = run_agent(msg, history)
        print("النظام:", reply)

        history.extend([
            {"role": "user", "content": msg},
            {"role": "assistant", "content": reply}
        ])
        