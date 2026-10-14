from __future__ import annotations

import csv
import html
import re
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\additionalclaims_black_seed_oil_thymo.csv")
HTML_DIR = Path(r"D:\analysis\amazon_pages_black_seed")
OUT_CSV = Path(r"D:\analysis\black_seed_claim_candidates.csv")


SECTION_IDS = [
    "feature-bullets",
    "featurebullets_feature_div",
    "productOverview_feature_div",
    "richProductInformation_feature_div",
    "productFactsDesktop_feature_div",
    "dietaryInformationLogo_feature_div",
    "importantInformation_feature_div",
    "productDetails_feature_div",
    "productDetailsNonPets_feature_div",
    "detailBullets_feature_div",
    "aplus_feature_div",
    "productDescription_feature_div",
    "pqv-feature-bullets",
    "pqv-description",
    "voyager-ns-desktop-side-sheet-content",
    "voyagerNorthstarBTF",
]

CLAIM_KEYWORDS = [
    "additive",
    "antioxidant",
    "bioactive",
    "black seed",
    "black cumin",
    "botanical",
    "brain",
    "breathing",
    "cardio",
    "cellular",
    "certified",
    "cold pressed",
    "cold-pressed",
    "concentrate",
    "digestion",
    "digestive",
    "energy",
    "focus",
    "free",
    "gluten",
    "gut",
    "halal",
    "heart",
    "immune",
    "immunity",
    "kosher",
    "liver",
    "lung",
    "memory",
    "metabolism",
    "natural",
    "non-gmo",
    "non gmo",
    "omega",
    "organic",
    "potency",
    "potent",
    "raw",
    "respiratory",
    "support",
    "thymo",
    "tq",
    "vegan",
    "vitality",
    "wellness",
]

CERT_KEYWORDS = [
    "certified",
    "non-gmo",
    "non gmo",
    "gmo free",
    "gluten free",
    "vegan",
    "organic",
    "usda",
    "kosher",
    "halal",
    "gmp",
    "third party",
    "third-party",
]

HEALTH_KEYWORDS = [
    "antioxidant",
    "brain",
    "breathing",
    "cardio",
    "cellular",
    "digestion",
    "digestive",
    "energy",
    "focus",
    "gut",
    "heart",
    "immune",
    "immunity",
    "liver",
    "lung",
    "memory",
    "metabolism",
    "nutrient absorption",
    "oxygenation",
    "respiratory",
    "vitality",
    "wellness",
]

