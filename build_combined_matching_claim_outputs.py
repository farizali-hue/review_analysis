import csv
import json
import re
from pathlib import Path


BASE = Path(r"D:\analysis")
SECTIONS_PATH = BASE / "combined_matching_sections.json"
BROWSER_PATH = BASE / "combined_matching_browser_sections.json"

ROW_OUTPUT = BASE / "combined_matching_claims_formalized_with_evidence.csv"
CLAIM_OUTPUT = BASE / "combined_matching_claims_claim_level_evidence.csv"
ORDER_OUTPUT = BASE / "combined_matching_claim_order.csv"

CATEGORIES = [
    "health_benefit_claims",
    "certification_claims",
    "nutritional_claims",
    "structure_function_statements_claims",
    "other_claims",
]

INPUT_EVIDENCE_FIELDS = {
    "health_benefit_claims": ("health_benefit_claims_source", "health_benefit_claims_evidence"),
    "certification_claims": ("certification_claims_source", "certification_claims_evidence"),
    "nutritional_claims": ("nutritional_claims_source", "nutritional_claims_evidence"),
    "structure_function_statements_claims": (
        "structure_function_statements_claims_source",
        "structure_function_statements_claims_evidence",
    ),
    "other_claims": ("other_claims_source", "other_claims_evidence"),
}

KNOWN_SPEC_LABELS = {
    "Brand",
    "Brand Name",
    "Primary Supplement Type",
    "Diet Type",
    "Product Benefits",
    "Flavor",
    "Special Ingredients",
    "Material Features",
    "Item Form",
    "Specialty",
    "Recommended Uses For Product",
    "Allergen Information",
    "Net Content Volume",
    "Liquid Volume",
    "Unit Count",
    "Total Servings Per Container",
    "Size",
    "Supplement Formulation",
    "Item Nype Name",
    "Dosage Form",
    "Special Features",
    "Set Name",
    "Plant or Animal Product Type",
    "Cuisine",
    "Age Range Description",
    "Age Range (Description)",
    "Container Type",
    "Model Name",
    "UPC",
    "Manufacturer",
    "Manufacturer Part Number",
    "Model Number",
    "Global Trade Identification Number",
    "Item Weight",
    "Item Dimensions",
    "Item dimensions L x W x H",
    "Number of Items",
    "Item Package Quantity",
    "Item Volume",
    "Item Package Weight",
    "Number of Pieces",
    "Materials & Care",
    "Material Type Free",
    "User guide",
    "Color",
    "Additional details",
    "Specific Uses For Product",
    "Dose Release Method",
    "Melting Temperature (degrees Celsius)",
}

SPEC_STOP_PREFIXES = (
    "about this item",
    "feedback",
    "share:",
    "found a lower price",
    "report an issue",
    "sponsored",
    "best sellers rank",
    "asin",
    "customer reviews",
    "manufacturer",
    "upc",
    "global trade identification number",
    "model number",
    "part number",
    "date first available",
    "features & specs",
    "materials & care",
    "additional details",
    "customers who viewed",
)


def clean_text(value: str) -> str:
    value = value or ""
    value = value.replace("\u200e", " ").replace("\u200f", " ")
    value = value.replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def split_lines(value: str):
    for line in (value or "").splitlines():
        text = clean_text(line)
        if text:
            yield text


def compact_source_text(value):
    if isinstance(value, list):
        return "\n".join(str(v) for v in value if str(v).strip())
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value or "")


def extract_spec_pairs(context: str):
    lines = list(split_lines(context))
    pairs = []
    for idx, line in enumerate(lines):
        if line not in KNOWN_SPEC_LABELS:
            continue
        values = []
        j = idx + 1
        while j < len(lines):
            next_line = lines[j]
            lower = next_line.lower()
            if next_line in KNOWN_SPEC_LABELS:
                break
            if lower.startswith(SPEC_STOP_PREFIXES):
                break
            values.append(next_line)
            j += 1
        value = clean_text("; ".join(values[:4]))
        if value:
            pairs.append((line, value))
    deduped = []
    seen = set()
    for pair in pairs:
        key = tuple(clean_text(x).lower() for x in pair)
        if key not in seen:
            seen.add(key)
            deduped.append(pair)
    return deduped


