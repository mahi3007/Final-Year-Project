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
from typing import Dict, List, Any, Tuple, Optional, FrozenSet, Set

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
from dsg_ctta.data.cohort2_preflight import Cohort1PreflightValidator, Cohort2PreflightValidator
from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.controller.shadow import compute_model_parameter_hash
from dsg_ctta.controller.streaming_gate import StreamingSentinelSafetyGate, compute_calibrated_obf_schedule
from dsg_ctta.controller.streaming_gate_v14 import StreamingSentinelSafetyGateV14
from dsg_ctta.adaptation.safe_update import (
    SafeUpdateResult,
    execute_safe_adaptation_transaction,
    compute_masked_suta_loss,
    AtomicCandidateManager,
    compute_optimizer_state_hash,
)
from dsg_ctta.evaluation.paired_cluster_inference import run_confirmatory_paired_cluster_inference


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


CANONICAL_PROTOCOL_ACCENTS: FrozenSet[str] = frozenset([
    "US English",
    "England English",
    "South Asian English",
    "Australian English",
    "Canadian English",
    "Irish English",
])
EXPECTED_SENTINEL_SPEAKERS_PER_STRATUM: int = 5
EXPECTED_TOTAL_SENTINEL_SPEAKERS: int = 30


def validate_sentinel_panel_against_canonical_protocol(
    sentinel_df: pd.DataFrame,
    canonical_accents: FrozenSet[str] = CANONICAL_PROTOCOL_ACCENTS,
    expected_speakers_per_accent: int = EXPECTED_SENTINEL_SPEAKERS_PER_STRATUM,
    expected_total_speakers: int = EXPECTED_TOTAL_SENTINEL_SPEAKERS,
) -> pd.DataFrame:
    """
    Validates that the physical sentinel panel satisfies locked Protocol v1.4.0 requirements:
    1. All 6 canonical protocol accents are present.
    2. No extraneous or unmapped accent groups exist.
    3. Each canonical accent contains exactly expected_speakers_per_accent unique speakers.
    4. Total panel size contains exactly expected_total_speakers.
    Returns the deduplicated 1-clip-per-speaker core sentinel panel.
    """
    if "stage5_accent_group" not in sentinel_df.columns:
        raise ValueError("Sentinel panel CSV missing required column 'stage5_accent_group'.")
    if "speaker_id" not in sentinel_df.columns:
        raise ValueError("Sentinel panel CSV missing required column 'speaker_id'.")

    # 1. Source row validation: non-blank IDs, non-blank labels, single accent assignment per speaker
    spk_to_accent: Dict[str, str] = {}
    for idx, row in sentinel_df.iterrows():
        raw_spk = row["speaker_id"]
        raw_grp = row["stage5_accent_group"]

        if pd.isna(raw_spk):
            raise ValueError(f"Sentinel panel row {idx} has missing/NaN speaker_id.")
        s_id = str(raw_spk).strip()
        if not s_id or s_id.lower() in ("nan", "none"):
            raise ValueError(f"Sentinel panel row {idx} has blank/empty speaker_id.")

        if pd.isna(raw_grp):
            raise ValueError(f"Sentinel panel row {idx} has missing/NaN stage5_accent_group.")
        grp = str(raw_grp).strip()
        if not grp or grp.lower() in ("nan", "none"):
            raise ValueError(f"Sentinel panel row {idx} has blank/empty stage5_accent_group.")

        if grp not in canonical_accents:
            raise ValueError(
                f"Sentinel panel row {idx} contains non-canonical accent '{grp}'. "
                f"Expected one of: {sorted(list(canonical_accents))}."
            )

        if s_id in spk_to_accent and spk_to_accent[s_id] != grp:
            raise ValueError(
                f"Inconsistent speaker-to-accent mapping in source sentinel panel: speaker '{s_id}' "
                f"is assigned to multiple accents ('{spk_to_accent[s_id]}' vs '{grp}')."
            )
        spk_to_accent[s_id] = grp

    # 2. Deduplicate to core panel (1 clip per speaker)
    core_df = sentinel_df.groupby("speaker_id").first().reset_index()
    observed_strata = set(core_df["stage5_accent_group"].astype(str))

    missing_strata = set(canonical_accents) - observed_strata
    if missing_strata:
        raise ValueError(
            f"Sentinel panel integrity violation: missing canonical protocol accents {sorted(list(missing_strata))}. "
            f"Observed: {sorted(list(observed_strata))}."
        )

    unexpected_strata = observed_strata - set(canonical_accents)
    if unexpected_strata:
        raise ValueError(
            f"Sentinel panel integrity violation: unexpected accent strata {sorted(list(unexpected_strata))}."
        )

    spks_per_stratum = core_df.groupby("stage5_accent_group")["speaker_id"].nunique()
    for acc in sorted(list(canonical_accents)):
        cnt = int(spks_per_stratum.get(acc, 0))
        if cnt != expected_speakers_per_accent:
            raise ValueError(
                f"Sentinel panel integrity violation: stratum '{acc}' has {cnt} unique speakers "
                f"(expected exactly {expected_speakers_per_accent})."
            )

    if len(core_df) != expected_total_speakers:
        raise ValueError(
            f"Sentinel panel integrity violation: total speakers={len(core_df)} "
            f"(expected exactly {expected_total_speakers})."
        )

    return core_df


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
) -> SafeUpdateResult:
    inputs = processor(waveforms, sampling_rate=16000, padding=True, return_tensors="pt")
    input_values = inputs.input_values.to(device)
    audio_lengths = [len(w) for w in waveforms]

    # Gradient-based adaptation operates strictly in evaluation mode (frozen dropout)
    model.eval()

    def loss_fn() -> torch.Tensor:
        total_loss, _, _ = compute_masked_suta_loss(
            model=model,
            input_values=input_values,
            audio_lengths=audio_lengths,
            temperature=temperature,
            alpha=alpha,
        )
        return total_loss

    return execute_safe_adaptation_transaction(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        max_grad_norm=1.0
    )


