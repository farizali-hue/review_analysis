from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROWS_JSON = Path(r"D:\analysis\nad_rows.json")
BROWSER_JSON = Path(r"D:\analysis\nad_browser_sections.json")
OUT_ROW = Path(r"D:\analysis\claims_nad_formalized_with_evidence.csv")
OUT_CLAIM = Path(r"D:\analysis\claims_nad_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\claims_nad_claim_order.csv")

CATEGORIES = [
    "health_benefit_claims",
    "certification_claims",
    "nutritional_claims",
    "structure_function_statements_claims",
    "other_claims",
]

CLAIM_ORDER = {
    "health_benefit_claims": [
        "NAD+ Level Support",
        "Cellular Energy Support",
        "Mitochondrial Support",
        "Energy Support",
        "Energy Metabolism Support",
        "Vitality Support",
        "Physical Endurance Support",
        "Healthy Aging Support",
        "Anti-Aging Support",
        "Longevity Support",
        "Cellular Health Support",
        "DNA Repair Support",
        "DNA Health Support",
        "Cellular Repair Support",
        "Cell Resilience Support",
        "Cognitive Function Support",
        "Mental Clarity Support",
        "Focus Support",
        "Brain Health Support",
        "Heart Health Support",
        "Muscle Health Support",
        "Muscle Endurance Support",
        "Muscle Strength Support",
        "Immune Support",
        "Metabolic Health Support",
        "Reduces Fatigue",
        "Oxidative Stress Support",
        "Wellness Support",
    ],
    "certification_claims": [
        "Third-Party Tested",
        "Triple Lab Tested",
        "Laboratory Tested",
        "ISO 17025 Tested",
        "GMP Certified/Compliant",
        "NSF Certified Facility",
        "FDA Registered Facility",
        "Made in USA",
        "USA Manufactured",
        "Made and Certified in USA",
        "Non-GMO",
        "Gluten Free",
        "Soy Free",
        "Vegan",
        "Vegetarian",
        "Dairy Free",
    ],
    "nutritional_claims": [
        "NAD+",
        "NAD+ Supplement",
        "NAD+ Booster",
        "NAD+ Precursor",
        "Nicotinamide Adenine Dinucleotide",
        "NMN",
        "Nicotinamide Mononucleotide",
        "Uthever NMN",
        "Vitamin B3/Niacin Derivative",
        "1,000 mg NAD+ per Serving",
        "1,000 mg NMN per Serving",
        "500 mg NMN per Serving",
        "99% Pure NMN",
        "High-Purity NMN",
        "Stabilized NMN",
        "BioPerine",
        "NAD+ Coenzyme",
        "Sirtuin Activator",
        "Hypromellose Capsule",
        "Magnesium Stearate",
        "Silica",
        "Rice Flour",
        "Veggie Capsules",
        "Plant-Based Capsules",
        "Sublingual Lozenges",
        "Lozenges",
        "Capsules",
        "Tablets",
        "Unflavored",
        "60 Servings",
        "30 Servings",
        "120 Capsules",
        "60 Capsules",
        "120 Lozenges",
    ],
    "structure_function_statements_claims": [
        "Supports NAD+ Levels",
        "Supports NAD+ Production",
        "Boosts NAD+ Levels",
        "Replenishes NAD+ Levels",
        "Supports Cellular Energy",
        "Supports Mitochondrial Function",
        "Supports Energy Production",
        "Supports Energy Metabolism",
        "Supports Daily Energy Levels",
        "Supports Vitality",
        "Supports Physical Endurance",
        "Supports Healthy Cellular Aging",
        "Supports Healthy Aging",
        "Supports Anti-Aging",
        "Supports Longevity",
        "Supports Cellular Health",
        "Supports DNA Repair",
        "Supports DNA Health",
        "Supports Cellular Repair",
        "Supports Cell Resilience",
        "Supports Cognitive Function",
        "Supports Mental Clarity",
        "Supports Focus",
        "Supports Brain Health",
        "Supports Heart Health",
        "Supports Muscle Health",
        "Supports Muscle Endurance",
        "Supports Muscle Strength",
        "Supports Immune System",
        "Supports Metabolic Health",
        "Helps Reduce Fatigue",
        "Protects Against Oxidative Stress",
        "Supports Sirtuin Activation",
        "Enhances Bioavailability",
        "Enhances Absorption",
    ],
    "other_claims": [
        "High Purity",
        "99% Purity",
        "Proven Purity",
        "High Potency",
        "Max Potency",
        "Pure and Potent",
        "Enhanced Bioavailability",
        "Max Absorption",
        "Fast-Acting",
        "Sublingual Delivery",
        "Easy to Swallow",
        "No Mixing Required",
        "Convenient Supply",
        "60-Day Supply",
        "120-Day Supply",
        "30-Day Supply",
        "2-Month Supply",
        "120 Capsules",
        "60 Capsules",
        "120 Lozenges",
        "Stabilized Form",
        "Shelf-Stable",
        "No Refrigeration Needed",
        "Light/Moisture/Oxygen Protected",
        "Doctor-Formulated",
        "Clinically Studied",
        "Clinically Researched",
        "Backed by Science",
        "Quality You Can Trust",
        "Full Transparency",
        "Money-Back Guarantee",
        "Great Taste",
        "Sustainable",
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
        "\u00ae": "",
        "\u03b2": "beta",
        "\uff08": "(",
        "\uff09": ")",
        "\uff1a": ":",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


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
            ("health_benefit_claims", "NAD+ Level Support", r"nad\+|nad production|nad levels"),
            ("health_benefit_claims", "Cellular Energy Support", r"cellular energy|energy"),
            ("health_benefit_claims", "Mitochondrial Support", r"mitochondrial"),
            ("health_benefit_claims", "Energy Support", r"energy|vitality"),
            ("health_benefit_claims", "Healthy Aging Support", r"healthy aging"),
            ("health_benefit_claims", "Anti-Aging Support", r"anti-aging|anti aging"),
            ("health_benefit_claims", "Longevity Support", r"longevity"),
            ("health_benefit_claims", "DNA Health Support", r"healthy dna|\bdna\b"),
            ("health_benefit_claims", "Cognitive Function Support", r"brain|cognitive|mental clarity|focus"),
            ("health_benefit_claims", "Brain Health Support", r"brain"),
            ("health_benefit_claims", "Heart Health Support", r"heart"),
            ("health_benefit_claims", "Muscle Health Support", r"muscle"),
            ("health_benefit_claims", "Immune Support", r"immune"),
            ("health_benefit_claims", "Reduces Fatigue", r"fatigue"),
            ("structure_function_statements_claims", "Supports NAD+ Production", r"nad\+ production|boosts nad"),
            ("structure_function_statements_claims", "Supports NAD+ Levels", r"nad\+|nad levels"),
            ("structure_function_statements_claims", "Supports Cellular Energy", r"cellular energy|energy"),
            ("structure_function_statements_claims", "Supports Mitochondrial Function", r"mitochondrial"),
            ("structure_function_statements_claims", "Supports Healthy Aging", r"healthy aging"),
            ("structure_function_statements_claims", "Supports Anti-Aging", r"anti-aging|anti aging"),
            ("structure_function_statements_claims", "Supports Longevity", r"longevity"),
            ("structure_function_statements_claims", "Supports DNA Health", r"healthy dna|\bdna\b"),
            ("structure_function_statements_claims", "Supports Brain Health", r"brain"),
            ("structure_function_statements_claims", "Supports Heart Health", r"heart"),
            ("structure_function_statements_claims", "Supports Muscle Health", r"muscle"),
            ("structure_function_statements_claims", "Supports Immune System", r"immune"),
            ("structure_function_statements_claims", "Helps Reduce Fatigue", r"fatigue"),
            ("structure_function_statements_claims", "Enhances Absorption", r"absorption|max absorption"),
            ("certification_claims", "Third-Party Tested", r"third[- ]party|3rd[- ]party"),
            ("certification_claims", "Triple Lab Tested", r"triple[- ]tested|triple lab"),
            ("certification_claims", "Laboratory Tested", r"lab[- ]tested|laboratory-tested"),
            ("certification_claims", "GMP Certified/Compliant", r"gmp"),
            ("certification_claims", "NSF Certified Facility", r"nsf certified"),
            ("certification_claims", "FDA Registered Facility", r"fda registered"),
            ("certification_claims", "Made in USA", r"made in (the )?usa"),
            ("certification_claims", "USA Manufactured", r"usa manufactured|manufactured in the usa"),
            ("certification_claims", "Made and Certified in USA", r"made and certified in the usa"),
            ("certification_claims", "Non-GMO", r"non[- ]?gmo|gmo"),
            ("certification_claims", "Gluten Free", r"gluten[- ]free|gluten free"),
            ("certification_claims", "Soy Free", r"soy free|soy-free"),
            ("certification_claims", "Vegan", r"vegan"),
            ("nutritional_claims", "NAD+", r"nad\+"),
            ("nutritional_claims", "NMN", r"\bnmn\b"),
            ("nutritional_claims", "Nicotinamide Mononucleotide", r"nicotinamide mononucleotide"),
            ("nutritional_claims", "Nicotinamide Adenine Dinucleotide", r"nicotinamide adenine dinucleotide"),
            ("nutritional_claims", "99% Pure NMN", r"99% pure|99% purity"),
            ("nutritional_claims", "500 mg NMN per Serving", r"500\s?mg"),
            ("nutritional_claims", "1,000 mg NMN per Serving", r"1000\s?mg|1,000\s?mg"),
            ("other_claims", "High Purity", r"high purity|purity|proven purity"),
            ("other_claims", "99% Purity", r"99% pure|99% purity"),
            ("other_claims", "High Potency", r"high potency|potency"),
            ("other_claims", "Max Potency", r"max potency"),
            ("other_claims", "Enhanced Bioavailability", r"bioavailability"),
            ("other_claims", "Max Absorption", r"max absorption|absorption"),
            ("other_claims", "Great Taste", r"great taste"),
            ("other_claims", "Sustainable", r"sustainable"),
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
        ("health_benefit_claims", "NAD+ Level Support", r"nad\+ levels?|nad levels?|boost your nad|more nad"),
        ("health_benefit_claims", "Cellular Energy Support", r"cellular energy"),
        ("health_benefit_claims", "Mitochondrial Support", r"mitochondrial support|mitochondria"),
        ("health_benefit_claims", "Energy Support", r"energy management|energy levels?|more energy|daily energy|energized|energy support"),
        ("health_benefit_claims", "Energy Metabolism Support", r"energy metabolism|metabolism management"),
        ("health_benefit_claims", "Vitality Support", r"vitality"),
        ("health_benefit_claims", "Physical Endurance Support", r"physical endurance|endurance"),
        ("health_benefit_claims", "Healthy Aging Support", r"healthy (?:cellular )?aging"),
        ("health_benefit_claims", "Anti-Aging Support", r"anti[- ]aging"),
        ("health_benefit_claims", "Longevity Support", r"longevity|living better longer"),
        ("health_benefit_claims", "Cellular Health Support", r"cellular health|cells'health|cell health"),
        ("health_benefit_claims", "DNA Repair Support", r"dna repair"),
        ("health_benefit_claims", "DNA Health Support", r"healthy dna|genetic damage"),
        ("health_benefit_claims", "Cellular Repair Support", r"cellular repair|cell repair"),
        ("health_benefit_claims", "Cell Resilience Support", r"cell(?:s)?[' ]* normal function and resilience|resilience"),
        ("health_benefit_claims", "Cognitive Function Support", r"cognitive function|neurological function"),
        ("health_benefit_claims", "Mental Clarity Support", r"mental clarity"),
        ("health_benefit_claims", "Focus Support", r"\bfocus\b"),
        ("health_benefit_claims", "Brain Health Support", r"brain health|brain"),
        ("health_benefit_claims", "Heart Health Support", r"heart health|heart"),
        ("health_benefit_claims", "Muscle Health Support", r"muscle health|muscles?"),
        ("health_benefit_claims", "Muscle Endurance Support", r"muscle endurance"),
        ("health_benefit_claims", "Muscle Strength Support", r"strength"),
        ("health_benefit_claims", "Immune Support", r"immune system|immune defense|immune support"),
        ("health_benefit_claims", "Metabolic Health Support", r"metabolic health"),
        ("health_benefit_claims", "Reduces Fatigue", r"reduces fatigue|fatigue"),
        ("health_benefit_claims", "Oxidative Stress Support", r"oxidative stress"),
        ("health_benefit_claims", "Wellness Support", r"wellness"),
        ("structure_function_statements_claims", "Supports NAD+ Levels", r"nad\+ levels?|nad levels?|more nad"),
        ("structure_function_statements_claims", "Supports NAD+ Production", r"nad\+ production|nad production"),
        ("structure_function_statements_claims", "Boosts NAD+ Levels", r"boost(?:ing)? nad\+|boost your nad|increase nad\+|raising blood nad"),
        ("structure_function_statements_claims", "Replenishes NAD+ Levels", r"replenish nad\+ levels|restore youthful nad\+ levels"),
        ("structure_function_statements_claims", "Supports Cellular Energy", r"cellular energy"),
        ("structure_function_statements_claims", "Supports Mitochondrial Function", r"mitochondrial support|mitochondria"),
        ("structure_function_statements_claims", "Supports Energy Production", r"energy production"),
        ("structure_function_statements_claims", "Supports Energy Metabolism", r"energy metabolism|metabolism management"),
        ("structure_function_statements_claims", "Supports Daily Energy Levels", r"daily energy|energy levels?|more energy|energized"),
        ("structure_function_statements_claims", "Supports Vitality", r"vitality"),
        ("structure_function_statements_claims", "Supports Physical Endurance", r"physical endurance|endurance"),
        ("structure_function_statements_claims", "Supports Healthy Cellular Aging", r"healthy cellular aging"),
        ("structure_function_statements_claims", "Supports Healthy Aging", r"healthy aging"),
        ("structure_function_statements_claims", "Supports Anti-Aging", r"anti[- ]aging"),
        ("structure_function_statements_claims", "Supports Longevity", r"longevity|living better longer"),
        ("structure_function_statements_claims", "Supports Cellular Health", r"cellular health|cells'health|cell health"),
        ("structure_function_statements_claims", "Supports DNA Repair", r"dna repair"),
        ("structure_function_statements_claims", "Supports DNA Health", r"healthy dna|genetic damage"),
        ("structure_function_statements_claims", "Supports Cellular Repair", r"cellular repair|cell repair"),
        ("structure_function_statements_claims", "Supports Cell Resilience", r"cell(?:s)?[' ]* normal function and resilience|resilience"),
        ("structure_function_statements_claims", "Supports Cognitive Function", r"cognitive function|neurological function"),
        ("structure_function_statements_claims", "Supports Mental Clarity", r"mental clarity"),
        ("structure_function_statements_claims", "Supports Focus", r"\bfocus\b"),
        ("structure_function_statements_claims", "Supports Brain Health", r"brain health|brain"),
        ("structure_function_statements_claims", "Supports Heart Health", r"heart health|heart"),
        ("structure_function_statements_claims", "Supports Muscle Health", r"muscle health|muscles?"),
        ("structure_function_statements_claims", "Supports Muscle Endurance", r"muscle endurance"),
        ("structure_function_statements_claims", "Supports Muscle Strength", r"strength"),
        ("structure_function_statements_claims", "Supports Immune System", r"immune system|immune defense|immune support"),
        ("structure_function_statements_claims", "Supports Metabolic Health", r"metabolic health"),
        ("structure_function_statements_claims", "Helps Reduce Fatigue", r"reduces fatigue|fatigue"),
        ("structure_function_statements_claims", "Protects Against Oxidative Stress", r"oxidative stress"),
        ("structure_function_statements_claims", "Supports Sirtuin Activation", r"sirtuin"),
        ("structure_function_statements_claims", "Enhances Bioavailability", r"bioavailability enhancer|increase .*bioavailability|greatly increase the bioavailability"),
        ("structure_function_statements_claims", "Enhances Absorption", r"enhanced absorption|enhance absorption|increase nmn absorption|max absorption|absorbed directly"),
        ("certification_claims", "Third-Party Tested", r"third[- ]party tested|3rd party tested|third-party tested"),
        ("certification_claims", "Triple Lab Tested", r"triple[- ]tested|triple lab[- ]tested"),
        ("certification_claims", "Laboratory Tested", r"laboratory[- ]tested|lab[- ]tested"),
        ("certification_claims", "ISO 17025 Tested", r"iso 17025"),
        ("certification_claims", "GMP Certified/Compliant", r"gmp[- ]certified|gmp compliant|gmp-certified"),
        ("certification_claims", "NSF Certified Facility", r"nsf certified"),
        ("certification_claims", "FDA Registered Facility", r"fda registered"),
        ("certification_claims", "Made in USA", r"made in the usa|made in usa|here in the usa"),
        ("certification_claims", "USA Manufactured", r"usa manufactured|manufactured in the usa"),
        ("certification_claims", "Made and Certified in USA", r"made and certified in the usa"),
        ("certification_claims", "Non-GMO", r"non[- ]?gmo|without genetically modified ingredients|gmos"),
        ("certification_claims", "Gluten Free", r"gluten[- ]free|gluten free"),
        ("certification_claims", "Soy Free", r"soy free|soy-free"),
        ("certification_claims", "Vegan", r"vegan"),
        ("certification_claims", "Vegetarian", r"vegetarian"),
        ("certification_claims", "Dairy Free", r"dairy free|dairy-free"),
        ("nutritional_claims", "NAD+", r"nad\+|\bnad\b"),
        ("nutritional_claims", "NAD+ Supplement", r"nad\+ supplement|nad supplement"),
        ("nutritional_claims", "NAD+ Booster", r"nad\+ booster|nad booster"),
        ("nutritional_claims", "NAD+ Precursor", r"nad\+ precursor|precursor to nad"),
        ("nutritional_claims", "Nicotinamide Adenine Dinucleotide", r"nicotinamide adenine dinucleotide"),
        ("nutritional_claims", "NMN", r"\bnmn\b"),
        ("nutritional_claims", "Nicotinamide Mononucleotide", r"nicotinamide mononucleotide"),
        ("nutritional_claims", "Uthever NMN", r"uthev|uthever"),
        ("nutritional_claims", "Vitamin B3/Niacin Derivative", r"vitamin b3|niacin"),
        ("nutritional_claims", "1,000 mg NAD+ per Serving", r"1,?000\s?mg.*(?:nad\+|nicotinamide adenine dinucleotide)|(?:nad\+|nicotinamide adenine dinucleotide).*1,?000\s?mg"),
        ("nutritional_claims", "1,000 mg NMN per Serving", r"1,?000\s?mg.*(?:nmn|nicotinamide mononucleotide)|(?:nmn|nicotinamide mononucleotide).*1,?000\s?mg"),
        ("nutritional_claims", "500 mg NMN per Serving", r"500\s?mg.*(?:nmn|nicotinamide mononucleotide)|(?:nmn|nicotinamide mononucleotide).*500\s?mg"),
        ("nutritional_claims", "99% Pure NMN", r"99% pure.*nmn|99% purity|99% high purity"),
        ("nutritional_claims", "High-Purity NMN", r"high[- ]purity.*nmn|purest.*nmn"),
        ("nutritional_claims", "Stabilized NMN", r"stabilized.*nmn|shelf-stable.*nmn"),
        ("nutritional_claims", "BioPerine", r"bioperine"),
        ("nutritional_claims", "NAD+ Coenzyme", r"vital coenzyme"),
        ("nutritional_claims", "Sirtuin Activator", r"sirtuin"),
        ("nutritional_claims", "Hypromellose Capsule", r"hypromellose"),
        ("nutritional_claims", "Magnesium Stearate", r"magnesium stear"),
        ("nutritional_claims", "Silica", r"silica"),
        ("nutritional_claims", "Rice Flour", r"rice flour"),
        ("nutritional_claims", "Veggie Capsules", r"veggie capsules"),
        ("nutritional_claims", "Plant-Based Capsules", r"plant[- ]based capsules"),
        ("nutritional_claims", "Sublingual Lozenges", r"sublingual.*lozenges|lozenges.*sublingual"),
        ("nutritional_claims", "Lozenges", r"lozenges?|lozeng"),
        ("nutritional_claims", "Capsules", r"capsules?|capsule"),
        ("nutritional_claims", "Tablets", r"tablet"),
        ("nutritional_claims", "Unflavored", r"unflavored"),
        ("nutritional_claims", "60 Servings", r"60 servings|total servings per container 60"),
        ("nutritional_claims", "30 Servings", r"30 servings|servings per container: 30|total servings per container 30"),
        ("nutritional_claims", "120 Capsules", r"120 capsules|120 count"),
        ("nutritional_claims", "60 Capsules", r"60 capsules"),
        ("nutritional_claims", "120 Lozenges", r"120 lozenges"),
        ("other_claims", "High Purity", r"high purity|high-purity|purest"),
        ("other_claims", "99% Purity", r"99% purity|99% pure"),
        ("other_claims", "Proven Purity", r"proven purity"),
        ("other_claims", "High Potency", r"high potency|potent"),
        ("other_claims", "Max Potency", r"max potency|maximum potency|full potency"),
        ("other_claims", "Pure and Potent", r"purest.*potent|pure and potent|safety, potency, and purity"),
        ("other_claims", "Enhanced Bioavailability", r"enhanced bioavailability|bioavailability enhancer|increase .*bioavailability"),
        ("other_claims", "Max Absorption", r"max absorption|max absorbency|enhance absorption|absorbed directly|increase nmn absorption"),
        ("other_claims", "Fast-Acting", r"fast[- ]acting"),
        ("other_claims", "Sublingual Delivery", r"sublingual"),
        ("other_claims", "Easy to Swallow", r"easy-to-swallow|easy to swallow"),
        ("other_claims", "No Mixing Required", r"no mixing|no mixing or prep"),
        ("other_claims", "Convenient Supply", r"convenient and long-lasting supply"),
        ("other_claims", "60-Day Supply", r"60-day supply"),
        ("other_claims", "120-Day Supply", r"120-day supply|120 days supply"),
        ("other_claims", "30-Day Supply", r"30 servings|1 month"),
        ("other_claims", "2-Month Supply", r"2-month supply|2 month supply"),
        ("other_claims", "120 Capsules", r"120 capsules"),
        ("other_claims", "60 Capsules", r"60 capsules"),
        ("other_claims", "120 Lozenges", r"120 lozenges"),
        ("other_claims", "Stabilized Form", r"stabilized form|fully stabilized"),
        ("other_claims", "Shelf-Stable", r"shelf-stable"),
        ("other_claims", "No Refrigeration Needed", r"non-refrigerated|fridge or freezer"),
        ("other_claims", "Light/Moisture/Oxygen Protected", r"block light, moisture, and oxygen|light, moisture, and oxygen"),
        ("other_claims", "Doctor-Formulated", r"doctor-formulated"),
        ("other_claims", "Clinically Studied", r"clinically studied|clinically tested"),
        ("other_claims", "Clinically Researched", r"clinically researched"),
        ("other_claims", "Backed by Science", r"backed by science"),
        ("other_claims", "Quality You Can Trust", r"quality you can trust|you can trust"),
        ("other_claims", "Full Transparency", r"full transparency"),
        ("other_claims", "Money-Back Guarantee", r"money-back guarantee"),
        ("other_claims", "Great Taste", r"great taste"),
        ("other_claims", "Sustainable", r"sustainable"),
    ]

    for category, claim, pattern in rules:
        bag.add_from_pattern(primary_sources, category, claim, pattern, primary_labels)

    aplus_rules = [
        ("certification_claims", "Third-Party Tested", r"third party tested|3rd party tested"),
        ("certification_claims", "GMP Certified/Compliant", r"gmp certified|gmp compliant"),
        ("certification_claims", "Made and Certified in USA", r"made and certified in the usa"),
        ("other_claims", "Backed by Science", r"backed by science"),
        ("other_claims", "Clinically Studied", r"clinically tested|clinically studied"),
        ("health_benefit_claims", "Immune Support", r"immune defense|immune support"),
        ("structure_function_statements_claims", "Supports Immune System", r"immune defense|immune support"),
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
