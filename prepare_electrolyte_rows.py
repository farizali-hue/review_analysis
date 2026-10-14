import csv
import json
from pathlib import Path


INPUT = Path(r"D:\codex_variation_analysis\outputs\claims-electrolyte_img.csv")
OUTPUT = Path(r"D:\analysis\electrolyte_rows.json")


def main():
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"rows={len(rows)}")
    print(OUTPUT)


if __name__ == "__main__":
    main()