def add_chunk(chunks, origin, source, text, category=None, evidence=None, url=None):
    text = clean_text(text)
    if not text:
        return
    chunks.append(
        {
            "origin": origin,
            "source": source,
            "text": text,
            "category": category,
            "input_evidence": clean_text(evidence or ""),
            "url": clean_text(url or ""),
        }
    )


def make_chunks(record):
    chunks = []
    sections = record.get("sections", {})
    input_row = record.get("input", {})
    url = record.get("url") or input_row.get("url") or ""

    spec_context = "\n".join(
        [
            compact_source_text(sections.get("product_specifications_context")),
            compact_source_text(sections.get("see_all_product_specifications_context")),
        ]
    )
    for label, value in extract_spec_pairs(spec_context):
        add_chunk(chunks, "page", "Product specifications", f"{label}: {value}", url=url)

    for title in sections.get("product_title", []) or []:
        add_chunk(chunks, "page", "Product title", title, url=url)
    if input_row.get("title"):
        add_chunk(chunks, "page", "Workbook title", input_row.get("title"), url=url)

    for bullet_block in sections.get("feature_bullets", []) or []:
        for line in split_lines(bullet_block):
            if line.lower() in {"about this item", "see more product details", "show more", "\u203a"}:
                continue
            add_chunk(chunks, "page", "Feature bullets", line, url=url)

    important = compact_source_text(sections.get("important_information"))
    if important:
        # Keep compact ingredient/direction lines first so nutritional claims cite short snippets.
        for line in split_lines(important):
            lower_line = line.lower()
            if lower_line in {"important information", "safety information", "directions", "legal disclaimer"}:
                continue
            if lower_line.startswith(
                (
                    "caution:",
                    "statements regarding dietary supplements",
                    "*these statements",
                    "* these statements",
                    "this product is labelled",
                    "if you are pregnant",
                    "consult with",
                    "consult your",
                    "keep out of reach",
                    "do not use if",
                    "not recommended for use",
                    "safety sealed",
                    "avoid excessive heat",
                    "excessive use may",
                )
            ):
                continue
            add_chunk(chunks, "page", "Important information", line, url=url)

    for category in CATEGORIES:
        claims_text = input_row.get(category, "")
        if not clean_text(claims_text):
            continue
        src_field, ev_field = INPUT_EVIDENCE_FIELDS[category]
        evidence = input_row.get(ev_field, "")
        src = input_row.get(src_field, "")
        add_chunk(
            chunks,
            "input_image",
            f"Input image extraction: {category}",
            claims_text,
            category=category,
            evidence=evidence,
            url=src,
        )
    return chunks


def claim(category, label, patterns):
    return {"category": category, "label": label, "patterns": [re.compile(p, re.I) for p in patterns]}


