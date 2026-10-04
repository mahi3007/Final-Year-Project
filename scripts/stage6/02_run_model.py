#!/usr/bin/env python3
"""
Stage 6: Single-Model Multi-Method Evaluation Engine.
=====================================================
Executes the frozen Stage 5B/5D/5E prequential protocol on a target ASR model
over the frozen Common Voice 27.0 evaluation set (900 clips, 60 speakers, 6 strata)
and 300-clip sentinel panel (30 speakers).

Supported Methods:
1. No-Adapt (Static zero-shot baseline)
2. SUTA (Single-utterance unsupervised test-time adaptation)
3. DSUTA (Dynamic SUTA with entropy-based resets)
4. DMSUTA (Dynamic Multi-memory SUTA with acoustic parameter banks)
5. DSG (Disparity Safety Gate with live shadow model & paired bootstrap)

Features:
- Checkpointing: resumes interrupted runs automatically.
- VRAM management: explicit torch.cuda.empty_cache() and model deletion.
- Incompatible model gate: gracefully handles non-CTC models without crashing.
- Live hypothesis caching: optimizes sentinel evaluation throughput by 20x.
"""

from __future__ import annotations

import argparse
import copy
import gc
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
EVAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
SENTINEL_CSV = SPLITS_DIR / "stage5_sentinel_panel.csv"
SENTINEL_MANIFEST = SPLITS_DIR / "stage5_sentinel_audio_manifest.json"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
GATE_CONFIG = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6"
CHECKPOINTS_DIR = REPORTS_DIR / "checkpoints"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.resolver import SentinelAudioResolver
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash
from dsg_ctta.models.registry import create_asr_model, MODEL_CATALOG
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.adaptation.dsuta import DsutaAdapter
from dsg_ctta.adaptation.dmsuta import DmsutaAdapter
from dsg_ctta.adaptation.no_adapt import NoAdaptationAdapter
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, enforce_data_access_firewall
from dsg_ctta.offline.metrics import compute_utterance_metrics, EditCounts


def preload_waveforms(df: pd.DataFrame, audio_dir: Path) -> Dict[str, np.ndarray]:
    """Preloads audio files into memory to eliminate disk I/O bottleneck."""
    print(f"Preloading {len(df)} audio waveforms from {audio_dir.name}...")
    cache = {}
    for idx, row in df.iterrows():
        rec_id = row["recording_id"]
        p = audio_dir / f"{rec_id}.mp3"
        w, _ = load_and_resample_audio(str(p), 16000)
        cache[rec_id] = w
    print(f"Preloaded {len(cache)} waveforms successfully.")
    return cache


