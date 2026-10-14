from __future__ import annotations

import csv
from pathlib import Path

from build_black_seed_claims_with_evidence import EVIDENCE


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo.csv")
OUT_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_formalized_with_evidence.csv")
ORDER_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_formalized_order.csv")


CLAIM_ORDER = [
    "Black Seed Oil",
    "Pure Black Seed Oil",
    "Nigella Sativa Oil",
    "Nigella Seed",
    "Ethiopian Black Seed Oil",
    "Ethiopian Black Cumin Seed Oil",
    "Black Seed Extract",
    "Cold Pressed",
    "Softgel Capsules",
    "Liquid Phyto-Caps",
    "1000mg Black Seed Oil",
    "500mg Per Capsule",
    "2.5% Thymoquinone",
    "4.64% Thymoquinone",
    "5% Thymoquinone",
    "10mg Thymoquinone Per Serving",
    "20mg Thymoquinone Per Serving",
    "High Thymoquinone",
    "High Potency",
    "High-Potency Black Seed Oil",
    "Most Potent Available",
    "5% Thymoquinone Is Twice The Industry Standard",
    "3x To 10x Higher Thymoquinone Than Leading Brands",
    "TQ-Advanced",
    "15:1 Nigella Sativa Concentrate",
    "2g Serving Derived From 30g Nigella Sativa",
    "Raw Form",
    "Thymoquinone Active Compound",
    "Full Spectrum Extract",
    "Full Bioactive Components",
    "Full-Spectrum Constituents",
    "Maintains Natural Integrity",
    "Preserves Natural Integrity",
    "Preserves Natural Character",
    "Avoids High Heat And Excess Processing",
    "Locks In Natural Thymoquinone Levels",
    "Naturally Rich In Omega 3, 6 & 9",
    "Superior Absorption",
    "Quick-Release Softgels",
    "Faster Absorption",
    "Maximum Benefits",
    "Premium Health Supplement",
    "Clean Formula",
    "Clean High-Quality Softgels",
    "Pure Wholesome Supplement",
    "Superior Concentration Of Active Compounds",
    "100% Pure",
    "Additive Free",
    "Filler Free",
    "Preservative Free",
    "Binder Free",
    "No Unnecessary Additives",
    "No Unnecessary Extras",
    "Simple Ingredients",
    "Natural Balance",
    "Plant-Based Daily Option",
    "Nutrient-Rich Superfood",
    "Herbal Supplement",
    "Topical Use For Skin & Hair",
    "Purity, Quality, And Integrity",
    "Over 2,000 Years Of Traditional Use",
    "Time-Tested Potent Remedy",
    "One Capsule Daily",
    "Two Capsules Daily",
    "Two Softgels Daily",
]

HEALTH_ORDER = [
    "Immune Support",
    "Healthy Immune System Balance",
    "Digestive & Gut Health Support",
    "Digestive Comfort Support",
    "Nutrient Absorption Support",
    "Body Processing And Elimination Support",
    "Energy Support",
    "Steady Energy Support",
    "Vitality Support",
    "Overall Balance Support",
    "Daily Wellness Support",
    "Calm Nutritional Support",
    "Refreshed Feeling Support",
    "Overall Health Support",
    "Overall Wellness Support",
    "Healthy Lifestyle Support",
    "Cellular Health Support",
    "Healthy Cells Support",
    "Antioxidant Support",
    "Oxidative Stress Support",
    "Heart Health Support",
    "Cardiovascular Support",
    "Strong Cardiovascular Function Support",
    "Lung Health Support",
    "Respiratory Support",
    "Breathing Support",
    "Brain Support",
    "Memory Support",
    "Focus And Mental Clarity Support",
    "Liver Support",
    "Metabolism Support",
    "Mobility Support",
    "Hair & Skin Support",
    "Nail Support",
    "Skin Appearance Support",
    "Healthy Scalp Support",
    "Hydration Support",
    "Dryness Reduction",
    "Shine Restoration",
    "Weight Loss",
]

CERTIFICATION_ORDER = [
    "Organic",
    "Vegan",
    "Vegan Capsule",
    "Plant Based",
    "Non-GMO",
    "Gluten Free",
    "Soy Free",
    "Dairy Free",
    "Preservative Free",
    "Filler Free",
    "Binder Free",
    "Additive Free",
    "No Unnecessary Additives",
    "3rd Party Tested",
    "Tested For 100+ Contaminants",
    "GMP Manufacturing",
    "Manufactured In USA In GMP-Regulated Facility",
]

