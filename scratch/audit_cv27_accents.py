import csv
from collections import Counter
from pathlib import Path

tsv_path = Path("datasets/external/common_voice_27_intermediate/validated.tsv")

accent_counter = Counter()
variant_counter = Counter()
multi_accent_count = 0
empty_accent_count = 0
total_rows = 0

print(f"Auditing accent taxonomy in: {tsv_path}...")
with open(tsv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        total_rows += 1
        acc = (r.get("accents") or r.get("accent") or "").strip()
        var = (r.get("variant") or "").strip()
        
        if not acc:
            empty_accent_count += 1
        else:
            if "|" in acc:
                multi_accent_count += 1
            accent_counter[acc] += 1
            
        if var:
            variant_counter[var] += 1

print(f"\nTotal Rows: {total_rows:,}")
print(f"Empty accents: {empty_accent_count:,} ({empty_accent_count/total_rows*100:.1f}%)")
print(f"Compound/multi-accents (containing '|'): {multi_accent_count:,} ({multi_accent_count/total_rows*100:.1f}%)")
print(f"Distinct accent strings: {len(accent_counter):,}")
print(f"Distinct variants: {len(variant_counter):,}")

print("\n--- Top 30 Most Frequent Accent Values in CV27 ---")
for acc, count in accent_counter.most_common(30):
    print(f"  {count:8,d} | {acc}")

print("\n--- Frequency of Target Group Candidate Strings in CV27 ---")
target_candidates = [
    "us", "United States English",
    "england", "England English", "British English",
    "indian", "India and South Asia (India, Pakistan, Sri Lanka)", "India and South Asia English",
    "australia", "Australian English",
    "canada", "Canadian English",
    "ireland", "Irish English",
]
for tc in target_candidates:
    print(f"  Exact match '{tc}': {accent_counter.get(tc, 0):,}")