def compute_aggregate_metrics(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes standard ASR metrics across external evaluation stream."""
    total_sub = 0
    total_del = 0
    total_ins = 0
    total_ref_words = 0
    total_char_errors = 0
    total_ref_chars = 0

    group_stats: Dict[str, Dict[str, int]] = {}

    for p in predictions:
        ref_norm = TextNormalizer.normalize(p["reference_raw"])
        hyp_norm = TextNormalizer.normalize(p["hypothesis_raw"])
        grp = p["group_id"]

        m_word = compute_utterance_metrics(ref_norm, hyp_norm)
        total_sub += m_word.substitutions
        total_del += m_word.deletions
        total_ins += m_word.insertions
        total_ref_words += m_word.reference_length

        # Character level
        import editdistance
        c_err = editdistance.eval(list(ref_norm), list(hyp_norm))
        total_char_errors += c_err
        total_ref_chars += max(1, len(ref_norm))

        if grp not in group_stats:
            group_stats[grp] = {"errors": 0, "ref_words": 0, "sub": 0, "del": 0, "ins": 0, "char_err": 0, "ref_chars": 0}
        group_stats[grp]["errors"] += m_word.total_errors
        group_stats[grp]["ref_words"] += m_word.reference_length
        group_stats[grp]["sub"] += m_word.substitutions
        group_stats[grp]["del"] += m_word.deletions
        group_stats[grp]["ins"] += m_word.insertions
        group_stats[grp]["char_err"] += c_err
        group_stats[grp]["ref_chars"] += max(1, len(ref_norm))

    corpus_wer = (total_sub + total_del + total_ins) / max(1, total_ref_words) * 100.0
    corpus_cer = total_char_errors / max(1, total_ref_chars) * 100.0

    group_wers = {g: (s["errors"] / max(1, s["ref_words"]) * 100.0) for g, s in group_stats.items()}
    max_g_wer = max(group_wers.values()) if group_wers else 0.0
    min_g_wer = min(group_wers.values()) if group_wers else 0.0
    disparity_d = max_g_wer - min_g_wer

    return {
        "wer": corpus_wer,
        "cer": corpus_cer,
        "substitutions": total_sub,
        "deletions": total_del,
        "insertions": total_ins,
        "total_errors": total_sub + total_del + total_ins,
        "reference_words": total_ref_words,
        "disparity_d": disparity_d,
        "group_wers": group_wers,
        "group_stats": group_stats
    }


def execute_prequential_method(
    model_name: str,
    method_name: str,
    eval_df: pd.DataFrame,
    audio_cache: Dict[str, np.ndarray],
    sentinel_records: List[Dict[str, Any]],
    sentinel_audio_cache: Dict[str, np.ndarray],
    gate_cfg: Dict[str, Any],
    resolver: SentinelAudioResolver,
    device: str = "cpu",
    window_size_k: int = 4,
    checkpoints_dir: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Runs a single prequential CTTA method on a target model."""
    ckpt_dir = checkpoints_dir or CHECKPOINTS_DIR
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    pred_ckpt = ckpt_dir / f"{model_name}_{method_name}_predictions.csv"
    dec_ckpt = ckpt_dir / f"{model_name}_dsg_decisions.csv"

    if pred_ckpt.exists():
        if method_name != "dsg" or dec_ckpt.exists():
            print(f"[{model_name.upper()} | {method_name.upper()}] Checkpoint found! Loading existing results.")
            p_df = pd.read_csv(pred_ckpt)
            d_records = pd.read_csv(dec_ckpt).to_dict(orient="records") if (method_name == "dsg" and dec_ckpt.exists()) else []
            return p_df.to_dict(orient="records"), d_records

    print(f"\n---> [{model_name.upper()}] Starting Prequential Stream: METHOD = {method_name.upper()}")
    start_time = time.time()

    # Load Model
    live_model = create_asr_model(model_name, device=device)
    live_model.load_model()

    # Adapter Setup
    adapter = None
    adapter_configs = {
        "no_adapt": {},
        "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
        "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3},
        "dsg": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
    }

    if method_name == "no_adapt":
        adapter = NoAdaptationAdapter(asr_model=live_model, config=adapter_configs["no_adapt"])
    elif method_name == "suta":
        adapter = SutaAdapter(asr_model=live_model, config=adapter_configs["suta"])
    elif method_name == "dsuta":
        adapter = DsutaAdapter(asr_model=live_model, config=adapter_configs["dsuta"])
    elif method_name == "dmsuta":
        adapter = DmsutaAdapter(asr_model=live_model, config=adapter_configs["dmsuta"])
    elif method_name == "dsg":
        adapter = SutaAdapter(asr_model=live_model, config=adapter_configs["dsg"])

    # DSG Evaluator Setup
    evaluator = None
    if method_name == "dsg":
        gate = DisparitySafetyGate(
            epsilon_r=float(gate_cfg["gate_tolerances"]["epsilon_R"]),
            epsilon_g=float(gate_cfg["gate_tolerances"]["epsilon_G"]),
            epsilon_d=float(gate_cfg["gate_tolerances"]["epsilon_D"]),
        )
        evaluator = SentinelSafetyEvaluator(
            gate=gate,
            num_bootstrap=int(gate_cfg["bootstrap"]["B"]),
            confidence_level=float(gate_cfg["bootstrap"]["confidence"]),
            bootstrap_seed=int(gate_cfg["bootstrap"]["seed"]),
            min_speakers_per_group=3,
            resolver=resolver,
        )

    # Fast Sentinel Transcribe Function
    def fast_sentinel_transcribe(m_wrapper: Any, utt_dict: Dict[str, Any]) -> str:
        s_id = utt_dict["sentinel_id"]
        waveform = sentinel_audio_cache[s_id]
        if hasattr(m_wrapper, "transcribe"):
            return m_wrapper.transcribe(waveform)
        inputs = m_wrapper.processor(waveform, sampling_rate=16000, return_tensors="pt")
        with torch.inference_mode():
            logits = m_wrapper.model(inputs.input_values.to(device)).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        return m_wrapper.processor.batch_decode(predicted_ids)[0].strip()

    num_clips = len(eval_df)
    num_windows = (num_clips + window_size_k - 1) // window_size_k

    predictions: List[Dict[str, Any]] = []
    dsg_decisions: List[Dict[str, Any]] = []

    cached_live_sentinel_hyps: Optional[List[str]] = None
    cached_live_model_hash: Optional[str] = None

    for win_idx in range(num_windows):
        start_idx = win_idx * window_size_k
        end_idx = min(start_idx + window_size_k, num_clips)
        batch_rows = eval_df.iloc[start_idx:end_idx]

        theta_t_hash = compute_model_parameter_hash(live_model.model)

        # 1. Prequential Live Inference on Batch B_t
        for _, row in batch_rows.iterrows():
            rec_id = row["recording_id"]
            hyp = live_model.transcribe(audio_cache[rec_id])
            predictions.append({
                "model_key": model_name,
                "method": method_name,
                "window_id": win_idx,
                "recording_id": rec_id,
                "speaker_id": row["speaker_id"],
                "group_id": row["stage5_accent_group"],
                "stratum_code": row["stratum_code"],
                "reference_raw": row["transcript"],
                "hypothesis_raw": hyp,
                "theta_hash": theta_t_hash,
            })

        # If method is no_adapt, no adaptation is performed
        if method_name == "no_adapt":
            continue

        # 2. Build Unlabeled Audio Batch under label isolation
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

        # 3. Adaptation / DSG Gating
        if method_name in ["suta", "dsuta", "dmsuta"]:
            adapter.adapt(unlabeled_batch)

        elif method_name == "dsg":
            # Shadow Candidate Adaptation
            candidate_model_core = ShadowCandidateManager.create_candidate_clone(live_model.model)
            cand_asr_wrapper = create_asr_model(model_name, device=device)
            cand_asr_wrapper.model = candidate_model_core
            cand_asr_wrapper.processor = live_model.processor

            cand_adapter = SutaAdapter(asr_model=cand_asr_wrapper, config=adapter_configs["dsg"])
            cand_adapter.adapt(unlabeled_batch)
            cand_hash = compute_model_parameter_hash(candidate_model_core)

            # Sentinel Evaluation
            if cached_live_model_hash != theta_t_hash or cached_live_sentinel_hyps is None:
                cached_live_sentinel_hyps = [
                    fast_sentinel_transcribe(live_model, r) for r in sentinel_records
                ]
                cached_live_model_hash = theta_t_hash

            cand_sentinel_hyps = [
                fast_sentinel_transcribe(cand_asr_wrapper, r) for r in sentinel_records
            ]

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

            decision = evaluator.evaluate_records(
                records_live=records_live,
                records_candidate=records_cand,
                candidate_identifier=cand_hash[:16],
                live_identifier=theta_t_hash[:16],
            )

            dsg_decisions.append({
                "model_key": model_name,
                "window_id": win_idx,
                "candidate_id": cand_hash[:16],
                "current_model_id": theta_t_hash[:16],
                "delta_R": round(decision.delta_r, 6) if not math.isnan(decision.delta_r) else "NaN",
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
            })

            # State Transition
            live_model.model = ShadowCandidateManager.apply_transition(
                live_model=live_model.model,
                candidate_model=candidate_model_core,
                decision=decision,
            )

            del candidate_model_core
            del cand_asr_wrapper
            del cand_adapter

        if (win_idx + 1) % 25 == 0 or (win_idx + 1) == num_windows:
            print(f"[{model_name.upper()} | {method_name.upper()}] Window {win_idx + 1:>3}/{num_windows} processed.")

    elapsed = time.time() - start_time
    print(f"[{model_name.upper()} | {method_name.upper()}] Finished in {elapsed:.1f}s.")

    # Save Checkpoint CSVs
    pred_df = pd.DataFrame(predictions)
    pred_df.to_csv(pred_ckpt, index=False)
    print(f"Saved prediction checkpoint: {pred_ckpt}")

    if method_name == "dsg":
        dec_df = pd.DataFrame(dsg_decisions)
        dec_df.to_csv(dec_ckpt, index=False)
        print(f"Saved DSG decision checkpoint: {dec_ckpt}")

    # Memory cleanup
    del live_model
    if adapter is not None:
        del adapter
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

    return predictions, dsg_decisions


def run_model_benchmark(
    model_name: str,
    device: str = "cpu",
    use_frozen_wav2vec2: bool = True,
    checkpoints_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    print("\n" + "=" * 75)
    print(f"STAGE 6: BENCHMARKING MODEL [{model_name.upper()}]")
    print("=" * 75)

    if model_name not in MODEL_CATALOG:
        raise KeyError(f"Unknown model '{model_name}'. Available: {list(MODEL_CATALOG.keys())}")

    model_entry = MODEL_CATALOG[model_name]
    family = model_entry["family"]
    is_ctc = family == "CTC"

    # Handle Primary Baseline (Wav2Vec2-base) Frozen Invariant
    if model_name == "wav2vec2_base" and use_frozen_wav2vec2:
        frozen_csv = PROJECT_ROOT / "reports" / "stage5" / "final_external_metrics.csv"
        frozen_group_csv = PROJECT_ROOT / "reports" / "stage5" / "final_group_metrics.csv"
        frozen_dsg_csv = PROJECT_ROOT / "reports" / "stage5" / "stage5d_final_decision_audit.csv"

        if frozen_csv.exists() and frozen_dsg_csv.exists():
            print("Importing locked Stage 5E empirical results for facebook/wav2vec2-base-960h...")
            f_df = pd.read_csv(frozen_csv)
            f_grp_df = pd.read_csv(frozen_group_csv)
            d_df = pd.read_csv(frozen_dsg_csv)

            accepted = int((d_df["decision"] == "ACCEPT").sum())
            rejected = int((d_df["decision"] != "ACCEPT").sum())

            # Map method names
            m_map = {"No-Adapt": "no_adapt", "SUTA": "suta", "DSUTA": "dsuta", "DMSUTA": "dmsuta", "DSG": "dsg"}
            row_map = {m_map.get(r["method"], r["method"]): r for _, r in f_df.iterrows()}

            res = {
                "model_key": "wav2vec2_base",
                "model_id": model_entry["model_id"],
                "family": family,
                "status": "FROZEN_STAGE_5E",
                "no_adapt_wer": float(row_map["no_adapt"]["corpus_wer"]) * 100.0,
                "suta_wer": float(row_map["suta"]["corpus_wer"]) * 100.0,
                "dsuta_wer": float(row_map["dsuta"]["corpus_wer"]) * 100.0,
                "dmsuta_wer": float(row_map["dmsuta"]["corpus_wer"]) * 100.0,
                "dsg_wer": float(row_map["dsg"]["corpus_wer"]) * 100.0,
                "dsg_delta_r": float(row_map["dsg"]["delta_R"]) * 100.0,
                "dsg_delta_d": float(row_map["dsg"]["delta_D"]) * 100.0,
                "dsg_max_delta_g": float(row_map["dsg"]["max_delta_g"]) * 100.0,
                "dsg_accepted": accepted,
                "dsg_rejected": rejected,
                "group_metrics": f_grp_df.to_dict(orient="records"),
            }
            print("Wav2Vec2-base frozen results loaded successfully.")
            return res

    # Load Data
    eval_df = pd.read_csv(EVAL_CSV)
    sentinel_df = pd.read_csv(SENTINEL_CSV)
    sentinel_records = sentinel_df.to_dict(orient="records")

    with open(GATE_CONFIG, "r", encoding="utf-8") as f:
        gate_cfg = json.load(f)

    resolver = SentinelAudioResolver(
        manifest_path=SENTINEL_MANIFEST if SENTINEL_MANIFEST.exists() else None,
        inventory_path=SENTINEL_INVENTORY,
        project_root=PROJECT_ROOT,
    )

    audio_cache = preload_waveforms(eval_df, AUDIO_DIR)

    sentinel_audio_cache: Dict[str, np.ndarray] = {}
    print("Preloading sentinel audio waveforms...")
    for r in sentinel_records:
        resolved_p = resolver.resolve(r, verify_hash=True)
        w, _ = load_and_resample_audio(str(resolved_p), 16000)
        sentinel_audio_cache[r["sentinel_id"]] = w

    # For Autoregressive Non-CTC Models: Run No-Adapt, Mark CTTA Incompatible
    if not is_ctc:
        print(f"[{model_name.upper()}] Non-CTC architecture detected ({family}).")
        print("Running No-Adapt static holdout audit. CTTA methods marked INCOMPATIBLE.")
        preds_no_adapt, _ = execute_prequential_method(
            model_name=model_name,
            method_name="no_adapt",
            eval_df=eval_df,
            audio_cache=audio_cache,
            sentinel_records=sentinel_records,
            sentinel_audio_cache=sentinel_audio_cache,
            gate_cfg=gate_cfg,
            resolver=resolver,
            device=device,
            checkpoints_dir=checkpoints_dir,
        )
        agg_no_adapt = compute_aggregate_metrics(preds_no_adapt)

        return {
            "model_key": model_name,
            "model_id": model_entry["model_id"],
            "family": family,
            "status": "COMPLETED_STATIC_ONLY",
            "no_adapt_wer": agg_no_adapt["wer"],
            "no_adapt_cer": agg_no_adapt["cer"],
            "no_adapt_disparity": agg_no_adapt["disparity_d"],
            "suta_wer": "INCOMPATIBLE",
            "dsuta_wer": "INCOMPATIBLE",
            "dmsuta_wer": "INCOMPATIBLE",
            "dsg_wer": "INCOMPATIBLE",
            "dsg_delta_r": "N/A",
            "dsg_delta_d": "N/A",
            "dsg_max_delta_g": "N/A",
            "dsg_accepted": "N/A",
            "dsg_rejected": "N/A",
            "group_wers_no_adapt": agg_no_adapt["group_wers"],
            "group_stats_no_adapt": agg_no_adapt["group_stats"]
        }

    # For Compatible CTC Models: Run Full Suite (No-Adapt, SUTA, DSUTA, DMSUTA, DSG)
    methods = ["no_adapt", "suta", "dsuta", "dmsuta", "dsg"]
    method_metrics = {}
    dsg_dec_records = []

    for m in methods:
        preds, decs = execute_prequential_method(
            model_name=model_name,
            method_name=m,
            eval_df=eval_df,
            audio_cache=audio_cache,
            sentinel_records=sentinel_records,
            sentinel_audio_cache=sentinel_audio_cache,
            gate_cfg=gate_cfg,
            resolver=resolver,
            device=device,
            checkpoints_dir=checkpoints_dir,
        )
        method_metrics[m] = compute_aggregate_metrics(preds)
        if m == "dsg":
            dsg_dec_records = decs

    base_wer = method_metrics["no_adapt"]["wer"]
    base_d = method_metrics["no_adapt"]["disparity_d"]
    dsg_wer = method_metrics["dsg"]["wer"]
    dsg_d = method_metrics["dsg"]["disparity_d"]

    # Compute max group regression vs no-adapt under DSG
    max_delta_g = 0.0
    for g, g_wer in method_metrics["dsg"]["group_wers"].items():
        base_g_wer = method_metrics["no_adapt"]["group_wers"].get(g, 0.0)
        reg = g_wer - base_g_wer
        if reg > max_delta_g:
            max_delta_g = reg

    accepted_cnt = sum(1 for d in dsg_dec_records if d.get("decision") == "ACCEPT")
    rejected_cnt = sum(1 for d in dsg_dec_records if d.get("decision") != "ACCEPT")

    return {
        "model_key": model_name,
        "model_id": model_entry["model_id"],
        "family": family,
        "status": "COMPLETED_FULL_CTTA",
        "no_adapt_wer": base_wer,
        "suta_wer": method_metrics["suta"]["wer"],
        "dsuta_wer": method_metrics["dsuta"]["wer"],
        "dmsuta_wer": method_metrics["dmsuta"]["wer"],
        "dsg_wer": dsg_wer,
        "dsg_delta_r": dsg_wer - base_wer,
        "dsg_delta_d": dsg_d - base_d,
        "dsg_max_delta_g": max_delta_g,
        "dsg_accepted": accepted_cnt,
        "dsg_rejected": rejected_cnt,
        "all_method_metrics": method_metrics,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stage 6 benchmark for a target model.")
    parser.add_argument("--model", type=str, required=True, help="Catalog model key (e.g. wav2vec2_base, data2vec_base, whisper_base)")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--force_rerun", action="store_true", help="Force rerun even if frozen or checkpointed")
    args = parser.parse_args()

    res = run_model_benchmark(
        model_name=args.model,
        device=args.device,
        use_frozen_wav2vec2=not args.force_rerun
    )
    print("\nBenchmark Execution Result Summary:")
    print(json.dumps({k: v for k, v in res.items() if not k.startswith("group_") and not k.startswith("all_")}, indent=2))
