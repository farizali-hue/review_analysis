from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo_formalized_with_evidence.csv")
PAIRWISE_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_similarity_pairwise.csv")
MATRIX_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_similarity_matrix.csv")

WEIGHTS = {
    "claims": 0.40,
    "health_claims": 0.40,
    "certifications": 0.20,
}


def parse_items(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split("|") if item.strip()}


def jaccard(left: set[str], right: set[str]) -> tuple[float, set[str], set[str]]:
    if not left and not right:
        return 1.0, set(), set()
    union = left | right
    intersection = left & right
    return len(intersection) / len(union), intersection, union


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    parsed = []
    for row in rows:
        parsed.append(
            {
                "asin": row["asin"],
                "url": row["url"],
                "claims": parse_items(row["claims"]),
                "health_claims": parse_items(row["health_claims"]),
                "certifications": parse_items(row["certifications"]),
            }
        )

    pairwise_rows = []
    scores: dict[tuple[str, str], float] = {}
    for left, right in combinations(parsed, 2):
        field_scores: dict[str, float] = {}
        shared_by_field: dict[str, set[str]] = {}
        union_by_field: dict[str, set[str]] = {}
        for field in WEIGHTS:
            score, shared, union = jaccard(left[field], right[field])
            field_scores[field] = score
            shared_by_field[field] = shared
            union_by_field[field] = union

        overall = sum(field_scores[field] * weight for field, weight in WEIGHTS.items())
        scores[(left["asin"], right["asin"])] = overall
        scores[(right["asin"], left["asin"])] = overall

        pairwise_rows.append(
            {
                "asin_1": left["asin"],
                "asin_2": right["asin"],
                "overall_similarity_pct": pct(overall),
                "claims_similarity_pct": pct(field_scores["claims"]),
                "health_claims_similarity_pct": pct(field_scores["health_claims"]),
                "certifications_similarity_pct": pct(field_scores["certifications"]),
                "shared_claims": " | ".join(sorted(shared_by_field["claims"])),
                "shared_health_claims": " | ".join(sorted(shared_by_field["health_claims"])),
                "shared_certifications": " | ".join(sorted(shared_by_field["certifications"])),
                "shared_total_count": sum(len(shared_by_field[field]) for field in WEIGHTS),
                "unique_total_count": sum(len(union_by_field[field]) for field in WEIGHTS),
                "weighting": "claims=40%; health_claims=40%; certifications=20%",
            }
        )

    pairwise_rows.sort(key=lambda row: float(row["overall_similarity_pct"]), reverse=True)

    with PAIRWISE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairwise_rows[0].keys()))
        writer.writeheader()
        writer.writerows(pairwise_rows)

    asins = [row["asin"] for row in parsed]
    with MATRIX_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["asin", *asins])
        for asin in asins:
            row = [asin]
            for other in asins:
                row.append("100.00" if asin == other else pct(scores[(asin, other)]))
            writer.writerow(row)

    print(f"Wrote {PAIRWISE_CSV} ({len(pairwise_rows)} rows)")
    print(f"Wrote {MATRIX_CSV} ({len(asins)}x{len(asins)} matrix)")


if __name__ == "__main__":
    main()
