import os
import io
import streamlit as st
import pandas as pd
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env file into environment

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Review Issue Classifier",
    page_icon="🔍",
    layout="centered"
)

st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #7c3aed; }
    .stButton > button { background: linear-gradient(135deg, #7c3aed, #3b82f6); color: white; border: none; font-weight: 600; }
    .stButton > button:hover { opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🔍 Review Issue Classifier")
st.markdown("Upload your product reviews → AI auto-discovers issue categories → Export classified CSV")
st.divider()

# ── Model config ─────────────────────────────────────────────────────────────
DISCOVERY_MODEL = "gpt-4.1"        # smarter model for category discovery
CLASSIFY_MODEL  = "gpt-4.1-mini"   # fast + cheap for bulk classification
BATCH_SIZE = 15

# ── Helpers ──────────────────────────────────────────────────────────────────
def extract_json(text: str):
    """Strip markdown fences and parse JSON."""
    clean = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(clean)

def discover_categories(client, reviews, title_col, body_col):
    """Use a sample of reviews to auto-discover issue categories."""
    sample = reviews[:min(60, len(reviews))]
    sample_text = "\n\n".join(
        f"{i+1}. Title: {r.get(title_col, '')}\n   Review: {r.get(body_col, '')}"
        for i, r in enumerate(sample)
    )
    prompt = f"""You are an expert product analyst. Read these negative customer reviews and identify distinct, 
standardised issue categories that customers are complaining about.

Rules:
- Use clear, consistent category names (e.g. "Digestive Issues", "Overpriced", "Bad Taste", "No Effect", "Poor Packaging", "Side Effects", "Bad Smell", "Misleading Description")
- Merge similar issues into one category (e.g. "runny stomach" and "upset stomach" = "Digestive Issues")
- Aim for 5-15 meaningful categories that cover the main complaints
- Return ONLY a JSON array of strings, no explanation

Reviews:
{sample_text}"""

    response = client.chat.completions.create(
        model=DISCOVERY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return extract_json(response.choices[0].message.content)

def classify_batch(client, batch, categories, title_col, body_col):
    """Classify a batch of reviews into categories with justification."""
    batch_text = "\n\n".join(
        f"{i+1}. Title: {r.get(title_col, '')}\n   Review: {r.get(body_col, '')}"
        for i, r in enumerate(batch)
    )
    cats_str = ", ".join(categories)
    prompt = f"""You are classifying negative product reviews.
Available categories: {cats_str}

For each review, assign the SINGLE most dominant issue category.
If none of the categories fit well, create a new short, clear category name.

Return ONLY a JSON array: [{{"index": 1, "category": "Digestive Issues"}}, ...]

Reviews:
{batch_text}"""

    response = client.chat.completions.create(
        model=CLASSIFY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return extract_json(response.choices[0].message.content)

def unify_justifications(client, results_df, body_col):
    """For each category, generate one canonical justification representing all reviews in it."""
    category_justifications = {}
    categories = results_df["Issue_Category"].unique()

    for category in categories:
        group = results_df[results_df["Issue_Category"] == category]
        sample_reviews = group[body_col].dropna().tolist()[:20]  # cap at 20 samples
        sample_text = "\n".join(f"- {r}" for r in sample_reviews)

        prompt = f"""Multiple customers have been grouped under the issue category: "{category}".

Here are their reviews:
{sample_text}

Your task: Write ONE short consolidated description (3-8 words max) that names the core problem shared across these reviews.

Rules:
- Be specific about the actual problem, not vague
- Do NOT write a full sentence — just a short problem label
- Do NOT include phrases like "customers report" or "users say"
- Only include details that appear consistently across multiple reviews — ignore one-off specifics
- Match this style exactly:
  * "Upset stomach" (not "Customers experience stomach discomfort after use")
  * "Causing bloating and stomach pain" (not "Product causes significant gastrointestinal issues")
  * "Should be in glass bottle" (not "Customers prefer glass bottle packaging")
  * "No noticeable difference" (not "Product did not show expected results for users")

Return ONLY the short label, nothing else."""

        try:
            response = client.chat.completions.create(
                model=DISCOVERY_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            category_justifications[category] = response.choices[0].message.content.strip()
        except Exception:
            category_justifications[category] = category

    return category_justifications

# ── Load API Key from .env ────────────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ `OPENAI_API_KEY` not found. Please add it to your `.env` file:\n\n```\nOPENAI_API_KEY=sk-...\n```")
    st.stop()

client = OpenAI(api_key=api_key)

# ── Step 2: Upload file ───────────────────────────────────────────────────────
st.divider()
st.subheader("Step 1 — Upload Reviews File")
st.caption("Accepted formats: CSV, XLSX, XLS")

uploaded = st.file_uploader("Drop your file here", type=["csv", "xlsx", "xls"], label_visibility="collapsed")

if not uploaded:
    st.stop()

try:
    file_bytes = uploaded.getvalue()

    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    else:
        workbook = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_name = st.selectbox("Select spreadsheet sheet", options=workbook.sheet_names, index=0)
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name)
    st.success(f"✅ Loaded **{len(df):,} rows** and **{len(df.columns)} columns**")
    with st.expander("Preview first 5 rows"):
        st.dataframe(df.head(), use_container_width=True)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

# ── Step 3: Map columns ───────────────────────────────────────────────────────
st.divider()
st.subheader("Step 2 — Map Your Columns")

cols = list(df.columns)
verified_purchase_col = "Verified Purchase"

col1, col2, col3, col4 = st.columns(4)
with col1:
    title_col = st.selectbox("📌 Review Title Column", options=["(none)"] + cols)
with col2:
    body_col = st.selectbox("📝 Review Body Column", options=["(select)"] + cols)
with col3:
    rating_col = st.selectbox("⭐ Star Rating Column", options=["(select)"] + cols)
with col4:
    date_col = st.selectbox("📅 Review Date Column", options=["(select)"] + cols)

if body_col == "(select)" or rating_col == "(select)" or date_col == "(select)":
    st.warning("Please map the Review Body, Star Rating, and Review Date columns to continue.")
    st.stop()

# Filter to the last 6 months, then keep only negative reviews
try:
    if verified_purchase_col not in df.columns:
        st.error(f"Selected sheet must contain a '{verified_purchase_col}' column.")
        st.stop()

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None)
    latest_sheet_date = df[date_col].dropna().max()

    if pd.isna(latest_sheet_date):
        st.error(f"No valid dates were found in the '{date_col}' column.")
        st.stop()

    latest_sheet_date = latest_sheet_date.normalize()
    cutoff_date = latest_sheet_date - pd.DateOffset(months=6)
    df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")
    verified_df = df[
        df[verified_purchase_col].fillna("").astype(str).str.strip().str.upper() == "Y"
    ].reset_index(drop=True)
    recent_df = verified_df[
        verified_df[date_col].notna() & (verified_df[date_col] >= cutoff_date)
    ].reset_index(drop=True)
    negative_df = recent_df[recent_df[rating_col] < 4].reset_index(drop=True)

    st.info(
        f"Using **{len(verified_df):,} verified purchase reviews** where `{verified_purchase_col}` = `Y`."
    )
    st.info(
        f"Latest review date in the selected sheet is **{latest_sheet_date.date()}**."
    )
    st.info(
        f"Keeping **{len(recent_df):,} verified reviews** dated between **{cutoff_date.date()}** and **{latest_sheet_date.date()}**."
    )
    st.info(
        f"Found **{len(negative_df):,} negative reviews** (rating < 4) within that 6-month window."
    )
except Exception as e:
    st.error(f"Could not parse the date or rating column: {e}")
    st.stop()

if len(verified_df) == 0:
    st.warning(f"No reviews with '{verified_purchase_col}' = 'Y' were found in this sheet.")
    st.stop()

if len(recent_df) == 0:
    st.warning(
        f"No verified purchase reviews were found between {cutoff_date.date()} and {latest_sheet_date.date()}."
    )
    st.stop()

if len(negative_df) == 0:
    st.warning(
        f"No reviews with rating < 4 were found between {cutoff_date.date()} and {latest_sheet_date.date()}."
    )
    st.stop()

with st.expander("Preview filtered reviews"):
    st.dataframe(negative_df, use_container_width=True)

# ── Step 4: Classify ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Step 3 — Classify Reviews")

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Discovery model", DISCOVERY_MODEL)
with col_b:
    st.metric("Classification model", CLASSIFY_MODEL)

if st.button("🤖 Start Classification", use_container_width=True):
    records = negative_df.to_dict("records")

    # Discover categories
    with st.spinner("Discovering issue categories from your reviews…"):
        try:
            categories = discover_categories(
                client, records,
                title_col if title_col != "(none)" else body_col,
                body_col
            )
        except Exception as e:
            st.error(f"Category discovery failed: {e}")
            st.stop()

    st.success(f"✅ Discovered **{len(categories)} categories**: {', '.join(categories)}")

    # Classify in batches
    progress_bar = st.progress(0, text="Starting classification…")
    status_text = st.empty()

    results = []
    total = len(records)
    batches = [records[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    for batch_idx, batch in enumerate(batches):
        start = batch_idx * BATCH_SIZE
        status_text.text(f"Classifying reviews {start+1}–{min(start+BATCH_SIZE, total)} of {total}…")
        try:
            parsed = classify_batch(
                client, batch, categories,
                title_col if title_col != "(none)" else body_col,
                body_col
            )
            result_map = {item["index"]: item["category"] for item in parsed}
            for idx, row in enumerate(batch):
                row_copy = dict(row)
                row_copy["Issue_Category"] = result_map.get(idx + 1, "Uncategorized")
                results.append(row_copy)
        except Exception as e:
            for row in batch:
                row_copy = dict(row)
                row_copy["Issue_Category"] = "Classification Error"
                results.append(row_copy)

        progress_bar.progress(
            (batch_idx + 1) / len(batches),
            text=f"Processed {min(start+BATCH_SIZE, total)}/{total} reviews"
        )

    status_text.empty()
    progress_bar.empty()

    results_df = pd.DataFrame(results)

   # Unify justifications per category
    with st.spinner("Standardising justifications across similar reviews…"):
        unified = unify_justifications(client, results_df, body_col)
        results_df["Justification"] = results_df["Issue_Category"].map(unified)

    st.session_state["results"] = results_df
    st.session_state["categories"] = categories
    st.success(f"✅ Done! Classified **{len(results)} reviews** with unified justifications.")

# ── Step 5: Results ───────────────────────────────────────────────────────────
if "results" in st.session_state:
    result_df = st.session_state["results"]

    st.divider()
    st.subheader("Step 4 — Results")

    # Issue summary / pivot
    summary = result_df["Issue_Category"].value_counts().reset_index()
    summary.columns = ["Issue Category", "Count"]
    summary["% of Negative Reviews"] = (
        summary["Count"] / len(result_df) * 100
    ).round(1).astype(str) + "%"

    st.markdown("**Issue Breakdown (Pivot Summary)**")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.bar_chart(summary.set_index("Issue Category")["Count"])

    # Full classified table
    with st.expander("View all classified reviews"):
        display_cols = [c for c in [
            title_col if title_col != "(none)" else None,
            rating_col, body_col, "Issue_Category", "Justification"
        ] if c]
        st.dataframe(result_df[display_cols], use_container_width=True)

    # Export
    st.divider()
    csv_bytes = result_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Classified Reviews CSV",
        data=csv_bytes,
        file_name="classified_reviews.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.caption("CSV includes all original columns + new `Issue_Category` column — ready to pivot in Excel.")
