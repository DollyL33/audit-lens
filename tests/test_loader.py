from pathlib import Path

import pandas as pd
import pytest

from auditlens.loader import LoadError, load_file

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "messy_sales.csv"


def test_reads_csv_as_text():
    df = load_file(SAMPLE)
    assert len(df) > 1000
    assert "Invoice No" in df.columns
    # Messy values are kept exactly as written until a fix is approved.
    assert df[" Amount "].astype(str).str.contains(r"\$").any()


def test_reads_xlsx(tmp_path):
    path = tmp_path / "book.xlsx"
    pd.DataFrame({"Amount": [1, 2], "Customer": ["A", "B"]}).to_excel(path, index=False)
    df = load_file(path)
    assert list(df.columns) == ["Amount", "Customer"]


def test_rejects_other_file_types(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello")
    with pytest.raises(LoadError, match="CSV and Excel"):
        load_file(path)


def test_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(LoadError):
        load_file(path)
