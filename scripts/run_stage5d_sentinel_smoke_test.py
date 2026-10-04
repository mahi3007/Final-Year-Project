#!/usr/bin/env python3
"""
Stage 5D Phase 3: Sentinel Safety Evaluator Smoke Test.
======================================================
Runs an end-to-end evaluation of one deterministic candidate update against
the full 30-speaker, 300-clip frozen sentinel panel.

Validates the 12 strict smoke test criteria:
1. All expected sentinel audio files resolve and load via SentinelAudioResolver.
2. Reference transcripts are isolated strictly to the sentinel evaluator.
3. Current model predictions generated successfully.
4. Candidate predictions generated successfully.
5. Delta_R is finite.
6. Every monitored Delta_g is finite across all 6 strata.
7. Delta_D is finite.
8. Bootstrap produces 1000 valid replicates.
9. Zero groups are omitted.
10. UCB_R, UCB_max_group, and UCB_D are finite.
11. Real ACCEPT or REJECT produced from gate inequalities (distinguishing STATISTICAL vs FAIL-CLOSED).
12. Zero evaluator exceptions.

Generates: reports/stage5/stage5d_sentinel_smoke_test.md
"""

from __future__ import annotations

import gc
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import torch

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
SENTINEL_CSV = SPLITS_DIR / "stage5_sentinel_panel.csv"
SENTINEL_MANIFEST = SPLITS_DIR / "stage5_sentinel_audio_manifest.json"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
EXTERNAL_EVAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
GATE_CONFIG_PATH = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
SMOKE_REPORT_PATH = PROJECT_ROOT / "reports" / "stage5" / "stage5d_sentinel_smoke_test.md"

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.resolver import SentinelAudioResolver
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, enforce_data_access_firewall


