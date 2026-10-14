import csv
import json
import re
from pathlib import Path


INPUT_ROWS_JSON = Path(r"D:\analysis\black_seed_thymo2_input_rows.json")
SECTIONS_JSON = Path(r"D:\analysis\black_seed_thymo2_sections.json")
OUT_ASIN = Path(r"D:\analysis\black_seed_oilthymo2_nutritional_other_claims_with_evidence.csv")
OUT_CLAIMS = Path(r"D:\analysis\black_seed_oilthymo2_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\black_seed_oilthymo2_claim_order.csv")


CATEGORY_ORDER = ["Nutritional Claims", "Other Claims"]

CLAIM_ORDER = {
    "Nutritional Claims": [
        "Black Seed Oil",
        "Nigella Sativa Oil",
        "Black Cumin Seed Oil",
        "Ethiopian Black Seed Oil",
        "Organic Black Seed Oil",
        "Cold-Pressed Black Seed Oil",
        "Pure Black Seed Oil",
        "Full-Spectrum Cold-Pressed Oil Extract",
        "Thymoquinone",
        "5% Thymoquinone",
        "4.64% Thymoquinone",
        "2.5% Thymoquinone",
        "High Thymoquinone",
        "10 mg Thymoquinone per serving",
        "20 mg Thymoquinone",
        "High-Potency Black Seed Oil",
        "500 mg per capsule",
        "1000 mg per serving",
        "400 mg Organic Nigella Seed Oil",
        "15:1 Concentrate",
        "2-gram serving from 30 grams Nigella sativa",
        "Omega 3-6-9",
        "Bioactive Compounds",
        "Organic",
        "Non-GMO/GMO-Free",
        "Gluten-Free",
        "Soy-Free",
        "Dairy-Free",
        "Vegan",
        "Plant-Based",
        "Natural",
        "Raw Form",
        "No Additives",
        "No Fillers",
        "Preservative-Free",
        "Softgel Form",
        "Capsule Form",
        "Liquid Phyto-Caps",
        "Vegan Capsule",
        "30 Count",
        "60 Count/60 Softgels",
        "30 Servings",
        "60 Servings",
        "One Capsule Daily",
        "2 Capsules Daily",
        "Herbal Supplement",
        "Dietary Supplement",
        "Unflavored",
        "Sativa Flavor",
    ],
    "Other Claims": [
        "Immune Support",
        "Digestive Health Support",
        "Digestive Comfort",
        "Nutrient Absorption Support",
        "Energy Support",
        "Daily Vitality Support",
        "Vitality Support",
        "Cellular Health Support",
        "Memory Support",
        "Mental Focus/Clarity Support",
        "Brain Oxygenation Support",
        "Respiratory/Lung Support",
        "Antioxidant Support",
        "Cardiovascular/Heart Support",
        "Liver Support",
        "Metabolism Support",
        "Cholesterol Support",
        "Hair/Skin/Nails Support",
        "Hair/Skin Support",
        "Scalp Support",
        "Skin Appearance Support",
        "Gut Health Support",
        "Overall Health/Wellness Support",
        "Balanced Wellness",
        "Healthy Lifestyle Support",
        "Mobility Support",
        "Natural Hydration",
        "Nutritional Support",
        "Calm Nutritional Support",
        "Overall Balance",
        "Easy Daily Use",
        "Easy to Take",
        "Convenient Softgels",
        "No Messy Droppers/Measuring Spoons",
        "Quick-Release Softgels",
        "Fast/Superior Absorption",
        "Clean Formula",
        "Straightforward Formula",
        "Clean, High-Quality Softgels",
        "Premium/High-Quality Ingredients",
        "Purity/Quality/Integrity",
        "Third-Party Tested",
        "GMP Manufacturing",
        "USA Manufactured",
        "100+ Contaminant Testing",
        "Thoughtfully Sourced Ingredients",
        "Natural Integrity Preserved",
        "Gentle Extraction/No High Heat",
        "No Unnecessary Extras",
        "No Artificial Fillers/Binders/Additives",
        "100% Pure",
        "Small Business",
        "Safety-Sealed",
        "Glass Bottle",
    ],
}


