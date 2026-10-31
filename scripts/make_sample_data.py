"""Generate the MADE-UP sample files used for the demo and the tests.

    python scripts/make_sample_data.py

messy_sales.csv   ~1,200 invoices with messy formats, a few blanks, planted
                  duplicates, and a planted spike of amounts just under a
                  $5,000 approval limit ($4,500-$4,999, so first digit 4).
clean_natural.csv ~1,500 tidy invoices whose amounts follow Benford's Law.

All names and numbers are invented. A fixed random seed means the files
come out identical every time.
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "sample_data"
CUSTOMERS = [
    "Acme Ltd", "Birch Co", "Cedar Supplies", "Delta Foods", "Evergreen Retail",
    "Falcon Logistics", "Granite Builders", "Harbor Traders", "Ivy Wellness",
    "Juniper Tech", "Kestrel Media", "Lotus Imports",
]
PRODUCTS = ["Consulting", "Hardware", "Software licence", "Maintenance", "Training", "Shipping"]
START = date(2025, 1, 1)

N_NATURAL_MESSY = 1090   # natural invoices in the messy file
N_SPIKE = 110            # invoices kept just under $5,000
N_DUPLICATES = 6         # rows copied a second time (same amount, date, customer)
N_CLEAN = 1500


def benford_amounts(rng, n):
    """Amounts spread evenly on a log scale from $10 to $10,000, which follows Benford's Law."""
    return np.round(10 ** rng.uniform(1, 4, n), 2)


def random_dates(rng, n):
    return [START + timedelta(days=int(d)) for d in rng.integers(0, 365, n)]


def build_rows(rng, amounts):
    return pd.DataFrame({
        "Invoice Date": random_dates(rng, len(amounts)),
        "Customer": rng.choice(CUSTOMERS, len(amounts)),
        "Product": rng.choice(PRODUCTS, len(amounts)),
        "Amount": amounts,
    })


def messy_amount(rng, value):
    style = rng.integers(0, 4)
    if style == 0:
        return f"${value:,.2f}"
    if style == 1:
        return f"{value:,.2f}"
    if style == 2:
        return f" {value:.2f} "
    return f"{value:.2f}"


def messy_date(rng, d):
    style = rng.integers(0, 3)
    if style == 0:
        return d.isoformat()                 # 2025-03-14
    if style == 1:
        return d.strftime("%m/%d/%Y")         # 03/14/2025
    return d.strftime("%d %b %Y")             # 14 Mar 2025


def messy_name(rng, name):
    style = rng.integers(0, 5)
    if style == 0:
        return f"  {name.lower()} "
    if style == 1:
        return name.upper()
    if style == 2:
        return name.replace(" ", "  ")
    return name


def make_messy(rng):
    natural = build_rows(rng, benford_amounts(rng, N_NATURAL_MESSY))
    spike = build_rows(rng, np.round(rng.uniform(4500, 4999.99, N_SPIKE), 2))
    df = pd.concat([natural, spike], ignore_index=True).sample(frac=1, random_state=7)
    df = df.reset_index(drop=True)

    # Planted duplicates: same amount, date and customer as an existing row.
    # Their customer name is written messily so they only match after clean-up.
    dupes = df.sample(N_DUPLICATES, random_state=11).copy()
    df = pd.concat([df, dupes], ignore_index=True)
    df["Invoice No"] = [f"INV-{1000 + i}" for i in range(len(df))]
    # A duplicate payment often reuses the invoice number too.
    df.loc[df.index[-N_DUPLICATES:], "Invoice No"] = df.loc[dupes.index, "Invoice No"].values

    out = pd.DataFrame({
        "Invoice No": df["Invoice No"],
        "Invoice Date": [messy_date(rng, d) for d in df["Invoice Date"]],
        "Customer": [messy_name(rng, c) for c in df["Customer"]],
        "Product": df["Product"],
        " Amount ": [messy_amount(rng, v) for v in df["Amount"]],
    })
    out.iloc[-N_DUPLICATES:, out.columns.get_loc("Customer")] = [
        f"  {c.lower()} " for c in df["Customer"].iloc[-N_DUPLICATES:]
    ]

    # A few returns written the accountant's way, in brackets.
    returns = rng.choice(len(out) - N_DUPLICATES, 12, replace=False)
    for i in returns:
        out.iloc[i, out.columns.get_loc(" Amount ")] = f"({rng.uniform(20, 400):.2f})"

    # Some blanks, avoiding the planted duplicates.
    blanks = rng.choice(len(out) - N_DUPLICATES, 10, replace=False)
    out.iloc[blanks[:8], out.columns.get_loc("Invoice Date")] = ""
    out.iloc[blanks[8:], out.columns.get_loc("Customer")] = ""
    return out


def make_clean(rng):
    df = build_rows(rng, benford_amounts(rng, N_CLEAN)).sort_values("Invoice Date")
    df.insert(0, "Invoice No", [f"INV-{5000 + i}" for i in range(len(df))])
    return df


def main():
    rng = np.random.default_rng(42)
    OUT.mkdir(exist_ok=True)
    make_messy(rng).to_csv(OUT / "messy_sales.csv", index=False)
    make_clean(rng).to_csv(OUT / "clean_natural.csv", index=False)
    print(f"Wrote {OUT / 'messy_sales.csv'} and {OUT / 'clean_natural.csv'}")


if __name__ == "__main__":
    main()
