import csv
import json
import re
from pathlib import Path


SECTIONS_JSON = Path(r"D:\analysis\black_seed_oilthymo2_sections.json")
OUT_ASIN = Path(r"D:\analysis\black_seed_oilthymo2_claims_formalized_with_evidence.csv")
OUT_CLAIMS = Path(r"D:\analysis\black_seed_oilthymo2_claims_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\black_seed_oilthymo2_claim_order.csv")

CATEGORY_ORDER = [
    "Nutritional Claims",
    "Structure/Function Statements Claims",
    "Other Claims",
]

CLAIM_ORDER = {
    "Nutritional Claims": [
        "Black Seed Oil",
        "Black Cumin Seed Oil",
        "Nigella Sativa Oil/Extract",
        "Organic Nigella Seed Oil",
        "Ethiopian Black Seed Oil",
        "Pure Black Seed Oil",
        "Cold-Pressed",
        "Organic",
        "Full-Spectrum Extract",
        "Full Bioactive Components",
        "Raw Form",
        "TQ-Advanced",
        "High Thymoquinone",
        "5% Thymoquinone",
        "4.64% Thymoquinone",
        "2.5% Thymoquinone",
        "10 mg Thymoquinone per serving",
        "20 mg Thymoquinone per serving",
        "High-Potency Formula",
        "Thymoquinone level above leading brands",
        "500 mg per capsule",
        "1000 mg per serving",
        "400 mg Nigella seed oil",
        "15:1 Concentrate",
        "2 g serving derived from 30 g Nigella sativa",
        "Omega 3, 6 and 9",
        "Sunflower Lecithin",
        "Non-GMO/GMO-Free",
        "Gluten-Free",
        "Soy-Free",
        "Dairy-Free",
        "Filler-Free",
        "Preservative-Free",
        "Additive-Free",
        "No Artificial Fillers/Binders",
        "Vegan",
        "Plant-Based",
        "Natural",
        "Softgel Form",
        "Vegan Softgels",
        "Liquid Phyto-Caps",
        "Capsule Form",
        "Herbal Supplement",
        "Unflavored",
        "60 Count",
        "30 Count",
        "30 Servings",
        "60 Servings",
        "2-Capsule Serving",
    ],
    "Structure/Function Statements Claims": [
        "Immune Support",
        "Immune System Balance",
        "Digestive Health Support",
        "Gut Health Support",
        "Nutrient Absorption Support",
        "Detox/Elimination Support",
        "Energy Support",
        "Daily Wellness Support",
        "Overall Balance Support",
        "Overall Health/Wellness Support",
        "Vitality Support",
        "Memory Support",
        "Cellular Health Support",
        "Healthy Cells Support",
        "Antioxidant Support",
        "Oxidative Stress Support",
        "Lung Support",
        "Respiratory Support",
        "Healthy Lung Function",
        "Healthy Respiratory System Support",
        "Brain/Mental Focus Support",
        "Cardiovascular Support",
        "Heart Health Support",
        "Mobility Support",
        "Skin Health Support",
        "Hair Health Support",
        "Nail Health Support",
        "Hydration/Dryness Support",
        "Healthy Scalp Support",
        "Liver Support",
        "Metabolism Support",
        "Cholesterol Support",
        "Healthy Lifestyle Support",
    ],
    "Other Claims": [
        "Premium Supplement",
        "Most Potent Available",
        "Clean Formula",
        "Simple Ingredients",
        "No Unnecessary Extras",
        "Pure/Wholesome Supplement",
        "Purity Claim",
        "High-Quality Ingredients",
        "High-Quality Softgels",
        "Gentle Processing/No High Heat",
        "Quick-Release Softgels",
        "Faster/Superior Absorption",
        "Easy to Take",
        "Easy Daily Use",
        "Daily Use",
        "One Capsule a Day",
        "Convenient Softgels",
        "Easy Intake",
        "No Droppers/Measuring Spoons",
        "Mess-Free Use",
        "3rd Party Tested",
        "GMP Manufacturing",
        "Made in USA",
        "Tested for 100+ Contaminants",
        "Glass Bottle",
        "Topical Use",
        "Small Business",
        "Quality Sourcing",
        "Quality/Purity/Integrity",
        "Safety-Sealed",
        "Product Quality Maintained Despite Natural Separation",
    ],
}

