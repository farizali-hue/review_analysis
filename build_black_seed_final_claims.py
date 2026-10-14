from __future__ import annotations

import csv
from pathlib import Path


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo.csv")
OUT_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_verified.csv")


FINAL = {
    "B0DQ3774GD": {
        "claims": [
            "Pure Black Seed Oil",
            "Cold Pressed",
            "Pure Nigella Sativa Oil",
            "5% Thymoquinone",
            "5% Thymoquinone is twice the industry standard",
            "High concentration of thymoquinone",
            "Most Potent Black Seed Oil Capsules",
            "100% Pure",
            "Zero Additives",
            "No Fillers",
            "No Preservatives",
            "A Time-Tested Potent Remedy",
            "Premium Health Supplement",
            "Superior Concentration of Active Compounds",
            "Over 2,000 Years of Traditional Use",
            "One Capsule Daily",
        ],
        "health_claims": [
            "Immune Support",
            "Supports Memory",
            "Supports Vitality",
            "Supports Cellular Health",
            "Supports Overall Health",
            "Supports Cardiovascular Well-Being",
            "Antioxidant Support",
            "Combats Oxidative Stress",
            "Helps Boost Energy",
            "Supports Overall Wellness",
            "Supports Lung Health",
            "Enhances Respiratory Function and Clarity",
            "Improves Brain Oxygenation",
            "Supports Mental Focus and Clarity",
            "Promotes Clear Lungs and Better Breathing",
        ],
        "certifications": [],
        "missed_or_unclear": "",
    },
    "B0GHM7VV81": {
        "claims": [
            "Natural Balance",
            "High-Potency Black Seed Oil With Thymoquinone",
            "Premium Ethiopian Black Cumin Seed Oil",
            "4.64% Thymoquinone",
            "Organic Cold Pressed Black Seed Oil",
            "Preserves Natural Integrity",
            "Avoids High Heat and Excessive Processing",
            "Clean High-Quality Softgels",
            "Easy-To-Take Softgels",
            "2 Capsules Daily",
        ],
        "health_claims": [
            "Immune System Support",
            "Supports Unbreakable Immune Function",
            "Digestive & Gut Support",
            "Supports Healthy Digestion and Nutrient Absorption",
            "Supports Digestive Comfort",
            "Supports Balanced Daily Energy",
            "Helps Your Body Function Optimally for Sustained Energy",
            "Supports Overall Vitality",
            "Daily Wellness Support",
            "Maintains Steady Energy",
            "Maintains Overall Balance",
            "Calm Nutritional Support",
            "Helps Your Body Process and Eliminate",
        ],
        "certifications": [
            "Organic",
            "Non-GMO",
            "Gluten-Free",
        ],
        "missed_or_unclear": "",
    },
    "B0GFP46CNQ": {
        "claims": [
            "Natural Balance",
            "Ethiopian Black Seed Oil Softgels",
            "Ethiopian Black Seed Oil Organic Cold Pressed",
            "4.64% Thymoquinone",
            "Ethiopia Highlands-Sourced Black Seed Oil",
            "Simple Ingredients",
            "Clean Formula",
            "No Unnecessary Extras",
            "Plant-Based Daily Option",
            "Cold-Pressed Quality",
            "Preserves Natural Character",
            "Gentle Processing Avoids High Heat and Unnecessary Steps",
            "Clean High-Quality Softgel",
            "2 Softgels Daily",
        ],
        "health_claims": [
            "Immune System Support",
            "Digestive & Gut Support",
            "Gut Health Support",
            "Everyday Vitality",
            "Maintains a Refreshed Ready-To-Go Feeling",
        ],
        "certifications": [
            "Organic",
            "Non-GMO",
            "Gluten-Free",
        ],
        "missed_or_unclear": "",
    },
    "B0938R37X3": {
        "claims": [
            "5% Thymoquinone",
            "TQ-Advanced",
            "High Potency",
            "500 mg per Capsule",
            "Most Potent Available",
            "3x to 10x Higher Thymoquinone Levels Than Leading Brands",
            "15:1 Concentrate from Nigella Sativa Extract",
            "2-gram serving derived from 30 grams Nigella sativa",
            "Raw Form",
            "Maintains Full Bioactive Components",
            "Nutrient-Rich Superfood",
            "Thymoquinone Active Compound",
            "Topical Use for Skin & Hair",
        ],
        "health_claims": [
            "Immunity",
            "Liver",
            "Metabolism",
            "Cardiovascular",
            "Supports Overall Health and Wellness",
            "Promotes Balanced Wellness",
            "Helps Maintain a Healthy Lifestyle",
            "Immune Support",
            "Gut Health",
            "Hair & Skin",
            "Supports Skin Appearance",
            "Supports Healthy Scalp",
        ],
        "certifications": [
            "Vegan",
            "Gluten Free",
            "GMO-Free",
            "Filler-Free",
            "Soy-Free",
            "Dairy-Free",
            "Preservative-Free",
            "Plant Based",
            "3rd Party Tested",
            "Tested for 100+ Contaminants",
            "GMP Manufacturing",
            "Manufactured in the USA in a GMP Regulated Facility",
        ],
        "missed_or_unclear": "",
    },
    "B0CLB3FZ5M": {
        "claims": [
            "1000mg Black Seed Oil Capsules",
            "Cold Pressed Softgels",
            "Cold Pressed for Maximum Potency",
            "High Thymoquinone",
            "20mg High Potency Thymoquinone per Serving",
            "Nigella Sativa Black Cumin Seed Oil",
            "Locks in Natural Thymoquinone Levels",
            "Full Spectrum of Nigella Sativa Bioactive Compounds",
            "Naturally Rich in Omega 3, 6 & 9",
            "Quick-Release Softgels",
            "Superior Absorption",
            "Absorbs Faster and More Efficiently",
            "Pure Wholesome Supplement",
        ],
        "health_claims": [
            "Immunity & Wellness Supplement",
            "Heart Health Support",
            "Fortifies Immune System Daily",
            "Immune-Supporting Properties",
            "Antioxidant Properties",
            "Supports Immune Health",
            "Supports Healthy Cells",
            "Supports Digestion",
            "Promotes Mobility",
            "Supports Strong Cardiovascular Function",
            "Provides Natural Hydration",
            "Helps Reduce Dryness",
            "Helps Restore Shine for Healthier Hair, Skin, and Nails",
            "Immune Support",
            "Hair Support",
            "Brain Support",
            "Weight Loss",
        ],
        "certifications": [
            "Clean, Vegan & Non-GMO Certified",
            "100% Vegan",
            "Non-GMO",
            "GMO Free",
            "Gluten-Free",
            "Gluten Free Ingredient",
            "Artificial Filler Free",
            "Binder Free",
            "No Unnecessary Additives",
        ],
        "missed_or_unclear": "",
    },
    "B08NYHVHZ6": {
        "claims": [
            "Gaia Herbs Black Seed Oil",
            "Cold-Pressed Capsules",
            "Nigella Seed",
            "Herbal Supplement",
            "Full Spectrum Cold-Pressed Oil Extract",
            "Maximum Benefits",
            "10mg Thymoquinone Guaranteed per Serving",
            "2.5% Thymoquinone",
            "Organic Nigella Seed Oil",
            "Liquid Phyto-Caps",
            "Full-Spectrum Constituents",
            "Maintains Natural Integrity and Balance",
            "As Close to the Original Plant as Possible",
            "Purity, Quality, and Integrity",
        ],
        "health_claims": [
            "Immune System Support",
            "Supports Healthy Immune System Balance",
            "Lung Health Support",
            "Respiratory Support",
            "Supports Healthy Lung Function",
            "Maintains a Healthy Respiratory System",
            "Botanicals for Overall Respiratory Wellness",
            "Antioxidant Support",
            "General Antioxidant Defense",
            "Helps Keep Lungs Working Optimally and Efficiently",
        ],
        "certifications": [
            "Vegan",
            "Gluten-Free",
            "Soy-Free",
            "Organic",
            "Vegan Capsule",
        ],
        "missed_or_unclear": "",
    },
}


def join(values: list[str]) -> str:
    return " | ".join(values)


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        input_rows = list(csv.DictReader(handle))

    output_rows = []
    for row in input_rows:
        asin = row["asin"]
        values = FINAL[asin]
        output_rows.append(
            {
                "asin": asin,
                "url": row["url"],
                "claims": join(values["claims"]),
                "health_claims": join(values["health_claims"]),
                "certifications": join(values["certifications"]),
                "missed_or_unclear": values["missed_or_unclear"],
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "asin",
                "url",
                "claims",
                "health_claims",
                "certifications",
                "missed_or_unclear",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {OUT_CSV} with {len(output_rows)} rows")


if __name__ == "__main__":
    main()