SPEC_KEYS = [
    "Allergen Information",
    "Diet Type",
    "Flavor",
    "Ingredient Features",
    "Item Form",
    "Material Feature",
    "Material Features",
    "Material Type Free",
    "Primary Supplement Type",
    "Product Benefits",
    "Product Grade",
    "Recommended Uses For Product",
    "Special Ingredients",
    "Specialty",
    "Specific Uses For Product",
]


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("\u200e", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n:-")


def add_unique(items: list[str], value: str) -> None:
    value = clean_text(value)
    if not value:
        return
    norm = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    if not norm:
        return
    if any(re.sub(r"[^a-z0-9]+", " ", existing.lower()).strip() == norm for existing in items):
        return
    items.append(value)


def has_any(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return any(keyword in low for keyword in keywords)


def split_claims(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    parts = re.split(r"\s+[|•]\s+|;\s+|\s+-\s+|,\s+(?=(?:Non|Vegan|Gluten|Organic|Cold|Immune|Digestive|Heart|Antioxidant|Energy|Omega|Raw|High|Pure)\\b)", text)
    return [clean_text(part) for part in parts if clean_text(part)]


def scoped_text(soup: BeautifulSoup, element_id: str) -> str:
    node = soup.find(id=element_id)
    if not node:
        return ""
    for bad in node.select("script, style, noscript"):
        bad.decompose()
    return clean_text(node.get_text(" ", strip=True))


def table_rows(scope) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for tr in scope.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        key = clean_text(th.get_text(" ", strip=True))
        val = clean_text(td.get_text(" ", strip=True))
        if key and val:
            rows.append((key, val))
    return rows


def get_title(soup: BeautifulSoup) -> str:
    node = soup.find(id="productTitle")
    if node:
        title = clean_text(node.get_text(" ", strip=True))
        if title:
            return title
    meta = soup.find("meta", attrs={"name": "title"})
    if meta and meta.get("content"):
        title = str(meta["content"])
        title = re.sub(r"^Amazon\.com:\s*", "", title)
        title = re.sub(r"\s*:\s*Health & Household\s*$", "", title)
        return clean_text(title)
    if soup.title:
        return clean_text(soup.title.get_text(" ", strip=True))
    return ""


def extract_bullets(soup: BeautifulSoup) -> list[str]:
    bullets: list[str] = []
    for section_id in ["feature-bullets", "featurebullets_feature_div", "pqv-feature-bullets"]:
        section = soup.find(id=section_id)
        if not section:
            continue
        for li in section.find_all("li"):
            text = clean_text(li.get_text(" ", strip=True))
            if text and text.lower() not in {"show more", "make sure this fits by entering your model number."}:
                add_unique(bullets, text)
    return bullets


def extract_specs(soup: BeautifulSoup) -> dict[str, list[str]]:
    specs: dict[str, list[str]] = {}
    for container_id in [
        "voyager-ns-desktop-side-sheet-content",
        "voyagerNorthstarBTF",
        "productDetails_feature_div",
        "productDetailsNonPets_feature_div",
        "detailBullets_feature_div",
        "productOverview_feature_div",
    ]:
        node = soup.find(id=container_id)
        if not node:
            continue
        for key, value in table_rows(node):
            specs.setdefault(key, [])
            add_unique(specs[key], value)
    return specs


def extract_row(row: dict[str, str]) -> dict[str, str]:
    asin = row["asin"]
    path = HTML_DIR / f"{asin}.html"
    if not path.exists():
        return {
            "asin": asin,
            "url": row.get("url", ""),
            "title": row.get("title", ""),
            "image_claims": row.get("claims", ""),
            "image_certifications": row.get("certifications", ""),
            "image_health_claims": row.get("health_claims", ""),
            "title_candidates": "",
            "bullet_candidates": "",
            "spec_key_values": "",
            "claim_candidates": "",
            "health_candidates": "",
            "certification_candidates": "",
            "source_status": "MISSING_HTML",
        }

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    page_text = soup.get_text(" ", strip=True)
    source_status = "CAPTCHA_OR_ROBOT_CHECK" if "not a robot" in page_text.lower() else "OK"
    title = get_title(soup) or row.get("title", "")

    title_candidates: list[str] = []
    for part in split_claims(title):
        if has_any(part, CLAIM_KEYWORDS):
            add_unique(title_candidates, part)

    bullet_candidates = [b for b in extract_bullets(soup) if has_any(b, CLAIM_KEYWORDS)]

    specs = extract_specs(soup)
    spec_key_values: list[str] = []
    for key, values in specs.items():
        for value in values:
            pair = f"{key}: {value}"
            if key in SPEC_KEYS or has_any(pair, CLAIM_KEYWORDS):
                add_unique(spec_key_values, pair)

    claim_candidates: list[str] = []
    health_candidates: list[str] = []
    certification_candidates: list[str] = []
    for text in title_candidates + bullet_candidates + spec_key_values:
        for part in split_claims(text):
            if has_any(part, CLAIM_KEYWORDS):
                add_unique(claim_candidates, part)
            if has_any(part, HEALTH_KEYWORDS):
                add_unique(health_candidates, part)
            if has_any(part, CERT_KEYWORDS):
                add_unique(certification_candidates, part)

    for section_id in SECTION_IDS:
        text = scoped_text(soup, section_id)
        if not text:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+|\s{2,}", text):
            sentence = clean_text(sentence)
            if 8 <= len(sentence) <= 260 and has_any(sentence, CLAIM_KEYWORDS):
                add_unique(claim_candidates, sentence)
                if has_any(sentence, HEALTH_KEYWORDS):
                    add_unique(health_candidates, sentence)
                if has_any(sentence, CERT_KEYWORDS):
                    add_unique(certification_candidates, sentence)

    return {
        "asin": asin,
        "url": row.get("url", ""),
        "title": title,
        "image_claims": row.get("claims", ""),
        "image_certifications": row.get("certifications", ""),
        "image_health_claims": row.get("health_claims", ""),
        "title_candidates": " | ".join(title_candidates),
        "bullet_candidates": " | ".join(bullet_candidates),
        "spec_key_values": " | ".join(spec_key_values),
        "claim_candidates": " | ".join(claim_candidates),
        "health_candidates": " | ".join(health_candidates),
        "certification_candidates": " | ".join(certification_candidates),
        "source_status": source_status,
    }


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    out_rows = [extract_row(row) for row in rows]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {OUT_CSV} with {len(out_rows)} rows")


if __name__ == "__main__":
    main()
