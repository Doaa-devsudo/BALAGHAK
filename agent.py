"""The agent that talks to the user, classifies the report and saves it.  Owner: Person 2 (Agent)

How it works
------------
This is a tool-calling agent: the LLM (Gemini) decides by itself when to use each tool.

  1. search_guidelines  -> RAG over the 3 department guidelines (rag.py)
                           used to choose the department and the priority
  2. save_report        -> saves the report (storage.py) and notifies the team (notify.py)

The agent asks the user for any missing information (one question at a time),
refuses reports outside the 3 departments, and only saves when everything is complete.

Contract (used by the UI, don't change):
    run_agent(user_input: str, history: list[dict]) -> str
    history = [{"role": "user" | "assistant", "content": "..."}, ...]  (previous messages only)
"""
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

import notify
import rag
import storage

load_dotenv()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_guidelines(complaint: str) -> str:
    """ابحث في أدلة الإدارات عن الإدارة المختصة بالبلاغ وقواعد الأولوية.

    استخدم هذه الأداة دائمًا قبل تحديد الإدارة والأولوية وقبل حفظ البلاغ.

    Args:
        complaint: وصف المشكلة كما كتبه المستخدم (بدون الموقع إن أمكن).
    """
    try:
        result = rag.search_guidelines(complaint)
    except Exception as error:
        print("[agent] search_guidelines failed:", error)
        return "تعذر البحث في الأدلة حاليًا. اعتذر للمستخدم واطلب منه المحاولة لاحقًا."
    return result or "لم يتم العثور على دليل مناسب."


@tool
def save_report(text: str, department: str, neighborhood: str, street: str,
                priority: str, facility: str = "") -> str:
    """احفظ البلاغ بعد اكتمال جميع المعلومات وبعد استخدام أداة search_guidelines.

    Args:
        text: وصف المشكلة كما كتبه المستخدم.
        department: اسم الإدارة المختصة، ويجب أن يكون واحدًا من:
            "الطرق والأرصفة" أو "صحة البيئة والمنشآت الغذائية" أو "النظافة العامة".
        neighborhood: اسم الحي.
        street: اسم الشارع أو أقرب معلم.
        priority: الأولوية حسب قواعد الدليل، ويجب أن تكون واحدة من: "عاجلة" أو "متوسطة" أو "منخفضة".
        facility: اسم المنشأة (مطعم/بقالة/مخبز...) إذا كان البلاغ عنها، وإلا اتركه فارغًا.
    """
    data = {
        "text": text or "",
        "department": (department or "").strip(),
        "neighborhood": neighborhood or "",
        "street": street or "",
        "priority": (priority or "").strip(),
        "facility": facility or "",
    }
    try:
        report = storage.add_report(data)
    except ValueError as error:
        # Returned to the LLM so it can fix the value and call the tool again
        return f"لم يتم الحفظ: {error}"

    notify.send_to_n8n(report)  # never raises

    return (f"تم الحفظ بنجاح. رقم البلاغ: {report['id']}، "
            f"الإدارة: {report['department']}، الأولوية: {report['priority']}")


TOOLS = [search_guidelines, save_report]


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_departments = "\n".join(f"- {d}" for d in storage.DEPARTMENTS)
_priorities = "، ".join(storage.PRIORITIES)

SYSTEM_PROMPT = f"""أنت «بلاغك»، مساعد يستقبل البلاغات البلدية من المواطنين باللهجة السعودية.
ترد دائمًا بالعربية، بأسلوب مختصر ولطيف.

الإدارات المتاحة فقط:
{_departments}

إذا كان البلاغ خارج اختصاص هذه الإدارات الثلاث (مثل الكهرباء، المياه، المرور، الاتصالات)،
اعتذر بلطف ووضّح أنه خارج نطاق الخدمة، ولا تحفظ البلاغ.

المعلومات المطلوبة قبل الحفظ:
1. وصف المشكلة
2. الحي
3. اسم الشارع أو أقرب معلم
4. اسم المنشأة، فقط إذا كان البلاغ عن مطعم أو بقالة أو مخبز أو أي منشأة غذائية

إذا نقصت معلومة، اسأل عنها بسؤال واحد فقط في كل رسالة. لا تخترع أي معلومة لم يذكرها المستخدم.

خطوات العمل:
1. استخدم أداة search_guidelines دائمًا لتحديد الإدارة المختصة. اقرأ قسم «خارج الاختصاص» في الدليل
   (مثلًا: النفايات في الشارع أمام مطعم تتبع النظافة العامة، وليس صحة البيئة).
2. حدّد الأولوية ({_priorities}) حسب «قواعد الأولوية» في الدليل. لا تخمّن.
3. عند اكتمال المعلومات، استخدم أداة save_report. اكتب اسم الإدارة والأولوية حرفيًا كما في القوائم أعلاه.
4. إذا رجعت save_report بخطأ، صحّح القيمة وحاول مرة أخرى.
5. بعد الحفظ، رد على المستخدم برسالة قصيرة فيها: رقم البلاغ، الإدارة، الأولوية.
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

_agent = None


def _get_agent():
    """Create the agent once (on first use), then reuse it."""
    global _agent
    if _agent is None:
        if not os.getenv("GOOGLE_API_KEY"):
            raise RuntimeError("GOOGLE_API_KEY is missing in .env")
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            temperature=0,
            timeout=60,       # seconds per Gemini call, so it never hangs forever
            max_retries=1,
        )
        _agent = create_agent(model=llm, tools=TOOLS, system_prompt=SYSTEM_PROMPT)
    return _agent


def _content_to_text(content) -> str:
    """Gemini sometimes returns a list of parts instead of a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)


def run_agent(user_input: str, history: list[dict]) -> str:
    """Return the assistant's reply in Arabic."""
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": user_input})
    try:
        result = _get_agent().invoke({"messages": messages})
        reply = _content_to_text(result["messages"][-1].content).strip()
        return reply or "عذرًا، ما فهمت. ممكن توضح البلاغ أكثر؟"
    except Exception as error:
        print("[agent] error:", error)
        if "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error):
            return "الخدمة مشغولة حاليًا، حاول بعد دقيقة."
        if "timeout" in str(error).lower() or "timed out" in str(error).lower():
            return "الخدمة تأخرت في الرد، حاول مرة ثانية."
        return "صار خطأ أثناء معالجة البلاغ، حاول مرة ثانية."


if __name__ == "__main__":
    print("مرحبًا بك في بلاغك. اكتب «خروج» للإنهاء.")
    history = []
    while True:
        msg = input("أنت: ").strip()
        if msg in ("exit", "خروج"):
            break
        if not msg:
            continue
        print("...جاري المعالجة")
        reply = run_agent(msg, history)
        print("بلاغك:", reply)
        history += [{"role": "user", "content": msg}, {"role": "assistant", "content": reply}]
