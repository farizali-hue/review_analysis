import csv
import json
import re
from pathlib import Path


BASE = Path(r"D:\analysis")
BROWSER_SECTIONS = BASE / "electrolyte_browser_sections.json"

ROW_OUTPUT = BASE / "claims_electrolyte_formalized_with_evidence.csv"
CLAIM_OUTPUT = BASE / "claims_electrolyte_claim_level_evidence.csv"
ORDER_OUTPUT = BASE / "claims_electrolyte_claim_order.csv"

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
    claim("health_benefit_claims", "Hydration Support", [r"\bhydrat(?:e|ion|ing|ed)\b", r"\bwhole-body hydration\b"]),
    claim("health_benefit_claims", "Rapid/Fast Hydration", [r"\brapid hydration\b", r"\bquick hydration\b", r"\bfast hydration\b", r"\bhydrates? faster\b"]),
    claim("health_benefit_claims", "Dehydration Relief / Rehydration", [r"\bdehydration relief\b", r"\bdefeat dehydration\b", r"\brehydrat(?:e|ion)\b"]),
    claim("health_benefit_claims", "Superior Hydration Than Water Alone", [r"\bsuperior hydration than water alone\b", r"\bfaster than water alone\b"]),
    claim("health_benefit_claims", "Electrolyte Balance Support", [r"\bsupports? electrolyte balance\b", r"\belectrolyte balance\b"]),
    claim("health_benefit_claims", "Electrolyte Replenishment", [r"\breplenish(?:es|ing)? electrolyte", r"\breplenishment\b", r"\blost water and electrolytes\b"]),
    claim("health_benefit_claims", "Sodium Replenishment", [r"\breplenish(?:es)? sodium\b", r"\bmineral lost in sweat\b", r"\belectrolytes lost through sweat\b"]),
    claim("health_benefit_claims", "Fluid Balance / Cellular Hydration", [r"\bfluid balance\b", r"\bcellular hydration\b"]),
    claim("health_benefit_claims", "Energy Support", [r"\benergy support\b", r"\bhealthy energy\b", r"\bmore energy\b", r"\bclean energy\b", r"\benergy & endurance\b", r"\ball-day energy\b"]),
    claim("health_benefit_claims", "Cellular Energy Support", [r"\bcellular energy\b", r"\bcell function\b"]),
    claim("health_benefit_claims", "Mental Clarity / Focus", [r"\bbrain fog\b", r"\bfocus\b", r"\bcognitive function\b"]),
    claim("health_benefit_claims", "Muscle Performance Support", [r"\bmuscle performance\b", r"\bmuscle function\b", r"\bstrength & movement\b", r"\bstronger muscles\b"]),
    claim("health_benefit_claims", "Cramp Relief / Reduced Cramping", [r"\bcramps?\b", r"\bcramping\b"]),
    claim("health_benefit_claims", "Endurance / Athletic Performance", [r"\bendurance\b", r"\bathletic performance\b", r"\bperforming your best\b", r"\bdaily performance\b"]),
    claim("health_benefit_claims", "Exercise/Post-Workout Recovery", [r"\brecovery after exercise\b", r"\bpost-workout recovery\b", r"\bmuscle recovery\b", r"\bquick recovery\b", r"\bfaster recovery\b", r"\bboost recovery\b"]),
    claim("health_benefit_claims", "Muscle & Tissue Support", [r"\bmuscle & tissue support\b", r"\bmuscle and tissue support\b", r"\brebuild damaged tissue\b"]),
    claim("health_benefit_claims", "Nerve Function Support", [r"\bnerve function\b"]),
    claim("health_benefit_claims", "Immune Support", [r"\bimmune support\b"]),
    claim("health_benefit_claims", "Metabolism Support", [r"\bmetabolism\b", r"\benergy metabolism\b"]),
    claim("health_benefit_claims", "Skin Hydration", [r"\bskin hydrating\b", r"\bdry skin\b"]),
    claim("health_benefit_claims", "Active Lifestyle Support", [r"\bactive lifestyles?\b", r"\btraining\b", r"\bworkouts?\b", r"\bsports activities?\b"]),
    # Certification / diet / free-from claims
    claim("certification_claims", "NSF Certified for Sport", [r"\bNSF Certified for Sport\b"]),
    claim("certification_claims", "NSF Certified Facility", [r"\bNSF Certified Facility\b"]),
    claim("certification_claims", "NSF", [r"\bNSF\b(?!\s+Certified for Sport)"]),
    claim("certification_claims", "cGMP Facility", [r"\bcGMP\b"]),
    claim("certification_claims", "Clinician Tested / Verified", [r"\bclinicians? tested\b", r"\bverified by FrontrowMD\b", r"\btrusted by hundreds of clinicians\b"]),
    claim("certification_claims", "Non-GMO Project Verified", [r"\bNon[- ]GMO Project Verified\b", r"\bNon GMO Project Verified\b", r"\bnon gmo verified\b"]),
    claim("certification_claims", "Non-GMO", [r"\bNon[- ]GMO\b", r"\bNON-GMO\b"]),
    claim("certification_claims", "Certified Vegan / Vegan", [r"\bCertified Vegan\b", r"\bVegan\b", r"\bVegan Friendly\b"]),
    claim("certification_claims", "Plant Based", [r"\bPlant[- ]Based\b", r"\bplant based\b"]),
    claim("certification_claims", "Keto Friendly", [r"\bKeto Friendly\b", r"\bketo diets?\b", r"\bDiet Type .*Keto\b", r"\bKeto\b"]),
    claim("certification_claims", "Paleo / Paleo-Keto Friendly", [r"\bPaleo[- ]Keto Friendly\b", r"\bPaleo Friendly\b", r"\bPaleo\b"]),
    claim("certification_claims", "Certified Gluten Free", [r"\bCertified Gluten[- ]Free\b", r"\bGluten[- ]Free Certified\b"]),
    claim("certification_claims", "Gluten Free / No Gluten", [r"\bGluten[- ]Free\b", r"\bNo Gluten\b"]),
    claim("certification_claims", "Dairy Free", [r"\bDairy[- ]Free\b"]),
    claim("certification_claims", "Soy Free", [r"\bSoy[- ]Free\b"]),
    claim("certification_claims", "Kosher Certified", [r"\bKosher Certified\b", r"\bKosher\b"]),
    claim("certification_claims", "Allergen Free", [r"\bAllergen Free\b"]),
    claim("certification_claims", "Osmolality Certified", [r"\bOsmolality Certified\b"]),
    claim("certification_claims", "Third-Party Tested", [r"\bthird[- ]party[- ]tested\b", r"\b3rd party certified\b", r"\bthird party certified\b"]),
    claim("certification_claims", "Lab-Tested", [r"\blab[- ]tested\b"]),
    # Nutritional claims
    claim("nutritional_claims", "Electrolyte Powder / Drink Mix", [r"\belectrolyte (?:powder|drink mix|packets?)\b", r"\belectrolytes powder\b"]),
    claim("nutritional_claims", "Electrolytes", [r"\belectrolytes?\b"]),
    claim("nutritional_claims", "3x Electrolytes", [r"\b3x (?:the )?electrolytes\b", r"\b3X ELECTROLYTES\b"]),
    claim("nutritional_claims", "6 Electrolytes", [r"\b6 (?:key |essential )?electrolytes\b", r"\ball 6 electrolytes\b"]),
    claim("nutritional_claims", "7 Key Electrolytes", [r"\b7 (?:key |essential )?electrolytes\b"]),
    claim("nutritional_claims", "Essential Electrolytes", [r"\bessential electrolytes\b"]),
    claim("nutritional_claims", "Sodium", [r"\bsodium\b", r"\bsalt\b"]),
    claim("nutritional_claims", "High Sodium", [r"\bhigh[- ]sodium\b", r"\bhigh sodium\b", r"\b1000 mg sodium\b", r"\b500mg Sodium\b"]),
    claim("nutritional_claims", "Potassium", [r"\bpotassium\b"]),
    claim("nutritional_claims", "Magnesium", [r"\bmagnesium\b"]),
    claim("nutritional_claims", "Calcium", [r"\bcalcium\b"]),
    claim("nutritional_claims", "Chloride", [r"\bchloride\b"]),
    claim("nutritional_claims", "Phosphorus", [r"\bphosphorus\b", r"\bphosphate\b"]),
    claim("nutritional_claims", "Zinc", [r"\bzinc\b"]),
    claim("nutritional_claims", "Vitamin C", [r"\bvitamin C\b", r"\bAscorbic Acid\b"]),
    claim("nutritional_claims", "B Vitamins", [r"\bvitamins? B3\b", r"\bB3, B5, B6", r"\bB12\b", r"\bB-Complex\b"]),
    claim("nutritional_claims", "5 Vitamins", [r"\b5 (?:key )?vitamins\b"]),
    claim("nutritional_claims", "8 Vitamins & Nutrients", [r"\b8 vitamins and nutrients\b"]),
    claim("nutritional_claims", "10 Vitamins & Nutrients", [r"\b10 vitamins? & nutrients\b", r"\b10 vitamins and nutrients\b"]),
    claim("nutritional_claims", "Trace Minerals", [r"\btrace minerals\b", r"\b83 trace minerals\b"]),
    claim("nutritional_claims", "Multivitamin", [r"\bmultivitamin\b"]),
    claim("nutritional_claims", "Himalayan Pink Salt / Sea Salt", [r"\bHimalayan pink salt\b", r"\bsea salt\b", r"\bFrench Grey Sea Salt\b"]),
    claim("nutritional_claims", "Sugar Free / Zero Sugar / No Sugar", [r"\bsugar[- ]free\b", r"\bzero sugar\b", r"\b0g sugar\b", r"\b0 g sugar\b", r"\bno sugar\b"]),
    claim("nutritional_claims", "No Added Sugar", [r"\bwithout added sugars?\b", r"\bno added sugar\b"]),
    claim("nutritional_claims", "Zero Calories / 0 Calories", [r"\bzero calories?\b", r"\b0 calories?\b", r"\b0 calorie\b", r"\bzero calorie\b"]),
    claim("nutritional_claims", "Low Calorie", [r"\blow[- ]calorie\b"]),
    claim("nutritional_claims", "0g Carbs / No Carbs", [r"\b0g carbs?\b", r"\b0 g carbs?\b", r"\bNo Carbs?\b"]),
    claim("nutritional_claims", "No Artificial Sweeteners", [r"\bno artificial sweeteners?\b", r"\bwithout .*artificial sweeteners?\b"]),
    claim("nutritional_claims", "No Artificial Colors", [r"\bno artificial colors?\b", r"\bNo FD&C colors\b", r"\bNo Artificial Dye Coloring\b", r"\b0 Artificial Colors\b"]),
    claim("nutritional_claims", "No Artificial Preservatives", [r"\bNo Artificial Preservatives\b"]),
    claim("nutritional_claims", "No Caffeine", [r"\bNo Caffeine\b", r"\bno jitters\b", r"\bno crash\b"]),
    claim("nutritional_claims", "Organic Stevia / Organic Sweetener", [r"\borganic stevia\b", r"\bOrganic Sweetener\b", r"\bOrganic Stevia Leaf Extract\b"]),
    claim("nutritional_claims", "Stevia Leaf", [r"\bstevia leaf\b", r"\bRebaudioside\b"]),
    claim("nutritional_claims", "Organic Fruit", [r"\bOrganic Fruit\b", r"\borganic fruits?\b"]),
    claim("nutritional_claims", "Plant-Based Flavors & Colors", [r"\bplant[- ]based flavors? (?:&|and) colors?\b", r"\bplant[- ]based flavor\b"]),
    claim("nutritional_claims", "Natural Flavors / Colors", [r"\bnatural flavors?\b", r"\bnatural colors?\b", r"\bcolors? derived from natural sources\b", r"\bfruit and vegetable juice.*color\b"]),
    claim("nutritional_claims", "Non-GMO", [r"\bNon[- ]GMO\b", r"\bNON-GMO\b"]),
    claim("nutritional_claims", "Vegan", [r"\bVegan\b"]),
    claim("nutritional_claims", "Keto Friendly", [r"\bKeto Friendly\b", r"\bketo diets?\b", r"\bDiet Type .*Keto\b", r"\bKeto\b"]),
    claim("nutritional_claims", "Paleo Friendly", [r"\bPaleo[- ]Keto Friendly\b", r"\bPaleo Friendly\b", r"\bPaleo\b"]),
    claim("nutritional_claims", "Gluten Free / No Gluten", [r"\bGluten[- ]Free\b", r"\bNo Gluten\b"]),
    claim("nutritional_claims", "Dairy Free", [r"\bDairy[- ]Free\b"]),
    claim("nutritional_claims", "Soy Free", [r"\bSoy[- ]Free\b"]),
    claim("nutritional_claims", "Allergen Free", [r"\bAllergen Free\b"]),
    # Structure/function claims
    claim("structure_function_statements_claims", "Hydration Support", [r"\bhydrat(?:e|ion|ing|ed)\b", r"\bwhole-body hydration\b"]),
    claim("structure_function_statements_claims", "Rapid/Fast Hydration", [r"\brapid hydration\b", r"\bquick hydration\b", r"\bfast hydration\b", r"\bhydrates? faster\b"]),
    claim("structure_function_statements_claims", "Dehydration Relief / Rehydration", [r"\bdehydration relief\b", r"\bdefeat dehydration\b", r"\brehydrat(?:e|ion)\b"]),
    claim("structure_function_statements_claims", "Superior Hydration Than Water Alone", [r"\bsuperior hydration than water alone\b", r"\bfaster than water alone\b"]),
    claim("structure_function_statements_claims", "Electrolyte Balance Support", [r"\bsupports? electrolyte balance\b", r"\belectrolyte balance\b"]),
    claim("structure_function_statements_claims", "Electrolyte Replenishment", [r"\breplenish(?:es|ing)? electrolyte", r"\blost water and electrolytes\b"]),
    claim("structure_function_statements_claims", "Sodium Replenishment", [r"\breplenish(?:es)? sodium\b", r"\bmineral lost in sweat\b", r"\belectrolytes lost through sweat\b"]),
    claim("structure_function_statements_claims", "Fluid Balance / Cellular Hydration", [r"\bfluid balance\b", r"\bcellular hydration\b"]),
    claim("structure_function_statements_claims", "Energy Support", [r"\benergy support\b", r"\bhealthy energy\b", r"\bmore energy\b", r"\bclean energy\b", r"\benergy & endurance\b", r"\ball-day energy\b"]),
    claim("structure_function_statements_claims", "Cellular Energy Support", [r"\bcellular energy\b", r"\bcell function\b"]),
    claim("structure_function_statements_claims", "Mental Clarity / Focus", [r"\bbrain fog\b", r"\bfocus\b", r"\bcognitive function\b"]),
    claim("structure_function_statements_claims", "Muscle Performance Support", [r"\bmuscle performance\b", r"\bmuscle function\b", r"\bstrength & movement\b", r"\bstronger muscles\b"]),
    claim("structure_function_statements_claims", "Cramp Relief / Reduced Cramping", [r"\bcramps?\b", r"\bcramping\b"]),
    claim("structure_function_statements_claims", "Endurance / Athletic Performance", [r"\bendurance\b", r"\bathletic performance\b", r"\bperforming your best\b", r"\bdaily performance\b"]),
    claim("structure_function_statements_claims", "Exercise/Post-Workout Recovery", [r"\brecovery after exercise\b", r"\bpost-workout recovery\b", r"\bmuscle recovery\b", r"\bquick recovery\b", r"\bfaster recovery\b", r"\bboost recovery\b"]),
    claim("structure_function_statements_claims", "Muscle & Tissue Support", [r"\bmuscle & tissue support\b", r"\bmuscle and tissue support\b", r"\brebuild damaged tissue\b"]),
    claim("structure_function_statements_claims", "Nerve Function Support", [r"\bnerve function\b"]),
    claim("structure_function_statements_claims", "Immune Support", [r"\bimmune support\b"]),
    claim("structure_function_statements_claims", "Metabolism Support", [r"\bmetabolism\b", r"\benergy metabolism\b"]),
    claim("structure_function_statements_claims", "Skin Hydration", [r"\bskin hydrating\b", r"\bdry skin\b"]),
    claim("structure_function_statements_claims", "Active Lifestyle Support", [r"\bactive lifestyles?\b", r"\btraining\b", r"\bworkouts?\b", r"\bsports activities?\b"]),
    # Other claims
    claim("other_claims", "Plant-Based Flavors & Colors", [r"\bplant[- ]based flavors? (?:&|and) colors?\b", r"\bplant[- ]based flavor\b"]),
    claim("other_claims", "Organic Sweetener / Organic Stevia", [r"\bOrganic Sweetener\b", r"\borganic stevia\b", r"\bOrganic Stevia Leaf Extract\b"]),
    claim("other_claims", "Organic Fruit", [r"\bOrganic Fruit\b", r"\borganic fruits?\b"]),
    claim("other_claims", "Natural Flavors / Colors", [r"\bnatural flavors?\b", r"\bnatural colors?\b", r"\bcolors? derived from natural sources\b", r"\bfruit and vegetable juice.*color\b"]),
    claim("other_claims", "No Artificial Sweeteners", [r"\bno artificial sweeteners?\b", r"\bwithout .*artificial sweeteners?\b"]),
    claim("other_claims", "No Artificial Colors", [r"\bno artificial colors?\b", r"\bNo FD&C colors\b", r"\bNo Artificial Dye Coloring\b", r"\b0 Artificial Colors\b"]),
    claim("other_claims", "No Artificial Preservatives", [r"\bNo Artificial Preservatives\b"]),
    claim("other_claims", "No Junk / Clean Ingredients", [r"\bno junk\b", r"\bclean ingredients\b", r"\bwithout the junk\b", r"\bHydration without the Junk\b"]),
    claim("other_claims", "No Dodgy Ingredients / Nothing Dodgy", [r"\bNo Dodgy Ingredients\b", r"\bNothing Dodgy\b", r"\bnothing you don't\b"]),
    claim("other_claims", "Raw Unflavored / Unflavored", [r"\bRaw Unflavored\b", r"\bUnflavored\b"]),
    claim("other_claims", "No Caffeine / No Jitters / No Crash", [r"\bNo Caffeine\b", r"\bno jitters\b", r"\bno crash\b"]),
    claim("other_claims", "On-The-Go / Travel Friendly", [r"\bon[- ]the[- ]go\b", r"\btravel[- ]friendly\b", r"\bportable\b", r"\bsingle[- ]serving\b", r"\bstick packs?\b"]),
    claim("other_claims", "Mixes With Water", [r"\bmix (?:one|1|a) .* with .*water\b", r"\badd .* to .* ounces of water\b", r"\b16 ?oz of water\b"]),
    claim("other_claims", "Science-Backed / Scientifically Formulated", [r"\bscience[- ]backed\b", r"\bscientifically (?:validated|formulated|backed)\b", r"\bscience-based\b"]),
    claim("other_claims", "Third-Party Tested", [r"\bthird[- ]party[- ]tested\b", r"\b3rd party certified\b"]),
    claim("other_claims", "Lab-Tested for Safety/Efficacy", [r"\blab[- ]tested\b", r"\bsafety and efficacy\b"]),
    claim("other_claims", "Clinician Trusted / FrontrowMD Verified", [r"\btrusted by hundreds of clinicians\b", r"\bverified by FrontrowMD\b", r"\btrusted by 45K\+ Health Pros\b"]),
    claim("other_claims", "Doctor Developed / Awarded", [r"\bdoctor[- ]developed\b", r"\bCreated by a doctor\b", r"\bMayo Clinic Humanitarian Award\b", r"\bMen's Journal Fitness Award\b"]),
    claim("other_claims", "Backed by 30+ Years Expertise", [r"\b30\+ years of expertise\b"]),
    claim("other_claims", "Trusted by Professional Sports Teams", [r"\btrusted by 100\+ professional sports teams\b", r"\bchosen by champions\b"]),
    claim("other_claims", "Recommended Clinical Brand", [r"\b#1 recommended clinical brand\b"]),
    claim("other_claims", "Public Benefit / Donations", [r"\bPublic Benefit Company\b", r"\bdonations?\b", r"\bEvery purchase supports\b", r"\bdonate over 1%\b"]),
    claim("other_claims", "No-Return Refund / Risk-Free", [r"\bno-return refund policy\b", r"\brisk-free\b"]),
    claim("other_claims", "Flavored With Natural Flavors", [r"\bflavored with .*natural flavors\b"]),
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
    if len(text) <= 420:
        snippet = text
    else:
        base = chunk["text"]
        start = max(match.start() - 140, 0)
        end = min(match.end() + 260, len(base))
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
    notes.append("Browser visit succeeded" if not record.get("error") else f"Browser error: {record.get('error')}")
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
    notes.append("Recommendations, review text, and comparison-table claims were not used")
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
