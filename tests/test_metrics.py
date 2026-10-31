from pathlib import Path

import pandas as pd

from auditlens import detect, metrics
from auditlens.fixes import apply_fixes, suggest_by_rules
from auditlens.loader import load_file

DATA = Path(__file__).resolve().parent.parent / "sample_data"


def analysed(raw):
    df = detect.for_analysis(apply_fixes(raw, suggest_by_rules(raw)))
    return df, detect.find_columns(df)


def test_cards_match_pandas_totals():
    df, cols = analysed(load_file(DATA / "messy_sales.csv"))
    k = metrics.kpis(df, cols)
    assert k["total"] == df["Amount"].sum()
    assert k["count"] == df["Amount"].notna().sum()
    assert k["biggest"] == df["Amount"].max()
    monthly = metrics.monthly_totals(df, cols)
    last, prev = monthly["total"].iloc[-1], monthly["total"].iloc[-2]
    assert abs(k["change"]["pct"] - (last - prev) / abs(prev) * 100) < 1e-9
    assert k["change"]["label"] == "Dec 2025 vs Nov 2025"


def test_one_bar_per_month():
    df, cols = analysed(load_file(DATA / "messy_sales.csv"))
    monthly = metrics.monthly_totals(df, cols)
    assert len(monthly) == 12
    assert monthly["month"].is_monotonic_increasing


def test_top_five_sorted_largest_first():
    df, cols = analysed(load_file(DATA / "clean_natural.csv"))
    top = metrics.top_transactions(df, cols)
    assert len(top) == 5
    assert top["Amount"].is_monotonic_decreasing
    assert top["Amount"].iloc[0] == df["Amount"].max()


def test_no_date_column_means_no_comparison():
    df, cols = analysed(pd.DataFrame({"Amount": ["10", "20", "30"], "Customer": ["A", "B", "C"]}))
    assert metrics.monthly_totals(df, cols) is None
    assert metrics.kpis(df, cols)["change"] is None


def test_no_amount_column_means_no_numbers():
    df, cols = analysed(pd.DataFrame({"City": ["Paris", "Oslo"], "Colour": ["red", "blue"]}))
    assert all(v is None for v in cols.values())
    assert metrics.kpis(df, cols) is None
    assert metrics.top_transactions(df, cols) is None
