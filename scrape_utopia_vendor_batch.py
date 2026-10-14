import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from datetime import date
from pathlib import Path

import pandas as pd
from lxml import html as lxml_html


INPUT_XLSX = Path(r"C:\Users\dell\OneDrive - Utopia\Documents\B2B Hospitality - batch 2.xlsx")
OUT_DIR = Path(r"D:\analysis\outputs\utopia_vendor_scrape")
DATE_CHECKED = "2026-05-08"
PRODUCT_PAGE_TEXT = {}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}


CORE_TERMS = [
    "sheet",
    "pillowcase",
    "duvet",
    "comforter",
    "coverlet",
    "quilt",
    "blanket",
    "mattress encasement",
    "mattress protector",
    "mattress pad",
    "mattress topper",
    "pillow protector",
    "bed pillow",
    "pillow",
    "bed skirt",
    "bedwrap",
    "bed wrap",
    "box spring wrap",
    "bath towel",
    "hand towel",
    "washcloth",
    "wash cloth",
    "towel set",
    "towels",
    "bath mat",
    "bath rug",
    "featherbed",
]

BACKUP_TERMS = [
    "tablecloth",
    "table cloth",
    "table linen",
    "napkin",
    "placemat",
    "kitchen towel",
    "dish towel",
    "spa towel",
    "pool towel",
    "beach towel",
    "bed runner",
    "bed scarf",
    "cushion cover",
    "shower wrap",
    "bath robe",
    "robe",
    "slipper",
]

EXCLUDED_TERMS = [
    "decorative pillow",
    "dec pillow",
    "throw pillow",
    "shower curtain",
    "curtain",
    "furniture",
    "wallcovering",
    "fabric",
    "upholstery",
    "casegoods",
]

MATERIAL_PATTERNS = [
    r"\b\d{1,3}\s*/\s*\d{1,3}\s*(?:cotton|polyester)[^.;,\n<]*",
    r"\b\d{1,3}%\s*[^.;,\n<]*(?:cotton|polyester|microfiber|linen|cashmere|wool|down|feather|tencel|lyocell|rayon|nylon|polypropylene|latex|acrylic|spandex)[^.;\n<]*",
    r"\b(?:100%|all)\s+[^.;,\n<]*(?:cotton|polyester|microfiber|linen|cashmere|wool|down|feather|tencel|lyocell|rayon|nylon|polypropylene|latex|acrylic)[^.;\n<]*",
    r"\b(?:cotton|polyester|microfiber|linen|cashmere|wool|down|feather|tencel|lyocell|rayon|nylon|polypropylene|latex|acrylic)\s+(?:blend|fill|cover|shell|yarns?|fabric|construction)[^.;\n<]*",
]


def fetch_bytes(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), resp.headers.get_content_type()


def fetch_text(url):
    data, _ = fetch_bytes(url)
    return data.decode("utf-8", "ignore")


def fetch_json(url):
    data, _ = fetch_bytes(url)
    return json.loads(data.decode("utf-8", "ignore"))


def clean_text(value):
    if value is None:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def money(value):
    if value is None or value == "":
        return "Not visible"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def abs_url(base, href):
    if not href:
        return base
    return urllib.parse.urljoin(base, href)


def collection_json_url(base_url, handle):
    return urllib.parse.urljoin(base_url, f"/collections/{handle}/products.json?limit=250")


def product_url(base_url, handle):
    return urllib.parse.urljoin(base_url, f"/products/{urllib.parse.quote(str(handle), safe='')}")


def product_page_text(url):
    if url in PRODUCT_PAGE_TEXT:
        return PRODUCT_PAGE_TEXT[url]
    try:
        text = fetch_text(url)
        tree = lxml_html.fromstring(text)
        main_text = clean_text(" ".join(tree.xpath("//main//text() | //article//text() | //body//text()")))
    except Exception as exc:
        print(f"WARN product page text failed {url}: {exc}", file=sys.stderr)
        main_text = ""
    PRODUCT_PAGE_TEXT[url] = main_text
    return main_text