CLAIMS = [
    # Health/benefit claims
    claim(
        "health_benefit_claims",
        "Energy Support",
        [
            r"\benergy support\b",
            r"\benergy management\b",
            r"\benergy boost(?:ing)?\b",
            r"\bfast fuel\b",
            r"\bsource of energy\b",
            r"\bconverted into energy\b",
            r"\bprovide(?:s|d| you with)?(?: valuable)? .*energy\b",
            r"\bbody fuel\b",
        ],
    ),
    claim(
        "health_benefit_claims",
        "Quick & Lasting Energy",
        [
            r"\bquick\s*&\s*lasting energy\b",
            r"\bquick(?:ly)? and long-lasting energy\b",
            r"\bquick.*lasting energy\b",
        ],
    ),
    claim(
        "health_benefit_claims",
        "Long-Lasting/Sustained Energy",
        [
            r"\blong[- ]lasting energy\b",
            r"\bsustained energy\b",
            r"\blightweight energy\b",
            r"\bnatural energy\b",
        ],
    ),
    claim(
        "health_benefit_claims",
        "Mental Clarity / Focus",
        [r"\bmental clarity\b", r"\bmental energy\b", r"\bfocus\b", r"\bbrain performance\b"],
    ),
    claim(
        "health_benefit_claims",
        "Brain Health / Brain Function Support",
        [
            r"\bbrain health support\b",
            r"\bsupports? brain function\b",
            r"\bsupports? .*brain health\b",
            r"\bbrain-boosting energy\b",
            r"\benergy source for the brain\b",
            r"\bfuel for (?:the )?brain\b",
            r"\bfast fuel for .*brain\b",
        ],
    ),
    claim(
        "health_benefit_claims",
        "Brain & Body Fuel",
        [r"\bbrain\s*&\s*body fuel\b", r"\bbrain and body fuel\b", r"\bbody and brain\b"],
    ),
    claim(
        "health_benefit_claims",
        "Metabolism Support",
        [
            r"\bmetabolism support\b",
            r"\bsupports? metabolism\b",
            r"\bmetabolism management\b",
            r"\bmetabolic\b",
        ],
    ),
    claim(
        "health_benefit_claims",
        "Fat-Burning Support",
        [r"\bfat[- ]burning\b", r"\bburn body fat\b", r"\buses fat as its main fuel source\b"],
    ),
    claim(
        "health_benefit_claims",
        "Ketosis Support",
        [r"\bstate of ketosis\b", r"\bwhile in ketosis\b", r"\bketones?\b", r"\bketogenic\b"],
    ),
    claim(
        "health_benefit_claims",
        "Keto Lifestyle Support",
        [r"\bsupport(?:s)? a keto\b", r"\bketo lifestyle\b", r"\bketo routines?\b"],
    ),
    claim(
        "health_benefit_claims",
        "Weight Management Support",
        [r"\bweight loss support\b", r"\bsupport weight loss\b", r"\bweight management\b"],
    ),
    claim(
        "health_benefit_claims",
        "Digestive Health / Easy Digestion",
        [r"\bdigestive health support\b", r"\bsupports digestion\b", r"\beasy digestion\b", r"\beasy to digest\b"],
    ),
    claim(
        "health_benefit_claims",
        "Blood Pressure Management",
        [r"\bblood pressure management\b"],
    ),
    claim(
        "health_benefit_claims",
        "Inflammation Management",
        [r"\binflammation management\b"],
    ),
    claim(
        "health_benefit_claims",
        "Stamina Support",
        [r"\bstamina\b"],
    ),
    claim(
        "health_benefit_claims",
        "Active Lifestyle / Workout Support",
        [r"\bworkouts?\b", r"\bactive lifestyle\b", r"\bproductivity\b"],
    ),
    # Certification claims
    claim("certification_claims", "USDA Organic", [r"\bUSDA Organic\b"]),
    claim("certification_claims", "Certified Organic by QAI", [r"\bCertified Organic by QAI\b"]),
    claim("certification_claims", "Certified Organic", [r"\bCertifiedOrganic\b", r"\bCertified Organic\b(?! by QAI)"]),
    claim("certification_claims", "Organic", [r"\borganic\b"]),
    claim(
        "certification_claims",
        "Non-GMO Project Verified",
        [r"\bNon[- ]GMO Project Verified\b", r"\bNON GMO Project VERIFIED\b"],
    ),
    claim(
        "certification_claims",
        "Non-GMO / GMO Free",
        [r"\bGMO Free\b", r"\bNon[- ]GMO\b(?! Project)", r"\bnon[- ]gmo\b(?! project)"],
    ),
    claim("certification_claims", "Keto / Keto Friendly", [r"\bketo friendly\b", r"\bketo diet-friendly\b", r"\bdiet type:.*\bketo\b", r"\bcertified keto\b", r"\bketo certified\b"]),
    claim("certification_claims", "Paleo / Certified Paleo", [r"\bCertified Paleo\b", r"\bPaleo Certified\b", r"\bpaleo\b"]),
    claim("certification_claims", "Vegan / Certified Vegan", [r"\bCertified Vegan\b", r"\bVegan Certified\b", r"\bdiet type:.*\bvegan\b", r"\bvegan\b"]),
    claim("certification_claims", "Vegetarian", [r"\bvegetarian\b"]),
    claim("certification_claims", "Gluten Free", [r"\bgluten[- ]free\b", r"\bGlutenFree\b"]),
    claim("certification_claims", "Dairy Free", [r"\bdairy[- ]free\b", r"\bDairy Free\b"]),
    claim("certification_claims", "Soy Free", [r"\bsoy[- ]free\b", r"\bSoy Free\b"]),
    claim("certification_claims", "Kosher", [r"\bkosher\b"]),
    claim("certification_claims", "Halal", [r"\bhalal\b"]),
    claim("certification_claims", "Informed Choice Certified / Quality Tested", [r"\bInformed Choice\b"]),
    claim("certification_claims", "Third-Party Tested", [r"\bthird[- ]party tested\b", r"\b3rd party\b"]),
    claim("certification_claims", "cGMP-Compliant Facility", [r"\bcGMP[- ]compliant facility\b", r"\bcGMP Compliant\b"]),
    claim("certification_claims", "Lab Tested for Quality/Purity", [r"\blab tested\b", r"\btested for quality and purity\b"]),
    claim("certification_claims", "Heavy Metals Tested", [r"\bheavy metals?\b"]),
    claim("certification_claims", "Mold Tested", [r"\bmold\b"]),
    claim("certification_claims", "BPA Free", [r"\bBPAFree\b", r"\bBPA Free\b"]),
    # Nutritional claims
    claim("nutritional_claims", "MCT Oil", [r"\bMCT Oil\b"]),
    claim("nutritional_claims", "Coconut MCT Oil", [r"\bCoconut MCT Oil\b", r"\bmct coconut oil\b"]),
    claim(
        "nutritional_claims",
        "Medium Chain Triglycerides (MCTs)",
        [r"\bMedium[- ]Chain Triglycerides\b", r"\bMedium Chain Triglycerides\b", r"\bMCTs\b"],
    ),
    claim("nutritional_claims", "Organic Coconut MCT Oil", [r"\bOrganic Coconut MCT Oil\b"]),
    claim("nutritional_claims", "100% Organic Coconut MCT Oil", [r"\b100% Organic Coconut MCT Oil\b"]),
    claim("nutritional_claims", "100% Coconut Oil", [r"\b100% (?:Pure )?Coconut Oil\b", r"\b100% coconut\b"]),
    claim("nutritional_claims", "100% Organic Coconut Oil", [r"\b100% organic coconut oil\b"]),
    claim("nutritional_claims", "100% Virgin Coconut Oil", [r"\b100% Virgin Coconut Oil\b", r"\bvirgin coconut oil\b"]),
    claim("nutritional_claims", "100% Cold Pressed Virgin Coconut Oil", [r"\b100% cold pressed virgin coconut oil\b"]),
    claim("nutritional_claims", "Caprylic Acid (C8)", [r"\bCaprylic Acid\b", r"\bC8\b"]),
    claim("nutritional_claims", "Capric Acid (C10)", [r"\bCapric Acid\b", r"\bC10\b"]),
    claim("nutritional_claims", "Lauric Acid (C12)", [r"\bLauric Acid\b", r"\bC12\b"]),
    claim("nutritional_claims", "C8 + C10", [r"\bC8\s*\+\s*C10\b", r"\bC8 and C10\b", r"\bC8 & C10\b"]),
    claim("nutritional_claims", "C8 + C10 + C12", [r"\bC8\s*,?\s*C10\s*,?\s*(?:and|\+|&)?\s*C12\b", r"\bC8\s*\+\s*C10\s*\+\s*C12\b"]),
    claim("nutritional_claims", "Pure C8", [r"\bPure C8\b", r"\bC8 \(Caprylic Acid\)\b"]),
    claim("nutritional_claims", "14g MCTs per Serving", [r"\b14\s*g\b.*\bMCT\b", r"\bMCTs? with 14 g per serving\b"]),
    claim("nutritional_claims", "13g MCTs per Serving", [r"\b13\s*g\b.*\bMCT\b"]),
    claim("nutritional_claims", "0g Sugar", [r"\b0g sugar\b", r"\b0 g sugar\b"]),
    claim("nutritional_claims", "0g Carbs", [r"\b0g carbs?\b", r"\b0 g carbs?\b"]),
    claim("nutritional_claims", "0g Trans Fat", [r"\b0g trans fat\b", r"\b0 g trans fat\b"]),
    claim("nutritional_claims", "125 Calories", [r"\b125 cal(?:ories)?\b"]),
    claim("nutritional_claims", "Dietary Supplement", [r"\bdietary supplement\b"]),
    claim("nutritional_claims", "Organic", [r"\borganic\b"]),
    claim("nutritional_claims", "Keto / Keto Friendly", [r"\bketo\b"]),
    claim("nutritional_claims", "Paleo", [r"\bpaleo\b"]),
    claim("nutritional_claims", "Vegan", [r"\bvegan\b"]),
    claim("nutritional_claims", "Vegetarian", [r"\bvegetarian\b"]),
    claim("nutritional_claims", "Gluten Free", [r"\bgluten[- ]free\b", r"\bGlutenFree\b"]),
    claim("nutritional_claims", "Dairy Free", [r"\bdairy[- ]free\b"]),
    claim("nutritional_claims", "Non-GMO / GMO Free", [r"\bNon[- ]GMO\b", r"\bGMO Free\b", r"\bGMOFree\b"]),
    claim("nutritional_claims", "Palm Oil Free / Never Palm Oil", [r"\bnever palm\b", r"\bno palm oil\b", r"\bpalm[- ]free\b"]),
    claim("nutritional_claims", "No Filler Oils", [r"\bno filler oils\b", r"\bfiller oils\b"]),
    claim("nutritional_claims", "No Additives or Fillers", [r"\bno additives? or fillers?\b", r"\bfree of fillers? and additives?\b"]),
    claim("nutritional_claims", "No Artificial Colors", [r"\bno artificial colors\b", r"\bNo Artificial Colors\b"]),
    claim("nutritional_claims", "No Artificial Flavors", [r"\bno artificial flavors\b", r"\bNo Artificial Flavors\b"]),
    claim("nutritional_claims", "No Artificial Sweeteners", [r"\bno artificial sweeteners\b", r"\bNo Artificial Sweeteners\b"]),
    claim("nutritional_claims", "No Preservatives", [r"\bno preservatives\b", r"\bNo Artificial Preservatives\b"]),
    claim("nutritional_claims", "Non-Hydrogenated", [r"\bnon[- ]hydrogenated\b"]),
    claim("nutritional_claims", "Hexane-Free", [r"\bhexane[- ]free\b"]),
    claim("nutritional_claims", "Unflavored", [r"\bunflavored\b"]),
    claim("nutritional_claims", "Flavorless/Odorless", [r"\bflavorless\b", r"\bodorless\b", r"\bscentless\b", r"\btasteless\b"]),
    claim("nutritional_claims", "32 fl oz", [r"\b32(?:\.0+)?\s*(?:Fluid Ounces|fl oz)\b"]),
    claim("nutritional_claims", "30 fl oz", [r"\b30(?:\.0+)?\s*(?:Fluid Ounces|fl oz)\b"]),
    claim("nutritional_claims", "16 fl oz", [r"\b16(?:\.0+)?\s*(?:Fluid Ounces|fl oz)\b"]),
    claim("nutritional_claims", "16.9 fl oz", [r"\b16\.9\s*(?:Fluid Ounces|fl oz)\b"]),
    # Structure/function statements
    claim("structure_function_statements_claims", "Energy Support", [r"\benergy support\b", r"\benergy management\b", r"\bfast fuel\b", r"\bsource of energy\b", r"\bconverted into energy\b"]),
    claim("structure_function_statements_claims", "Quick & Lasting Energy", [r"\bquick\s*&\s*lasting energy\b", r"\bquick.*lasting energy\b"]),
    claim("structure_function_statements_claims", "Long-Lasting/Sustained Energy", [r"\blong[- ]lasting energy\b", r"\bsustained energy\b", r"\bnatural energy\b"]),
    claim("structure_function_statements_claims", "Mental Clarity / Focus", [r"\bmental clarity\b", r"\bmental energy\b", r"\bfocus\b", r"\bbrain performance\b"]),
    claim("structure_function_statements_claims", "Brain Health / Brain Function Support", [r"\bbrain health support\b", r"\bsupports? brain function\b", r"\bbrain-boosting energy\b", r"\benergy source for the brain\b", r"\bfuel for (?:the )?brain\b"]),
    claim("structure_function_statements_claims", "Brain & Body Fuel", [r"\bbrain\s*&\s*body fuel\b", r"\bbrain and body fuel\b", r"\bbody and brain\b"]),
    claim("structure_function_statements_claims", "Metabolism Support", [r"\bmetabolism support\b", r"\bsupports? metabolism\b", r"\bmetabolism management\b"]),
    claim("structure_function_statements_claims", "Fat-Burning Support", [r"\bfat[- ]burning\b", r"\bburn body fat\b"]),
    claim("structure_function_statements_claims", "Ketosis Support", [r"\bstate of ketosis\b", r"\bwhile in ketosis\b", r"\bketones?\b"]),
    claim("structure_function_statements_claims", "Keto Lifestyle Support", [r"\bsupport(?:s)? a keto\b", r"\bketo lifestyle\b"]),
    claim("structure_function_statements_claims", "Weight Management Support", [r"\bweight loss support\b", r"\bsupport weight loss\b"]),
    claim("structure_function_statements_claims", "Digestive Health / Easy Digestion", [r"\bdigestive health support\b", r"\bsupports digestion\b", r"\beasy digestion\b", r"\beasy to digest\b"]),
    claim("structure_function_statements_claims", "Blood Pressure Management", [r"\bblood pressure management\b"]),
    claim("structure_function_statements_claims", "Inflammation Management", [r"\binflammation management\b"]),
    claim("structure_function_statements_claims", "Stamina Support", [r"\bstamina\b"]),
    claim("structure_function_statements_claims", "Active Lifestyle / Workout Support", [r"\bworkouts?\b", r"\bactive lifestyle\b", r"\bproductivity\b"]),
    # Other claims
    claim("other_claims", "Flavorless/Unflavored", [r"\bflavorless\b", r"\bunflavored\b", r"\btasteless\b"]),
    claim("other_claims", "Odorless/Scentless", [r"\bodorless\b", r"\bscentless\b"]),
    claim("other_claims", "Mild Taste / Subtle Odor", [r"\bmild taste\b", r"\bmild flavor\b", r"\bsubtle odor\b"]),
    claim("other_claims", "Versatile Use", [r"\bversatile\b", r"\beveryday routine\b", r"\balternative to traditional oils\b"]),
    claim("other_claims", "Coffee/Smoothies/Shakes Use", [r"\bcoffee\b", r"\bsmoothies?\b", r"\bshakes?\b", r"\btea\b"]),
    claim("other_claims", "Low/No-Heat Recipes", [r"\bnon heat recipes\b", r"\bno[- ]heat recipes\b", r"\bNot intended for cooking\b"]),
    claim("other_claims", "No Refrigeration Required", [r"\brefrigeration (?:is )?not required\b", r"\bNo refrigeration required\b"]),
    claim("other_claims", "Glass Bottle", [r"\bglass bottle\b"]),
    claim("other_claims", "Non-Toxic Glass Bottle", [r"\bnon[- ]toxic .*glass\b"]),
    claim("other_claims", "Eco-Friendly Packaging", [r"\beco[- ]friendly packaging\b", r"\benvironment\b"]),
    claim("other_claims", "Plastic-Free/Biodegradable Packaging", [r"\bplastic[- ]free\b", r"\bbiodegradable\b"]),
    claim("other_claims", "Plant-Based Inks", [r"\bplant[- ]based inks\b"]),
    claim("other_claims", "Recyclable Aluminum Cap", [r"\brecyclable aluminum cap\b"]),
    claim("other_claims", "Sustainably Sourced", [r"\bsustainably[- ]sourced\b", r"\bsustainably grown\b"]),
    claim("other_claims", "No Palm Oil / Never Palm Oil", [r"\bnever palm\b", r"\bno palm oil\b", r"\bpalm[- ]free\b"]),
    claim("other_claims", "No Additives or Fillers", [r"\bno additives? or fillers?\b", r"\bfree of fillers? and additives?\b", r"\bwithout palm or filler oils\b"]),
    claim("other_claims", "No Artificial Colors/Flavors/Preservatives", [r"\bno artificial colors\b", r"\bno artificial flavors\b", r"\bno artificial .*preservatives\b", r"\bno preservatives\b"]),
    claim("other_claims", "Hexane-Free", [r"\bhexane[- ]free\b"]),
    claim("other_claims", "Steam Distilled Without Chemicals", [r"\bsteam distilled without chemicals\b", r"\bsteam[- ]distilled\b"]),
    claim("other_claims", "Triple-Steam/Triple-Distilled", [r"\btriple[- ]steam distillation\b", r"\btriple[- ]distilled\b"]),
    claim("other_claims", "Hydrolyzed", [r"\bhydrolyzed\b"]),
    claim("other_claims", "Lab Tested for Quality/Purity", [r"\blab tested\b", r"\btested for quality and purity\b"]),
    claim("other_claims", "Third-Party Tested", [r"\bthird[- ]party tested\b", r"\b3rd party\b"]),
    claim("other_claims", "cGMP Facility", [r"\bcGMP[- ]compliant facility\b", r"\bcGMP facility\b"]),
    claim("other_claims", "Heavy Metals Tested", [r"\bheavy metals?\b"]),
    claim("other_claims", "Mold Tested", [r"\bmold\b"]),
    claim("other_claims", "Family-Owned", [r"\bfamily[- ]owned\b"]),
    claim("other_claims", "Research-Backed", [r"\bresearch[- ]backed\b"]),
    claim("other_claims", "One Ingredient", [r"\b1 ingredient\b", r"\bone ingredient\b", r"\bone clean ingredient\b"]),
    claim("other_claims", "Remains Liquid", [r"\bremains liquid\b"]),
    claim("other_claims", "Blends Easily / Seamlessly", [r"\bblends seamlessly\b", r"\bmix into\b", r"\bmixing it into\b"]),
    claim("other_claims", "Leak-Proof / Mess-Free", [r"\bleak[- ]proof\b", r"\bmess free\b", r"\bmess[- ]free\b"]),
]

