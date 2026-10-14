from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROWS_JSON = Path(r"D:\analysis\creatine_hcl_rows.json")
BROWSER_JSON = Path(r"D:\analysis\creatine_hcl_browser_sections.json")
OUT_ROW = Path(r"D:\analysis\claims_creatine_hcl_formalized_with_evidence.csv")
OUT_CLAIM = Path(r"D:\analysis\claims_creatine_hcl_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\claims_creatine_hcl_claim_order.csv")

CATEGORIES = [
    "health_benefit_claims",
    "certification_claims",
    "nutritional_claims",
    "structure_function_statements_claims",
    "other_claims",
]

CLAIM_ORDER = {
    "health_benefit_claims": [
        "Muscle Health Support",
        "Muscle Growth Support",
        "Muscle Building Support",
        "Muscle Recovery Support",
        "Strength Support",
        "Power Support",
        "Exercise Performance Support",
        "Endurance Support",
        "Stamina Support",
        "Energy Support",
        "Cellular Energy Support",
        "Cognitive Function Support",
        "Brain Health Support",
        "Focus Support",
        "Mental Clarity Support",
        "Immune Support",
        "Heart Health Support",
        "Metabolism Support",
        "Weight Loss Support",
        "Healthy Aging Support",
        "Cellular Hydration Support",
        "No Bloating",
        "No Cramps",
        "Digestive Comfort",
        "No Water Retention",
        "Fatigue Support",
    ],
    "certification_claims": [
        "NSF Certified for Sport",
        "NSF Certified Facility",
        "SQF Certified Facility",
        "GMP/cGMP Facility",
        "GMP Certificate Available Upon Request",
        "Formal COA Available Upon Request",
        "Informed Sport Certified",
        "Banned Substance Tested",
        "Third-Party Tested",
        "Substance Free",
        "Test Safe",
        "Non-GMO",
        "Gluten Free",
        "Dairy Free",
        "Gelatin Free",
        "BPA Free",
        "Vegan",
        "Vegetarian",
        "Kosher",
        "Keto",
        "Paleo",
        "Caffeine Free",
        "Stimulant Free",
        "Sugar Free",
        "No Artificial Colors",
        "No Artificial Flavors",
        "No Artificial Preservatives",
        "No Artificial Sweeteners",
        "No Artificial Additives",
        "No Added Fillers",
    ],
    "nutritional_claims": [
        "Creatine HCl",
        "Creatine Hydrochloride",
        "CON-CRET Creatine HCl",
        "Creatine",
        "Creatine Capsules",
        "Creatine Pills",
        "750 mg Creatine HCl per Serving",
        "750 mg Creatine HCl per Capsule",
        "7X Concentrated vs Creatine Monohydrate",
        "Creatine Monohydrate Comparison",
        "Rhodiola Root Extract",
        "L-Theanine",
        "Hypromellose Capsule",
        "Vegetable Cellulose Capsule",
        "Magnesium Stearate",
        "Silicon Dioxide",
        "Microcrystalline Cellulose",
        "Amino Acid",
        "Unflavored",
        "No Calories",
        "No Carbs",
        "No Sugar",
        "Caffeine Free",
        "Stimulant Free",
        "90 Servings",
        "120 Servings",
        "75 Servings",
        "60 Servings",
        "30 Servings",
        "90 Capsules",
        "120 Capsules",
        "75 Capsules",
        "60 Capsules",
    ],
    "structure_function_statements_claims": [
        "Supports Muscle Health",
        "Supports Muscle Growth",
        "Supports Muscle Building",
        "Supports Muscle Recovery",
        "Supports Strength",
        "Supports Power",
        "Supports Exercise Performance",
        "Supports Endurance",
        "Supports Stamina",
        "Supports Energy Levels",
        "Supports Cellular Energy",
        "Supports ATP Energy Production",
        "Supports Cognitive Function",
        "Supports Brain Health",
        "Supports Focus",
        "Supports Mental Clarity",
        "Supports Immune Function",
        "Supports Heart Health",
        "Supports Metabolism Management",
        "Supports Weight Loss",
        "Supports Healthy Aging",
        "Supports Cellular Hydration",
        "Helps Reduce Muscle Cramps",
        "Supports Digestive Comfort",
        "Supports Faster Cellular Uptake",
        "Promotes Better Absorption",
        "Helps Improve Exercise Performance",
    ],
    "other_claims": [
        "No Bloating",
        "No Loading Phase",
        "No Cramps",
        "No Stomachaches",
        "No Digestive Problems",
        "No Water Retention",
        "High Absorption",
        "Rapid Absorption",
        "Superior Solubility",
        "High Bioavailability",
        "Faster Cellular Uptake",
        "Mixes Easily",
        "Completely Dissolves",
        "No Messy Powders",
        "No Mixing Required",
        "Easy Consumption",
        "Fast and Convenient",
        "Clean Formula",
        "Stomach-Friendly Creatine",
        "High-Potency Formula",
        "Premium Quality",
        "Ultra-Pure",
        "Pure Muscle Gains",
        "Patented Formula",
        "Micropure Guarantee",
        "Quality Controlled",
        "Made in USA",
        "American Made",
        "USA Manufactured",
        "Plastic Neutral",
        "4-Month Supply",
        "2-Month Supply",
        "30-Day Supply",
        "90 Count",
        "120 Capsules",
        "75 Servings",
        "60 Pills",
        "60 Capsules",
        "60 Servings",
        "Tightly Dosed",
    ],
}

