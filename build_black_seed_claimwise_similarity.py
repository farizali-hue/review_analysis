from __future__ import annotations

import csv
from pathlib import Path


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo_formalized_with_evidence.csv")
ORDER_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo_formalized_order.csv")
COVERAGE_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_claimwise_coverage.csv")
MATRIX_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_claimwise_matrix.csv")

FIELDS = ["claims", "health_claims", "certifications"]


def split_items(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split("|") if item.strip()}


def pct(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator) * 100:.2f}" if denominator else "0.00"


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    with ORDER_CSV.open(newline="", encoding="utf-8-sig") as handle:
        order_rows = list(csv.DictReader(handle))

    asins = [row["asin"] for row in rows]
    total_asins = len(asins)
    row_sets = {
        row["asin"]: {field: split_items(row.get(field, "")) for field in FIELDS}
        for row in rows
    }

    present_claims = {
        field: set().union(*(row_sets[asin][field] for asin in asins))
        for field in FIELDS
    }

    ordered_claims: list[tuple[str, str]] = []
    for order_row in order_rows:
        field = order_row["field"]
        claim = order_row["canonical_value"]
        if field in present_claims and claim in present_claims[field]:
            ordered_claims.append((field, claim))

    coverage_rows = []
    matrix_rows = []
    for field, claim in ordered_claims:
        present_asins = [asin for asin in asins if claim in row_sets[asin][field]]
        absent_asins = [asin for asin in asins if claim not in row_sets[asin][field]]
        coverage = pct(len(present_asins), total_asins)

        coverage_rows.append(
            {
                "field": field,
                "claim": claim,
                "coverage_pct": coverage,
                "asin_count": len(present_asins),
                "total_asins": total_asins,
                "present_asins": " | ".join(present_asins),
                "absent_asins": " | ".join(absent_asins),
            }
        )

        matrix_row = {
            "field": field,
            "claim": claim,
            "coverage_pct": coverage,
            "asin_count": len(present_asins),
        }
        for asin in asins:
            matrix_row[asin] = "100.00" if asin in present_asins else "0.00"
        matrix_rows.append(matrix_row)

    with COVERAGE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "field",
                "claim",
                "coverage_pct",
                "asin_count",
                "total_asins",
                "present_asins",
                "absent_asins",
            ],
        )
        writer.writeheader()
        writer.writerows(coverage_rows)

    with MATRIX_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["field", "claim", "coverage_pct", "asin_count", *asins],
        )
        writer.writeheader()
        writer.writerows(matrix_rows)

    print(f"Wrote {COVERAGE_CSV} ({len(coverage_rows)} claim rows)")
    print(f"Wrote {MATRIX_CSV} ({len(matrix_rows)} claim rows x {len(asins)} ASIN columns)")


if __name__ == "__main__":
    main()