CLAIMS = {
    "B0DQ3774GD": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil", "Cold-Pressed Black Seed Oil",
            "Pure Black Seed Oil", "Thymoquinone", "5% Thymoquinone",
            "High Thymoquinone", "Bioactive Compounds", "No Additives",
            "No Fillers", "Preservative-Free", "Softgel Form", "30 Count",
            "One Capsule Daily", "Dietary Supplement", "Natural",
        ],
        "Other Claims": [
            "Immune Support", "Energy Support", "Vitality Support", "Cellular Health Support",
            "Memory Support", "Mental Focus/Clarity Support", "Brain Oxygenation Support",
            "Respiratory/Lung Support", "Antioxidant Support", "Cardiovascular/Heart Support",
            "Overall Health/Wellness Support", "Convenient Softgels",
            "No Messy Droppers/Measuring Spoons", "100% Pure", "Premium/High-Quality Ingredients",
        ],
    },
    "B0GHM7VV81": {
        "Nutritional Claims": [
            "Black Seed Oil", "Black Cumin Seed Oil", "Ethiopian Black Seed Oil",
            "Organic Black Seed Oil", "Cold-Pressed Black Seed Oil", "Thymoquinone",
            "4.64% Thymoquinone", "High-Potency Black Seed Oil", "Organic",
            "Non-GMO/GMO-Free", "Gluten-Free", "Softgel Form", "Capsule Form",
            "60 Count/60 Softgels", "2 Capsules Daily", "Natural",
        ],
        "Other Claims": [
            "Immune Support", "Digestive Health Support", "Digestive Comfort",
            "Nutrient Absorption Support", "Energy Support", "Daily Vitality Support",
            "Vitality Support", "Nutritional Support", "Calm Nutritional Support",
            "Overall Balance", "Easy Daily Use", "Easy to Take",
            "Clean, High-Quality Softgels", "Natural Integrity Preserved",
            "Gentle Extraction/No High Heat",
        ],
    },
    "B0GFP46CNQ": {
        "Nutritional Claims": [
            "Black Seed Oil", "Ethiopian Black Seed Oil", "Organic Black Seed Oil",
            "Cold-Pressed Black Seed Oil", "Thymoquinone", "4.64% Thymoquinone",
            "Organic", "Non-GMO/GMO-Free", "Gluten-Free", "Plant-Based",
            "Softgel Form", "60 Count/60 Softgels", "2 Capsules Daily", "Unflavored",
        ],
        "Other Claims": [
            "Gut Health Support", "Daily Vitality Support", "Vitality Support",
            "Easy Daily Use", "Clean Formula", "Straightforward Formula",
            "Natural Integrity Preserved", "Gentle Extraction/No High Heat",
            "No Unnecessary Extras", "Clean, High-Quality Softgels",
        ],
    },
    "B0938R37X3": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil", "Black Cumin Seed Oil",
            "Thymoquinone", "5% Thymoquinone", "High Thymoquinone",
            "High-Potency Black Seed Oil", "500 mg per capsule", "15:1 Concentrate",
            "2-gram serving from 30 grams Nigella sativa", "Bioactive Compounds",
            "Gluten-Free", "Non-GMO/GMO-Free", "Soy-Free", "Dairy-Free",
            "Vegan", "Plant-Based", "Natural", "Raw Form", "No Fillers",
            "Preservative-Free", "Softgel Form", "Capsule Form", "60 Count/60 Softgels",
            "60 Servings", "Sativa Flavor",
        ],
        "Other Claims": [
            "Immune Support", "Liver Support", "Metabolism Support",
            "Cardiovascular/Heart Support", "Hair/Skin Support", "Scalp Support",
            "Skin Appearance Support", "Gut Health Support", "Overall Health/Wellness Support",
            "Balanced Wellness", "Healthy Lifestyle Support", "Third-Party Tested",
            "GMP Manufacturing", "USA Manufactured", "100+ Contaminant Testing",
            "Glass Bottle",
        ],
    },
    "B0CLB3FZ5M": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil", "Black Cumin Seed Oil",
            "Cold-Pressed Black Seed Oil", "Thymoquinone", "High Thymoquinone",
            "20 mg Thymoquinone", "1000 mg per serving", "Omega 3-6-9",
            "Bioactive Compounds", "Non-GMO/GMO-Free", "Gluten-Free", "Vegan",
            "Softgel Form", "60 Count/60 Softgels", "60 Servings", "Unflavored",
        ],
        "Other Claims": [
            "Immune Support", "Digestive Health Support", "Antioxidant Support",
            "Cardiovascular/Heart Support", "Liver Support", "Cholesterol Support",
            "Hair/Skin/Nails Support", "Cellular Health Support", "Mobility Support",
            "Natural Hydration", "Quick-Release Softgels", "Fast/Superior Absorption",
            "No Artificial Fillers/Binders/Additives", "Premium/High-Quality Ingredients",
            "Small Business",
        ],
    },
    "B08NYHVHZ6": {
        "Nutritional Claims": [
            "Black Seed Oil", "Nigella Sativa Oil", "Cold-Pressed Black Seed Oil",
            "Full-Spectrum Cold-Pressed Oil Extract", "Thymoquinone", "2.5% Thymoquinone",
            "10 mg Thymoquinone per serving", "400 mg Organic Nigella Seed Oil",
            "Organic", "Gluten-Free", "Soy-Free", "Vegan", "Liquid Phyto-Caps",
            "Vegan Capsule", "60 Count/60 Softgels", "30 Servings", "Herbal Supplement",
        ],
        "Other Claims": [
            "Immune Support", "Respiratory/Lung Support", "Antioxidant Support",
            "Thoughtfully Sourced Ingredients", "Premium/High-Quality Ingredients",
            "Purity/Quality/Integrity", "Safety-Sealed",
        ],
    },
}