ORDER_INDEX = {
    category: {claim: i for i, claim in enumerate(claims)}
    for category, claims in CLAIM_ORDER.items()
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    if any(marker in text for marker in ("â", "Ã", "�")):
        try:
            text = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u200b": "",
        "\u2713": "yes",
        "\u2714": "yes",
        "\u2122": "",
        "\u00ae": "",
        "\u0112": "E",
        "\u0113": "e",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ascii_clean(value: object) -> str:
    return clean_text(value).encode("ascii", errors="ignore").decode("ascii").strip()


def split_snippets(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\s+\|\s+|(?<=:)\s+(?=[A-Z][A-Za-z])", text)
    return [p.strip() for p in parts if len(p.strip()) >= 5]


def compact_snippet(text: str, pattern: str | None = None, max_len: int = 390) -> str:
    text = ascii_clean(text)
    if len(text) <= max_len:
        return text
    if pattern:
        match = re.search(pattern, text, flags=re.I)
        if match:
            start = max(0, match.start() - 140)
            end = min(len(text), match.end() + 230)
            return ("..." if start else "") + text[start:end].strip() + ("..." if end < len(text) else "")
    return text[: max_len - 3].strip() + "..."


def find_evidence(
    sources: list[tuple[str, str]],
    pattern: str,
    allowed_labels: set[str] | None = None,
) -> tuple[str, str] | None:
    for label, text in sources:
        if allowed_labels and label not in allowed_labels:
            continue
        if not re.search(pattern, text, flags=re.I):
            continue
        for snippet in split_snippets(text):
            if re.search(pattern, snippet, flags=re.I):
                return label, compact_snippet(snippet, pattern)
        return label, compact_snippet(text, pattern)
    return None


class ClaimBag:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, list[str]]] = {
            category: defaultdict(list) for category in CATEGORIES
        }

    def add(self, category: str, claim: str, evidence: str) -> None:
        if category not in self.data or not claim or not evidence:
            return
        claim = ascii_clean(claim)
        evidence = ascii_clean(evidence)
        current = self.data[category][claim]
        if evidence not in current:
            current.append(evidence)

    def add_from_pattern(
        self,
        sources: list[tuple[str, str]],
        category: str,
        claim: str,
        pattern: str,
        allowed_labels: set[str] | None = None,
    ) -> None:
        found = find_evidence(sources, pattern, allowed_labels)
        if found:
            label, snippet = found
            self.add(category, claim, f'{label}: "{snippet}"')

    def claims(self, category: str) -> list[str]:
        claims = list(self.data[category].keys())
        return sorted(
            claims,
            key=lambda c: (ORDER_INDEX.get(category, {}).get(c, 10_000), c.lower()),
        )

    def evidence_for(self, category: str, claim: str) -> str:
        return " || ".join(self.data[category].get(claim, [])[:4])

    def category_evidence(self, category: str) -> str:
        return " || ".join(
            f"{claim}: {self.evidence_for(category, claim)}"
            for claim in self.claims(category)
        )


