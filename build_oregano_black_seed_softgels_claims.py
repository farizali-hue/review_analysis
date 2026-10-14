from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROWS_JSON = Path(r"D:\analysis\oregano_black_seed_softgels_rows.json")
BROWSER_JSON = Path(r"D:\analysis\oregano_black_seed_softgels_browser_sections.json")
OUT_ROW = Path(r"D:\analysis\claims_oregano_black_seed_softgels_formalized_with_evidence.csv")
OUT_CLAIM = Path(r"D:\analysis\claims_oregano_black_seed_softgels_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\claims_oregano_black_seed_softgels_claim_order.csv")

CATEGORIES = [
    "health_benefit_claims",
    "certification_claims",
    "nutritional_claims",
    "structure_function_statements_claims",
    "other_claims",
]

CLAIM_ORDER = {
    "health_benefit_claims": [
        "Immune Support",
        "Seasonal Immune Support",
        "Immune Defense",
        "Digestive Health Support",
        "Gut Health Support",
        "Gut Cleanse Support",
        "Respiratory Health Support",
        "Antioxidant Support",
        "Cellular Health Support",
        "Body Balance Support",
        "Overall Wellness Support",
        "Energy Support",
        "Skin and Hair Health Support",
        "Joint Health Support",
        "Anxiety Relief",
        "Inflammation Relief",
        "Microbial Balance Support",
        "Bone Health Support",
        "Nerve and Muscle Health Support",
        "Rest and Relaxation Support",
    ],
    "certification_claims": [
        "Non-GMO Project Verified",
        "Non-GMO",
        "Gluten Free",
        "Dairy Free",
        "Soy Free",
        "Tree Nut Free",
        "No Artificial Additives",
        "No Preservatives",
        "No Added Flavors",
        "Plant Based",
        "Vegetarian",
        "Vegan",
        "Organic",
        "GMP Certified/Compliant",
        "Lab Tested",
        "Third-Party Lab Tested",
    ],
    "nutritional_claims": [
        "Oil of Oregano",
        "Wild Oregano Oil",
        "Black Seed Oil",
        "2-in-1 Oregano Oil and Black Seed Oil Formula",
        "Origanum minutiflorum",
        "Nigella sativa",
        "Cold-Pressed Black Seed Oil",
        "Organic Oregano Oil",
        "300 mg Oil of Oregano per Serving",
        "300 mg Oregano Oil Extract",
        "200 mg Black Seed Oil per Serving",
        "6,000 mg Oil of Oregano per Serving",
        "9,000 mg per Serving",
        "20:1 Oregano Oil Extract",
        "30:1 Oregano Oil Equivalent",
        "4X Strength Carvacrol and Thymoquinone",
        "High Carvacrol",
        "Carvacrol-Rich Oregano Oil",
        "Naturally Occurring Carvacrol",
        "165 mg Naturally Occurring Carvacrol",
        "Thymoquinone",
        "Naturally Occurring Thymoquinone",
        "Natural Active Compounds",
        "Natural Antioxidants",
        "Herbal Formula",
        "Seaweed",
        "Apple Cider Vinegar Blend",
        "Extra Virgin Olive Oil",
        "Gelatin",
        "Glycerin",
        "Purified Water",
        "Softgels",
        "Capsules",
        "Dietary Supplement",
    ],
    "structure_function_statements_claims": [
        "Supports Immune System",
        "Supports Seasonal Immune Health",
        "Maintains Immune Balance",
        "Supports Digestive Health",
        "Maintains Digestive Balance",
        "Supports Gut Health",
        "Supports Gut Cleanse",
        "Supports Respiratory Function",
        "Provides Antioxidant Protection",
        "Helps Neutralize Free Radicals",
        "Supports Cellular Health",
        "Supports Microbial Balance",
        "Supports Daily Vitality",
        "Promotes Overall Health and Vitality",
        "Supports Body Balance",
        "Supports Skin and Hair Health",
        "Supports Joint Health",
        "Promotes Nutrient Absorption",
        "Supports Bone Health",
        "Supports Nerve and Muscle Health",
        "Promotes Rest and Relaxation",
        "Maintains Bodily Functions",
    ],
    "other_claims": [
        "Premium Quality",
        "Premium Grade",
        "Quality Assured",
        "Safe, Pure and Potent",
        "Purity You Can Trust",
        "Easy to Swallow",
        "No Strong Aftertaste",
        "No Strong Odor",
        "Enteric-Coated Capsules",
        "Better Absorption",
        "Convenient Daily Use",
        "UV-Blocking Bottle and Oxygen Absorbers",
        "Airtight Seal Protects Potency",
        "150-Day Supply",
        "140-Day Supply",
        "75-Day Supply",
        "60-Day Supply",
        "30-Day Supply",
        "300 Softgels",
        "280 Softgels",
        "180 Count",
        "150 Softgels",
        "120 Softgels",
        "60 Softgels",
        "Family Wellness Solution",
        "Natural Herbal Supplement",
        "Natural Defense",
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
        "\u2022": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ascii_clean(value: object) -> str:
    text = clean_text(value)
    return text.encode("ascii", errors="ignore").decode("ascii").strip()


def split_pipes(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*", text) if part.strip()]


def split_snippets(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\s+\|\s+|(?<=:)\s+(?=[A-Z][A-Za-z])", text)
    return [p.strip() for p in parts if len(p.strip()) >= 5]


def compact_snippet(text: str, pattern: str | None = None, max_len: int = 360) -> str:
    text = ascii_clean(text)
    if len(text) <= max_len:
        return text
    if pattern:
        match = re.search(pattern, text, flags=re.I)
        if match:
            start = max(0, match.start() - 120)
            end = min(len(text), match.end() + 220)
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
        evidence = self.data[category].get(claim, [])
        return " || ".join(evidence[:4])

    def category_evidence(self, category: str) -> str:
        chunks = []
        for claim in self.claims(category):
            chunks.append(f"{claim}: {self.evidence_for(category, claim)}")
        return " || ".join(chunks)


def source_evidence(row: dict[str, str], source_category: str) -> str:
    evidence = row.get(f"{source_category}_evidence", "")
    source = row.get(f"{source_category}_source", "")
    text = evidence or row.get(source_category, "")
    bits = []
    if text:
        bits.append(compact_snippet(text, max_len=420))
    if source:
        bits.append(f"source={source}")
    return "Input image extraction: " + "; ".join(bits)


def add_existing_image_claims(row: dict[str, str], bag: ClaimBag) -> None:
    contexts: list[tuple[str, str, str]] = []
    for source_category in CATEGORIES:
        claims = row.get(source_category, "")
        if not claims:
            continue
        evidence = source_evidence(row, source_category)
        contexts.append((source_category, claims, evidence))

    for source_category, raw_claims, evidence in contexts:
        full = " | ".join([raw_claims, row.get(f"{source_category}_evidence", "")])
        low = full.lower()

        if re.search(r"non[- ]?gmo|gmo free|no gmo|genetically modified organism", low):
            bag.add("certification_claims", "Non-GMO", evidence)
        if re.search(r"gluten", low):
            bag.add("certification_claims", "Gluten Free", evidence)
        if re.search(r"dairy", low):
            bag.add("certification_claims", "Dairy Free", evidence)
        if re.search(r"\bsoy\b", low):
            bag.add("certification_claims", "Soy Free", evidence)
        if re.search(r"tree nuts?|tree[- ]?nut", low):
            bag.add("certification_claims", "Tree Nut Free", evidence)
        if re.search(r"lab tested|3rd party|third[- ]party", low):
            bag.add("certification_claims", "Lab Tested", evidence)
        if re.search(r"gmp", low):
            bag.add("certification_claims", "GMP Certified/Compliant", evidence)
        if re.search(r"plant based|plant-based", low):
            bag.add("certification_claims", "Plant Based", evidence)

        if re.search(r"immune", low):
            bag.add("health_benefit_claims", "Immune Support", evidence)
            bag.add("structure_function_statements_claims", "Supports Immune System", evidence)
        if re.search(r"digest|gut", low):
            bag.add("health_benefit_claims", "Digestive Health Support", evidence)
            bag.add("structure_function_statements_claims", "Supports Digestive Health", evidence)
        if re.search(r"natural antioxidant|antioxidant", low):
            bag.add("health_benefit_claims", "Antioxidant Support", evidence)
            bag.add("structure_function_statements_claims", "Provides Antioxidant Protection", evidence)
        if re.search(r"easy to swallow", low):
            bag.add("other_claims", "Easy to Swallow", evidence)
        if re.search(r"quality assured", low):
            bag.add("other_claims", "Quality Assured", evidence)
        if re.search(r"stay healthy", low):
            bag.add("other_claims", "Natural Herbal Supplement", evidence)
        if re.search(r"naturally occurring thymoquinone", low):
            bag.add("nutritional_claims", "Naturally Occurring Thymoquinone", evidence)
        if re.search(r"thymoquinone", low):
            bag.add("nutritional_claims", "Thymoquinone", evidence)
        if re.search(r"carvacrol", low):
            bag.add("nutritional_claims", "High Carvacrol", evidence)
        if re.search(r"maintain bodily functions", low):
            bag.add("structure_function_statements_claims", "Maintains Bodily Functions", evidence)
        if re.search(r"\bbone\b", low):
            bag.add("health_benefit_claims", "Bone Health Support", evidence)
            bag.add("structure_function_statements_claims", "Supports Bone Health", evidence)
        if re.search(r"nerve and muscle", low):
            bag.add("health_benefit_claims", "Nerve and Muscle Health Support", evidence)
            bag.add("structure_function_statements_claims", "Supports Nerve and Muscle Health", evidence)
        if re.search(r"rest and relaxation", low):
            bag.add("health_benefit_claims", "Rest and Relaxation Support", evidence)
            bag.add("structure_function_statements_claims", "Promotes Rest and Relaxation", evidence)


def build_sources(rec: dict) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    sections = rec.get("sections", {})
    sources: list[tuple[str, str]] = []

    def add(label: str, value: object) -> None:
        if isinstance(value, list):
            for item in value:
                text = clean_text(item)
                if text:
                    sources.append((label, text))
        else:
            text = clean_text(value)
            if text:
                sources.append((label, text))

    add("Page title", sections.get("productTitle") or rec.get("title"))
    add("Feature bullets", sections.get("featureBullets"))
    add("Product specs/details", sections.get("detailTables"))
    add("Product details", sections.get("productDetails"))
    add("Important information", sections.get("importantInformation"))
    add("Product description", sections.get("productDescription"))

    aplus_sources: list[tuple[str, str]] = []
    for item in sections.get("aplus") or []:
        text = clean_text(item)
        if text:
            aplus_sources.append(("A+ content", text))

    return sources, sources + aplus_sources


def add_page_claims(rec: dict, bag: ClaimBag) -> None:
    primary_sources, all_sources = build_sources(rec)
    title_feature_specs = {"Page title", "Feature bullets", "Product specs/details", "Product details", "Important information", "Product description"}

    rules = [
        ("health_benefit_claims", "Immune Support", r"immune (support|health|system|protection|function)|boost immunity|immunity-focused|immune enhancement"),
        ("health_benefit_claims", "Seasonal Immune Support", r"seasonal immune"),
        ("health_benefit_claims", "Immune Defense", r"immune defense|defense[s]?"),
        ("health_benefit_claims", "Digestive Health Support", r"digestive health|healthy digestion|digestion|digestive function|digestive balance|poor digestion|digestive discomfort"),
        ("health_benefit_claims", "Gut Health Support", r"gut health|balanced gut|gut wellness|microbiome"),
        ("health_benefit_claims", "Gut Cleanse Support", r"gut cleanse"),
        ("health_benefit_claims", "Respiratory Health Support", r"respiratory (health|function)|breathe easier"),
        ("health_benefit_claims", "Antioxidant Support", r"antioxidant|free radicals"),
        ("health_benefit_claims", "Cellular Health Support", r"cellular health"),
        ("health_benefit_claims", "Body Balance Support", r"body balance"),
        ("health_benefit_claims", "Overall Wellness Support", r"overall (health|wellness|well-being)|wellness routine|daily wellness"),
        ("health_benefit_claims", "Energy Support", r"boost energy|increase energy|more energy|energized|daily vitality|vitality"),
        ("health_benefit_claims", "Skin and Hair Health Support", r"skin and hair health"),
        ("health_benefit_claims", "Joint Health Support", r"joint health"),
        ("health_benefit_claims", "Anxiety Relief", r"anxiety relief"),
        ("health_benefit_claims", "Inflammation Relief", r"inflammation relief"),
        ("health_benefit_claims", "Microbial Balance Support", r"microbial (balance|harmony)|clear unwanted microbes"),
        ("structure_function_statements_claims", "Supports Immune System", r"immune (support|health|system|protection|function)|boost immunity|immunity-focused|immune enhancement"),
        ("structure_function_statements_claims", "Supports Seasonal Immune Health", r"seasonal immune"),
        ("structure_function_statements_claims", "Maintains Immune Balance", r"maintain[s]? immune balance"),
        ("structure_function_statements_claims", "Supports Digestive Health", r"digestive health|healthy digestion|digestion|digestive function|poor digestion|digestive discomfort"),
        ("structure_function_statements_claims", "Maintains Digestive Balance", r"digestive balance"),
        ("structure_function_statements_claims", "Supports Gut Health", r"gut health|balanced gut|gut wellness|microbiome"),
        ("structure_function_statements_claims", "Supports Gut Cleanse", r"gut cleanse"),
        ("structure_function_statements_claims", "Supports Respiratory Function", r"respiratory (health|function)|breathe easier"),
        ("structure_function_statements_claims", "Provides Antioxidant Protection", r"antioxidant protection|antioxidant support|antioxidant effects|natural antioxidants|antioxidant"),
        ("structure_function_statements_claims", "Helps Neutralize Free Radicals", r"free radicals|neutralize harmful free radicals|combat free radicals"),
        ("structure_function_statements_claims", "Supports Cellular Health", r"cellular health"),
        ("structure_function_statements_claims", "Supports Microbial Balance", r"microbial (balance|harmony)|clear unwanted microbes"),
        ("structure_function_statements_claims", "Supports Daily Vitality", r"daily vitality|vitality"),
        ("structure_function_statements_claims", "Promotes Overall Health and Vitality", r"promote overall health and vitality|overall health|overall well-being"),
        ("structure_function_statements_claims", "Supports Body Balance", r"body balance"),
        ("structure_function_statements_claims", "Supports Skin and Hair Health", r"skin and hair health"),
        ("structure_function_statements_claims", "Supports Joint Health", r"joint health"),
        ("structure_function_statements_claims", "Promotes Nutrient Absorption", r"nutrient absorption|enhance absorption|better absorption|easy to absorb"),
        ("certification_claims", "Non-GMO Project Verified", r"non[- ]gmo project verified"),
        ("certification_claims", "Non-GMO", r"non[- ]?gmo|gmo free|genetically modified organism"),
        ("certification_claims", "Gluten Free", r"gluten[- ]free|free (?:from|of) [^.]*gluten|without [^.]*gluten|made without [^.]*gluten|diet type gluten free"),
        ("certification_claims", "Dairy Free", r"dairy[- ]free|free (?:from|of) [^.]*dairy|without [^.]*dairy|made without [^.]*dairy|allergen information.*dairy free"),
        ("certification_claims", "Soy Free", r"soy[- ]free|free (?:from|of) [^.]*soy|without [^.]*soy|made without [^.]*soy|allergen information.*soy free"),
        ("certification_claims", "Tree Nut Free", r"tree[- ]?nut free|free (?:from|of) [^.]*tree nuts?|without [^.]*tree nuts?|made without [^.]*tree nuts?|tree nuts|tree nut"),
        ("certification_claims", "No Artificial Additives", r"artificial additives|unnecessary additives|synthetic additives|harmful additives"),
        ("certification_claims", "No Preservatives", r"without .*preservatives|made without .*preservatives|no preservatives"),
        ("certification_claims", "No Added Flavors", r"without .*flavors|made without .*flavors|no added flavors"),
        ("certification_claims", "Plant Based", r"plant[- ]based"),
        ("certification_claims", "Vegetarian", r"vegetarian"),
        ("certification_claims", "Organic", r"\borganic\b"),
        ("certification_claims", "GMP Certified/Compliant", r"\bgmp\b"),
        ("certification_claims", "Lab Tested", r"\blab tested\b"),
        ("certification_claims", "Third-Party Lab Tested", r"3rd party lab test|third[- ]party tested|third party tested|third[- ]party lab"),
        ("nutritional_claims", "Oil of Oregano", r"oil of oregano|oregano oil"),
        ("nutritional_claims", "Wild Oregano Oil", r"wild oregano oil"),
        ("nutritional_claims", "Black Seed Oil", r"black seed oil"),
        ("nutritional_claims", "2-in-1 Oregano Oil and Black Seed Oil Formula", r"2[- ]?in[- ]?1|2 in 1"),
        ("nutritional_claims", "Origanum minutiflorum", r"origanum minutiflorum"),
        ("nutritional_claims", "Nigella sativa", r"nigella sativa"),
        ("nutritional_claims", "Cold-Pressed Black Seed Oil", r"cold[- ]pressed black seed oil"),
        ("nutritional_claims", "Organic Oregano Oil", r"organic oregano oil|organic capsules"),
        ("nutritional_claims", "300 mg Oil of Oregano per Serving", r"300\s?mg (?:of )?(?:fresh )?oil of oregano.*per serving|per serving.*300\s?mg.*oil of oregano"),
        ("nutritional_claims", "300 mg Oregano Oil Extract", r"300\s?mg.*(?:oregano oil extract|fresh oregano oil extract)"),
        ("nutritional_claims", "200 mg Black Seed Oil per Serving", r"200\s?mg black seed oil|black seed oil.*200\s?mg"),
        ("nutritional_claims", "6,000 mg Oil of Oregano per Serving", r"6,?000\s?mg.*(?:oil of oregano|oregano oil)|(?:oil of oregano|oregano oil).*6,?000\s?mg"),
        ("nutritional_claims", "9,000 mg per Serving", r"9,?000\s?mg per serving"),
        ("nutritional_claims", "20:1 Oregano Oil Extract", r"20:1 .*oregano|20:1 extract"),
        ("nutritional_claims", "30:1 Oregano Oil Equivalent", r"30:1 herbal equivalent"),
        ("nutritional_claims", "4X Strength Carvacrol and Thymoquinone", r"4x strength.*carvacrol.*thymoquinone|4x strength of carvacrol and thymoquinone"),
        ("nutritional_claims", "High Carvacrol", r"high carvacrol|high concentrated carvacrol"),
        ("nutritional_claims", "Carvacrol-Rich Oregano Oil", r"carvacrol[- ]rich"),
        ("nutritional_claims", "Naturally Occurring Carvacrol", r"naturally occurring carvacrol"),
        ("nutritional_claims", "165 mg Naturally Occurring Carvacrol", r"165\s?mg.*carvacrol"),
        ("nutritional_claims", "Thymoquinone", r"thymoquinone"),
        ("nutritional_claims", "Naturally Occurring Thymoquinone", r"naturally occurring thymoquinone"),
        ("nutritional_claims", "Natural Active Compounds", r"natural active compounds|active compounds"),
        ("nutritional_claims", "Natural Antioxidants", r"natural antioxidants"),
        ("nutritional_claims", "Herbal Formula", r"herbal ingredients|herbal blend|herbal formula|herbal supplement"),
        ("nutritional_claims", "Seaweed", r"\bseaweed\b"),
        ("nutritional_claims", "Apple Cider Vinegar Blend", r"apple cider vinegar"),
        ("nutritional_claims", "Extra Virgin Olive Oil", r"extra virgin olive oil"),
        ("nutritional_claims", "Gelatin", r"\bgelatin\b"),
        ("nutritional_claims", "Glycerin", r"\bglycerin\b"),
        ("nutritional_claims", "Purified Water", r"purified water"),
        ("nutritional_claims", "Softgels", r"softgels?|softgel form"),
        ("nutritional_claims", "Capsules", r"capsules?|capsule form"),
        ("nutritional_claims", "Dietary Supplement", r"dietary supplement"),
        ("other_claims", "Premium Quality", r"premium quality"),
        ("other_claims", "Premium Grade", r"premium grade"),
        ("other_claims", "Safe, Pure and Potent", r"safe, pure, and potent|safe, pure and potent"),
        ("other_claims", "Purity You Can Trust", r"purity you can trust"),
        ("other_claims", "Easy to Swallow", r"easy[- ]to[- ]swallow|easy to swallow"),
        ("other_claims", "No Strong Aftertaste", r"no unpleasant aftertaste|minimize .*aftertaste|no strong taste"),
        ("other_claims", "No Strong Odor", r"without the strong odor|no strong odor|strong odor"),
        ("other_claims", "Enteric-Coated Capsules", r"enteric[- ]coated"),
        ("other_claims", "Better Absorption", r"better absorption|enhance absorption|optimal nutrient absorption|easy to absorb"),
        ("other_claims", "Convenient Daily Use", r"convenient daily use|daily wellness routine|easy daily consumption|easy to carry"),
        ("other_claims", "UV-Blocking Bottle and Oxygen Absorbers", r"uv[- ]blocking bottles? with oxygen absorbers|oxygen absorbers"),
        ("other_claims", "Airtight Seal Protects Potency", r"airtight seal.*potency|protects contents from oxidation|preserving potency"),
        ("other_claims", "150-Day Supply", r"150[- ]day supply"),
        ("other_claims", "140-Day Supply", r"140[- ]day"),
        ("other_claims", "75-Day Supply", r"75[- ]day supply"),
        ("other_claims", "60-Day Supply", r"60[- ]day supply"),
        ("other_claims", "30-Day Supply", r"30[- ]day supply"),
        ("other_claims", "300 Softgels", r"300 (?:count|softgels?)"),
        ("other_claims", "280 Softgels", r"280[- ]capsule|280 softgels?|280 count"),
        ("other_claims", "180 Count", r"180 count"),
        ("other_claims", "150 Softgels", r"150 (?:count|softgels?)"),
        ("other_claims", "120 Softgels", r"120 (?:count|softgels?)"),
        ("other_claims", "60 Softgels", r"60 (?:count|softgels?)"),
        ("other_claims", "Family Wellness Solution", r"family wellness solution"),
        ("other_claims", "Natural Herbal Supplement", r"natural herbal (health |wellness )?supplement|natural alternatives|natural wellness formula"),
        ("other_claims", "Natural Defense", r"natural defense"),
    ]

    for category, claim, pattern in rules:
        bag.add_from_pattern(primary_sources, category, claim, pattern, title_feature_specs)

    # A+ text is used only for explicit product/image-alt claims that are not usually present in specs.
    aplus_only = [
        ("health_benefit_claims", "Seasonal Immune Support", r"best for seasonal immune support"),
        ("structure_function_statements_claims", "Supports Seasonal Immune Health", r"best for seasonal immune support"),
        ("certification_claims", "Vegan", r"vegan oregano oil capsules|vegan .*oil of oregano|oil of oregano.*vegan"),
        ("health_benefit_claims", "Microbial Balance Support", r"clear unwanted microbes"),
        ("structure_function_statements_claims", "Supports Microbial Balance", r"clear unwanted microbes"),
    ]
    for category, claim, pattern in aplus_only:
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
                writer.writerow(
                    {"category": category, "global_claim_order": idx, "claim": claim}
                )

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