CLAIMS = {
    "B0DQ3774GD": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil/Extract", "Pure Black Seed Oil", "Cold-Pressed",
            "High Thymoquinone", "5% Thymoquinone", "High-Potency Formula",
            "Thymoquinone level above leading brands", "Additive-Free", "Filler-Free",
            "Preservative-Free", "Softgel Form", "30 Count",
        ],
        "Structure/Function Statements Claims": [
            "Immune Support", "Energy Support", "Overall Health/Wellness Support", "Vitality Support",
            "Memory Support", "Cellular Health Support", "Antioxidant Support", "Oxidative Stress Support",
            "Lung Support", "Respiratory Support", "Brain/Mental Focus Support", "Cardiovascular Support",
        ],
        "Other Claims": [
            "Premium Supplement", "Most Potent Available", "Pure/Wholesome Supplement", "Purity Claim",
            "One Capsule a Day", "Convenient Softgels", "Easy Intake",
            "No Droppers/Measuring Spoons", "Mess-Free Use",
        ],
    },
    "B0GHM7VV81": {
        "Nutritional Claims": [
            "Black Seed Oil", "Black Cumin Seed Oil", "Ethiopian Black Seed Oil", "Cold-Pressed",
            "Organic", "4.64% Thymoquinone", "High-Potency Formula",
            "Non-GMO/GMO-Free", "Gluten-Free", "Softgel Form", "60 Count", "2-Capsule Serving",
        ],
        "Structure/Function Statements Claims": [
            "Immune Support", "Digestive Health Support", "Nutrient Absorption Support",
            "Detox/Elimination Support", "Energy Support", "Daily Wellness Support",
            "Overall Balance Support", "Vitality Support",
        ],
        "Other Claims": [
            "Clean Formula", "High-Quality Softgels", "Gentle Processing/No High Heat",
            "Easy to Take", "Easy Daily Use", "Daily Use", "Convenient Softgels",
        ],
    },
    "B0GFP46CNQ": {
        "Nutritional Claims": [
            "Black Seed Oil", "Ethiopian Black Seed Oil", "Cold-Pressed", "Organic",
            "4.64% Thymoquinone", "Non-GMO/GMO-Free", "Gluten-Free", "Plant-Based",
            "Softgel Form", "Unflavored", "60 Count", "2-Capsule Serving",
        ],
        "Structure/Function Statements Claims": [
            "Gut Health Support", "Vitality Support",
        ],
        "Other Claims": [
            "Clean Formula", "Simple Ingredients", "No Unnecessary Extras",
            "High-Quality Softgels", "Gentle Processing/No High Heat",
            "Easy Daily Use", "Convenient Softgels",
        ],
    },
    "B0938R37X3": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil/Extract", "Full Bioactive Components",
            "Raw Form", "TQ-Advanced", "High Thymoquinone", "5% Thymoquinone",
            "High-Potency Formula", "Thymoquinone level above leading brands", "500 mg per capsule",
            "15:1 Concentrate", "2 g serving derived from 30 g Nigella sativa",
            "Gluten-Free", "Soy-Free", "Dairy-Free", "Filler-Free", "Preservative-Free",
            "Non-GMO/GMO-Free", "Vegan", "Plant-Based", "Natural", "Softgel Form", "60 Count", "60 Servings",
        ],
        "Structure/Function Statements Claims": [
            "Immune Support", "Gut Health Support",
            "Overall Health/Wellness Support", "Skin Health Support", "Hair Health Support",
            "Healthy Scalp Support", "Liver Support", "Metabolism Support", "Cardiovascular Support",
            "Healthy Lifestyle Support",
        ],
        "Other Claims": [
            "Most Potent Available", "3rd Party Tested", "GMP Manufacturing", "Made in USA",
            "Tested for 100+ Contaminants", "Glass Bottle", "Topical Use",
        ],
    },
    "B0CLB3FZ5M": {
        "Nutritional Claims": [
            "Black Seed Oil", "Black Cumin Seed Oil", "Nigella Sativa Oil/Extract", "Cold-Pressed",
            "Full Bioactive Components", "High Thymoquinone", "20 mg Thymoquinone per serving",
            "High-Potency Formula", "1000 mg per serving", "Omega 3, 6 and 9",
            "Non-GMO/GMO-Free", "Gluten-Free", "Additive-Free", "No Artificial Fillers/Binders",
            "Vegan", "Softgel Form", "Unflavored", "60 Count", "60 Servings",
        ],
        "Structure/Function Statements Claims": [
            "Immune Support", "Digestive Health Support", "Overall Health/Wellness Support",
            "Healthy Cells Support", "Antioxidant Support",
            "Cardiovascular Support", "Heart Health Support", "Mobility Support",
            "Skin Health Support", "Hair Health Support", "Nail Health Support",
            "Hydration/Dryness Support", "Liver Support", "Cholesterol Support",
        ],
        "Other Claims": [
            "Clean Formula", "Pure/Wholesome Supplement", "Quick-Release Softgels",
            "Faster/Superior Absorption", "Small Business",
        ],
    },
    "B08NYHVHZ6": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil/Extract", "Organic Nigella Seed Oil", "Cold-Pressed",
            "Organic", "Full-Spectrum Extract", "2.5% Thymoquinone",
            "10 mg Thymoquinone per serving", "400 mg Nigella seed oil",
            "Sunflower Lecithin", "Gluten-Free", "Soy-Free", "Vegan",
            "Liquid Phyto-Caps", "Capsule Form", "Herbal Supplement", "60 Count",
            "30 Servings", "2-Capsule Serving",
        ],
        "Structure/Function Statements Claims": [
            "Immune Support", "Immune System Balance", "Antioxidant Support",
            "Lung Support", "Respiratory Support", "Healthy Lung Function",
            "Healthy Respiratory System Support",
        ],
        "Other Claims": [
            "High-Quality Ingredients", "Quality Sourcing", "Quality/Purity/Integrity",
            "Safety-Sealed", "Product Quality Maintained Despite Natural Separation",
        ],
    },
}