def source_evidence(row: dict[str, str], source_category: str) -> str:
    evidence = row.get(f"{source_category}_evidence", "")
    source = row.get(f"{source_category}_source", "")
    text = evidence or row.get(source_category, "")
    bits = []
    if text:
        bits.append(compact_snippet(text, max_len=430))
    if source:
        bits.append(f"source={source}")
    return "Input image extraction: " + "; ".join(bits)


def add_existing_image_claims(row: dict[str, str], bag: ClaimBag) -> None:
    for source_category in CATEGORIES:
        raw = row.get(source_category, "")
        if not raw:
            continue
        evidence = source_evidence(row, source_category)
        low = f"{raw} {row.get(f'{source_category}_evidence', '')}".lower()

        mappings = [
            ("health_benefit_claims", "Muscle Health Support", r"muscle health|supports muscle health"),
            ("health_benefit_claims", "Muscle Growth Support", r"muscle growth"),
            ("health_benefit_claims", "Muscle Building Support", r"build muscle|muscle building"),
            ("health_benefit_claims", "Cognitive Function Support", r"cognitive function"),
            ("health_benefit_claims", "Brain Health Support", r"brain health|brain-boosting"),
            ("health_benefit_claims", "Energy Support", r"energy"),
            ("health_benefit_claims", "Muscle Recovery Support", r"recovery"),
            ("health_benefit_claims", "Endurance Support", r"endurance"),
            ("health_benefit_claims", "Metabolism Support", r"metabolism"),
            ("health_benefit_claims", "Weight Loss Support", r"weight loss"),
            ("health_benefit_claims", "Healthy Aging Support", r"anti[- ]aging|healthy aging|graceful aging"),
            ("health_benefit_claims", "No Bloating", r"no bloat|bloating: less likely|less likely"),
            ("health_benefit_claims", "Digestive Comfort", r"stomach-friendly"),
            ("structure_function_statements_claims", "Supports Muscle Health", r"muscle health|supports muscle health"),
            ("structure_function_statements_claims", "Supports Muscle Growth", r"muscle growth"),
            ("structure_function_statements_claims", "Supports Muscle Building", r"build muscle|muscle building"),
            ("structure_function_statements_claims", "Supports Cognitive Function", r"cognitive function"),
            ("structure_function_statements_claims", "Supports Brain Health", r"brain health|brain-boosting"),
            ("structure_function_statements_claims", "Supports Energy Levels", r"energy management"),
            ("structure_function_statements_claims", "Supports Metabolism Management", r"metabolism management"),
            ("structure_function_statements_claims", "Supports Weight Loss", r"weight loss"),
            ("structure_function_statements_claims", "Supports Healthy Aging", r"anti[- ]aging|healthy aging|graceful aging"),
            ("certification_claims", "NSF Certified for Sport", r"nsf certified sport"),
            ("certification_claims", "Informed Sport Certified", r"informed sport"),
            ("certification_claims", "Banned Substance Tested", r"banned substance tested"),
            ("certification_claims", "Third-Party Tested", r"third[- ]party tested|third party tested"),
            ("certification_claims", "GMP Certificate Available Upon Request", r"gmp certificate available"),
            ("certification_claims", "Formal COA Available Upon Request", r"formal coa"),
            ("certification_claims", "Non-GMO", r"non[- ]?gmo|gmo-free|gmo free"),
            ("certification_claims", "Gluten Free", r"gluten[- ]free|gluten free"),
            ("certification_claims", "Vegan", r"\bvegan\b"),
            ("certification_claims", "Vegetarian", r"\bvegetarian\b"),
            ("certification_claims", "Kosher", r"\bkosher\b"),
            ("certification_claims", "Stimulant Free", r"stimulant free|stimulant-free"),
            ("certification_claims", "No Artificial Colors", r"no artificial colors"),
            ("nutritional_claims", "No Calories", r"no calories"),
            ("nutritional_claims", "No Carbs", r"no carbs"),
            ("nutritional_claims", "No Sugar", r"no sugar"),
            ("nutritional_claims", "Stimulant Free", r"stimulant free|stimulant-free"),
            ("other_claims", "No Bloating", r"no bloat|bloating: less likely|less likely"),
            ("other_claims", "No Loading Phase", r"loading not required|no loading"),
            ("other_claims", "Mixes Easily", r"mixes easily"),
            ("other_claims", "Clean Formula", r"\bclean\b"),
            ("other_claims", "Stomach-Friendly Creatine", r"stomach-friendly"),
        ]
        for category, claim, pattern in mappings:
            if re.search(pattern, low, flags=re.I):
                bag.add(category, claim, evidence)


