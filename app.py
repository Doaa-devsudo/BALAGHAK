"""Streamlit entry point.  Owner: Person 3 (UI)

Run with:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="بلاغك", page_icon="📢", layout="wide")

st.html("""
<style>
    .stApp { direction: rtl; }
    [data-testid="stHeader"] { direction: ltr; }
    [data-testid="stChatMessage"], [data-testid="stMetric"] { text-align: right; }
    [data-testid="stChatInput"] textarea { direction: rtl; }
    .balaghak-hero {
        padding: clamp(1.25rem, 4vw, 2.75rem);
        margin-bottom: 1rem;
        border-radius: 1.5rem;
        background: #104845;
        color: #f5fffb;
    }
    .balaghak-hero h1 {
        color: inherit;
        font-size: clamp(1.9rem, 5vw, 3rem);
        padding: 0;
        margin: .4rem 0;
    }
    .balaghak-hero p { color: #def7ee; margin: 0; }
    .balaghak-hero .hero-icon {
        display: inline-grid;
        place-items: center;
        width: 3rem;
        height: 3rem;
        background: #ffffff24;
        border: 1px solid #ffffff44;
        border-radius: 1rem;
        font-size: 1.6rem;
    }
    .balaghak-hero .hero-emblem {
        background: #fff;
        padding: .4rem;
        object-fit: contain;
    }
</style>
""")

st.sidebar.title("📢 بلاغك")
st.sidebar.caption("☀️ 🌙 لتغيير المظهر، افتح ⋮ ثم اختر Light أو Dark.")

pages = st.navigation([
    st.Page("pages_/user_chat.py", title="تقديم بلاغ", icon="💬"),
    st.Page("pages_/admin_dashboard.py", title="لوحة المشرف", icon="📊"),
])
pages.run()