ORDER_INDEX = {
    "claims": {claim: index for index, claim in enumerate(CLAIM_ORDER)},
    "health_claims": {claim: index for index, claim in enumerate(HEALTH_ORDER)},
    "certifications": {claim: index for index, claim in enumerate(CERTIFICATION_ORDER)},
}


FORMALIZED = {
    "B0DQ3774GD": {
        "claims": [
            "Pure Black Seed Oil",
            "Nigella Sativa Oil",
            "Cold Pressed",
            "5% Thymoquinone",
            "High Thymoquinone",
            "Most Potent Available",
            "5% Thymoquinone Is Twice The Industry Standard",
            "Premium Health Supplement",
            "Superior Concentration Of Active Compounds",
            "100% Pure",
            "Additive Free",
            "Filler Free",
            "Preservative Free",
            "Over 2,000 Years Of Traditional Use",
            "Time-Tested Potent Remedy",
            "One Capsule Daily",
        ],
        "health_claims": [
            "Immune Support",
            "Energy Support",
            "Vitality Support",
            "Overall Health Support",
            "Overall Wellness Support",
            "Cellular Health Support",
            "Antioxidant Support",
            "Oxidative Stress Support",
            "Heart Health Support",
            "Cardiovascular Support",
            "Lung Health Support",
            "Respiratory Support",
            "Breathing Support",
            "Brain Support",
            "Memory Support",
            "Focus And Mental Clarity Support",
        ],
        "certifications": [],
        "missed_or_unclear": "",
    },
    "B0GHM7VV81": {
        "claims": [
            "Ethiopian Black Seed Oil",
            "Ethiopian Black Cumin Seed Oil",
            "Cold Pressed",
            "4.64% Thymoquinone",
            "High-Potency Black Seed Oil",
            "Preserves Natural Integrity",
            "Avoids High Heat And Excess Processing",
            "Clean High-Quality Softgels",
            "Natural Balance",
            "Two Capsules Daily",
        ],
        "health_claims": [
            "Immune Support",
            "Digestive & Gut Health Support",
            "Digestive Comfort Support",
            "Nutrient Absorption Support",
            "Body Processing And Elimination Support",
            "Energy Support",
            "Steady Energy Support",
            "Vitality Support",
            "Overall Balance Support",
            "Daily Wellness Support",
            "Calm Nutritional Support",
        ],
        "certifications": [
            "Organic",
            "Non-GMO",
            "Gluten Free",
        ],
        "missed_or_unclear": "",
    },
    "B0GFP46CNQ": {
        "claims": [
            "Ethiopian Black Seed Oil",
            "Cold Pressed",
            "4.64% Thymoquinone",
            "Clean Formula",
            "Preserves Natural Character",
            "Avoids High Heat And Excess Processing",
            "No Unnecessary Extras",
            "Simple Ingredients",
            "Natural Balance",
            "Plant-Based Daily Option",
            "Two Softgels Daily",
        ],
        "health_claims": [
            "Immune Support",
            "Digestive & Gut Health Support",
            "Refreshed Feeling Support",
        ],
        "certifications": [
            "Organic",
            "Non-GMO",
            "Gluten Free",
        ],
        "missed_or_unclear": "",
    },
    "B0938R37X3": {
        "claims": [
            "Black Seed Oil",
            "Black Seed Extract",
            "Softgel Capsules",
            "500mg Per Capsule",
            "5% Thymoquinone",
            "High Potency",
            "Most Potent Available",
            "3x To 10x Higher Thymoquinone Than Leading Brands",
            "TQ-Advanced",
            "15:1 Nigella Sativa Concentrate",
            "2g Serving Derived From 30g Nigella Sativa",
            "Raw Form",
            "Thymoquinone Active Compound",
            "Full Bioactive Components",
            "Nutrient-Rich Superfood",
            "Topical Use For Skin & Hair",
        ],
        "health_claims": [
            "Immune Support",
            "Digestive & Gut Health Support",
            "Overall Health Support",
            "Overall Wellness Support",
            "Healthy Lifestyle Support",
            "Cardiovascular Support",
            "Liver Support",
            "Metabolism Support",
            "Hair & Skin Support",
            "Skin Appearance Support",
            "Healthy Scalp Support",
        ],
        "certifications": [
            "Vegan",
            "Plant Based",
            "Non-GMO",
            "Gluten Free",
            "Soy Free",
            "Dairy Free",
            "Preservative Free",
            "Filler Free",
            "3rd Party Tested",
            "Tested For 100+ Contaminants",
            "GMP Manufacturing",
            "Manufactured In USA In GMP-Regulated Facility",
        ],
        "missed_or_unclear": "",
    },
    "B0CLB3FZ5M": {
        "claims": [
            "Black Seed Oil",
            "Nigella Sativa Oil",
            "Cold Pressed",
            "Softgel Capsules",
            "1000mg Black Seed Oil",
            "20mg Thymoquinone Per Serving",
            "High Thymoquinone",
            "High Potency",
            "Locks In Natural Thymoquinone Levels",
            "Naturally Rich In Omega 3, 6 & 9",
            "Full Bioactive Components",
            "Superior Absorption",
            "Quick-Release Softgels",
            "Faster Absorption",
            "Pure Wholesome Supplement",
            "Filler Free",
            "Binder Free",
            "No Unnecessary Additives",
        ],
        "health_claims": [
            "Immune Support",
            "Digestive & Gut Health Support",
            "Overall Wellness Support",
            "Healthy Cells Support",
            "Antioxidant Support",
            "Heart Health Support",
            "Strong Cardiovascular Function Support",
            "Brain Support",
            "Mobility Support",
            "Hair & Skin Support",
            "Nail Support",
            "Hydration Support",
            "Dryness Reduction",
            "Shine Restoration",
            "Weight Loss",
        ],
        "certifications": [
            "Vegan",
            "Non-GMO",
            "Gluten Free",
            "Filler Free",
            "Binder Free",
            "No Unnecessary Additives",
        ],
        "missed_or_unclear": "",
    },
    "B08NYHVHZ6": {
        "claims": [
            "Black Seed Oil",
            "Nigella Seed",
            "Cold Pressed",
            "Liquid Phyto-Caps",
            "2.5% Thymoquinone",
            "10mg Thymoquinone Per Serving",
            "Full Spectrum Extract",
            "Full-Spectrum Constituents",
            "Maintains Natural Integrity",
            "Maximum Benefits",
            "Herbal Supplement",
            "Purity, Quality, And Integrity",
        ],
        "health_claims": [
            "Immune Support",
            "Healthy Immune System Balance",
            "Antioxidant Support",
            "Lung Health Support",
            "Respiratory Support",
        ],
        "certifications": [
            "Organic",
            "Vegan",
            "Vegan Capsule",
            "Gluten Free",
            "Soy Free",
        ],
        "missed_or_unclear": "",
    },
}