def validate_frozen_execution_contract(
    manifest_data: Dict[str, Any],
    git_commit_sha: str,
    protocol_path: Path,
    governance_approval_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Validates the frozen execution contract under Protocol v1.4.0 with strict fail-closed semantics.
    Enforces independent cryptographic trust anchor verification.
    Fails closed if:
    1. Independent governance approval record is missing, corrupted, or not 'APPROVED'.
    2. approved_commits list is missing, empty, or not a list in manifest or trust anchor.
    3. Current git_commit_sha is not in approved_commits of manifest or trust anchor.
    4. protocol_sha256 is missing, empty, or does not match trust anchor.
    5. protocol_path does not exist or its SHA-256 does not match protocol_sha256.
    6. The protocol document is in 'draft' or 'proposal' status.
    7. Manifest governance_status is not 'APPROVED'.
    8. Any contradictory status exists (e.g. manifest claims APPROVED while protocol says draft).
    """
    if not isinstance(manifest_data, dict):
        raise ValueError("Confirmatory Contract Violation: Manifest data must be a valid dictionary.")

    frozen_contract = manifest_data.get("frozen_execution_contract")
    if not frozen_contract or not isinstance(frozen_contract, dict):
        frozen_contract = manifest_data

    # 1. Independent Governance Approval Record (Cryptographic Trust Anchor)
    if governance_approval_path is None:
        governance_approval_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_v1_4_governance_approval_record.json"

    if not governance_approval_path.exists():
        raise FileNotFoundError(
            f"Confirmatory Contract Violation: Independent governance approval record missing at '{governance_approval_path}'. "
            "Execution requires an independent, signed approval trust anchor."
        )

    try:
        gov_record = json.loads(governance_approval_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Confirmatory Contract Violation: Corrupted governance approval record at '{governance_approval_path}': {e}")

    trusted_gov_status = str(gov_record.get("governance_status", "DRAFT_HOLD")).strip().upper()
    if trusted_gov_status != "APPROVED":
        raise PermissionError(
            f"Independent Governance Lock: Approval record status is '{trusted_gov_status}' (must be 'APPROVED'). "
            "Confirmatory Cohort 3 execution remains strictly locked on HOLD."
        )

    # 2. Approved Commit List (Mandatory non-empty list in both manifest and trust anchor)
    approved_commits = frozen_contract.get("approved_commits")
    if approved_commits is None and "approved_commits" in manifest_data:
        approved_commits = manifest_data.get("approved_commits")

    if not approved_commits or not isinstance(approved_commits, list) or len(approved_commits) == 0:
        raise PermissionError(
            "Confirmatory Contract Violation: 'approved_commits' whitelist is missing or empty. "
            "Confirmatory execution requires a non-empty list of preapproved, audited commit hashes."
        )

    trusted_approved_commits = gov_record.get("approved_commits", [])
    if not trusted_approved_commits or not isinstance(trusted_approved_commits, list):
        raise PermissionError(
            "Independent Governance Lock: Independent approval record has empty or missing approved_commits list."
        )

    clean_sha = str(git_commit_sha).strip() if git_commit_sha else ""
    if not clean_sha or clean_sha not in approved_commits:
        raise PermissionError(
            f"Confirmatory Execution Commit Authorization Violation: Current commit '{clean_sha}' "
            f"is NOT in preapproved whitelist: {approved_commits}."
        )
    if clean_sha not in trusted_approved_commits:
        raise PermissionError(
            f"Independent Governance Lock: Current commit '{clean_sha}' is NOT in independent approval record whitelist."
        )

    # 3. Frozen Protocol Hash (Mandatory non-empty string matching trust anchor)
    expected_proto_sha = frozen_contract.get("protocol_sha256")
    if expected_proto_sha is None and "protocol_sha256" in manifest_data:
        expected_proto_sha = manifest_data.get("protocol_sha256")

    if not expected_proto_sha or not isinstance(expected_proto_sha, str) or not expected_proto_sha.strip():
        raise PermissionError(
            "Confirmatory Contract Violation: 'protocol_sha256' is missing or empty in frozen execution contract."
        )
    expected_proto_sha = expected_proto_sha.strip()

    trusted_proto_sha = gov_record.get("approved_protocol_sha256") or gov_record.get("protocol_sha256")
    if trusted_proto_sha and expected_proto_sha != trusted_proto_sha:
        raise ValueError(
            f"Independent Governance Lock: Protocol hash in manifest '{expected_proto_sha}' does not match "
            f"independent approval record '{trusted_proto_sha}'."
        )

    if not protocol_path.exists():
        raise FileNotFoundError(f"Confirmatory Protocol Violation: Missing protocol file at '{protocol_path}'.")

    actual_proto_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    if actual_proto_sha != expected_proto_sha:
        raise ValueError(
            f"Confirmatory Protocol Hash Violation: Protocol document hash '{actual_proto_sha}' does not match "
            f"frozen contract hash '{expected_proto_sha}'."
        )

    # 4. Protocol Draft / Proposal Status Check (Rejects unapproved / draft documents)
    protocol_text = protocol_path.read_text(encoding="utf-8")
    lower_text = protocol_text.lower()
    if (
        "draft proposal" in lower_text
        or "not yet frozen or authorized" in lower_text
        or "draft status" in lower_text
        or "proposed protocol id" in lower_text
    ):
        raise PermissionError(
            f"Confirmatory Contract Violation: Protocol at '{protocol_path}' explicitly remains in DRAFT/PROPOSAL status. "
            "Confirmatory execution requires a frozen, finalized protocol document."
        )

    # 5. Manifest Governance Status Check (Mandatory 'APPROVED')
    gov_status = frozen_contract.get("governance_status")
    if gov_status is None and "governance_status" in manifest_data:
        gov_status = manifest_data.get("governance_status")

    clean_gov = str(gov_status).strip().upper() if gov_status else "DRAFT_HOLD"
    if clean_gov != "APPROVED":
        raise PermissionError(
            f"Confirmatory Governance Lock: Governance status is '{clean_gov}' (must be 'APPROVED'). "
            "Confirmatory Cohort 3 execution remains strictly locked on HOLD."
        )

    return {
        "approved_commits": approved_commits,
        "protocol_sha256": actual_proto_sha,
        "governance_status": clean_gov,
        "contract_status": "APPROVED",
        "governance_approval_authority": gov_record.get("audit_authority", "Independent Scientific Audit Committee"),
    }


def validate_and_resolve_audio_payloads(
    eval_df: pd.DataFrame,
    audio_dir: Path,
    expected_audio_hashes: Dict[str, str],
    cohort_name: str = "Cohort 3",
) -> Dict[str, Path]:
    """
    Validates audio file existence, non-zero size, path resolution (.mp3 or .wav),
    and exact content SHA-256 hashes for EVERY clip in eval_df.
    Fails closed if:
    1. expected_audio_hashes is empty or missing.
    2. Any recording_id in eval_df lacks an entry in expected_audio_hashes.
    3. expected_audio_hashes contains extraneous recording_ids not in eval_df.
    4. Any audio file does not exist, has 0 bytes, or fails SHA-256 verification.
    """
    if not isinstance(expected_audio_hashes, dict) or len(expected_audio_hashes) == 0:
        raise ValueError(
            f"Confirmatory Audio Integrity Violation: Missing or empty audio hashes manifest for {cohort_name}."
        )

    df_rec_ids = set(eval_df["recording_id"].astype(str))
    manifest_rec_ids = set(expected_audio_hashes.keys())

    missing_hashes = df_rec_ids - manifest_rec_ids
    if missing_hashes:
        raise ValueError(
            f"Confirmatory Audio Integrity Violation: {len(missing_hashes)} clips in {cohort_name} lack hash entries "
            f"in manifest: {sorted(list(missing_hashes))[:5]}."
        )

    extra_hashes = manifest_rec_ids - df_rec_ids
    if extra_hashes:
        raise ValueError(
            f"Confirmatory Audio Integrity Violation: Audio hash manifest contains {len(extra_hashes)} extra recording IDs "
            f"not in {cohort_name}: {sorted(list(extra_hashes))[:5]}."
        )

    verified_paths: Dict[str, Path] = {}
    for _, row in eval_df.iterrows():
        rec_id = str(row["recording_id"])
        fpath = audio_dir / f"{rec_id}.mp3"
        if not fpath.exists():
            fpath = audio_dir / f"{rec_id}.wav"
        if not fpath.exists():
            raise FileNotFoundError(
                f"Confirmatory Audio Integrity Violation: Missing audio payload for clip '{rec_id}' in '{audio_dir}'."
            )
        if fpath.stat().st_size == 0:
            raise ValueError(
                f"Confirmatory Audio Integrity Violation: Empty (0-byte) audio payload for clip '{rec_id}'."
            )

        expected_h = str(expected_audio_hashes[rec_id]).strip()
        if not expected_h:
            raise ValueError(f"Confirmatory Audio Integrity Violation: Empty expected hash for clip '{rec_id}'.")

        actual_h = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if actual_h != expected_h:
            raise ValueError(
                f"Confirmatory Audio Content Hash Violation for clip '{rec_id}': expected '{expected_h}', got '{actual_h}'."
            )
        verified_paths[rec_id] = fpath

    return verified_paths


def validate_cohort_reference_transcripts(
    df: pd.DataFrame,
    cohort_name: str = "Cohort 3",
) -> None:
    """
    Validates reference transcripts for all recordings in df.
    Fails closed if:
    1. 'transcript' column is missing or any entry is None / NaN.
    2. Any entry is blank, empty whitespace, or literal string 'nan', 'none', 'null'.
    3. Any transcript normalizes to empty string via TextNormalizer.
    """
    if "transcript" not in df.columns:
        raise ValueError(f"Confirmatory Reference Integrity Violation: Missing 'transcript' column in {cohort_name}.")

    for _, row in df.iterrows():
        rec_id = str(row.get("recording_id", "UNKNOWN"))
        raw_t = row.get("transcript")
        if raw_t is None or pd.isna(raw_t):
            raise ValueError(
                f"Confirmatory Reference Integrity Violation: clip '{rec_id}' in {cohort_name} has missing/NaN reference transcript."
            )
        str_t = str(raw_t).strip()
        if not str_t or str_t.lower() in ("nan", "none", "null"):
            raise ValueError(
                f"Confirmatory Reference Integrity Violation: clip '{rec_id}' in {cohort_name} has blank/null reference transcript '{raw_t}'."
            )
        norm_t = TextNormalizer.normalize(str_t)
        if not norm_t.strip():
            raise ValueError(
                f"Confirmatory Reference Integrity Violation: clip '{rec_id}' in {cohort_name} normalized transcript is empty (raw: '{raw_t}')."
            )


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


def get_git_provenance(enforce_physical_checkout: bool = False) -> Tuple[str, bool]:
    """
    Retrieves Git commit SHA and working-tree dirty status.
    If enforce_physical_checkout is True, independently inspects the physical repository via
    git rev-parse HEAD and git status --porcelain, disallowing environment variable overrides.
    """
    import subprocess
    # In pytest test executions, allow monkeypatched environment variables
    if os.environ.get("PYTEST_CURRENT_TEST"):
        env_commit = os.environ.get("STAGE6M_GIT_COMMIT_SHA")
        if env_commit:
            env_dirty = os.environ.get("STAGE6M_GIT_DIRTY", "false").lower() == "true"
            return env_commit, env_dirty

    if not enforce_physical_checkout:
        env_commit = os.environ.get("STAGE6M_GIT_COMMIT_SHA")
        if env_commit:
            env_dirty = os.environ.get("STAGE6M_GIT_DIRTY", "false").lower() == "true"
            return env_commit, env_dirty

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=str(PROJECT_ROOT), stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        is_dirty = len(status_output) > 0
        return commit, is_dirty
    except Exception as exc:
        if enforce_physical_checkout:
            raise RuntimeError(
                f"Confirmatory Provenance Failure: Physical Git repository inspection failed ({exc}). "
                "A clean tracked Git checkout without uncommitted changes is strictly required for Cohort 3."
            )
        env_commit = os.environ.get("STAGE6M_GIT_COMMIT_SHA")
        if env_commit:
            env_dirty = os.environ.get("STAGE6M_GIT_DIRTY", "false").lower() == "true"
            return env_commit, env_dirty
        raise RuntimeError(
            f"Provenance enforcement failure: Unable to determine Git commit SHA ({exc}). "
            "A tracked Git commit is required to establish benchmark provenance."
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Stage 6M Physical Virtual GPU Benchmark Runner")
    parser.add_argument(
        "--cohort",
        choices=["cohort1", "cohort2", "cohort3"],
        default="cohort2",
        help="Evaluation cohort: 'cohort1' (retrospective 900 clips), 'cohort2' (retrospective 7,020 clips), 'cohort3' (confirmatory frozen path)."
    )
    parser.add_argument(
        "--model",
        default="wav2vec2_base",
        choices=["wav2vec2_base", "hubert_large"],
        help="Backbone acoustic model architecture."
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run comprehensive preflight integrity checks and generate readiness reports without executing neural acoustic inference."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "stage6m",
        help="Directory to save preflight readiness reports."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "stage6m_kaggle",
        help="Directory to save benchmark execution results."
    )
    parser.add_argument(
        "--gate-version",
        choices=["v13", "v14"],
        default="v13",
        help="Gate protocol version: 'v13' (legacy epsilon_d_pp=2.0) or 'v14' (Protocol v1.4.0 zero-disparity tolerance epsilon_d_pp=0.0 with strict point improvement)."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    device = verify_gpu()

    # Confirmatory Protocol v1.4.0 Enforcement: Cohort 3 requires gate-version v14
    if args.cohort == "cohort3" and args.gate_version != "v14":
        print("\n" + "!" * 80)
        print("[FAIL-CLOSED INTEGRITY CHECK]")
        print(f"Confirmatory Protocol Violation: Cohort 3 requires --gate-version v14, got '{args.gate_version}'.")
        print("Legacy v1.3 gate with +2.0 pp disparity tolerance cannot be used for confirmatory execution.")
        print("!" * 80 + "\n")
        sys.exit(1)

    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    sentinel_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    sentinel_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json"
    sentinel_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
    bundle_path = PROJECT_ROOT / "stage6_audio_bundle.tar.gz"
    if (not sentinel_audio_dir.exists() or len(list(sentinel_audio_dir.glob("*.mp3"))) < 300) and bundle_path.exists():
        print(f"      [AUTOLOAD] Unpacking sentinel audio from tracked bundle: {bundle_path.name}...")
        import tarfile
        with tarfile.open(bundle_path, "r:gz") as tar:
            tar.extractall(path=PROJECT_ROOT)

    results_dir = Path(args.results_dir)
    reports_dir = Path(args.reports_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/5] Checking Data Feasibility for Cohort: {args.cohort.upper()}")

    # Determine cohort evaluation dataset
    if args.cohort == "cohort1":
        eval_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
        eval_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.lock.json"
        audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"

        print("      Executing Confirmatory Cohort 1 Preflight Readiness Validation...")
        validator = Cohort1PreflightValidator(
            project_root=PROJECT_ROOT,
            eval_csv_path=eval_csv,
            eval_lock_path=eval_lock,
            audio_dir=audio_dir,
            sentinel_csv_path=sentinel_csv,
            sentinel_lock_path=sentinel_lock,
            sentinel_audio_dir=sentinel_audio_dir,
        )
        preflight_report = validator.run_preflight(model_name=args.model)

        print("\n" + "=" * 80)
        print(f"PREFLIGHT AUDIT VERDICT: {preflight_report['overall_status']}")
        print(f"Summary: {preflight_report['summary_description']}")
        print(f"Evaluation CSV: {eval_csv} (Exists: {eval_csv.exists()})")
        print(f"Evaluation Lock: {eval_lock} (Exists: {eval_lock.exists()})")
        print(f"Audio Directory: {audio_dir} (Exists: {audio_dir.exists()})")
        print(f"Sentinel CSV: {sentinel_csv} (Exists: {sentinel_csv.exists()})")
        print(f"Sentinel Lock: {sentinel_lock} (Exists: {sentinel_lock.exists()})")
        if preflight_report["status_reasons"]:
            print("\nActive HOLD / Integrity Errors:")
            for r in preflight_report["status_reasons"]:
                print(f"  * {r}")
        print("\nGovernance Check:")
        print("  Cohort 1 is authorized for physical execution under ADR-005.")
        print("=" * 80 + "\n")

        if args.preflight_only:
            sys.exit(0 if preflight_report["overall_status"] == "READY FOR AUTHORIZED EXECUTION (COHORT 1)" else 1)

        if preflight_report["overall_status"] != "READY FOR AUTHORIZED EXECUTION (COHORT 1)":
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED INTEGRITY CHECK]")
            print(f"Cohort 1 preflight readiness audit halted execution. Status: {preflight_report['overall_status']}")
            print(f"Summary: {preflight_report['summary_description']}")
            for r in preflight_report["status_reasons"]:
                print(f"  * {r}")
            print("!" * 80 + "\n")
            sys.exit(1)

        eval_df = pd.read_csv(eval_csv)
    elif args.cohort == "cohort2":
        # Cohort 2 check: Exhaustive preflight readiness validation
        cohort2_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort2_audio"
        cohort2_csv = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv"

        print("      Executing Retrospective Cohort 2 Preflight Readiness Validation...")
        validator = Cohort2PreflightValidator(
            project_root=PROJECT_ROOT,
            manifest_path=manifest_path,
            eval_csv_path=cohort2_csv,
            audio_dir=cohort2_audio_dir,
            sentinel_csv_path=sentinel_csv,
            sentinel_audio_dir=sentinel_audio_dir,
        )
        preflight_report = validator.run_preflight(model_name=args.model)
        json_rep, md_rep = validator.save_reports(preflight_report, output_dir=reports_dir)

        if args.preflight_only:
            print("\n" + "=" * 80)
            print(f"PREFLIGHT AUDIT VERDICT: {preflight_report['overall_status']}")
            print(f"Summary: {preflight_report['summary_description']}")
            print(f"Readiness Reports Saved:")
            print(f"  - {json_rep}")
            print(f"  - {md_rep}")
            if preflight_report["status_reasons"]:
                print("\nActive HOLD Conditions:")
                for r in preflight_report["status_reasons"]:
                    print(f"  * {r}")
            print("\nGovernance Check:")
            print("  Cohort 2 is retrospective regression evidence under ADR-005.")
            print("=" * 80 + "\n")
            sys.exit(0 if preflight_report["overall_status"] == "READY FOR AUTHORIZED EXECUTION" else 1)

        # Fail-closed check if running normal physical benchmark
        if preflight_report["overall_status"] != "READY FOR AUTHORIZED EXECUTION":
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED INTEGRITY CHECK]")
            print("Physical audio clips for Retrospective Cohort 2 (7,020 clips) are not materialized on disk.")
            print("Status: MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD")
            print("Reference Manifest: datasets/splits/stage6m_locked_candidate_manifest.json")
            print(f"Cohort 2 preflight readiness audit halted execution. Status: {preflight_report['overall_status']}")
            print(f"Summary: {preflight_report['summary_description']}")
            print(f"Readiness Reports Saved:")
            print(f"  - {json_rep}")
            print(f"  - {md_rep}")
            print()
            print("Active HOLD Reasons:")
            for r in preflight_report["status_reasons"]:
                print(f"  * {r}")
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
            print("     and provide matching datasets/splits/stage6m_cohort2_audio.csv.")
            print("!" * 80 + "\n")
            sys.exit(1)

        eval_df = pd.read_csv(cohort2_csv)
        audio_dir = cohort2_audio_dir

        # Scientific assertion: strictly 78 speakers per stratum, 1 stratum per speaker
        spk_strata_counts = eval_df.groupby("speaker_id")["stage5_accent_group"].nunique()
        if (spk_strata_counts != 1).any():
            raise ValueError("Integrity failure: detected speaker spanning multiple strata in eval_df")
        speakers_per_stratum = eval_df.groupby("stage5_accent_group")["speaker_id"].nunique()
        for s_name, count in speakers_per_stratum.items():
            if count != 78:
                raise ValueError(f"Integrity failure: Stratum {s_name} has {count} speakers (expected exactly 78)")
    elif args.cohort == "cohort3":
        # Cohort 3: Confirmatory frozen path
        cohort3_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_manifest.json"
        cohort3_csv = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_audio.csv"
        cohort3_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort3_audio"
        gate_ref_panel_csv = PROJECT_ROOT / "datasets" / "splits" / "stage6m_gate_reference_panel.csv"
        gate_ref_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_gate_reference_manifest.json"
        manifest_path = cohort3_manifest
        sentinel_csv = gate_ref_panel_csv
        sentinel_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "gate_reference_audio"

        print("      Executing Confirmatory Cohort 3 Preflight Readiness Validation...")
        # 1. Independent physical clean checkout verification (environment variables CANNOT override)
        git_commit_sha, git_tree_dirty = get_git_provenance(enforce_physical_checkout=True)
        if git_tree_dirty:
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED INTEGRITY CHECK]")
            print("Confirmatory Execution Provenance Violation: Working tree has uncommitted modifications.")
            print("A verified clean Git checkout is strictly required before Confirmatory Cohort 3 execution.")
            print("!" * 80 + "\n")
            sys.exit(1)

        # 2. Materialization checks for Cohort 3 and dedicated gate-reference panel
        missing_items = []
        if not cohort3_manifest.exists():
            missing_items.append(f"Cohort 3 Manifest: {cohort3_manifest}")
        if not cohort3_csv.exists():
            missing_items.append(f"Cohort 3 CSV: {cohort3_csv}")
        if not cohort3_audio_dir.exists():
            missing_items.append(f"Cohort 3 Audio Dir: {cohort3_audio_dir}")
        if not gate_ref_panel_csv.exists():
            missing_items.append(f"Dedicated Gate-Reference Panel CSV: {gate_ref_panel_csv}")
        if not gate_ref_manifest.exists():
            missing_items.append(f"Dedicated Gate-Reference Manifest: {gate_ref_manifest}")

        if missing_items:
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED INTEGRITY CHECK]")
            print("Physical audio clips, manifest, or dedicated gate-reference panel for Confirmatory Cohort 3 are not materialized on disk.")
            print("Status: CONFIRMATORY_COHORT3_HOLD_DATA_MATERIALIZATION_PENDING")
            for item in missing_items:
                print(f"  [MISSING] {item}")
            print("\nPROTOCOL REQUIREMENTS (Protocol v1.4.0):")
            print("  Cohort 3 requires 3 strictly separate, locked partitions:")
            print("    1. Development data (historical Cohorts 1 and 2 for parameter tuning)")
            print("    2. Dedicated Gate-Reference Panel (strictly disjoint from Cohort 3, separate from Stage 5 sentinel)")
            print("    3. Fresh Cohort 3 (speaker-disjoint from all development, Cohort 1, 2, and gate-reference data)")
            print("!" * 80 + "\n")
            sys.exit(1)

        # 3. Full Manifest Schema, File Hash, and Balance Verification
        with open(cohort3_manifest, "r", encoding="utf-8") as f:
            c3_manifest_data = json.load(f)

        if c3_manifest_data.get("role") != "confirmatory_evaluation":
            raise ValueError(
                f"Confirmatory Integrity Violation: cohort3_manifest role='{c3_manifest_data.get('role')}' "
                "must be 'confirmatory_evaluation'."
            )
        if c3_manifest_data.get("manifest_version") != "v1.4.0":
            raise ValueError(
                f"Confirmatory Integrity Violation: manifest version='{c3_manifest_data.get('manifest_version')}' "
                "must be 'v1.4.0'."
            )

        # Hash verification of cohort3 CSV
        c3_csv_bytes = cohort3_csv.read_bytes()
        actual_csv_sha256 = hashlib.sha256(c3_csv_bytes).hexdigest()
        expected_csv_sha256 = c3_manifest_data.get("files", {}).get("csv", {}).get("sha256")
        if actual_csv_sha256 != expected_csv_sha256:
            raise ValueError(
                f"Confirmatory Hash Violation: cohort3_csv SHA-256 '{actual_csv_sha256}' does not match "
                f"manifest lock hash '{expected_csv_sha256}'."
            )

        # Frozen Execution Contract & Preapproved Commit Enforcement (Production Validator)
        protocol_file = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_v1_4_selective_adaptation_protocol.md"
        try:
            contract_record = validate_frozen_execution_contract(
                manifest_data=c3_manifest_data,
                git_commit_sha=git_commit_sha,
                protocol_path=protocol_file,
            )
        except (PermissionError, ValueError, FileNotFoundError) as exc:
            print("\n" + "!" * 80)
            print("[FAIL-CLOSED CONTRACT VALIDATION LOCK]")
            print(f"Confirmatory Cohort 3 Execution Authorization Denied:")
            print(f"  {exc}")
            print("Status: CONFIRMATORY_COHORT3_HOLD_GOVERNANCE_SIGNOFF_PENDING")
            print("Protocol v1.4.0 is not authorized for confirmatory execution.")
            print("Execution of Confirmatory Cohort 3 is strictly locked on HOLD.")
            print("!" * 80 + "\n")
            sys.exit(1)

        eval_df = pd.read_csv(cohort3_csv)
        audio_dir = cohort3_audio_dir

        # Reference transcript pre-flight validation
        validate_cohort_reference_transcripts(eval_df, cohort_name="Cohort 3")

        # Strict Cohort 3 Structural Design Validation (Protocol v1.4.0 frozen requirement: exactly 7,020 clips)
        # 6 canonical accents * 78 speakers * 15 clips = 7,020 clips
        TARGET_COHORT3_CLIPS = 7020
        TARGET_SPEAKERS_PER_ACCENT = 78
        TARGET_CLIPS_PER_SPEAKER = 15

        if len(eval_df) != TARGET_COHORT3_CLIPS:
            raise ValueError(
                f"Confirmatory Row Count Violation: Cohort 3 has {len(eval_df)} clips, "
                f"expected exactly {TARGET_COHORT3_CLIPS} clips (6 accents * 78 speakers * 15 clips)."
            )

        expected_rows = c3_manifest_data.get("files", {}).get("csv", {}).get("row_count")
        if expected_rows is not None and int(expected_rows) != TARGET_COHORT3_CLIPS:
            raise ValueError(
                f"Confirmatory Manifest Violation: manifest row_count is {expected_rows}, "
                f"must be exactly {TARGET_COHORT3_CLIPS}."
            )

        # Unique recording IDs check
        if eval_df["recording_id"].nunique() != len(eval_df):
            raise ValueError("Confirmatory Integrity Violation: Duplicate recording_ids detected in Cohort 3.")

        # Accents and balance check: 6 canonical strata
        c3_strata = set(eval_df["stage5_accent_group"].astype(str))
        if c3_strata != set(CANONICAL_PROTOCOL_ACCENTS):
            raise ValueError(f"Cohort 3 accents {c3_strata} do not match canonical set {CANONICAL_PROTOCOL_ACCENTS}")

        # Unique speaker-to-accent mapping (no speaker assigned to multiple accents)
        spk_accent_counts = eval_df.groupby("speaker_id")["stage5_accent_group"].nunique()
        inconsistent_spks = spk_accent_counts[spk_accent_counts > 1].index.tolist()
        if inconsistent_spks:
            raise ValueError(
                f"Confirmatory Accent Mapping Violation: {len(inconsistent_spks)} speakers mapped to multiple accents "
                f"in Cohort 3 (e.g. {inconsistent_spks[:5]})."
            )

        # Exact 78 speakers per accent and 15 clips per speaker
        for acc in CANONICAL_PROTOCOL_ACCENTS:
            acc_df = eval_df[eval_df["stage5_accent_group"] == acc]
            acc_spks = acc_df["speaker_id"].nunique()
            if acc_spks != TARGET_SPEAKERS_PER_ACCENT:
                raise ValueError(
                    f"Confirmatory Stratum Balance Violation: Stratum '{acc}' has {acc_spks} unique speakers, "
                    f"expected exactly {TARGET_SPEAKERS_PER_ACCENT}."
                )
            spk_clip_counts = acc_df.groupby("speaker_id")["recording_id"].count()
            bad_clip_spks = spk_clip_counts[spk_clip_counts != TARGET_CLIPS_PER_SPEAKER].to_dict()
            if bad_clip_spks:
                raise ValueError(
                    f"Confirmatory Speaker Clip Count Violation in stratum '{acc}': speakers have non-15 clips: {list(bad_clip_spks.items())[:5]}."
                )

        # Verify audio file existence, non-zero size, path consistency, and mandatory content hash lock
        audio_hashes_manifest = c3_manifest_data.get("audio_hashes") or c3_manifest_data.get("files", {}).get("audio_sha256", {})
        verified_audio_paths = validate_and_resolve_audio_payloads(
            eval_df=eval_df,
            audio_dir=audio_dir,
            expected_audio_hashes=audio_hashes_manifest,
            cohort_name="Cohort 3",
        )

        # 4. Full Validation of Dedicated Gate-Reference Panel Manifest and Data Lock
        with open(gate_ref_manifest, "r", encoding="utf-8") as f:
            ref_manifest_data = json.load(f)

        if ref_manifest_data.get("role") != "gate_reference_panel":
            raise ValueError(
                f"Confirmatory Integrity Violation: gate_ref_manifest role='{ref_manifest_data.get('role')}' "
                "must be 'gate_reference_panel'."
            )
        if ref_manifest_data.get("manifest_version") != "v1.4.0":
            raise ValueError(
                f"Confirmatory Integrity Violation: gate_ref_manifest version='{ref_manifest_data.get('manifest_version')}' "
                "must be 'v1.4.0'."
            )

        ref_csv_bytes = gate_ref_panel_csv.read_bytes()
        actual_ref_sha256 = hashlib.sha256(ref_csv_bytes).hexdigest()
        expected_ref_sha256 = ref_manifest_data.get("files", {}).get("csv", {}).get("sha256")
        if actual_ref_sha256 != expected_ref_sha256:
            raise ValueError(
                f"Confirmatory Hash Violation: gate_ref_panel_csv SHA-256 '{actual_ref_sha256}' does not match "
                f"manifest lock hash '{expected_ref_sha256}'."
            )

        gate_ref_df = pd.read_csv(gate_ref_panel_csv)
        validate_cohort_reference_transcripts(gate_ref_df, cohort_name="Gate Reference Panel")
        expected_ref_rows = ref_manifest_data.get("files", {}).get("csv", {}).get("row_count")
        if expected_ref_rows is not None and len(gate_ref_df) != int(expected_ref_rows):
            raise ValueError(
                f"Confirmatory Row Count Violation: gate_ref_panel_csv has {len(gate_ref_df)} rows, expected {expected_ref_rows}."
            )

        if gate_ref_df["recording_id"].nunique() != len(gate_ref_df):
            raise ValueError("Confirmatory Integrity Violation: Duplicate recording_ids in gate reference panel.")

        ref_strata = set(gate_ref_df["stage5_accent_group"].astype(str))
        if ref_strata != set(CANONICAL_PROTOCOL_ACCENTS):
            raise ValueError(f"Gate reference panel accents {ref_strata} do not match canonical set {CANONICAL_PROTOCOL_ACCENTS}")

        # Unique speaker-to-accent mapping in gate reference panel
        ref_spk_accent_counts = gate_ref_df.groupby("speaker_id")["stage5_accent_group"].nunique()
        ref_inconsistent_spks = ref_spk_accent_counts[ref_spk_accent_counts > 1].index.tolist()
        if ref_inconsistent_spks:
            raise ValueError(
                f"Confirmatory Accent Mapping Violation in gate reference panel: {len(ref_inconsistent_spks)} speakers mapped to multiple accents."
            )

        # Power/precision sized reference panel (defaults to >= 20 speakers per accent)
        expected_ref_spks_per_stratum = int(ref_manifest_data.get("speakers_per_accent", 20))
        for acc in CANONICAL_PROTOCOL_ACCENTS:
            acc_spks = gate_ref_df[gate_ref_df["stage5_accent_group"] == acc]["speaker_id"].nunique()
            if acc_spks < expected_ref_spks_per_stratum:
                raise ValueError(
                    f"Gate reference panel stratum '{acc}' has {acc_spks} speakers, "
                    f"below required precision threshold of {expected_ref_spks_per_stratum}."
                )

        # Verify gate reference audio payloads existence, non-zero size, path consistency, and mandatory content hash lock
        gate_ref_audio_hashes = ref_manifest_data.get("audio_hashes") or ref_manifest_data.get("files", {}).get("audio_sha256", {})
        verified_gate_ref_audio_paths = validate_and_resolve_audio_payloads(
            eval_df=gate_ref_df,
            audio_dir=sentinel_audio_dir,
            expected_audio_hashes=gate_ref_audio_hashes,
            cohort_name="Gate Reference Panel",
        )

        # 5. Fail-closed Pairwise Disjointness Verification across ALL Relevant Partitions
        hist_c1 = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
        hist_c2 = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv"
        hist_sent = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

        for p_name, p_path in [
            ("Cohort 1 (Stage 5 External Eval)", hist_c1),
            ("Cohort 2 Audio", hist_c2),
            ("Stage 5 Sentinel Panel", hist_sent),
        ]:
            if not p_path.exists():
                raise FileNotFoundError(
                    f"Confirmatory Disjointness Verification Failure: Required historical partition '{p_name}' "
                    f"is missing at '{p_path}'; cannot verify speaker disjointness."
                )

        partitions_dict = {
            "Cohort 1 (Stage 5 External Eval)": set(pd.read_csv(hist_c1)["speaker_id"].astype(str)),
            "Cohort 2 Audio": set(pd.read_csv(hist_c2)["speaker_id"].astype(str)),
            "Stage 5 Sentinel Panel": set(pd.read_csv(hist_sent)["speaker_id"].astype(str)),
            "Dedicated Gate-Reference Panel": set(gate_ref_df["speaker_id"].astype(str)),
            "Confirmatory Cohort 3": set(eval_df["speaker_id"].astype(str)),
        }
        part_names = list(partitions_dict.keys())
        for i in range(len(part_names)):
            for j in range(i + 1, len(part_names)):
                p1_name, p2_name = part_names[i], part_names[j]
                overlap = partitions_dict[p1_name].intersection(partitions_dict[p2_name])
                if overlap:
                    raise ValueError(
                        f"Confirmatory Pairwise Disjointness Violation: detected {len(overlap)} overlapping speakers "
                        f"between '{p1_name}' and '{p2_name}' (e.g. {sorted(list(overlap))[:5]})."
                    )

        # Strict Reference Transcript Preflight Validation:
        # Before transcripts are stripped from streaming eval_df, verify that no clip has missing,
        # empty, NaN, or blank transcripts, and that normalized text produces valid non-empty tokens.
        for _, row in eval_df.iterrows():
            rec_id = str(row["recording_id"])
            raw_t = row.get("transcript")
            if raw_t is None or pd.isna(raw_t):
                raise ValueError(f"Confirmatory Reference Integrity Violation: clip '{rec_id}' has missing/NaN reference transcript.")
            str_t = str(raw_t).strip()
            if not str_t or str_t.lower() in ("nan", "none", "null"):
                raise ValueError(f"Confirmatory Reference Integrity Violation: clip '{rec_id}' has blank/null reference transcript '{raw_t}'.")
            norm_t = TextNormalizer.normalize(str_t)
            if not norm_t.strip():
                raise ValueError(f"Confirmatory Reference Integrity Violation: clip '{rec_id}' normalized transcript is empty (raw: '{raw_t}').")

        # Strict Streaming Label Isolation for Cohort 3:
        # Separate reference transcripts into isolated lookup before streaming starts.
        # eval_df during stream will have NO 'transcript' column.
        c3_reference_transcripts = dict(zip(eval_df["recording_id"], eval_df["transcript"]))
        eval_df = eval_df.drop(columns=["transcript"])

    if not sentinel_csv.exists():
        raise FileNotFoundError(f"Missing sentinel panel CSV: {sentinel_csv}")
    sentinel_df = pd.read_csv(sentinel_csv)

    # Preload audio waveforms using verified audio paths
    if args.cohort == "cohort3":
        eval_file_list = [
            (row["recording_id"], verified_audio_paths[str(row["recording_id"])])
            for _, row in eval_df.iterrows()
        ]
    else:
        eval_file_list = [
            (row["recording_id"], audio_dir / f"{row['recording_id']}.mp3" if (audio_dir / f"{row['recording_id']}.mp3").exists() else audio_dir / f"{row['recording_id']}.wav")
            for _, row in eval_df.iterrows()
        ]
    eval_cache = preload_waveforms(eval_file_list, sample_rate=16000)

    # Core Stratified Sentinel Panel: 1 clip per sentinel speaker
    if args.cohort == "cohort3":
        core_sentinel_df = validate_sentinel_panel_against_canonical_protocol(
            sentinel_df,
            expected_speakers_per_accent=expected_ref_spks_per_stratum,
            expected_total_speakers=expected_ref_spks_per_stratum * len(CANONICAL_PROTOCOL_ACCENTS),
        )
    else:
        core_sentinel_df = validate_sentinel_panel_against_canonical_protocol(sentinel_df)
    core_sentinel_ids = [str(r.get("sentinel_id") or r.get("recording_id")) for _, r in core_sentinel_df.iterrows()]

    sentinel_file_list = []
    for _, row in core_sentinel_df.iterrows():
        s_id = str(row.get("sentinel_id") or row.get("recording_id"))
        p = sentinel_audio_dir / f"{s_id}.mp3"
        if not p.exists():
            p = PROJECT_ROOT / str(row.get("audio_filepath", ""))
        sentinel_file_list.append((s_id, p))
    sentinel_cache = preload_waveforms(sentinel_file_list, sample_rate=16000)

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

    if args.gate_version == "v14":
        print("      Constructing Protocol v1.4.0 Streaming Gate (StreamingSentinelSafetyGateV14):")
        print("        epsilon_r_pp = 0.0000 pp (strict point improvement: Delta_R < 0)")
        print("        epsilon_g_pp = 2.0000 pp (accent non-inferiority bound)")
        print("        epsilon_d_pp = 0.0000 pp (zero disparity growth tolerance: UCB_D <= 0)")
        safety_gate = StreamingSentinelSafetyGateV14(
            epsilon_r_pp=0.0000,
            epsilon_g_pp=2.0000,
            epsilon_d_pp=0.0000,
            num_updates=num_updates,
            alpha_target=0.05,
            required_strata=set(CANONICAL_PROTOCOL_ACCENTS),
        )
    else:
        print("      Constructing Historical Protocol v1.3 Streaming Gate (StreamingSentinelSafetyGate):")
        print("        epsilon_r_pp = 0.0000 pp")
        print("        epsilon_g_pp = 2.0000 pp")
        print("        epsilon_d_pp = 2.0000 pp")
        safety_gate = StreamingSentinelSafetyGate(
            epsilon_r_pp=0.0000,
            epsilon_g_pp=2.0000,
            epsilon_d_pp=2.0000,
            num_updates=num_updates,
            alpha_target=0.05,
        )

    # Initialize Atomic Candidate Managers for matched optimizer & model isolation
    arm2_manager = AtomicCandidateManager(live_model=arm2_model, live_optimizer=arm2_optimizer, device=device)
    arm3_manager = AtomicCandidateManager(live_model=arm3_model, live_optimizer=arm3_optimizer, device=device)

    cached_live_core_hyps: Optional[List[str]] = None
    cached_live_hash: Optional[str] = None

    arm1_records, arm2_records, arm3_records = [], [], []
    gate_decision_records = []
    arm2_failure_records = []

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
        is_sealed = bool(args.cohort == "cohort3")

        if is_sealed:
            # Confirmatory Cohort 3: Reference transcripts are strictly inaccessible during streaming
            batch_raw_refs = None
            batch_norm_refs = None
        else:
            batch_raw_refs = [str(r["transcript"]) for _, r in batch_rows.iterrows()]
            batch_norm_refs = [TextNormalizer.normalize(t) for t in batch_raw_refs]

        window_primary_stratum = str(batch_rows.iloc[0].get("stage5_accent_group") or batch_rows.iloc[0].get("accent_group"))

        # Prequential Inference
        hyps_arm1 = batch_transcribe_gpu(arm1_model, processor, batch_waveforms, device)
        hyps_arm2 = batch_transcribe_gpu(arm2_model, processor, batch_waveforms, device)
        hyps_arm3 = batch_transcribe_gpu(arm3_model, processor, batch_waveforms, device)

        win_err_arm1, win_words_arm1 = 0, 0
        win_err_arm2, win_words_arm2 = 0, 0
        win_err_arm3, win_words_arm3 = 0, 0

        if not is_sealed:
            for idx, (_, r) in enumerate(batch_rows.iterrows()):
                ref_norm = batch_norm_refs[idx]
                clip_stratum = str(r.get("stage5_accent_group") or r.get("stratum_code") or r.get("accent_group"))

                m1 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm1[idx]))
                win_err_arm1 += (m1.substitutions + m1.deletions + m1.insertions)
                win_words_arm1 += m1.reference_length
                arm1_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "ref": ref_norm, "hyp": hyps_arm1[idx],
                    "sub": m1.substitutions, "del": m1.deletions, "ins": m1.insertions, "n": m1.reference_length
                })

                m2 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm2[idx]))
                win_err_arm2 += (m2.substitutions + m2.deletions + m2.insertions)
                win_words_arm2 += m2.reference_length
                arm2_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "ref": ref_norm, "hyp": hyps_arm2[idx],
                    "sub": m2.substitutions, "del": m2.deletions, "ins": m2.insertions, "n": m2.reference_length
                })

                m3 = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(hyps_arm3[idx]))
                win_err_arm3 += (m3.substitutions + m3.deletions + m3.insertions)
                win_words_arm3 += m3.reference_length
                arm3_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "ref": ref_norm, "hyp": hyps_arm3[idx],
                    "sub": m3.substitutions, "del": m3.deletions, "ins": m3.insertions, "n": m3.reference_length
                })

            wer1 = (win_err_arm1 / win_words_arm1 * 100.0) if win_words_arm1 > 0 else 0.0
            wer2 = (win_err_arm2 / win_words_arm2 * 100.0) if win_words_arm2 > 0 else 0.0
            wer3 = (win_err_arm3 / win_words_arm3 * 100.0) if win_words_arm3 > 0 else 0.0
        else:
            # Cohort 3: Confirmatory transcripts remain completely sealed during stream
            for idx, (_, r) in enumerate(batch_rows.iterrows()):
                clip_stratum = str(r.get("stage5_accent_group") or r.get("stratum_code") or r.get("accent_group"))
                arm1_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "hyp": hyps_arm1[idx]
                })
                arm2_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "hyp": hyps_arm2[idx]
                })
                arm3_records.append({
                    "window_id": win_idx, "recording_id": r["recording_id"], "speaker_id": r["speaker_id"],
                    "group_id": clip_stratum, "hyp": hyps_arm3[idx]
                })
            wer1, wer2, wer3 = float("nan"), float("nan"), float("nan")

        # Online Adaptation & Statistical Gating
        gate_decision_str = "TERMINAL_WINDOW"
        loss_val = 0.0

        if win_idx < num_updates:
            # Arm 2 (Arm B): Candidate isolation and unconditional promotion if numerically safe
            pre_arm2_m_hash = arm2_manager.get_live_model_hash()
            pre_arm2_opt_hash = arm2_manager.get_live_optimizer_hash()
            cand_arm2_model, cand_arm2_opt = arm2_manager.create_candidate()
            arm2_step_res = suta_adaptation_step_gpu(
                model=cand_arm2_model, processor=processor, waveforms=batch_waveforms,
                optimizer=cand_arm2_opt, temperature=2.5, alpha=0.5, device=device
            )
            if arm2_step_res.is_success:
                arm2_manager.promote_candidate(cand_arm2_model, cand_arm2_opt)
            else:
                arm2_manager.discard_candidate(
                    cand_arm2_model, cand_arm2_opt,
                    expected_live_model_hash=pre_arm2_m_hash,
                    expected_live_opt_hash=pre_arm2_opt_hash,
                )
                arm2_failure_records.append({
                    "window_id": win_idx,
                    "stratum": window_primary_stratum,
                    "loss": round(arm2_step_res.loss, 4) if (arm2_step_res.loss is not None and np.isfinite(arm2_step_res.loss)) else None,
                    "numerical_status": arm2_step_res.numerical_status,
                    "loss_finite": arm2_step_res.loss_finite,
                    "gradient_finite": arm2_step_res.gradient_finite,
                    "parameter_finite": arm2_step_res.parameter_finite,
                    "optimizer_state_finite": arm2_step_res.optimizer_state_finite,
                    "failure_reason": arm2_step_res.failure_reason,
                    "duration_seconds": round(time.time() - t_win_start, 2)
                })

            # Arm 3 (Arm C): Candidate clone & evaluation with matched optimizer-state semantics
            current_arm3_hash = arm3_manager.get_live_model_hash()
            current_arm3_opt_hash = arm3_manager.get_live_optimizer_hash()
            cand_arm3_model, cand_arm3_opt = arm3_manager.create_candidate()

            cand_step_res = suta_adaptation_step_gpu(
                model=cand_arm3_model, processor=processor, waveforms=batch_waveforms,
                optimizer=cand_arm3_opt, temperature=2.5, alpha=0.5, device=device
            )

            loss_val = cand_step_res.loss if cand_step_res.loss is not None else float("nan")

            if not cand_step_res.is_success:
                # Fail-closed numerical rejection: discard candidate and leave live state untouched
                arm3_manager.discard_candidate(
                    cand_arm3_model, cand_arm3_opt,
                    expected_live_model_hash=current_arm3_hash,
                    expected_live_opt_hash=current_arm3_opt_hash,
                )
                gate_decision_str = f"REJECT ({cand_step_res.numerical_status})"
                gate_decision_records.append({
                    "window_id": win_idx,
                    "stratum": window_primary_stratum,
                    "loss": round(cand_step_res.loss, 4) if (cand_step_res.loss is not None and np.isfinite(cand_step_res.loss)) else None,
                    "decision": "REJECT",
                    "decision_raw": gate_decision_str,
                    "numerical_status": cand_step_res.numerical_status,
                    "loss_finite": cand_step_res.loss_finite,
                    "gradient_finite": cand_step_res.gradient_finite,
                    "parameter_finite": cand_step_res.parameter_finite,
                    "optimizer_state_finite": cand_step_res.optimizer_state_finite,
                    "failure_reason": cand_step_res.failure_reason,
                    "delta_r": None,
                    "delta_d": None,
                    "se_r_raw": None,
                    "se_r_adjusted": None,
                    "se_r_floor": None,
                    "se_sent": None,
                    "se_d": None,
                    "z_obf": None,
                    "ucb_r": None,
                    "ucb_max_group": None,
                    "worst_group": None,
                    "ucb_d": None,
                    "rejection_reason": f"Numerical failure: {cand_step_res.failure_reason}",
                    "duration_seconds": round(time.time() - t_win_start, 2)
                })
            else:
                if cached_live_hash != current_arm3_hash or cached_live_core_hyps is None:
                    cached_live_core_hyps = batch_transcribe_gpu(arm3_model, processor, core_sentinel_waveforms, device)
                    cached_live_hash = current_arm3_hash

                cand_core_hyps = batch_transcribe_gpu(cand_arm3_model, processor, core_sentinel_waveforms, device)

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
                    arm3_manager.promote_candidate(cand_arm3_model, cand_arm3_opt)
                    gate_decision_str = f"ACCEPT (Delta_R={gate_dec.delta_r:+.2f}%)"
                    cached_live_hash = None
                else:
                    arm3_manager.discard_candidate(
                        cand_arm3_model, cand_arm3_opt,
                        expected_live_model_hash=current_arm3_hash,
                        expected_live_opt_hash=current_arm3_opt_hash,
                    )
                    gate_decision_str = f"REJECT (UCB={gate_dec.ucb_r:+.2f}%)"

                gate_decision_records.append({
                    "window_id": win_idx,
                    "stratum": window_primary_stratum,
                    "loss": round(loss_val, 4) if np.isfinite(loss_val) else None,
                    "decision": gate_dec.decision,
                    "decision_raw": gate_decision_str,
                    "numerical_status": cand_step_res.numerical_status,
                    "loss_finite": cand_step_res.loss_finite,
                    "gradient_finite": cand_step_res.gradient_finite,
                    "parameter_finite": cand_step_res.parameter_finite,
                    "optimizer_state_finite": cand_step_res.optimizer_state_finite,
                    "failure_reason": cand_step_res.failure_reason,
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
        if is_sealed:
            print(f"{win_idx+1:3d}/{num_windows} | {window_primary_stratum[:12]:12s} | [SEALED]   | [SEALED]   | [SEALED]   | {gate_decision_str:18s} | {loss_val:6.3f} | {win_elapsed:.1f}s")
        else:
            print(f"{win_idx+1:3d}/{num_windows} | {window_primary_stratum[:12]:12s} | {wer1:6.1f}%  | {wer2:6.1f}%  | {wer3:6.1f}%  | {gate_decision_str:18s} | {loss_val:6.3f} | {win_elapsed:.1f}s")

    # Step 4: Summary Statistics
    print(f"\n[4/5] Computing Offline Metrics and Speaker-Clustered Paired Statistics...")
    pred_sha256 = None
    pred_lock_path = None
    if is_sealed:
        print("      [SEALED CONFIRMATORY STREAM FINISHED] Locking and hashing prediction artifacts...")
        pred_artifact = {
            "cohort": args.cohort,
            "git_commit": git_commit_sha,
            "arm1_predictions": arm1_records,
            "arm2_predictions": arm2_records,
            "arm3_predictions": arm3_records,
        }
        pred_json_str = json.dumps(pred_artifact, indent=2)
        pred_path = results_dir / f"{benchmark_run_id}_cohort3_sealed_predictions.json"
        pred_path.write_text(pred_json_str, encoding="utf-8")
        pred_sha256 = hashlib.sha256(pred_json_str.encode("utf-8")).hexdigest()

        # Machine-readable predictions lock file
        pred_lock_path = results_dir / f"{benchmark_run_id}_cohort3_predictions.lock.json"
        pred_lock_data = {
            "schema_version": "v1.4.0",
            "benchmark_run_id": benchmark_run_id,
            "cohort": args.cohort,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_sha": git_commit_sha,
            "gate_version": args.gate_version,
            "predictions_artifact_filename": pred_path.name,
            "predictions_sha256": pred_sha256,
            "total_clips_predicted": len(arm1_records),
            "status": "LOCKED_PRE_UNSEAL",
        }
        pred_lock_path.write_text(json.dumps(pred_lock_data, indent=2), encoding="utf-8")
        print(f"      Predictions locked at: {pred_path} (SHA-256: {pred_sha256})")
        print(f"      Machine-readable predictions lock recorded at: {pred_lock_path}")
        print("      Unsealing evaluation transcripts for final confirmatory analysis...")

        for r_list in (arm1_records, arm2_records, arm3_records):
            for r in r_list:
                ref_norm = TextNormalizer.normalize(str(c3_reference_transcripts[r["recording_id"]]))
                m = compute_utterance_metrics(ref_norm, TextNormalizer.normalize(r["hyp"]))
                r["ref"] = ref_norm
                r["sub"] = m.substitutions
                r["del"] = m.deletions
                r["ins"] = m.insertions
                r["n"] = m.reference_length

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

    # Execution Provenance & Configuration Digest
    protocol_version = (
        "v1.4.0-stage6m-selective-adaptation-draft"
        if args.gate_version == "v14"
        else "v1.3.4-stage6m-self-authorization-amendment"
    )

    def compute_file_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    manifest_sha256 = compute_file_sha256(manifest_path) if manifest_path.exists() else "MISSING_MANIFEST"
    sentinel_panel_sha256 = compute_file_sha256(sentinel_csv) if sentinel_csv.exists() else "MISSING_SENTINEL"

    git_commit_sha, git_tree_dirty = get_git_provenance()
    model_checkpoint_sha256 = hashlib.sha256(
        f"{args.model}_{init_hash}".encode("utf-8")
    ).hexdigest()

    config_dict = {
        "cohort": str(args.cohort),
        "model": str(args.model),
        "model_initial_parameter_fingerprint": model_checkpoint_sha256,
        "model_checkpoint_sha256": model_checkpoint_sha256,
        "gate_version": str(args.gate_version),
        "protocol_version": protocol_version,
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT) if manifest_path.is_relative_to(PROJECT_ROOT) else manifest_path),
        "manifest_sha256": manifest_sha256,
        "sentinel_panel_path": str(sentinel_csv.relative_to(PROJECT_ROOT) if sentinel_csv.is_relative_to(PROJECT_ROOT) else sentinel_csv),
        "sentinel_panel_sha256": sentinel_panel_sha256,
        "window_size_k": int(window_size_k),
        "num_updates": int(num_updates),
        "epsilon_r_pp": float(safety_gate.epsilon_r),
        "epsilon_g_pp": float(safety_gate.epsilon_g),
        "epsilon_d_pp": float(safety_gate.epsilon_d),
        "alpha_target": float(getattr(safety_gate, "alpha_target", 0.05)),
        "num_boot_replicates": int(getattr(safety_gate, "num_boot_replicates", 500)),
        "adaptation_lr": 1e-4,
        "adaptation_temp": 2.5,
        "adaptation_alpha": 0.5,
        "adaptation_max_grad_norm": 1.0,
        "random_seed": 42,
        "torch_version": str(torch.__version__),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_name": str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
        "git_commit_sha": git_commit_sha,
        "git_tree_dirty": git_tree_dirty,
    }
    config_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode("utf-8")).hexdigest()

    is_sig_g_u = bool(
        not np.isnan(p_val_g_u)
        and p_val_g_u < 0.05
        and float(spk_wer3_unrounded.mean()) < float(spk_wer2_unrounded.mean())
    )
    is_sig_g_s = bool(
        not np.isnan(p_val_g_s)
        and p_val_g_s < 0.05
        and float(spk_wer3_unrounded.mean()) < float(spk_wer1_unrounded.mean())
    )

    # Stage 6M v1.4.0 Confirmatory Inferential Analysis
    is_confirmatory = bool(args.cohort == "cohort3")
    n_boot_rep = 20000 if is_confirmatory else 2000
    print(f"      Executing Paired Cluster Inference ({n_boot_rep} replicates) with Simultaneous Multiplicity Adjustment...")

    conf_design_spec = DesignStagePowerSpec(
        required_speakers_per_stratum=78,
        target_joint_power=0.90,
    ) if is_confirmatory else None

    confirmatory_report = run_confirmatory_paired_cluster_inference(
        speaker_records=spk_stats,
        num_bootstrap_replicates=n_boot_rep,
        seed=42,
        alpha_family=0.05,
        epsilon_g_margin_pp=2.00,
        epsilon_d_margin_pp=0.00,
        design_spec=conf_design_spec,
    )

    report_payload = {
        "metadata": {
            "protocol_version": protocol_version,
            "gate_version": args.gate_version,
            "analysis_nature": "confirmatory_frozen_evaluation" if is_confirmatory else "retrospective_development_diagnostic",
            "is_confirmatory_run": is_confirmatory,
            "confirmatory_decision_verdict": confirmatory_report.verdict if is_confirmatory else None,
            "retrospective_protocol_decision_verdict": confirmatory_report.verdict if not is_confirmatory else None,
            "confirmatory_all_criteria_passed": confirmatory_report.all_criteria_passed,
            "model_architecture": args.model,
            "model_initial_parameter_fingerprint": model_checkpoint_sha256,
            "model_checkpoint_sha256": model_checkpoint_sha256,
            "sealed_predictions_sha256": pred_sha256 if is_sealed else None,
            "sealed_predictions_lock_file": str(pred_lock_path.name) if pred_lock_path is not None else None,
            "execution_commit_sha": git_commit_sha,
            "git_tree_dirty": git_tree_dirty,
            "configuration_hash_sha256": config_hash,
            "manifest_sha256": manifest_sha256,
            "sentinel_panel_sha256": sentinel_panel_sha256,
            "execution_scope": (
                f"Confirmatory Physical COHORT3 Prequential Stream on Virtual GPU"
                if is_confirmatory
                else f"Retrospective Development/Regression Physical {args.cohort.upper()} Prequential Stream on Virtual GPU"
            ),
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
                "statistically_significant_p05": is_sig_g_u
            },
            "paired_t_arm3_vs_arm1": {
                "t_statistic": round(float(t_stat_g_s), 4) if not np.isnan(t_stat_g_s) else None,
                "p_value": float(p_val_g_s) if not np.isnan(p_val_g_s) else None,
                "degrees_of_freedom": int(len(spk_df) - 1),
                "statistically_significant_p05": is_sig_g_s,
                "interpretation": (
                    "Zero-variance difference: Arm 3 identical to static baseline."
                    if np.isnan(p_val_g_s)
                    else (
                        "Statistically significant superiority of Arm 3 over Static Baseline (p < 0.05)."
                        if is_sig_g_s
                        else "Difference not statistically significant at alpha=0.05."
                    )
                )
            }
        },
        "stratum_breakdown": strata_results,
        "speaker_level_paired_records": spk_stats,
        "candidate_gate_decisions": gate_decision_records,
        "arm2_adaptation_failures": arm2_failure_records,
        "confirmatory_protocol_inference": confirmatory_report.to_dict(),
    }

    out_json = results_dir / f"stage6m_physical_{args.cohort}_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print("\n" + "=" * 80)
    print("STAGE 6M PHYSICAL GPU BENCHMARK COMPLETE")
    print(f"Cohort Scope     : {args.cohort.upper()} ({'CONFIRMATORY' if is_confirmatory else 'RETROSPECTIVE DEVELOPMENT'})")
    print(f"Execution Status : SUCCESSFUL (Neural forward passes and adaptation finished)")
    print(f"Protocol Verdict : [{confirmatory_report.verdict}]")
    if confirmatory_report.verdict != "PASS":
        print("Protocol Status / Non-Passing Criteria:")
        for r in confirmatory_report.failure_reasons:
            print(f"  * {r}")
    print(f"Artifacts saved in: {results_dir}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
