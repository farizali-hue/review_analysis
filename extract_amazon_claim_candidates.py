from __future__ import annotations

import csv
import html
import re
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\claims_coq10.csv")
HTML_DIR = Path(r"D:\analysis\amazon_pages")
OUT_CSV = Path(r"D:\analysis\amazon_claim_candidates.csv")


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
]

CLAIM_KEYWORDS = [
    "absorption",
    "absorb",
    "active form",
    "antioxidant",
    "artificial",
    "bioavailability",
    "bioperine",
    "black pepper",
    "blood pressure",
    "cardio",
    "cellular",
    "clinical",
    "coconut",
    "color added",
    "dairy",
    "delivery",
    "dissolve",
    "energy",
    "fermented",
    "filler",
    "free",
    "gluten",
    "gmp",
    "heart",
    "immune",
    "lactose",
    "mitochondrial",
    "non-gmo",
    "non gmo",
    "preservative",
    "recommended",
    "sodium",
    "soy",
    "statin",
    "sugar",
    "support",
    "tested",
    "ubiquinol",
    "vegan",
    "vascular",
    "wheat",
]

SPEC_KEYS = [
    "Age Range Description",
    "Allergen Information",
    "Diet Type",
    "Flavor",
    "Ingredient Features",
    "Ingredients",
    "Item Form",
    "Material Feature",
    "Primary Supplement Type",
    "Product Benefits",
    "Product Grade",
    "Recommended Uses For Product",
    "Special Ingredients",
    "Specialty",
]


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n:-")


def split_claims(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    pieces: list[str] = []
    for raw in re.split(r"\s+[|•]\s+|;\s+|\s+-\s+", text):
        raw = clean_text(raw)
        if raw:
            pieces.append(raw)
    return pieces


def add_unique(items: list[str], value: str) -> None:
    value = clean_text(value)
    if not value:
        return
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    if not normalized:
        return
    for item in items:
        if re.sub(r"[^a-z0-9]+", " ", item.lower()).strip() == normalized:
            return
    items.append(value)


def text_has_claim_signal(text: str) -> bool:
    low = text.lower()
    return any(keyword in low for keyword in CLAIM_KEYWORDS)


def scoped_text(soup: BeautifulSoup, element_id: str) -> str:
    node = soup.find(id=element_id)
    if not node:
        return ""
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
    title = scoped_text(soup, "productTitle")
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
            if text and text.lower() not in {"", "show more"}:
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
        for key, val in table_rows(node):
            specs.setdefault(key, [])
            add_unique(specs[key], val)
    return specs


def extract_claim_candidates(row: dict[str, str]) -> dict[str, str]:
    asin = row["asin"]
    path = HTML_DIR / f"{asin}.html"
    source_status = "OK"
    if not path.exists():
        return {
            "asin": asin,
            "url": row.get("url", ""),
            "title": row.get("title", ""),
            "image_claims": row.get("claims", ""),
            "title_claims": "",
            "bullet_claims": "",
            "spec_claims": "",
            "section_claims": "",
            "spec_key_values": "",
            "source_status": "MISSING_HTML",
        }

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    title = get_title(soup) or row.get("title", "")

    title_claims: list[str] = []
    for piece in split_claims(title):
        if text_has_claim_signal(piece):
            add_unique(title_claims, piece)

    bullet_claims: list[str] = []
    for bullet in extract_bullets(soup):
        if text_has_claim_signal(bullet):
            add_unique(bullet_claims, bullet)

    specs = extract_specs(soup)
    spec_claims: list[str] = []
    spec_key_values: list[str] = []
    for key, vals in specs.items():
        for val in vals:
            kv = f"{key}: {val}"
            if key in SPEC_KEYS or text_has_claim_signal(kv):
                add_unique(spec_key_values, kv)
            if key in SPEC_KEYS or text_has_claim_signal(kv):
                for piece in split_claims(val):
                    if text_has_claim_signal(piece) or key in SPEC_KEYS:
                        add_unique(spec_claims, piece)

    section_claims: list[str] = []
    for section_id in SECTION_IDS:
        text = scoped_text(soup, section_id)
        if not text:
            continue
        for sent in re.split(r"(?<=[.!?])\s+|\s{2,}", text):
            sent = clean_text(sent)
            if 8 <= len(sent) <= 240 and text_has_claim_signal(sent):
                add_unique(section_claims, sent)

    if "Sorry, we just need to make sure you're not a robot" in soup.get_text(" ", strip=True):
        source_status = "CAPTCHA_OR_ROBOT_CHECK"

    return {
        "asin": asin,
        "url": row.get("url", ""),
        "title": title,
        "image_claims": row.get("claims", ""),
        "title_claims": " | ".join(title_claims),
        "bullet_claims": " | ".join(bullet_claims),
        "spec_claims": " | ".join(spec_claims),
        "section_claims": " | ".join(section_claims),
        "spec_key_values": " | ".join(spec_key_values),
        "source_status": source_status,
    }


def main() -> None:
    with INPUT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    out_rows = [extract_claim_candidates(row) for row in rows]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {OUT_CSV} with {len(out_rows)} rows")


if __name__ == "__main__":
    main()
