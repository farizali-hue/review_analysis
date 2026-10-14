import csv
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\liposomal_vitc_claims.csv")
PAGES_DIR = Path(r"D:\analysis\liposomal_vitc_pages")
OUT_JSON = Path(r"D:\analysis\liposomal_vitc_sections.json")
OUT_TXT = Path(r"D:\analysis\liposomal_vitc_section_dump.txt")

SELECTORS = {
    "product_title": "#productTitle",
    "feature_bullets": "#feature-bullets",
    "feature_bullets_btf": "#feature-bullets-btf",
    "product_overview": "#productOverview_feature_div",
    "product_description": "#productDescription",
    "important_information": "#important-information",
    "detail_bullets": "#detailBullets_feature_div",
    "detail_bullets_wrapper": "#detailBulletsWrapper_feature_div",
    "product_details_feature": "#productDetails_feature_div",
    "prod_details": "#prodDetails",
    "technical_details": "#productDetails_techSpec_section_1",
    "product_facts_desktop": "#productFactsDesktop_feature_div",
    "aplus": "#aplus",
}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?im)^\s*(show more|read more|click to play video|image unavailable)\s*$", "", text)
    return text.strip()


def node_text(node) -> str:
    for tag in node.select("script,style,noscript,svg"):
        tag.decompose()
    return clean_text(node.get_text("\n", strip=True))


def page_sections(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for name, selector in SELECTORS.items():
        nodes = soup.select(selector)
        texts = []
        for node in nodes[:4]:
            text = node_text(node)
            if text and text not in texts:
                texts.append(text)
        out[name] = texts

    # Amazon's spec/product-summary drawer text is sometimes present as a disabled
    # link or hidden card. Capture a small local context so we can verify whether
    # the page exposed it without scraping unrelated recommendation widgets.
    full_text = clean_text(soup.get_text("\n", strip=True))
    idx = full_text.lower().find("see all product specifications")
    out["see_all_product_specifications_context"] = (
        full_text[max(0, idx - 1200) : idx + 2500] if idx >= 0 else ""
    )
    return out


def main() -> None:
    rows = list(csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")))
    extracted = []
    dump_parts = []
    for row in rows:
        asin = row["asin"]
        path = PAGES_DIR / f"{asin}.html"
        html = path.read_text(encoding="utf-8", errors="replace")
        sections = page_sections(html)
        record = {
            "asin": asin,
            "url": row["url"],
            "input_title": row["title"],
            "sections": sections,
        }
        extracted.append(record)

        dump_parts.append("=" * 90)
        dump_parts.append(f"ASIN: {asin}")
        dump_parts.append(f"URL: {row['url']}")
        for name, texts in sections.items():
            dump_parts.append(f"\n--- {name} ---")
            if isinstance(texts, list):
                dump_parts.append("\n\n".join(texts) if texts else "")
            else:
                dump_parts.append(texts)

    OUT_JSON.write_text(json.dumps(extracted, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_TXT.write_text("\n".join(dump_parts), encoding="utf-8")


if __name__ == "__main__":
    main()
