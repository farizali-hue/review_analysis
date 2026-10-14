import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


INPUT_ROWS_JSON = Path(r"D:\analysis\black_seed_thymo2_input_rows.json")
PAGES_DIR = Path(r"D:\analysis\black_seed_thymo2_pages")
OUT_JSON = Path(r"D:\analysis\black_seed_thymo2_sections.json")
OUT_TXT = Path(r"D:\analysis\black_seed_thymo2_section_dump.txt")


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
    text = (text or "").replace("\xa0", " ")
    text = text.replace("â€Ž", "").replace("â€", "")
    text = text.replace("Â®", "®").replace("â€“", "-").replace("â€™", "'")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
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
    out["see_all_product_specifications_context"] = (
        full_text[max(0, idx - 1400) : idx + 4000] if idx >= 0 else ""
    )
    return out


def main() -> None:
    rows = json.loads(INPUT_ROWS_JSON.read_text(encoding="utf-8"))
    records = []
    dump = []

    for row in rows:
        asin = str(row["asin"]).strip()
        html = (PAGES_DIR / f"{asin}.html").read_text(encoding="utf-8", errors="replace")
        sections = page_sections(html)
        record = {
            "asin": asin,
            "url": row.get("url", ""),
            "input_title": row.get("title", ""),
            "input_nutritional_claims": row.get("nutritional_claims", ""),
            "input_structure_function_statements_claims": row.get("structure_function_statements_claims", ""),
            "sections": sections,
        }
        records.append(record)

        dump.append("=" * 90)
        dump.append(f"ASIN: {asin}")
        dump.append(f"URL: {row.get('url', '')}")
        dump.append(f"INPUT nutritional_claims: {row.get('nutritional_claims', '')}")
        dump.append(f"INPUT structure_function: {row.get('structure_function_statements_claims', '')}")
        for name, value in sections.items():
            dump.append(f"\n--- {name} ---")
            if isinstance(value, list):
                dump.append("\n\n".join(value))
            else:
                dump.append(value)

    OUT_JSON.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_TXT.write_text("\n".join(dump), encoding="utf-8")


if __name__ == "__main__":
    main()
