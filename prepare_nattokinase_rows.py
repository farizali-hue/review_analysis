import csv
import json
from pathlib import Path


SOURCE = Path(r"D:\codex_variation_analysis\outputs\claims-Nottokinase.csv")
OUT = Path(r"D:\analysis\nattokinase_rows.json")


def clean(value):
    return " ".join((value or "").replace("\ufeff", "").split())


with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
    rows = [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]

OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(rows)} rows to {OUT}")