ORDERED_BY_CATEGORY = {category: [] for category in CATEGORIES}
for item in CLAIMS:
    ORDERED_BY_CATEGORY[item["category"]].append(item)


def find_match(item, chunks):
    page_match = None
    input_match = None
    for chunk in chunks:
        for pattern in item["patterns"]:
            match = pattern.search(chunk["text"])
            if not match:
                continue
            found = (chunk, match, pattern)
            if chunk["origin"] == "page":
                if page_match is None:
                    page_match = found
                if chunk["source"] == "Product specifications":
                    return found
            elif input_match is None:
                input_match = found
    return page_match or input_match


def snippet_for(chunk, match):
    if chunk["origin"] == "input_image" and chunk.get("input_evidence"):
        evidence = chunk["input_evidence"]
    else:
        evidence = chunk["text"]

    evidence = clean_text(evidence)
    if len(evidence) <= 360:
        snippet = evidence
    else:
        start = max(match.start() - 130, 0)
        end = min(match.end() + 230, len(chunk["text"]))
        snippet = clean_text(chunk["text"][start:end])
        if start > 0:
            snippet = "..." + snippet
        if end < len(chunk["text"]):
            snippet = snippet + "..."

    if chunk["origin"] == "input_image":
        source = chunk["source"]
        if chunk.get("url"):
            source = f"{source} ({chunk['url']})"
    else:
        source = chunk["source"]
    return source, snippet


