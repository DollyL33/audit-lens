from pathlib import Path

import pandas as pd

from auditlens import detect, duplicates
from auditlens.fixes import apply_fixes, suggest_by_rules
from auditlens.loader import load_file

DATA = Path(__file__).resolve().parent.parent / "sample_data"


def analysed(name, fixed=True):
    raw = load_file(DATA / name)
    clean = apply_fixes(raw, suggest_by_rules(raw)) if fixed else raw
    df = detect.for_analysis(clean)
    return df, detect.find_columns(df)


def test_finds_all_planted_duplicates():
    df, cols = analysed("messy_sales.csv")
    keys, groups = duplicates.find(df, cols)
    assert keys == ["Amount", "Invoice Date", "Customer"]
    assert len(groups) == 6
    assert (groups["times"] == 2).all()


def test_duplicates_hidden_by_messy_names_need_the_clean_up():
    # The planted copies have names like "  ivy wellness ", so before the
    # tidy-up they don't match; after it they do.
    raw = load_file(DATA / "messy_sales.csv")
    fixes = [f for f in suggest_by_rules(raw) if f["operation"] != "tidy_text"]
    df = detect.for_analysis(apply_fixes(raw, fixes))
    _, groups = duplicates.find(df, detect.find_columns(df))
    assert len(groups) < 6


def test_clean_file_has_no_duplicates():
    df, cols = analysed("clean_natural.csv")
    _, groups = duplicates.find(df, cols)
    assert groups.empty


def test_falls_back_to_identical_rows_without_key_columns():
    df = pd.DataFrame({"Amount": [5.0, 5.0, 7.0], "Note": ["a", "a", "b"]})
    keys, groups = duplicates.find(df, detect.find_columns(df))
    assert keys == []
    assert len(groups) == 1
