#!/usr/bin/env python3
"""
Stage 5M: Closed-Loop Online Control Suite Runner
=================================================
Protocol: v1.1.0-model-expansion
Standard: ADR-005
Review Decision: CONDITIONAL GO — Authorized for Controlled Research Evaluation

Executes the frozen Stage 5M Closed-Loop Online Control matrix:
- Evaluates whether the operational Disparity Safety Gate (DSG) prevents harmful
  continual test-time adaptation across 5 acoustic conditions, 3 CTC backbones,
  3 active adaptation methods, and 3 stream arrival orderings.
- Enforces strict isolation between operational sentinel decisions and retrospective labels.
- Computes operational vs. retrospective decision agreement/disagreement rates,
  specifically tracking false approvals (operational ACCEPT of retrospectively harmful updates).
- Seq2Seq models evaluated as static No-Adapt portability controls.

Outputs:
- results/stage5m/checkpoints/*.json
- results/stage5m/stage5m_operational_decisions.csv
- results/stage5m/stage5m_decision_agreement_matrix.csv
- results/stage5m/stage5m_closed_loop_results.csv
- reports/stage5m/stage5m_closed_loop_report.md
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import math
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import transformers

transformers.logging.set_verbosity_error()
warnings.filterwarnings("ignore", message=".*Both `max_new_tokens`.*")

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.resolver import SentinelAudioResolver
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash
from dsg_ctta.models.registry import create_asr_model, MODEL_CATALOG
from dsg_ctta.adaptation.base import BaseTestTimeAdapter
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.adaptation.dsuta import DsutaAdapter
from dsg_ctta.adaptation.dmsuta import DmsutaAdapter
from dsg_ctta.adaptation.no_adapt import NoAdaptationAdapter
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.online.stream import PrequentialStream
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, enforce_data_access_firewall
from dsg_ctta.offline.metrics import compute_utterance_metrics

# Paths
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
RESULTS_DIR = PROJECT_ROOT / "results" / "stage5m"
CHECKPOINTS_DIR = RESULTS_DIR / "checkpoints"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5m"
SENTINEL_CSV = SPLITS_DIR / "stage5_sentinel_panel.csv"
SENTINEL_MANIFEST = SPLITS_DIR / "stage5_sentinel_audio_manifest.json"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
SENTINEL_AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
GATE_CONFIG = PROJECT_ROOT / "configs" / "stage5_gate_config.json"

CONDITIONS = {
    "clean": "datasets/splits/stage4_characterization.csv",
    "noise_15db": "datasets/splits/stage4_noise_moderate.csv",
    "noise_5db": "datasets/splits/stage4_noise_severe.csv",
    "babble_15db": "datasets/splits/stage4_babble_moderate.csv",
    "reverb_t60_04": "datasets/splits/stage4_reverberation.csv"
}

CTC_MODELS = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
SEQ2SEQ_MODELS = ["whisper_base", "distil_whisper_small", "whisper_tiny"]
ACTIVE_METHODS = ["suta", "dsuta", "dmsuta"]
ALL_METHODS = ["no_adapt", "suta", "dsuta", "dmsuta"]
ORDERS = ["ORDER_A", "ORDER_B", "ORDER_C"]

ADAPTER_CONFIGS = {
    "no_adapt": {},
    "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
    "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
    "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
}


def resolve_audio_path(raw_path: str, project_root: Path) -> str:
    """Cross-platform audio filepath resolver handling relative/absolute paths."""
    p = Path(raw_path)
    if p.exists():
        return str(p)
    parts = p.parts
    if "datasets" in parts:
        idx = parts.index("datasets")
        rel = Path(*parts[idx:])
        candidate = project_root / rel
        if candidate.exists():
            return str(candidate)
    return str(project_root / raw_path)


def derive_run_seed(experiment_id: str, base_seed: int = 42) -> int:
    h = hashlib.sha256(f"{experiment_id}_{base_seed}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % (2**31 - 1)


def create_adapter_for_model(
    method_name: str,
    asr_model: Any,
    config: Optional[Dict[str, Any]] = None
) -> BaseTestTimeAdapter:
    cfg = config or ADAPTER_CONFIGS.get(method_name, {})
    m_lower = method_name.lower()
    if m_lower == "no_adapt":
        return NoAdaptationAdapter(asr_model=asr_model, config=cfg)
    elif m_lower == "suta":
        return SutaAdapter(asr_model=asr_model, config=cfg)
    elif m_lower == "dsuta":
        return DsutaAdapter(asr_model=asr_model, config=cfg)
    elif m_lower == "dmsuta":
        return DmsutaAdapter(asr_model=asr_model, config=cfg)
    else:
        raise ValueError(f"Unknown adaptation method: {method_name}")


def preload_sentinel_waveforms(
    sentinel_records: List[Dict[str, Any]],
    resolver: SentinelAudioResolver
) -> Dict[str, np.ndarray]:
    """Preload sentinel audio into RAM for fast inference during online control."""
    print(f"Preloading {len(sentinel_records)} sentinel audio waveforms into memory...")
    cache: Dict[str, np.ndarray] = {}
    for r in sentinel_records:
        s_id = r["sentinel_id"]
        resolved_p = resolver.resolve(r, verify_hash=False)
        w, _ = load_and_resample_audio(str(resolved_p), 16000)
        cache[s_id] = w
    print(f"Sentinel waveforms preloaded ({len(cache)} clips).")
    return cache


def preload_stream_waveforms(
    utterances: List[UtteranceMetadata],
    project_root: Path
) -> Dict[str, np.ndarray]:
    """Preload evaluation stream audio into RAM."""
    cache: Dict[str, np.ndarray] = {}
    for u in utterances:
        resolved_p = resolve_audio_path(u.audio_filepath, project_root)
        w, _ = load_and_resample_audio(resolved_p, 16000)
        cache[u.utterance_id] = w
    return cache


def fast_batch_sentinel_transcribe(
    asr_model: Any,
    sentinel_records: List[Dict[str, Any]],
    sentinel_cache: Dict[str, np.ndarray],
    device: str,
    batch_size: int = 16
) -> List[str]:
    """Batched sentinel transcription for high GPU throughput."""
    hyps: List[str] = []
    model_core = asr_model.model
    processor = asr_model.processor
    model_core.eval()

    # If CPU or batch_size == 1, iterate
    if device == "cpu" or batch_size <= 1:
        for r in sentinel_records:
            s_id = r["sentinel_id"]
            w = sentinel_cache[s_id]
            inputs = processor(w, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                logits = model_core(inputs.input_values.to(device)).logits
            pred_ids = torch.argmax(logits, dim=-1)
            text = processor.batch_decode(pred_ids)[0].strip()
            hyps.append(text)
        return hyps

    # Batched GPU inference
    for i in range(0, len(sentinel_records), batch_size):
        batch_recs = sentinel_records[i : i + batch_size]
        waveforms = [sentinel_cache[r["sentinel_id"]] for r in batch_recs]
        inputs = processor(waveforms, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.inference_mode():
            logits = model_core(inputs.input_values.to(device)).logits
        pred_ids = torch.argmax(logits, dim=-1)
        batch_texts = processor.batch_decode(pred_ids)
        hyps.extend([t.strip() for t in batch_texts])

    return hyps


def run_stage5m_closed_loop_cell(
    model_name: str,
    condition: str,
    method: str,
    order_id: str,
    utterances: List[UtteranceMetadata],
    sentinel_records: List[Dict[str, Any]],
    sentinel_cache: Dict[str, np.ndarray],
    evaluator: SentinelSafetyEvaluator,
    gate: DisparitySafetyGate,
    device: str,
    asr_model: Any,
    init_weights: Dict[str, torch.Tensor],
    stream_cache: Dict[str, np.ndarray],
    window_size_k: int = 4,
    checkpoint_dir: Optional[Path] = None,
    max_windows: Optional[int] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Executes a single Stage 5M Closed-Loop Online Control stream:
    - Prequential inference on window B_w with live model theta_w.
    - Candidate parameter adaptation theta'_w on unlabeled B_w (reference labels strictly isolated).
    - Operational DSG candidate evaluation on Sentinel Panel (N=30) via paired bootstrap (B=1000).
    - Live state update if ACCEPT; rollback/retain if REJECT.
    - Diagnostic retrospective scoring on test stream ground truth to measure agreement/false approvals.
    """
    exp_id = f"STAGE5M_{model_name}_{condition}_{method}_{order_id.lower()}_k{window_size_k}"
    ckpt_file = checkpoint_dir / f"{exp_id}.json" if checkpoint_dir else None

    if ckpt_file and ckpt_file.exists():
        try:
            with open(ckpt_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            print(f"  [Resume] Loaded completed checkpoint: {exp_id}")
            return saved["summary"], saved["operational_decisions"], saved["predictions"]
        except Exception:
            pass

    run_seed = derive_run_seed(exp_id)
    # Reset model to pristine initial weights
    asr_model.model.load_state_dict(copy.deepcopy(init_weights))
    asr_model.model.eval()

    stream = PrequentialStream(
        utterances=utterances,
        window_size_k=window_size_k,
        ordering_id=order_id,
        seed=run_seed
    )

    operational_decisions: List[Dict[str, Any]] = []
    prediction_records: List[Dict[str, Any]] = []

    cumulative_errors = 0
    cumulative_words = 0
    group_stats: Dict[str, Dict[str, int]] = {}

    total_candidates = 0
    accepted_candidates = 0
    rejected_candidates = 0

    # Agreement tracking counters
    true_approvals = 0
    false_approvals = 0
    true_rejections = 0
    false_rejections = 0
    neutral_rejections = 0

    # Cache for live model sentinel hypotheses
    cached_live_sentinel_hyps: Optional[List[str]] = None
    cached_live_model_hash: Optional[str] = None

    t0_cell = time.time()
    windows = list(stream.generate_windows())
    if max_windows is not None and max_windows > 0:
        windows = windows[:max_windows]
    num_windows = len(windows)

    for batch_idx, batch_utts, unlabeled_batch in windows:
        theta_t_hash = compute_model_parameter_hash(asr_model.model)

        # -------------------------------------------------------------
        # STEP 1: PREDICT WINDOW B_t WITH LIVE MODEL theta_t
        # -------------------------------------------------------------
        window_hyps: List[str] = []
        for u in batch_utts:
            w = stream_cache[u.utterance_id]
            inputs = asr_model.processor(w, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                logits = asr_model.model(inputs.input_values.to(device)).logits
            pred_id = torch.argmax(logits, dim=-1)
            hyp = asr_model.processor.batch_decode(pred_id)[0].strip()
            window_hyps.append(hyp)

            # Offline ground-truth evaluation
            metrics = compute_utterance_metrics(u.reference_normalized, hyp)
            cumulative_errors += metrics.total_errors
            cumulative_words += metrics.reference_length

            gid = u.group_id
            if gid not in group_stats:
                group_stats[gid] = {"errors": 0, "words": 0}
            group_stats[gid]["errors"] += metrics.total_errors
            group_stats[gid]["words"] += metrics.reference_length

            prediction_records.append({
                "experiment_id": exp_id,
                "model_key": model_name,
                "condition": condition,
                "method": method,
                "ordering_id": order_id,
                "window_id": batch_idx,
                "utterance_id": u.utterance_id,
                "speaker_id": u.speaker_id,
                "group_id": u.group_id,
                "reference_raw": u.reference_raw,
                "hypothesis_raw": hyp,
                "substitutions": metrics.substitutions,
                "deletions": metrics.deletions,
                "insertions": metrics.insertions,
                "reference_length": metrics.reference_length,
                "wer": round(metrics.wer, 4),
                "theta_hash": theta_t_hash[:16]
            })

        # Terminal Window Rule: omit adaptation for last window (w == 29)
        if batch_idx == num_windows - 1 or method == "no_adapt":
            operational_decisions.append({
                "experiment_id": exp_id,
                "model_key": model_name,
                "condition": condition,
                "method": method,
                "ordering_id": order_id,
                "window_id": batch_idx,
                "candidate_id": "N/A",
                "live_id": theta_t_hash[:16],
                "decision": "SKIP_TERMINAL" if batch_idx == num_windows - 1 else "NO_ADAPT_STATIC",
                "rejection_category": "NONE",
                "delta_R": 0.0,
                "max_delta_g": 0.0,
                "delta_D": 0.0,
                "UCB_R": 0.0,
                "UCB_max_group": 0.0,
                "UCB_D": 0.0,
                "retrospective_nature": "NEUTRAL",
                "agreement_class": "N/A",
                "state_action": "RETAIN"
            })
            continue

        # -------------------------------------------------------------
        # STEP 2: PROPOSE CANDIDATE UPDATE theta' (LABEL ISOLATION ENFORCED)
        # -------------------------------------------------------------
        total_candidates += 1
        enforce_data_access_firewall(unlabeled_batch)

        # Clone live model weights for candidate
        cand_core = ShadowCandidateManager.create_candidate_clone(asr_model.model)
        cand_wrapper = create_asr_model(model_name, device=device)
        cand_wrapper.model = cand_core
        cand_wrapper.processor = asr_model.processor

        # Adapt candidate on unlabeled batch
        cand_adapter = create_adapter_for_model(method, cand_wrapper)
        cand_adapter.adapt(unlabeled_batch)
        cand_hash = compute_model_parameter_hash(cand_core)

        # -------------------------------------------------------------
        # STEP 3: OPERATIONAL DSG EVALUATION ON SENTINEL PANEL (N=30)
        # -------------------------------------------------------------
        # Re-use cached live sentinel predictions if live model hasn't changed
        if cached_live_model_hash != theta_t_hash or cached_live_sentinel_hyps is None:
            cached_live_sentinel_hyps = fast_batch_sentinel_transcribe(
                asr_model=asr_model,
                sentinel_records=sentinel_records,
                sentinel_cache=sentinel_cache,
                device=device,
                batch_size=16
            )
            cached_live_model_hash = theta_t_hash

        # Candidate sentinel predictions
        cand_sentinel_hyps = fast_batch_sentinel_transcribe(
            asr_model=cand_wrapper,
            sentinel_records=sentinel_records,
            sentinel_cache=sentinel_cache,
            device=device,
            batch_size=16
        )

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
                "reference_length": m_live.reference_length
            })
            records_cand.append({
                "utterance_id": r["sentinel_id"],
                "speaker_id": r["speaker_id"],
                "group_id": r["stage5_accent_group"],
                "substitutions": m_cand.substitutions,
                "deletions": m_cand.deletions,
                "insertions": m_cand.insertions,
                "reference_length": m_cand.reference_length
            })

        # Operational Gate Decision via Paired Bootstrap
        gate_decision = evaluator.evaluate_records(
            records_live=records_live,
            records_candidate=records_cand,
            candidate_identifier=cand_hash[:16],
            live_identifier=theta_t_hash[:16]
        )

        # -------------------------------------------------------------
        # STEP 4: RETROSPECTIVE GROUND-TRUTH DIAGNOSTIC COMPARISON
        # -------------------------------------------------------------
        # Evaluate candidate vs live on current test window B_t with labels
        cand_test_errors = 0
        live_test_errors = 0
        for u_idx, u in enumerate(batch_utts):
            w = stream_cache[u.utterance_id]
            inputs = asr_model.processor(w, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                logits_c = cand_core(inputs.input_values.to(device)).logits
            pred_id_c = torch.argmax(logits_c, dim=-1)
            hyp_c = asr_model.processor.batch_decode(pred_id_c)[0].strip()

            m_live = compute_utterance_metrics(u.reference_normalized, window_hyps[u_idx])
            m_cand = compute_utterance_metrics(u.reference_normalized, hyp_c)
            live_test_errors += m_live.total_errors
            cand_test_errors += m_cand.total_errors

        delta_err = cand_test_errors - live_test_errors
        if delta_err < 0:
            retro_nature = "BENEFICIAL"
        elif delta_err > 0:
            retro_nature = "HARMFUL"
        else:
            retro_nature = "NEUTRAL"

        # -------------------------------------------------------------
        # STEP 5: STATE TRANSITION
        # -------------------------------------------------------------
        if gate_decision.decision == "ACCEPT":
            accepted_candidates += 1
            asr_model.model = ShadowCandidateManager.apply_transition(
                live_model=asr_model.model,
                candidate_model=cand_core,
                decision=gate_decision
            )
            cached_live_sentinel_hyps = cand_sentinel_hyps
            cached_live_model_hash = cand_hash
            state_action = "UPDATE"
        else:
            rejected_candidates += 1
            # Retain live model, discard candidate
            del cand_core
            del cand_wrapper
            state_action = "RETAIN"

        # Agreement Classification
        if gate_decision.decision == "ACCEPT":
            if retro_nature in ["BENEFICIAL", "NEUTRAL"]:
                agreement_class = "TRUE_APPROVAL"
                true_approvals += 1
            else:
                agreement_class = "FALSE_APPROVAL"  # CRITICAL FAILURE DIAGNOSTIC
                false_approvals += 1
        else:
            if retro_nature == "HARMFUL":
                agreement_class = "TRUE_REJECTION"
                true_rejections += 1
            elif retro_nature == "BENEFICIAL":
                agreement_class = "FALSE_REJECTION"
                false_rejections += 1
            else:
                agreement_class = "NEUTRAL_REJECTION"
                neutral_rejections += 1

        operational_decisions.append({
            "experiment_id": exp_id,
            "model_key": model_name,
            "condition": condition,
            "method": method,
            "ordering_id": order_id,
            "window_id": batch_idx,
            "candidate_id": cand_hash[:16],
            "live_id": theta_t_hash[:16],
            "decision": gate_decision.decision,
            "decision_reason": gate_decision.decision_reason,
            "rejection_category": gate_decision.rejection_category or "NONE",
            "delta_R": round(gate_decision.delta_r, 6) if not math.isnan(gate_decision.delta_r) else "NaN",
            "max_delta_g": round(gate_decision.max_delta_g, 6) if not math.isnan(gate_decision.max_delta_g) else "NaN",
            "delta_D": round(gate_decision.delta_d, 6) if not math.isnan(gate_decision.delta_d) else "NaN",
            "UCB_R": round(gate_decision.ucb_r, 6) if not math.isnan(gate_decision.ucb_r) else "NaN",
            "UCB_max_group": round(gate_decision.ucb_max_group, 6) if not math.isnan(gate_decision.ucb_max_group) else "NaN",
            "UCB_D": round(gate_decision.ucb_d, 6) if not math.isnan(gate_decision.ucb_d) else "NaN",
            "retrospective_nature": retro_nature,
            "agreement_class": agreement_class,
            "state_action": state_action
        })

    elapsed_cell = time.time() - t0_cell

    # Final corpus and group metrics under closed-loop control
    final_wer = round(cumulative_errors / cumulative_words, 4) if cumulative_words > 0 else 0.0
    group_wers = {
        gid: round(g["errors"] / g["words"], 4) if g["words"] > 0 else 0.0
        for gid, g in group_stats.items()
    }
    final_disparity = round(max(group_wers.values()) - min(group_wers.values()), 4) if len(group_wers) > 1 else 0.0

    acceptance_rate = round(accepted_candidates / total_candidates, 4) if total_candidates > 0 else 0.0

    summary = {
        "experiment_id": exp_id,
        "model_key": model_name,
        "condition": condition,
        "method": method,
        "ordering_id": order_id,
        "final_wer": final_wer,
        "final_disparity": final_disparity,
        "total_errors": cumulative_errors,
        "total_words": cumulative_words,
        "total_candidates": total_candidates,
        "accepted_candidates": accepted_candidates,
        "rejected_candidates": rejected_candidates,
        "acceptance_rate": acceptance_rate,
        "true_approvals": true_approvals,
        "false_approvals": false_approvals,
        "true_rejections": true_rejections,
        "false_rejections": false_rejections,
        "neutral_rejections": neutral_rejections,
        "group_wers": group_wers,
        "elapsed_seconds": round(elapsed_cell, 2)
    }

    if ckpt_file:
        with open(ckpt_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "operational_decisions": operational_decisions,
                "predictions": prediction_records
            }, f, indent=2)

    return summary, operational_decisions, prediction_records


