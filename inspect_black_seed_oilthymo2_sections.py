import csv
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_CSV = Path(r"D:\analysis\black_seed_oilthymo2_pages\input_rows.csv")
PAGES_DIR = Path(r"D:\analysis\black_seed_oilthymo2_pages")
OUT_JSON = Path(r"D:\analysis\black_seed_oilthymo2_sections.json")
OUT_TXT = Path(r"D:\analysis\black_seed_oilthymo2_section_dump.txt")

SELECTORS = {
    "product_title": "#productTitle",
    "feature_bullets": "#feature-bullets",
    "product_overview": "#productOverview_feature_div",
    "important_information": "#important-information",
    "detail_bullets": "#detailBullets_feature_div",
    "detail_bullets_wrapper": "#detailBulletsWrapper_feature_div",
    "product_description": "#productDescription",
    "product_details_feature": "#productDetails_feature_div",
    "prod_details": "#prodDetails",
    "product_facts_desktop": "#productFactsDesktop_feature_div",
    "aplus": "#aplus",
}


def clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ")
    text = text.replace("â€Ž", "").replace("â€", "").replace("Â®", "®")
    text = text.replace("â€“", "–").replace("â€”", "—")
    text = text.replace("â€œ", '"').replace("â€", '"').replace("â€™", "'")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?im)^\s*(show more|read more|loading content\.)\s*$", "", text)
    return text.strip()


def node_text(node) -> str:
    node = BeautifulSoup(str(node), "html.parser")
    for tag in node.select("script,style,noscript,svg"):
        tag.decompose()
    return clean_text(node.get_text("\n", strip=True))


def page_sections(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for name, selector in SELECTORS.items():
        texts = []
        for node in soup.select(selector)[:4]:
            text = node_text(node)
            if text and text not in texts:
                texts.append(text)
        out[name] = texts

    full_text = clean_text(soup.get_text("\n", strip=True))
    idx = full_text.lower().find("see all product specifications")
    context = full_text[max(0, idx - 1800) : idx + 6000] if idx >= 0 else ""
    spec_idx = full_text.lower().find("product specifications")
    spec_context = full_text[spec_idx : spec_idx + 5000] if spec_idx >= 0 else ""
    out["see_all_product_specifications_context"] = clean_text(context)
    out["product_specifications_context"] = clean_text(spec_context)
    return out


def main() -> None:
    rows = list(csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")))
    extracted = []
    dump = []
    for row in rows:
        asin = row["asin"]
        html = (PAGES_DIR / f"{asin}.html").read_text(encoding="utf-8", errors="replace")
        sections = page_sections(html)
        extracted.append({"asin": asin, "url": row["url"], "input": row, "sections": sections})

        dump.append("=" * 90)
        dump.append(f"ASIN: {asin}")
        dump.append(f"URL: {row['url']}")
        for name, value in sections.items():
            dump.append(f"\n--- {name} ---")
            dump.append("\n\n".join(value) if isinstance(value, list) else value)

    OUT_JSON.write_text(json.dumps(extracted, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_TXT.write_text("\n".join(dump), encoding="utf-8")


if __name__ == "__main__":
    main()
