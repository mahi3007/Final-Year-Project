import json
from pathlib import Path
from collections import Counter

STREAM_FILE = Path("results/stage6m_cohort3_results/prequential_stream_records.jsonl")
ONLINE_MANIFEST = Path("datasets/splits/stage6m_cohort3_online_inference_manifest.json")

print("=== Starting Task 3: Three-Arm Prediction Audit ===")

assert STREAM_FILE.exists(), f"Missing stream file: {STREAM_FILE}"
assert ONLINE_MANIFEST.exists(), f"Missing online manifest: {ONLINE_MANIFEST}"

with open(ONLINE_MANIFEST, "r", encoding="utf-8") as f:
    online_data = json.load(f)

eval_manifest_records = [
    r for r in online_data.get("records", [])
    if r.get("panel_role") == "evaluation"
]

print(f"Manifest registered evaluation clips: {len(eval_manifest_records)}")

clip_ids = []
window_ids = set()
strata_counts = Counter()
speaker_counts = Counter()
arm1_count = 0
arm2_count = 0
arm3_count = 0

total_lines = 0
order_valid = True

manifest_clip_order = [r["recording_id"] for r in eval_manifest_records]

with open(STREAM_FILE, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        total_lines += 1
        rec = json.loads(line)
        cid = rec.get("recording_id")
        win = rec.get("window_idx")
        
        clip_ids.append(cid)
        window_ids.add(win)
        
        # Verify predictions exist and are non-None strings
        hyp1 = rec.get("hyp_arm1")
        hyp2 = rec.get("hyp_arm2")
        hyp3 = rec.get("hyp_arm3")
        
        if hyp1 is not None and isinstance(hyp1, str):
            arm1_count += 1
        if hyp2 is not None and isinstance(hyp2, str):
            arm2_count += 1
        if hyp3 is not None and isinstance(hyp3, str):
            arm3_count += 1
            
        stratum = rec.get("stratum_code")
        spk = rec.get("speaker_id")
        strata_counts[stratum] += 1
        speaker_counts[spk] += 1
        
        # Check ordering matches manifest
        if idx < len(manifest_clip_order):
            if cid != manifest_clip_order[idx]:
                order_valid = False

unique_clips = set(clip_ids)
duplicates = len(clip_ids) - len(unique_clips)

print(f"Total stream lines: {total_lines}")
print(f"Unique recording IDs: {len(unique_clips)}")
print(f"Duplicates: {duplicates}")
print(f"Arm 1 outputs: {arm1_count}")
print(f"Arm 2 outputs: {arm2_count}")
print(f"Arm 3 outputs: {arm3_count}")
print(f"Total arm-level outputs: {arm1_count + arm2_count + arm3_count}")
print(f"Total windows represented: {len(window_ids)} (min: {min(window_ids)}, max: {max(window_ids)})")
print(f"Strata distribution: {dict(strata_counts)}")
print(f"Unique speakers: {len(speaker_counts)}")
print(f"Ordering strictly matches manifest: {order_valid}")

# Assertions
assert total_lines == 16500, f"Expected 16500 lines, got {total_lines}"
assert len(unique_clips) == 16500, f"Expected 16500 unique clips, got {len(unique_clips)}"
assert duplicates == 0, f"Expected 0 duplicates, got {duplicates}"
assert arm1_count == 16500, f"Expected 16500 Arm 1 outputs, got {arm1_count}"
assert arm2_count == 16500, f"Expected 16500 Arm 2 outputs, got {arm2_count}"
assert arm3_count == 16500, f"Expected 16500 Arm 3 outputs, got {arm3_count}"
assert arm1_count + arm2_count + arm3_count == 49500, "Expected 49500 arm outputs"
assert len(window_ids) == 4125, f"Expected 4125 windows, got {len(window_ids)}"
assert min(window_ids) == 0 and max(window_ids) == 4124, "Window indexing mismatch"
assert len(speaker_counts) == 1100, f"Expected 1100 speakers, got {len(speaker_counts)}"
for st, cnt in strata_counts.items():
    assert cnt == 3300, f"Expected 3300 clips per stratum, got {cnt} for {st}"
for spk, cnt in speaker_counts.items():
    assert cnt == 15, f"Expected 15 clips per speaker, got {cnt} for {spk}"
assert order_valid == True, "Stream record order does not match locked manifest order"

print("\n>>> ALL TASK 3 ASSERTIONS PASSED BITWISE EXACT <<<")
