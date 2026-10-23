import csv
from pathlib import Path

tsv_path = Path("datasets/external/common_voice_27/validated.tsv")
with open(tsv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    rows = list(reader)

print(f"Total rows in validated.tsv: {len(rows)}")
spk1_prefix = "fc22fd45"
spk2_prefix = "f3ea0447"

spk1_rows = [r for r in rows if r["client_id"].startswith(spk1_prefix)]
spk2_rows = [r for r in rows if r["client_id"].startswith(spk2_prefix)]

print(f"\n--- Speaker 1 ({spk1_prefix}) ---")
print(f"Total rows in TSV: {len(spk1_rows)}")
if spk1_rows:
    print(f"Full client_id: {spk1_rows[0]['client_id']}")
    for i, r in enumerate(spk1_rows, 1):
        acc = r.get("accents") or r.get("accent")
        words = len((r.get("sentence") or "").split())
        up = r.get("up_votes")
        down = r.get("down_votes")
        loc = r.get("locale")
        print(f"  Clip {i:2d}: up={up}, down={down}, loc={loc}, words={words}, accent={acc}, path={r.get('path')}")

print(f"\n--- Speaker 2 ({spk2_prefix}) ---")
print(f"Total rows in TSV: {len(spk2_rows)}")
if spk2_rows:
    print(f"Full client_id: {spk2_rows[0]['client_id']}")
    for i, r in enumerate(spk2_rows, 1):
        acc = r.get("accents") or r.get("accent")
        words = len((r.get("sentence") or "").split())
        up = r.get("up_votes")
        down = r.get("down_votes")
        loc = r.get("locale")
        print(f"  Clip {i:2d}: up={up}, down={down}, loc={loc}, words={words}, accent={acc}, path={r.get('path')}")
