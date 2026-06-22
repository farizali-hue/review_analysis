import os
import io
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from review_classifier_core import (
    DEFAULT_RATING_SCOPE,
    DEFAULT_SEVERITY,
    GENERIC_CATEGORY_LABELS,
    NO_COMPLAINT_LABEL,
    RATING_SCOPES,
    SEVERITY_NONE,
    build_results_context,
    build_review_block,
    clean_category_label,
    clean_text,
    compute_safe_context_budget,
    clear_stale_results,
    couple_category_severity,
    detect_encoding,
    estimate_input_tokens,
    filter_reviews_by_scope,
    fix_mojibake,
    format_review_window_label,
    get_upload_extension,
    is_csv_upload,
    is_vague_category_label,
    load_excel_sheet,
    normalize_severity,
    pack_prompt_items,
    resolve_model_token_limits,
    sanitize_category_label,
    sanitize_csv_field,
)

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
DISCOVERY_MODEL = "gpt-5.4-mini"   # better fit for discovery + consolidation
CLASSIFY_MODEL  = "gpt-5.4-nano"   # cheaper high-volume batch classification
BATCH_SIZE = 15
DISCOVERY_SAMPLE_PCT = 0.20
DISCOVERY_SAMPLE_MIN = 50
DISCOVERY_SAMPLE_MAX = 200
DISCOVERY_SAMPLE_SEED = 42
MAX_CATEGORY_EVIDENCE = 8
LOGS_DIR_NAME = "logs"
MAX_API_COST_USD = 0.3
TERMINAL_LOGGING_ENABLED = True
MODEL_PRICING_PER_1M = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "output": 1.25},
}
DISCOVERY_MODEL_LIMITS = resolve_model_token_limits(DISCOVERY_MODEL)
CLASSIFICATION_MODEL_LIMITS = resolve_model_token_limits(CLASSIFY_MODEL)
DISCOVERY_SAFE_CONTEXT_BUDGET = int(
    os.getenv(
        "DISCOVERY_SAFE_CONTEXT_BUDGET",
        str(compute_safe_context_budget(DISCOVERY_MODEL)),
    )
)
DISCOVERY_RESERVED_OUTPUT_TOKENS = int(os.getenv("DISCOVERY_RESERVED_OUTPUT_TOKENS", "1200"))
CLASSIFICATION_SAFE_CONTEXT_BUDGET = int(
    os.getenv(
        "CLASSIFICATION_SAFE_CONTEXT_BUDGET",
        str(compute_safe_context_budget(CLASSIFY_MODEL)),
    )
)
CLASSIFICATION_RESERVED_OUTPUT_TOKENS_BASE = int(os.getenv("CLASSIFICATION_RESERVED_OUTPUT_TOKENS_BASE", "400"))
CLASSIFICATION_RESERVED_OUTPUT_TOKENS_PER_REVIEW = int(os.getenv("CLASSIFICATION_RESERVED_OUTPUT_TOKENS_PER_REVIEW", "80"))

# ── Helpers ──────────────────────────────────────────────────────────────────
def extract_json(text: str):
    """Strip markdown fences and parse JSON."""
    clean = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return json.loads(clean)

class ApiBudgetExceededError(RuntimeError):
    """Raised when the estimated API budget is exhausted."""

DISCOVER_CATEGORIES_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "discovered_categories",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["categories"],
        },
    },
}

CLASSIFICATION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "classified_reviews",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "index": {"type": "integer"},
                            "category": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["High", "Medium", "Low", "None"],
                            },
                            "justification": {"type": "string"},
                        },
                        "required": ["index", "category", "severity", "justification"],
                    },
                }
            },
            "required": ["items"],
        },
    },
}

CONSOLIDATION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "category_consolidation",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "canonical_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                        },
                        "required": ["source", "target"],
                    },
                },
                "reclassify_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["canonical_categories", "mappings", "reclassify_categories"],
        },
    },
}

def emit_terminal_log(timestamp, event, message):
    """Print a formatted live log line to the terminal."""
    if not TERMINAL_LOGGING_ENABLED:
        return
    print(f"[{timestamp}] [{event}] {message}", flush=True)

def log_response_block(log_state, stage_name, response_text, event="REPLY", reason=None):
    """Persist a model response block to the log file and terminal."""
    if not log_state or not log_state.get("path"):
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"{stage_name} response"
    if reason:
        header = f"{header} | reason={reason}"
    lines = str(response_text).splitlines() or ["<empty response>"]
    with open(log_state["path"], "a", encoding="utf-8") as log_file:
        begin_line = f"--- BEGIN {header} ---"
        end_line = f"--- END {stage_name} response ---"
        log_file.write(f"[{timestamp}] [{event}] {begin_line}\n")
        emit_terminal_log(timestamp, event, begin_line)
        for idx, line in enumerate(lines, start=1):
            payload_line = f"{idx:03d} | {line}"
            log_file.write(f"[{timestamp}] [{event}] {payload_line}\n")
            emit_terminal_log(timestamp, event, payload_line)
        log_file.write(f"[{timestamp}] [{event}] {end_line}\n")
        emit_terminal_log(timestamp, event, end_line)

def create_run_logger():
    """Create a per-run log file and token/cost accumulator."""
    logs_dir = Path.cwd() / LOGS_DIR_NAME
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"review_classifier_{timestamp}.log"
    log_state = {
        "path": str(log_path),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "budget_limit": MAX_API_COST_USD,
        "budget_reached": False,
    }
    append_run_log(
        log_state,
        f"Run started | budget_limit=${MAX_API_COST_USD:.2f} | log_file={log_path}",
        event="RUN",
    )
    return log_state

def append_run_log(log_state, message, event="INFO"):
    """Append a formatted line to the run log file and terminal."""
    if not log_state or not log_state.get("path"):
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [{event}] {message}"
    with open(log_state["path"], "a", encoding="utf-8") as log_file:
        log_file.write(f"{formatted_message}\n")
    emit_terminal_log(timestamp, event, message)

