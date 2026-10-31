"""Benford's Law first-digit test, following Mark Nigrini's forensic analytics methods.

In genuine financial data, about 30.1% of amounts start with 1, 17.6% with 2,
and so on down to 4.6% starting with 9. Big departures can point to invented,
manipulated, or limit-dodging amounts.
"""

import numpy as np
import pandas as pd

DIGITS = np.arange(1, 10)
EXPECTED = np.log10(1 + 1 / DIGITS)  # Benford's expected proportions

MIN_AMOUNT = 10        # Nigrini usually leaves out amounts under 10
MIN_COUNT = 100        # fewer than this: too few to judge
CAUTION_COUNT = 1000   # fewer than this: run it, but read with caution
Z_CRITICAL = 1.96      # 5% significance

# Nigrini's first-digit MAD bands: (upper limit, label, looks normal?)
MAD_BANDS = [
    (0.006, "Close conformity", True),
    (0.012, "Acceptable conformity", True),
    (0.015, "Marginally acceptable conformity", False),
    (float("inf"), "Nonconformity", False),
]


def first_digits(amounts):
    values = pd.Series(amounts, dtype=float).dropna()
    values = values[values >= MIN_AMOUNT]
    # e.g. 4850.25 -> 4.85025 -> 4
    digits = np.floor(values / 10 ** np.floor(np.log10(values))).astype(int)
    return digits.clip(1, 9)


def z_statistic(actual, expected, n):
    """Nigrini's z-statistic, with the continuity correction used only when it's smaller than the gap."""
    gap = np.abs(actual - expected)
    correction = 1 / (2 * n)
    gap = np.where(correction < gap, gap - correction, gap)
    return gap / np.sqrt(expected * (1 - expected) / n)


def conformity(mad):
    for limit, label, normal in MAD_BANDS:
        if mad <= limit:
            return label, normal


def run(amounts):
    """Run the first-digit test.

    Returns a dict with: n, status ("too_few" or "ok"), caution, and when status is "ok":
    table (digit, count, actual, expected, z, spike), mad, label, normal.
    """
    digits = first_digits(amounts)
    n = len(digits)
    result = {"n": n, "status": "ok", "caution": MIN_COUNT <= n < CAUTION_COUNT}
    if n < MIN_COUNT:
        result["status"] = "too_few"
        return result

    counts = digits.value_counts().reindex(DIGITS, fill_value=0).to_numpy()
    actual = counts / n
    z = z_statistic(actual, EXPECTED, n)
    table = pd.DataFrame({
        "digit": DIGITS,
        "count": counts,
        "actual": actual,
        "expected": EXPECTED,
        "z": z,
        "spike": (z > Z_CRITICAL) & (actual > EXPECTED),
    })
    mad = float(np.mean(np.abs(actual - EXPECTED)))
    label, normal = conformity(mad)
    result.update(table=table, mad=mad, label=label, normal=normal)
    return result
