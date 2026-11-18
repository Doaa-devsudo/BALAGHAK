"""User chat page.  Owner: Person 3 (UI)

STUB: basic working chat that calls agent.run_agent (currently a stub too).
TODO: polish, "new report" button, etc.
"""
import streamlit as st

from agent import run_agent

st.title("تقديم بلاغ")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if prompt := st.chat_input("اكتب بلاغك هنا..."):
    with st.chat_message("user"):
        st.write(prompt)
    reply = run_agent(prompt, st.session_state.messages)
    with st.chat_message("assistant"):
        st.write(reply)
    st.session_state.messages += [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": reply},
    ]
