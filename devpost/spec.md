---
doc: spec
status: approved
---

# Audit Lens — Technical Spec

## How This Works, In Plain Language
Audit Lens is one Python program built with **Streamlit**, a library that turns a Python script into a web page. When someone opens the page, Streamlit runs `app.py` from top to bottom and draws what it says. Every click (uploading, ticking a box, pressing a button) makes Streamlit **run the script again**. To remember things between those re-runs, such as the uploaded file, the suggested fixes and which stage we're on, the app keeps them in **session state**, a small memory box that lasts while the browser tab is open.

The work is split into small Python files, each with one job:
- **Loader:** reads the uploaded CSV or Excel file into a **DataFrame** (pandas' word for a table in memory, like a spreadsheet sheet).
- **Fix menu:** a fixed list of clean-up actions the app knows how to do, such as "make this date column one format." Only these can ever happen to the data.
- **Suggester:** decides which fixes to suggest. It sends column names and about 20 sample rows to an AI model on **NVIDIA's free API** and asks it to pick from the menu. If there's no key, the call fails, or the reply makes no sense, simple **built-in rules** suggest fixes instead. The user never sees the word "AI."
- **Column finder:** works out which columns hold the amounts, dates, customer/vendor, and invoice number.
- **Audit checks:** the dashboard numbers, the Benford's Law test, and the duplicates test, all following **Mark Nigrini's** forensic analytics methods.
- **Screen pieces:** the dark styling and card layouts.

Why this shape: one program, no database, no accounts. The AI only *chooses* fixes and pandas *applies* them, so every change is predictable, previewable, and controlled by your tick boxes. The audit maths is plain Python you can read and test, and the free hosting deploys it straight from GitHub.

## The Core Journey Through the System
PRD ref: `prd.md > The Core Journey`.

1. **Arrive.** The browser opens the app; `app.py` sees `stage = "upload"` in session state and draws the hero headline and upload box.
2. **Upload.** The user drops in `sales.xlsx` → **Loader** reads it into a DataFrame → it's stored in session state as `raw_df` → stage becomes `"review"`.
3. **Spot the mess.** **Suggester** builds a small sample (headers + 20 rows + a per-column summary) → sends it to NVIDIA → gets back JSON like `[{"operation": "to_number", "column": "Amount", ...}]` → keeps only valid menu items for real columns. On failure → **rule-based suggester** produces the same kind of list. The list is saved as `fixes`. The preview highlights the cells each fix would change.
4. **Review.** Each fix shows as a tick box (stored in `ticked`). On every tick or untick, Streamlit re-runs → the **Fix menu** applies only the ticked fixes to a copy of the first rows → the before/after table updates. Pressing **"Approve & build dashboard"** applies the ticked fixes to the whole table → saved as `clean_df` → stage becomes `"dashboard"`.
5. **Dashboard.** **Column finder** picks the amount/date/party/invoice columns from `clean_df` → **Metrics** computes the number cards, the monthly totals, and the top 5 → **Benford** runs the first-digit test → **Duplicates** runs same-same-same → **Questions** writes the question to ask for each finding → the **screen pieces** draw it all.
6. **Start over.** A "Analyse another file" button clears session state → back to stage `"upload"`. Nothing is saved anywhere.

## Stack
| Piece | Choice | Why | Docs |
|---|---|---|---|
| Language | Python (3.12 recommended; 3.14 is installed locally) | Learner's choice | https://docs.python.org/3/ |
| Web app | Streamlit | Learner's choice; Python-only, built-in upload, tables, session state | https://docs.streamlit.io |
| Tables & cleaning | pandas | Standard Python spreadsheet library; a learning goal | https://pandas.pydata.org/docs/ |
| Excel reading | openpyxl (.xlsx), xlrd (.xls) | pandas uses these to open Excel files | https://openpyxl.readthedocs.io · https://xlrd.readthedocs.io |
| Charts | Plotly | Interactive charts with a ready dark theme; works in Streamlit | https://plotly.com/python/ |
| Maths | numpy | Used for the Benford maths (comes with pandas) | https://numpy.org/doc/ |
| AI helper | NVIDIA API (build.nvidia.com) via the `openai` Python library | Learner's choice: free developer access; works with the standard OpenAI client | https://build.nvidia.com · https://docs.api.nvidia.com/nim/reference/ · https://github.com/openai/openai-python |
| Secrets (local) | python-dotenv | Loads the key from `.env` on your laptop | https://pypi.org/project/python-dotenv/ |
| Tests | pytest | Checks the audit maths automatically | https://docs.pytest.org |

**Verify early in the build:** (1) Streamlit, pandas and Plotly install cleanly on Python 3.14; if not, install Python 3.12 for this project. (2) The current NVIDIA free allowance, and that the chosen model (planned: `meta/llama-3.3-70b-instruct`) is still listed. Any instruction-following chat model there will do.

## Where It Runs and How Someone Tries It
- **Locally:** a Python virtual environment, then:
  ```
  pip install -r requirements.txt
  streamlit run app.py
  ```
  Streamlit opens http://localhost:8501. Use **`sample_data/messy_sales.csv`** for the demo.
- **NVIDIA key (optional):** copy `.env.example` to `.env` and set `NVIDIA_API_KEY=...`. Without it, the built-in rules suggest the fixes and the app works the same.
- **Shareable link (learner's choice, for LinkedIn):** **Streamlit Community Cloud** (free).
  1. Push the project to a public GitHub repository (required for submission anyway).
  2. At https://share.streamlit.io, sign in with GitHub → *Create app* → pick the repo, branch `main`, main file `app.py` → *Advanced settings*: Python 3.12; Secrets: `NVIDIA_API_KEY = "..."`.
  3. Deploy → get a `*.streamlit.app` link.
  Docs: https://docs.streamlit.io/deploy/streamlit-community-cloud · secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- **Submission:** a short demo video (record the local or deployed app: upload sample → untick one fix → approve → dashboard with the Benford's red flag and duplicates) + the public GitHub repo. The deployed link is a bonus, not a replacement.

## Look and Feel
Implements `prd.md > Look and Feel`.
- **Streamlit theme** in `.streamlit/config.toml`: `base = "dark"`, `backgroundColor = "#132238"` (navy), `secondaryBackgroundColor = "#1b2e4a"`, `textColor = "#eef1f5"`, `primaryColor = "#5fbf8f"` (deep green), `font = "sans serif"`. Palette chosen by the learner during the build: navy, deep green, grey, burgundy.
- **Custom CSS** (injected once from `auditlens/ui.py`), for things Streamlit can't do alone:
  - Hero: large bold headline (~2.6rem, weight 800, tight letter-spacing) with a grey (#93a0b4) second line.
  - Number cards: rounded (14px), 1px border #2b4163, small uppercase grey label, large bold value, ▲ green / ▼ burgundy change.
  - Finding cards: same card style, an uppercase label coloured by verdict (deep green #5fbf8f = normal, burgundy #c4475c = red flag), one plain sentence, then a **"Question to ask →"** line.
  - Highlighted cells in the clean-up preview: light burgundy text on a dark burgundy background.
- **Charts:** Plotly `plotly_dark` template with transparent background; normal bars grey #5b6f8c, flagged bars burgundy #c4475c, Benford expected line deep green #5fbf8f.
- **Copy tone:** plain, confident, auditor-like. **Never the word "AI"** in any visible text, including spinners ("Checking your data…", not "AI is thinking…").
- **Streamlit limits:** the layout is Streamlit's single column with `st.columns` rows. It won't be pixel-identical to the PandasAI reference, but the colours, cards and headline style carry over.

## Components

### App Shell and Stages (`app.py`)
Draws the page, injects CSS, and shows one stage based on `st.session_state.stage` (`upload` → `review` → `dashboard`). Owns the "Analyse another file" reset.
PRD ref: `prd.md > Screens and Layout`, `prd.md > The Core Journey`.

### Loader (`auditlens/loader.py`)
`load_file(uploaded) -> DataFrame`. Reads `.csv` (tries UTF-8, then Latin-1), `.xlsx`, and `.xls` (first sheet). Raises a friendly error for other types or unreadable files.
PRD ref: `prd.md > Upload`.

### Fix Menu (`auditlens/fixes.py`)
The only changes that can ever happen to the data. Each fix is a small dict: `{"id", "operation", "column", "description"}`.

| operation | What it does |
|---|---|
| `clean_headers` | Trims spaces from column names (column = `*`) |
| `standardize_dates` | Parses mixed date formats into real dates, shown as YYYY-MM-DD |
| `to_number` | Removes `$ £ € ,` and spaces; `(120)` → −120; makes the column numeric |
| `tidy_text` | Trims and collapses spaces; consistent Title Case |
| `drop_empty_rows` | Removes rows where every cell is blank (column = `*`) |
| `flag_missing` | Changes nothing; counts and highlights blanks in that column so the user knows |

- `apply_fixes(df, fixes) -> DataFrame`: applies ticked fixes in a fixed order (headers → empty rows → text → numbers → dates).
- `cells_changed(df, fix) -> mask`: which cells a fix touches, for highlighting.
- **No operation removes duplicate rows**, by design (`prd.md > Spot the Mess and Suggested Fixes`).
- `suggest_by_rules(df) -> list[fix]`: built-in rules (text that looks like money → `to_number`; text that parses as dates in ≥ 80% of rows → `standardize_dates`; stray spaces or mixed case → `tidy_text`; blanks → `flag_missing`; …).
PRD ref: `prd.md > Spot the Mess and Suggested Fixes`, `prd.md > Review and Approve`.

### Suggester (`auditlens/suggest.py`)
`suggest_fixes(df) -> list[fix]`. If an NVIDIA key exists, it sends the headers, 20 sample rows, a short per-column summary, and the fix menu, and asks for a JSON array. It validates each item (known operation, real column), drops anything invalid, and writes plain-English `description`s if missing. If there's no key, an error, a timeout (15 s), or zero valid items → `suggest_by_rules(df)`. Either way the caller gets the same shape, and the user can't tell which path ran.
PRD ref: `prd.md > Spot the Mess and Suggested Fixes`.

### Column Finder (`auditlens/detect.py`)
`find_columns(df) -> {"amount", "date", "party", "invoice"}` (each a column name or `None`).
- **amount:** numeric column; name hints first (amount, total, value, net, sales, price); otherwise the numeric column with the largest sum that isn't ID-like (an ID-like column is all-unique whole numbers in sequence).
- **date:** a date-typed column, name hints (date, posted, invoice date).
- **party:** text column with hints (customer, vendor, supplier, client, payee, name).
- **invoice:** hints (invoice, inv, document, doc, ref, number).
No user input (learner's choice: "app can decide").
PRD ref: `prd.md > Automatic Column Detection`.

### Metrics (`auditlens/metrics.py`)
- `kpis(df, cols)`: total amount, transaction count, biggest transaction, % change of the latest month vs. the month before.
- `monthly_totals(df, cols)`: one row per month.
- `top_transactions(df, cols, n=5)`: largest amounts, sorted descending.
Returns `None` for anything whose column is missing; the UI shows the PRD's "not available" note.
PRD ref: `prd.md > Dashboard: Number Cards and Comparison`.

### Benford's Law Test (`auditlens/benford.py`)
Nigrini's **first-digit test**.
- **Input:** amounts ≥ 10 (Nigrini's usual cut-off; tiny amounts distort the test). Credits/negatives are excluded for this PoC.
- **Expected:** P(d) = log10(1 + 1/d) → 30.1%, 17.6%, 12.5%, 9.7%, 7.9%, 6.7%, 5.8%, 5.1%, 4.6%.
- **Per-digit Z-statistic** (with continuity correction): z = (|AP − EP| − 1/(2N)) / √(EP(1 − EP)/N), where the correction is used only if it's smaller than |AP − EP|. Digits with z > 1.96 **and** AP > EP are highlighted as spikes.
- **MAD** = mean of |AP − EP| over the 9 digits. **Verdict bands (Nigrini, first digit):** ≤ 0.006 close conformity · ≤ 0.012 acceptable conformity · ≤ 0.015 marginally acceptable · > 0.015 nonconformity. "Close" and "acceptable" = "looks normal" (green); "marginal" and "nonconformity" = red flag (orange).
- **Sample size:** N < 100 → skip with a note; 100 ≤ N < 1000 → run, labelled "Small sample, read with caution."
- Returns a table (digit, actual %, expected %, z, spike?), MAD, verdict, N.
PRD ref: `prd.md > Audit Finding: Benford's Law`.

### Duplicates Test (`auditlens/duplicates.py`)
Nigrini's **same-same-same test**: rows with the same **amount**, the same **date**, and the same **party** (or, if there's no party column, the same **invoice**). If none of the date/party/invoice columns exists, it falls back to rows identical in every column. Runs on `clean_df`, so rows that differed only by messy spacing or capitals are caught. Returns the groups, with a count for each, sorted by count then amount.
PRD ref: `prd.md > Audit Finding: Duplicates`.

### Questions to Ask (`auditlens/questions.py`)
Template sentences filled with the findings, with no AI involved, so the wording is predictable. Examples:
- Benford's spike on digit *d*: "Amounts starting with **4** appear 2.1× as often as expected. Are payments being kept just under an approval limit (e.g. $5,000)?" For other digits, a general "What business reason explains so many amounts starting with *d*?"
- Benford's normal: "No unusual pattern. Keep this as a baseline to compare next period's data."
- Duplicates found: "*k* transactions appear more than once with the same amount, date and customer. Were any of these paid or recorded twice?"
- No duplicates: "No same-same-same duplicates found."
PRD ref: `prd.md > Questions to Ask`.

### Screen Pieces (`auditlens/ui.py`)
`inject_css()`, `hero()`, `kpi_card(label, value, change=None)`, `finding_card(label, verdict, sentence, question)`, `benford_chart(table)`, `monthly_chart(df)`, `highlight_preview(df, masks)`.
PRD ref: `prd.md > Look and Feel`.

## Data Model
All data lives in **`st.session_state`** for the open browser tab. Nothing is written to disk, and nothing persists after the tab closes or "Analyse another file" is pressed (`prd.md > States and Boundaries`).

| Key | What | Set when | Updated by |
|---|---|---|---|
| `stage` | `"upload"`, `"review"` or `"dashboard"` | start | upload, approve, reset |
| `file_name` | uploaded file's name | upload | reset |
| `raw_df` | the table as uploaded | upload | reset |
| `fixes` | list of fix dicts | entering review | — |
| `ticked` | `{fix_id: True/False}`, all True at first | entering review | the tick boxes |
| `clean_df` | `raw_df` with ticked fixes applied | Approve | reset |

The NVIDIA key lives in `.env` (local) or Streamlit secrets (cloud), never in code or Git.

## File Structure
```
AI business project/
├── app.py                    # Streamlit entry: theme/CSS, stage routing, reset
├── auditlens/
│   ├── __init__.py
│   ├── loader.py             # read CSV / Excel into a DataFrame
│   ├── fixes.py              # fix menu, rule-based suggestions, apply_fixes, highlighting masks
│   ├── suggest.py            # NVIDIA call + validation, falls back to rules
│   ├── detect.py             # find amount / date / party / invoice columns
│   ├── metrics.py            # number cards, monthly totals, top 5
│   ├── benford.py            # Nigrini first-digit test: expected, z, MAD, verdict
│   ├── duplicates.py         # Nigrini same-same-same test
│   ├── questions.py          # "Question to ask" templates
│   └── ui.py                 # CSS, hero, cards, charts
├── sample_data/
│   ├── messy_sales.csv       # MADE-UP demo data: ~1,200 rows, messy formats, planted digit-4 spike + duplicates
│   └── clean_natural.csv     # MADE-UP data that follows Benford (for the "looks normal" check)
├── scripts/
│   └── make_sample_data.py   # regenerates the sample files (fixed random seed)
├── tests/
│   ├── test_benford.py
│   ├── test_duplicates.py
│   └── test_fixes.py
├── .streamlit/
│   └── config.toml           # dark theme colours
├── requirements.txt
├── .env.example              # NVIDIA_API_KEY= (no real key)
├── .gitignore                # already ignores .env and the learner profile
├── README.md                 # what it is, how to run, the link
└── devpost/                  # planning docs (Devpost learning workspace)
```

## External Services and Dependencies

### NVIDIA API (optional at runtime)
- **Sign-up:** https://build.nvidia.com → pick a model → *Get API Key*. Free developer access with usage limits (**verify the current allowance at sign-up**).
- **Call** (OpenAI-compatible):
  ```python
  from openai import OpenAI
  client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key, timeout=15)
  resp = client.chat.completions.create(
      model="meta/llama-3.3-70b-instruct",
      messages=[{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sample_as_text}],
      temperature=0)
  ```
- **Asked to return:** a JSON array, e.g. `[{"operation":"to_number","column":"Amount","description":"Remove $ and commas so Amount is a number"}]`. The system prompt lists the six allowed operations and says "reply with JSON only."
- **What's sent:** column names, up to 20 rows, per-column summary (type guess, blanks count, a few distinct values). The learner accepted this for the PoC.
- **Docs:** https://docs.api.nvidia.com/nim/reference/

### Streamlit Community Cloud (hosting)
Free; deploys from public GitHub; secrets set in the app's settings. https://docs.streamlit.io/deploy/streamlit-community-cloud

### Methods reference
Mark J. Nigrini, *Forensic Analytics: Methods and Techniques for Forensic Accounting Investigations* (Wiley), and *Benford's Law: Applications for Forensic Accounting, Auditing, and Fraud Detection* (Wiley, 2012). Source for the first-digit test, MAD bands, and the same-same-same test.

## Important Failure Modes
- **NVIDIA key missing, quota used up, slow, or a strange reply** → rule-based suggestions are used silently; the user sees the same review screen.
- **Unreadable or wrong file type** → "Audit Lens reads CSV and Excel files (.csv, .xlsx, .xls). Please try another file." Stays on upload.
- **Columns not found** → each dashboard section that needs a missing column shows its "not available" note; if no amount *and* nothing else to analyse → "We couldn't find anything to analyse in this file" plus the reset button.
- **Fewer than 100 usable amounts** → Benford's card shows "Too few amounts (N) for a reliable Benford's test" instead of a verdict.
- **Large files** → the PoC is sized for files up to ~50,000 rows; previews show only the first 20 rows.

## What Was Simplified and Why
- **AI chooses from a fixed menu** instead of rewriting data freely, so changes are predictable, previewable, and tick-box controlled. Free-form cleaning would need much more validation.
- **Rule-based fallback** instead of depending on the AI, so the demo and the public link never break when the free allowance runs out.
- **Template questions** instead of AI-written ones, for predictable, auditor-approved wording. AI-written questions could come later.
- **First-digit test only**: Nigrini's first-two-digits, last-two-digits, and same-same-different tests are deferred (learner: "for now just nigrini" first-digit + same-same-same).
- **Positive amounts ≥ 10 only** for Benford's: credits and returns would be analysed separately in a fuller version.
- **Session-only memory**, no database or accounts (cut in scope).
- **Sample data is made up** and labelled as such in the README and file names.

## Decisions and Open Issues
**Learner decisions**
- Python + Streamlit (from `1-start`).
- AI helper: **NVIDIA's free API**; a small sample of rows may be sent ("a small sample is fine").
- **Nigrini's methods** for the audit checks: MAD verdict bands, sample-size caution, same-same-same duplicates. Other Nigrini tests come later.
- **Shareable link** on Streamlit Community Cloud, to showcase on LinkedIn.
- Duplicates definition → same-same-same (resolves `prd.md > Open Questions`).
- Benford's minimum → skip under 100, caution under 1,000 (resolves `prd.md > Open Questions`).

**Implementation details derived by the agent**
- The six-item fix menu and the order fixes are applied in; the rule thresholds (e.g. 80% parseable dates); column-name hints; Z > 1.96 highlight; 15 s timeout; the `meta/llama-3.3-70b-instruct` model choice; the session-state keys.
- **Correction to a PRD example:** amounts kept just under a $5,000 approval limit start with **4** (e.g. $4,850), not 5. The demo sample plants a spike on digit 4, and the question text says so.

**The learner's useful unknown**
- *Question raised:* whether there's a free API key, and how AI access and cost work. *Clarified:* Anthropic's API is pay-as-you-go; NVIDIA offers free developer access with limits; the app works without any key thanks to the rule-based fallback. *To check in the build:* confirm the free allowance when signing up.

**Still open**
- Exact hero headline wording: decide in the build.
- Python 3.14 compatibility: verify in the first build step.
