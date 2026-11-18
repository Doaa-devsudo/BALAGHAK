"""Streamlit entry point.  Owner: Person 3 (UI)

Run with:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="بلاغك", page_icon="📢", layout="wide")

# Right-to-left layout for Arabic
st.markdown(
    "<style>.stApp, .stMarkdown, .stChatMessage {direction: rtl; text-align: right;}</style>",
    unsafe_allow_html=True,
)

pages = st.navigation([
    st.Page("pages_/user_chat.py", title="تقديم بلاغ", icon="💬"),
    st.Page("pages_/admin_dashboard.py", title="لوحة المشرف", icon="📊"),
])
pages.run()
