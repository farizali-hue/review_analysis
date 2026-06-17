import io

import pandas as pd

from review_classifier_core import (
    build_results_context,
    build_review_block,
    compute_safe_context_budget,
    clear_stale_results,
    estimate_input_tokens,
    filter_reviews_by_scope,
    is_csv_upload,
    load_excel_sheet,
    normalize_severity,
    normalize_spreadsheet_dataframe,
    pack_prompt_items,
    resolve_model_token_limits,
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


def test_build_review_block_preserves_full_review_text():
    record = {
        "title": "A" * 20,
        "body": "B" * 40,
    }

    block = build_review_block(record, index=1, title_col="title", body_col="body")

    assert "Title: " + ("A" * 20) in block
    assert "Review: " + ("B" * 40) in block


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