def ordered_claims_for_record(record):
    chunks = make_chunks(record)
    results = {category: [] for category in CATEGORIES}
    for category, items in ORDERED_BY_CATEGORY.items():
        for item in items:
            found = find_match(item, chunks)
            if not found:
                continue
            chunk, match, _pattern = found
            source, evidence = snippet_for(chunk, match)
            results[category].append(
                {
                    "claim": item["label"],
                    "evidence_source": source,
                    "evidence": evidence,
                    "origin": chunk["origin"],
                }
            )
    return results


def make_notes(record, browser_by_asin):
    asin = record["asin"]
    sections = record.get("sections", {})
    has_spec_context = bool(clean_text(sections.get("product_specifications_context") or "")) or bool(
        clean_text(sections.get("see_all_product_specifications_context") or "")
    )
    browser = browser_by_asin.get(asin, {})
    note_parts = ["Browser visit succeeded" if not browser.get("error") else f"Browser visit error: {browser.get('error')}"]
    if has_spec_context:
        note_parts.append(
            "Product specifications section was parsed from page HTML and used where relevant"
        )
    else:
        note_parts.append(
            "No product specifications section was exposed in the saved page HTML/Browser capture; extraction used title, feature bullets, important information, and input image evidence"
        )
    note_parts.append("Recommendations/reviews were not counted as claims")
    return "; ".join(note_parts)


