import io

import pandas as pd

from review_classifier_core import (
    build_results_context,
    build_review_block,
    clean_text,
    compute_safe_context_budget,
    clear_stale_results,
    couple_category_severity,
    detect_encoding,
    estimate_input_tokens,
    filter_reviews_by_scope,
    fix_mojibake,
    is_csv_upload,
    is_vague_category_label,
    load_excel_sheet,
    normalize_severity,
    normalize_spreadsheet_dataframe,
    pack_prompt_items,
    resolve_model_token_limits,
    sanitize_category_label,
    sanitize_csv_field,
)


def test_clear_stale_results_removes_cached_outputs_when_inputs_change():
    session_state = {
        "results": ["old"],
        "categories": ["Packaging"],
        "run_log_summary": {"total_tokens": 123},
        "run_log_path": "logs/old.log",
        "results_context": {"file_name": "old.csv", "sheet_name": None},
    }

    cleared = clear_stale_results(
        session_state,
        {"file_name": "new.csv", "sheet_name": None},
    )

    assert cleared is True
    assert "results" not in session_state
    assert "categories" not in session_state
    assert "run_log_summary" not in session_state
    assert "run_log_path" not in session_state
    assert "results_context" not in session_state


def test_clear_stale_results_keeps_cached_outputs_for_same_inputs():
    context = {"file_name": "same.csv", "sheet_name": "Sheet1"}
    session_state = {
        "results": ["current"],
        "results_context": context.copy(),
    }

    cleared = clear_stale_results(session_state, context.copy())

    assert cleared is False
    assert session_state["results"] == ["current"]
    assert session_state["results_context"] == context


def test_build_results_context_tracks_uploaded_file_contents_and_inputs():
    first = build_results_context(
        upload_name="reviews.csv",
        file_bytes=b"alpha",
        sheet_name=None,
        title_col="Title",
        body_col="Body",
        rating_col="Rating",
        date_col="Date",
        review_window_months=12,
    )
    second = build_results_context(
        upload_name="reviews.csv",
        file_bytes=b"beta",
        sheet_name=None,
        title_col="Title",
        body_col="Body",
        rating_col="Rating",
        date_col="Date",
        review_window_months=12,
    )

    assert first != second


def test_build_results_context_tracks_brand_column():
    base_kwargs = dict(
        upload_name="reviews.csv",
        file_bytes=b"alpha",
        sheet_name=None,
        title_col="Title",
        body_col="Body",
        rating_col="Rating",
        date_col="Date",
        review_window_months=12,
    )

    unmapped = build_results_context(**base_kwargs)
    mapped = build_results_context(**base_kwargs, brand_col="brand_name")

    assert unmapped["brand_col"] == "(none)"
    assert unmapped != mapped


def test_build_review_block_preserves_full_review_text():
    record = {
        "title": "A" * 20,
        "body": "B" * 40,
    }

    block = build_review_block(record, index=1, title_col="title", body_col="body")

    assert "Title: " + ("A" * 20) in block
    assert "Review: " + ("B" * 40) in block


def test_build_review_block_includes_compact_rating_when_given():
    record = {"title": "Good", "body": "Works well", "Rating": 5.0}

    block = build_review_block(record, index=1, title_col="title", body_col="body", rating_col="Rating")

    assert "[5 stars]" in block
    assert "5.0" not in block
    assert "Review: Works well" in block


def test_build_review_block_omits_rating_when_absent():
    record = {"title": "Good", "body": "Works well"}

    block = build_review_block(record, index=1, title_col="title", body_col="body", rating_col="Rating")

    assert "stars" not in block


def test_estimate_input_tokens_rounds_up_character_groups():
    assert estimate_input_tokens("abcd") == 1
    assert estimate_input_tokens("abcde") == 2


def test_pack_prompt_items_uses_strict_token_budget_with_reserved_output():
    selected, prompt, estimated_tokens = pack_prompt_items(
        ["abcd", "efgh", "ijkl"],
        format_item=lambda item, index: item,
        prompt_prefix="",
        prompt_suffix="",
        reserved_output_tokens=lambda count: count,
        safe_context_budget=5,
    )

    assert selected == ["abcd"]
    assert prompt == "abcd"
    assert estimated_tokens == 1


