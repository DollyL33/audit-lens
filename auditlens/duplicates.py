"""Nigrini's same-same-same test: transactions with the same amount, date and customer/vendor.

Runs on the cleaned data, so rows that only looked different because of messy
spacing or capitals are caught.
"""

import pandas as pd


def key_columns(cols):
    """Which columns make two rows 'the same'. Empty list = compare every column."""
    if cols["amount"] is None:
        return []
    keys = [cols["amount"]]
    if cols["date"]:
        keys.append(cols["date"])
    second = cols["party"] or cols["invoice"]
    if second:
        keys.append(second)
    return keys if len(keys) > 1 else []


def find(df, cols):
    """Return (keys used, duplicate groups as a DataFrame sorted by count then amount)."""
    keys = key_columns(cols)
    subset = keys or list(df.columns)
    data = df.dropna(subset=subset) if keys else df
    repeated = data[data.duplicated(subset=subset, keep=False)]
    if repeated.empty:
        return keys, pd.DataFrame()

    groups = repeated.groupby(subset, dropna=False, sort=False)
    summary = groups.size().rename("times").reset_index()
    invoice = cols["invoice"]
    if invoice and invoice not in subset:
        summary[invoice] = groups[invoice].agg(lambda s: ", ".join(sorted(set(s.astype(str))))).values
    sort_by = ["times"] + ([cols["amount"]] if keys else [])
    return keys, summary.sort_values(sort_by, ascending=False, ignore_index=True)
