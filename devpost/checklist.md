---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [x] **1. You can upload a file and see it on the dark Audit Lens page**
  Becomes usable: `streamlit run app.py` opens a dark-themed page with the Audit Lens headline and an upload box; uploading the sample CSV (or any CSV/Excel) shows the first rows as a table; a wrong file type shows a friendly message; "Analyse another file" goes back to the start.
  Why now: Proves the whole setup end to end: Python 3.14 compatibility (the spec's first thing to verify), libraries, the dark theme, reading files, and the stage-by-stage page. It also creates the made-up sample data every later slice tests against.
  PRD ref: `prd.md > Upload`, `prd.md > Screens and Layout`, `prd.md > Look and Feel`
  Spec ref: `spec.md > Stack`, `spec.md > Where It Runs and How Someone Tries It`, `spec.md > App Shell and Stages (app.py)`, `spec.md > Loader (auditlens/loader.py)`, `spec.md > Screen Pieces (auditlens/ui.py)`, `spec.md > Look and Feel`, `spec.md > File Structure`
  Build: Create a virtual environment and `requirements.txt` (falling back to Python 3.12 if 3.14 fails); `.streamlit/config.toml` theme; `auditlens/ui.py` CSS and hero; `auditlens/loader.py`; `app.py` with session-state stages and reset; `scripts/make_sample_data.py` generating `sample_data/messy_sales.csv` (~1,200 rows: mixed date formats, "$1,250"-style amounts, messy names, a few blanks, planted duplicates, a planted spike of amounts between $4,500 and $4,999) and `sample_data/clean_natural.csv`; `.env.example`.
  Verify (mechanical): `pip install -r requirements.txt` succeeds; `python scripts/make_sample_data.py` writes both files; `pytest tests/test_loader.py` reads CSV and XLSX and rejects a .txt file; `streamlit run app.py --server.headless true` starts and `curl localhost:8501` returns 200 with no errors in the log.
  Learner check: Run `streamlit run app.py`, look at the first screen, upload `sample_data/messy_sales.csv`, and say whether the dark look and headline feel right. Then try uploading a non-spreadsheet file.
  Commit: `Scaffold Audit Lens: dark upload page with file preview`

- [x] **2. You can review suggested fixes with tick boxes and approve them**
  Becomes usable: After upload, the app lists suggested fixes (from the built-in rules), highlights the messy cells, shows a before/after preview that follows the tick boxes, and "Approve & build dashboard" moves to a placeholder dashboard showing the cleaned table.
  Why now: The audit findings depend on clean amounts and dates, and duplicates must be caught after tidying. The rule-based suggester is also the backup the AI will rely on later, so it has to exist first.
  PRD ref: `prd.md > Spot the Mess and Suggested Fixes`, `prd.md > Review and Approve`, `prd.md > States and Boundaries` (nothing to clean)
  Spec ref: `spec.md > Fix Menu (auditlens/fixes.py)`, `spec.md > Data Model`, `spec.md > The Core Journey Through the System` (steps 3–4)
  Build: `auditlens/fixes.py`: the six-operation fix menu, `suggest_by_rules`, `apply_fixes`, `cells_changed`. Review stage in `app.py` with tick boxes, highlighted preview, and before/after; "Your data looks clean" path.
  Verify (mechanical): `pytest tests/test_fixes.py`: the messy sample gets ≥ 3 relevant fixes; `to_number` turns "$1,250" into 1250 and "(120)" into −120; dates become one format; an unticked fix is not applied; no fix removes duplicate rows; a clean file gets no changing fixes. App restarts cleanly.
  Learner check: Upload the messy sample, look at the suggested fixes and highlighted cells, untick one fix and watch the "after" row change back, then approve.
  Commit: `Add suggested fixes with tick-box review and before/after preview`

- [x] **3. You see Benford's Law and duplicate findings with questions to ask**
  Becomes usable: The dashboard shows the Benford's first-digit chart (actual vs. expected, spikes highlighted) with Nigrini's MAD verdict, and the same-same-same duplicates list, each in a finding card that ends with a "Question to ask". On the messy sample, digit 4 is flagged and the planted duplicates are listed.
  Why now: This is the unique kernel, an auditor's eye on the data, so it comes as soon as clean data exists. It's also where your feedback matters most before the rest is built.
  PRD ref: `prd.md > Audit Finding: Benford's Law`, `prd.md > Audit Finding: Duplicates`, `prd.md > Questions to Ask`, `prd.md > Automatic Column Detection`
  Spec ref: `spec.md > Benford's Law Test (auditlens/benford.py)`, `spec.md > Duplicates Test (auditlens/duplicates.py)`, `spec.md > Questions to Ask (auditlens/questions.py)`, `spec.md > Column Finder (auditlens/detect.py)`, `spec.md > Screen Pieces (auditlens/ui.py)`
  Build: `detect.py`, `benford.py` (expected %, z with continuity correction, MAD bands, sample-size rules), `duplicates.py`, `questions.py`; finding cards and the Benford chart in `ui.py`; dashboard stage in `app.py`.
  Verify (mechanical): `pytest tests/test_benford.py tests/test_duplicates.py`: expected percentages are correct; `clean_natural.csv` gets close/acceptable conformity; the messy sample after fixes gets marginal/nonconformity with digit 4 flagged; N < 100 is skipped and 100–999 is labelled caution; all planted duplicates are found, including ones that differed only by spacing/case before cleaning. Detect picks the correct columns on both samples.
  Learner check: Upload the messy sample, approve the fixes, and read the Benford's and duplicates cards as an auditor would. Do the verdicts and questions make sense to you? Then try `clean_natural.csv` and see it called normal.
  Commit: `Add Benford's Law and same-same-same duplicate findings`

- [x] **4. You see the number cards, monthly comparison, and biggest transactions**
  Becomes usable: Above the findings, the dashboard shows 4 number cards (total, count, biggest, change vs. last month), a monthly comparison chart, and the top 5 transactions. Files missing a date or amount column show "not available" notes instead of errors.
  Why now: Completes the dashboard around the kernel and handles the "show what it can" states.
  PRD ref: `prd.md > Dashboard: Number Cards and Comparison`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Metrics (auditlens/metrics.py)`, `spec.md > Screen Pieces (auditlens/ui.py)`, `spec.md > Important Failure Modes`
  Build: `metrics.py`; KPI cards and the monthly chart in `ui.py`; dashboard layout order per the PRD; missing-column notes; "nothing to analyse" message.
  Verify (mechanical): `pytest tests/test_metrics.py`: card values match pandas totals computed separately; one bar per month; top 5 sorted descending; a file without dates returns `None` for the comparison; a file with no numbers produces the "nothing to analyse" path. App restarts cleanly.
  Learner check: Run the messy sample through to the dashboard and check that the cards and monthly chart look right. Then upload a file with no date column and see what the app does.
  Commit: `Add number cards, monthly comparison, and top transactions`

- [ ] **5. Suggestions come from NVIDIA's AI behind the scenes, with automatic fallback**
  Becomes usable: With `NVIDIA_API_KEY` in `.env` (or Streamlit secrets), the suggested fixes come from the NVIDIA model; without a key, or on any error, the built-in rules are used and the screen looks the same. No "AI" wording anywhere. README explains how to run it.
  Why now: An enhancement on top of a working app. Because the fallback already exists, a problem here can never break the demo.
  PRD ref: `prd.md > Spot the Mess and Suggested Fixes`, `prd.md > Look and Feel` (no AI wording)
  Spec ref: `spec.md > Suggester (auditlens/suggest.py)`, `spec.md > NVIDIA API (optional at runtime)`, `spec.md > Important Failure Modes`
  Build: `auditlens/suggest.py` with the OpenAI-compatible NVIDIA client, prompt listing the fix menu, JSON validation, 15 s timeout, fallback; wire into `app.py`; read the key from env or `st.secrets`; `README.md`.
  Verify (mechanical): `pytest tests/test_suggest.py`: invalid or unknown operations and columns are dropped; garbage replies and a missing key fall back to rules. If the learner has added a key: one live call on the messy sample returns ≥ 1 valid fix. `grep -ri "\bAI\b"` over `app.py` and `auditlens/ui.py` finds no user-visible text.
  Learner check: (If you have a key) put it in `.env`, upload the messy sample, and compare the suggested fixes with before. Then remove the key and confirm the app still works the same.
  Commit: `Add NVIDIA-powered fix suggestions with rule-based fallback`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 3 (the audit findings), before the rest of the dashboard is built
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence:
Route and stops:
Edit outcome:
Reflection:
Activity mode:

## Revisions
- Added an Audit Lens logo (magnifying glass with a mini Benford chart and one orange spike) shown at the top of every stage — the learner asked for a logo after slice 1.
- `tidy_text` keeps the most common properly-capitalised spelling of each name instead of forcing Title Case — Title Case would have damaged codes like "INV-1000" ("Inv-1000"). Internal change; same behavior for the learner.
- The date fix is suggested only when date formats are mixed or non-standard, and the dashboard will read already-tidy text dates/numbers itself — the clean sample file was getting a "fix" that changed nothing visible.
- Column finder treats whole-number columns as IDs only when they count up by one or are named like an ID — a tiny file's real amounts were being mistaken for IDs. Short name hints ("no") must be whole words so "Note" isn't read as an invoice number.
- Early checkpoint (after slice 3): learner said "looks good" and wants to grow it into a fuller Nigrini fraud-analytics dashboard later; extra Nigrini tests stay on the Later list, not in this PoC.