NOTES = {
    "B0DQ3774GD": "Product specification button was visible but disabled in the browser; saved HTML included specs. USDA Organic/sustainability text appeared after related-product carousel and was not counted for this ASIN.",
    "B0GHM7VV81": "Other Claims includes image-extracted structure/function wording; the text/spec page confirms related digestion, energy, vitality, and daily wellness wording, but not every image phrase verbatim.",
    "B0GFP46CNQ": "Gut Health Support is confirmed in Product Benefits/specifications. Customer-review and related-product carousel text was excluded.",
    "B0938R37X3": "Liver, Metabolism, and Cardiovascular claims are retained from the image-extracted structure/function field; page text/specs confirmed immune, hair/skin, and gut benefits but did not repeat all image-only wording.",
    "B0CLB3FZ5M": "Liver and Cholesterol claims are retained from the image-extracted structure/function field; current page text confirmed immune, digestion, hair/skin/nails, cardiovascular/heart, and antioxidant wording.",
    "B08NYHVHZ6": "Product text/specs clearly supported the nutritional and respiratory/antioxidant claims. Related-product carousel text was excluded.",
}


PATTERNS = {
    "Black Seed Oil": [r"black seed oil"],
    "Nigella Sativa Oil": [r"nigella sativa", r"nigella .*seed oil"],
    "Black Cumin Seed Oil": [r"black cumin seed oil"],
    "Ethiopian Black Seed Oil": [r"ethiopian black seed oil", r"ethiopian blackseed oil"],
    "Organic Black Seed Oil": [r"organic.*black seed oil", r"organic.*blackseed oil"],
    "Cold-Pressed Black Seed Oil": [r"cold-pressed", r"cold pressed"],
    "Pure Black Seed Oil": [r"pure black seed oil", r"100% pure"],
    "Full-Spectrum Cold-Pressed Oil Extract": [r"full spectrum cold-pressed oil extract"],
    "Thymoquinone": [r"thymoquinone", r"\bTQ\b"],
    "5% Thymoquinone": [r"5% thymoquinone"],
    "4.64% Thymoquinone": [r"4\.64% thymoquinone"],
    "2.5% Thymoquinone": [r"2\.5% thymoquinone"],
    "High Thymoquinone": [r"high thymoquinone", r"high concentration of thymoquinone", r"high potency thymoquinone"],
    "10 mg Thymoquinone per serving": [r"10mg thymoquinone", r"10 mg.*thymoquinone"],
    "20 mg Thymoquinone": [r"20mg .*thymoquinone", r"20 mg .*thymoquinone"],
    "High-Potency Black Seed Oil": [r"high-potency black seed oil", r"high potency black seed oil"],
    "500 mg per capsule": [r"500 mg per capsule", r"500mg per capsule"],
    "1000 mg per serving": [r"1000mg", r"1000 mg"],
    "400 mg Organic Nigella Seed Oil": [r"400 mg"],
    "15:1 Concentrate": [r"15:1 concentrate"],
    "2-gram serving from 30 grams Nigella sativa": [r"2-gram serving", r"30 grams nigella"],
    "Omega 3-6-9": [r"omega 3", r"omega 3 6", r"omega 3 6 & 9"],
    "Bioactive Compounds": [r"bioactive"],
    "Organic": [r"organic"],
    "Non-GMO/GMO-Free": [r"non-gmo", r"gmo-free"],
    "Gluten-Free": [r"gluten-free", r"gluten free"],
    "Soy-Free": [r"soy-free", r"soy free"],
    "Dairy-Free": [r"dairy-free", r"dairy free"],
    "Vegan": [r"vegan"],
    "Plant-Based": [r"plant-based", r"plant based"],
    "Natural": [r"natural"],
    "Raw Form": [r"raw form"],
    "No Additives": [r"no additives", r"zero additives"],
    "No Fillers": [r"fillers?", r"filler-free"],
    "Preservative-Free": [r"preservative"],
    "Softgel Form": [r"softgel"],
    "Capsule Form": [r"capsule"],
    "Liquid Phyto-Caps": [r"liquid phyto"],
    "Vegan Capsule": [r"vegan capsule"],
    "30 Count": [r"30\.0 count", r"30 count"],
    "60 Count/60 Softgels": [r"60 count", r"60 softgels", r"60 vegan liquid"],
    "30 Servings": [r"30 servings"],
    "60 Servings": [r"60 servings", r"total servings per container 60"],
    "One Capsule Daily": [r"one capsule daily", r"1 liquid capsule"],
    "2 Capsules Daily": [r"2 capsules daily", r"2 softgels daily", r"adults take 2 capsules"],
    "Herbal Supplement": [r"herbal supplement"],
    "Dietary Supplement": [r"dietary supplement"],
    "Unflavored": [r"unflavored"],
    "Sativa Flavor": [r"flavor.*sativa", r"sativa"],
    "Immune Support": [r"immune", r"immunity"],
    "Digestive Health Support": [r"digestive health", r"digestion"],
    "Digestive Comfort": [r"digestive comfort"],
    "Nutrient Absorption Support": [r"nutrient absorption"],
    "Energy Support": [r"energy"],
    "Daily Vitality Support": [r"daily vitality"],
    "Vitality Support": [r"vitality"],
    "Cellular Health Support": [r"cellular health", r"healthy cells"],
    "Memory Support": [r"memory"],
    "Mental Focus/Clarity Support": [r"mental focus", r"clarity"],
    "Brain Oxygenation Support": [r"brain oxygenation"],
    "Respiratory/Lung Support": [r"respiratory", r"lung"],
    "Antioxidant Support": [r"antioxidant", r"oxidative stress"],
    "Cardiovascular/Heart Support": [r"cardiovascular", r"heart health"],
    "Liver Support": [r"\bliver\b"],
    "Metabolism Support": [r"metabolism"],
    "Cholesterol Support": [r"cholesterol"],
    "Hair/Skin/Nails Support": [r"hair, skin, and nails", r"hair, skin, nail"],
    "Hair/Skin Support": [r"hair & skin", r"skin & hair", r"skin appearance"],
    "Scalp Support": [r"scalp"],
    "Skin Appearance Support": [r"skin appearance"],
    "Gut Health Support": [r"gut health"],
    "Overall Health/Wellness Support": [r"overall health", r"overall wellness", r"daily wellness", r"wellness"],
    "Balanced Wellness": [r"balanced wellness"],
    "Healthy Lifestyle Support": [r"healthy lifestyle"],
    "Mobility Support": [r"mobility"],
    "Natural Hydration": [r"natural hydration"],
    "Nutritional Support": [r"nutritional support"],
    "Calm Nutritional Support": [r"calm sense of nutritional support"],
    "Overall Balance": [r"overall balance"],
    "Easy Daily Use": [r"easy daily use", r"daily use"],
    "Easy to Take": [r"easy to take"],
    "Convenient Softgels": [r"convenient softgel", r"soft gel capsule simplifies"],
    "No Messy Droppers/Measuring Spoons": [r"messy droppers", r"measuring spoons"],
    "Quick-Release Softgels": [r"quick-release", r"begin releasing"],
    "Fast/Superior Absorption": [r"absorbs faster", r"superior absorption", r"absorbs.*efficiently"],
    "Clean Formula": [r"clean formula"],
    "Straightforward Formula": [r"straightforward formula"],
    "Clean, High-Quality Softgels": [r"clean, high-quality softgel"],
    "Premium/High-Quality Ingredients": [r"premium", r"high-quality ingredients"],
    "Purity/Quality/Integrity": [r"purity", r"quality", r"integrity"],
    "Third-Party Tested": [r"3rd party", r"third-party"],
    "GMP Manufacturing": [r"gmp"],
    "USA Manufactured": [r"manufactured in the usa", r"usa"],
    "100+ Contaminant Testing": [r"100\\+ contaminants"],
    "Thoughtfully Sourced Ingredients": [r"thoughtfully source", r"sourced"],
    "Natural Integrity Preserved": [r"preserve.*natural integrity", r"preserve its natural character"],
    "Gentle Extraction/No High Heat": [r"avoids high heat", r"gentle extraction"],
    "No Unnecessary Extras": [r"no unnecessary extras", r"unnecessary"],
    "No Artificial Fillers/Binders/Additives": [r"artificial fillers", r"binders", r"unnecessary additives"],
    "100% Pure": [r"100% pure"],
    "Small Business": [r"small business"],
    "Safety-Sealed": [r"safety-sealed"],
    "Glass Bottle": [r"glass bottle"],
}


def clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ")
    text = text.replace("â€“", "-").replace("Â®", "®")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> list[str]:
    text = clean_text(text)
    lines = re.split(r"[\n;|]+", text)
    out = []
    for line in lines:
        line = clean_text(line)
        if not line:
            continue
        if re.search(r"customer reviews|buying options|price availability|not intended to diagnose|submit feedback", line, re.I):
            continue
        out.append(line)
    return out


def crop_current_product(text: str) -> str:
    markers = [
        "Customers who viewed this item also viewed",
        "Product Videos",
        "Disclaimer : While we work",
    ]
    result = text or ""
    for marker in markers:
        idx = result.find(marker)
        if idx >= 0:
            result = result[:idx]
    return result


def spec_lines(context: str) -> list[str]:
    context = crop_current_product(context)
    labels = {
        "Brand Name", "Item Form", "Primary Supplement Type", "Diet Type",
        "Product Benefits", "Recommended Uses For Product", "Special Ingredients",
        "Dosage Form", "Material Features", "Flavor", "Unit Count",
        "Total Servings Per Container", "Number of Items", "Item Nype Name",
        "Container Type", "Package Quantity", "Is Product Expirable",
    }
    raw = [clean_text(x) for x in context.splitlines() if clean_text(x)]
    out = []
    for i, line in enumerate(raw[:-1]):
        if line in labels:
            out.append(f"Product specifications: {line} = {raw[i + 1]}")
    if "Small Business" in raw:
        out.append("Product specifications: Additional Details = Small Business")
    return out


