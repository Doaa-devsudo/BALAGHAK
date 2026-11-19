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
from langchain.agents.middleware import ModelRetryMiddleware
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

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

# Gemini is sometimes busy (503 UNAVAILABLE) or too slow (504 DEADLINE_EXCEEDED).
# These are temporary, so we retry each model call. The retry is per model call,
# NOT around the whole agent, so a report that was already saved is never saved twice.
_TEMPORARY_ERRORS = ("503", "504", "UNAVAILABLE", "DEADLINE_EXCEEDED", "high demand",
                     "429", "RESOURCE_EXHAUSTED", "timed out", "timeout")


def _is_temporary(error: Exception) -> bool:
    text = str(error)
    return any(marker.lower() in text.lower() for marker in _TEMPORARY_ERRORS)


def _make_llm():
    """Gemini by default. If LLM_BASE_URL is set in .env, use an OpenAI-compatible API instead
    (e.g. OpenRouter, or the endpoint given by the instructors)."""
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if base_url:
        from langchain_openai import ChatOpenAI
        if not os.getenv("LLM_API_KEY"):
            raise RuntimeError("LLM_API_KEY is missing in .env")
        return ChatOpenAI(
            base_url=base_url,
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL"),
            temperature=0,
            timeout=60,
            max_retries=0,  # retries are handled by ModelRetryMiddleware
        )
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is missing in .env")
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        temperature=0,
        timeout=60,
        max_retries=0,  # retries are handled by ModelRetryMiddleware
    )


def _build_agent(checkpointer=None):
    llm = _make_llm()
    retry = ModelRetryMiddleware(
        max_retries=3,          # up to 4 attempts per model call
        retry_on=_is_temporary,
        on_failure="error",     # after the last attempt, raise -> chat_error_message
        initial_delay=2.0,      # wait 2s, 4s, 8s between attempts
        backoff_factor=2.0,
    )
    return create_agent(
        model=llm, tools=TOOLS, system_prompt=SYSTEM_PROMPT,
        middleware=[retry], checkpointer=checkpointer,
    )


def create_chat_agent():
    """Create a graph and checkpoint store owned by one Streamlit session."""
    return _build_agent(checkpointer=InMemorySaver())


def _get_agent():
    """Reuse the stateless agent for callers that supply their own history."""
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


def content_to_text(content) -> str:
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
        reply = content_to_text(result["messages"][-1].content).strip()
        return reply or "عذرًا، ما فهمت. ممكن توضح البلاغ أكثر؟"
    except Exception as error:
        return chat_error_message(error)


def chat_error_message(error: Exception) -> str:
    print("[agent] error:", error)
    if _is_temporary(error):
        return "الخدمة مشغولة حاليًا، حاول بعد دقيقة."
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
