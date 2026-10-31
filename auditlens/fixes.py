"""The fix menu: the only changes Audit Lens can ever make to the data.

A fix is a small dict:
    {"id": "to_number: Amount", "operation": "to_number",
     "column": " Amount ", "description": "Turn text like $1,250 into numbers"}

Suggestions (by the built-in rules here, or by the AI in suggest.py) only
*choose* fixes from this menu. pandas applies them, and only the ticked ones.
No operation ever removes duplicate rows: duplicates are audit evidence.
"""

import re

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

OPERATIONS = {
    "clean_headers": "Trim extra spaces from column names",
    "drop_empty_rows": "Remove rows where every cell is blank",
    "tidy_text": "Trim extra spaces and make spelling of the same name consistent",
    "to_number": "Turn text like $1,250 or (120) into numbers",
    "standardize_dates": "Make all dates one format (YYYY-MM-DD)",
    "flag_missing": "Highlight blank cells (they are left as they are)",
}
ALL_COLUMNS = "*"

# Order fixes are applied in. Headers go last so the other fixes can still
# find their columns by the original (messy) names.
ORDER = ["drop_empty_rows", "tidy_text", "to_number", "standardize_dates", "flag_missing", "clean_headers"]

MONEY = re.compile(r"^\(?-?\s*[$£€]?\s*-?[\d,]*\.?\d+\s*\)?$")


def make_fix(operation, column, description=None):
    label = column.strip() if column != ALL_COLUMNS else "all columns"
    return {
        "id": f"{operation}: {label}",
        "operation": operation,
        "column": column,
        "description": description or f"{OPERATIONS[operation]} ({label})",
    }


# ---------- helpers ----------

def blank_mask(series):
    """True where a cell is empty or only spaces."""
    return series.isna() | series.astype(str).str.strip().eq("")


def is_text(series):
    return not is_numeric_dtype(series) and not is_datetime64_any_dtype(series)


def _filled(series):
    return series[~blank_mask(series)].astype(str).str.strip()


def parse_number(value):
    """'$1,250.00' -> 1250.0, '(120)' -> -120.0, anything else -> NaN."""
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    if not text:
        return float("nan")
    negative = text.startswith("(") and text.endswith(")")
    text = re.sub(r"[()$£€,\s]", "", text)
    try:
        number = float(text)
    except ValueError:
        return float("nan")
    return -abs(number) if negative else number


def parse_dates(series):
    return pd.to_datetime(series.where(~blank_mask(series)), format="mixed", errors="coerce")


def _date_style(text):
    """A rough 'shape' of a date string, used to spot mixed formats."""
    return re.sub(r"[A-Za-z]+", "a", re.sub(r"\d", "9", text))


def tidy_series(series):
    """Trim and collapse spaces, then use one spelling for names that differ only by case."""
    filled = ~blank_mask(series)
    tidy = series.copy().astype(object)
    tidy[filled] = series[filled].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    keys = tidy[filled].str.lower()
    # For each name, prefer a spelling that isn't all caps or all lower case.
    preferred = {}
    for key, group in tidy[filled].groupby(keys):
        counts = group.value_counts()
        nice = [v for v in counts.index if not (v.isupper() or v.islower())]
        preferred[key] = nice[0] if nice else counts.index[0]
    tidy[filled] = keys.map(preferred)
    return tidy


# ---------- suggestions by built-in rules ----------

def suggest_by_rules(df):
    """Look at the data and suggest fixes from the menu."""
    fixes = []
    if any(c != c.strip() for c in df.columns):
        fixes.append(make_fix("clean_headers", ALL_COLUMNS, "Trim extra spaces from column names"))

    if df.apply(blank_mask).all(axis=1).any():
        fixes.append(make_fix("drop_empty_rows", ALL_COLUMNS, "Remove rows where every cell is blank"))

    for col in df.columns:
        series = df[col]
        name = col.strip()
        values = _filled(series)
        if values.empty:
            continue

        if is_text(series) and values.str.match(MONEY).mean() >= 0.8:
            if values.str.contains(r"[$£€,()\s]").any() or (values != series[values.index]).any():
                fixes.append(make_fix(
                    "to_number", col,
                    f"Turn {name} into numbers: remove $ signs, commas and spaces; (120) becomes −120"))
        elif is_text(series) and values.str.contains(r"\d").mean() >= 0.8 and parse_dates(series).notna().sum() >= 0.8 * len(values):
            styles = set(values.map(_date_style))
            if styles != {"9999-99-99"}:  # already all YYYY-MM-DD: nothing to fix
                reason = f"{len(styles)} different date formats" if len(styles) > 1 else "an unusual date format"
                fixes.append(make_fix(
                    "standardize_dates", col,
                    f"Make all dates in {name} one format (YYYY-MM-DD). Found {reason}"))
        elif is_text(series) and (tidy_series(series)[values.index].astype(str) != series[values.index].astype(str)).any():
            fixes.append(make_fix(
                "tidy_text", col,
                f"Tidy {name}: trim extra spaces and use one spelling for names that differ only by capitals"))

        missing = int(blank_mask(series).sum())
        if missing:
            fixes.append(make_fix(
                "flag_missing", col,
                f"Highlight {missing} blank cell{'s' if missing != 1 else ''} in {name} (left as they are)"))
    return fixes


def changes_data(fix):
    return fix["operation"] != "flag_missing"


# ---------- applying fixes ----------

def apply_fix(df, fix):
    op, col = fix["operation"], fix["column"]
    if col != ALL_COLUMNS and col not in df.columns:
        return df  # unknown column: ignore safely
    out = df.copy()
    if op == "clean_headers":
        out.columns = [c.strip() for c in out.columns]
    elif op == "drop_empty_rows":
        out = out[~out.apply(blank_mask).all(axis=1)]
    elif op == "tidy_text":
        out[col] = tidy_series(out[col])
    elif op == "to_number":
        out[col] = out[col].map(parse_number).astype(float)
    elif op == "standardize_dates":
        out[col] = parse_dates(out[col])
    # flag_missing changes nothing
    return out


def apply_fixes(df, fixes):
    """Apply the given (ticked) fixes in a fixed, safe order."""
    for fix in sorted(fixes, key=lambda f: ORDER.index(f["operation"])):
        df = apply_fix(df, fix)
    return df


def cells_changed(df, fix):
    """True/False table: which cells this fix would change (or flag)."""
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    op, col = fix["operation"], fix["column"]
    if op == "clean_headers":
        return mask
    if op == "drop_empty_rows":
        mask.loc[df.apply(blank_mask).all(axis=1), :] = True
        return mask
    if col not in df.columns:
        return mask
    if op == "flag_missing":
        mask[col] = blank_mask(df[col])
        return mask
    after = apply_fix(df, fix)[col]
    mask[col] = to_display(after).astype(str) != df[col].astype(str)
    mask[col] &= ~blank_mask(df[col])
    return mask


def to_display(series_or_df):
    """Show dates as YYYY-MM-DD and blanks as empty text, for previews."""
    if isinstance(series_or_df, pd.DataFrame):
        return series_or_df.apply(to_display)
    s = series_or_df
    if is_datetime64_any_dtype(s):
        return s.dt.strftime("%Y-%m-%d").fillna("")
    if is_numeric_dtype(s):
        return s.map(lambda v: "" if pd.isna(v) else f"{v:g}" if float(v).is_integer() else f"{v:.2f}")
    return s.astype(object).where(s.notna(), "")
