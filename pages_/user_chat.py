"""Citizen chat with session-local conversation threads and checkpoints."""
from base64 import b64encode
from pathlib import Path
from uuid import uuid4

import streamlit as st

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import START

from agent import chat_error_message, content_to_text, create_chat_agent

emblem_path = Path(__file__).resolve().parents[1] / "assets" / "saudi-emblem.png"
emblem_data = b64encode(emblem_path.read_bytes()).decode("ascii")

st.html(f"""
<section class="balaghak-hero" lang="ar" dir="rtl">
    <img class="hero-icon hero-emblem" src="data:image/png;base64,{emblem_data}"
         alt="شعار المملكة العربية السعودية">
    <h1>أهلًا بك في بلاغك</h1>
    <p>لاحظت مشكلة في حيك؟ صفها لنا واذكر الحي والشارع.</p>
</section>
""")

def new_thread():
    thread_id = uuid4().hex
    threads[thread_id] = {"title": f"محادثة {len(threads) + 1}", "checkpoints": {}, "active": None}
    st.session_state.chat_thread = thread_id


threads = st.session_state.setdefault("chat_threads", {})
if not threads:
    new_thread()

with st.sidebar:
    st.button("محادثة جديدة", icon="➕", on_click=new_thread)
    thread_id = st.selectbox(
        "المحادثات",
        options=list(threads),
        format_func=lambda key: threads[key]["title"],
        key="chat_thread",
    )
    thread = threads[thread_id]
    checkpoints = thread["checkpoints"]
    if checkpoints:
        selected = st.selectbox(
            "نقاط الحفظ",
            options=list(reversed(checkpoints)),
            format_func=lambda key: checkpoints[key]["label"],
            key=f"checkpoint_{thread_id}",
        )
        if st.button("الرجوع إلى نقطة الحفظ", icon="↩️"):
            thread["active"] = selected
    st.caption("تُحفظ المحادثات خلال جلسة التصفح الحالية.")

active = thread["active"]
graph = st.session_state.get("chat_graph")
config = (
    checkpoints[active]["config"]
    if active is not None
    else {"configurable": {"thread_id": thread_id}}
)
messages = []
if active is not None:
    if active != next(reversed(checkpoints)):
        st.info(
            "يمكنك المتابعة من هذه النقطة برسالة جديدة. البلاغات المرسلة سابقًا تبقى محفوظة.",
            icon="↩️",
        )
    messages = graph.get_state(config).values["messages"]
for message in messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.write(content_to_text(message.content))
    elif isinstance(message, AIMessage) and not message.tool_calls:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content_to_text(message.content) or "عذرًا، ممكن توضّح البلاغ أكثر؟")

if not messages:
    st.info("مثال: توجد حفرة في شارع رابغ بحي حطين.", icon="💡")

if prompt := st.chat_input("اكتب بلاغك هنا..."):
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
    try:
        if graph is None:
            graph = create_chat_agent()
            st.session_state.chat_graph = graph
        if active is None:
            config = graph.update_state(config, {"messages": []}, as_node=START)
            initial_id = config["configurable"]["checkpoint_id"]
            checkpoints[initial_id] = {"config": config, "label": "بداية المحادثة"}
            thread["active"] = initial_id
        with st.spinner("جاري تجهيز الرد..."):
            # Pin the parent snapshot so a new message forks from the selected turn.
            graph.invoke({"messages": [HumanMessage(content=prompt)]}, config)
            snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    except Exception as error:
        st.error(chat_error_message(error))
    else:
        checkpoint_id = snapshot.config["configurable"]["checkpoint_id"]
        checkpoints[checkpoint_id] = {
            "config": snapshot.config,
            "label": f"{len(checkpoints)}. {prompt[:50]}",
        }
        thread["active"] = checkpoint_id
        st.rerun()