def build_sources(rec: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    sections = rec.get("sections", {})
    primary: list[tuple[str, str]] = []

    def add(label: str, value: object) -> None:
        if isinstance(value, list):
            for item in value:
                text = clean_text(item)
                if text:
                    primary.append((label, text))
        else:
            text = clean_text(value)
            if text:
                primary.append((label, text))

    add("Page title", sections.get("productTitle") or rec.get("title"))
    add("Feature bullets", sections.get("featureBullets"))
    add("Product overview", sections.get("productOverview"))
    add("Product specs/details", sections.get("detailTables"))
    add("Product details", sections.get("productDetails"))
    add("Important information", sections.get("importantInformation"))
    add("Product description", sections.get("productDescription"))

    all_sources = list(primary)
    for item in sections.get("aplus") or []:
        text = clean_text(item)
        if text:
            all_sources.append(("A+ content", text))
    return primary, all_sources


def add_page_claims(rec: dict, bag: ClaimBag) -> None:
    primary_sources, all_sources = build_sources(rec)
    primary_labels = {
        "Page title",
        "Feature bullets",
        "Product overview",
        "Product specs/details",
        "Product details",
        "Important information",
        "Product description",
    }

    rules = [
        ("health_benefit_claims", "Muscle Health Support", r"muscle health|muscle support"),
        ("health_benefit_claims", "Muscle Growth Support", r"muscle growth|muscle mass|muscle gains"),
        ("health_benefit_claims", "Muscle Building Support", r"muscle building|build muscle|strength-building"),
        ("health_benefit_claims", "Muscle Recovery Support", r"muscle recovery|recovery after|better recovery|support muscle recovery"),
        ("health_benefit_claims", "Strength Support", r"strength|more reps"),
        ("health_benefit_claims", "Power Support", r"explosive strength|muscle power|power when needed|strength and power|strength-building power|more power"),
        ("health_benefit_claims", "Exercise Performance Support", r"exercise performance|athletic performance|workout performance|performance"),
        ("health_benefit_claims", "Endurance Support", r"endurance"),
        ("health_benefit_claims", "Stamina Support", r"stamina"),
        ("health_benefit_claims", "Energy Support", r"energy management|energy support|energy levels|increase energy|fuel source|fuel your workouts"),
        ("health_benefit_claims", "Cellular Energy Support", r"cellular energy|energy to all your cells|cells.*more energy"),
        ("health_benefit_claims", "Cognitive Function Support", r"cognitive function"),
        ("health_benefit_claims", "Brain Health Support", r"brain health|brain.*memory"),
        ("health_benefit_claims", "Focus Support", r"focus|focused energy|concentration"),
        ("health_benefit_claims", "Mental Clarity Support", r"mental clarity|sharp concentration"),
        ("health_benefit_claims", "Immune Support", r"immune support"),
        ("health_benefit_claims", "Heart Health Support", r"heart health"),
        ("health_benefit_claims", "Metabolism Support", r"metabolism management"),
        ("health_benefit_claims", "Weight Loss Support", r"weight loss"),
        ("health_benefit_claims", "Healthy Aging Support", r"anti-aging|graceful aging|healthy aging"),
        ("health_benefit_claims", "Cellular Hydration Support", r"cellular hydration|cell hydration|water content in muscle cells"),
        ("health_benefit_claims", "No Bloating", r"no bloat|no bloating|without the bloating|zero bloat|does not cause bloating"),
        ("health_benefit_claims", "No Cramps", r"no cramps|muscle cramps|reduces dehydration and muscle cramps"),
        ("health_benefit_claims", "Digestive Comfort", r"digestive problems|gi discomfort|easier on your digestion|sensitive stomachs"),
        ("health_benefit_claims", "No Water Retention", r"water retention|without the water retention"),
        ("health_benefit_claims", "Fatigue Support", r"fatigue"),
        ("structure_function_statements_claims", "Supports Muscle Health", r"muscle health|muscle support"),
        ("structure_function_statements_claims", "Supports Muscle Growth", r"muscle growth|muscle mass|muscle gains"),
        ("structure_function_statements_claims", "Supports Muscle Building", r"muscle building|build muscle|strength-building"),
        ("structure_function_statements_claims", "Supports Muscle Recovery", r"muscle recovery|recovery after|better recovery|support muscle recovery"),
        ("structure_function_statements_claims", "Supports Strength", r"strength|more reps"),
        ("structure_function_statements_claims", "Supports Power", r"explosive strength|muscle power|power when needed|strength and power|strength-building power|more power"),
        ("structure_function_statements_claims", "Supports Exercise Performance", r"exercise performance|athletic performance|workout performance|performance"),
        ("structure_function_statements_claims", "Supports Endurance", r"endurance"),
        ("structure_function_statements_claims", "Supports Stamina", r"stamina"),
        ("structure_function_statements_claims", "Supports Energy Levels", r"energy management|energy support|energy levels|increase energy|fuel source|fuel your workouts"),
        ("structure_function_statements_claims", "Supports Cellular Energy", r"cellular energy|energy to all your cells|cells.*more energy"),
        ("structure_function_statements_claims", "Supports ATP Energy Production", r"atp energy"),
        ("structure_function_statements_claims", "Supports Cognitive Function", r"cognitive function"),
        ("structure_function_statements_claims", "Supports Brain Health", r"brain health|brain.*memory"),
        ("structure_function_statements_claims", "Supports Focus", r"focus|focused energy|concentration"),
        ("structure_function_statements_claims", "Supports Mental Clarity", r"mental clarity|sharp concentration"),
        ("structure_function_statements_claims", "Supports Immune Function", r"immune support"),
        ("structure_function_statements_claims", "Supports Heart Health", r"heart health"),
        ("structure_function_statements_claims", "Supports Metabolism Management", r"metabolism management"),
        ("structure_function_statements_claims", "Supports Weight Loss", r"weight loss"),
        ("structure_function_statements_claims", "Supports Healthy Aging", r"anti-aging|graceful aging|healthy aging"),
        ("structure_function_statements_claims", "Supports Cellular Hydration", r"cellular hydration|cell hydration|water content in muscle cells"),
        ("structure_function_statements_claims", "Helps Reduce Muscle Cramps", r"muscle cramps|reduces dehydration and muscle cramps"),
        ("structure_function_statements_claims", "Supports Digestive Comfort", r"digestive problems|gi discomfort|easier on your digestion|sensitive stomachs"),
        ("structure_function_statements_claims", "Supports Faster Cellular Uptake", r"cellular uptake"),
        ("structure_function_statements_claims", "Promotes Better Absorption", r"absorption|high absorption|absorbs quickly|bioavailability"),
        ("structure_function_statements_claims", "Helps Improve Exercise Performance", r"help improve exercise performance|improve exercise performance"),
        ("certification_claims", "NSF Certified for Sport", r"nsf certified sport"),
        ("certification_claims", "NSF Certified Facility", r"nsf certified facility|nsf certified"),
        ("certification_claims", "SQF Certified Facility", r"sqf"),
        ("certification_claims", "GMP/cGMP Facility", r"\bcgmp\b|\bgmp\b|good manufacturing practices"),
        ("certification_claims", "GMP Certificate Available Upon Request", r"gmp certificate available"),
        ("certification_claims", "Formal COA Available Upon Request", r"formal coa"),
        ("certification_claims", "Informed Sport Certified", r"informed sport"),
        ("certification_claims", "Banned Substance Tested", r"banned substance tested|free of banned substances"),
        ("certification_claims", "Third-Party Tested", r"third[- ]party tested|3rd[- ]party tested|third party lab tested"),
        ("certification_claims", "Non-GMO", r"non[- ]?gmo|gmo-free|gmo free"),
        ("certification_claims", "Gluten Free", r"gluten[- ]free|gluten free|diet type gluten free"),
        ("certification_claims", "Dairy Free", r"dairy free|dairy-free"),
        ("certification_claims", "Gelatin Free", r"gelatin free|gelatin-free"),
        ("certification_claims", "BPA Free", r"bpa-free|bpa free"),
        ("certification_claims", "Vegan", r"\bvegan\b"),
        ("certification_claims", "Vegetarian", r"\bvegetarian\b"),
        ("certification_claims", "Kosher", r"\bkosher\b"),
        ("certification_claims", "Keto", r"\bketo\b"),
        ("certification_claims", "Paleo", r"\bpaleo\b"),
        ("certification_claims", "Caffeine Free", r"caffeine free|caffeine-free"),
        ("certification_claims", "Stimulant Free", r"stimulant free|stimulant-free"),
        ("certification_claims", "Sugar Free", r"sugar free|sugar-free"),
        ("certification_claims", "No Artificial Colors", r"no artificial colors|colors"),
        ("certification_claims", "No Artificial Flavors", r"no artificial flavors|artificial flavors"),
        ("certification_claims", "No Artificial Preservatives", r"no artificial preservatives|artificial preservatives"),
        ("certification_claims", "No Artificial Sweeteners", r"no artificial sweeteners|artificial sweeteners"),
        ("certification_claims", "No Artificial Additives", r"artificial additives|additives"),
        ("certification_claims", "No Added Fillers", r"no added fillers|fillers"),
        ("nutritional_claims", "Creatine HCl", r"creatine hcl|creatine hcl"),
        ("nutritional_claims", "Creatine Hydrochloride", r"creatine hydrochloride"),
        ("nutritional_claims", "CON-CRET Creatine HCl", r"con-cret.*creatine hcl|con cret.*creatine hcl"),
        ("nutritional_claims", "Creatine", r"\bcreatine\b"),
        ("nutritional_claims", "Creatine Capsules", r"creatine capsules|capsules"),
        ("nutritional_claims", "Creatine Pills", r"creatine pills|pills"),
        ("nutritional_claims", "750 mg Creatine HCl per Serving", r"750\s?mg serving|serving contains 750\s?mg|750\s?mg.*per serving"),
        ("nutritional_claims", "750 mg Creatine HCl per Capsule", r"750\s?mg.*per capsule"),
        ("nutritional_claims", "7X Concentrated vs Creatine Monohydrate", r"7x concentrated|7x more concentrated"),
        ("nutritional_claims", "Creatine Monohydrate Comparison", r"creatine monohydrate|monohydrate"),
        ("nutritional_claims", "Rhodiola Root Extract", r"rhodiola root extract|rhodiola"),
        ("nutritional_claims", "L-Theanine", r"l-theanine|theanine"),
        ("nutritional_claims", "Hypromellose Capsule", r"hypromellose"),
        ("nutritional_claims", "Vegetable Cellulose Capsule", r"vegetable cellulose capsule"),
        ("nutritional_claims", "Magnesium Stearate", r"magnesium stearate"),
        ("nutritional_claims", "Silicon Dioxide", r"silicon dioxide"),
        ("nutritional_claims", "Microcrystalline Cellulose", r"microcrystalline cellulose"),
        ("nutritional_claims", "Amino Acid", r"amino acid"),
        ("nutritional_claims", "Unflavored", r"unflavored"),
        ("nutritional_claims", "No Calories", r"no calories"),
        ("nutritional_claims", "No Carbs", r"no carbs"),
        ("nutritional_claims", "No Sugar", r"no sugar|sugar free|sugar-free"),
        ("nutritional_claims", "Caffeine Free", r"caffeine free|caffeine-free"),
        ("nutritional_claims", "Stimulant Free", r"stimulant free|stimulant-free"),
        ("nutritional_claims", "90 Servings", r"90\.?0? servings|90 servings|total servings per container 90"),
        ("nutritional_claims", "120 Servings", r"120 servings|total servings per container 120"),
        ("nutritional_claims", "75 Servings", r"75 servings|total servings per container 75"),
        ("nutritional_claims", "60 Servings", r"60 servings"),
        ("nutritional_claims", "30 Servings", r"30 servings|total servings per container 30"),
        ("nutritional_claims", "90 Capsules", r"90 ct|90 count|90 capsules"),
        ("nutritional_claims", "120 Capsules", r"120 capsules|120 count"),
        ("nutritional_claims", "75 Capsules", r"75 count|75 capsules"),
        ("nutritional_claims", "60 Capsules", r"60 capsules|60 pills"),
        ("other_claims", "No Bloating", r"no bloat|no bloating|without the bloating|zero bloat|does not cause bloating"),
        ("other_claims", "No Loading Phase", r"no loading|loading not required|loading phase"),
        ("other_claims", "No Cramps", r"no cramps|muscle cramps"),
        ("other_claims", "No Stomachaches", r"stomachaches"),
        ("other_claims", "No Digestive Problems", r"digestive problems|gi discomfort"),
        ("other_claims", "No Water Retention", r"water retention|without the water retention"),
        ("other_claims", "High Absorption", r"high absorption|highly-absorbable"),
        ("other_claims", "Rapid Absorption", r"rapid absorption|absorbs quickly|fast absorption"),
        ("other_claims", "Superior Solubility", r"superior solubility|solubility"),
        ("other_claims", "High Bioavailability", r"bioavailability|bioavailable"),
        ("other_claims", "Faster Cellular Uptake", r"cellular uptake"),
        ("other_claims", "Mixes Easily", r"mixes easily|dissolves"),
        ("other_claims", "Completely Dissolves", r"completely dissolves"),
        ("other_claims", "No Messy Powders", r"messy powders|powdered creatine"),
        ("other_claims", "No Mixing Required", r"without mixing|no need.*mixing|mixing into drinks"),
        ("other_claims", "Easy Consumption", r"easy consumption"),
        ("other_claims", "Fast and Convenient", r"fast & convenient|fast and convenient"),
        ("other_claims", "Clean Formula", r"clean formula|clean, tightly dosed|clean, quality products|the clean, stomach-friendly|just clean"),
        ("other_claims", "Stomach-Friendly Creatine", r"stomach-friendly|sensitive stomachs"),
        ("other_claims", "High-Potency Formula", r"high-potency|high potency"),
        ("other_claims", "Premium Quality", r"premium quality"),
        ("other_claims", "Ultra-Pure", r"ultra-pure|pure creatine"),
        ("other_claims", "Pure Muscle Gains", r"pure muscle gains"),
        ("other_claims", "Patented Formula", r"patented"),
        ("other_claims", "Micropure Guarantee", r"micropure"),
        ("other_claims", "Quality Controlled", r"quality controlled|quality you can trust"),
        ("other_claims", "Made in USA", r"made in the usa|manufactured in the usa|produced in.*usa"),
        ("other_claims", "American Made", r"american made"),
        ("other_claims", "USA Manufactured", r"usa manufactured"),
        ("other_claims", "Plastic Neutral", r"plastic neutral"),
        ("other_claims", "4-Month Supply", r"4-month supply"),
        ("other_claims", "2-Month Supply", r"2 month supply|2-month supply"),
        ("other_claims", "30-Day Supply", r"30-day supply"),
        ("other_claims", "90 Count", r"90 ct|90 count"),
        ("other_claims", "120 Capsules", r"120 capsules"),
        ("other_claims", "75 Servings", r"75 servings"),
        ("other_claims", "60 Pills", r"60 pills"),
        ("other_claims", "60 Capsules", r"60 capsules"),
        ("other_claims", "60 Servings", r"60 servings"),
        ("other_claims", "Tightly Dosed", r"tightly dosed"),
    ]

    for category, claim, pattern in rules:
        bag.add_from_pattern(primary_sources, category, claim, pattern, primary_labels)

    aplus_rules = [
        ("certification_claims", "Third-Party Tested", r"third-party lab tested|third party lab tested"),
        ("certification_claims", "Substance Free", r"substance free"),
        ("certification_claims", "Test Safe", r"test safe"),
        ("certification_claims", "No Artificial Additives", r"artificial .*additives|additives that compromise"),
        ("certification_claims", "No Artificial Flavors", r"artificial flavoring"),
        ("other_claims", "Plastic Neutral", r"plastic neutral"),
        ("health_benefit_claims", "Muscle Growth Support", r"lean muscle growth"),
        ("health_benefit_claims", "Brain Health Support", r"cognitive function"),
        ("health_benefit_claims", "Exercise Performance Support", r"workout performance|performance & brain health"),
        ("health_benefit_claims", "Energy Support", r"energy support|boost energy"),
        ("health_benefit_claims", "Healthy Aging Support", r"anti-aging"),
        ("structure_function_statements_claims", "Supports Muscle Growth", r"lean muscle growth"),
        ("structure_function_statements_claims", "Supports Cognitive Function", r"cognitive function"),
        ("structure_function_statements_claims", "Supports Exercise Performance", r"workout performance|performance & brain health"),
        ("structure_function_statements_claims", "Supports Energy Levels", r"energy support|boost energy"),
        ("structure_function_statements_claims", "Supports Healthy Aging", r"anti-aging"),
    ]
    for category, claim, pattern in aplus_rules:
        bag.add_from_pattern(all_sources, category, claim, pattern, {"A+ content"})


def row_notes(rec: dict) -> str:
    spec = rec.get("specControl", {})
    notes = []
    if rec.get("error"):
        notes.append(f"Browser error: {rec['error']}")
    sections = rec.get("sections", {})
    if sections.get("captcha"):
        notes.append("CAPTCHA detected; claims may be incomplete.")
    if sections.get("unavailable"):
        notes.append("Amazon page showed unavailable/not-found text; claims may be incomplete.")
    if spec.get("count"):
        if spec.get("clicked"):
            notes.append("See all product specifications control clicked.")
        elif spec.get("visible") is True and spec.get("enabled") is False:
            notes.append("See all product specifications control was visible but Browser reported it as not enabled; visible product specs/details tables were parsed.")
        else:
            notes.append("See all product specifications control was present but could not be clicked; visible product specs/details tables were parsed.")
    else:
        notes.append("See all product specifications control was not found; visible product specs/details tables were parsed.")
    return " ".join(notes)


def main() -> None:
    rows = json.loads(ROWS_JSON.read_text(encoding="utf-8"))
    browser_records = {
        rec.get("asin"): rec for rec in json.loads(BROWSER_JSON.read_text(encoding="utf-8"))
    }

    row_output = []
    claim_output = []

    for row in rows:
        asin = row.get("asin", "")
        rec = browser_records.get(asin, {"asin": asin, "sections": {}, "specControl": {}})
        bag = ClaimBag()
        add_existing_image_claims(row, bag)
        add_page_claims(rec, bag)

        out = {
            "asin": asin,
            "url": row.get("url", ""),
            "title": ascii_clean((rec.get("sections") or {}).get("productTitle") or row.get("title", "")),
        }
        for category in CATEGORIES:
            claims = bag.claims(category)
            out[category] = " | ".join(claims)
            out[f"{category}_evidence"] = bag.category_evidence(category)
        out["extraction_notes"] = row_notes(rec)
        row_output.append(out)

        for category in CATEGORIES:
            for order, claim in enumerate(bag.claims(category), 1):
                claim_output.append(
                    {
                        "asin": asin,
                        "url": row.get("url", ""),
                        "category": category,
                        "claim_order_within_asin_category": order,
                        "claim": claim,
                        "evidence": bag.evidence_for(category, claim),
                        "extraction_notes": out["extraction_notes"],
                    }
                )

    row_fields = [
        "asin",
        "url",
        "title",
        "health_benefit_claims",
        "health_benefit_claims_evidence",
        "certification_claims",
        "certification_claims_evidence",
        "nutritional_claims",
        "nutritional_claims_evidence",
        "structure_function_statements_claims",
        "structure_function_statements_claims_evidence",
        "other_claims",
        "other_claims_evidence",
        "extraction_notes",
    ]
    with OUT_ROW.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=row_fields)
        writer.writeheader()
        writer.writerows(row_output)

    claim_fields = [
        "asin",
        "url",
        "category",
        "claim_order_within_asin_category",
        "claim",
        "evidence",
        "extraction_notes",
    ]
    with OUT_CLAIM.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=claim_fields)
        writer.writeheader()
        writer.writerows(claim_output)

    with OUT_ORDER.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "global_claim_order", "claim"])
        writer.writeheader()
        for category in CATEGORIES:
            for idx, claim in enumerate(CLAIM_ORDER[category], 1):
                writer.writerow({"category": category, "global_claim_order": idx, "claim": claim})

    print(
        json.dumps(
            {
                "asin_rows": len(row_output),
                "claim_rows": len(claim_output),
                "row_csv": str(OUT_ROW),
                "claim_csv": str(OUT_CLAIM),
                "order_csv": str(OUT_ORDER),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