def test_pack_prompt_items_raises_when_single_item_cannot_fit_budget():
    try:
        pack_prompt_items(
            ["a" * 40],
            format_item=lambda item, index: item,
            prompt_prefix="",
            prompt_suffix="",
            reserved_output_tokens=1,
            safe_context_budget=5,
        )
    except ValueError as exc:
        assert "exceeds the configured token budget" in str(exc)
    else:
        raise AssertionError("Expected a ValueError when no items fit in the token budget.")


def test_filter_reviews_by_scope_below_4_keeps_only_low_ratings():
    df = pd.DataFrame({"Rating": [1, 2, 3, 4, 5], "Body": list("abcde")})

    filtered = filter_reviews_by_scope(df, "Rating", "below_4")

    assert filtered["Rating"].tolist() == [1, 2, 3]


def test_filter_reviews_by_scope_4_and_5_keeps_only_high_ratings():
    df = pd.DataFrame({"Rating": [1, 2, 3, 4, 5], "Body": list("abcde")})

    filtered = filter_reviews_by_scope(df, "Rating", "4_and_5")

    assert filtered["Rating"].tolist() == [4, 5]


def test_filter_reviews_by_scope_all_keeps_every_numerically_rated_row():
    df = pd.DataFrame({"Rating": [1, 5, "n/a", None], "Body": list("abcd")})

    filtered = filter_reviews_by_scope(df, "Rating", "all")

    assert filtered["Rating"].tolist() == [1, 5]


def test_filter_reviews_by_scope_rejects_unknown_scope():
    df = pd.DataFrame({"Rating": [1], "Body": ["a"]})

    try:
        filter_reviews_by_scope(df, "Rating", "five_stars")
    except ValueError as exc:
        assert "Unknown rating scope" in str(exc)
    else:
        raise AssertionError("Expected a ValueError for an unknown scope.")


def test_normalize_severity_accepts_known_levels_case_insensitively():
    assert normalize_severity("high") == "High"
    assert normalize_severity("MEDIUM") == "Medium"
    assert normalize_severity("Low") == "Low"
    assert normalize_severity("none") == "None"


def test_normalize_severity_falls_back_for_unknown_or_empty_values():
    assert normalize_severity("") == "Medium"
    assert normalize_severity("catastrophic") == "Medium"
    assert normalize_severity(None) == "Medium"


def test_is_vague_category_label_flags_generic_buckets_only():
    assert is_vague_category_label("Other") is True
    assert is_vague_category_label("  misc ") is True
    assert is_vague_category_label("Stomach Pain") is False
    assert is_vague_category_label("No Complaint") is False


def test_sanitize_category_label_rejects_severity_tokens():
    assert sanitize_category_label("High") == "Needs Review"
    assert sanitize_category_label("none") == "Needs Review"
    assert sanitize_category_label("Low", fallback="Unmapped") == "Unmapped"


def test_sanitize_category_label_keeps_real_categories():
    assert sanitize_category_label("Stomach Pain") == "Stomach Pain"
    assert sanitize_category_label("No Complaint") == "No Complaint"


def test_couple_category_severity_demotes_severity_none_to_no_complaint():
    # Reverse coupling: a positive review tagged with a topic category but no
    # severity is not a complaint (the bug seen at scale in real outputs).
    assert couple_category_severity("Hair Growth", "None") == ("No Complaint", "None")
    assert couple_category_severity("Prostate Support", "none") == ("No Complaint", "None")


def test_couple_category_severity_strips_severity_from_no_complaint():
    # Forward coupling: a No Complaint row never carries a severity.
    assert couple_category_severity("No Complaint", "Medium") == ("No Complaint", "None")
    assert couple_category_severity("no complaint", "High") == ("No Complaint", "None")


def test_couple_category_severity_leaves_real_complaints_untouched():
    assert couple_category_severity("Stomach Pain", "High") == ("Stomach Pain", "High")
    assert couple_category_severity("High Price", "Low") == ("High Price", "Low")
    assert couple_category_severity("No Complaint", "None") == ("No Complaint", "None")


