import hashlib
from pathlib import Path
import json

EXPECTED_DIGESTS = {
    "results/stage6m_cohort3_results/prequential_stream_records.jsonl": "42fc02cefc00f4ffd40022feade68aec8dd915818afde46ce71bd534c2b72163",
    "datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json": "f427ae7fbf386f77b0795cc1fa33b2f7831c89f89ecfce7fa30036cde5c5223e",
    "datasets/splits/stage6m_cohort3_final_manifest.json": "171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0",
    "datasets/splits/stage6m_cohort3_online_inference_manifest.json": "0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1",
    "datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv": "b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5"
}

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== Stage 6M Gate 6: Phase 1 Immutable Input Verification ===")
    all_matched = True
    results = {}
    
    for rel_path, exp_hash in EXPECTED_DIGESTS.items():
        p = Path(rel_path)
        if not p.exists():
            print(f"[MISSING] {rel_path}")
            all_matched = False
            results[rel_path] = {"status": "MISSING"}
            continue
        act_hash = compute_sha256(p)
        matched = (act_hash == exp_hash)
        status = "MATCH" if matched else "MISMATCH"
        print(f"[{status}] {p.name}")
        print(f"  Actual:   {act_hash}")
        print(f"  Expected: {exp_hash}")
        results[rel_path] = {
            "status": status,
            "actual_sha256": act_hash,
            "expected_sha256": exp_hash,
            "bytes": p.stat().st_size
        }
        if not matched:
            all_matched = False
            
    print("\nPhase 1 Input Verification Overall Verdict:", "PASS" if all_matched else "FAIL")
    assert all_matched, "FATAL FAIL-CLOSED: Phase 1 input hash mismatch!"
    return results

if __name__ == "__main__":
    main()
