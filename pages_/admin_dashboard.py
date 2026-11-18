"""Admin dashboard.  Owner: Person 3 (UI)

STUB: shows the reports table. storage.py is real, so this already uses real data.
TODO: filters, metrics, charts, repeated reports, report detail + suggested action
      (rag.get_guideline), status update (storage.update_status).
"""
import pandas as pd
import streamlit as st

from storage import load_reports

st.title("لوحة المشرف")

df = pd.DataFrame(load_reports())
st.write(f"عدد البلاغات: {len(df)}")
st.dataframe(df, use_container_width=True)
