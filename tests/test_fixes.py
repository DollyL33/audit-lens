from pathlib import Path

import pandas as pd

from auditlens.fixes import apply_fixes, cells_changed, changes_data, parse_number, suggest_by_rules
from auditlens.loader import load_file

DATA = Path(__file__).resolve().parent.parent / "sample_data"


def messy():
    return load_file(DATA / "messy_sales.csv")


def ops(fixes):
    return {(f["operation"], f["column"].strip()) for f in fixes}


def test_messy_sample_gets_relevant_fixes():
    found = ops(suggest_by_rules(messy()))
    assert ("clean_headers", "*") in found
    assert ("to_number", "Amount") in found
    assert ("standardize_dates", "Invoice Date") in found
    assert ("tidy_text", "Customer") in found
    assert ("flag_missing", "Invoice Date") in found
    # Invoice numbers are already consistent and must be left alone.
    assert not any(col == "Invoice No" and op != "flag_missing" for op, col in found)


def test_parse_number():
    assert parse_number("$1,250.00") == 1250.0
    assert parse_number(" 77.46 ") == 77.46
    assert parse_number("(120)") == -120.0
    assert pd.isna(parse_number("n/a"))


def test_applying_all_fixes_cleans_the_data():
    df = messy()
    clean = apply_fixes(df, suggest_by_rules(df))
    assert "Amount" in clean.columns and " Amount " not in clean.columns
    assert clean["Amount"].dtype == float
    assert clean["Invoice Date"].notna().sum() == len(df) - 8  # the 8 planted blanks stay blank
    assert pd.api.types.is_datetime64_any_dtype(clean["Invoice Date"])
    # Messy spellings collapse to one each.
    assert clean["Customer"].dropna().nunique() == 12
    assert "Acme Ltd" in set(clean["Customer"])


def test_unticked_fix_is_not_applied():
    df = messy()
    fixes = [f for f in suggest_by_rules(df) if f["operation"] != "to_number"]
    clean = apply_fixes(df, fixes)
    assert clean["Amount"].astype(str).str.contains(r"\$").any()


def test_no_fix_removes_duplicates():
    df = messy()
    clean = apply_fixes(df, suggest_by_rules(df))
    assert len(clean) == len(df)
    assert clean.duplicated(["Invoice Date", "Customer", "Amount"]).sum() >= 6


def test_clean_file_gets_no_changing_fixes():
    df = load_file(DATA / "clean_natural.csv")
    assert not [f for f in suggest_by_rules(df) if changes_data(f)]


def test_cells_changed_highlights_messy_amounts_only():
    df = messy()
    fix = next(f for f in suggest_by_rules(df) if f["operation"] == "to_number")
    mask = cells_changed(df, fix)
    amounts = df[" Amount "]
    assert mask[" Amount "][amounts.str.contains(r"\$", na=False)].all()
    assert not mask["Customer"].any()