def run_stage5m_suite(
    models: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    methods: Optional[List[str]] = None,
    orders: Optional[List[str]] = None,
    device: Optional[str] = None,
    smoke_test: bool = False
) -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 5M: CLOSED-LOOP ONLINE CONTROL SUITE")
    print("Protocol: v1.1.0-model-expansion | ADR-005")
    print("Stakeholder Decision: CONDITIONAL GO — Controlled Research Evaluation")
    print("=" * 80)
    t_start = time.time()

    # Hardware detection
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Execution Device : {device}")
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        gpu_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"GPU Hardware     : {gpu_name} ({gpu_vram:.2f} GB VRAM)")

    # Ensure output directories
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Sentinel Panel & Resolver
    print("\n>>> INITIALIZING SENTINEL PANEL & DSG EVALUATOR...")
    with open(GATE_CONFIG, "r", encoding="utf-8") as f:
        gate_cfg = json.load(f)

    eps_r = float(gate_cfg["gate_tolerances"]["epsilon_R"])
    eps_g = float(gate_cfg["gate_tolerances"]["epsilon_G"])
    eps_d = float(gate_cfg["gate_tolerances"]["epsilon_D"])
    bootstrap_b = int(gate_cfg["bootstrap"]["B"])
    bootstrap_conf = float(gate_cfg["bootstrap"]["confidence"])
    bootstrap_seed = int(gate_cfg["bootstrap"]["seed"])

    print(f"Frozen Tolerances: eps_R={eps_r:.4f} (0.00 pp), eps_G={eps_g:.4f} (2.00 pp), eps_D={eps_d:.4f} (2.00 pp)")
    print(f"Bootstrap Policy : B={bootstrap_b}, conf={bootstrap_conf}, seed={bootstrap_seed}")

    resolver = SentinelAudioResolver(
        manifest_path=SENTINEL_MANIFEST if SENTINEL_MANIFEST.exists() else None,
        inventory_path=SENTINEL_INVENTORY,
        project_root=PROJECT_ROOT
    )
    sentinel_df = pd.read_csv(SENTINEL_CSV)
    sentinel_records = sentinel_df.to_dict(orient="records")
    print(f"Sentinel Panel   : {len(sentinel_records)} clips across {sentinel_df['speaker_id'].nunique()} speakers.")

    sentinel_cache = preload_sentinel_waveforms(sentinel_records, resolver)

    gate = DisparitySafetyGate(epsilon_r=eps_r, epsilon_g=eps_g, epsilon_d=eps_d)
    evaluator = SentinelSafetyEvaluator(
        gate=gate,
        num_bootstrap=bootstrap_b,
        confidence_level=bootstrap_conf,
        bootstrap_seed=bootstrap_seed,
        min_speakers_per_group=3,
        resolver=resolver
    )

    # 2. Load Acoustic Stress Partitions
    condition_partitions: Dict[str, List[UtteranceMetadata]] = {}
    selected_conditions = conditions or (["clean"] if smoke_test else list(CONDITIONS.keys()))
    max_win = 2 if smoke_test else None

    for c_name in selected_conditions:
        c_rel = CONDITIONS[c_name]
        c_path = PROJECT_ROOT / c_rel
        assert c_path.exists(), f"Condition partition not found: {c_path}"
        utts = load_partition_from_csv(str(c_path))
        condition_partitions[c_name] = utts
        print(f"Acoustic Condition Loaded: {c_name:15s} ({len(utts)} utts)")

    # Model and Method Selection
    if smoke_test:
        target_ctc_models = ["wav2vec2_base"]
        target_seq2seq_models = []
        target_methods = ["suta"]
        target_orders = ["ORDER_A"]
        print("\n*** SMOKE-TEST MODE ACTIVE (Fast 2-window validation) ***")
    else:
        target_ctc_models = models or CTC_MODELS
        target_seq2seq_models = [m for m in (models or SEQ2SEQ_MODELS) if m in SEQ2SEQ_MODELS]
        target_methods = methods or ACTIVE_METHODS
        target_orders = orders or ORDERS

    all_cell_summaries: List[Dict[str, Any]] = []
    all_decisions: List[Dict[str, Any]] = []
    all_predictions: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # 3. EXECUTE CTC CLOSED-LOOP CONTROL
    # -------------------------------------------------------------
    for model_name in target_ctc_models:
        print("\n" + "=" * 70)
        print(f"LOADING CTC MODEL: {model_name}...")
        print("=" * 70)
        asr_model = create_asr_model(model_name, device=device)
        asr_model.load_model()
        init_weights = {k: v.cpu().clone() for k, v in asr_model.model.state_dict().items()}

        for c_name in selected_conditions:
            utts = condition_partitions[c_name]
            stream_cache = preload_stream_waveforms(utts, PROJECT_ROOT)

            # First run No-Adapt baseline for this condition
            print(f"\n--- Model: {model_name} | Condition: {c_name} | Method: no_adapt | ORDER_A ---")
            na_sum, na_dec, na_pred = run_stage5m_closed_loop_cell(
                model_name=model_name,
                condition=c_name,
                method="no_adapt",
                order_id="ORDER_A",
                utterances=utts,
                sentinel_records=sentinel_records,
                sentinel_cache=sentinel_cache,
                evaluator=evaluator,
                gate=gate,
                device=device,
                asr_model=asr_model,
                init_weights=init_weights,
                stream_cache=stream_cache,
                checkpoint_dir=CHECKPOINTS_DIR,
                max_windows=max_win
            )
            all_cell_summaries.append(na_sum)
            all_decisions.extend(na_dec)
            all_predictions.extend(na_pred)

            # Active closed-loop methods
            for method in target_methods:
                for order_id in target_orders:
                    print(f"\n--- Model: {model_name} | Condition: {c_name} | Method: {method} | Order: {order_id} ---")
                    cell_sum, cell_dec, cell_pred = run_stage5m_closed_loop_cell(
                        model_name=model_name,
                        condition=c_name,
                        method=method,
                        order_id=order_id,
                        utterances=utts,
                        sentinel_records=sentinel_records,
                        sentinel_cache=sentinel_cache,
                        evaluator=evaluator,
                        gate=gate,
                        device=device,
                        asr_model=asr_model,
                        init_weights=init_weights,
                        stream_cache=stream_cache,
                        checkpoint_dir=CHECKPOINTS_DIR,
                        max_windows=max_win
                    )
                    all_cell_summaries.append(cell_sum)
                    all_decisions.extend(cell_dec)
                    all_predictions.extend(cell_pred)

        del asr_model
        del init_weights
        if device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()

    # -------------------------------------------------------------
    # 4. EXECUTE SEQ2SEQ STATIC CONTROLS (NO-ADAPT ONLY)
    # -------------------------------------------------------------
    for model_name in target_seq2seq_models:
        print("\n" + "=" * 70)
        print(f"LOADING SEQ2SEQ STATIC CONTROL: {model_name}...")
        print("=" * 70)
        asr_model = create_asr_model(model_name, device=device)
        asr_model.load_model()
        init_weights = {k: v.cpu().clone() for k, v in asr_model.model.state_dict().items()}

        for c_name in selected_conditions:
            utts = condition_partitions[c_name]
            stream_cache = preload_stream_waveforms(utts, PROJECT_ROOT)

            print(f"\n--- Model: {model_name} | Condition: {c_name} | Method: no_adapt | ORDER_A ---")
            na_sum, na_dec, na_pred = run_stage5m_closed_loop_cell(
                model_name=model_name,
                condition=c_name,
                method="no_adapt",
                order_id="ORDER_A",
                utterances=utts,
                sentinel_records=sentinel_records,
                sentinel_cache=sentinel_cache,
                evaluator=evaluator,
                gate=gate,
                device=device,
                asr_model=asr_model,
                init_weights=init_weights,
                stream_cache=stream_cache,
                checkpoint_dir=CHECKPOINTS_DIR
            )
            all_cell_summaries.append(na_sum)
            all_decisions.extend(na_dec)
            all_predictions.extend(na_pred)

        del asr_model
        del init_weights
        if device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()

    # -------------------------------------------------------------
    # 5. SYNTHESIZE REPORTS & DIAGNOSTIC AUDIT TABLES
    # -------------------------------------------------------------
    print("\n>>> SYNTHESIZING STAGE 5M RESULTS & AUDIT TABLES...")
    df_sum = pd.DataFrame(all_cell_summaries)
    df_dec = pd.DataFrame(all_decisions)

    out_sum_csv = RESULTS_DIR / "stage5m_closed_loop_results.csv"
    out_dec_csv = RESULTS_DIR / "stage5m_operational_decisions.csv"
    out_agree_csv = RESULTS_DIR / "stage5m_decision_agreement_matrix.csv"

    df_sum.to_csv(out_sum_csv, index=False)
    df_dec.to_csv(out_dec_csv, index=False)

    # Agreement matrix cross-tabulation
    # Filter active decisions
    active_dec = df_dec[df_dec["decision"].isin(["ACCEPT", "REJECT"])]
    if len(active_dec) > 0:
        crosstab = pd.crosstab(
            active_dec["decision"],
            active_dec["retrospective_nature"],
            margins=True
        )
        crosstab.to_csv(out_agree_csv)
    else:
        crosstab = pd.DataFrame()

    # Generate Markdown Report
    report_path = REPORTS_DIR / "stage5m_closed_loop_report.md"
    generate_markdown_report(
        df_sum=df_sum,
        df_dec=df_dec,
        crosstab=crosstab,
        report_path=report_path,
        total_time=time.time() - t_start
    )

    t_total = time.time() - t_start
    print("=" * 80)
    print(f"STAGE 5M EXECUTION COMPLETE in {t_total:.1f}s ({t_total/60:.2f} mins)")
    print(f"Results CSV     : {out_sum_csv}")
    print(f"Decisions CSV   : {out_dec_csv}")
    print(f"Agreement CSV   : {out_agree_csv}")
    print(f"Summary Report  : {report_path}")
    print("=" * 80)

    return {
        "summary_csv": str(out_sum_csv),
        "decisions_csv": str(out_dec_csv),
        "agreement_csv": str(out_agree_csv),
        "report_md": str(report_path),
        "total_cells": len(df_sum),
        "total_decisions": len(df_dec)
    }


