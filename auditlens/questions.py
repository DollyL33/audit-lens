"""The 'Question to ask' at the end of each finding: an auditor's next step.

Fixed templates, so the wording is predictable.
"""


def benford(result):
    if result["status"] == "too_few":
        return "Collect a larger set of transactions (at least 100) before drawing conclusions from Benford's Law."
    spikes = result["table"][result["table"]["spike"]]
    if result["normal"] and spikes.empty:
        return "No unusual pattern. Keep this result as a baseline to compare against next period's data."
    if spikes.empty:
        return ("The overall digit pattern drifts from what natural data looks like. "
                "Which sources, people or periods could explain it?")
    top = spikes.assign(ratio=spikes["actual"] / spikes["expected"]).sort_values("ratio").iloc[-1]
    d = int(top["digit"])
    limit = (d + 1) * 1000
    return (f"Amounts starting with {d} appear {top['ratio']:.1f}× as often as expected. "
            f"Are amounts being kept just under an approval limit, such as ${limit:,}?")


def duplicates(groups, keys_label):
    if groups.empty:
        return "None found. Re-run this check on each new period's data."
    rows = int(groups["times"].sum())
    return (f"{len(groups)} sets of transactions ({rows} rows) share the same {keys_label}. "
            "Were any of these paid or recorded twice?")
