from copy import copy
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


SOURCE_TEMPLATE = Path(
    r"C:\Users\dell\OneDrive - Utopia\hassan\black_seed_oil_thymo\claims-black_seed_oil.xlsx"
)
MCT_WORKBOOK = Path(
    r"C:\Users\dell\OneDrive - Utopia\maha\MCT Oil\combined_mct_oil_claims.xlsx"
)
OUTPUT_WORKBOOK = Path(r"D:\analysis\combined_mct_oil_claims_with_claimwise_coverage.xlsx")

SOURCE_DATA_SHEET = "combined claims-img+txt"
TARGET_SHEET = "ClaimWise_coverage"

CLAIM_FIELDS = [
    "health_benefit_claims",
    "certification_claims",
    "nutritional_claims",
    "structure_function_statements_claims",
    "other_claims",
]

HEADERS = [
    "field",
    "claim",
    "coverage_pct",
    "asin_count",
    "total_asins",
    "present_asins",
    "absent_asins",
]


def split_claims(value):
    if value is None:
        return []
    claims = []
    seen = set()
    for part in str(value).split("|"):
        claim = " ".join(part.strip().split())
        if not claim:
            continue
        key = claim.lower()
        if key in seen:
            continue
        seen.add(key)
        claims.append(claim)
    return claims


def copy_sheet_layout(source_ws, target_ws):
    for col_idx in range(1, source_ws.max_column + 1):
        letter = source_ws.cell(1, col_idx).column_letter
        target_ws.column_dimensions[letter].width = source_ws.column_dimensions[letter].width

    for cell in source_ws[1]:
        out = target_ws.cell(1, cell.column)
        out.font = copy(cell.font)
        out.fill = copy(cell.fill)
        out.border = copy(cell.border)
        out.alignment = copy(cell.alignment)
        out.number_format = cell.number_format


def apply_fallback_style(ws):
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF")
    thin = Side(style="thin", color="D9E2F3")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    widths = [16, 46, 14, 14, 12, 82, 70]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(1, idx).column_letter].width = width


def build_coverage_rows(ws):
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    col_by_header = {str(h).strip(): idx + 1 for idx, h in enumerate(headers) if h}

    missing = ["asin"] + [field for field in CLAIM_FIELDS if field not in col_by_header]
    missing = [field for field in missing if field not in col_by_header]
    if missing:
        raise ValueError(f"Missing required columns in {SOURCE_DATA_SHEET}: {missing}")

    asin_claims = []
    for row_idx in range(2, ws.max_row + 1):
        asin = ws.cell(row_idx, col_by_header["asin"]).value
        if asin is None or not str(asin).strip():
            continue
        asin = str(asin).strip()
        per_field = {}
        for field in CLAIM_FIELDS:
            per_field[field] = split_claims(ws.cell(row_idx, col_by_header[field]).value)
        asin_claims.append((asin, per_field))

    all_asins = [asin for asin, _ in asin_claims]
    total = len(all_asins)
    if not total:
        raise ValueError("No ASIN rows found in MCT source sheet")

    rows = []
    for field in CLAIM_FIELDS:
        ordered_claims = []
        seen_claims = set()
        for _, per_field in asin_claims:
            for claim in per_field[field]:
                key = claim.lower()
                if key not in seen_claims:
                    seen_claims.add(key)
                    ordered_claims.append(claim)

        for claim in ordered_claims:
            present = [
                asin
                for asin, per_field in asin_claims
                if claim.lower() in {item.lower() for item in per_field[field]}
            ]
            absent = [asin for asin in all_asins if asin not in set(present)]
            coverage = round((len(present) / total) * 100, 2)
            rows.append(
                {
                    "field": field,
                    "claim": claim,
                    "coverage_pct": coverage,
                    "asin_count": len(present),
                    "total_asins": total,
                    "present_asins": " | ".join(present),
                    "absent_asins": " | ".join(absent),
                }
            )

    rows.sort(key=lambda row: (-row["coverage_pct"], -row["asin_count"], row["field"], row["claim"].lower()))
    return rows


def main():
    template_wb = load_workbook(SOURCE_TEMPLATE)
    template_ws = template_wb[TARGET_SHEET]

    wb = load_workbook(MCT_WORKBOOK)
    if SOURCE_DATA_SHEET not in wb.sheetnames:
        raise ValueError(f"Sheet not found: {SOURCE_DATA_SHEET}")

    if TARGET_SHEET in wb.sheetnames:
        del wb[TARGET_SHEET]
    ws = wb.create_sheet(TARGET_SHEET, 0)

    for col_idx, header in enumerate(HEADERS, start=1):
        ws.cell(1, col_idx).value = header

    try:
        copy_sheet_layout(template_ws, ws)
    except Exception:
        apply_fallback_style(ws)

    rows = build_coverage_rows(wb[SOURCE_DATA_SHEET])
    for row_idx, row in enumerate(rows, start=2):
        for col_idx, header in enumerate(HEADERS, start=1):
            ws.cell(row_idx, col_idx).value = row[header]

    ws.auto_filter.ref = f"A1:G{ws.max_row}"
    ws.freeze_panes = "A2"

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=7):
        for cell in row:
            cell.alignment = Alignment(vertical="top")
        row[2].number_format = "0.00"

    # Keep long ASIN lists readable while matching the compact source workbook style.
    for col in (6, 7):
        for cell in ws.iter_cols(min_col=col, max_col=col, min_row=2, max_row=ws.max_row):
            for item in cell:
                item.alignment = Alignment(vertical="top", wrap_text=False)

    wb.save(OUTPUT_WORKBOOK)
    print(f"saved={OUTPUT_WORKBOOK}")
    print(f"rows={len(rows)}")
    print(f"total_asins={rows[0]['total_asins'] if rows else 0}")


if __name__ == "__main__":
    main()
