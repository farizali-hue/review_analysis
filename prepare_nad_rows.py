from __future__ import annotations

import csv
import json
from pathlib import Path


SOURCE = Path(r"D:\codex_variation_analysis\outputs\claims-nad.csv")
OUT = Path(r"D:\analysis\nad_rows.json")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if any(marker in text for marker in ("â", "Ã", "�")):
        try:
            text = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    return (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\xa0", " ")
    )


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for idx, row in enumerate(reader, 2):
            record = {clean_text(k): clean_text(v) for k, v in row.items()}
            if record.get("asin") or record.get("url"):
                record["_source_row"] = idx
                rows.append(record)

    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
