# 🔍 Review Issue Classifier

A Streamlit web app that automatically mines product reviews for complaints, groups them into consistent issue categories using OpenAI, and rates how severe each complaint is — so you can build pivot tables effortlessly instead of reading reviews one by one.

---

## What It Does

1. Filters reviews to a **review-date window** and a **rating scope** you choose (negative only, 4–5 stars only, or all ratings)
2. **Auto-discovers** issue categories from your reviews (no predefined list needed)
3. **Classifies** each review into its single most dominant issue category
4. Assigns a **severity** (`High` / `Medium` / `Low`) to each complaint
5. Routes genuinely happy reviews to a **`No Complaint`** bucket instead of inventing a fake issue
6. **Consolidates** near-duplicate categories into one canonical set
7. Exports a **CSV** ready to pivot in Excel

> **Why include 4–5 star reviews?** High-rated reviews still contain real complaints ("great product, but the cap leaks") — they're just milder. With a rating scope of *4–5 stars* or *all ratings*, those complaints are extracted too, and the `Severity` column lets you tell a safety risk apart from a minor nitpick.

---

## Output Columns

The exported CSV includes all your original columns plus three new ones:

| Column | Description |
|---|---|
| `Issue_Category` | The issue group this review belongs to (e.g. `Health Risk`, `Packaging`, `Product Quality`, or `No Complaint`) |
| `Severity` | How serious the complaint is — `High`, `Medium`, `Low`, or `None` (for `No Complaint`) |
| `Justification` | A short 2–6 word label describing the core problem (e.g. `Upset stomach`, `Cap leaks`) |

---

## Models Used

| Task | Model | Reason |
|---|---|---|
| Category discovery & consolidation | `gpt-5.4-mini` | Higher reasoning to standardise categories and merge duplicates |
| Bulk classification | `gpt-5.4-nano` | Fast and cost-efficient for processing large volumes of reviews |

Each run logs token usage and an estimated cost to `logs/`, and stops automatically once the estimated spend reaches the per-run budget (default **$0.30**).

---

## Prerequisites

- Python **3.12+** (the code uses 3.12 f-string syntax)
- An [OpenAI API key](https://platform.openai.com/api-keys) with access to the models above

---

## Setup

### 1. Project files

```
your-folder/
├── review_classifier_python.py   # Main Streamlit app (entrypoint)
├── review_classifier_core.py     # Pure, testable logic (imported by the app)
├── tests/                        # Unit tests for the core logic
├── requirements.txt
├── .env                          # you create this (see step 3)
└── readme.md
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your OpenAI API key

Copy `.env.example` to `.env` and fill in your key:

```
OPENAI_API_KEY=sk-your-api-key-here
```

> ⚠️ Never share or commit your `.env` file. It is already listed in `.gitignore`.

---

## Running the App

```bash
py -m streamlit run review_classifier_python.py
```

This opens the app in your browser at `http://localhost:8501`.

> ❌ Do **not** run with `python review_classifier_python.py` — it must be launched via Streamlit.

---

## How to Use

### Step 1 — Upload Reviews File
Supported formats: `.csv`, `.xlsx`, `.xls`. For spreadsheets you can pick the sheet; the header row is detected automatically.

### Step 2 — Map Your Columns
Select which columns correspond to the review **title** (optional), **body**, **star rating**, and **review date**, then choose:
- **Review window (months)** — keeps reviews from the latest date in the sheet back this many months.
- **Ratings to analyze** — `Negative only (rating below 4)` (default), `High ratings only (4 and 5 stars)`, or `All ratings`.

### Step 3 — Classify Reviews
Click **Start Classification**. The app will:
1. Build a representative, stratified sample of your filtered reviews to discover issue categories
2. Classify all filtered reviews in token-sized batches (assigning category, severity, and justification)
3. Consolidate near-duplicate categories and reclassify any vague/mixed buckets

### Step 4 — Results
- View the **issue breakdown** table and bar chart, plus a **severity breakdown**
- Expand the full classified reviews table
- Click **Download Classified Reviews CSV** to export

---

## Input File Requirements

| Column | Required | Notes |
|---|---|---|
| Review Body | ✅ Yes | Full text of the customer review |
| Star Rating | ✅ Yes | Must be numeric (1–5). Rows analyzed depend on the chosen rating scope |
| Review Date | ✅ Yes | Used for the review-date window filter |
| Review Title | ❌ Optional | Used alongside body for better classification accuracy |

---

## Classification Logic

- Each review is assigned the **single most dominant issue** only
- Categories are **auto-discovered** from your data — no hardcoded list
- A **shared canonical category set** is used across all ratings, so the same complaint groups whether it came from a 2★ or a 5★ review
- Genuinely positive reviews land in **`No Complaint`** (with severity `None`) instead of a fabricated issue; this label is never merged away during consolidation
- Similar complaints are merged under one canonical category during consolidation

---

## Requirements

```
streamlit>=1.35.0
openai>=1.30.0
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
xlrd>=2.0.1
```

---

## Running the Tests

```bash
py -m pytest tests/
```

---

## Project Structure

```
your-folder/
├── review_classifier_python.py   # Main Streamlit app (UI + OpenAI orchestration)
├── review_classifier_core.py     # Pure logic: parsing, sampling, token budgeting, filtering
├── tests/
│   └── test_review_classifier_core.py
├── requirements.txt
├── .env                          # Your OpenAI API key (not committed)
├── .env.example                  # Template
└── readme.md                     # This file
```

> Note: earlier prototypes (`streamlit_app.py`, `neg_issue.py`, `review_classifier_python_v1.py`) were removed from the working tree; they remain in git history (initial commit) if ever needed.