def visible_collection_products(base_url, handle):
    url = urllib.parse.urljoin(base_url, f"/collections/{handle}")
    try:
        text = fetch_text(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"WARN collection missing {url}", file=sys.stderr)
            return url, OrderedDict()
        raise
    tree = lxml_html.fromstring(text)
    links = []
    for a in tree.xpath("//a[contains(@href, '/products/')]"):
        href = a.get("href") or ""
        title = clean_text(" ".join(a.xpath(".//text()")))
        href_no_query = href.split("?")[0]
        if not title:
            img_alt = a.xpath(".//img/@alt")
            title = clean_text(img_alt[0]) if img_alt else ""
        if not title:
            continue
        if "gift card" in title.lower():
            continue
        if title.lower() in {"quick buy", "show options", "add to cart", "view full details"}:
            continue
        links.append((abs_url(base_url, href_no_query), title))
    # Preserve order and remove duplicate product links/titles.
    out = OrderedDict()
    for link, title in links:
        if "/products/" not in link:
            continue
        # Product-card image links often duplicate title links; keep the title-like entry.
        if link not in out or len(title) > len(out[link]):
            out[link] = title
    return url, out


def collect_collection_products(base_url, handle):
    collection_url, visible = visible_collection_products(base_url, handle)
    by_handle = OrderedDict()
    try:
        data = fetch_json(collection_json_url(base_url, handle))
        for product in data.get("products", []):
            by_handle[product["handle"]] = product
    except Exception as exc:
        print(f"WARN json failed {collection_url}: {exc}", file=sys.stderr)
    for link, title in visible.items():
        parsed = urllib.parse.urlparse(link)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[-2] == "products":
            handle = urllib.parse.unquote(parts[-1])
            if handle not in by_handle:
                by_handle[handle] = {
                    "title": title,
                    "handle": handle,
                    "body_html": "",
                    "product_type": "",
                    "tags": [],
                    "variants": [],
                    "_visible_only": True,
                }
    return collection_url, list(by_handle.values())


def extract_material(title, product_type, body_html, tags):
    haystack = " ".join([title or "", product_type or "", clean_text(body_html), " ".join(tags or [])])
    candidates = []
    for pattern in MATERIAL_PATTERNS:
        for match in re.finditer(pattern, haystack, re.I):
            text = clean_text(match.group(0)).rstrip(" ,")
            if not text:
                continue
            if len(text) > 160:
                text = text[:157].rstrip(" ,") + "..."
            score = 0
            if "%" in text:
                score += 100
            if re.search(r"\d+\s*/\s*\d+", text):
                score += 90
            if re.search(r"\b100%|^all\b", text, re.I):
                score += 40
            if re.search(r"\b(cotton|polyester|microfiber|linen|cashmere|wool|down|feather|tencel|lyocell|nylon)\b", text, re.I):
                score += 20
            if re.search(r"\b(yarns and woven|provide|experience|softness|feel)\b", text, re.I):
                score -= 25
            candidates.append((score, len(text), text))
    if candidates:
        candidates.sort(key=lambda item: (-item[0], item[1]))
        return candidates[0][2]
    return "Not visible"


def variant_unit_text(variant_title):
    value = clean_text(variant_title)
    if not value or value.lower() == "default title":
        return "Not visible"
    # Keep only the visible variant dimension that carries a unit/pack/count signal.
    parts = [p.strip() for p in value.split("/") if p.strip()]
    unit_parts = []
    for part in parts:
        if re.search(r"\b(set|pair|piece|pack|case|dozen|bath towel|hand towel|washcloth|wash cloth|pillowcase|robe|towel)\b", part, re.I):
            unit_parts.append(part)
    return " / ".join(unit_parts) if unit_parts else "Not visible"


def listing_price(product, visible_price=True):
    if not visible_price:
        return "Not visible"
    variants = product.get("variants") or []
    prices = []
    compare = []
    for v in variants:
        if v.get("price") not in (None, ""):
            prices.append(float(v["price"]))
        if v.get("compare_at_price") not in (None, ""):
            compare.append(float(v["compare_at_price"]))
    if not prices:
        return "Not visible"
    if len(set(prices)) == 1:
        text = money(prices[0])
    else:
        text = f"From {money(min(prices))}"
    if compare:
        low_compare = min(compare)
        if low_compare > min(prices):
            text += f" (compare at {money(low_compare)})"
    return text