def generate_markdown_report(
    df_sum: pd.DataFrame,
    df_dec: pd.DataFrame,
    crosstab: pd.DataFrame,
    report_path: Path,
    total_time: float
):
    """Generates the official Stage 5M Research Report with agreement metrics."""
    active_dec = df_dec[df_dec["decision"].isin(["ACCEPT", "REJECT"])]
    tot_eval = len(active_dec)

    n_acc = len(active_dec[active_dec["decision"] == "ACCEPT"])
    n_rej = len(active_dec[active_dec["decision"] == "REJECT"])

    acc_rate = (n_acc / tot_eval * 100.0) if tot_eval > 0 else 0.0
    rej_rate = (n_rej / tot_eval * 100.0) if tot_eval > 0 else 0.0

    n_true_app = len(active_dec[active_dec["agreement_class"] == "TRUE_APPROVAL"])
    n_false_app = len(active_dec[active_dec["agreement_class"] == "FALSE_APPROVAL"])
    n_true_rej = len(active_dec[active_dec["agreement_class"] == "TRUE_REJECTION"])
    n_false_rej = len(active_dec[active_dec["agreement_class"] == "FALSE_REJECTION"])
    n_neut_rej = len(active_dec[active_dec["agreement_class"] == "NEUTRAL_REJECTION"])

    # Group rejection reasons
    rejection_reasons = active_dec[active_dec["decision"] == "REJECT"]["rejection_category"].value_counts().to_dict()

    md = []
    md.append("# Stage 5M: Closed-Loop Online Control Results Report")
    md.append("## Controlled Research Evaluation of the Operational Disparity Safety Gate")
    md.append("")
    md.append(f"**Protocol**: `v1.1.0-model-expansion` | **Standard**: ADR-005  ")
    md.append(f"**Execution Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  ")
    md.append(f"**Total Runtime**: {total_time:.1f} seconds ({total_time/60:.2f} minutes)  ")
    md.append("")
    md.append("---")
    md.append("")
    md.append("### 1. Executive Summary & Authorizing Criteria Compliance")
    md.append("")
    md.append("This report presents the controlled research evaluation of **Stage 5M Closed-Loop Online Control**, authorized under the frozen protocol.")
    md.append("In Stage 4M, retrospective auditing revealed that 85.2% of unconstrained adaptation settings failed safety criteria.")
    md.append("Stage 5M deployed the operational Disparity Safety Gate (DSG) online during sequential streaming, testing candidate updates")
    md.append("exclusively on the designated **Sentinel Panel ($N=30$)** without access to test-stream reference labels.")
    md.append("")
    md.append("| Metric | Operational Gate Value | Preregistered Specification | Status |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(f"| $\\epsilon_R$ Overall Risk Threshold | $0.00\\text{{ pp}}$ ($0.0000$) | $\\epsilon_R = 0.00\\text{{ pp}}$ | **FROZEN & ENFORCED** |")
    md.append(f"| $\\epsilon_G$ Subgroup Harm Threshold | $+2.00\\text{{ pp}}$ ($0.0200$) | $\\epsilon_G = +2.00\\text{{ pp}}$ | **FROZEN & ENFORCED** |")
    md.append(f"| $\\epsilon_D$ Disparity Expansion Threshold | $+2.00\\text{{ pp}}$ ($0.0200$) | $\\epsilon_D = +2.00\\text{{ pp}}$ | **FROZEN & ENFORCED** |")
    md.append(f"| Bootstrap Resamples $B$ | $1,000$ | $B = 1000$ | **FROZEN** |")
    md.append(f"| Confidence Level | $95\\%$ ($\\alpha=0.05$) | $95\\%$ | **FROZEN** |")
    md.append(f"| Total Candidate Evaluations | {tot_eval} | Prequential Stream | **EVALUATED** |")
    md.append(f"| Operational Acceptance Rate | **{acc_rate:.2f}%** ({n_acc} / {tot_eval}) | Operational Sentinel | — |")
    md.append(f"| Operational Rejection Rate | **{rej_rate:.2f}%** ({n_rej} / {tot_eval}) | Operational Sentinel | — |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("### 2. Primary Result: Operational Decisions vs. Retrospective Ground-Truth")
    md.append("")
    md.append("As mandated by Condition C of the Stakeholder Review, the table below cross-tabulates **operational gate decisions**")
    md.append("(evaluated on the Sentinel Panel) against the **retrospective ground-truth effect** of the candidate update on the test stream.")
    md.append("")
    md.append("| Operational Decision | Retrospectively Beneficial | Retrospectively Neutral | Retrospectively Harmful | Total |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")

    b_acc = len(active_dec[(active_dec["decision"] == "ACCEPT") & (active_dec["retrospective_nature"] == "BENEFICIAL")])
    neut_acc = len(active_dec[(active_dec["decision"] == "ACCEPT") & (active_dec["retrospective_nature"] == "NEUTRAL")])
    harm_acc = len(active_dec[(active_dec["decision"] == "ACCEPT") & (active_dec["retrospective_nature"] == "HARMFUL")])

    b_rej = len(active_dec[(active_dec["decision"] == "REJECT") & (active_dec["retrospective_nature"] == "BENEFICIAL")])
    neut_rej = len(active_dec[(active_dec["decision"] == "REJECT") & (active_dec["retrospective_nature"] == "NEUTRAL")])
    harm_rej = len(active_dec[(active_dec["decision"] == "REJECT") & (active_dec["retrospective_nature"] == "HARMFUL")])

    md.append(f"| **ACCEPT (Model Updated)** | {b_acc} (Safe Improvement) | {neut_acc} (Neutral) | **{harm_acc} (False Approval Hazard)** | {b_acc + neut_acc + harm_acc} |")
    md.append(f"| **REJECT (Model Retained)** | {b_rej} (False Rejection) | {neut_rej} (Neutral Blocked) | **{harm_rej} (True Safe Rejection)** | {b_rej + neut_rej + harm_rej} |")
    md.append(f"| **Total** | {b_acc + b_rej} | {neut_acc + neut_rej} | {harm_acc + harm_rej} | {tot_eval} |")
    md.append("")
    md.append("#### Critical Safety Diagnostics:")
    md.append(f"1. **False Approval Rate (Hazard Rate)**: **{harm_acc / tot_eval * 100.0:.2f}%** ({harm_acc} occurrences).")
    md.append("   - Represents cases where the sentinel panel indicated safety, but the update caused increased word errors on the test stream.")
    md.append(f"2. **True Safe Rejection Rate**: **{harm_rej / tot_eval * 100.0:.2f}%** ({harm_rej} occurrences).")
    md.append("   - Represents harmful updates successfully intercepted and prevented by the operational gate.")
    md.append(f"3. **Conservative Over-Rejection Rate**: **{b_rej / tot_eval * 100.0:.2f}%** ({b_rej} occurrences).")
    md.append("   - Represents candidate updates that would have reduced test stream errors, but were rejected due to sentinel panel uncertainty or disparity risk.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("### 3. Operational Rejection Categories Breakdown")
    md.append("")
    md.append("| Rejection Reason Category | Count | Percentage of Rejections |")
    md.append("| :--- | :---: | :---: |")
    for r_cat, count in rejection_reasons.items():
        pct = count / n_rej * 100.0 if n_rej > 0 else 0.0
        md.append(f"| `{r_cat}` | {count} | {pct:.1f}% |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("### 4. Recognition Outcomes Across Acoustic Stress Conditions")
    md.append("")
    md.append("| Model | Condition | Method | Order | WER (%) | Disparity (pp) | Accept Rate (%) | False Approvals |")
    md.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    for _, row in df_sum.iterrows():
        md.append(
            f"| `{row['model_key']}` | `{row['condition']}` | `{row['method']}` | {row['ordering_id']} | "
            f"**{row['final_wer']*100:.2f}%** | {row['final_disparity']*100:.2f} pp | "
            f"{row['acceptance_rate']*100:.1f}% | {row['false_approvals']} |"
        )

    md.append("")
    md.append("---")
    md.append("")
    md.append("### 5. Research Scope and Small-Sample Limitations")
    md.append("- **Acoustic Stress Scope**: The evaluation validates performance across 5 acoustic conditions on L2-ARCTIC ($N=12$ speakers, 6 accents).")
    md.append("- **Non-Independent Speakers**: As documented, 6 of the 12 speakers overlap with Stage 3M; this remains an expanded-sample stress characterization.")
    md.append("- **Seq2Seq Boundary**: Autoregressive Seq2Seq models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) serve strictly as static No-Adapt controls.")
    md.append("- **Deployment Limitation**: Controlled research evaluation only. Not authorized for unmonitored production deployment.")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stage 5M Closed-Loop Online Control Suite")
    parser.add_argument("--models", nargs="+", default=None, help="ASR model keys")
    parser.add_argument("--conditions", nargs="+", default=None, help="Acoustic stress conditions")
    parser.add_argument("--methods", nargs="+", default=None, help="Adaptation methods")
    parser.add_argument("--orders", nargs="+", default=None, help="Stream arrival orders")
    parser.add_argument("--device", default=None, help="Hardware device ('cuda' or 'cpu')")
    parser.add_argument("--smoke-test", action="store_true", help="Run fast 1-cell smoke test")
    args = parser.parse_args()

    run_stage5m_suite(
        models=args.models,
        conditions=args.conditions,
        methods=args.methods,
        orders=args.orders,
        device=args.device,
        smoke_test=args.smoke_test
    )
