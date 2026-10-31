"""Audit Lens: upload a messy spreadsheet, review the clean-up, get an audit dashboard.

Run with:  streamlit run app.py
"""

import streamlit as st

from auditlens import ui
from auditlens.loader import LoadError, load_file

st.set_page_config(page_title="Audit Lens", page_icon="🔎", layout="wide")
ui.inject_css()

# Session state is the app's memory for this browser tab (spec.md > Data Model).
state = st.session_state
state.setdefault("stage", "upload")
state.setdefault("upload_key", 0)


def start_over():
    """Forget everything about the current file and go back to the upload screen."""
    key = state.upload_key + 1
    state.clear()
    state.stage = "upload"
    state.upload_key = key  # a new key gives a fresh, empty upload box


def show_upload():
    ui.hero()
    uploaded = st.file_uploader(
        "Drop a CSV or Excel file",
        type=None,  # we check the type ourselves to show a friendly message
        key=f"uploader_{state.upload_key}",
    )
    if uploaded is None:
        return
    try:
        df = load_file(uploaded)
    except LoadError as err:
        st.error(str(err))
        return
    state.file_name = uploaded.name
    state.raw_df = df
    state.stage = "review"
    st.rerun()


def show_review():
    ui.section(f"Your file: {state.file_name}")
    ui.note(f"{len(state.raw_df):,} rows · {len(state.raw_df.columns)} columns. Showing the first 20.")
    st.dataframe(state.raw_df.head(20), width="stretch", hide_index=True)
    st.button("Analyse another file", on_click=start_over)


ui.brand()
if state.stage == "upload":
    show_upload()
elif state.stage == "review":
    show_review()