def product_notes(product, source_type, hidden_price=False):
    notes = []
    variants = product.get("variants") or []
    variant_titles = [clean_text(v.get("title")) for v in variants if clean_text(v.get("title")) and clean_text(v.get("title")).lower() != "default title"]
    if len(variant_titles) > 1:
        sample = "; ".join(variant_titles[:5])
        if len(variant_titles) > 5:
            sample += f"; +{len(variant_titles) - 5} more"
        notes.append(f"Variants visible/available: {sample}.")
    if product.get("_visible_only"):
        notes.append("Visible on collection page; product JSON unavailable.")
    if hidden_price:
        notes.append("Product data endpoint contains pricing, but no price was visible on the public product/listing page.")
    if source_type:
        notes.append(source_type)
    return " ".join(notes) if notes else ""


def classify_product(title, product_type, collection_handle, source_label, is_hospitality=False):
    text = " ".join([title or "", product_type or "", collection_handle or "", source_label or ""]).lower()
    text = re.sub(r"[-_]+", " ", text)
    if any(term in text for term in EXCLUDED_TERMS):
        return "Excluded_Unrelated", "Outside the requested scope or decor/service category."
    if "pool towel" in text or "beach towel" in text or "table" in text or "napkin" in text or "placemat" in text or "bed runner" in text or "bed scarf" in text:
        return "Backup_Gap_Fill", ""
    if ("robe" in text or "slipper" in text or "shower wrap" in text) and not is_hospitality:
        return "Excluded_Unrelated", "Robe/wrap item is not positioned as hotel/spa/hospitality soft goods on this source."
    if ("robe" in text or "slipper" in text or "shower wrap" in text) and is_hospitality:
        return "Backup_Gap_Fill", ""
    if any(term in text for term in CORE_TERMS):
        return "Core_Utopia_Overlap", ""
    if any(term in text for term in BACKUP_TERMS):
        return "Backup_Gap_Fill", ""
    return "Excluded_Unrelated", "Not a requested home textile or hospitality soft-goods category."


def row_key(row):
    return (row.get("Vendor Name"), row.get("Product URL"), row.get("Title"), row.get("Units shown on listing", ""))


def add_product_rows(rows, excluded, vendor_name, website, base_url, main_head, subcategory, product, collection_handle, source_note, visible_price=True, is_hospitality=False):
    title = clean_text(product.get("title"))
    product_type = clean_text(product.get("product_type"))
    p_url = product_url(base_url, product.get("handle", ""))
    classification, reason = classify_product(title, product_type, collection_handle, source_note, is_hospitality)
    page_text = product_page_text(p_url)
    material = extract_material(title, product_type, f"{page_text} {product.get('body_html', '')}", product.get("tags", []))
    hidden_price = not visible_price and any(v.get("price") not in (None, "") for v in product.get("variants", []))
    notes = product_notes(product, source_note, hidden_price=hidden_price)
    variants = product.get("variants") or []
    unit_variants = []
    seen_units = set()
    for variant in variants:
        unit = variant_unit_text(variant.get("title"))
        if unit == "Not visible":
            continue
        price = money(variant.get("price")) if visible_price else "Not visible"
        key = (unit, price)
        if key not in seen_units:
            seen_units.add(key)
            unit_variants.append((unit, price))
    # Split only when unit/pack/case quantities are explicit. Plain size/color variants stay one row.
    split_units = unit_variants if len(unit_variants) > 1 else []
    if not split_units and unit_variants and re.search(r"\b(set|pair|piece|pack|case|dozen)\b", unit_variants[0][0], re.I):
        split_units = unit_variants

    target_rows = []
    if classification == "Excluded_Unrelated":
        excluded.append({
            "Vendor Name": vendor_name,
            "Website": website,
            "Product URL or Source URL": p_url,
            "Main Head": main_head,
            "Subcategory": subcategory,
            "Title": title,
            "Reason Excluded": reason,
            "Notes": notes or source_note,
            "Date Checked": DATE_CHECKED,
        })
        return

    if split_units:
        for unit, price in split_units:
            target_rows.append((unit, price))
    else:
        target_rows.append(("Not visible", listing_price(product, visible_price=visible_price)))

    for unit, price in target_rows:
        rows.append({
            "Vendor Name": vendor_name,
            "Website": website,
            "Product URL": p_url,
            "Main Head": main_head,
            "Subcategory": subcategory,
            "Title": title,
            "Prices": price,
            "Units shown on listing": unit,
            "Product material": material,
            "Classification": classification,
            "Notes": notes,
            "Date Checked": DATE_CHECKED,
        })


