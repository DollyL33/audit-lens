"""Audit Lens: upload a messy spreadsheet, review the clean-up, get an audit dashboard.

Run with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from auditlens import fixes as fixes_mod
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
    with st.spinner("Checking your data…"):
        state.fixes = fixes_mod.suggest_by_rules(df)
    state.stage = "review"
    st.rerun()


def ticked_fixes():
    """The fixes whose tick box is on. Each box remembers itself under the key 'fix::<id>'."""
    return [f for f in state.fixes if state.get(f"fix::{f['id']}", True)]


def approve():
    state.clean_df = fixes_mod.apply_fixes(state.raw_df, ticked_fixes())
    state.stage = "dashboard"


def show_review():
    raw = state.raw_df
    ui.section(f"Here's what looks messy in {state.file_name}")
    ui.note(f"{len(raw):,} rows · {len(raw.columns)} columns")

    if not any(fixes_mod.changes_data(f) for f in state.fixes):
        st.success("Your data looks clean. Nothing needs changing.")
        st.button("Build dashboard", type="primary", on_click=approve)
        st.button("Analyse another file", on_click=start_over)
        return

    # Highlight every cell that any suggested fix would change or flag.
    problems = pd.DataFrame(False, index=raw.index, columns=raw.columns)
    for f in state.fixes:
        problems |= fixes_mod.cells_changed(raw, f)
    rows = problems.any(axis=1)
    ui.note(f"{int(problems.values.sum()):,} cells highlighted in {int(rows.sum()):,} rows. "
            "Showing the first 15 rows with problems.")
    preview = raw.index[rows][:15]
    st.dataframe(ui.highlight(raw.loc[preview], problems.loc[preview]), width="stretch", hide_index=True)

    ui.section("Suggested fixes")
    ui.note("Untick anything you don't want changed. The before and after below updates as you go.")
    for f in state.fixes:
        st.checkbox(f["description"], value=True, key=f"fix::{f['id']}")

    ui.section("Before and after")
    after = fixes_mod.apply_fixes(raw, ticked_fixes())
    sample = raw.index[rows & raw.index.isin(after.index)][:6]
    left, right = st.columns(2)
    with left:
        ui.note("Before")
        st.dataframe(raw.loc[sample], width="stretch", hide_index=True)
    with right:
        ui.note("After")
        st.dataframe(fixes_mod.to_display(after.loc[sample]), width="stretch", hide_index=True)

    st.button("Approve & build dashboard", type="primary", on_click=approve)
    st.button("Analyse another file", on_click=start_over)


def show_dashboard():
    ui.section(f"Cleaned data: {state.file_name}")
    ui.note("The audit dashboard arrives in the next steps. For now, here's your cleaned table.")
    st.dataframe(fixes_mod.to_display(state.clean_df.head(20)), width="stretch", hide_index=True)
    st.button("Analyse another file", on_click=start_over)


ui.brand()
if state.stage == "upload":
    show_upload()
elif state.stage == "review":
    show_review()
elif state.stage == "dashboard":
    show_dashboard()