def source_lines(record: dict) -> list[tuple[str, str]]:
    lines = []
    sections = record["sections"]
    for name, label in [
        ("product_title", "Title"),
        ("feature_bullets", "About this item"),
        ("important_information", "Important information"),
    ]:
        for text in sections.get(name, []) or []:
            for line in split_lines(text):
                lines.append((label, line))

    for line in spec_lines(sections.get("see_all_product_specifications_context") or ""):
        lines.append(("Product specifications", line))

    for text in sections.get("aplus", []) or []:
        text = crop_current_product(text)
        for line in split_lines(text):
            lines.append(("A+ product description", line))

    if record.get("input_nutritional_claims"):
        lines.append(("input image nutritional", record["input_nutritional_claims"]))
    if record.get("input_structure_function_statements_claims"):
        lines.append(("input image structure/function", record["input_structure_function_statements_claims"]))
    return lines


def first_evidence(claim: str, sources: list[tuple[str, str]]) -> tuple[str, str]:
    for source, line in sources:
        for pattern in PATTERNS.get(claim, [re.escape(claim)]):
            if re.search(pattern, line, re.I):
                evidence = clean_text(line)
                if len(evidence) > 190:
                    evidence = evidence[:187].rstrip() + "..."
                return source, evidence
    return "manual review", "Claim retained after product-page review; no short matching snippet was isolated automatically."