def dedupe_rows(rows):
    out = OrderedDict()
    for row in rows:
        key = row_key(row)
        if key not in out:
            out[key] = row
        else:
            # Prefer rows with visible material/units/prices.
            old = out[key]
            for field in ["Product material", "Prices", "Units shown on listing", "Notes"]:
                if old.get(field) == "Not visible" and row.get(field) != "Not visible":
                    old[field] = row[field]
    return list(out.values())


def scrape_category(rows, excluded, source_log, vendor_name, website, base_url, main_head, subcategory, handle, source_type, supports, visible_price=True, is_hospitality=False):
    collection_url, products = collect_collection_products(base_url, handle)
    source_log.append({
        "Vendor Name": vendor_name,
        "Source URL": collection_url,
        "Source Type": source_type,
        "What This Source Supports": supports,
        "Date Checked": DATE_CHECKED,
    })
    for product in products:
        add_product_rows(rows, excluded, vendor_name, website, base_url, main_head, subcategory, product, handle, source_type, visible_price=visible_price, is_hospitality=is_hospitality)
    time.sleep(0.2)


def scrape_product(rows, excluded, source_log, vendor_name, website, base_url, main_head, subcategory, handle, source_type, supports, visible_price=True, is_hospitality=False):
    p_url = product_url(base_url, handle)
    product = None
    try:
        product = fetch_json(urllib.parse.urljoin(base_url, f"/products/{handle}.json")).get("product")
    except Exception:
        try:
            text = fetch_text(p_url)
            tree = lxml_html.fromstring(text)
            title = clean_text(" ".join(tree.xpath("//h1//text()"))) or handle.replace("-", " ").title()
            product = {"title": title, "handle": handle, "body_html": clean_text(" ".join(tree.xpath("//main//text()"))), "product_type": "", "tags": [], "variants": [], "_visible_only": True}
        except Exception as exc:
            print(f"WARN product failed {p_url}: {exc}", file=sys.stderr)
            return
    source_log.append({
        "Vendor Name": vendor_name,
        "Source URL": p_url,
        "Source Type": source_type,
        "What This Source Supports": supports,
        "Date Checked": DATE_CHECKED,
    })
    add_product_rows(rows, excluded, vendor_name, website, base_url, main_head, subcategory, product, handle, source_type, visible_price=visible_price, is_hospitality=is_hospitality)


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    batch = pd.read_excel(INPUT_XLSX, sheet_name="Sheet1").fillna("")

    rows = []
    excluded = []
    source_log = []

    for _, vendor in batch.iterrows():
        vendor_name = str(vendor["Vendor Name"]).strip()
        website = str(vendor["Website"]).strip()
        source_log.append({
            "Vendor Name": vendor_name,
            "Source URL": website,
            "Source Type": "Vendor website/homepage",
            "What This Source Supports": "Vendor-owned site and navigation/category evidence.",
            "Date Checked": DATE_CHECKED,
        })
        evidence = str(vendor.get("B2B Evidence URL", "")).strip()
        if evidence:
            source_log.append({
                "Vendor Name": vendor_name,
                "Source URL": evidence,
                "Source Type": "B2B/wholesale/hospitality evidence URL from batch",
                "What This Source Supports": "Hospitality/B2B relevance noted in uploaded batch.",
                "Date Checked": DATE_CHECKED,
            })

    # Standard Textile Home: vendor-owned DTC pages plus listed hospitality/interiors evidence.
    st_name = "Standard Textile Home"
    st_site = "https://standardtextilehome.com"
    st_sources = [
        ("Bedding", "Sheets & Pillowcases", "sheets", "DTC category page", "Visible sheet and pillowcase listings.", True, False),
        ("Bedding", "Duvet Sets, Top Covers & Quilts", "duvets-shams-coverlets", "DTC category page", "Visible duvet cover/set, top cover, sham, and quilt listings.", True, False),
        ("Bedding", "Throws & Blankets", "throw-blankets", "DTC category page", "Visible blanket, throw, quilt, and duvet insert listings.", True, False),
        ("Pillows, Inserts & Toppers", "Pillows", "pillows", "DTC category page", "Visible pillow and pillow protector listings.", True, False),
        ("Pillows, Inserts & Toppers", "Duvet Inserts", "duvet-insert", "DTC category page", "Visible duvet insert listings.", True, False),
        ("Pillows, Inserts & Toppers", "Mattress Toppers", "mattress-toppers", "DTC category page", "Visible mattress topper/featherbed listings.", True, False),
        ("Bath", "Towels", "towels", "DTC category page", "Visible bath towel, hand towel, washcloth, and pool towel listings.", True, False),
        ("Bath", "Pool Towels", "pool-towels", "DTC category page", "Visible pool towel listings.", True, False),
    ]
    for args in st_sources:
        scrape_category(rows, excluded, source_log, st_name, st_site, st_site, *args)
    scrape_product(rows, excluded, source_log, st_name, st_site, st_site, "Bedding", "Bed Wrap / Bed Skirt Alternative", "circa-bed-wrap", "DTC product page", "Visible bed wrap product listing.", visible_price=True, is_hospitality=False)

    # WestPoint Home: DTC category pages.
    wph_name = "WestPoint Home"
    wph_site = "https://westpointhome.com"
    wph_sources = [
        ("Bedding", "Sheets & Pillowcases", "sheet-sets", "DTC category page", "Visible sheet and pillowcase listings.", True, False),
        ("Bedding", "Comforters", "comforters", "DTC category page", "Visible comforter listings.", True, False),
        ("Bedding", "Coverlets & Quilts", "coverlets-quilts", "DTC category page", "Visible coverlet and quilt listings.", True, False),
        ("Bedding", "Mattress Pads & Toppers", "bedding-basics", "DTC category page", "Visible mattress pad/protector and bedding basics listings.", True, False),
        ("Bedding", "Pillows", "bed-pillows", "DTC category page", "Visible pillow and pillow protector listings.", True, False),
        ("Bedding", "Bed Skirts", "bed-skirts", "DTC category page", "Visible bed skirt listings.", True, False),
        ("Bath", "Towels", "towels", "DTC category page", "Visible towel and wash cloth listings.", True, False),
        ("Bath", "Bath Rugs", "bath-rugs", "DTC category page", "Visible bath rug listings.", True, False),
        ("Bath", "Bath Robes", "bath-robes", "DTC category page", "Visible bath robe listings.", True, False),
        ("Decor", "Table Linens", "table-linens", "DTC category page", "Visible table linen/tablecloth listings.", True, False),
        ("Bedding", "Blankets & Throws", "blanket-throws", "DTC category page", "Visible blanket and throw listings.", True, False),
    ]
    for args in wph_sources:
        scrape_category(rows, excluded, source_log, wph_name, wph_site, wph_site, *args)

    # WestPoint Hospitality: hospitality collection pages. Prices are not visible in rendered public pages.
    wh_site = "https://www.westpointhospitality.com"
    wh_sources = [
        ("Hospitality Products", "Sheets", "sheets", "Hospitality category page", "Visible hospitality sheet collection listings.", False, True),
        ("Hospitality Products", "Bath Towels", "bath-towels", "Hospitality category page", "Visible hospitality bath towel listings.", False, True),
        ("Hospitality Products", "Pool Towels", "pool-towels", "Hospitality category page", "Visible hospitality pool towel listings.", False, True),
        ("Hospitality Products", "Box Spring Wraps", "box-spring-wraps", "Hospitality category page", "Visible hospitality bed-wrap listings.", False, True),
        ("Hospitality Products", "Comforters", "comforters", "Hospitality category page", "Visible hospitality comforter listings.", False, True),
        ("Hospitality Products", "Cotton Blankets", "cotton-blankets", "Hospitality category page", "Visible hospitality cotton blanket listings.", False, True),
        ("Hospitality Products", "Cotton Blankets / Throws", "cotton-blankets-throws", "Hospitality category page", "Visible hospitality blanket/throw listings.", False, True),
        ("Hospitality Products", "Coverlets", "coverlets", "Hospitality category page", "Visible hospitality coverlet listings.", False, True),
        ("Hospitality Products", "Duvet Covers", "duvet-covers", "Hospitality category page", "Visible hospitality duvet cover listings.", False, True),
        ("Hospitality Products", "Filled Blankets", "filled-blankets", "Hospitality category page", "Visible hospitality filled blanket listings.", False, True),
        ("Hospitality Products", "Filled Blankets / Comforters / Inserts", "filled-blankets-comforters-inserts", "Hospitality category page", "Visible hospitality filled blanket/comforter/insert listings.", False, True),
        ("Hospitality Products", "Fleece Blankets", "fleece-blankets", "Hospitality category page", "Visible hospitality fleece blanket listings.", False, True),
        ("Hospitality Products", "Mattress Encasements", "mattress-encasements", "Hospitality category page", "Visible hospitality mattress encasement listings.", False, True),
        ("Hospitality Products", "Mattress Pads", "mattress-pads", "Hospitality category page", "Visible hospitality mattress pad listings.", False, True),
        ("Hospitality Products", "Mattress Pads / Protectors / Encasements", "mattress-pads-protectors-encasements", "Hospitality category page", "Visible hospitality mattress protection listings.", False, True),
        ("Hospitality Products", "Mattress Protectors", "mattress-protectors", "Hospitality category page", "Visible hospitality mattress protector listings.", False, True),
        ("Hospitality Products", "Pillow Protectors", "pillow-protectors", "Hospitality category page", "Visible hospitality pillow protector listings.", False, True),
        ("Hospitality Products", "Pillows", "pillows", "Hospitality category page", "Visible hospitality pillow listings.", False, True),
        ("Hospitality Products", "Pillows / Protectors", "pillows-protectors", "Hospitality category page", "Visible hospitality pillow/protector listings.", False, True),
        ("Hospitality Products", "Polyester Blankets", "polyester-blankets", "Hospitality category page", "Visible hospitality polyester blanket listings.", False, True),
        ("Hospitality Products", "Room Essentials", "room-essentials", "Hospitality category page", "Visible hospitality room-essential soft goods listings.", False, True),
    ]
    for args in wh_sources:
        scrape_category(rows, excluded, source_log, wph_name, wph_site, wh_site, *args)

    rows = dedupe_rows(rows)
    excluded = list(OrderedDict(((r["Vendor Name"], r["Product URL or Source URL"], r["Title"]), r) for r in excluded).values())

    core = [r for r in rows if r["Classification"] == "Core_Utopia_Overlap"]
    backup = [r for r in rows if r["Classification"] == "Backup_Gap_Fill"]

    outputs = {
        "core": core,
        "backup": backup,
        "excluded": excluded,
        "source_log": source_log,
    }
    (OUT_DIR / "scrape_output.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_specs = [
        ("core.csv", core),
        ("backup.csv", backup),
        ("excluded.csv", excluded),
        ("source_log.csv", source_log),
    ]
    for filename, data in csv_specs:
        if not data:
            continue
        with (OUT_DIR / filename).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)

    qc = {
        "core_rows": len(core),
        "backup_rows": len(backup),
        "excluded_rows": len(excluded),
        "source_log_rows": len(source_log),
        "missing_vendor_name": sum(1 for r in rows if not r.get("Vendor Name")),
        "missing_product_url": sum(1 for r in rows if not r.get("Product URL")),
        "missing_values_not_visible_used": True,
        "vendor_relevant_counts": {},
        "vendor_availability_flags": {},
    }
    for vendor_name in sorted(set(r["Vendor Name"] for r in rows)):
        vendor_rows = [r for r in rows if r["Vendor Name"] == vendor_name]
        qc["vendor_relevant_counts"][vendor_name] = len(vendor_rows)
        total = max(len(vendor_rows), 1)
        mostly_missing = {
            field: sum(1 for r in vendor_rows if r.get(field) == "Not visible") / total >= 0.6
            for field in ["Prices", "Units shown on listing", "Product material"]
        }
        qc["vendor_availability_flags"][vendor_name] = mostly_missing
    (OUT_DIR / "qc.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(qc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()
