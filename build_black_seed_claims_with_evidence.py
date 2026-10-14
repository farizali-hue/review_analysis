from __future__ import annotations

import csv
from pathlib import Path

from build_black_seed_final_claims import FINAL


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo.csv")
OUT_CSV = Path(r"D:\analysis\additionalclaims_black_seed_oil_thymo_verified_with_evidence.csv")


EVIDENCE = {
    "B0DQ3774GD": {
        "claims_evidence": [
            "Title: Better Black Seed Oil Cold Pressed; Pure Nigella Sativa Oil; 5% Thymoquinone.",
            "Original image extraction: bottle label printed Zero Additives, 5% Thymoquinone + Cold Pressed, and A Time-Tested Potent Remedy.",
            "About this item: describes Pure Black Seed Oil, premium health supplement, high thymoquinone concentration, 5% thymoquinone twice the industry standard, no additives/fillers/preservatives, and one capsule daily.",
            "Product description: says 5% thymoquinone concentration is twice the industry standard and that the formula has zero additives, fillers, or preservatives.",
        ],
        "health_claims_evidence": [
            "Title: says Immune Support and Support Memory, Vitality, and Cellular Health.",
            "Original image extraction: lists brain oxygenation/focus, oxidative stress, clear lungs/breathing, and heart-health balance claims.",
            "About this item: says comprehensive support for overall health, cardiovascular well-being and vitality; antioxidant properties combat oxidative stress; supports lung health, respiratory function and clarity; improves brain oxygenation for mental focus and clarity.",
            "Product description: says the product supports immune system, enhanced lung health, and improved brain function for mental clarity.",
        ],
        "certifications_evidence": [
            "No current-ASIN certification claim was clearly found in title, bullets, product details, or product specifications.",
            "USDA Organic/Non-GMO snippets on this page appeared in related-product or carousel containers, so they were excluded.",
        ],
    },
    "B0GHM7VV81": {
        "claims_evidence": [
            "Title: Ethiopian Black Seed Oil Capsules with 4.64% Thymoquinone; Non-GMO; Gluten-Free.",
            "Original image extraction: front label lists Natural Balance, Immune System Support, and Digestive & Gut Support.",
            "About this item: says High-Potency Black Seed Oil With Thymoquinone, Premium Ethiopian Black Cumin Seed Oil, 4.64% Thymoquinone, Organic Cold Pressed Black Seed Oil, avoids high heat/excess processing, clean high-quality softgels, and 2 capsules daily.",
        ],
        "health_claims_evidence": [
            "Title: says Immune Support, Digestion, and Energy Booster.",
            "Original image extraction: lists immune function, healthy digestion/nutrient absorption, sustained energy, and process/eliminate support claims.",
            "About this item: says Supports Digestion, Energy & Daily Vitality; helps promote digestive comfort; supports balanced daily energy; maintains overall vitality; Daily Wellness Support; maintains steady energy, overall balance, and calm nutritional support.",
            "Product specifications: Recommended Uses For Product is Digestive Health.",
        ],
        "certifications_evidence": [
            "Title: explicitly says Non-GMO and Gluten-Free.",
            "About this item: says Organic Cold Pressed Black Seed Oil.",
        ],
    },
    "B0GFP46CNQ": {
        "claims_evidence": [
            "Title: Ethiopian Black Seed Oil Softgels; Organic Cold Pressed; 4.64% Thymoquinone; Non-GMO; Gluten-Free.",
            "Original image extraction: front label lists Natural Balance, Immune System Support, and Digestive & Gut Support.",
            "About this item: says Organic Non-GMO Gluten-Free; 4.64% thymoquinone; Ethiopia highlands-sourced black seed oil; clean formula; no unnecessary extras; plant-based daily option; cold-pressed quality; preserves natural character; gentle processing avoids high heat/unnecessary steps; and 2 softgels daily.",
        ],
        "health_claims_evidence": [
            "Original image extraction: front label lists Immune System Support and Digestive & Gut Support.",
            "About this item: For Everyday Vitality says it is a plant-based daily option for maintaining a refreshed ready-to-go feeling.",
            "Product specifications: Product Benefits is Gut Health Support.",
        ],
        "certifications_evidence": [
            "Title: explicitly says Organic Cold Pressed, Non-GMO, and Gluten-Free.",
            "About this item: heading says Organic Non-GMO Gluten-Free.",
        ],
    },
    "B0938R37X3": {
        "claims_evidence": [
            "Title: 5% Thymoquinone, TQ-Advanced, High Potency, 500 mg per capsule, 15:1 concentrate from Nigella Sativa extract, raw form, vegan formula.",
            "Original image extraction: front label lists Immunity, Liver, Metabolism, and Cardiovascular.",
            "About this item: says 5% Thymoquinone (TQ) Most Potent Available; delivers 3x to 10x higher TQ levels than leading brands; 15:1 concentrate; each 2-gram serving is derived from 30 grams Nigella sativa; delivered in raw form; maintains full bioactive components; nutrient-rich superfood; topical support for skin and hair.",
            "Product specifications: Primary Supplement Type is Black Seed Extract; Product Benefits includes Immune Support, Hair & Skin, Gut Health.",
        ],
        "health_claims_evidence": [
            "Original image extraction: front label lists Immunity, Liver, Metabolism, and Cardiovascular.",
            "About this item: says thymoquinone is recognized for supporting overall health and wellness; promotes balanced wellness; helps maintain a healthy lifestyle; offers topical support for skin appearance and healthy scalp.",
            "Product specifications: Product Benefits lists Immune Support, Hair & Skin, and Gut Health.",
        ],
        "certifications_evidence": [
            "Title: says Vegan Formula.",
            "About this item: says Vegan, 3rd Party Tested and GMP Manufacturing; vegan, GMO-free, filler-free, soy-free, dairy-free, preservative-free; 3rd party tested for 100+ contaminants; manufactured in USA in a GMP regulated facility.",
            "Product specifications: Diet Type is Gluten Free, Vegan; Material Features are Vegan, Plant Based, Natural.",
        ],
    },
    "B0CLB3FZ5M": {
        "claims_evidence": [
            "Title: 1000mg Black Seed Oil Capsules; Cold Pressed Softgels; High Thymoquinone; Nigella Sativa Black Cumin Seed Oil; Omega 3 6 9; Non-GMO & Vegan.",
            "Original image extraction: certifications listed Vegan and Non-GMO; health claim listed Heart Health Support.",
            "About this item: says Cold Pressed for Maximum Potency; locks in natural thymoquinone levels; full spectrum Nigella Sativa bioactive compounds; 1000mg black seed oil with 20mg high potency thymoquinone; naturally rich in Omega 3, 6 & 9; quick-release softgels; superior absorption; absorbs faster and more efficiently; clean vegan & non-GMO certified.",
            "Product specifications: Product Benefits is Heart Health Support; Material Features include GMO Free and Gluten Free Ingredient.",
        ],
        "health_claims_evidence": [
            "Title: says Immunity & Wellness Supplement.",
            "Original image extraction: health claim listed Heart Health Support.",
            "About this item: says Fortify Your Immune System Daily; immune-supporting and antioxidant properties; supports immune health, healthy cells, digestion; promotes mobility and strong cardiovascular function; provides natural hydration to reduce dryness and restore shine for hair, skin, and nails.",
            "Product description: says the softgels provide immune, hair, and brain support and mentions weight loss.",
            "Product specifications: Product Benefits is Heart Health Support.",
        ],
        "certifications_evidence": [
            "Title: says Non-GMO & Vegan.",
            "About this item: says Clean, Vegan & Non-GMO Certified; 100% vegan, gluten-free, and Non-GMO; free from artificial fillers, binders, and unnecessary additives.",
            "Product specifications: Material Features includes GMO Free and Gluten Free Ingredient.",
        ],
    },
    "B08NYHVHZ6": {
        "claims_evidence": [
            "Title: Gaia Herbs Black Seed Oil; Cold-Pressed Capsules; Nigella Seed; Herbal Supplement; 60 Vegan Liquid Phyto-Caps.",
            "Original image extraction: lists respiratory-system and antioxidant-support claims.",
            "About this item: says Full spectrum cold-pressed oil extract with maximum benefits, 10mg thymoquinone guaranteed per serving, gluten-free and soy-free.",
            "Product specifications: Recommended Uses include Antioxidant Support, Lung Health, Respiratory Support; Diet Type is Vegan; Material Features is Organic.",
            "Product description: says full-spectrum constituents maintain natural integrity and balance and keep the extract close to the original plant.",
        ],
        "health_claims_evidence": [
            "Title: says traditionally used for Lung, Respiratory & Antioxidant Support.",
            "Original image extraction: says traditionally for maintaining a healthy respiratory system, botanicals for respiratory wellness, and antioxidant support.",
            "About this item: says supports healthy immune system balance, respiratory health, general antioxidant defense, and healthy lung function.",
            "Product description: says Black Seed Oil supports lung health, helps maintain the respiratory system, and helps keep lungs working optimally and efficiently.",
            "Product specifications: Recommended Uses include Antioxidant Support, Lung Health, Respiratory Support.",
        ],
        "certifications_evidence": [
            "Title: says Vegan Liquid Phyto-Caps.",
            "About this item: says gluten-free and soy-free.",
            "Product specifications: Diet Type is Vegan; Material Features is Organic.",
            "Ingredients/other ingredients section: lists Organic Nigella seed oil and vegan capsule.",
        ],
    },
}


def join(values: list[str]) -> str:
    return " | ".join(values)


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        input_rows = list(csv.DictReader(handle))

    rows = []
    for input_row in input_rows:
        asin = input_row["asin"]
        final = FINAL[asin]
        evidence = EVIDENCE[asin]
        rows.append(
            {
                "asin": asin,
                "url": input_row["url"],
                "claims": join(final["claims"]),
                "claims_evidence": join(evidence["claims_evidence"]),
                "health_claims": join(final["health_claims"]),
                "health_claims_evidence": join(evidence["health_claims_evidence"]),
                "certifications": join(final["certifications"]),
                "certifications_evidence": join(evidence["certifications_evidence"]),
                "missed_or_unclear": final["missed_or_unclear"],
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
    print(f"Wrote {OUT_CSV} with {len(rows)} rows")


if __name__ == "__main__":
    main()
