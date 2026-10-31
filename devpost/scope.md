---
doc: scope
status: approved
---

# Audit Lens (working name)

Upload a messy spreadsheet, have it cleaned with your approval, and get a dashboard that looks at your data the way an internal or forensic auditor would.

## The Unique Kernel
**An internal and forensic auditor's eye on your data.** Most "upload a file, get charts" tools stop at charts. This one also runs audit-style tests, starting with **Benford's Law** and **duplicate detection**, and explains in plain English where the gaps and red flags are, so the data "speaks itself."

## Who It's For
A small business owner (or whoever handles their numbers) who has sales and returns data in Excel/CSV and wants to know where they're losing margin or taking on risk, without an audit team. Today they eyeball spreadsheets by hand or not at all. The learner did this work manually in an internal audit job: finding gaps that "help company improve their margins and also help them be compliant."

## The Core Loop
1. Upload a CSV or Excel file.
2. The app looks at the messy data and proposes cleaning steps (AI does this behind the scenes).
3. User reviews the proposed changes (before/after) and approves.
4. App shows a dashboard: basic charts (e.g. sales, returns, % increase/decrease) plus audit findings.

They come back whenever they have a new export to check.

## Inspiration & Identity
Feels like a sharp, trustworthy auditor's review rather than a flashy BI tool. Findings are explained plainly, not in jargon. **AI works under the hood but is never mentioned:** no "AI" in the app's name, screens, buttons, or messages. It should feel like an auditor's tool, not an AI product. No visual references given yet; `3-prd` will ask.

## Why This Matters to the Learner
Draws directly on the learner's internal audit experience: turning manual Excel analysis (sales, returns, % changes, finding gaps) into an app. A personal project, and a chance to learn Python, Streamlit, and pandas, and to understand the code the AI writes instead of having it all built for them.

## What "Working" Looks Like
In a one-minute demo: upload a messy sales file → see proposed cleaning steps and a before/after preview → approve → land on a dashboard with a few charts, a **Benford's Law chart** (actual vs. expected first-digit distribution) with a plain-English verdict, and a list of **duplicate records** found.

The "oh, that's useful" beat: the Benford's chart showing where numbers deviate from what real data should look like, with an explanation of why that matters to an auditor.

## The POC Boundary
- Python + Streamlit app, run locally
- CSV and Excel uploads, one file at a time
- Cleaning steps proposed by AI behind the scenes, applied by the app, with user review and approval
- No mention of "AI" anywhere in the user-facing app
- Dashboard with a few basic charts
- Two audit checks: Benford's Law and duplicates, each with a short plain-English explanation

## Later
- Grow into a fuller **fraud analytics dashboard** based on Nigrini's methods (learner plans to study his book): first-two-digits, last-two-digits, same-same-different, relative size factor, round numbers
- More audit tests: outliers, round-number transactions, weekend/after-hours entries, gaps in invoice sequences
- Compliance rule checks
- Downloadable audit report
- Process-efficiency insights

## Explicitly Cut
- **"Any file" types (PDF, JSON, etc.):** CSV/Excel covers the real use case; other formats add parsing work without proving the kernel.
- **User accounts and saved history:** not needed to demonstrate one upload → one review → one dashboard.
- **Deployment:** optional for the hackathon; running locally is enough for the demo.
