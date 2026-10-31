"""Choose which fixes to suggest: NVIDIA's model first, the built-in rules as backup.

The model only picks from the fix menu (fixes.OPERATIONS); pandas does the
actual changes. If there's no key, the call fails, or the reply makes no
sense, the built-in rules are used. The screen looks the same either way.
"""

import json
import logging
import os
import re

from auditlens import fixes as F

log = logging.getLogger(__name__)

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "meta/llama-3.3-70b-instruct"
TIMEOUT_SECONDS = 15
SAMPLE_ROWS = 20

SYSTEM_PROMPT = f"""You help clean messy spreadsheets for an audit tool.
You may ONLY suggest fixes from this menu (operation: what it does):
{chr(10).join(f"- {op}: {text}" for op, text in F.OPERATIONS.items())}

Rules:
- "clean_headers" and "drop_empty_rows" use column "*". Every other fix names one column exactly as written.
- Suggest a fix only if the sample shows that problem. Never suggest removing duplicates.
- Reply with JSON only: an array of objects with keys "operation", "column", "description".
- "description" is one short plain-English sentence for a business user. Do not mention AI."""


def get_api_key():
    """The NVIDIA key from .env / the environment, or from Streamlit secrets when deployed."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("NVIDIA_API_KEY", "")).strip() or None
    except Exception:
        return None


def describe(df):
    """The small sample sent to the model: a summary of each column plus the first rows."""
    lines = ["Columns:"]
    for col in df.columns:
        s = df[col]
        blanks = int(F.blank_mask(s).sum())
        examples = s.dropna().astype(str).drop_duplicates().head(5).tolist()
        lines.append(f"- {col!r}: {blanks} blank cells; examples: {examples}")
    lines.append(f"\nFirst {SAMPLE_ROWS} rows (CSV):")
    lines.append(df.head(SAMPLE_ROWS).to_csv(index=False))
    return "\n".join(lines)


def parse_reply(text):
    """Pull the JSON array out of the reply, even if it's wrapped in ```json fences."""
    match = re.search(r"\[.*\]", text or "", re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [i for i in items if isinstance(i, dict)]


def _fits_data(df, op, col):
    """Guard against suggestions that would damage the data, e.g. turning names into numbers."""
    if op not in ("to_number", "standardize_dates"):
        return True
    values = df[col][~F.blank_mask(df[col])]
    if values.empty:
        return False
    if op == "to_number":
        return values.map(F.parse_number).notna().mean() >= 0.8
    return F.parse_dates(values).notna().mean() >= 0.8


def validate(items, df):
    """Keep only real menu operations on real columns that fit the data."""
    by_stripped = {str(c).strip(): c for c in df.columns}
    fixes, seen = [], set()
    for item in items:
        op = item.get("operation")
        if op not in F.OPERATIONS:
            continue
        if op in ("clean_headers", "drop_empty_rows"):
            col = F.ALL_COLUMNS
        else:
            raw = item.get("column")
            col = raw if raw in df.columns else by_stripped.get(str(raw).strip())
            if col is None or not _fits_data(df, op, col):
                continue
        description = str(item.get("description") or "").strip()[:160]
        if not description or re.search(r"\bAI\b", description):
            description = None
        fix = F.make_fix(op, col, description)
        if fix["id"] not in seen:
            seen.add(fix["id"])
            fixes.append(fix)
    return fixes


def ask_model(df, key, client=None):
    if client is None:
        from openai import OpenAI
        client = OpenAI(base_url=BASE_URL, api_key=key, timeout=TIMEOUT_SECONDS, max_retries=0)
    reply = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": describe(df)}],
        temperature=0,
        max_tokens=800,
    )
    return reply.choices[0].message.content


def suggest_fixes(df, client=None, key=None):
    """Suggested fixes for this table. Never raises: falls back to the built-in rules."""
    key = key or get_api_key()
    if key or client:
        try:
            fixes = validate(parse_reply(ask_model(df, key, client)), df)
            if fixes:
                log.info("Fixes suggested by %s", MODEL)
                return fixes
            log.warning("Model reply had no usable fixes; using built-in rules")
        except Exception as err:  # network, quota, timeout, bad reply…
            log.warning("Model call failed (%s); using built-in rules", type(err).__name__)
    return F.suggest_by_rules(df)
