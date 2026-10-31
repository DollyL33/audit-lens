"""Look and feel: CSS and small HTML building blocks for the dark Audit Lens style."""

import html

import streamlit as st

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
.al-hero {{
  font-size: 2.8rem; font-weight: 800; line-height: 1.1; letter-spacing: -.02em;
  margin: .6rem 0 .4rem; color: {INK};
}}
.al-hero span {{ display: block; color: {MUTED}; }}
.al-sub {{ color: {MUTED}; font-size: 1.1rem; max-width: 640px; margin-bottom: 1.5rem; }}
.al-section {{ font-size: 1.3rem; font-weight: 700; margin: 1.6rem 0 .4rem; }}
.al-note {{ color: {MUTED}; font-size: .9rem; }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
        <span class="al-tag">Audit Lens</span>
        <div class="al-hero">Let your data speak.<span>See it through an auditor's eyes.</span></div>
        <div class="al-sub">Upload a sales or transactions spreadsheet. Audit Lens tidies it up with
        your approval, then runs forensic audit checks and tells you which questions to ask.</div>
        """,
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="al-section">{html.escape(title)}</div>', unsafe_allow_html=True)


def note(text):
    st.markdown(f'<div class="al-note">{html.escape(text)}</div>', unsafe_allow_html=True)
