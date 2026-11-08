import hashlib
import json
from pathlib import Path

CATALOGUE_PATH = Path("reports/stage6m/stage6m_gate5_output_catalogue.json")

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

print("=== Starting Task 5: Output Integrity Verification ===")

with open(CATALOGUE_PATH, "r", encoding="utf-8") as f:
    catalogue = json.load(f)

targets = [
    ("prequential_stream_records.jsonl", Path("results/stage6m_cohort3_results/prequential_stream_records.jsonl")),
    ("stage6m_cohort3_results.tar.gz", Path("results/stage6m_cohort3_results/stage6m_cohort3_results.tar.gz")),
    ("checkpoint_latest.json", Path("checkpoints/stage6m_cohort3/checkpoint_latest.json")),
    ("stage6m_gate5_execution_start_verification_report.json", Path("reports/stage6m/stage6m_gate5_execution_start_verification_report.json")),
    ("stage6m_gate5_confirmatory_execution.log", Path("reports/stage6m/stage6m_gate5_confirmatory_execution.log")),
]

all_matched = True

for key, p in targets:
    if not p.exists():
        print(f"[MISSING] {key} at {p}")
        all_matched = False
        continue
    actual_hash = compute_sha256(p)
    actual_size = p.stat().st_size
    expected = catalogue["artifacts"].get(key)
    if not expected:
        print(f"[UNEXPECTED] {key} not found in catalogue")
        all_matched = False
        continue
    expected_hash = expected["sha256"]
    expected_size = expected["bytes"]
    
    match = (actual_hash == expected_hash) and (actual_size == expected_size)
    print(f"[{'MATCH' if match else 'MISMATCH'}] {key}")
    print(f"  Actual:   {actual_hash} ({actual_size} B)")
    print(f"  Expected: {expected_hash} ({expected_size} B)")
    if not match:
        all_matched = False

# Also verify state_win_4124.pt
pt_path = Path("checkpoints/stage6m_cohort3/state_win_4124.pt")
pt_hash = compute_sha256(pt_path)
pt_size = pt_path.stat().st_size
expected_pt_hash = "cd18e4e890240f66c11db465c8514463930939a587645fe1c56819314a174cfb"
expected_pt_size = 1113000
pt_match = (pt_hash == expected_pt_hash) and (pt_size == expected_pt_size)
print(f"[{'MATCH' if pt_match else 'MISMATCH'}] state_win_4124.pt")
print(f"  Actual:   {pt_hash} ({pt_size} B)")
print(f"  Expected: {expected_pt_hash} ({expected_pt_size} B)")
if not pt_match:
    all_matched = False

print(f"\nOverall Output Integrity Status: {'PASS' if all_matched else 'FAIL'}")
assert all_matched, "Cryptographic digest mismatch detected!"
