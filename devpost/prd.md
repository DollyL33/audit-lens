---
doc: prd
status: approved
---

# Audit Lens — Product Requirements

Upload a messy spreadsheet, approve the suggested clean-up, and get a dashboard that looks at your data the way an internal or forensic auditor would. For anyone who has data and wants insights from it, without doing the reporting by hand: "make reporting simple for anyone who has data and wants to get insights from it."
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`.

## The Core Journey
Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. **Arrive.** The person opens Audit Lens and sees a bold headline, a short subheading, and an upload area.
2. **Upload.** They drop in one CSV or Excel file.
3. **Spot the mess.** The app shows a preview of the data with the problem cells highlighted, and a list of suggested fixes. Each fix has its own tick box, all ticked by default.
4. **Review.** They untick any fix they disagree with and check the before/after preview of a few rows. Then they press one button to continue.
5. **Dashboard.** The app applies only the ticked fixes and shows the dashboard: number cards, a monthly comparison chart, the biggest transactions, and the audit findings (Benford's Law, duplicates), each ending with a **question to ask**.
6. **Start over.** They can upload a different file at any time to begin again.

Success = going from a messy file to an audit dashboard with at least one meaningful finding and its question, in about a minute.

## Screens and Layout
One page that moves through three stages in order. No sidebar navigation or multiple pages.

1. **Upload stage:** headline, subheading, upload area.
2. **Clean-up stage:** data preview with highlighted problems, the fix list with tick boxes, before/after preview, and a continue button.
3. **Dashboard stage**, top to bottom:
   - Number cards in a row
   - Monthly comparison chart
   - Biggest transactions list
   - Audit findings: Benford's Law card (chart + verdict + question), Duplicates card (list + question)

## Look and Feel
Source: learner's screenshots of pandas-ai.com.
- **Dark theme**: deep navy/near-black background (learner chose dark over the white version).
- Borrowed from the reference: a **big, bold headline** with a lighter grey second line; generous spacing; clean, modern sans-serif type.
- **Rounded cards** for numbers, with a small uppercase label (e.g. "TOTAL AMOUNT") and a large value; small coloured icon accents.
- **Finding cards** in the reference's "Insight" style: a big headline number or statement, one plain-English sentence, and a coloured accent. Green for "looks normal," a warm warning colour for a red flag.
- Feels like a sharp, trustworthy auditor's tool, not a flashy BI product.
- **Never mention "AI"** anywhere the user can see: name, headings, buttons, messages (`scope.md > Inspiration & Identity`).
- Avoid: chat boxes, "Ask a question" inputs, robot or assistant imagery.

## Features and Behavior

### Upload
- Accepts one `.csv`, `.xlsx`, or `.xls` file.
- First screen copy: headline + subheading in the bold/grey style. Exact wording is set during the build; no "AI" wording.
- Acceptance criteria:
  - [ ] Uploading a valid CSV or Excel file moves the person to the clean-up stage.
  - [ ] Uploading another file type shows a friendly message saying only CSV and Excel are supported.

### Spot the Mess and Suggested Fixes
Source: `scope.md > The POC Boundary`.
- The app examines the file and lists suggested fixes in plain English, such as: make all dates one format, turn text amounts like "$1,250" into numbers, trim extra spaces and standardise capitalisation in names, flag rows with missing values.
- Suggestions are produced behind the scenes (AI under the hood), but they're presented as the app's suggestions.
- The data preview highlights the cells each fix would change.
- **Duplicates are never removed during clean-up.** They're kept for the Duplicates finding, because in an audit a duplicate is evidence.
- Acceptance criteria:
  - [ ] A messy sample file produces a list of at least three relevant, plainly worded fixes.
  - [ ] Each fix has its own tick box, ticked by default.
  - [ ] Problem cells are visibly highlighted in the preview.
  - [ ] No fix deletes duplicate rows.

### Review and Approve
- A before/after preview of a few affected rows shows exactly what the ticked fixes change.
- Unticking a fix updates the before/after preview to match.
- One continue button (e.g. "Approve & build dashboard") applies only the ticked fixes.
- Acceptance criteria:
  - [ ] Unticking a fix means that change does not appear in the after view or in the dashboard data.
  - [ ] Pressing continue shows the dashboard built from the cleaned data.
  - [ ] A file with nothing to fix says so ("Your data looks clean") and lets the person continue.

### Automatic Column Detection
- The app decides which column holds the amounts and which holds the dates, with no dropdowns or questions to the user (learner's choice: "app can decide").
- Acceptance criteria:
  - [ ] For the sample file, the app picks the correct amount and date columns without any input.

### Dashboard: Number Cards and Comparison
Source: learner's audit experience ("comparison is major thing").
- **Number cards:** total amount, number of transactions, biggest single transaction, and change vs. the previous month (▲/▼ %).
- **Monthly comparison chart:** totals per month, so jumps and drops stand out.
- **Biggest transactions:** a short list of the largest entries (the top 5).
- Acceptance criteria:
  - [ ] Card values match totals calculated by hand from the cleaned sample file.
  - [ ] The chart shows one bar or point per month present in the data.
  - [ ] The biggest-transactions list is sorted largest first.

### Audit Finding: Benford's Law
Source: `scope.md > The Unique Kernel`.
- Chart of the actual first-digit frequency (1–9) of the amounts, compared with the expected Benford's Law percentages.
- Digits that stray noticeably from expected are highlighted.
- A plain-English verdict ("Looks consistent with natural data" or "Unusual pattern found") plus a **question to ask**, e.g. "Amounts starting with 4 appear about twice as often as expected. Are payments being kept just under a $5,000 approval limit?"
- Acceptance criteria:
  - [ ] Expected line shows the standard Benford percentages (1 ≈ 30.1% down to 9 ≈ 4.6%).
  - [ ] A sample file with a planted spike on one digit is flagged, with that digit highlighted and a question shown.
  - [ ] A file that follows Benford closely gets a "looks normal" verdict.

### Audit Finding: Duplicates
- Lists records that appear more than once after cleaning, with how many times each appears.
- Ends with a **question to ask**, e.g. "3 invoices appear twice with the same customer, date and amount. Were any of these paid twice?"
- Acceptance criteria:
  - [ ] Planted duplicate rows in the sample file are all listed.
  - [ ] Rows that were only "different" because of messy spacing/capitals before cleaning are caught as duplicates after cleaning.
  - [ ] A file without duplicates says "No duplicates found."

### Questions to Ask
- Every finding card ends with one auditor-style question that gives the person a clear next step (learner's "path to action" and "asking right questions").

## States and Boundaries
- **First use / nothing uploaded:** headline, subheading, and upload area only.
- **Wrong file type or unreadable file:** friendly message; stays on the upload stage.
- **No date column:** the dashboard shows everything else; the monthly comparison and month-change card are replaced by a short note ("No date column found, so the monthly comparison isn't available").
- **No amount column:** the dashboard shows what it can (e.g. duplicates) and explains that number cards, comparison, and Benford's need a column of amounts. If nothing at all can be analysed, it says so plainly.
- **Too few amounts for Benford's:** shows a note instead of a misleading verdict (*assumption: under roughly 50 amounts is too few; confirm in spec*).
- **Nothing to clean:** "Your data looks clean," then continue.
- **Persistence:** nothing is saved. Closing the app or uploading a new file starts fresh.

## Product Decisions
- Name: **Audit Lens**. The learner kept the working name.
- **Per-fix tick boxes** rather than all-or-nothing, so people control what changes.
- **Before/after preview** so people can trust the fixes.
- **App decides columns automatically**, no dropdowns. Keeps it simple.
- **Show what it can** when columns are missing, rather than rejecting the file.
- **Dark theme** with the clean, bold, card-based style of the PandasAI reference.
- **Questions to ask** on each finding: an auditor's "path to action."
- **No AI wording** anywhere the user sees.
- **No chat** (the reference's main feature), because it isn't part of the core loop.
- Duplicates are kept during clean-up and reported as a finding. Proposed by the agent; the learner approved the scope with this in it.

## What We're Building
- One-page app: upload → spot the mess → review with tick boxes and before/after → dashboard
- CSV and Excel, one file at a time
- Suggested fixes produced behind the scenes, applied only when ticked
- Automatic amount/date column detection
- Number cards, monthly comparison chart, top 5 biggest transactions
- Benford's Law finding and Duplicates finding, each with a verdict and a question to ask
- Graceful handling of missing columns, wrong files, and clean files
- Dark, card-based look with no AI wording

## Deferred From the POC
- **Letting users change the detected columns:** the learner chose automatic; a manual override could come later if detection proves unreliable.
- **Downloading the cleaned file or a report:** useful, but not needed to prove the kernel in a demo.
- **Saving past uploads:** would need storage or accounts.

## Possible Later Enhancements
- More audit tests: outliers, round-number amounts, weekend/after-hours entries, gaps in invoice numbers.
- Compliance rule checks.
- Downloadable audit report (PDF) of findings and questions.
- Process-efficiency insights.

## Non-Goals
- **Chat / "ask your data" box:** not part of the upload → review → dashboard loop.
- **Live or real-time updating dashboards, decision trees, shared metric definitions:** enterprise BI features from the reference, far beyond a proof of concept.
- **File types other than CSV/Excel:** cut in scope.
- **Accounts, saved history, deployment:** cut in scope.

## Open Questions
- How strict is "duplicate": every column identical, or key fields (e.g. invoice, date, amount)? *Can be decided in `4-spec`.*
- Minimum number of amounts for a meaningful Benford's check. *Can be decided in `4-spec`.*
- Exact headline and subheading wording. *Can wait for the build.*
