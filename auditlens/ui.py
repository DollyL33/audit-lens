"""Look and feel: CSS and small HTML building blocks for the dark Audit Lens style."""

import html
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.svg"

# Colours from spec.md > Look and Feel
INK = "#eef2f7"
MUTED = "#93a0b4"
LINE = "#26324a"
SURFACE = "#152036"
GREEN = "#4ade80"
ORANGE = "#f59e5b"
BAR = "#4a5b7a"

CSS = f"""
<style>
.block-container {{ padding-top: 3rem; max-width: 1100px; }}
.al-tag {{
  display: inline-block; font-size: .75rem; font-weight: 600; letter-spacing: .05em;
  text-transform: uppercase; color: {MUTED}; border: 1px solid {LINE};
  padding: 3px 10px; border-radius: 999px;
}}
.al-brand {{ display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem; }}
.al-brand svg {{ width: 40px; height: 40px; }}
.al-hero {{
  font-size: 2.8rem; font-weight: 800; line-height: 1.1; letter-spacing: -.02em;
  margin: .6rem 0 .4rem; color: {INK};
}}
.al-hero span {{ display: block; color: {MUTED}; }}
.al-sub {{ color: {MUTED}; font-size: 1.1rem; max-width: 640px; margin-bottom: 1.5rem; }}
.al-section {{ font-size: 1.3rem; font-weight: 700; margin: 1.6rem 0 .4rem; }}
.al-note {{ color: {MUTED}; font-size: .9rem; }}
.al-finding-label {{ font-size: .75rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }}
.al-finding-headline {{ font-size: 1.5rem; font-weight: 800; margin: .2rem 0 .3rem; color: {INK}; }}
.al-question {{
  border-top: 1px solid {LINE}; margin-top: .6rem; padding-top: .7rem; color: {INK};
}}
.al-question b {{ color: {GREEN}; }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def logo_svg():
    return LOGO_PATH.read_text()


def brand():
    """Logo and name, shown at the top of every stage."""
    st.markdown(
        f'<div class="al-brand">{logo_svg()}<span>Audit Lens</span></div>',
        unsafe_allow_html=True,
    )


def hero():
    st.markdown(
        """
        <div class="al-hero">Let your data speak.<span>See it through an auditor's eyes.</span></div>
        <div class="al-sub">Upload a sales or transactions spreadsheet. Audit Lens tidies it up with
        your approval, then runs forensic audit checks and tells you which questions to ask.</div>
        """,
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="al-section">{html.escape(title)}</div>', unsafe_allow_html=True)


def finding_header(label, flagged, headline, sentence):
    """Top of a finding card: coloured uppercase label, big headline, one plain sentence."""
    colour = ORANGE if flagged else GREEN
    st.markdown(
        f"""
        <div class="al-finding-label" style="color:{colour}">{html.escape(label)}</div>
        <div class="al-finding-headline">{html.escape(headline)}</div>
        <div class="al-note">{html.escape(sentence)}</div>
        """,
        unsafe_allow_html=True,
    )


def question(text):
    st.markdown(
        f'<div class="al-question"><b>Question to ask →</b> {html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def benford_chart(table):
    import plotly.graph_objects as go

    colours = [ORANGE if spike else BAR for spike in table["spike"]]
    fig = go.Figure()
    fig.add_bar(
        x=table["digit"], y=table["actual"] * 100, marker_color=colours, name="Your data",
        hovertemplate="First digit %{x}<br>Your data: %{y:.1f}%<extra></extra>",
    )
    fig.add_scatter(
        x=table["digit"], y=table["expected"] * 100, mode="lines+markers", name="Expected (Benford)",
        line=dict(color=GREEN, width=2), hovertemplate="Expected: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=300, margin=dict(l=10, r=10, t=10, b=10), bargap=0.25,
        legend=dict(orientation="h", y=1.1, x=0),
        xaxis=dict(title="First digit", tickmode="linear", dtick=1),
        yaxis=dict(title="% of amounts", gridcolor=LINE),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def highlight(df, mask):
    """Colour the cells where `mask` is True in the warning orange."""
    style = f"background-color: #3a2616; color: {ORANGE};"
    return df.style.apply(lambda _: mask.replace({True: style, False: ""}), axis=None)


def note(text):
    st.markdown(f'<div class="al-note">{html.escape(text)}</div>', unsafe_allow_html=True)
