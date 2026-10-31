"""The dashboard numbers: number cards, monthly totals, and the biggest transactions.

Each function returns None when the column it needs is missing, so the
dashboard can show a "not available" note instead of an error.
"""

import pandas as pd


def monthly_totals(df, cols):
    """One row per month: month (first day) and total."""
    amount, date = cols["amount"], cols["date"]
    if amount is None or date is None:
        return None
    data = df.dropna(subset=[amount, date])
    if data.empty:
        return None
    months = data[date].dt.to_period("M")
    totals = data.groupby(months)[amount].sum().sort_index()
    return pd.DataFrame({"month": totals.index.to_timestamp(), "total": totals.to_numpy()})


def kpis(df, cols):
    """Total, count, biggest, and the latest month's change vs the month before."""
    amount = cols["amount"]
    if amount is None:
        return None
    values = df[amount].dropna()
    result = {
        "total": float(values.sum()),
        "count": int(values.size),
        "biggest": float(values.max()) if values.size else None,
        "change": None,
    }
    monthly = monthly_totals(df, cols)
    if monthly is not None and len(monthly) >= 2:
        last, prev = monthly.iloc[-1], monthly.iloc[-2]
        if prev["total"] != 0:
            result["change"] = {
                "pct": (last["total"] - prev["total"]) / abs(prev["total"]) * 100,
                "label": f"{last['month']:%b %Y} vs {prev['month']:%b %Y}",
            }
    return result


def top_transactions(df, cols, n=5):
    amount = cols["amount"]
    if amount is None:
        return None
    return df.dropna(subset=[amount]).nlargest(n, amount)
