"""Read an uploaded CSV or Excel file into a pandas DataFrame."""

from pathlib import Path

import pandas as pd

SUPPORTED = (".csv", ".xlsx", ".xls")
UNSUPPORTED_MESSAGE = (
    "Audit Lens reads CSV and Excel files (.csv, .xlsx, .xls). Please try another file."
)


class LoadError(Exception):
    """Raised when a file can't be read. The message is safe to show the user."""


def load_file(file, name=None):
    """Return the file's first sheet as a DataFrame.

    `file` is a path or a file-like object (like Streamlit's upload).
    CSV cells are kept as text so messy values such as "$1,250" survive
    untouched until the user approves a fix.
    """
    name = name or getattr(file, "name", None) or str(file)
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED:
        raise LoadError(UNSUPPORTED_MESSAGE)

    try:
        if suffix == ".csv":
            df = _read_csv(file)
        else:
            df = pd.read_excel(file, engine="openpyxl" if suffix == ".xlsx" else "xlrd")
    except LoadError:
        raise
    except Exception as err:
        raise LoadError(UNSUPPORTED_MESSAGE) from err

    if df.empty or len(df.columns) == 0:
        raise LoadError("This file looks empty. Please try another file.")
    return df


def _read_csv(file):
    # Try UTF-8 first, then Latin-1, which is common for files saved from Excel.
    for encoding in ("utf-8", "latin-1"):
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            return pd.read_csv(file, dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise LoadError(UNSUPPORTED_MESSAGE)
