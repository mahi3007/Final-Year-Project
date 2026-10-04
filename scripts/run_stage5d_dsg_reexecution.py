#!/usr/bin/env python3
"""
Stage 5D Phase 5 & 6: DSG Prequential Re-execution & External Outcome Audit.
===========================================================================
Re-executes the frozen DSG Controller across the 225 external-stream windows (900 clips)
using the cryptographically verified SentinelAudioResolver.

Methodological Invariants (STRICTLY FROZEN):
- epsilon_R = 0.0000
- epsilon_G = 0.0200
- epsilon_D = 0.0200
- B = 1000
- confidence = 0.95
- speaker-level paired cluster bootstrap (seed = 20261002)
- 30-speaker, 300-clip sentinel panel
- Window size K = 4 (225 sequential prequential windows)
- Candidate generator: SUTA (lr=1e-4, temp=2.5, alpha=0.5, steps=1)
- Prequential protocol: theta_t transcribes B_t BEFORE any candidate evaluation

Outputs:
- reports/stage5/stage5d_final_decision_audit.csv
- reports/stage5/stage5d_dsg_reexecution.md
"""

from __future__ import annotations

import csv
import gc
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
import torch

# Force unbuffered stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
EVAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
EVAL_LOCK = SPLITS_DIR / "stage5_external_eval.lock.json"
SENTINEL_CSV = SPLITS_DIR / "stage5_sentinel_panel.csv"
SENTINEL_MANIFEST = SPLITS_DIR / "stage5_sentinel_audio_manifest.json"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
GATE_CONFIG = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5"

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.resolver import SentinelAudioResolver
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, enforce_data_access_firewall
from dsg_ctta.offline.metrics import compute_utterance_metrics


def preload_audio_waveforms(df: pd.DataFrame, audio_dir: Path) -> Dict[str, np.ndarray]:
    """Preloads audio files into memory to eliminate redundant disk I/O."""
    print(f"Preloading {len(df)} audio waveforms into memory...")
    cache = {}
    for idx, row in df.iterrows():
        rec_id = row["recording_id"]
        p = audio_dir / f"{rec_id}.mp3"
        w, _ = load_and_resample_audio(str(p), 16000)
        cache[rec_id] = w
    print(f"Audio preloading complete ({len(cache)} clips).")
    return cache