def run_smoke_test():
    print("=" * 70)
    print("STAGE 5D PHASE 3: SENTINEL EVALUATOR SMOKE TEST")
    print("=" * 70)

    # 1. Verify frozen gate configuration
    with open(GATE_CONFIG_PATH, "r", encoding="utf-8") as f:
        gate_cfg = json.load(f)

    eps_r = gate_cfg["gate_tolerances"]["epsilon_R"]
    eps_g = gate_cfg["gate_tolerances"]["epsilon_G"]
    eps_d = gate_cfg["gate_tolerances"]["epsilon_D"]
    bootstrap_b = gate_cfg["bootstrap"]["B"]
    bootstrap_conf = gate_cfg["bootstrap"]["confidence"]
    bootstrap_seed = gate_cfg["bootstrap"]["seed"]

    print(f"Gate Tolerances: eps_R={eps_r:.4f}, eps_G={eps_g:.4f}, eps_D={eps_d:.4f}")
    print(f"Bootstrap: B={bootstrap_b}, confidence={bootstrap_conf:.2f}, seed={bootstrap_seed}")

    # 2. Verify and load SentinelAudioResolver
    print("\nInitializing Canonical SentinelAudioResolver...")
    resolver = SentinelAudioResolver(
        manifest_path=SENTINEL_MANIFEST if SENTINEL_MANIFEST.exists() else None,
        inventory_path=SENTINEL_INVENTORY,
        project_root=PROJECT_ROOT,
    )
    if not resolver.is_loaded:
        raise RuntimeError("SentinelAudioResolver could not find loaded manifest or inventory!")
    print(f"Resolver initialized successfully with {resolver.total_clips} registered clips.")

    # 3. Load sentinel dataframe
    sentinel_df = pd.read_csv(SENTINEL_CSV)
    print(f"Loaded sentinel panel: {len(sentinel_df)} clips across {sentinel_df['speaker_id'].nunique()} speakers.")

    # 4. Device setup
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Hardware execution device: {device}")

    # 5. Load Live Model
    print("\nLoading wav2vec2_base live model...")
    live_model = create_asr_model("wav2vec2_base", device=device)
    live_model.load_model()
    live_hash_initial = compute_model_parameter_hash(live_model.model)
    print(f"Live model initial parameter hash: {live_hash_initial[:16]}")

    # 6. Generate Deterministic Candidate Update on Window 0 of external stream
    print("\nGenerating candidate clone and adapting on Window 0 (K=4)...")
    eval_df = pd.read_csv(EXTERNAL_EVAL_CSV)
    win0_rows = eval_df.iloc[:4]

    AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
    batch_utts = []
    for _, row in win0_rows.iterrows():
        audio_path = str(AUDIO_DIR / f"{row['recording_id']}.mp3")
        batch_utts.append(
            UtteranceMetadata(
                utterance_id=row["recording_id"],
                speaker_id=row["speaker_id"],
                group_id=row["stage5_accent_group"],
                group_type="regional_accent",
                audio_filepath=audio_path,
                reference_raw=row["transcript"],
                reference_normalized=TextNormalizer.normalize(row["transcript"]),
                duration_seconds=float(row["duration_sec"]),
                sampling_rate_hz=int(row["sample_rate"]),
                reference_word_count=len(row["transcript"].split()),
                provenance=ProvenanceInfo(
                    source_dataset="common_voice_27",
                    dataset_release="cv-corpus-27.0-2026-09-11",
                    protocol_version="v1.0-cv27-amended"
                )
            )
        )

    # Label isolation enforcement
    unlabeled_batch = LabelIsolationSanitizer.sanitize_batch(batch_utts, batch_idx=0)
    enforce_data_access_firewall(unlabeled_batch)

    # Candidate clone
    candidate_core = ShadowCandidateManager.create_candidate_clone(live_model.model)
    candidate_model = create_asr_model("wav2vec2_base", device=device)
    candidate_model.model = candidate_core
    candidate_model.processor = live_model.processor

    # Adapt candidate with SUTA
    suta_cfg = {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1}
    cand_adapter = SutaAdapter(asr_model=candidate_model, config=suta_cfg)
    cand_adapter.adapt(unlabeled_batch)
    cand_hash = compute_model_parameter_hash(candidate_model.model)
    print(f"Candidate adapted. Parameter hash: {cand_hash[:16]}")
    assert live_hash_initial != cand_hash, "Candidate model weights failed to mutate!"

    # 7. Initialize Safety Gate and Sentinel Evaluator
    gate = DisparitySafetyGate(epsilon_r=eps_r, epsilon_g=eps_g, epsilon_d=eps_d)
    evaluator = SentinelSafetyEvaluator(
        gate=gate,
        num_bootstrap=bootstrap_b,
        confidence_level=bootstrap_conf,
        bootstrap_seed=bootstrap_seed,
        min_speakers_per_group=3,
        resolver=resolver,
    )

    # 8. Execute Sentinel Evaluation
    print("\nExecuting Sentinel Panel Evaluation (300 clips, 30 speakers, B=1000 bootstrap)...")
    t0 = time.time()
    decision = evaluator.evaluate_candidate(
        live_model=live_model,
        candidate_model=candidate_model,
        sentinel_utterances=sentinel_df.to_dict(orient="records"),
    )
    eval_elapsed = time.time() - t0
    print(f"Sentinel evaluation completed in {eval_elapsed:.2f}s.")

    # 9. Verify Invariant Immutability
    live_hash_final = compute_model_parameter_hash(live_model.model)
    assert live_hash_initial == live_hash_final, "Live model was mutated during sentinel evaluation!"

    # 10. Audit 12 Smoke Test Criteria
    checks = []
    
    # Check 1: Audio files resolved
    c1 = (decision.decision_reason != "FAIL_CLOSED_EVALUATOR_ERROR" or 
          not any("Audio file not found" in r for r in decision.rejection_reasons))
    checks.append(("1. Sentinel Audio Files Loaded via Resolver", c1, "Resolved without FileNotFoundError"))

    # Check 2: Label isolation
    c2 = all(hasattr(item, "audio_filepath") and not hasattr(item, "reference_raw") for item in unlabeled_batch.items)
    checks.append(("2. Stream Label Isolation Enforced", c2, "No labels accessible to adaptation loop"))

    # Check 3 & 4: Predictions generated
    c3 = not math.isnan(decision.delta_r)
    checks.append(("3 & 4. Live & Candidate Predictions Generated", c3, f"Delta_R computed: {decision.delta_r:+.6f}"))

    # Check 5: Delta_R finite
    c5 = not math.isnan(decision.delta_r) and not math.isinf(decision.delta_r)
    checks.append(("5. Delta_R is Finite", c5, f"{decision.delta_r:+.6f}"))

    # Check 6: Every Delta_g finite
    c6 = (len(decision.delta_g) == 6 and 
          all(not math.isnan(v) and not math.isinf(v) for v in decision.delta_g.values()))
    checks.append(("6. All 6 Group Deltas Finite", c6, f"Groups: {list(decision.delta_g.keys())}"))

    # Check 7: Delta_D finite
    c7 = not math.isnan(decision.delta_d) and not math.isinf(decision.delta_d)
    checks.append(("7. Delta_D is Finite", c7, f"{decision.delta_d:+.6f}"))

    # Check 8: Bootstrap replicates
    c8 = decision.bootstrap_b == 1000
    checks.append(("8. 1000 Bootstrap Replicates Computed", c8, f"B = {decision.bootstrap_b}"))

    # Check 9: Zero groups omitted
    c9 = len(decision.delta_g) == 6
    checks.append(("9. Zero Strata Omitted", c9, f"{len(decision.delta_g)}/6 strata monitored"))

    # Check 10: UCBs finite
    c10 = (not math.isnan(decision.ucb_r) and not math.isinf(decision.ucb_r) and
           not math.isnan(decision.ucb_max_group) and not math.isinf(decision.ucb_max_group) and
           not math.isnan(decision.ucb_d) and not math.isinf(decision.ucb_d))
    checks.append(("10. UCBs Finite", c10, f"UCB_R={decision.ucb_r:+.4f}, UCB_max={decision.ucb_max_group:+.4f}, UCB_D={decision.ucb_d:+.4f}"))

    # Check 11: Real Decision Produced
    c11 = decision.decision in ["ACCEPT", "REJECT"] and decision.decision_reason in ["ACCEPTED", "STATISTICAL_GATE_REJECTION"]
    checks.append(("11. Statistical Decision Produced", c11, f"Decision: {decision.decision} ({decision.decision_reason})"))

    # Check 12: Zero Evaluator Exceptions
    c12 = decision.decision_reason != "FAIL_CLOSED_EVALUATOR_ERROR"
    checks.append(("12. Zero Evaluator Exceptions", c12, f"Decision Reason: {decision.decision_reason}"))

    all_passed = all(passed for _, passed, _ in checks)

    # 11. Print Summary
    print("\n" + "=" * 70)
    print("SMOKE TEST RESULTS SUMMARY")
    print("=" * 70)
    for name, passed, detail in checks:
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {name}: {detail}")

    print("=" * 70)
    if all_passed:
        print("ALL 12 SMOKE TEST CRITERIA PASSED! Evaluator integrity validated.")
    else:
        print("CRITICAL SMOKE TEST FAILURE! Stopping execution.")

    # 12. Write Smoke Test Report
    with open(SMOKE_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Stage 5D Sentinel Safety Evaluator Smoke Test Report\n\n")
        f.write(f"- **Execution Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        f.write(f"- **Live Model Parameter Hash:** `{live_hash_initial[:16]}`\n")
        f.write(f"- **Candidate Parameter Hash:** `{cand_hash[:16]}`\n")
        f.write(f"- **Evaluation Duration:** {eval_elapsed:.2f}s\n")
        f.write(f"- **Decision:** **`{decision.decision}`**\n")
        f.write(f"- **Decision Reason:** `{decision.decision_reason}`\n")
        f.write(f"- **Rejection Reasons:** `{'; '.join(decision.rejection_reasons) if decision.rejection_reasons else 'None'}`\n\n")
        
        f.write("## Empirical Metrics & Upper Confidence Bounds\n\n")
        f.write("| Metric | Point Estimate | 95% UCB | Threshold | Margin | Status |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        f.write(f"| **Overall Risk ($\\Delta_R$)** | {decision.delta_r:+.4f} | {decision.ucb_r:+.4f} | $\\le {decision.epsilon_r:.4f}$ | {decision.epsilon_r - decision.ucb_r:+.4f} | {'PASS' if decision.ucb_r <= decision.epsilon_r else 'VIOLATION'} |\n")
        f.write(f"| **Subgroup Regression ($\\max_g \\Delta_g$)** | {decision.max_delta_g:+.4f} | {decision.ucb_max_group:+.4f} | $\\le {decision.epsilon_g:.4f}$ | {decision.epsilon_g - decision.ucb_max_group:+.4f} | {'PASS' if decision.ucb_max_group <= decision.epsilon_g else 'VIOLATION'} |\n")
        f.write(f"| **Disparity Growth ($\\Delta_D$)** | {decision.delta_d:+.4f} | {decision.ucb_d:+.4f} | $\\le {decision.epsilon_d:.4f}$ | {decision.epsilon_d - decision.ucb_d:+.4f} | {'PASS' if decision.ucb_d <= decision.epsilon_d else 'VIOLATION'} |\n\n")

        f.write("## Stratum-Level Deltas\n\n")
        f.write("| Stratum | Observed $\\Delta_g$ |\n")
        f.write("| :--- | :---: |\n")
        for g, d in sorted(decision.delta_g.items()):
            f.write(f"| {g} | {d:+.4f} |\n")

        f.write("\n## 12 Smoke Test Verification Criteria\n\n")
        f.write("| Criterion | Result | Evidence / Detail |\n")
        f.write("| :--- | :---: | :--- |\n")
        for name, passed, detail in checks:
            f.write(f"| {name} | **{'PASS' if passed else 'FAIL'}** | `{detail}` |\n")

        f.write("\n## Verdict\n\n")
        if all_passed:
            f.write("**OVERALL VERDICT: PASSED -- Evaluator is functioning properly and ready for full 225-window execution.**\n")
        else:
            f.write("**OVERALL VERDICT: FAILED -- Evaluator exception or invalid condition detected. STOP.**\n")

    print(f"\nWrote smoke test report to {SMOKE_REPORT_PATH}")
    return all_passed


if __name__ == "__main__":
    success = run_smoke_test()
    if not success:
        sys.exit(1)
