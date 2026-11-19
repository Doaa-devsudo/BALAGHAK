"""Admin dashboard.  Owner: Person 3 (UI)

STUB: shows the reports table. storage.py is real, so this already uses real data.
TODO: filters, metrics, charts, repeated reports, report detail + suggested action
      (rag.get_guideline), status update (storage.update_status).
"""
import pandas as pd
import streamlit as st

from storage import PRIORITIES, STATUSES, load_reports

st.html("""
<section class="balaghak-hero" lang="ar" dir="rtl">
    <span class="hero-icon" aria-hidden="true">📊</span>
    <h1>لوحة المشرف</h1>
    <p>تابع البلاغات البلدية وراجع الحالات العاجلة.</p>
</section>
""")

reports = load_reports()
total, urgent, closed = st.columns(3)
total.metric("📋 إجمالي البلاغات", len(reports), border=True)
urgent.metric(
    "🚨 البلاغات العاجلة",
    sum(report.get("priority") == PRIORITIES[0] for report in reports),
    border=True,
)
closed.metric(
    "✅ البلاغات المغلقة",
    sum(report.get("status") == STATUSES[-1] for report in reports),
    border=True,
)

st.subheader("سجل البلاغات")
st.dataframe(pd.DataFrame(reports), width="stretch", hide_index=True)
