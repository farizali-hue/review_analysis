import csv
import json
import re
from pathlib import Path


BASE = Path(r"D:\analysis")
BROWSER_SECTIONS = BASE / "mushroom_coffee_browser_sections.json"

ROW_OUTPUT = BASE / "claims_mushroomcoffee_formalized_with_evidence.csv"
CLAIM_OUTPUT = BASE / "claims_mushroomcoffee_claim_level_evidence.csv"
ORDER_OUTPUT = BASE / "claims_mushroomcoffee_claim_order.csv"

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


def clean_text(value):
    value = str(value or "")
    value = value.replace("\u200e", " ").replace("\u200f", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def strip_noise(value):
    text = clean_text(value)
    text = re.sub(r"\.po-break-word.*?logTechTermAssistEvent\(nexusSchemaId\).*?\}", "", text)
    text = re.sub(r"function logTechTermAssistMetric.*?Brand ", "Brand ", text)
    if "logTechTermAssist" in text and "Brand " in text:
        text = text[text.find("Brand ") :]
    if text.startswith("); } Brand "):
        text = text[text.find("Brand ") :]
    text = re.sub(r"Legal Disclaimer .*", "", text, flags=re.I)
    text = re.sub(r"Statements regarding dietary supplements .*", "", text, flags=re.I)
    for marker in [
        "Customer Reviews",
        "Customers who viewed",
        "Compare with similar items",
        "Add to Cart",
        "Price",
    ]:
        idx = text.lower().find(marker.lower())
        if idx >= 0:
            text = text[:idx]
    text = text.replace("About this item ", "").replace(" Show more", "")
    return clean_text(text)


def add_chunk(chunks, origin, source, text, category=None, evidence=None, url=None):
    text = strip_noise(text)
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
    page_url = record.get("navigatedUrl") or record.get("url") or input_row.get("url") or ""

    add_chunk(chunks, "page", "Product title", sections.get("title") or input_row.get("title"), url=page_url)
    add_chunk(chunks, "page", "Workbook title", input_row.get("title"), url=input_row.get("url"))

    for text in sections.get("productOverview") or []:
        add_chunk(chunks, "page", "Top highlights / product overview", text, url=page_url)
    for text in sections.get("featureBullets") or []:
        add_chunk(chunks, "page", "Feature bullets", text, url=page_url)
    for text in sections.get("importantInformation") or []:
        add_chunk(chunks, "page", "Important information / ingredients", text, url=page_url)
    for text in sections.get("aplus") or []:
        add_chunk(chunks, "page", "A+ product content", text, url=page_url)

    for category in CATEGORIES:
        claim_text = input_row.get(category, "")
        if not clean_text(claim_text):
            continue
        src_field, ev_field = INPUT_EVIDENCE_FIELDS[category]
        add_chunk(
            chunks,
            "input_image",
            f"Input image extraction: {category}",
            claim_text,
            category=category,
            evidence=input_row.get(ev_field, ""),
            url=input_row.get(src_field, ""),
        )
    return chunks


def claim(category, label, patterns):
    return {"category": category, "label": label, "patterns": [re.compile(p, re.I) for p in patterns]}


CLAIMS = [
    # Health / benefit claims
    claim("health_benefit_claims", "Energy Support", [r"\bEnergy Support\b", r"\bBoosts? Energy\b", r"\bImproved Energy\b", r"\bEnergy Management\b", r"\bEnergy Booster\b", r"\benergy kick\b", r"\benergy and focus\b"]),
    claim("health_benefit_claims", "All-Day Energy", [r"\bAll[- ]?day Energy\b"]),
    claim("health_benefit_claims", "Jitter-Free / No Crash Energy", [r"\bNo Jitters\b", r"\bNo Crash\b", r"\bjitter[- ]free\b", r"\bnone of the jitters\b", r"\bwithout jitters or crash\b"]),
    claim("health_benefit_claims", "Focus / Mental Clarity", [r"\bFocus\b", r"\bMental Clarity\b", r"\bLaser Focus\b", r"\bClarity & Focus\b", r"\bFocus Enhancer\b", r"\bFocus & Alertness\b"]),
    claim("health_benefit_claims", "Cognitive / Brain Health Support", [r"\bCognitive\b", r"\bBrain Health\b", r"\bbrain supplement\b", r"\bsupport cognitive function\b", r"\bBrain & Immune Support\b"]),
    claim("health_benefit_claims", "Memory Support", [r"\bMemory\b"]),
    claim("health_benefit_claims", "Mood Support / Stress Relief", [r"\bMood\b", r"\bStress Relief\b", r"\bReduces Stress\b", r"\bRelax(?:es|ation)\b", r"\bcalmness\b", r"\bawareness\b"]),
    claim("health_benefit_claims", "Gut Health / Digestive Support", [r"\bGut Health\b", r"\bGut Friendly\b", r"\bDigest(?:ion|ive)\b", r"\bMaintains? Gut Health\b", r"\bDigestive Health\b", r"\bprebiotic\b", r"\bprobiotic\b"]),
    claim("health_benefit_claims", "Immune Support / Immune Defense", [r"\bImmune Support\b", r"\bSupports? Immunity\b", r"\bEnhance Immunity\b", r"\bBoosted Immunity\b", r"\bImmune Defense\b", r"\bImmune Health\b"]),
    claim("health_benefit_claims", "Antioxidant Support", [r"\bAntioxidant\b", r"\bfree radicals\b"]),
    claim("health_benefit_claims", "Longevity Support", [r"\bLongevity\b"]),
    claim("health_benefit_claims", "Sleep Support", [r"\bSleep Support\b", r"\bLess Caffeine for Sleep\b", r"\bBetter sleep\b"]),
    claim("health_benefit_claims", "Healthy Skin / Hair Support", [r"\bHealthy Skin\b", r"\bGlowing Skin\b", r"\bFull Hair\b", r"\bSkin\b"]),
    claim("health_benefit_claims", "Joint / Bone Support", [r"\bhealthy joints\b", r"\bstrong bones\b", r"\bJoint\b", r"\bBone\b"]),
    claim("health_benefit_claims", "Appetite Support", [r"\bAppetite\b"]),
    claim("health_benefit_claims", "Recovery Support", [r"\bRecovery\b"]),
    claim("health_benefit_claims", "Healthy Fats", [r"\bHealthy Fats\b", r"\bMCT oil\b"]),
    # Certifications, free-from, and quality claims
    claim("certification_claims", "USDA Organic", [r"\bUSDA Organic\b"]),
    claim("certification_claims", "Certified Organic / Organic", [r"\bCertified Organic\b", r"\bOrganic\b"]),
    claim("certification_claims", "Whole30 Approved", [r"\bWhole30 Approved\b"]),
    claim("certification_claims", "Paleo Friendly", [r"\bPaleo Friendly\b", r"\bPaleo\b"]),
    claim("certification_claims", "Keto Friendly", [r"\bKeto Friendly\b", r"\bKeto\b"]),
    claim("certification_claims", "Vegan / 100% Vegan", [r"\b100% Vegan\b", r"\bVegan Friendly\b", r"\bVegan\b"]),
    claim("certification_claims", "Vegetarian", [r"\bVegetarian\b"]),
    claim("certification_claims", "Gluten Free", [r"\bGluten[- ]Free\b", r"\bGluten Free\b"]),
    claim("certification_claims", "Dairy Free", [r"\bDairy[- ]Free\b", r"\bDairy Free\b"]),
    claim("certification_claims", "Soy Free", [r"\bSoy[- ]Free\b", r"\bSoy Free\b"]),
    claim("certification_claims", "Non-GMO / GMO Free", [r"\bNon[- ]GMO\b", r"\bNON GMO\b", r"\bGMO Free\b", r"\bGMO FREE\b"]),
    claim("certification_claims", "No Added Sugar / No Sugar / Sugar Free", [r"\bNo Added Sugar\b", r"\bNo Sugar\b", r"\bSugar Free\b", r"\b0 sugar\b"]),
    claim("certification_claims", "Glyphosate Residue Free", [r"\bGlyphosate Residue Free\b"]),
    claim("certification_claims", "Lab Tested", [r"\bLab Tested\b", r"\bLab-Tested\b"]),
    claim("certification_claims", "Third-Party Lab Tested", [r"\b3rd[- ]Party Lab Tested\b", r"\bThird[- ]Party Lab Tested\b", r"\bThird[- ]party tested\b"]),
    claim("certification_claims", "GMP / GMP Certified", [r"\bGMP Certified\b", r"\bcGMP\b", r"\bGMP\b"]),
    claim("certification_claims", "Fair Trade", [r"\bFair Trade\b"]),
    claim("certification_claims", "Made in USA / USA Grown", [r"\bMade in USA\b", r"\bUSA Grown\b", r"\bgrown locally\b"]),
    claim("certification_claims", "Natural Ingredients", [r"\bNatural Ingredients\b", r"\bnatural mushroom ingredients\b"]),
    # Nutritional claims
    claim("nutritional_claims", "Mushroom Coffee", [r"\bMushroom Coffee\b"]),
    claim("nutritional_claims", "Mushroom Powder / Supplement", [r"\bMushroom Powder\b", r"\bMushroom Powder Supplement\b", r"\bMushroom Extract Powder\b"]),
    claim("nutritional_claims", "Adaptogenic Mushrooms / Adaptogens", [r"\bAdaptogenic Mushrooms\b", r"\bAdaptogens\b", r"\badaptogenic mushroom\b"]),
    claim("nutritional_claims", "6 Mushroom Blend", [r"\b6 Adaptogenic Mushrooms\b", r"\bsix superfood mushrooms\b", r"\bSix Mushrooms\b", r"\b6 Mushrooms\b"]),
    claim("nutritional_claims", "7 Mushroom Blend / Sacred 7", [r"\b7[- ]in[- ]1\b", r"\bSacred 7\b", r"\b7 mushroom blend\b"]),
    claim("nutritional_claims", "10 Mushroom Blend", [r"\b10 Mushroom\b"]),
    claim("nutritional_claims", "16-in-1 Mushroom Blend", [r"\b16 in 1\b", r"\b16-in-1\b"]),
    claim("nutritional_claims", "Superfood Blend", [r"\bSuperfood Blend\b", r"\bsuperfood mushrooms\b", r"\bsuperfoods\b"]),
    claim("nutritional_claims", "Lion's Mane", [r"\bLion'?s Mane\b", r"\bLion Mane\b"]),
    claim("nutritional_claims", "Reishi", [r"\bReishi\b"]),
    claim("nutritional_claims", "Chaga", [r"\bChaga\b"]),
    claim("nutritional_claims", "Cordyceps", [r"\bCordyceps\b"]),
    claim("nutritional_claims", "Turkey Tail", [r"\bTurkey Tail\b"]),
    claim("nutritional_claims", "Shiitake", [r"\bShiitake\b"]),
    claim("nutritional_claims", "King Trumpet", [r"\bKing Trumpet\b"]),
    claim("nutritional_claims", "Maitake", [r"\bMaitake\b"]),
    claim("nutritional_claims", "Fruiting Bodies / Fruiting Body Extracts", [r"\b100% Fruiting Bod(?:y|ies)\b", r"\bfruiting bod(?:y|ies)\b", r"\bfruiting body extracts\b"]),
    claim("nutritional_claims", "Full Spectrum / Whole Mushrooms", [r"\bFull Spectrum\b", r"\bwhole mushrooms\b"]),
    claim("nutritional_claims", "Double-Extracted", [r"\bdouble[- ]extracted\b"]),
    claim("nutritional_claims", "Beta-Glucans", [r"\bBeta[- ]Glucans\b"]),
    claim("nutritional_claims", "Coffee / Instant Coffee", [r"\bInstant Coffee\b", r"\bArabica Coffee\b", r"\bCoffee Extract\b", r"\bInstant Mushroom Coffee\b"]),
    claim("nutritional_claims", "Low Caffeine", [r"\bLow[- ]Caffeine\b", r"\bLess Caffeine\b"]),
    claim("nutritional_claims", "Caffeine-Free", [r"\bCaffeine[- ]free\b"]),
    claim("nutritional_claims", "90mg Caffeine", [r"\b90mg Caffeine\b", r"\b90mg of caffeine\b"]),
    claim("nutritional_claims", "L-Theanine", [r"\bL[- ]Theanine\b"]),
    claim("nutritional_claims", "Collagen / Grass-Fed Collagen", [r"\bCollagen\b", r"\bGrass[- ]Fed Collagen\b"]),
    claim("nutritional_claims", "MCT Oil", [r"\bMCT oil\b"]),
    claim("nutritional_claims", "Coconut Milk", [r"\bCoconut Milk\b"]),
    claim("nutritional_claims", "Prebiotic Blend / Prebiotics", [r"\bPrebiotic Blend\b", r"\bprebiotics?\b"]),
    claim("nutritional_claims", "2000mg Mushroom Blend", [r"\b2000mg\b", r"\b2,000mg\b"]),
    claim("nutritional_claims", "1,730mg Mushroom Blend", [r"\b1,730mg\b", r"\b1730mg\b"]),
    claim("nutritional_claims", "No Added Sugar / No Sugar / Sugar Free", [r"\bNo Added Sugar\b", r"\bNo Sugar\b", r"\bSugar Free\b", r"\b0 sugar\b"]),
    claim("nutritional_claims", "No Oat Fillers", [r"\bNo Oat Fillers\b"]),
    claim("nutritional_claims", "No Fillers / No Grains / No Additives", [r"\bNo Fillers\b", r"\bZero Fillers\b", r"\bNo Grains\b", r"\bNo Additives\b", r"\bNo sneaky additives\b"]),
    claim("nutritional_claims", "Paleo Friendly", [r"\bPaleo Friendly\b", r"\bPaleo\b"]),
    claim("nutritional_claims", "Keto Friendly", [r"\bKeto Friendly\b", r"\bKeto\b"]),
    claim("nutritional_claims", "Vegan / 100% Vegan", [r"\b100% Vegan\b", r"\bVegan Friendly\b", r"\bVegan\b"]),
    claim("nutritional_claims", "Vegetarian", [r"\bVegetarian\b"]),
    claim("nutritional_claims", "Gluten Free", [r"\bGluten[- ]Free\b", r"\bGluten Free\b"]),
    claim("nutritional_claims", "Dairy Free", [r"\bDairy[- ]Free\b", r"\bDairy Free\b"]),
    claim("nutritional_claims", "Soy Free", [r"\bSoy[- ]Free\b", r"\bSoy Free\b"]),
    claim("nutritional_claims", "Non-GMO / GMO Free", [r"\bNon[- ]GMO\b", r"\bNON GMO\b", r"\bGMO Free\b", r"\bGMO FREE\b"]),
    claim("nutritional_claims", "Organic", [r"\bUSDA Organic\b", r"\bCertified Organic\b", r"\bOrganic\b"]),
    claim("nutritional_claims", "Fair Trade", [r"\bFair Trade\b"]),
    claim("nutritional_claims", "Made in USA / USA Grown", [r"\bMade in USA\b", r"\bUSA Grown\b", r"\bManufactured in Brooklyn\b", r"\bgrown locally\b"]),
    claim("nutritional_claims", "Glyphosate Residue Free", [r"\bGlyphosate Residue Free\b"]),
    claim("nutritional_claims", "Natural Ingredients", [r"\bNatural Ingredients\b", r"\bnatural mushroom ingredients\b"]),
    # Structure/function statements
    claim("structure_function_statements_claims", "Energy Support", [r"\bEnergy Support\b", r"\bBoosts? Energy\b", r"\bImproved Energy\b", r"\bEnergy Management\b", r"\bEnergy Booster\b", r"\benergy kick\b", r"\benergy and focus\b"]),
    claim("structure_function_statements_claims", "All-Day Energy", [r"\bAll[- ]?day Energy\b"]),
    claim("structure_function_statements_claims", "Jitter-Free / No Crash Energy", [r"\bNo Jitters\b", r"\bNo Crash\b", r"\bjitter[- ]free\b", r"\bnone of the jitters\b", r"\bwithout jitters or crash\b"]),
    claim("structure_function_statements_claims", "Focus / Mental Clarity", [r"\bFocus\b", r"\bMental Clarity\b", r"\bLaser Focus\b", r"\bClarity & Focus\b", r"\bFocus Enhancer\b", r"\bFocus & Alertness\b"]),
    claim("structure_function_statements_claims", "Cognitive / Brain Health Support", [r"\bCognitive\b", r"\bBrain Health\b", r"\bbrain supplement\b", r"\bsupport cognitive function\b", r"\bBrain & Immune Support\b"]),
    claim("structure_function_statements_claims", "Memory Support", [r"\bMemory\b"]),
    claim("structure_function_statements_claims", "Mood Support / Stress Relief", [r"\bMood\b", r"\bStress Relief\b", r"\bReduces Stress\b", r"\bRelax(?:es|ation)\b", r"\bcalmness\b", r"\bawareness\b"]),
    claim("structure_function_statements_claims", "Gut Health / Digestive Support", [r"\bGut Health\b", r"\bGut Friendly\b", r"\bDigest(?:ion|ive)\b", r"\bMaintains? Gut Health\b", r"\bDigestive Health\b", r"\bprebiotic\b", r"\bprobiotic\b"]),
    claim("structure_function_statements_claims", "Immune Support / Immune Defense", [r"\bImmune Support\b", r"\bSupports? Immunity\b", r"\bEnhance Immunity\b", r"\bBoosted Immunity\b", r"\bImmune Defense\b", r"\bImmune Health\b"]),
    claim("structure_function_statements_claims", "Antioxidant Support", [r"\bAntioxidant\b", r"\bfree radicals\b"]),
    claim("structure_function_statements_claims", "Longevity Support", [r"\bLongevity\b"]),
    claim("structure_function_statements_claims", "Sleep Support", [r"\bSleep Support\b", r"\bLess Caffeine for Sleep\b", r"\bBetter sleep\b"]),
    claim("structure_function_statements_claims", "Healthy Skin / Hair Support", [r"\bHealthy Skin\b", r"\bGlowing Skin\b", r"\bFull Hair\b", r"\bSkin\b"]),
    claim("structure_function_statements_claims", "Joint / Bone Support", [r"\bhealthy joints\b", r"\bstrong bones\b", r"\bJoint\b", r"\bBone\b"]),
    claim("structure_function_statements_claims", "Appetite Support", [r"\bAppetite\b"]),
    claim("structure_function_statements_claims", "Recovery Support", [r"\bRecovery\b"]),
    claim("structure_function_statements_claims", "Healthy Fats", [r"\bHealthy Fats\b", r"\bMCT oil\b"]),
    # Other claims
    claim("other_claims", "Coffee Alternative", [r"\bCoffee Alternative\b", r"\balternative to regular coffee\b", r"\bhealthy coffee alternative\b"]),
    claim("other_claims", "Instant / Easy to Brew", [r"\bInstant Coffee\b", r"\bEasy to Brew\b", r"\bEasy to mix\b", r"\bjust take\b", r"\bMix\b", r"\bready\b"]),
    claim("other_claims", "Great Taste / Smooth Texture", [r"\bGreat Tasting\b", r"\bgreat taste\b", r"\bsmooth texture\b", r"\brich & robust flavor\b", r"\bdeliciousness\b"]),
    claim("other_claims", "Jitter-Free / No Crash", [r"\bNo Jitters\b", r"\bNo Crash\b", r"\bjitter[- ]free\b", r"\bnone of the jitters\b", r"\bwithout jitters or crash\b"]),
    claim("other_claims", "Low Caffeine / Less Caffeine", [r"\bLow[- ]Caffeine\b", r"\bLess Caffeine\b"]),
    claim("other_claims", "Caffeine-Free", [r"\bCaffeine[- ]free\b"]),
    claim("other_claims", "No Added Sugar / No Sugar / Sugar Free", [r"\bNo Added Sugar\b", r"\bNo Sugar\b", r"\bSugar Free\b", r"\b0 sugar\b"]),
    claim("other_claims", "No Fillers / No Grains / No Additives", [r"\bNo Fillers\b", r"\bZero Fillers\b", r"\bNo Grains\b", r"\bNo Additives\b", r"\bNo sneaky additives\b"]),
    claim("other_claims", "No Oat Fillers", [r"\bNo Oat Fillers\b"]),
    claim("other_claims", "No Sweeteners", [r"\bNo .*sweeteners\b"]),
    claim("other_claims", "Natural Ingredients", [r"\bNatural Ingredients\b", r"\bnatural mushroom ingredients\b"]),
    claim("other_claims", "Full Spectrum / Whole Mushrooms", [r"\bFull Spectrum\b", r"\bwhole mushrooms\b"]),
    claim("other_claims", "Fruiting Bodies / Fruiting Body Extracts", [r"\b100% Fruiting Bod(?:y|ies)\b", r"\bfruiting bod(?:y|ies)\b", r"\bfruiting body extracts\b"]),
    claim("other_claims", "Double-Extracted", [r"\bdouble[- ]extracted\b"]),
    claim("other_claims", "No Mycelium on Grain", [r"\bnever mycelium\b", r"\bmycelium grown on grain\b"]),
    claim("other_claims", "Lab Tested / Third-Party Tested", [r"\bLab Tested\b", r"\b3rd[- ]Party Lab Tested\b", r"\bThird[- ]Party Lab Tested\b", r"\bThird[- ]party tested\b"]),
    claim("other_claims", "Glyphosate Residue Free", [r"\bGlyphosate Residue Free\b"]),
    claim("other_claims", "GMP / GMP Certified", [r"\bGMP Certified\b", r"\bcGMP\b", r"\bGMP\b"]),
    claim("other_claims", "Fair Trade", [r"\bFair Trade\b"]),
    claim("other_claims", "Made in USA / USA Grown", [r"\bMade in USA\b", r"\bUSA Grown\b", r"\bManufactured in Brooklyn\b", r"\bgrown locally\b"]),
    claim("other_claims", "30 Servings", [r"\b30 Servings\b"]),
    claim("other_claims", "60 Servings", [r"\b60 Servings\b"]),
    claim("other_claims", "7-Month Supply", [r"\b7-Month Supply\b"]),
]


ORDERED_BY_CATEGORY = {category: [] for category in CATEGORIES}
for item in CLAIMS:
    ORDERED_BY_CATEGORY[item["category"]].append(item)


def find_match(item, chunks):
    page_match = None
    same_input_match = None
    other_input_match = None
    for chunk in chunks:
        for pattern in item["patterns"]:
            match = pattern.search(chunk["text"])
            if not match:
                continue
            found = (chunk, match)
            if chunk["origin"] == "page":
                if page_match is None:
                    page_match = found
                if chunk["source"] == "Top highlights / product overview":
                    return found
            elif chunk.get("category") == item["category"] and same_input_match is None:
                same_input_match = found
            elif other_input_match is None:
                other_input_match = found
    return page_match or same_input_match or other_input_match


def snippet_for(chunk, match):
    if chunk["origin"] == "input_image" and chunk["input_evidence"]:
        text = chunk["input_evidence"]
    else:
        text = chunk["text"]
    text = clean_text(text)
    if len(text) <= 430:
        snippet = text
    else:
        base = chunk["text"]
        start = max(match.start() - 150, 0)
        end = min(match.end() + 270, len(base))
        snippet = clean_text(base[start:end])
        if start > 0:
            snippet = "..." + snippet
        if end < len(base):
            snippet += "..."

    source = chunk["source"]
    if chunk["origin"] == "input_image" and chunk.get("url"):
        source = f"{source} ({chunk['url']})"
    return source, snippet


def extract_record_claims(record):
    chunks = make_chunks(record)
    results = {category: [] for category in CATEGORIES}
    for category, items in ORDERED_BY_CATEGORY.items():
        seen = set()
        for item in items:
            found = find_match(item, chunks)
            if not found:
                continue
            key = item["label"].lower()
            if key in seen:
                continue
            seen.add(key)
            chunk, match = found
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


def join_claims(items):
    return " | ".join(item["claim"] for item in items)


def join_evidence(items):
    return " | ".join(
        f"{item['claim']} -> {item['evidence_source']}: {item['evidence']}" for item in items
    )


def make_notes(record):
    sections = record.get("sections", {})
    sc = record.get("specControl") or {}
    notes = []
    if record.get("error"):
        notes.append(f"Browser error: {record.get('error')}")
    else:
        notes.append("Browser visit succeeded")
    if sections.get("unavailable"):
        notes.append("Amazon page showed an unavailable/status message during capture")
    if (sections.get("title") or "").lower().startswith("page not found") or sections.get("bodyLength", 0) == 0:
        notes.append("Amazon page returned Page Not Found/no extractable product text")
    if sc.get("count"):
        if sc.get("clicked"):
            notes.append("See all product specifications control was clicked and captured")
        elif sc.get("enabled") is False:
            notes.append(
                "See all product specifications control was visible but browser-reported not enabled; available Top highlights/product overview/spec text was parsed from page HTML"
            )
        else:
            notes.append("See all product specifications control was present; available page HTML/spec text was parsed")
    else:
        notes.append("No See all product specifications control detected")
    if not clean_text(" ".join(sections.get("productOverview") or [])):
        notes.append("No Top highlights/product overview block was exposed in page HTML")
    notes.append("Recommendations, reviews, and comparison-table claims were not used")
    return "; ".join(notes)


def main():
    records = json.loads(BROWSER_SECTIONS.read_text(encoding="utf-8"))

    row_fields = ["asin", "url", "title"]
    for category in CATEGORIES:
        row_fields += [category, f"{category}_evidence"]
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

    row_rows = []
    claim_rows = []
    for record in records:
        input_row = record.get("input", {})
        sections = record.get("sections", {})
        asin = record.get("asin") or input_row.get("asin")
        url = record.get("navigatedUrl") or input_row.get("url") or record.get("url")
        title = clean_text(sections.get("title") or input_row.get("title"))
        results = extract_record_claims(record)

        out = {"asin": asin, "url": url, "title": title}
        for category in CATEGORIES:
            out[category] = join_claims(results[category])
            out[f"{category}_evidence"] = join_evidence(results[category])
            for idx, item in enumerate(results[category], start=1):
                claim_rows.append(
                    {
                        "asin": asin,
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
        out["missed_or_unclear_notes"] = make_notes(record)
        row_rows.append(out)

    with ROW_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=row_fields)
        writer.writeheader()
        writer.writerows(row_rows)

    with CLAIM_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=claim_fields)
        writer.writeheader()
        writer.writerows(claim_rows)

    with ORDER_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "claim_order", "canonical_claim"])
        writer.writeheader()
        for category in CATEGORIES:
            for idx, item in enumerate(ORDERED_BY_CATEGORY[category], start=1):
                writer.writerow(
                    {"category": category, "claim_order": idx, "canonical_claim": item["label"]}
                )

    print(f"row_count={len(row_rows)}")
    print(f"claim_rows={len(claim_rows)}")
    print(ROW_OUTPUT)
    print(CLAIM_OUTPUT)
    print(ORDER_OUTPUT)


if __name__ == "__main__":
    main()