def parse_json_response(response_text, log_state=None, stage_name="api_call"):
    """Parse JSON from a response that has already been logged."""
    try:
        return extract_json(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{exc}. See logged REPLY block for stage '{stage_name}'.") from exc

def estimate_model_cost(model_name, prompt_tokens, completion_tokens):
    """Estimate cost for known models using current per-million token pricing."""
    pricing = MODEL_PRICING_PER_1M.get(model_name)
    if not pricing:
        return None
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost

def log_api_usage(log_state, model_name, stage_name, usage):
    """Record API token usage and estimated cost for a single call."""
    if not usage:
        append_run_log(
            log_state,
            f"{stage_name} completed | model={model_name} | usage metadata not returned by the API",
            event="TOKENS",
        )
        return

    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    total_tokens = getattr(usage, "total_tokens", prompt_tokens + completion_tokens)
    estimated_cost = estimate_model_cost(model_name, prompt_tokens, completion_tokens)

    log_state["prompt_tokens"] += prompt_tokens
    log_state["completion_tokens"] += completion_tokens
    log_state["total_tokens"] += total_tokens
    if estimated_cost is not None:
        log_state["estimated_cost"] += estimated_cost

    cost_text = f"${estimated_cost:.6f}" if estimated_cost is not None else "unknown"
    append_run_log(
        log_state,
        (
            f"{stage_name} completed | model={model_name} | prompt_tokens={prompt_tokens:,} | "
            f"completion_tokens={completion_tokens:,} | total_tokens={total_tokens:,} | "
            f"call_cost={cost_text} | cumulative_cost=${log_state['estimated_cost']:.6f}"
        ),
        event="TOKENS",
    )
    if log_state["estimated_cost"] >= log_state["budget_limit"]:
        log_state["budget_reached"] = True
        append_run_log(
            log_state,
            (
                f"Budget threshold reached after {stage_name} | "
                f"cumulative_cost=${log_state['estimated_cost']:.6f} | "
                f"limit=${log_state['budget_limit']:.2f}"
            ),
            event="BUDGET",
        )

def enforce_budget(log_state, stage_name):
    """Stop new API calls once the run's estimated cost limit has been reached."""
    if not log_state:
        return
    if log_state.get("budget_reached") or log_state.get("estimated_cost", 0.0) >= log_state.get("budget_limit", float("inf")):
        raise ApiBudgetExceededError(
            f"Estimated API usage reached the ${log_state['budget_limit']:.2f} limit before {stage_name}."
        )

def create_chat_completion(client, model_name, messages, temperature, log_state=None, stage_name="api_call", response_format=None):
    """Wrap chat completions so token usage and cost are logged in one place."""
    enforce_budget(log_state, stage_name)
    format_label = response_format.get("type", "text") if isinstance(response_format, dict) else "text"
    append_run_log(
        log_state,
        f"{stage_name} started | model={model_name} | temperature={temperature} | response_format={format_label}",
        event="API",
    )
    try:
        request_kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format is not None:
            request_kwargs["response_format"] = response_format
        response = client.chat.completions.create(**request_kwargs)
    except Exception as exc:
        append_run_log(
            log_state,
            f"{stage_name} failed | model={model_name} | error={exc}",
            event="ERROR",
        )
        raise
    response_text = response.choices[0].message.content if response.choices else ""
    log_response_block(log_state, stage_name, response_text, event="REPLY")
    log_api_usage(log_state, model_name, stage_name, getattr(response, "usage", None))
    return response

def stop_for_budget(log_state):
    """Stop the Streamlit run with a clear warning once the API budget is exhausted."""
    budget_limit = log_state.get("budget_limit", MAX_API_COST_USD) if log_state else MAX_API_COST_USD
    estimated_cost = log_state.get("estimated_cost", 0.0) if log_state else 0.0
    message = (
        f"Stopped because the estimated API usage reached the budget limit of "
        f"${budget_limit:.2f}. Current estimate: ${estimated_cost:.4f}."
    )
    append_run_log(log_state, message, event="BUDGET")
    st.warning(message)
    st.stop()

def compute_discovery_sample_size(total_rows: int) -> int:
    """Scale discovery sample size with dataset size using caps."""
    if total_rows <= 0:
        return 0
    target = int(round(total_rows * DISCOVERY_SAMPLE_PCT))
    target = max(DISCOVERY_SAMPLE_MIN, target)
    target = min(DISCOVERY_SAMPLE_MAX, target)
    return min(total_rows, target)

def build_discovery_sample(df, rating_col, date_col):
    """Create a representative stratified sample using Model, ASIN fallback, rating, and date buckets."""
    if df.empty:
        return df.copy()

    target_size = compute_discovery_sample_size(len(df))
    if target_size >= len(df):
        return df.copy().reset_index(drop=True)

    sampled_df = df.copy()
    col_lookup = {col.lower(): col for col in sampled_df.columns}
    model_col = col_lookup.get("model")
    asin_col = col_lookup.get("asin")

    model_series = sampled_df[model_col] if model_col else pd.Series("", index=sampled_df.index)
    asin_series = sampled_df[asin_col] if asin_col else pd.Series("", index=sampled_df.index)

    product_bucket = model_series.fillna("").astype(str).str.strip()
    product_bucket = product_bucket.mask(product_bucket.eq(""), asin_series.fillna("").astype(str).str.strip())
    product_bucket = product_bucket.mask(product_bucket.eq(""), "(unknown product)")

    rating_bucket = sampled_df[rating_col].fillna("unknown").astype(str).str.strip()
    date_bucket = sampled_df[date_col].dt.to_period("M").astype(str).replace("NaT", "unknown-date")

    sampled_df["_stratum"] = (
        product_bucket.astype(str)
        + " | rating="
        + rating_bucket.astype(str)
        + " | date="
        + date_bucket.astype(str)
    )

    counts = sampled_df["_stratum"].value_counts()
    exact_allocations = counts / counts.sum() * target_size
    base_allocations = exact_allocations.astype(int)
    allocations = base_allocations.copy()
    remaining = target_size - int(base_allocations.sum())

    for stratum in (exact_allocations - base_allocations).sort_values(ascending=False).index:
        if remaining <= 0:
            break
        if allocations[stratum] < counts[stratum]:
            allocations[stratum] += 1
            remaining -= 1

    sampled_parts = []
    sampled_indices = set()
    for stratum, n_rows in allocations.items():
        if n_rows <= 0:
            continue
        group = sampled_df[sampled_df["_stratum"] == stratum]
        take_n = min(len(group), int(n_rows))
        if take_n <= 0:
            continue
        sampled_group = group.sample(n=take_n, random_state=DISCOVERY_SAMPLE_SEED)
        sampled_parts.append(sampled_group)
        sampled_indices.update(sampled_group.index.tolist())

    if sampled_parts:
        discovery_sample = pd.concat(sampled_parts)
    else:
        discovery_sample = sampled_df.sample(n=target_size, random_state=DISCOVERY_SAMPLE_SEED)

    if len(discovery_sample) < target_size:
        remaining_pool = sampled_df.drop(index=list(sampled_indices), errors="ignore")
        top_up_n = min(target_size - len(discovery_sample), len(remaining_pool))
        if top_up_n > 0:
            discovery_sample = pd.concat(
                [
                    discovery_sample,
                    remaining_pool.sample(n=top_up_n, random_state=DISCOVERY_SAMPLE_SEED),
                ]
            )

    return (
        discovery_sample.drop(columns=["_stratum"], errors="ignore")
        .sample(frac=1, random_state=DISCOVERY_SAMPLE_SEED)
        .reset_index(drop=True)
    )

def build_discovery_prompt_prefix():
    return """You are an expert product review analyst.

Read these customer reviews and identify the main complaint categories.
Some reviews may be largely positive and contain little or no complaint; ignore pure praise and focus on the genuine complaints that appear.
Reviews may be in any language; identify complaints regardless of language and name the categories in English.

Goal:
Create a short list of canonical issue categories that will be used later for row-by-row classification.

Rules:
- Return 5-15 categories when possible.
- Use short, standardized category names.
- Merge synonyms and near-duplicates into one canonical label.
- Do NOT create vague labels such as "No issue", "No dominant issue", "Other", "Misc", "General complaint", or "Uncategorized".
- Even if a review contains praise or mixed sentiment, focus on the main complaint if one is present.
- Prefer concrete issue names such as "Bad Taste", "Poor Dissolvability", "No Noticeable Effect", "Poor Packaging", "Side Effects", "Overpriced", or "Bad Smell".
- If multiple labels mean the same thing, choose one best canonical label only.
- Categories should describe the customer's problem, not the level of severity.
- Respond using the provided JSON schema only.

Reviews:
"""


def prepare_discovery_request(reviews, title_col, body_col, rating_col=None):
    """Fit the representative sample into a safe context window without truncating reviews."""
    selected_reviews, prompt, estimated_input_tokens = pack_prompt_items(
        reviews,
        format_item=lambda review, idx: build_review_block(review, idx, title_col, body_col, rating_col),
        prompt_prefix=build_discovery_prompt_prefix(),
        prompt_suffix="",
        reserved_output_tokens=DISCOVERY_RESERVED_OUTPUT_TOKENS,
        safe_context_budget=DISCOVERY_SAFE_CONTEXT_BUDGET,
    )
    return {
        "reviews": selected_reviews,
        "prompt": prompt,
        "estimated_input_tokens": estimated_input_tokens,
        "reserved_output_tokens": DISCOVERY_RESERVED_OUTPUT_TOKENS,
        "safe_context_budget": DISCOVERY_SAFE_CONTEXT_BUDGET,
    }


def discover_categories(client, prompt_text, log_state=None, stage_name="discover_categories"):
    """Use a representative sample of reviews to discover canonical issue categories."""
    prompt_tokens = estimate_input_tokens(prompt_text)
    append_run_log(
        log_state,
        (
            f"{stage_name} prompt prepared | estimated_input_tokens={prompt_tokens:,} | "
            f"reserved_output_tokens={DISCOVERY_RESERVED_OUTPUT_TOKENS:,} | "
            f"safe_context_budget={DISCOVERY_SAFE_CONTEXT_BUDGET:,} | "
            f"model_context_window={DISCOVERY_MODEL_LIMITS['context_window']:,} | "
            f"model_max_output_tokens={DISCOVERY_MODEL_LIMITS['max_output_tokens']:,}"
        ),
        event="DATA",
    )

    response = create_chat_completion(
        client,
        DISCOVERY_MODEL,
        [{"role": "user", "content": prompt_text}],
        temperature=0.2,
        log_state=log_state,
        stage_name=stage_name,
        response_format=DISCOVER_CATEGORIES_RESPONSE_FORMAT,
    )
    response_text = response.choices[0].message.content
    parsed = parse_json_response(response_text, log_state=log_state, stage_name=stage_name)
    if not isinstance(parsed, dict):
        raise ValueError(
            "Category discovery did not return a JSON object. "
            f"See the logged REPLY block for stage '{stage_name}'."
        )
    categories = [clean_category_label(item) for item in parsed.get("categories", []) if clean_text(item)]
    if not categories:
        raise ValueError(
            "Category discovery returned no usable categories. "
            f"See the logged REPLY block for stage '{stage_name}'."
        )
    return list(dict.fromkeys(categories))

def parse_classification_items(parsed):
    """Accept either a raw list or a wrapped object and normalize it into a list."""
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("items", "results", "classifications"):
            if isinstance(parsed.get(key), list):
                return parsed[key]
    raise ValueError("Classification output did not include a usable items array.")

def classification_reserved_output_tokens(review_count):
    """Reserve enough output space for a JSON response with one item per review."""
    return CLASSIFICATION_RESERVED_OUTPUT_TOKENS_BASE + (
        review_count * CLASSIFICATION_RESERVED_OUTPUT_TOKENS_PER_REVIEW
    )


def build_classification_prompt_prefix(categories, allow_new_category):
    cats_str = ", ".join(categories)
    category_rule = (
        "Only create a new category if none of the available categories genuinely fit."
        if allow_new_category
        else "You MUST choose from the available categories and must not invent a new category."
    )
    return f"""You are classifying product reviews into standardized complaint categories.

Available canonical categories:
{cats_str}

Task:
For each review, assign the SINGLE best issue category, rate its severity, and write a short review-specific justification.

Each review is prefixed with its star rating as "[N stars]". Reviews may be in any language.

Category rules:
- Choose exactly one dominant complaint category per review.
- Use one of the available categories whenever possible.
- {category_rule}
- Classify the complaint regardless of the review's language.
- If the review has NO genuine complaint, assign the category "{NO_COMPLAINT_LABEL}". This includes reviews that are entirely positive, and reviews whose only "issue" is a neutral observation or is actually praise (for example "good quality for price" or "works but turns urine blue").
- A 4 or 5 star review is usually "{NO_COMPLAINT_LABEL}" unless it explicitly states a real problem the reviewer experienced.
- The following are NOT complaints; classify them as "{NO_COMPLAINT_LABEL}":
  - merely naming a benefit or topic the product is for (for example "helps with circulation" or "good for hair growth");
  - general advice or cautions that apply to anyone (for example "consult your doctor" or "if you are allergic to soy, do not take this") when the reviewer reports no problem of their own;
  - a personal preference or routine rather than a defect (for example "I take only one capsule instead of two");
  - a stated reason for buying, such as a bare answer to "Why did you pick this product?" (for example "Price" or "good value") — this means price was an attraction, not a complaint about high price.
- Do NOT use vague labels such as "No issue", "Other", "Misc", or "Uncategorized"; use "{NO_COMPLAINT_LABEL}" when there is genuinely nothing to complain about.
- When a review contains more than one genuine complaint, classify the SINGLE most severe one (greatest safety, health, or financial impact), not the first mentioned.
- When the review is genuinely mixed (clear praise plus a clear complaint), classify the complaint, not the praise.
- Merge complaint variants into the closest canonical issue when they mean the same thing.

Severity rules:
- Rate how serious the complaint is for the customer: "High", "Medium", or "Low".
- "High" = safety or health risk, product unusable, or significant harm or financial loss.
- "Medium" = a real problem that meaningfully hurts the experience.
- "Low" = a minor annoyance or nitpick.
- Use the star rating as a signal: a complaint in a 1-2 star review is rarely "Low" (usually "Medium" or "High"); a complaint inside a 4-5 star review is usually "Low".
- Use "None" only when the category is "{NO_COMPLAINT_LABEL}".

Justification rules:
- The justification must be specific to that review, not generic to the category.
- The justification must be short: 2 to 6 words.
- Always write the justification in English, even when the review is in another language.
- It should describe the actual complaint mentioned in the review; for "{NO_COMPLAINT_LABEL}" use a short positive summary (for example "Happy with product").
- Do not write full sentences.
- Respond using the provided JSON schema only.

Reviews:
"""


def prepare_classification_batch(records, categories, title_col, body_col, allow_new_category=True, rating_col=None):
    """Build the largest batch that fits under the safe context budget."""
    selected_records, prompt, estimated_input_tokens = pack_prompt_items(
        records,
        format_item=lambda review, idx: build_review_block(review, idx, title_col, body_col, rating_col),
        prompt_prefix=build_classification_prompt_prefix(categories, allow_new_category),
        prompt_suffix="",
        reserved_output_tokens=classification_reserved_output_tokens,
        safe_context_budget=CLASSIFICATION_SAFE_CONTEXT_BUDGET,
        max_items=BATCH_SIZE,
    )
    reserved_output_tokens = classification_reserved_output_tokens(len(selected_records))
    return {
        "records": selected_records,
        "prompt": prompt,
        "estimated_input_tokens": estimated_input_tokens,
        "reserved_output_tokens": reserved_output_tokens,
        "safe_context_budget": CLASSIFICATION_SAFE_CONTEXT_BUDGET,
    }


def classify_batch(client, prompt_text, batch_size, log_state=None, stage_name="classify_batch"):
    """Classify a pre-sized batch into one category plus a row-specific justification."""
    append_run_log(
        log_state,
        (
            f"{stage_name} prompt prepared | reviews={batch_size:,} | "
            f"estimated_input_tokens={estimate_input_tokens(prompt_text):,} | "
            f"reserved_output_tokens={classification_reserved_output_tokens(batch_size):,} | "
            f"safe_context_budget={CLASSIFICATION_SAFE_CONTEXT_BUDGET:,} | "
            f"model_context_window={CLASSIFICATION_MODEL_LIMITS['context_window']:,} | "
            f"model_max_output_tokens={CLASSIFICATION_MODEL_LIMITS['max_output_tokens']:,}"
        ),
        event="DATA",
    )

    response = create_chat_completion(
        client,
        CLASSIFY_MODEL,
        [{"role": "user", "content": prompt_text}],
        temperature=0.1,
        log_state=log_state,
        stage_name=stage_name,
        response_format=CLASSIFICATION_RESPONSE_FORMAT,
    )
    response_text = response.choices[0].message.content
    parsed = parse_classification_items(
        parse_json_response(response_text, log_state=log_state, stage_name=stage_name)
    )
    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            item_index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        category = sanitize_category_label(item.get("category"))
        severity = normalize_severity(item.get("severity"))
        # Enforce the No Complaint <-> None invariant in both directions: a None
        # severity means the review had no real complaint, so it is not tagged
        # with a leftover topic category.
        category, severity = couple_category_severity(category, severity)
        normalized.append(
            {
                "index": item_index,
                "category": category,
                "severity": severity,
                "justification": clean_text(item.get("justification"), fallback="Needs review"),
            }
        )
    return normalized

def evenly_spaced_indices(length, count):
    """Pick deterministic indices spread across a sorted list."""
    if count >= length:
        return list(range(length))
    return [int(i * length / count) for i in range(count)]

def select_category_evidence(group_df, body_col):
    """Pick representative rows for category consolidation."""
    if len(group_df) <= MAX_CATEGORY_EVIDENCE:
        return group_df.copy()

    deduped = group_df.copy()
    deduped["_evidence_key"] = (
        deduped["Justification"].fillna("").astype(str).str.strip().str.lower()
        + " || "
        + deduped[body_col].fillna("").astype(str).str.slice(0, 220).str.strip().str.lower()
    )
    deduped = deduped.drop_duplicates("_evidence_key").copy()

    if len(deduped) <= MAX_CATEGORY_EVIDENCE:
        return deduped.drop(columns=["_evidence_key"], errors="ignore")

    deduped["_sort_key"] = (
        deduped["Justification"].fillna("").astype(str).str.lower()
        + " || "
        + deduped[body_col].fillna("").astype(str).str.slice(0, 120).str.lower()
    )
    deduped = deduped.sort_values("_sort_key").reset_index(drop=True)
    picked = deduped.iloc[evenly_spaced_indices(len(deduped), MAX_CATEGORY_EVIDENCE)].copy()
    return picked.drop(columns=["_evidence_key", "_sort_key"], errors="ignore")

def build_consolidation_payload(results_df, title_col, body_col):
    """Create representative evidence bundles for each provisional category."""
    payload = []
    for category in sorted(results_df["Issue_Category"].dropna().unique()):
        # "No Complaint" is a reserved outcome, not a complaint label to merge.
        if clean_category_label(category) == NO_COMPLAINT_LABEL:
            continue
        group = results_df[results_df["Issue_Category"] == category].copy()
        evidence_rows = select_category_evidence(group, body_col)
        examples = []
        for _, row in evidence_rows.iterrows():
            review_excerpt = clean_text(row.get(body_col, ""))
            review_excerpt = review_excerpt[:220] + ("..." if len(review_excerpt) > 220 else "")
            example = {
                "justification": clean_text(row.get("Justification", "")),
                "review_excerpt": review_excerpt,
            }
            if title_col:
                example["title"] = clean_text(row.get(title_col, ""))
            examples.append(example)
        payload.append(
            {
                "category": clean_category_label(category),
                "row_count": int(len(group)),
                "examples": examples,
            }
        )
    return payload

def consolidate_categories(client, results_df, title_col, body_col, log_state=None, stage_name="consolidate_categories"):
    """Merge duplicate categories and flag vague mixed buckets for reclassification."""
    payload = build_consolidation_payload(results_df, title_col, body_col)
    prompt = f"""You are cleaning issue-category labels produced from product review classification.

Task:
- Merge duplicate or overlapping issue categories into one canonical label.
- Remap vague labels to a concrete category only when the evidence under that label is coherent.
- If a category is internally mixed and should not be mapped to a single label, add it to "reclassify_categories".

Rules:
- Use the evidence examples under each label, not label wording alone.
- Keep final labels short, concrete, and standardized.
- Do NOT keep vague labels such as "No issue", "No dominant issue", "Other", "Misc", or "Uncategorized" unless the evidence truly shows no complaint.
- If two labels describe the same underlying complaint, map both to one best canonical label.
- If a label contains multiple different complaint families, do not force one mapping; send it to "reclassify_categories".
- Respond using the provided JSON schema only.

Category evidence:
{json.dumps(payload, ensure_ascii=False)}"""

    response = create_chat_completion(
        client,
        DISCOVERY_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        log_state=log_state,
        stage_name=stage_name,
        response_format=CONSOLIDATION_RESPONSE_FORMAT,
    )
    response_text = response.choices[0].message.content
    parsed = parse_json_response(response_text, log_state=log_state, stage_name=stage_name)
    if not isinstance(parsed, dict):
        raise ValueError(
            f"Category consolidation did not return a JSON object. "
            f"See the logged REPLY block for stage '{stage_name}'."
        )

    mapping = {
        clean_category_label(item.get("source")): clean_category_label(item.get("target"))
        for item in parsed.get("mappings", [])
        if isinstance(item, dict) and clean_text(item.get("source")) and clean_text(item.get("target"))
    }
    # Only genuinely vague buckets may be dissolved and reclassified. The model
    # tends to over-flag concrete categories (e.g. "Stomach Pain") here, which
    # then get force-fit into the wrong surviving category — so guard in code.
    reclassify_categories = [
        clean_category_label(label)
        for label in parsed.get("reclassify_categories", [])
        if clean_text(label)
        and clean_category_label(label) != NO_COMPLAINT_LABEL
        and is_vague_category_label(label)
    ]

    existing_categories = [clean_category_label(cat) for cat in results_df["Issue_Category"].dropna().unique()]
    for category in existing_categories:
        if category not in reclassify_categories and category not in mapping:
            mapping[category] = category

    canonical_categories = [
        clean_category_label(label)
        for label in parsed.get("canonical_categories", [])
        if clean_text(label)
    ]
    canonical_categories = list(dict.fromkeys(canonical_categories + list(mapping.values())))
    if not canonical_categories:
        canonical_categories = sorted(set(mapping.values()))

    return {
        "mapping": mapping,
        "canonical_categories": list(dict.fromkeys(canonical_categories)),
        "reclassify_categories": list(dict.fromkeys(reclassify_categories)),
    }

def apply_category_mapping(results_df, mapping):
    """Apply a category mapping to the results dataframe."""
    mapped_df = results_df.copy()
    mapped_df["Issue_Category"] = mapped_df["Issue_Category"].apply(
        lambda value: mapping.get(clean_category_label(value), clean_category_label(value))
    )
    return mapped_df

def reclassify_mixed_categories(client, results_df, categories_to_reclassify, categories, title_col, body_col, log_state=None, rating_col=None):
    """Reclassify rows that landed in vague or internally mixed labels."""
    categories_to_reclassify = {
        clean_category_label(category)
        for category in categories_to_reclassify
        if clean_text(category)
    }
    if not categories_to_reclassify:
        return results_df

    available_categories = [
        clean_category_label(category)
        for category in categories
        if clean_category_label(category) not in categories_to_reclassify
    ]
    if not available_categories:
        return results_df

    reclassify_df = results_df[
        results_df["Issue_Category"].isin(categories_to_reclassify)
    ].copy()
    if reclassify_df.empty:
        return results_df

    reclassify_df = reclassify_df.reset_index().rename(columns={"index": "_row_index"})
    records = reclassify_df.to_dict("records")
    updated_rows = []
    cursor = 0
    batch_idx = 0

    while cursor < len(records):
        batch_idx += 1
        try:
            prepared_batch = prepare_classification_batch(
                records[cursor:],
                available_categories,
                title_col,
                body_col,
                allow_new_category=False,
                rating_col=rating_col,
            )
            batch = prepared_batch["records"]
            parsed = classify_batch(
                client,
                prepared_batch["prompt"],
                len(batch),
                log_state=log_state,
                stage_name=f"reclassify_mixed_categories_{batch_idx}",
            )
        except ValueError as exc:
            append_run_log(
                log_state,
                f"Reclassification batch {batch_idx} could not be prepared | error={exc}",
                event="ERROR",
            )
            raise
        result_map = {item["index"]: item for item in parsed}
        for idx, row in enumerate(batch):
            item = result_map.get(
                idx + 1,
                {
                    "category": row.get("Issue_Category", "Needs Review"),
                    "severity": row.get("Severity", DEFAULT_SEVERITY),
                    "justification": row.get("Justification", "Needs review"),
                },
            )
            updated_rows.append(
                {
                    "_row_index": row["_row_index"],
                    "Issue_Category": clean_category_label(item.get("category", row.get("Issue_Category"))),
                    "Severity": normalize_severity(item.get("severity"), fallback=row.get("Severity", DEFAULT_SEVERITY)),
                    "Justification": clean_text(item.get("justification"), fallback=row.get("Justification", "Needs review")),
                }
            )
        cursor += len(batch)

    updated_df = pd.DataFrame(updated_rows).set_index("_row_index")
    final_df = results_df.copy()
    final_df.loc[updated_df.index, "Issue_Category"] = updated_df["Issue_Category"].values
    final_df.loc[updated_df.index, "Severity"] = updated_df["Severity"].values
    final_df.loc[updated_df.index, "Justification"] = updated_df["Justification"].values
    return final_df

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
    file_extension = get_upload_extension(uploaded.name)
    sheet_name = None

    if is_csv_upload(uploaded.name):
        df = pd.read_csv(io.BytesIO(file_bytes), encoding=detect_encoding(file_bytes))
    else:
        excel_engine = "xlrd" if file_extension == ".xls" else None
        workbook = pd.ExcelFile(io.BytesIO(file_bytes), engine=excel_engine)
        sheet_name = st.selectbox("Select spreadsheet sheet", options=workbook.sheet_names, index=0)
        df = load_excel_sheet(file_bytes, sheet_name=sheet_name, engine=excel_engine)
    st.success(f"✅ Loaded **{len(df):,} rows** and **{len(df.columns)} columns**")
    with st.expander("Preview first 5 rows"):
        st.dataframe(df.head(), width="stretch")
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

# ── Step 3: Map columns ───────────────────────────────────────────────────────
st.divider()
st.subheader("Step 2 — Map Your Columns")

cols = list(df.columns)

col1, col2, col3, col4 = st.columns(4)
with col1:
    title_col = st.selectbox("📌 Review Title Column", options=["(none)"] + cols)
with col2:
    body_col = st.selectbox("📝 Review Body Column", options=["(select)"] + cols)
with col3:
    rating_col = st.selectbox("⭐ Star Rating Column", options=["(select)"] + cols)
with col4:
    date_col = st.selectbox("📅 Review Date Column", options=["(select)"] + cols)

review_window_months = st.number_input(
    "Review window (months)",
    min_value=1,
    max_value=120,
    value=12,
    step=1,
    help="Keeps reviews from the latest review date in the sheet minus this many months.",
)
review_window_label = format_review_window_label(review_window_months)

rating_scope = st.selectbox(
    "⭐ Ratings to analyze",
    options=list(RATING_SCOPES.keys()),
    index=list(RATING_SCOPES.keys()).index(DEFAULT_RATING_SCOPE),
    format_func=lambda key: RATING_SCOPES[key],
    help=(
        "Which reviews to mine for complaints. 4-5 star reviews can still contain "
        f"real issues, but they are usually milder — they may also land in '{NO_COMPLAINT_LABEL}'."
    ),
)

current_results_context = build_results_context(
    upload_name=uploaded.name,
    file_bytes=file_bytes,
    sheet_name=sheet_name,
    title_col=title_col,
    body_col=body_col,
    rating_col=rating_col,
    date_col=date_col,
    review_window_months=review_window_months,
    rating_scope=rating_scope,
)
clear_stale_results(st.session_state, current_results_context)

if body_col == "(select)" or rating_col == "(select)" or date_col == "(select)":
    st.warning("Please map the Review Body, Star Rating, and Review Date columns to continue.")
    st.stop()

# Repair mojibake in the mapped text columns so both the model and the exported
# CSV see clean text (e.g. "MagnÃ­fico" -> "Magnífico").
for text_col in {body_col, title_col}:
    if text_col in df.columns:
        df[text_col] = df[text_col].map(lambda v: fix_mojibake(v) if isinstance(v, str) else v)

# Filter to the selected review window, then keep reviews within the chosen rating scope
try:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_localize(None)
    latest_sheet_date = df[date_col].dropna().max()

    if pd.isna(latest_sheet_date):
        st.error(f"No valid dates were found in the '{date_col}' column.")
        st.stop()

    latest_sheet_date = latest_sheet_date.normalize()
    cutoff_date = latest_sheet_date - pd.DateOffset(months=review_window_months)
    df[rating_col] = pd.to_numeric(df[rating_col], errors="coerce")
    all_reviews_df = df.reset_index(drop=True)
    recent_df = all_reviews_df[
        all_reviews_df[date_col].notna() & (all_reviews_df[date_col] >= cutoff_date)
    ].reset_index(drop=True)
    selected_df = filter_reviews_by_scope(recent_df, rating_col, rating_scope).reset_index(drop=True)

    st.info(
        f"Using **{len(all_reviews_df):,} total reviews** from the selected sheet, regardless of verified purchase status."
    )
    st.info(
        f"Latest review date in the selected sheet is **{latest_sheet_date.date()}**."
    )
    st.info(
        f"Keeping **{len(recent_df):,} reviews** dated between **{cutoff_date.date()}** and **{latest_sheet_date.date()}**."
    )
    st.info(
        f"Found **{len(selected_df):,} reviews** matching scope **{RATING_SCOPES[rating_scope]}** "
        f"within the selected **{review_window_label}** window."
    )
except Exception as e:
    st.error(f"Could not parse the date or rating column: {e}")
    st.stop()

if len(all_reviews_df) == 0:
    st.warning("No reviews were found in this sheet.")
    st.stop()

if len(recent_df) == 0:
    st.warning(
        f"No reviews were found in the selected {review_window_label} window between {cutoff_date.date()} and {latest_sheet_date.date()}."
    )
    st.stop()

if len(selected_df) == 0:
    st.warning(
        f"No reviews matching scope '{RATING_SCOPES[rating_scope]}' were found in the selected "
        f"{review_window_label} window between {cutoff_date.date()} and {latest_sheet_date.date()}."
    )
    st.stop()

with st.expander("Preview filtered reviews"):
    st.dataframe(selected_df, use_container_width=True)

# ── Step 4: Classify ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Step 3 — Classify Reviews")

col_a, col_b = st.columns(2)
with col_a:
    st.metric("Discovery model", DISCOVERY_MODEL)
with col_b:
    st.metric("Classification model", CLASSIFY_MODEL)

if st.button("🤖 Start Classification", use_container_width=True):
    effective_title_col = None if title_col == "(none)" else title_col
    run_log = create_run_logger()
    st.session_state["run_log_path"] = run_log["path"]
    records = selected_df.to_dict("records")
    discovery_sample_df = build_discovery_sample(selected_df, rating_col, date_col)
    discovery_records = discovery_sample_df.to_dict("records")
    append_run_log(
        run_log,
        (
            f"Filtered dataset prepared | total_rows={len(records):,} | "
            f"discovery_sample_rows={len(discovery_records):,} | "
            f"discovery_model={DISCOVERY_MODEL} | classification_model={CLASSIFY_MODEL}"
        ),
        event="DATA",
    )

    # Discover categories
    with st.spinner("Discovering issue categories from your reviews…"):
        try:
            prepared_discovery = prepare_discovery_request(
                discovery_records,
                effective_title_col,
                body_col,
                rating_col=rating_col,
            )
            categories = discover_categories(
                client,
                prepared_discovery["prompt"],
                log_state=run_log,
            )
            if run_log.get("budget_reached"):
                stop_for_budget(run_log)
        except ApiBudgetExceededError:
            stop_for_budget(run_log)
        except Exception as e:
            append_run_log(run_log, f"Category discovery failed | error={e}", event="ERROR")
            st.error(f"Category discovery failed: {e}")
            st.stop()

    st.info(
        f"Built a representative discovery sample of **{len(prepared_discovery['reviews']):,} reviews** "
        f"from **{len(records):,} filtered reviews**."
    )
    st.success(f"✅ Discovered **{len(categories)} categories**: {', '.join(categories)}")
    append_run_log(
        run_log,
        f"Discovered categories | count={len(categories)} | labels={', '.join(categories)}",
        event="RESULT",
    )

    # Classify in batches
    progress_bar = st.progress(0, text="Starting classification…")
    status_text = st.empty()

    results = []
    total = len(records)
    processed = 0
    batch_idx = 0

    while processed < total:
        batch_idx += 1
        try:
            prepared_batch = prepare_classification_batch(
                records[processed:],
                categories,
                effective_title_col,
                body_col,
                rating_col=rating_col,
            )
            batch = prepared_batch["records"]
            start = processed
            end = processed + len(batch)
            status_text.text(f"Classifying reviews {start+1}–{end} of {total}…")
            append_run_log(
                run_log,
                f"Classification batch {batch_idx} started | rows={start + 1}-{end}",
                event="STEP",
            )
            parsed = classify_batch(
                client,
                prepared_batch["prompt"],
                len(batch),
                log_state=run_log,
                stage_name=f"classify_batch_{batch_idx}",
            )
            result_map = {item["index"]: item for item in parsed}
            for idx, row in enumerate(batch):
                item = result_map.get(
                    idx + 1,
                    {"category": "Needs Review", "severity": DEFAULT_SEVERITY, "justification": "Needs review"},
                )
                row_copy = dict(row)
                row_copy["Issue_Category"] = clean_category_label(item.get("category"))
                row_copy["Severity"] = normalize_severity(item.get("severity"))
                row_copy["Justification"] = clean_text(item.get("justification"), fallback="Needs review")
                results.append(row_copy)
            if run_log.get("budget_reached"):
                stop_for_budget(run_log)
        except ValueError as e:
            append_run_log(
                run_log,
                f"Classification batch {batch_idx} could not be prepared | error={e}",
                event="ERROR",
            )
            st.error(f"Classification stopped: {e}")
            st.stop()
        except ApiBudgetExceededError:
            stop_for_budget(run_log)
        except Exception as e:
            append_run_log(
                run_log,
                f"Classification batch {batch_idx} failed | error={e}",
                event="ERROR",
            )
            for row in batch:
                row_copy = dict(row)
                row_copy["Issue_Category"] = "Classification Error"
                row_copy["Severity"] = DEFAULT_SEVERITY
                row_copy["Justification"] = "Needs review"
                results.append(row_copy)
        processed += len(batch)

        progress_bar.progress(
            processed / total,
            text=f"Processed {processed}/{total} reviews"
        )
        append_run_log(
            run_log,
            f"Classification batch {batch_idx} completed",
            event="STEP",
        )

    status_text.empty()
    progress_bar.empty()

    results_df = pd.DataFrame(results)

    with st.spinner("Consolidating categories and resolving vague labels…"):
        try:
            append_run_log(run_log, "Category consolidation started", event="STEP")
            consolidation = consolidate_categories(
                client,
                results_df,
                effective_title_col,
                body_col,
                log_state=run_log,
                stage_name="consolidate_categories_initial",
            )
            results_df = apply_category_mapping(results_df, consolidation["mapping"])
            if run_log.get("budget_reached"):
                stop_for_budget(run_log)

            if consolidation["reclassify_categories"]:
                append_run_log(
                    run_log,
                    "Reclassifying mixed/vague categories | labels="
                    + ", ".join(consolidation["reclassify_categories"]),
                    event="STEP",
                )
                results_df = reclassify_mixed_categories(
                    client,
                    results_df,
                    consolidation["reclassify_categories"],
                    consolidation["canonical_categories"],
                    effective_title_col,
                    body_col,
                    log_state=run_log,
                    rating_col=rating_col,
                )
                if run_log.get("budget_reached"):
                    stop_for_budget(run_log)
                consolidation = consolidate_categories(
                    client,
                    results_df,
                    effective_title_col,
                    body_col,
                    log_state=run_log,
                    stage_name="consolidate_categories_final",
                )
                results_df = apply_category_mapping(results_df, consolidation["mapping"])
                if run_log.get("budget_reached"):
                    stop_for_budget(run_log)

            categories = consolidation["canonical_categories"]
            append_run_log(
                run_log,
                f"Final canonical categories | count={len(categories)} | labels={', '.join(categories)}",
                event="RESULT",
            )
        except ApiBudgetExceededError:
            stop_for_budget(run_log)
        except Exception as e:
            append_run_log(run_log, f"Category consolidation failed | error={e}", event="ERROR")
            st.error(f"Category consolidation failed: {e}")
            st.stop()

    results_df["Issue_Category"] = results_df["Issue_Category"].apply(clean_category_label)
    results_df["Severity"] = results_df["Severity"].apply(normalize_severity)
    # Final enforcement of the No Complaint <-> None invariant in both directions
    # (see couple_category_severity): No Complaint has no severity, and a None
    # severity means there was no complaint to categorize.
    results_df.loc[results_df["Issue_Category"] == NO_COMPLAINT_LABEL, "Severity"] = SEVERITY_NONE
    results_df.loc[results_df["Severity"] == SEVERITY_NONE, "Issue_Category"] = NO_COMPLAINT_LABEL
    results_df["Justification"] = results_df["Justification"].apply(
        lambda value: clean_text(value, fallback="Needs review")
    )

    st.session_state["results"] = results_df
    st.session_state["categories"] = categories
    st.session_state["results_context"] = current_results_context
    st.session_state["run_log_summary"] = {
        "prompt_tokens": run_log["prompt_tokens"],
        "completion_tokens": run_log["completion_tokens"],
        "total_tokens": run_log["total_tokens"],
        "estimated_cost": run_log["estimated_cost"],
    }
    append_run_log(
        run_log,
        (
            f"Run completed | prompt_tokens={run_log['prompt_tokens']:,} | "
            f"completion_tokens={run_log['completion_tokens']:,} | "
            f"total_tokens={run_log['total_tokens']:,} | "
            f"estimated_cost=${run_log['estimated_cost']:.6f}"
        ),
        event="RUN",
    )
    st.success(f"✅ Done! Classified **{len(results)} reviews** with row-specific justifications.")
    st.caption(
        f"Run log saved to `{run_log['path']}` | "
        f"Estimated API cost: ${run_log['estimated_cost']:.4f} | "
        f"Total tokens: {run_log['total_tokens']:,}"
    )

# ── Step 5: Results ───────────────────────────────────────────────────────────
if "results" in st.session_state:
    result_df = st.session_state["results"]

    st.divider()
    st.subheader("Step 4 — Results")
    if "run_log_summary" in st.session_state and "run_log_path" in st.session_state:
        run_log_summary = st.session_state["run_log_summary"]
        st.caption(
            f"Run log: `{st.session_state['run_log_path']}` | "
            f"Estimated API cost: ${run_log_summary['estimated_cost']:.4f} | "
            f"Total tokens: {run_log_summary['total_tokens']:,}"
        )

    # Issue summary / pivot
    summary = result_df["Issue_Category"].value_counts().reset_index()
    summary.columns = ["Issue Category", "Count"]
    summary["% of Reviews"] = (
        summary["Count"] / len(result_df) * 100
    ).round(1).astype(str) + "%"

    st.markdown("**Issue Breakdown (Pivot Summary)**")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.bar_chart(summary.set_index("Issue Category")["Count"])

    # Severity breakdown
    if "Severity" in result_df.columns:
        severity_summary = result_df["Severity"].value_counts().reset_index()
        severity_summary.columns = ["Severity", "Count"]
        st.markdown("**Severity Breakdown**")
        st.dataframe(severity_summary, use_container_width=True, hide_index=True)

    # Full classified table
    with st.expander("View all classified reviews"):
        display_cols = [c for c in [
            title_col if title_col != "(none)" else None,
            rating_col, body_col, "Issue_Category", "Severity", "Justification"
        ] if c and c in result_df.columns]
        st.dataframe(result_df[display_cols], use_container_width=True)

    # Export — sanitize against CSV/formula injection (OWASP) and add a UTF-8 BOM
    # so Excel opens accented characters correctly.
    st.divider()
    export_df = result_df.copy()
    for col in export_df.columns:
        export_df[col] = export_df[col].map(sanitize_csv_field)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ Download Classified Reviews CSV",
        data=csv_bytes,
        file_name="classified_reviews.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.caption("CSV includes all original columns + new `Issue_Category`, `Severity`, and `Justification` columns — ready to pivot in Excel.")
