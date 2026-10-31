"""Work out which columns hold the amounts, dates, customer/vendor and invoice number.

The app decides on its own; the user is never asked (prd.md > Automatic Column Detection).
"""

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from auditlens.fixes import blank_mask

AMOUNT_HINTS = ("amount", "total", "value", "net", "sales", "price", "paid", "payment")
DATE_HINTS = ("date", "posted", "day")
PARTY_HINTS = ("customer", "vendor", "supplier", "client", "payee", "name")
INVOICE_HINTS = ("invoice", "inv", "document", "doc", "ref", "number", "no")


def for_analysis(df):
    """Copy of the cleaned table with tidy text numbers and YYYY-MM-DD dates turned into real types.

    This is strict on purpose: if the user unticked a fix, values like "$1,250"
    stay unreadable and are left out of the maths rather than quietly fixed.
    """
    out = df.copy()
    for col in out.columns:
        s = out[col]
        if is_numeric_dtype(s) or is_datetime64_any_dtype(s):
            continue
        filled = ~blank_mask(s)
        if not filled.any():
            continue
        numbers = pd.to_numeric(s.where(filled), errors="coerce")
        if numbers[filled].notna().mean() >= 0.9:
            out[col] = numbers
            continue
        dates = pd.to_datetime(s.where(filled), format="%Y-%m-%d", errors="coerce")
        if dates[filled].notna().mean() >= 0.9:
            out[col] = dates
    return out


def _hinted(columns, hints):
    for hint in hints:
        for col in columns:
            words = str(col).lower().replace("_", " ").replace("-", " ").split()
            # Short hints like "no" must be a whole word, so "Note" isn't mistaken for "No".
            if hint in words or (len(hint) >= 3 and str(col).lower().startswith(hint)):
                return col
    return None


def _id_like(name, series):
    """A row or invoice number: unique whole numbers that are named like an ID or count up one by one."""
    if _hinted([name], AMOUNT_HINTS):
        return False
    values = series.dropna()
    if len(values) < 2 or not values.is_unique or not (values % 1 == 0).all():
        return False
    counts_up = (values.sort_values().diff().dropna() == 1).all()
    return counts_up or _hinted([name], ("id", "no", "number", "invoice", "ref")) is not None


def find_columns(df):
    numeric = [c for c in df.columns if is_numeric_dtype(df[c]) and not _id_like(c, df[c])]
    dates = [c for c in df.columns if is_datetime64_any_dtype(df[c])]
    text = [c for c in df.columns if c not in numeric and c not in dates and not is_numeric_dtype(df[c])]

    amount = _hinted(numeric, AMOUNT_HINTS)
    if amount is None and numeric:
        amount = max(numeric, key=lambda c: df[c].abs().sum())

    date = _hinted(dates, DATE_HINTS) or (dates[0] if dates else None)
    party = _hinted(text, PARTY_HINTS)
    others = [c for c in df.columns if c not in (amount, date, party)]
    invoice = _hinted(others, INVOICE_HINTS)
    return {"amount": amount, "date": date, "party": party, "invoice": invoice}