def sort_claims(category: str, claims: list[str]) -> list[str]:
    order = {claim: i for i, claim in enumerate(CLAIM_ORDER[category])}
    return sorted(dict.fromkeys(claims), key=lambda c: order.get(c, 9999))


def main() -> None:
    input_rows = {row["asin"]: row for row in json.loads(INPUT_ROWS_JSON.read_text(encoding="utf-8"))}
    section_records = {row["asin"]: row for row in json.loads(SECTIONS_JSON.read_text(encoding="utf-8"))}
    asin_rows = []
    claim_rows = []

    for asin, categories in CLAIMS.items():
        input_row = input_rows[asin]
        record = section_records[asin]
        sources = source_lines(record)
        per_category = {}
        evidence_by_category = {}

        for category in CATEGORY_ORDER:
            claims = sort_claims(category, categories.get(category, []))
            per_category[category] = claims
            evidence_items = []
            for index, claim in enumerate(claims, 1):
                source, evidence = first_evidence(claim, sources)
                evidence_items.append(f"{claim} [{source}: {evidence}]")
                claim_rows.append({
                    "asin": asin,
                    "url": input_row["url"],
                    "claim_order": index,
                    "category": category,
                    "claim": claim,
                    "evidence_source": source,
                    "evidence": evidence,
                    "notes": NOTES.get(asin, ""),
                })
            evidence_by_category[category] = " || ".join(evidence_items)

        title = (record["sections"].get("product_title") or [input_row.get("title", "")])[0]
        asin_rows.append({
            "asin": asin,
            "url": input_row["url"],
            "title": title,
            "Nutritional Claims": " | ".join(per_category["Nutritional Claims"]),
            "Nutritional Claims Evidence": evidence_by_category["Nutritional Claims"],
            "Other Claims": " | ".join(per_category["Other Claims"]),
            "Other Claims Evidence": evidence_by_category["Other Claims"],
            "missed_or_unclear": NOTES.get(asin, ""),
        })

    asin_fields = [
        "asin", "url", "title",
        "Nutritional Claims", "Nutritional Claims Evidence",
        "Other Claims", "Other Claims Evidence",
        "missed_or_unclear",
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
            for index, claim in enumerate(CLAIM_ORDER[category], 1):
                writer.writerow({"category": category, "claim_order": index, "claim": claim})


if __name__ == "__main__":
    main()