def ordered(values: list[str], field: str) -> list[str]:
    unknown = [value for value in values if value not in ORDER_INDEX[field]]
    if unknown:
        raise ValueError(f"{field} has values missing from order list: {unknown}")
    return sorted(dict.fromkeys(values), key=ORDER_INDEX[field].__getitem__)


def join(values: list[str]) -> str:
    return " | ".join(values)


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        input_rows = list(csv.DictReader(handle))

    rows = []
    for input_row in input_rows:
        asin = input_row["asin"]
        formal = FORMALIZED[asin]
        evidence = EVIDENCE[asin]
        rows.append(
            {
                "asin": asin,
                "url": input_row["url"],
                "claims": join(ordered(formal["claims"], "claims")),
                "claims_evidence": join(evidence["claims_evidence"]),
                "health_claims": join(ordered(formal["health_claims"], "health_claims")),
                "health_claims_evidence": join(evidence["health_claims_evidence"]),
                "certifications": join(ordered(formal["certifications"], "certifications")),
                "certifications_evidence": join(evidence["certifications_evidence"]),
                "missed_or_unclear": formal["missed_or_unclear"],
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "asin",
                "url",
                "claims",
                "claims_evidence",
                "health_claims",
                "health_claims_evidence",
                "certifications",
                "certifications_evidence",
                "missed_or_unclear",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with ORDER_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "order", "canonical_value"])
        writer.writeheader()
        for field, values in [
            ("claims", CLAIM_ORDER),
            ("health_claims", HEALTH_ORDER),
            ("certifications", CERTIFICATION_ORDER),
        ]:
            for index, value in enumerate(values, start=1):
                writer.writerow({"field": field, "order": index, "canonical_value": value})

    print(f"Wrote {OUT_CSV} with {len(rows)} rows")
    print(f"Wrote {ORDER_CSV}")


if __name__ == "__main__":
    main()
