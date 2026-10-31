"""Audit Lens: upload a messy spreadsheet, review the clean-up, get an audit dashboard.

Run with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from auditlens import benford, detect, duplicates, metrics, questions, ui
from auditlens import fixes as fixes_mod
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
    df = detect.for_analysis(state.clean_df)
    cols = detect.find_columns(df)

    ui.section(f"Audit dashboard: {state.file_name}")
    found = [f"{label}: {cols[key]}" for key, label in
             [("amount", "Amounts"), ("date", "Dates"), ("party", "Customer/vendor"), ("invoice", "Invoice")]
             if cols[key]]
    ui.note(f"{len(df):,} rows · " + (" · ".join(found) if found else "No amount, date or name columns recognised"))

    if not found:
        st.info("We couldn't find amounts, dates or names to analyse in this file. "
                "Below is the one check that works on any table: looking for repeated rows.")
    else:
        show_overview(df, cols)

    ui.section("Audit findings")
    show_benford(df, cols)
    show_duplicates(df, cols)
    st.button("Analyse another file", on_click=start_over)


def show_overview(df, cols):
    numbers = metrics.kpis(df, cols)
    if numbers is None:
        ui.note("Number cards, the monthly comparison and Benford's Law need a column of amounts, "
                "and this file doesn't seem to have one.")
        return

    change = numbers["change"]
    ui.kpi_cards([
        ("Total amount", f"{numbers['total']:,.0f}", None, True),
        ("Transactions", f"{numbers['count']:,}", None, True),
        ("Biggest transaction", f"{numbers['biggest']:,.0f}" if numbers["biggest"] is not None else "–", None, True),
        ("vs last month", f"{abs(change['pct']):.1f}%" if change else "–",
         change["label"] if change else "Needs dates", (change["pct"] >= 0) if change else None),
    ])

    ui.section("Monthly comparison")
    monthly = metrics.monthly_totals(df, cols)
    if monthly is None:
        ui.note("No date column found, so the monthly comparison isn't available.")
    else:
        ui.monthly_chart(monthly)

    ui.section("Biggest transactions")
    st.dataframe(fixes_mod.to_display(metrics.top_transactions(df, cols)), width="stretch", hide_index=True)


def show_benford(df, cols):
    with st.container(border=True):
        if cols["amount"] is None:
            ui.finding_header("Benford's Law · not available", False, "No amounts found",
                              "Benford's Law needs a column of amounts, and this file doesn't seem to have one.")
            return
        result = benford.run(df[cols["amount"]])
        if result["status"] == "too_few":
            ui.finding_header("Benford's Law · too few amounts", False, f"{result['n']} amounts",
                              f"Benford's Law needs at least {benford.MIN_COUNT} amounts of 10 or more "
                              "to give a reliable result.")
            ui.question(questions.benford(result))
            return

        spikes = result["table"].query("spike")["digit"].tolist()
        flagged = not result["normal"] or bool(spikes)
        label = f"Benford's Law · {'unusual pattern' if flagged else 'looks normal'}"
        sentence = (f"MAD {result['mad']:.4f} across {result['n']:,} amounts (Nigrini first-digit test). "
                    + (f"Digit {spikes[0]} appears significantly more often than expected." if len(spikes) == 1
                       else f"Digits {', '.join(map(str, spikes))} appear significantly more often than expected."
                       if spikes
                       else "First digits follow the pattern expected of natural financial data."))
        if result["caution"]:
            sentence += f" Small sample (under {benford.CAUTION_COUNT:,} amounts): read with caution."
        ui.finding_header(label, flagged, result["label"], sentence)
        ui.benford_chart(result["table"])
        ui.question(questions.benford(result))


def show_duplicates(df, cols):
    keys, groups = duplicates.find(df, cols)
    keys_label = " + ".join(str(k) for k in keys) if keys else "values in every column"
    with st.container(border=True):
        if groups.empty:
            ui.finding_header("Duplicates · none found", False, "No duplicates",
                              f"No transactions share the same {keys_label} (Nigrini same-same-same test).")
        else:
            ui.finding_header("Duplicates · possible double entries", True,
                              f"{len(groups)} duplicate set{'s' if len(groups) != 1 else ''}",
                              f"Transactions with the same {keys_label} (Nigrini same-same-same test).")
            st.dataframe(fixes_mod.to_display(groups), width="stretch", hide_index=True)
        ui.question(questions.duplicates(groups, keys_label))


ui.brand()
if state.stage == "upload":
    show_upload()
elif state.stage == "review":
    show_review()
elif state.stage == "dashboard":
    show_dashboard()