def join_claims(items):
    return " | ".join(item["claim"] for item in items)


def join_evidence(items):
    return " | ".join(
        f"{item['claim']} -> {item['evidence_source']}: {item['evidence']}" for item in items
    )


def main():
    records = json.loads(SECTIONS_PATH.read_text(encoding="utf-8"))
    if BROWSER_PATH.exists():
        browser_records = json.loads(BROWSER_PATH.read_text(encoding="utf-8"))
        browser_by_asin = {r.get("asin"): r for r in browser_records}
    else:
        browser_by_asin = {}

    row_fields = ["asin", "url", "title"]
    for category in CATEGORIES:
        row_fields.extend([category, f"{category}_evidence"])
    row_fields.append("missed_or_unclear_notes")

    claim_fields = [
        "asin",
        "url",
        "title",
        "category",
        "claim_order",
        "claim",
        "evidence_source",
        "evidence",
        "evidence_origin",
    ]

    row_output = []
    claim_output = []
    for record in records:
        input_row = record.get("input", {})
        title = clean_text(input_row.get("title") or " | ".join(record.get("sections", {}).get("product_title", [])))
        url = input_row.get("url") or record.get("url") or ""
        results = ordered_claims_for_record(record)

        out = {"asin": record["asin"], "url": url, "title": title}
        for category in CATEGORIES:
            out[category] = join_claims(results[category])
            out[f"{category}_evidence"] = join_evidence(results[category])
            for idx, item in enumerate(results[category], start=1):
                claim_output.append(
                    {
                        "asin": record["asin"],
                        "url": url,
                        "title": title,
                        "category": category,
                        "claim_order": idx,
                        "claim": item["claim"],
                        "evidence_source": item["evidence_source"],
                        "evidence": item["evidence"],
                        "evidence_origin": item["origin"],
                    }
                )
        out["missed_or_unclear_notes"] = make_notes(record, browser_by_asin)
        row_output.append(out)

    with ROW_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row_fields)
        writer.writeheader()
        writer.writerows(row_output)

    with CLAIM_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=claim_fields)
        writer.writeheader()
        writer.writerows(claim_output)

    with ORDER_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "claim_order", "canonical_claim"])
        writer.writeheader()
        for category in CATEGORIES:
            for idx, item in enumerate(ORDERED_BY_CATEGORY[category], start=1):
                writer.writerow(
                    {
                        "category": category,
                        "claim_order": idx,
                        "canonical_claim": item["label"],
                    }
                )

    print(f"rows={len(row_output)}")
    print(f"claim_rows={len(claim_output)}")
    print(ROW_OUTPUT)
    print(CLAIM_OUTPUT)
    print(ORDER_OUTPUT)


if __name__ == "__main__":
    main()
