import sys
import json
import time
import math
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any

sys.path.insert(0, ".")

import numpy as np
import pandas as pd

from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    run_confirmatory_paired_cluster_inference_v15,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS
)

PRED_PATH = Path("results/stage6m_cohort3_results/prequential_stream_records.jsonl")
TRANSCRIPT_PATH = Path("datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json")

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== Stage 6M Gate 6: Official Offline Scoring Execution ===")
    t0 = time.time()
    
    # Load sealed evaluation transcripts (strictly inside memory)
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
        
    eval_transcripts = {
        k: v for k, v in transcript_data["transcripts"].items()
        if v.get("panel_role") == "evaluation"
    }
    
    assert len(eval_transcripts) == 16500, f"Expected 16500 eval transcripts, got {len(eval_transcripts)}"
    
    # Load predictions
    preds = []
    with open(PRED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            preds.append(json.loads(line))
            
    assert len(preds) == 16500, f"Expected 16500 predictions, got {len(preds)}"
    
    # Utterance-level scoring
    print("[Step 1] Computing Levenshtein edit counts for 16,500 clips across 3 arms (49,500 evaluations)...")
    
    speaker_data = defaultdict(lambda: {
        "speaker_id": "",
        "stratum": "",
        "stratum_code": "",
        "wc": 0,
        "err1": 0,
        "err2": 0,
        "err3": 0,
        "clip_count": 0
    })
    
    utterance_results = []
    
    for idx, p in enumerate(preds):
        cid = p["recording_id"]
        spk = p["speaker_id"]
        strat_code = p["stratum_code"]
        
        tr_rec = eval_transcripts[cid]
        ref_text = tr_rec["transcript"]
        accent_group = tr_rec["accent_group"]
        
        hyp1 = p["hyp_arm1"]
        hyp2 = p["hyp_arm2"]
        hyp3 = p["hyp_arm3"]
        
        m1 = compute_utterance_metrics(ref_text, hyp1, normalize=True)
        m2 = compute_utterance_metrics(ref_text, hyp2, normalize=True)
        m3 = compute_utterance_metrics(ref_text, hyp3, normalize=True)
        
        wc = m1.reference_length  # Reference length is identical across arms
        err1 = m1.total_errors
        err2 = m2.total_errors
        err3 = m3.total_errors
        
        # Aggregate to speaker level
        s_entry = speaker_data[spk]
        s_entry["speaker_id"] = spk
        s_entry["stratum"] = accent_group
        s_entry["stratum_code"] = strat_code
        s_entry["wc"] += wc
        s_entry["err1"] += err1
        s_entry["err2"] += err2
        s_entry["err3"] += err3
        s_entry["clip_count"] += 1
        
        if (idx + 1) % 4125 == 0:
            print(f"  Processed {idx + 1:5d} / 16,500 clips ({(idx + 1)/165.0:.1f}%)")
            
    # Verify speaker aggregation
    assert len(speaker_data) == 1100, f"Expected 1100 speakers, got {len(speaker_data)}"
    speaker_records = list(speaker_data.values())
    for s in speaker_records:
        assert s["clip_count"] == 15, f"Speaker {s['speaker_id']} has {s['clip_count']} clips (expected 15)"
        assert s["wc"] > 0, f"Speaker {s['speaker_id']} has 0 reference words!"
        
    print(f"\n[Step 2] Utterance evaluation completed. Total words across evaluation cohort: {sum(s['wc'] for s in speaker_records)}")
    
    # Execute Registered v1.5 Five-Stratum Inferential Analysis
    print("\n[Step 3] Executing Registered Confirmatory Inference (B = 20,000 bootstrap, M = 8 Bonferroni)...")
    
    conf_report = run_confirmatory_paired_cluster_inference_v15(
        speaker_records=speaker_records,
        num_bootstrap_replicates=20000,
        seed=42,
        alpha_family=0.05,
        epsilon_g_margin_pp=2.00,
        epsilon_d_margin_pp=0.00,
        confirmatory_accents=FIVE_STRATUM_CONFIRMATORY_ACCENTS
    )
    
    t_elapsed = time.time() - t0
    print(f"Inference completed in {t_elapsed:.2f} seconds.")
    
    # Print Headline Results
    print("\n" + "=" * 80)
    print("STAGE 6M GATE 6 CONFIRMATORY INFERENCE HEADLINE RESULTS")
    print("=" * 80)
    print(f"Overall Confirmatory Verdict: {conf_report.verdict}")
    print(f"All M=8 Confirmatory Criteria Passed: {conf_report.all_criteria_passed}")
    print("-" * 80)
    print(f"Corpus Pooled WER:")
    print(f"  Arm 1 (Static Baseline):     {conf_report.corpus_wer_arm1_static:6.2f}%")
    print(f"  Arm 2 (Ungated SUTA):        {conf_report.corpus_wer_arm2_ungated:6.2f}%")
    print(f"  Arm 3 (DSG-Gated SUTA):      {conf_report.corpus_wer_arm3_dsg:6.2f}%")
    print(f"Delta vs Static (Arm 3 - Arm 1):  {conf_report.delta_static_pp:+6.2f} pp")
    print(f"Delta vs Ungated (Arm 3 - Arm 2): {conf_report.delta_ungated_pp:+6.2f} pp")
    print("-" * 80)
    print("Five-Stratum Accent Breakdown:")
    for acc in sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS)):
        w1 = conf_report.accent_wers_arm1[acc]
        w2 = conf_report.accent_wers_arm2[acc]
        w3 = conf_report.accent_wers_arm3[acc]
        d = conf_report.accent_deltas_pp[acc]
        print(f"  {acc:20s} | Arm 1: {w1:5.2f}% | Arm 2: {w2:5.2f}% | Arm 3: {w3:5.2f}% | Delta: {d:+5.2f} pp")
    print("-" * 80)
    print(f"Accent Disparity (Max WER - Min WER):")
    print(f"  Arm 1 Disparity:             {conf_report.disparity_arm1_pp:6.2f} pp")
    print(f"  Arm 2 Disparity:             {conf_report.disparity_arm2_pp:6.2f} pp")
    print(f"  Arm 3 Disparity:             {conf_report.disparity_arm3_dsg if hasattr(conf_report, 'disparity_arm3_dsg') else conf_report.disparity_arm3_pp:6.2f} pp")
    print(f"Delta Disparity (Arm 3 - Arm 1): {conf_report.delta_disparity_pp:+6.2f} pp")
    print("=" * 80)
    print("EVALUATION OF M=8 CONFIRMATORY CRITERIA:")
    for cid, cr in conf_report.criteria.items():
        status_str = "PASS" if cr.is_success else "FAIL"
        print(f"  [{status_str}] {cr.criterion_name}")
        print(f"         Est: {cr.point_estimate:+.2f} pp | Adj UCB (99.375%): {cr.adjusted_ucb:+.2f} pp | Adj p: {cr.adjusted_p_value:.6f}")
        print(f"         Detail: {cr.interpretation}")
    print("=" * 80)
    
    # Save machine-readable JSON report
    report_dict = conf_report.to_dict()
    report_dict["report_id"] = "STAGE6M-GATE6-OFFLINE-SCORING-REPORT"
    report_dict["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    report_dict["governing_authorization"] = "STAGE6M-GATE6-AUTH-DECISION-20261108"
    report_dict["governing_protocol"] = "Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)"
    report_dict["execution_platform"] = "Local Offline Compute Environment"
    report_dict["evaluation_cohort_scale"] = {
        "total_clips": 16500,
        "total_speakers": 1100,
        "clips_per_speaker": 15,
        "total_reference_words": sum(s["wc"] for s in speaker_records),
        "confirmatory_strata": sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))
    }
    
    json_path = Path("reports/stage6m/stage6m_gate6_offline_scoring_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    print(f"\n[Artifact] Wrote JSON report: {json_path}")

    # Save Output Catalogue
    cat = {
        "catalogue_id": "STAGE6M-GATE6-OUTPUT-CATALOGUE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "stage6m_gate6_offline_scoring_report.json": {
                "rel_path": str(json_path.as_posix()),
                "bytes": json_path.stat().st_size,
                "sha256": compute_sha256(json_path)
            }
        }
    }
    cat_path = Path("reports/stage6m/stage6m_gate6_output_catalogue.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
    print(f"[Artifact] Wrote Output Catalogue: {cat_path}")
    
    return conf_report, speaker_records

if __name__ == "__main__":
    main()