NOTES = {
    "B0DQ3774GD": "Product specifications section was parsed from page HTML and used where relevant. Recommendation/review text was not counted.",
    "B0GHM7VV81": "Product specifications section was parsed from page HTML. Detox/Elimination Support and Immune Support were retained from the image-extracted input; page text confirms digestion, energy, balance, vitality, and specs list Digestive Health.",
    "B0GFP46CNQ": "Product specifications section was parsed from page HTML and confirmed Product Benefits = Gut Health Support. Recommendation/review text was not counted.",
    "B0938R37X3": "Product specifications section was parsed from page HTML and confirmed Immune, Hair & Skin, Gut Health, Diet Type, servings, and material features. Liver, Metabolism, and Cardiovascular claims were retained from the image-extracted input.",
    "B0CLB3FZ5M": "Liver Support and Cholesterol Support were retained from the image-extracted input. Product spec text was truncated at 'Vega' for material features, so Vegan is also supported by title/bullets.",
    "B08NYHVHZ6": "Product specifications section was parsed from page HTML. The Oregano Oil cross-sell sentence was excluded because it refers to another Gaia product.",
}

PATTERNS = {
    "Black Seed Oil": [r"black seed oil"],
    "Black Cumin Seed Oil": [r"black cumin seed oil"],
    "Nigella Sativa Oil/Extract": [r"nigella sativa", r"nigella seed oil"],
    "Organic Nigella Seed Oil": [r"organic nigella"],
    "Ethiopian Black Seed Oil": [r"ethiopian black seed"],
    "Pure Black Seed Oil": [r"pure black seed oil", r"100% pure"],
    "Cold-Pressed": [r"cold pressed", r"cold-pressed"],
    "Organic": [r"organic"],
    "Full-Spectrum Extract": [r"full spectrum", r"full-spectrum"],
    "Full Bioactive Components": [r"full bioactive", r"bioactive compounds"],
    "Raw Form": [r"raw form"],
    "TQ-Advanced": [r"tq-advanced", r"tq advanced"],
    "High Thymoquinone": [r"high thymoquinone", r"high concentration of thymoquinone", r"thymoquinone.*levels"],
    "5% Thymoquinone": [r"5% thymoquinone", r"5% tq"],
    "4.64% Thymoquinone": [r"4.64% thymoquinone"],
    "2.5% Thymoquinone": [r"2.5% thymoquinone"],
    "10 mg Thymoquinone per serving": [r"10 ?mg thymoquinone"],
    "20 mg Thymoquinone per serving": [r"20mg of high potency thymoquinone", r"20 mg.*thymoquinone"],
    "High-Potency Formula": [r"high potency", r"high-potency", r"potent formula", r"most potent"],
    "Thymoquinone level above leading brands": [r"twice the industry standard", r"3x to 10x higher"],
    "500 mg per capsule": [r"500 mg per capsule", r"500mg per capsule"],
    "1000 mg per serving": [r"1000mg", r"1000 mg"],
    "400 mg Nigella seed oil": [r"400 mg"],
    "15:1 Concentrate": [r"15:1 concentrate"],
    "2 g serving derived from 30 g Nigella sativa": [r"2-gram serving", r"derived from 30 grams"],
    "Omega 3, 6 and 9": [r"omega 3 6", r"omega 3,? 6"],
    "Sunflower Lecithin": [r"sunflower lecithin"],
    "Non-GMO/GMO-Free": [r"non-gmo", r"gmo-free", r"gmo free"],
    "Gluten-Free": [r"gluten-free", r"gluten free"],
    "Soy-Free": [r"soy-free", r"soy free"],
    "Dairy-Free": [r"dairy-free", r"dairy free"],
    "Filler-Free": [r"filler-free", r"fillers?"],
    "Preservative-Free": [r"preservative-free", r"preservatives?"],
    "Additive-Free": [r"zero additives", r"no additives", r"free from.*additives", r"unnecessary additives"],
    "No Artificial Fillers/Binders": [r"artificial fillers", r"binders"],
    "Vegan": [r"vegan"],
    "Plant-Based": [r"plant-based", r"plant based"],
    "Natural": [r"natural"],
    "Softgel Form": [r"softgels?", r"soft gel"],
    "Vegan Softgels": [r"vegan softgels?"],
    "Liquid Phyto-Caps": [r"liquid phyto"],
    "Capsule Form": [r"capsules?"],
    "Herbal Supplement": [r"herbal supplement"],
    "Unflavored": [r"unflavored"],
    "60 Count": [r"60 count", r"60 softgels?", r"60 capsules?", r"unit count = 60"],
    "30 Count": [r"30.0 count", r"30 count"],
    "30 Servings": [r"30 servings"],
    "60 Servings": [r"60 servings", r"total servings per container = 60"],
    "2-Capsule Serving": [r"2 capsules", r"2 softgels", r"two capsules"],
    "Immune Support": [r"immune", r"immunity"],
    "Immune System Balance": [r"immune system balance"],
    "Digestive Health Support": [r"digestive", r"digestion"],
    "Gut Health Support": [r"gut health"],
    "Nutrient Absorption Support": [r"nutrient absorption"],
    "Detox/Elimination Support": [r"process and eliminate"],
    "Energy Support": [r"energy"],
    "Daily Wellness Support": [r"daily wellness", r"everyday wellness", r"wellness habits"],
    "Overall Balance Support": [r"overall balance", r"balanced daily"],
    "Overall Health/Wellness Support": [r"overall health", r"overall wellness", r"health and wellness", r"balanced wellness", r"wellness supplement"],
    "Vitality Support": [r"vitality"],
    "Memory Support": [r"memory"],
    "Cellular Health Support": [r"cellular health"],
    "Healthy Cells Support": [r"healthy cells"],
    "Antioxidant Support": [r"antioxidant"],
    "Oxidative Stress Support": [r"oxidative stress"],
    "Lung Support": [r"lung"],
    "Respiratory Support": [r"respiratory"],
    "Healthy Lung Function": [r"healthy lung function"],
    "Healthy Respiratory System Support": [r"healthy respiratory system"],
    "Brain/Mental Focus Support": [r"brain", r"mental focus", r"mental clarity"],
    "Cardiovascular Support": [r"cardiovascular"],
    "Heart Health Support": [r"heart health"],
    "Mobility Support": [r"mobility"],
    "Skin Health Support": [r"skin"],
    "Hair Health Support": [r"hair"],
    "Nail Health Support": [r"nails?"],
    "Hydration/Dryness Support": [r"hydration", r"dryness", r"restore shine"],
    "Healthy Scalp Support": [r"healthy scalp"],
    "Liver Support": [r"liver"],
    "Metabolism Support": [r"metabolism"],
    "Cholesterol Support": [r"cholesterol"],
    "Healthy Lifestyle Support": [r"healthy lifestyle"],
    "Premium Supplement": [r"premium health supplement"],
    "Most Potent Available": [r"most potent", r"stand out", r"twice the industry standard", r"3x to 10x"],
    "Clean Formula": [r"clean formula", r"clean,"],
    "Simple Ingredients": [r"simple ingredients"],
    "No Unnecessary Extras": [r"no unnecessary extras", r"unnecessary steps"],
    "Pure/Wholesome Supplement": [r"purest", r"pure,", r"wholesome"],
    "Purity Claim": [r"purity", r"pure"],
    "High-Quality Ingredients": [r"high-quality ingredients"],
    "High-Quality Softgels": [r"high-quality softgels?", r"high-quality softgel"],
    "Gentle Processing/No High Heat": [r"avoids high heat", r"gentle extraction", r"gentle processing"],
    "Quick-Release Softgels": [r"quick-release"],
    "Faster/Superior Absorption": [r"superior absorption", r"absorbs faster", r"more efficiently"],
    "Easy to Take": [r"easy to take"],
    "Easy Daily Use": [r"easy daily use", r"easy to take.*daily use"],
    "Daily Use": [r"daily use", r"daily with water"],
    "One Capsule a Day": [r"one capsule a day", r"one capsule daily"],
    "Convenient Softgels": [r"convenient softgel", r"convenient"],
    "Easy Intake": [r"easy intake"],
    "No Droppers/Measuring Spoons": [r"no more messy droppers", r"measuring spoons"],
    "Mess-Free Use": [r"mess-free", r"no more messy"],
    "3rd Party Tested": [r"3rd party tested", r"third party tested"],
    "GMP Manufacturing": [r"gmp"],
    "Made in USA": [r"manufactured in the usa", r"made in usa"],
    "Tested for 100+ Contaminants": [r"100\+ contaminants"],
    "Glass Bottle": [r"glass bottle"],
    "Topical Use": [r"topical use"],
    "Small Business": [r"small business"],
    "Quality Sourcing": [r"source high-quality", r"sourced"],
    "Quality/Purity/Integrity": [r"purity, quality, and integrity", r"quality.*integrity"],
    "Safety-Sealed": [r"safety-sealed"],
    "Product Quality Maintained Despite Natural Separation": [r"natural separation.*does not affect product quality"],
}


def clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ")
    text = text.replace("â€œ", '"').replace("â€\u009d", '"').replace("â€™", "'")
    text = text.replace("Â®", "").replace("®", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> list[str]:
    raw = re.split(r"[\n;|]+", clean_text(text))
    lines = []
    for line in raw:
        line = clean_text(line)
        if not line:
            continue
        if re.search(r"customer reviews|buying options|where did you see|submit feedback|price availability", line, re.I):
            continue
        lines.append(line)
    return lines


SPEC_LABELS = {
    "Brand Name", "Primary Supplement Type", "Item Form", "Diet Type", "Product Benefits",
    "Recommended Uses For Product", "Special Ingredients", "Material Features",
    "Unit Count", "Total Servings Per Container", "Flavor", "Item Nype Name",
    "Dosage Form", "Container Type", "Manufacturer",
}


def spec_pairs(context: str) -> list[str]:
    lines = [clean_text(x) for x in context.splitlines() if clean_text(x)]
    out = []
    for i, line in enumerate(lines[:-1]):
        if line in SPEC_LABELS:
            out.append(f"Product specifications: {line} = {lines[i + 1]}")
    if "Small Business" in lines:
        out.append("Product specifications: Additional Details = Small Business")
    return out


def source_lines(record: dict) -> list[tuple[str, str]]:
    sections = record["sections"]
    input_row = record["input"]
    lines = []
    for name, label in [
        ("product_title", "Title"),
        ("feature_bullets", "About this item"),
        ("important_information", "Important information"),
    ]:
        for text in sections.get(name, []) or []:
            for line in split_lines(text):
                lines.append((label, line))
    for line in spec_pairs(sections.get("product_specifications_context") or ""):
        lines.append(("Product specifications", line))
    for name, value in [
        ("input image nutritional", input_row.get("nutritional_claims", "")),
        ("input image structure/function", input_row.get("structure_function_statements_claims", "")),
        ("input image nutritional evidence", input_row.get("nutritional_claims_evidence", "")),
        ("input image structure/function evidence", input_row.get("structure_function_statements_claims_evidence", "")),
    ]:
        if value:
            lines.append((name, value))
    return lines


def first_evidence(claim: str, sources: list[tuple[str, str]]) -> tuple[str, str]:
    patterns = PATTERNS.get(claim, [re.escape(claim)])
    for source, line in sources:
        for pat in patterns:
            if re.search(pat, line, re.I):
                evidence = clean_text(line)
                if len(evidence) > 220:
                    evidence = evidence[:217].rstrip() + "..."
                return source, evidence
    return "reviewed page/input", "Claim retained after product-page and input-image review; no short matching snippet was isolated."


def sort_claims(category: str, claims: list[str]) -> list[str]:
    order = {claim: i for i, claim in enumerate(CLAIM_ORDER[category])}
    return sorted(dict.fromkeys(claims), key=lambda c: order.get(c, 9999))


def main() -> None:
    records = {r["asin"]: r for r in json.loads(SECTIONS_JSON.read_text(encoding="utf-8"))}
    asin_rows = []
    claim_rows = []

    for asin, cats in CLAIMS.items():
        record = records[asin]
        sources = source_lines(record)
        category_claims = {}
        category_evidence = {}
        for category in CATEGORY_ORDER:
            claims = sort_claims(category, cats.get(category, []))
            category_claims[category] = claims
            evidence_items = []
            for idx, claim in enumerate(claims, 1):
                source, evidence = first_evidence(claim, sources)
                evidence_items.append(f"{claim} [{source}: {evidence}]")
                claim_rows.append({
                    "asin": asin,
                    "url": record["url"],
                    "claim_order": idx,
                    "category": category,
                    "claim": claim,
                    "evidence_source": source,
                    "evidence": evidence,
                    "notes": NOTES.get(asin, ""),
                })
            category_evidence[category] = " || ".join(evidence_items)

        title = (record["sections"].get("product_title") or [record["input"].get("title", "")])[0]
        asin_rows.append({
            "asin": asin,
            "url": record["url"],
            "title": title,
            "Nutritional Claims": " | ".join(category_claims["Nutritional Claims"]),
            "Nutritional Claims Evidence": category_evidence["Nutritional Claims"],
            "Structure/Function Statements Claims": " | ".join(category_claims["Structure/Function Statements Claims"]),
            "Structure/Function Statements Claims Evidence": category_evidence["Structure/Function Statements Claims"],
            "Other Claims": " | ".join(category_claims["Other Claims"]),
            "Other Claims Evidence": category_evidence["Other Claims"],
            "missed_or_unclear": NOTES.get(asin, ""),
        })

    asin_fields = [
        "asin", "url", "title",
        "Nutritional Claims", "Nutritional Claims Evidence",
        "Structure/Function Statements Claims", "Structure/Function Statements Claims Evidence",
        "Other Claims", "Other Claims Evidence", "missed_or_unclear",
    ]
    claim_fields = [
        "asin", "url", "claim_order", "category", "claim",
        "evidence_source", "evidence", "notes",
    ]

    with OUT_ASIN.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=asin_fields)
        writer.writeheader()
        writer.writerows(asin_rows)
    with OUT_CLAIMS.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=claim_fields)
        writer.writeheader()
        writer.writerows(claim_rows)
    with OUT_ORDER.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "claim_order", "claim"])
        writer.writeheader()
        for category in CATEGORY_ORDER:
            for idx, claim in enumerate(CLAIM_ORDER[category], 1):
                writer.writerow({"category": category, "claim_order": idx, "claim": claim})


if __name__ == "__main__":
    main()