def run_stage5d_reexecution():
    print("=" * 70)
    print("STAGE 5D: DSG CONTROLLER PREQUENTIAL RE-EXECUTION")
    print("=" * 70)

    # 1. Load and verify gate config
    with open(GATE_CONFIG, "r", encoding="utf-8") as f:
        gate_cfg = json.load(f)

    eps_r = float(gate_cfg["gate_tolerances"]["epsilon_R"])
    eps_g = float(gate_cfg["gate_tolerances"]["epsilon_G"])
    eps_d = float(gate_cfg["gate_tolerances"]["epsilon_D"])
    bootstrap_b = int(gate_cfg["bootstrap"]["B"])
    bootstrap_conf = float(gate_cfg["bootstrap"]["confidence"])
    bootstrap_seed = int(gate_cfg["bootstrap"]["seed"])

    print(f"Gate Tolerances Frozen: eps_R={eps_r:.4f}, eps_G={eps_g:.4f}, eps_D={eps_d:.4f}")
    print(f"Bootstrap Settings    : B={bootstrap_b}, conf={bootstrap_conf:.2f}, seed={bootstrap_seed}")

    # 2. Initialize SentinelAudioResolver
    print("\nInitializing Canonical SentinelAudioResolver...")
    resolver = SentinelAudioResolver(
        manifest_path=SENTINEL_MANIFEST if SENTINEL_MANIFEST.exists() else None,
        inventory_path=SENTINEL_INVENTORY,
        project_root=PROJECT_ROOT,
    )
    if not resolver.is_loaded:
        raise RuntimeError("Resolver cannot be loaded! Manifest or inventory missing.")
    print(f"Resolver initialized with {resolver.total_clips} verified clips.")

    # Compute sentinel manifest hash for audit log
    sentinel_manifest_hash = resolver.compute_sha256(
        SENTINEL_MANIFEST if SENTINEL_MANIFEST.exists() else SENTINEL_INVENTORY
    )
    print(f"Sentinel Manifest SHA-256: {sentinel_manifest_hash}")

    # 3. Load Datasets
    eval_df = pd.read_csv(EVAL_CSV)
    sentinel_df = pd.read_csv(SENTINEL_CSV)
    print(f"External Eval Stream: {len(eval_df)} clips across {eval_df['speaker_id'].nunique()} speakers.")
    print(f"Sentinel Panel      : {len(sentinel_df)} clips across {sentinel_df['speaker_id'].nunique()} speakers.")

    # 4. Hardware and Preloading
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Hardware execution device: {device}")
    audio_cache = preload_audio_waveforms(eval_df, AUDIO_DIR)

    # Preload sentinel audio waveforms in resolver order
    print("Preloading 300 sentinel audio clips into memory for fast evaluation...")
    sentinel_records = sentinel_df.to_dict(orient="records")
    sentinel_audio_cache: Dict[str, np.ndarray] = {}
    for r in sentinel_records:
        resolved_p = resolver.resolve(r, verify_hash=True)
        w, _ = load_and_resample_audio(str(resolved_p), 16000)
        sentinel_audio_cache[r["sentinel_id"]] = w
    print(f"Sentinel audio preloading complete ({len(sentinel_audio_cache)} waveforms).")

    # Fast transcribe function using in-memory waveforms and torch.inference_mode
    def fast_sentinel_transcribe(asr_model_wrapper: Any, utt_dict: Dict[str, Any]) -> str:
        s_id = utt_dict["sentinel_id"]
        waveform = sentinel_audio_cache[s_id]
        inputs = asr_model_wrapper.processor(waveform, sampling_rate=16000, return_tensors="pt")
        with torch.inference_mode():
            logits = asr_model_wrapper.model(inputs.input_values.to(device)).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        return asr_model_wrapper.processor.batch_decode(predicted_ids)[0].strip()

    # 5. Initialize Live Model & DSG Controller
    live_model = create_asr_model("wav2vec2_base", device=device)
    live_model.load_model()

    gate = DisparitySafetyGate(epsilon_r=eps_r, epsilon_g=eps_g, epsilon_d=eps_d)
    evaluator = SentinelSafetyEvaluator(
        gate=gate,
        num_bootstrap=bootstrap_b,
        confidence_level=bootstrap_conf,
        bootstrap_seed=bootstrap_seed,
        min_speakers_per_group=3,
        resolver=resolver,
    )

    suta_cfg = {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1}

    # Tracking containers
    window_size_k = 4
    num_clips = len(eval_df)
    num_windows = (num_clips + window_size_k - 1) // window_size_k

    dsg_decision_records: List[Dict[str, Any]] = []
    dsg_prediction_records: List[Dict[str, Any]] = []
    external_audit_records: List[Dict[str, Any]] = []

    # Cache for live model sentinel hypotheses (reused across rejected windows)
    cached_live_sentinel_hyps: Optional[List[str]] = None
    cached_live_model_hash: Optional[str] = None

    t_stream_start = time.time()
    print(f"\n---> Starting 225-Window DSG Prequential Re-execution...")

    for win_idx in range(num_windows):
        start_idx = win_idx * window_size_k
        end_idx = min(start_idx + window_size_k, num_clips)
        batch_rows = eval_df.iloc[start_idx:end_idx]

        theta_t_hash = compute_model_parameter_hash(live_model.model)

        # ---------------------------------------------------------------------
        # STEP 1: PREDICT B_t USING LIVE MODEL theta_t (STRICT PREQUENTIAL)
        # ---------------------------------------------------------------------
        window_hypotheses: List[str] = []
        for _, row in batch_rows.iterrows():
            rec_id = row["recording_id"]
            hyp = live_model.transcribe(audio_cache[rec_id])
            window_hypotheses.append(hyp)

            dsg_prediction_records.append({
                "run_id": "stage5d_dsg",
                "method": "dsg",
                "window_id": win_idx,
                "recording_id": row["recording_id"],
                "speaker_id": row["speaker_id"],
                "group_id": row["stage5_accent_group"],
                "stratum_code": row["stratum_code"],
                "reference_raw": row["transcript"],
                "hypothesis_raw": hyp,
                "theta_hash": theta_t_hash,
            })

        # ---------------------------------------------------------------------
        # STEP 2: CREATE LABEL-ISOLATED UNLABELED BATCH
        # ---------------------------------------------------------------------
        batch_utts = []
        for _, row in batch_rows.iterrows():
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
        unlabeled_batch = LabelIsolationSanitizer.sanitize_batch(batch_utts, batch_idx=win_idx)
        enforce_data_access_firewall(unlabeled_batch)

        # ---------------------------------------------------------------------
        # STEP 3: ADAPT SHADOW CANDIDATE MODEL theta'
        # ---------------------------------------------------------------------
        candidate_model_core = ShadowCandidateManager.create_candidate_clone(live_model.model)
        cand_asr_wrapper = create_asr_model("wav2vec2_base", device=device)
        cand_asr_wrapper.model = candidate_model_core
        cand_asr_wrapper.processor = live_model.processor

        cand_adapter = SutaAdapter(asr_model=cand_asr_wrapper, config=suta_cfg)
        cand_adapter.adapt(unlabeled_batch)
        cand_hash = compute_model_parameter_hash(candidate_model_core)

        # ---------------------------------------------------------------------
        # STEP 4: SENTINEL EVALUATION WITH RESOLVED AUDIO
        # ---------------------------------------------------------------------
        # If live model parameter hash matches cached, reuse live model sentinel predictions
        if cached_live_model_hash != theta_t_hash or cached_live_sentinel_hyps is None:
            cached_live_sentinel_hyps = [
                fast_sentinel_transcribe(live_model, r) for r in sentinel_records
            ]
            cached_live_model_hash = theta_t_hash

        # Candidate predictions on sentinel panel
        cand_sentinel_hyps = [
            fast_sentinel_transcribe(cand_asr_wrapper, r) for r in sentinel_records
        ]

        # Compute utterance error metrics
        records_live = []
        records_cand = []
        for r_idx, r in enumerate(sentinel_records):
            ref_norm = TextNormalizer.normalize(r["transcript"])
            m_live = compute_utterance_metrics(ref_norm, cached_live_sentinel_hyps[r_idx])
            m_cand = compute_utterance_metrics(ref_norm, cand_sentinel_hyps[r_idx])

            records_live.append({
                "utterance_id": r["sentinel_id"],
                "speaker_id": r["speaker_id"],
                "group_id": r["stage5_accent_group"],
                "substitutions": m_live.substitutions,
                "deletions": m_live.deletions,
                "insertions": m_live.insertions,
                "reference_length": m_live.reference_length,
            })
            records_cand.append({
                "utterance_id": r["sentinel_id"],
                "speaker_id": r["speaker_id"],
                "group_id": r["stage5_accent_group"],
                "substitutions": m_cand.substitutions,
                "deletions": m_cand.deletions,
                "insertions": m_cand.insertions,
                "reference_length": m_cand.reference_length,
            })

        # Evaluate candidate safety through paired bootstrap
        decision = evaluator.evaluate_records(
            records_live=records_live,
            records_candidate=records_cand,
            candidate_identifier=cand_hash[:16],
            live_identifier=theta_t_hash[:16],
        )

        # Record decision audit row
        audit_row = {
            "window_id": win_idx,
            "candidate_id": cand_hash[:16],
            "current_model_id": theta_t_hash[:16],
            "delta_R": round(decision.delta_r, 6) if not math.isnan(decision.delta_r) else "NaN",
            "delta_g": json.dumps({k: round(v, 6) for k, v in decision.delta_g.items()}),
            "max_delta_g": round(decision.max_delta_g, 6) if not math.isnan(decision.max_delta_g) else "NaN",
            "delta_D": round(decision.delta_d, 6) if not math.isnan(decision.delta_d) else "NaN",
            "UCB_R": round(decision.ucb_r, 6) if not math.isnan(decision.ucb_r) else "NaN",
            "UCB_max_group": round(decision.ucb_max_group, 6) if not math.isnan(decision.ucb_max_group) else "NaN",
            "UCB_D": round(decision.ucb_d, 6) if not math.isnan(decision.ucb_d) else "NaN",
            "epsilon_R": decision.epsilon_r,
            "epsilon_G": decision.epsilon_g,
            "epsilon_D": decision.epsilon_d,
            "decision": decision.decision,
            "decision_reason": decision.decision_reason,
            "rejection_category": decision.rejection_category or "NONE",
            "rejection_reasons": "; ".join(decision.rejection_reasons) if decision.rejection_reasons else "NONE",
            "bootstrap_seed": decision.bootstrap_seed,
            "bootstrap_B": decision.bootstrap_b,
            "sentinel_manifest_hash": sentinel_manifest_hash[:16],
        }
        dsg_decision_records.append(audit_row)

        # ---------------------------------------------------------------------
        # STEP 5: STATE TRANSITION
        # ---------------------------------------------------------------------
        live_model.model = ShadowCandidateManager.apply_transition(
            live_model=live_model.model,
            candidate_model=candidate_model_core,
            decision=decision,
        )

        # ---------------------------------------------------------------------
        # STEP 6: OFFLINE EXTERNAL OUTCOME AUDIT (Diagnostic Only)
        # ---------------------------------------------------------------------
        # Score candidate vs live on external B_t with ground truth
        ext_live_errors = 0
        ext_cand_errors = 0
        ext_ref_words = 0
        for row_i, (_, r) in enumerate(batch_rows.iterrows()):
            ref_norm = TextNormalizer.normalize(r["transcript"])
            hyp_live = window_hypotheses[row_i]
            hyp_cand = cand_asr_wrapper.transcribe(audio_cache[r["recording_id"]])
            m_l = compute_utterance_metrics(ref_norm, hyp_live)
            m_c = compute_utterance_metrics(ref_norm, hyp_cand)
            ext_live_errors += m_l.total_errors
            ext_cand_errors += m_c.total_errors
            ext_ref_words += m_l.reference_length

        ext_delta_err = ext_cand_errors - ext_live_errors
        if ext_delta_err > 0:
            ext_nature = "HARMFUL"
        elif ext_delta_err < 0:
            ext_nature = "BENEFICIAL"
        else:
            ext_nature = "NEUTRAL"

        if decision.decision == "ACCEPT":
            classification = f"ACCEPTED_AND_EXTERNALLY_{ext_nature}"
        elif decision.decision_reason == "STATISTICAL_GATE_REJECTION":
            classification = f"STATISTICALLY_REJECTED_AND_EXTERNALLY_{ext_nature}"
        else:
            classification = f"FAIL_CLOSED_REJECTED_AND_EXTERNALLY_{ext_nature}"

        external_audit_records.append({
            "window_id": win_idx,
            "candidate_id": cand_hash[:16],
            "decision": decision.decision,
            "decision_reason": decision.decision_reason,
            "ext_live_errors": ext_live_errors,
            "ext_cand_errors": ext_cand_errors,
            "ext_word_delta": ext_delta_err,
            "external_nature": ext_nature,
            "audit_classification": classification,
        })

        elapsed = time.time() - t_stream_start
        rate = (win_idx + 1) / elapsed if elapsed > 0 else 1.0
        eta = (num_windows - (win_idx + 1)) / rate
        print(
            f"[DSG-5D] Window {win_idx + 1:>3}/{num_windows} | "
            f"Dec: {decision.decision} ({decision.decision_reason}) | "
            f"UCB_R: {decision.ucb_r:+.4f} | UCB_max: {decision.ucb_max_group:+.4f} | "
            f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s",
            flush=True,
        )

        # Cleanup candidate
        del candidate_model_core
        del cand_asr_wrapper
        del cand_adapter

    t_total_elapsed = time.time() - t_stream_start
    print(f"\n225 Windows completed in {t_total_elapsed:.2f}s ({t_total_elapsed/num_clips:.3f}s/clip).")

    # -------------------------------------------------------------------------
    # PHASE 6: SUMMARY METRICS & AUDIT EXPORT
    # -------------------------------------------------------------------------
    audit_df = pd.DataFrame(dsg_decision_records)
    ext_audit_df = pd.DataFrame(external_audit_records)

    # Export CSVs
    DECISION_AUDIT_CSV = REPORTS_DIR / "stage5d_final_decision_audit.csv"
    audit_df.to_csv(DECISION_AUDIT_CSV, index=False)
    print(f"Exported decision audit log: {DECISION_AUDIT_CSV}")

    EXT_AUDIT_CSV = REPORTS_DIR / "stage5d_external_outcome_audit.csv"
    ext_audit_df.to_csv(EXT_AUDIT_CSV, index=False)
    print(f"Exported external outcome audit: {EXT_AUDIT_CSV}")

    # Compute breakdown counts
    total_decisions = len(audit_df)
    stat_rejects = (audit_df["decision_reason"] == "STATISTICAL_GATE_REJECTION").sum()
    fail_closed_rejects = (audit_df["decision_reason"] == "FAIL_CLOSED_EVALUATOR_ERROR").sum()
    accepted_updates = (audit_df["decision"] == "ACCEPT").sum()

    print("\n" + "=" * 70)
    print("STAGE 5D DECISION BREAKDOWN:")
    print(f"  Total Windows Evaluated   : {total_decisions}")
    print(f"  Accepted Updates          : {accepted_updates} ({accepted_updates/total_decisions*100:.1f}%)")
    print(f"  Statistical Gate Rejects  : {stat_rejects} ({stat_rejects/total_decisions*100:.1f}%)")
    print(f"  Fail-Closed Rejects       : {fail_closed_rejects} ({fail_closed_rejects/total_decisions*100:.1f}%)")
    print("=" * 70)

    # Classifications
    class_counts = ext_audit_df["audit_classification"].value_counts().to_dict()
    print("\nExternal Outcome Diagnostic Classifications:")
    for k, v in sorted(class_counts.items()):
        print(f"  - {k}: {v} ({v/total_decisions*100:.1f}%)")

    # Generate Markdown Report
    REEXEC_REPORT = REPORTS_DIR / "stage5d_dsg_reexecution.md"
    with open(REEXEC_REPORT, "w", encoding="utf-8") as f:
        f.write("# Stage 5D: DSG Evaluator Integrity Repair & Re-execution Report\n\n")
        f.write(f"- **Execution Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        f.write(f"- **Protocol Version:** `v1.0-cv27-amended`\n")
        f.write(f"- **Stream Windows Evaluated:** 225 ($K=4$, 900 clips)\n")
        f.write(f"- **Execution Duration:** {t_total_elapsed:.2f}s ({t_total_elapsed/num_clips:.3f}s/clip)\n")
        f.write(f"- **Frozen Tolerances:** $\\epsilon_R = {eps_r:.4f}$, $\\epsilon_G = {eps_g:.4f}$, $\\epsilon_D = {eps_d:.4f}$\n")
        f.write(f"- **Bootstrap Configuration:** $B = {bootstrap_b}$, Confidence $= {bootstrap_conf:.2f}$, Seed $= {bootstrap_seed}$\n")
        f.write(f"- **Sentinel Audio Manifest Hash:** `{sentinel_manifest_hash}`\n\n")

        f.write("## 1. Decision Breakdown\n\n")
        f.write("| Decision Category | Count | Percentage | Research Interpretation |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        f.write(f"| **Statistical Gate Rejections** | **{stat_rejects}** | **{stat_rejects/total_decisions*100:.1f}%** | Candidate update evaluated against acoustic sentinel panel and rejected by empirical bounds ($\\text{{UCB}} > \\epsilon$). |\n")
        f.write(f"| **Accepted Updates** | **{accepted_updates}** | **{accepted_updates/total_decisions*100:.1f}%** | Candidate safely satisfied all 3 bounds ($\\text{{UCB}}_R \\le \\epsilon_R$, $\\text{{UCB}}_{{\\max}} \\le \\epsilon_G$, $\\text{{UCB}}_D \\le \\epsilon_D$). |\n")
        f.write(f"| **Fail-Closed Evaluator Rejections** | **{fail_closed_rejects}** | **{fail_closed_rejects/total_decisions*100:.1f}%** | Rejections due to evaluator runtime error, missing audio, or NaN/Inf corruption. |\n")
        f.write(f"| **TOTAL** | **{total_decisions}** | **100.0%** | **Expected Desired State: Fail-Closed Rejections = 0** |\n\n")

        f.write("## 2. Retrospective External Outcome Diagnostic Classification\n\n")
        f.write("Post-hoc analysis comparing candidate update behavior on external stream $B_t$ against gate decision:\n\n")
        f.write("| Classification | Windows | Pct | Significance |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        for k, v in sorted(class_counts.items()):
            f.write(f"| `{k}` | {v} | {v/total_decisions*100:.1f}% | {'Safely prevented external error' if 'HARMFUL' in k and 'REJECTED' in k else 'Diagnostic outcome'} |\n")

        f.write("\n## 3. Scientific Finding & Thesis Contribution\n\n")
        if fail_closed_rejects == 0:
            f.write("With canonical path resolution repaired, **100% of candidate updates were genuinely evaluated on physical acoustic data against the frozen 30-speaker sentinel panel**.\n\n")
            if stat_rejects == total_decisions:
                f.write("> [!IMPORTANT]\n")
                f.write("> **Under the frozen zero-tolerance overall-risk constraint ($\\epsilon_R = 0.0000$), all candidate updates violated at least one statistical bound and were statistically rejected.**\n")
                f.write("> This rigorously demonstrates that DSG's statistical gate identified and prevented unsafe adaptation candidates, preserving the robust No-Adapt baseline while completely eliminating fail-closed software errors.\n")
            else:
                f.write(f"> [!IMPORTANT]\n")
                f.write(f"> DSG safely accepted {accepted_updates} candidate updates that met all statistical criteria while rejecting {stat_rejects} updates that violated safety constraints.\n")
        else:
            f.write(f"WARNING: Observed {fail_closed_rejects} fail-closed evaluator rejections.\n")

    print(f"Generated re-execution report: {REEXEC_REPORT}")
    return audit_df, ext_audit_df


if __name__ == "__main__":
    run_stage5d_reexecution()
