"""User chat page.  Owner: Person 3 (UI)

STUB: basic working chat that calls agent.run_agent (currently a stub too).
TODO: polish, "new report" button, etc.
"""
from base64 import b64encode
from pathlib import Path

import streamlit as st

from agent import run_agent

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

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🤖" if m["role"] == "assistant" else "👤"):
        st.write(m["content"])

if not st.session_state.messages:
    st.info("مثال: توجد حفرة في شارع رابغ بحي حطين.", icon="💡")

if prompt := st.chat_input("اكتب بلاغك هنا..."):
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
    reply = run_agent(prompt, st.session_state.messages)
    with st.chat_message("assistant", avatar="🤖"):
        st.write(reply)
    st.session_state.messages += [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": reply},
    ]
