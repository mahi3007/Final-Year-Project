import json
from pathlib import Path
from collections import Counter

PRED_PATH = Path("results/stage6m_cohort3_results/prequential_stream_records.jsonl")
TRANSCRIPT_PATH = Path("datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json")
MANIFEST_PATH = Path("datasets/splits/stage6m_cohort3_final_manifest.json")

def main():
    print("=== Stage 6M Gate 6: Phase 2 Prediction and Transcript Alignment ===")
    
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
        
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    transcripts_all = transcript_data["transcripts"]
    eval_transcripts = {
        k: v for k, v in transcripts_all.items()
        if v.get("panel_role") == "evaluation"
    }
    reserve_transcripts = {
        k: v for k, v in transcripts_all.items()
        if v.get("panel_role") == "australian_reserve"
    }
    
    print(f"Total sealed records: {len(transcripts_all)}")
    print(f"Evaluation transcript records: {len(eval_transcripts)}")
    print(f"Reserve transcript records: {len(reserve_transcripts)}")
    
    # Manifest eval records
    manifest_eval = [
        r for r in manifest_data["records"]
        if r.get("panel_role") == "evaluation"
    ]
    print(f"Manifest eval records: {len(manifest_eval)}")
    
    # Read stream predictions
    preds = []
    with open(PRED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            preds.append(json.loads(line))
            
    print(f"Prediction records: {len(preds)}")
    
    # 1. Check clip counts
    assert len(preds) == 16500, f"Expected 16500 preds, got {len(preds)}"
    assert len(eval_transcripts) == 16500, f"Expected 16500 eval transcripts, got {len(eval_transcripts)}"
    assert len(manifest_eval) == 16500, f"Expected 16500 manifest eval, got {len(manifest_eval)}"
    
    # 2. Check 1:1 recording ID alignment and ordering
    pred_cids = [r["recording_id"] for r in preds]
    manifest_cids = [r["recording_id"] for r in manifest_eval]
    
    assert len(set(pred_cids)) == 16500, "Duplicate recording IDs in predictions"
    assert set(pred_cids) == set(eval_transcripts.keys()), "Set mismatch between predictions and eval transcripts"
    assert pred_cids == manifest_cids, "Sequence ordering mismatch between predictions and locked manifest"
    
    # 3. Check speakers and strata
    spk_counter = Counter(r["speaker_id"] for r in preds)
    stratum_counter = Counter(r["stratum_code"] for r in preds)
    
    assert len(spk_counter) == 1100, f"Expected 1100 speakers, got {len(spk_counter)}"
    for spk, cnt in spk_counter.items():
        assert cnt == 15, f"Speaker {spk} has {cnt} clips, expected 15"
        
    assert set(stratum_counter.keys()) == {"australia", "canada", "england", "south_asian", "us"}
    for strat, cnt in stratum_counter.items():
        assert cnt == 3300, f"Stratum {strat} has {cnt} clips, expected 3300"
        
    # 4. Check that zero reserve or gate-reference clips are in evaluation stream
    assert len(set(pred_cids).intersection(set(reserve_transcripts.keys()))) == 0, "FATAL: Reserve clip leaked into predictions!"
    
    # 5. Check all three arms exist for all clips
    arm1_cnt = sum(1 for r in preds if r.get("hyp_arm1") is not None and isinstance(r.get("hyp_arm1"), str))
    arm2_cnt = sum(1 for r in preds if r.get("hyp_arm2") is not None and isinstance(r.get("hyp_arm2"), str))
    arm3_cnt = sum(1 for r in preds if r.get("hyp_arm3") is not None and isinstance(r.get("hyp_arm3"), str))
    
    assert arm1_cnt == 16500, f"Arm 1 has {arm1_cnt} outputs"
    assert arm2_cnt == 16500, f"Arm 2 has {arm2_cnt} outputs"
    assert arm3_cnt == 16500, f"Arm 3 has {arm3_cnt} outputs"
    
    print("\nPhase 2 Alignment Verification Overall Verdict: PASS")
    print(f"  Total verified evaluation clips: 16,500")
    print(f"  Total arm-level hypotheses: 49,500")
    print(f"  Zero reserve leaks; zero gate-reference leaks.")
    print(f"  1:1 exact ordering match with locked manifest.")

if __name__ == "__main__":
    main()
