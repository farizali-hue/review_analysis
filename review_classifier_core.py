import io
import hashlib
import math
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, MutableMapping, TypeVar

import pandas as pd
import re

CHARS_PER_TOKEN_ESTIMATE = 4
DEFAULT_SAFE_CONTEXT_RATIO = 0.8
FALLBACK_SAFE_CONTEXT_BUDGET = 24_000
MODEL_TOKEN_LIMITS = {
    "gpt-5-mini": {"context_window": 400_000, "max_output_tokens": 128_000},
    "gpt-5-nano": {"context_window": 400_000, "max_output_tokens": 128_000},
}
MODEL_LIMIT_ALIASES = {
    "gpt-5.4-mini": "gpt-5-mini",
    "gpt-5.4-nano": "gpt-5-nano",
}
RESULT_SESSION_KEYS = (
    "results",
    "categories",
    "run_log_summary",
    "run_log_path",
    "results_context",
)
HEADER_SCAN_ROW_LIMIT = 10
T = TypeVar("T")

# Reviews with no genuine complaint (common in 4-5 star reviews) land here
# instead of being forced into a fabricated issue category.
NO_COMPLAINT_LABEL = "No Complaint"
SEVERITY_LEVELS = ("High", "Medium", "Low")
SEVERITY_NONE = "None"
DEFAULT_SEVERITY = "Medium"

# Which star ratings to mine for negative issues. "4_and_5" and "all" still
# extract complaints, but complaints in high-rated reviews tend to be milder.
RATING_SCOPES = {
    "below_4": "Negative only (rating below 4)",
    "4_and_5": "High ratings only (4 and 5 stars)",
    "all": "All ratings",
}
DEFAULT_RATING_SCOPE = "below_4"


def clean_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except TypeError:
        pass
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or fallback


def format_review_window_label(months: int) -> str:
    return f"{months} month" if months == 1 else f"{months} months"


def clean_category_label(label: Any, fallback: str = "Needs Review") -> str:
    text = clean_text(label, fallback="")
    text = text.strip(" '\"`")
    return text or fallback


def filter_reviews_by_scope(
    df: pd.DataFrame,
    rating_col: str,
    scope: str = DEFAULT_RATING_SCOPE,
) -> pd.DataFrame:
    """Filter reviews to the requested star-rating scope.

    Rows whose rating is missing or non-numeric are always dropped.
    """
    if scope not in RATING_SCOPES:
        raise ValueError(
            f"Unknown rating scope '{scope}'. Expected one of {sorted(RATING_SCOPES)}."
        )
    ratings = pd.to_numeric(df[rating_col], errors="coerce")
    if scope == "below_4":
        mask = ratings < 4
    elif scope == "4_and_5":
        mask = ratings >= 4
    else:  # "all"
        mask = ratings.notna()
    return df[mask].reset_index(drop=True)


def normalize_severity(value: Any, fallback: str = DEFAULT_SEVERITY) -> str:
    """Coerce a model-provided severity into one of High/Medium/Low/None."""
    text = clean_text(value, fallback="").strip().lower()
    canonical = {level.lower(): level for level in SEVERITY_LEVELS}
    canonical[SEVERITY_NONE.lower()] = SEVERITY_NONE
    return canonical.get(text, fallback)


def estimate_input_tokens(text: str, chars_per_token: int = CHARS_PER_TOKEN_ESTIMATE) -> int:
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be greater than zero.")
    if not text:
        return 0
    return max(1, math.ceil(len(str(text)) / chars_per_token))


def normalize_model_limit_name(model_name: str) -> str:
    normalized = (model_name or "").strip().lower()
    return MODEL_LIMIT_ALIASES.get(normalized, normalized)


def resolve_model_token_limits(model_name: str) -> dict[str, int]:
    normalized = normalize_model_limit_name(model_name)
    limits = MODEL_TOKEN_LIMITS.get(normalized)
    if not limits:
        raise KeyError(f"No token limits are configured for model '{model_name}'.")
    return dict(limits)


def compute_safe_context_budget(
    model_name: str,
    safety_ratio: float = DEFAULT_SAFE_CONTEXT_RATIO,
    fallback_budget: int = FALLBACK_SAFE_CONTEXT_BUDGET,
) -> int:
    if safety_ratio <= 0 or safety_ratio >= 1:
        raise ValueError("safety_ratio must be between 0 and 1.")
    try:
        limits = resolve_model_token_limits(model_name)
    except KeyError:
        return fallback_budget
    return max(fallback_budget, math.floor(limits["context_window"] * safety_ratio))


def _resolve_reserved_output_tokens(
    reserved_output_tokens: int | Callable[[int], int],
    item_count: int,
) -> int:
    resolved = reserved_output_tokens(item_count) if callable(reserved_output_tokens) else reserved_output_tokens
    if resolved < 0:
        raise ValueError("reserved_output_tokens must be zero or greater.")
    return int(resolved)


