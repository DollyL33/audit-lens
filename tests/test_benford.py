from pathlib import Path

import numpy as np
import pytest

from auditlens import benford, detect
from auditlens.fixes import apply_fixes, suggest_by_rules
from auditlens.loader import load_file

DATA = Path(__file__).resolve().parent.parent / "sample_data"


def analysed(name):
    raw = load_file(DATA / name)
    df = detect.for_analysis(apply_fixes(raw, suggest_by_rules(raw)))
    return df, detect.find_columns(df)


def test_expected_percentages():
    assert benford.EXPECTED[0] == pytest.approx(0.301, abs=0.001)
    assert benford.EXPECTED[8] == pytest.approx(0.046, abs=0.001)
    assert benford.EXPECTED.sum() == pytest.approx(1.0)


def test_first_digits():
    assert list(benford.first_digits([4850.25, 10, 99.9, 1000, 5])) == [4, 1, 9, 1]  # 5 is under 10


def test_mad_bands():
    assert benford.conformity(0.004) == ("Close conformity", True)
    assert benford.conformity(0.010) == ("Acceptable conformity", True)
    assert benford.conformity(0.014)[1] is False
    assert benford.conformity(0.02)[0] == "Nonconformity"


def test_natural_data_looks_normal():
    df, cols = analysed("clean_natural.csv")
    result = benford.run(df[cols["amount"]])
    assert result["normal"]
    assert not result["table"]["spike"].any()


def test_messy_sample_flags_digit_4():
    df, cols = analysed("messy_sales.csv")
    result = benford.run(df[cols["amount"]])
    assert not result["normal"]
    assert list(result["table"].query("spike")["digit"]) == [4]
    assert not result["caution"]


def test_sample_size_rules():
    rng = np.random.default_rng(0)
    assert benford.run(10 ** rng.uniform(1, 4, 80))["status"] == "too_few"
    small = benford.run(10 ** rng.uniform(1, 4, 500))
    assert small["status"] == "ok" and small["caution"]


def test_columns_detected():
    for name in ("messy_sales.csv", "clean_natural.csv"):
        _, cols = analysed(name)
        assert cols == {"amount": "Amount", "date": "Invoice Date", "party": "Customer", "invoice": "Invoice No"}


def test_small_whole_number_amounts_are_not_mistaken_for_ids():
    import pandas as pd
    df = detect.for_analysis(pd.DataFrame({"Amount": ["12", "250", "3100"], "Customer": ["A", "B", "A"]}))
    assert detect.find_columns(df)["amount"] == "Amount"
    ids = detect.for_analysis(pd.DataFrame({"Row": ["1", "2", "3"], "Value": ["5.5", "7", "9"]}))
    assert detect.find_columns(ids)["amount"] == "Value"
