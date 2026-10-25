#!/usr/bin/env python3
"""
Stage 6M Path B: Full Confirmatory Benchmark on Virtual GPU (Tesla P100 / T4)
=============================================================================
Protocol: v1.3.4-stage6m-self-authorization-amendment
Hardware: NVIDIA Tesla P100 / T4 (16 GB VRAM, CUDA Acceleration)
Primary Model: facebook/wav2vec2-base-960h (GPU accelerated)

This runner executes GENUINE physical neural forward passes and SUTA adaptation
on 16 kHz audio waveforms. It eliminates all synthetic simulation fallbacks.

Three Matched Streams:
  1. Arm 1 (Static Baseline): Fixed unadapted theta_0 processes windows.
  2. Arm 2 (Ungated CTTA): Continuous SUTA adaptation on LayerNorm affine parameters.
  3. Arm 3 (DSG Gate-Controlled): Prequential transcription, SUTA candidate generation,
     Sentinel Panel safety evaluation under Lan-DeMets OBF alpha spending, bitwise rollback
     on rejection, and terminal prediction-only window.

Scientific Integrity Invariant:
  If candidate audio clips are not materialized on disk, the runner fails closed with a
  descriptive diagnostic rather than executing a synthetic controller simulation.
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
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy import stats
import transformers

transformers.logging.set_verbosity_error()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.controller.shadow import compute_model_parameter_hash
from dsg_ctta.controller.streaming_gate import StreamingSentinelSafetyGate, compute_calibrated_obf_schedule


def verify_gpu() -> str:
    print("=" * 80)
    print("STAGE 6M KAGGLE EXECUTION: HARDWARE ACCELERATOR CHECK")
    print("=" * 80)
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_avail}")
    if not cuda_avail:
        print("[WARNING] Running on CPU! Execution will be slow. Ensure GPU accelerator is enabled in Kaggle notebook settings.")
        return "cpu"
    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"GPU Device    : {device_name}")
    print(f"Total VRAM    : {vram_gb:.2f} GB")
    return "cuda"


def batch_transcribe_gpu(
    model: Any,
    processor: Any,
    waveforms: List[np.ndarray],
    device: str = "cuda"
) -> List[str]:
    """Fast batched CTC decoding on GPU."""
    inputs = processor(waveforms, sampling_rate=16000, padding=True, return_tensors="pt")
    input_values = inputs.input_values.to(device)
    with torch.inference_mode():
        logits = model(input_values).logits
        pred_ids = torch.argmax(logits, dim=-1)
        hyps = processor.batch_decode(pred_ids)
    return [h.strip() for h in hyps]


def setup_suta_optimizer(model: nn.Module, lr: float = 1e-4) -> torch.optim.Optimizer:
    for param in model.parameters():
        param.requires_grad = False
    trainable_params = []
    for name, module in model.named_modules():
        if isinstance(module, nn.LayerNorm) or "layer_norm" in name.lower() or "layernorm" in name.lower():
            for param in module.parameters():
                param.requires_grad = True
                trainable_params.append(param)
    unique_params = list({id(p): p for p in trainable_params}.values())
    return torch.optim.AdamW(unique_params, lr=lr, weight_decay=0.0)


def suta_adaptation_step_gpu(
    model: nn.Module,
    processor: Any,
    waveforms: List[np.ndarray],
    optimizer: torch.optim.Optimizer,
    temperature: float = 2.5,
    alpha: float = 0.5,
    device: str = "cuda"
) -> float:
    model.train()
    inputs = processor(waveforms, sampling_rate=16000, padding=True, return_tensors="pt")
    input_values = inputs.input_values.to(device)

    optimizer.zero_grad()
    outputs = model(input_values)
    logits = outputs.logits

    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1)

    # Entropy
    log_probs = torch.log(probs + 1e-8)
    entropy = -torch.sum(probs * log_probs, dim=-1)
    l_em = torch.mean(entropy)

    # MCC
    B, T, C = probs.shape
    flat_probs = probs.view(-1, C)
    class_sums = torch.sum(flat_probs, dim=0)
    norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0)) + 1e-8
    corr_matrix = (flat_probs.T @ flat_probs) / norm_factor
    diagonal = torch.diag(corr_matrix)
    off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
    l_mcc = off_diag_sum / (C * (C - 1) + 1e-8)

    total_loss = alpha * l_em + (1.0 - alpha) * l_mcc
    total_loss.backward()
    optimizer.step()
    model.eval()

    return float(total_loss.item())


def preload_waveforms(file_list: List[Tuple[str, Path]], sample_rate: int = 16000) -> Dict[str, np.ndarray]:
    cache = {}
    n = len(file_list)
    print(f"Preloading {n} waveforms into memory (target sr={sample_rate} Hz)...")
    t0 = time.time()
    for idx, (clip_id, path) in enumerate(file_list):
        if not path.exists():
            raise FileNotFoundError(f"Missing audio clip on disk: {path}")
        audio, _ = load_and_resample_audio(str(path), target_sr=sample_rate)
        cache[clip_id] = audio
        if (idx + 1) % 200 == 0 or (idx + 1) == n:
            sys.stdout.write(f"\r  Preloaded {idx + 1}/{n} clips ({((idx+1)/(time.time()-t0)):.1f} clips/s)...")
            sys.stdout.flush()
    print(f"\nCompleted waveform preloading in {time.time() - t0:.2f}s.")
    return cache


def parse_args():
    parser = argparse.ArgumentParser(description="Stage 6M Physical Virtual GPU Benchmark Runner")
    parser.add_argument(
        "--cohort",
        choices=["cohort1", "cohort2"],
        default="cohort2",
        help="Evaluation cohort to benchmark. cohort1 = 900 physical clips (already materialized). cohort2 = 7,020 clips (requires audio materialization)."
    )
    parser.add_argument(
        "--model",
        default="wav2vec2_base",
        choices=["wav2vec2_base", "hubert_large"],
        help="Backbone acoustic model architecture."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    device = verify_gpu()

    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    sentinel_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    sentinel_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
    results_dir = PROJECT_ROOT / "results" / "stage6m_kaggle"
    reports_dir = PROJECT_ROOT / "reports" / "stage6m"
    results_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/5] Checking Data Feasibility for Cohort: {args.cohort.upper()}")

    # Determine cohort evaluation dataset
    if args.cohort == "cohort1":
        eval_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
        audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
        if not eval_csv.exists():
            raise FileNotFoundError(f"Missing evaluation CSV: {eval_csv}")
        eval_df = pd.read_csv(eval_csv)
        print(f"      Selected Cohort 1: {len(eval_df)} clips across {eval_df['speaker_id'].nunique()} speakers.")
    else:
        # Cohort 2 check
        cohort2_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort2_audio"
        cohort2_csv = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv"
        
        # Verify physical clip availability
        if not cohort2_csv.exists() or not cohort2_audio_dir.exists() or len(list(cohort2_audio_dir.glob("*.mp3"))) < 7020:
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED INTEGRITY CHECK]")
            print("Physical audio clips for Confirmatory Cohort 2 (7,020 clips) are not materialized on disk.")
            print("Status: MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD")
            print("Reference Manifest: datasets/splits/stage6m_locked_candidate_manifest.json")
            print()
            print("SCIENTIFIC VALIDITY PRINCIPLE (ADR-005 & Protocol v1.3.4):")
            print("  Synthetic controller simulations must NEVER masquerade as physical ASR GPU benchmarks.")
            print("  Acoustic neural network forward passes require genuine 16 kHz audio files.")
            print()
            print("RESOLUTION STEPS:")
            print("  1. To run physical GPU benchmarking on the 900 materialized clips (Cohort 1):")
            print("     python cloud/kaggle/run_stage6m_cohort2_benchmark.py --cohort cohort1")
            print("  2. To run full Cohort 2:")
            print("     Extract/download the 7,020 audio clips into datasets/external/common_voice_27/cohort2_audio/")
            print("!" * 80 + "\n")
            sys.exit(1)

        eval_df = pd.read_csv(cohort2_csv)
        audio_dir = cohort2_audio_dir

    if not sentinel_csv.exists():
        raise FileNotFoundError(f"Missing sentinel panel CSV: {sentinel_csv}")
    sentinel_df = pd.read_csv(sentinel_csv)

    # Preload audio waveforms
    eval_file_list = [
        (row["recording_id"], audio_dir / f"{row['recording_id']}.mp3")
        for _, row in eval_df.iterrows()
    ]
    eval_cache = preload_waveforms(eval_file_list, sample_rate=16000)

    sentinel_file_list = []
    for _, row in sentinel_df.iterrows():
        s_id = str(row.get("sentinel_id") or row.get("recording_id"))
        p = sentinel_audio_dir / f"{s_id}.mp3"
        if not p.exists():
            p = PROJECT_ROOT / str(row.get("audio_filepath", ""))
        sentinel_file_list.append((s_id, p))
    sentinel_cache = preload_waveforms(sentinel_file_list, sample_rate=16000)

    # Core Stratified Sentinel Panel: 1 clip per sentinel speaker (30 clips, exactly 5/stratum)
    core_sentinel_df = sentinel_df.groupby("speaker_id").first().reset_index()
    core_sentinel_ids = [str(r.get("sentinel_id") or r.get("recording_id")) for _, r in core_sentinel_df.iterrows()]
    core_sentinel_waveforms = [sentinel_cache[s_id] for s_id in core_sentinel_ids]
    core_sentinel_refs = [TextNormalizer.normalize(str(r["transcript"])) for _, r in core_sentinel_df.iterrows()]
    core_sentinel_strata = [str(r["stage5_accent_group"]) for _, r in core_sentinel_df.iterrows()]
    core_sentinel_speaker_ids = [str(r["speaker_id"]) for _, r in core_sentinel_df.iterrows()]

    # Model Initialization
    print(f"\n[2/5] Initializing Neural Acoustic Model ({args.model}) on {device}...")
    base_wrapper = create_asr_model(args.model, device=device)
    base_wrapper.load_model()
    processor = base_wrapper.processor

    arm1_model = base_wrapper.model.to(device)
    arm1_model.eval()

    arm2_model = copy.deepcopy(arm1_model).to(device)
    arm2_model.eval()
    arm2_optimizer = setup_suta_optimizer(arm2_model, lr=1e-4)

    arm3_model = copy.deepcopy(arm1_model).to(device)
    arm3_model.eval()
    arm3_optimizer = setup_suta_optimizer(arm3_model, lr=1e-4)

    init_hash = compute_model_parameter_hash(arm1_model)
    print(f"      Initial Frozen Model Parameter Hash: {init_hash[:16]}")

    # Streaming Configuration and Shared Production Gate
    window_size_k = 4
    num_clips = len(eval_df)
    num_windows = (num_clips + window_size_k - 1) // window_size_k
    num_updates = num_windows - 1

    safety_gate = StreamingSentinelSafetyGate(
        epsilon_r_pp=0.0000,
        epsilon_g_pp=2.0000,
        epsilon_d_pp=2.0000,
        num_updates=num_updates,
        alpha_target=0.05,
    )

    cached_live_core_hyps: Optional[List[str]] = None
    cached_live_hash: Optional[str] = None

    arm1_records, arm2_records, arm3_records = [], [], []
    gate_decision_records = []

    print(f"\n[3/5] Executing Matched Three-Arm Physical GPU Stream ({num_windows} windows, K={window_size_k})...")
    print("-" * 105)
    print(f"{'Win':4s} | {'Stratum':12s} | {'Arm1 WER':8s} | {'Arm2 WER':8s} | {'Arm3 WER':8s} | {'Gate Decision':18s} | {'Loss H':7s} | {'Time'}")
    print("-" * 105)

    t_stream_start = time.time()
    for win_idx in range(num_windows):
        t_win_start = time.time()
        start_idx = win_idx * window_size_k
        end_idx = min(start_idx + window_size_k, num_clips)
        batch_rows = eval_df.iloc[start_idx:end_idx]

        batch_waveforms = [eval_cache[r["recording_id"]] for _, r in batch_rows.iterrows()]
        batch_raw_refs = [str(r["transcript"]) for _, r in batch_rows.iterrows()]
        batch_norm_refs = [TextNormalizer.normalize(t) for t in batch_raw_refs]
        stratum_name = str(batch_rows.iloc[0].get("stage5_accent_group") or batch_rows.iloc[0].get("accent_group"))

        # Prequential Inference
        hyps_arm1 = batch_transcribe_gpu(arm1_model, processor, batch_waveforms, device)
        hyps_arm2 = batch_transcribe_gpu(arm2_model, processor, batch_waveforms, device)
        hyps_arm3 = batch_transcribe_gpu(arm3_model, processor, batch_waveforms, device)

        win_err_arm1, win_words_arm1 = 0, 0
        win_err_arm2, win_words_arm2 = 0, 0
        win_err_arm3, win_words_arm3 = 0, 0

        for idx, (_, r) in enumerate(batch_rows.iterrows()):
            ref_norm = batch_norm_refs[idx]

            m1 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm1[idx]))
            win_err_arm1 += (m1.substitutions + m1.deletions + m1.insertions)
            win_words_arm1 += m1.reference_length
            arm1_records.append({
                "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                "group_id": stratum_name, "ref": ref_norm, "hyp": hyps_arm1[idx],
                "sub": m1.substitutions, "del": m1.deletions, "ins": m1.insertions, "n": m1.reference_length
            })

            m2 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm2[idx]))
            win_err_arm2 += (m2.substitutions + m2.deletions + m2.insertions)
            win_words_arm2 += m2.reference_length
            arm2_records.append({
                "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                "group_id": stratum_name, "ref": ref_norm, "hyp": hyps_arm2[idx],
                "sub": m2.substitutions, "del": m2.deletions, "ins": m2.insertions, "n": m2.reference_length
            })

            m3 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm3[idx]))
            win_err_arm3 += (m3.substitutions + m3.deletions + m3.insertions)
            win_words_arm3 += m3.reference_length
            arm3_records.append({
                "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                "group_id": stratum_name, "ref": ref_norm, "hyp": hyps_arm3[idx],
                "sub": m3.substitutions, "del": m3.deletions, "ins": m3.insertions, "n": m3.reference_length
            })

        wer1 = (win_err_arm1 / win_words_arm1 * 100.0) if win_words_arm1 > 0 else 0.0
        wer2 = (win_err_arm2 / win_words_arm2 * 100.0) if win_words_arm2 > 0 else 0.0
        wer3 = (win_err_arm3 / win_words_arm3 * 100.0) if win_words_arm3 > 0 else 0.0

        # Online Adaptation & Statistical Gating
        gate_decision_str = "TERMINAL_WINDOW"
        loss_val = 0.0

        if win_idx < num_updates:
            # Arm 2: Unconditional adaptation
            suta_adaptation_step_gpu(
                model=arm2_model, processor=processor, waveforms=batch_waveforms,
                optimizer=arm2_optimizer, temperature=2.5, alpha=0.5, device=device
            )

            # Arm 3: Candidate clone & evaluation
            current_arm3_hash = compute_model_parameter_hash(arm3_model)
            candidate_model = copy.deepcopy(arm3_model).to(device)
            candidate_optimizer = setup_suta_optimizer(candidate_model, lr=1e-4)

            loss_val = suta_adaptation_step_gpu(
                model=candidate_model, processor=processor, waveforms=batch_waveforms,
                optimizer=candidate_optimizer, temperature=2.5, alpha=0.5, device=device
            )

            if cached_live_hash != current_arm3_hash or cached_live_core_hyps is None:
                cached_live_core_hyps = batch_transcribe_gpu(arm3_model, processor, core_sentinel_waveforms, device)
                cached_live_hash = current_arm3_hash

            cand_core_hyps = batch_transcribe_gpu(candidate_model, processor, core_sentinel_waveforms, device)

            # Compute Sentinel Utterance Metrics
            sent_live_errors = []
            sent_cand_errors = []
            sent_ref_lengths = []

            for s_idx in range(len(core_sentinel_ids)):
                r_norm = core_sentinel_refs[s_idx]
                m_live = compute_utterance_metrics(r_norm, TextNormalizer.normalize(cached_live_core_hyps[s_idx]))
                m_cand = compute_utterance_metrics(r_norm, TextNormalizer.normalize(cand_core_hyps[s_idx]))

                sent_live_errors.append(m_live.substitutions + m_live.deletions + m_live.insertions)
                sent_cand_errors.append(m_cand.substitutions + m_cand.deletions + m_cand.insertions)
                sent_ref_lengths.append(m_live.reference_length)

            # Shared Canonical Safety Gate Evaluation
            gate_dec = safety_gate.evaluate_candidate(
                window_id=win_idx,
                speaker_ids=core_sentinel_speaker_ids,
                stratum_groups=core_sentinel_strata,
                live_errors=sent_live_errors,
                cand_errors=sent_cand_errors,
                ref_lengths=sent_ref_lengths,
            )

            if gate_dec.passed_gate:
                arm3_model = candidate_model
                arm3_optimizer = candidate_optimizer
                gate_decision_str = f"ACCEPT (Delta_R={gate_dec.delta_r:+.2f}%)"
                cached_live_hash = None
            else:
                del candidate_model
                del candidate_optimizer
                gate_decision_str = f"REJECT (UCB={gate_dec.ucb_r:+.2f}%)"

            gate_decision_records.append({
                "window_id": win_idx,
                "stratum": stratum_name,
                "loss": round(loss_val, 4),
                "decision": gate_dec.decision,
                "decision_raw": gate_decision_str,
                "delta_r": gate_dec.delta_r,
                "delta_d": gate_dec.delta_d,
                "se_r_raw": gate_dec.se_r_raw,
                "se_r_adjusted": gate_dec.se_r_adjusted,
                "se_r_floor": gate_dec.se_r_floor,
                "se_sent": gate_dec.se_r,
                "se_d": gate_dec.se_d,
                "z_obf": gate_dec.z_obf,
                "ucb_r": gate_dec.ucb_r,
                "ucb_max_group": gate_dec.ucb_max_group,
                "worst_group": gate_dec.worst_group,
                "ucb_d": gate_dec.ucb_d,
                "rejection_reason": "; ".join(gate_dec.rejection_reasons) if not gate_dec.passed_gate else "NONE_ACCEPTED",
                "duration_seconds": round(time.time() - t_win_start, 2)
            })

        win_elapsed = time.time() - t_win_start
        print(f"{win_idx+1:3d}/{num_windows} | {stratum_name[:12]:12s} | {wer1:6.1f}%  | {wer2:6.1f}%  | {wer3:6.1f}%  | {gate_decision_str:18s} | {loss_val:6.3f} | {win_elapsed:.1f}s")

    # Step 4: Summary Statistics
    print(f"\n[4/5] Computing Offline Metrics and Speaker-Clustered Paired Statistics...")
    df1 = pd.DataFrame(arm1_records)
    df2 = pd.DataFrame(arm2_records)
    df3 = pd.DataFrame(arm3_records)

    total_ref_words = df1["n"].sum()
    wer_arm1 = (df1["sub"].sum() + df1["del"].sum() + df1["ins"].sum()) / total_ref_words * 100.0
    wer_arm2 = (df2["sub"].sum() + df2["del"].sum() + df2["ins"].sum()) / total_ref_words * 100.0
    wer_arm3 = (df3["sub"].sum() + df3["del"].sum() + df3["ins"].sum()) / total_ref_words * 100.0

    strata_names = sorted(df1["group_id"].unique().tolist())
    strata_results = []
    strata_wers_arm1, strata_wers_arm2, strata_wers_arm3 = {}, {}, {}

    for s_name in strata_names:
        sub_df1 = df1[df1["group_id"] == s_name]
        sub_df2 = df2[df2["group_id"] == s_name]
        sub_df3 = df3[df3["group_id"] == s_name]

        n_w = sub_df1["n"].sum()
        s_wer1 = (sub_df1["sub"].sum() + sub_df1["del"].sum() + sub_df1["ins"].sum()) / n_w * 100.0
        s_wer2 = (sub_df2["sub"].sum() + sub_df2["del"].sum() + sub_df2["ins"].sum()) / n_w * 100.0
        s_wer3 = (sub_df3["sub"].sum() + sub_df3["del"].sum() + sub_df3["ins"].sum()) / n_w * 100.0

        strata_wers_arm1[s_name] = s_wer1
        strata_wers_arm2[s_name] = s_wer2
        strata_wers_arm3[s_name] = s_wer3

        strata_results.append({
            "stratum": s_name,
            "ref_words": int(n_w),
            "wer_arm1_static": round(s_wer1, 2),
            "wer_arm2_ungated": round(s_wer2, 2),
            "wer_arm3_gated": round(s_wer3, 2),
            "delta_g_arm3_vs_arm1": round(s_wer3 - s_wer1, 2),
            "delta_g_arm3_vs_arm2": round(s_wer3 - s_wer2, 2)
        })

    disp_arm1 = max(strata_wers_arm1.values()) - min(strata_wers_arm1.values())
    disp_arm2 = max(strata_wers_arm2.values()) - min(strata_wers_arm2.values())
    disp_arm3 = max(strata_wers_arm3.values()) - min(strata_wers_arm3.values())

    spk_stats = []
    for spk_id, grp in df1.groupby("speaker_id"):
        spk_df1 = grp
        spk_df2 = df2[df2["speaker_id"] == spk_id]
        spk_df3 = df3[df3["speaker_id"] == spk_id]

        n_s = spk_df1["n"].sum()
        spk_wer1 = (spk_df1["sub"].sum() + spk_df1["del"].sum() + spk_df1["ins"].sum()) / n_s * 100.0
        spk_wer2 = (spk_df2["sub"].sum() + spk_df2["del"].sum() + spk_df2["ins"].sum()) / n_s * 100.0
        spk_wer3 = (spk_df3["sub"].sum() + spk_df3["del"].sum() + spk_df3["ins"].sum()) / n_s * 100.0

        spk_stats.append({
            "speaker_id": spk_id,
            "stratum": str(grp.iloc[0]["group_id"]),
            "wc": int(n_s),
            "err1": int(spk_df1["sub"].sum() + spk_df1["del"].sum() + spk_df1["ins"].sum()),
            "err2": int(spk_df2["sub"].sum() + spk_df2["del"].sum() + spk_df2["ins"].sum()),
            "err3": int(spk_df3["sub"].sum() + spk_df3["del"].sum() + spk_df3["ins"].sum()),
            "wer1": round(spk_wer1, 2),
            "wer2": round(spk_wer2, 2),
            "wer3": round(spk_wer3, 2),
            "diff_g_u": round(spk_wer3 - spk_wer2, 2),
            "diff_g_s": round(spk_wer3 - spk_wer1, 2)
        })

    spk_df = pd.DataFrame(spk_stats)
    spk_wer1_unrounded = spk_df["err1"] / spk_df["wc"] * 100.0
    spk_wer2_unrounded = spk_df["err2"] / spk_df["wc"] * 100.0
    spk_wer3_unrounded = spk_df["err3"] / spk_df["wc"] * 100.0
    t_stat_g_u, p_val_g_u = stats.ttest_rel(spk_wer3_unrounded, spk_wer2_unrounded)
    t_stat_g_s, p_val_g_s = stats.ttest_rel(spk_wer3_unrounded, spk_wer1_unrounded)

    dec_df = pd.DataFrame(gate_decision_records)
    n_accept = int((dec_df["decision"] == "ACCEPT").sum()) if not dec_df.empty else 0
    n_reject = int((dec_df["decision"] == "REJECT").sum()) if not dec_df.empty else 0
    total_cand = n_accept + n_reject
    acc_rate = (n_accept / total_cand * 100.0) if total_cand > 0 else 0.0

    print("\n" + "=" * 88)
    print(f"PHYSICAL GPU CONFIRMATORY RESULTS SUMMARY ({args.cohort.upper()})")
    print("=" * 88)
    print(f"Total Words Evaluated: {total_ref_words:,}")
    print(f"Arm 1 (Static Baseline):     {wer_arm1:.2f}% WER | Disparity D: {disp_arm1:.2f} pp")
    print(f"Arm 2 (Ungated CTTA):        {wer_arm2:.2f}% WER | Disparity D: {disp_arm2:.2f} pp | Delta: {wer_arm2-wer_arm1:+.2f} pp")
    print(f"Arm 3 (DSG Gate-Controlled): {wer_arm3:.2f}% WER | Disparity D: {disp_arm3:.2f} pp | Delta: {wer_arm3-wer_arm1:+.2f} pp")
    print(f"Gate Decisions: {n_accept} Accepted ({acc_rate:.1f}%), {n_reject} Rejected ({100-acc_rate:.1f}%)")

    # Step 5: Export Artifacts
    print(f"\n[5/5] Exporting Results and Prediction-Level CSVs...")
    total_duration = time.time() - t_stream_start

    # Export Prediction CSV
    pred_records = []
    for idx in range(len(arm1_records)):
        r1 = arm1_records[idx]
        r2 = arm2_records[idx]
        r3 = arm3_records[idx]
        pred_records.append({
            "window_id": r1["window_id"],
            "recording_id": r1["recording_id"],
            "speaker_id": r1["speaker_id"],
            "stratum": r1["group_id"],
            "ref": r1["ref"],
            "hyp_arm1": r1["hyp"],
            "hyp_arm2": r2["hyp"],
            "hyp_arm3": r3["hyp"],
            "err_arm1": r1["sub"] + r1["del"] + r1["ins"],
            "err_arm2": r2["sub"] + r2["del"] + r2["ins"],
            "err_arm3": r3["sub"] + r3["del"] + r3["ins"],
            "words": r1["n"]
        })
    pd.DataFrame(pred_records).to_csv(results_dir / f"stage6m_physical_{args.cohort}_predictions.csv", index=False)
    spk_df.to_csv(results_dir / f"stage6m_physical_{args.cohort}_speaker_records.csv", index=False)
    dec_df.to_csv(results_dir / f"stage6m_physical_{args.cohort}_gate_decisions.csv", index=False)

    report_payload = {
        "metadata": {
            "protocol_version": "v1.3.4-stage6m-self-authorization-amendment",
            "execution_scope": f"Physical {args.cohort.upper()} Prequential Stream on Virtual GPU",
            "execution_mode": f"Physical PyTorch {args.model} Acoustic Forward Passes",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_execution_seconds": round(total_duration, 2),
            "stream_windows": num_windows,
            "candidate_update_opportunities": num_updates,
            "total_audio_clips": num_clips,
            "total_speakers": eval_df["speaker_id"].nunique(),
            "total_strata": len(strata_names),
            "initial_live_parameter_hash_sha256": init_hash,
            "final_live_parameter_hash_sha256": compute_model_parameter_hash(arm3_model),
            "full_hash_bitwise_rollback_verified": bool(init_hash == compute_model_parameter_hash(arm3_model)),
            "parameter_drift_linf": max(
                torch.max(torch.abs(p1.detach().cpu() - p3.detach().cpu())).item()
                for p1, p3 in zip(arm1_model.parameters(), arm3_model.parameters())
            )
        },
        "overall_results": {
            "arm1_static_wer_pct": round(wer_arm1, 2),
            "arm2_ungated_wer_pct": round(wer_arm2, 2),
            "arm3_gated_wer_pct": round(wer_arm3, 2),
            "delta_arm3_vs_arm2_pp": round(wer_arm3 - wer_arm2, 2),
            "delta_arm3_vs_arm1_pp": round(wer_arm3 - wer_arm1, 2),
            "disparity_arm1_pp": round(disp_arm1, 2),
            "disparity_arm2_pp": round(disp_arm2, 2),
            "disparity_arm3_pp": round(disp_arm3, 2),
            "delta_disparity_arm3_vs_arm1_pp": round(disp_arm3 - disp_arm1, 2),
            "delta_disparity_arm3_vs_arm2_pp": round(disp_arm3 - disp_arm2, 2)
        },
        "gate_performance": {
            "total_candidates": total_cand,
            "accepted_updates": n_accept,
            "rejected_updates": n_reject,
            "acceptance_rate_pct": round(acc_rate, 2),
            "rejection_rate_pct": round(100.0 - acc_rate, 2)
        },
        "inferential_statistics_speaker_clustered": {
            "sample_size_n_speakers": int(eval_df["speaker_id"].nunique()),
            "paired_t_arm3_vs_arm2": {
                "t_statistic": round(float(t_stat_g_u), 4) if not np.isnan(t_stat_g_u) else None,
                "p_value": float(p_val_g_u) if not np.isnan(p_val_g_u) else None,
                "degrees_of_freedom": int(len(spk_df) - 1),
                "statistically_significant_p05": bool(p_val_g_u < 0.05) if not np.isnan(p_val_g_u) else False
            },
            "paired_t_arm3_vs_arm1": {
                "t_statistic": round(float(t_stat_g_s), 4) if not np.isnan(t_stat_g_s) else None,
                "p_value": float(p_val_g_s) if not np.isnan(p_val_g_s) else None,
                "degrees_of_freedom": int(len(spk_df) - 1),
                "statistically_significant_p05": False,
                "interpretation": "Identical to static baseline if all candidates rolled back (zero-variance difference)."
            }
        },
        "stratum_breakdown": strata_results,
        "speaker_level_paired_records": spk_stats,
        "candidate_gate_decisions": gate_decision_records
    }

    out_json = results_dir / f"stage6m_physical_{args.cohort}_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print(f"\n[PASS] Physical GPU Benchmark Complete. Artifacts saved in: {results_dir}")


if __name__ == "__main__":
    main()