def pack_prompt_items(
    items: Sequence[T],
    format_item: Callable[[T, int], str],
    prompt_prefix: str,
    prompt_suffix: str,
    reserved_output_tokens: int | Callable[[int], int],
    safe_context_budget: int,
    max_items: int | None = None,
) -> tuple[list[T], str, int]:
    if safe_context_budget <= 0:
        raise ValueError("safe_context_budget must be greater than zero.")

    selected_items: list[T] = []
    selected_blocks: list[str] = []
    candidate_items = list(items[:max_items]) if max_items is not None else list(items)

    for item in candidate_items:
        next_block = format_item(item, len(selected_items) + 1)
        candidate_blocks = selected_blocks + [next_block]
        candidate_prompt = f"{prompt_prefix}{'\n\n'.join(candidate_blocks)}{prompt_suffix}"
        estimated_input_tokens = estimate_input_tokens(candidate_prompt)
        reserved_tokens = _resolve_reserved_output_tokens(
            reserved_output_tokens,
            len(candidate_blocks),
        )
        if estimated_input_tokens + reserved_tokens < safe_context_budget:
            selected_items.append(item)
            selected_blocks.append(next_block)
            continue
        break

    if not selected_items:
        raise ValueError(
            "A single review exceeds the configured token budget. "
            "Increase the safe context budget or reduce the reserved output tokens."
        )

    prompt = f"{prompt_prefix}{'\n\n'.join(selected_blocks)}{prompt_suffix}"
    return selected_items, prompt, estimate_input_tokens(prompt)


def build_review_block(
    record: dict[str, Any],
    index: int,
    title_col: str | None,
    body_col: str,
) -> str:
    title = clean_text(record.get(title_col, "")) if title_col else ""
    body = clean_text(record.get(body_col, ""))
    if title:
        return f"{index}. Title: {title}\n   Review: {body}"
    return f"{index}. Review: {body}"


def get_upload_extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def is_csv_upload(filename: str | None) -> bool:
    return get_upload_extension(filename) == ".csv"


def _is_probable_header_label(text: str) -> bool:
    normalized = clean_text(text, fallback="").lower()
    if not normalized:
        return False
    if normalized.startswith(("http://", "https://", "www.")):
        return False
    compact = normalized.replace(",", "")
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", compact):
        return False
    return True


def _score_header_candidate(values: Sequence[Any]) -> tuple[int, int, int, int]:
    cleaned_values = [clean_text(value, fallback="") for value in values]
    non_empty_values = [value for value in cleaned_values if value]
    if len(non_empty_values) < 2:
        return (-1, -1, -1, -1)

    probable_label_count = sum(_is_probable_header_label(value) for value in non_empty_values)
    string_value_count = sum(1 for raw_value, value in zip(values, cleaned_values) if value and isinstance(raw_value, str))
    unique_value_count = len({value.lower() for value in non_empty_values})
    return (probable_label_count, string_value_count, unique_value_count, len(non_empty_values))


def detect_header_row(raw_df: pd.DataFrame, max_rows: int = HEADER_SCAN_ROW_LIMIT) -> int:
    if raw_df.empty:
        return 0

    candidate_count = min(max_rows, len(raw_df.index))
    best_row_index = 0
    best_score: tuple[int, int, int, int] | None = None

    for row_index in range(candidate_count):
        candidate_score = _score_header_candidate(raw_df.iloc[row_index].tolist())
        if best_score is None or candidate_score > best_score:
            best_score = candidate_score
            best_row_index = row_index

    return best_row_index


def _build_unique_column_names(values: Sequence[Any]) -> list[str]:
    column_names: list[str] = []
    seen_counts: dict[str, int] = {}

    for column_index, value in enumerate(values):
        base_name = clean_text(value, fallback=f"Unnamed: {column_index}")
        normalized_key = base_name.lower()
        duplicate_count = seen_counts.get(normalized_key, 0)
        column_name = base_name if duplicate_count == 0 else f"{base_name}.{duplicate_count}"
        seen_counts[normalized_key] = duplicate_count + 1
        column_names.append(column_name)

    return column_names


def normalize_spreadsheet_dataframe(
    raw_df: pd.DataFrame,
    header_row_index: int | None = None,
) -> pd.DataFrame:
    compact_df = raw_df.dropna(axis=0, how="all").dropna(axis=1, how="all").reset_index(drop=True)
    if compact_df.empty:
        return compact_df.copy()

    resolved_header_row_index = detect_header_row(compact_df) if header_row_index is None else header_row_index
    if resolved_header_row_index < 0 or resolved_header_row_index >= len(compact_df.index):
        raise IndexError("header_row_index is out of range for the spreadsheet data.")

    normalized_df = compact_df.iloc[resolved_header_row_index + 1 :].copy().reset_index(drop=True)
    normalized_df.columns = _build_unique_column_names(compact_df.iloc[resolved_header_row_index].tolist())
    normalized_df = normalized_df.dropna(axis=0, how="all").reset_index(drop=True)
    return normalized_df.convert_dtypes()


def load_excel_sheet(
    file_bytes: bytes,
    sheet_name: str | int,
    engine: str | None = None,
) -> pd.DataFrame:
    raw_df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=None, engine=engine)
    return normalize_spreadsheet_dataframe(raw_df)


def build_results_context(
    upload_name: str,
    file_bytes: bytes,
    sheet_name: str | None,
    title_col: str,
    body_col: str,
    rating_col: str,
    date_col: str,
    review_window_months: int,
    rating_scope: str = DEFAULT_RATING_SCOPE,
) -> dict[str, Any]:
    return {
        "file_name": upload_name,
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "sheet_name": sheet_name,
        "title_col": title_col,
        "body_col": body_col,
        "rating_col": rating_col,
        "date_col": date_col,
        "review_window_months": int(review_window_months),
        "rating_scope": rating_scope,
    }


def clear_stale_results(
    session_state: MutableMapping[str, Any],
    current_context: dict[str, Any] | None,
) -> bool:
    previous_context = session_state.get("results_context")
    if previous_context is None:
        return False
    if current_context is not None and previous_context == current_context:
        return False
    for key in RESULT_SESSION_KEYS:
        session_state.pop(key, None)
    return True