def test_sanitize_csv_field_neutralizes_formula_leading_chars():
    assert sanitize_csv_field("=1+2") == "'=1+2"
    assert sanitize_csv_field("@SUM(A1)") == "'@SUM(A1)"
    assert sanitize_csv_field("-cmd|calc") == "'-cmd|calc"
    assert sanitize_csv_field("+1") == "'+1"


def test_sanitize_csv_field_leaves_safe_values_untouched():
    assert sanitize_csv_field("Great product") == "Great product"
    assert sanitize_csv_field("") == ""
    assert sanitize_csv_field(5) == 5


def test_fix_mojibake_repairs_double_encoded_text():
    mojibake = "Magnífico".encode("utf-8").decode("latin-1")
    assert fix_mojibake(mojibake) == "Magnífico"


def test_fix_mojibake_leaves_clean_text_untouched():
    assert fix_mojibake("Good product") == "Good product"
    assert fix_mojibake("") == ""


def test_detect_encoding_falls_back_for_empty_input():
    assert detect_encoding(b"") == "utf-8"


def test_clean_text_repairs_mojibake_in_review_content():
    mojibake = "Para mí no he notado nada".encode("utf-8").decode("latin-1")
    assert clean_text(mojibake) == "Para mí no he notado nada"


def test_is_csv_upload_handles_uppercase_extensions():
    assert is_csv_upload("REVIEWS.CSV") is True


def test_resolve_model_token_limits_supports_current_aliases():
    limits = resolve_model_token_limits("gpt-5.4-mini")

    assert limits["context_window"] == 400_000
    assert limits["max_output_tokens"] == 128_000


def test_compute_safe_context_budget_uses_model_context_window():
    assert compute_safe_context_budget("gpt-5.4-nano") == 320_000


def test_normalize_spreadsheet_dataframe_promotes_detected_header_row():
    raw_df = pd.DataFrame(
        [
            ["CoQ10 : Review Analysis", None, None, None, None, None],
            [None, None, None, None, None, None],
            ["Brand", "Link", "Reviews", "Rating", "BSR", "Category"],
            ["Qunol Ultra 1", "https://example.com/1", 59450, 4.7, 383, "Supplements"],
            ["Qunol Ultra 2", "https://example.com/2", 22291, 4.7, 404, "Supplements"],
        ]
    )

    normalized = normalize_spreadsheet_dataframe(raw_df)

    assert list(normalized.columns) == ["Brand", "Link", "Reviews", "Rating", "BSR", "Category"]
    assert normalized.to_dict("records") == [
        {
            "Brand": "Qunol Ultra 1",
            "Link": "https://example.com/1",
            "Reviews": 59450,
            "Rating": 4.7,
            "BSR": 383,
            "Category": "Supplements",
        },
        {
            "Brand": "Qunol Ultra 2",
            "Link": "https://example.com/2",
            "Reviews": 22291,
            "Rating": 4.7,
            "BSR": 404,
            "Category": "Supplements",
        },
    ]


def test_load_excel_sheet_detects_header_row_from_uploaded_workbook():
    workbook_bytes = io.BytesIO()
    raw_df = pd.DataFrame(
        [
            ["CoQ10 : Review Analysis", None, None, None],
            [None, None, None, None],
            ["Brand", "Link", "Reviews", "Rating"],
            ["Qunol Ultra 1", "https://example.com/1", 59450, 4.7],
        ]
    )

    with pd.ExcelWriter(workbook_bytes, engine="openpyxl") as writer:
        raw_df.to_excel(writer, sheet_name="Index", header=False, index=False)

    loaded = load_excel_sheet(workbook_bytes.getvalue(), sheet_name="Index")

    assert list(loaded.columns) == ["Brand", "Link", "Reviews", "Rating"]
    assert loaded.iloc[0].to_dict() == {
        "Brand": "Qunol Ultra 1",
        "Link": "https://example.com/1",
        "Reviews": 59450,
        "Rating": 4.7,
    }
    assert str(loaded.dtypes["Reviews"]) == "Int64"
    assert str(loaded.dtypes["Rating"]) == "Float64"
