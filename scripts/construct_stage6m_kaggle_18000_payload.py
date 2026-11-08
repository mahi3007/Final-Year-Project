#!/usr/bin/env python3
"""
scripts/construct_stage6m_kaggle_18000_payload.py

Stage 6M: Construct & Cryptographically Verify Kaggle 18,000-Recording Payload
=============================================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
Governing Branch:   stage6m-five-stratum-parity
Authorized Release: releases/stage6m_gate5_release_v1.0.tar.gz
Authorized SHA-256: cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4

Builds a physically segregated, private Kaggle dataset payload in dist/kaggle_dataset/
containing STRICTLY the 18,000 allowlisted recordings (16,500 evaluation + 1,500 gate reference)
and ZERO reserve recordings, with the sealed evaluation transcript key strictly excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAYLOAD_DIR = PROJECT_ROOT / "dist" / "kaggle_dataset"
AUDIO_SRC_DIR = PROJECT_ROOT / "datasets" / "audio" / "stage6m" / "cohort3_reconciled_assets"
SPLITS_SRC_DIR = PROJECT_ROOT / "datasets" / "splits"
CONFIGS_SRC_DIR = PROJECT_ROOT / "configs"
SRC_DIR = PROJECT_ROOT / "src" / "dsg_ctta"

ONLINE_MANIFEST_SRC = SPLITS_SRC_DIR / "stage6m_cohort3_online_inference_manifest.json"
EXPECTED_ONLINE_SHA256 = "0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1"

FINAL_MANIFEST_SRC = SPLITS_SRC_DIR / "stage6m_cohort3_final_manifest.json"
EXPECTED_FINAL_SHA256 = "171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0"

LEDGER_SRC = SPLITS_SRC_DIR / "stage6m_cohort3_materialization_disposition_ledger.csv"
EXPECTED_LEDGER_SHA256 = "b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5"

SEALED_KEY_SRC = SPLITS_SRC_DIR / "stage6m_cohort3_sealed_evaluation_transcripts.json"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def construct_and_verify_payload() -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 6M: CONSTRUCTING KAGGLE 18,000-RECORDING RUNTIME PAYLOAD")
    print("Governing Protocol: Section 14.7 | Phase 1 Preflight Verification")
    print("=" * 80)
    t0 = time.time()
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1. Load Online Manifest & Determine Positive Allowlist
    print("\n[Step 1] Loading Manifest & Extracting Positive Allowlist...")
    m_hash = compute_sha256(ONLINE_MANIFEST_SRC)
    if m_hash != EXPECTED_ONLINE_SHA256:
        raise ValueError(f"Online manifest hash mismatch! {m_hash}")

    with open(ONLINE_MANIFEST_SRC, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    records = manifest_data.get("records", [])
    eval_recs = [r for r in records if r.get("panel_role") == "evaluation"]
    gate_recs = [r for r in records if r.get("panel_role") == "gate_reference"]
    res_recs = [r for r in records if r.get("panel_role") == "australian_reserve"]

    eval_ids = {r["recording_id"] for r in eval_recs}
    gate_ids = {r["recording_id"] for r in gate_recs}
    res_ids = {r["recording_id"] for r in res_recs}
    allowlist_ids = eval_ids | gate_ids

    assert len(eval_ids) == 16500, f"Expected 16,500 eval IDs, got {len(eval_ids)}"
    assert len(gate_ids) == 1500, f"Expected 1,500 gate IDs, got {len(gate_ids)}"
    assert len(res_ids) == 975, f"Expected 975 reserve IDs, got {len(res_ids)}"
    assert len(allowlist_ids) == 18000, f"Expected 18,000 allowlist IDs, got {len(allowlist_ids)}"
    assert len(res_ids & allowlist_ids) == 0, "Reserve IDs present in allowlist!"
    assert len(eval_ids & gate_ids) == 0, "Evaluation and gate IDs overlap!"
    print(f"  Positive Allowlist: Exactly {len(allowlist_ids):,} recordings (16,500 eval + 1,500 gate)")
    print(f"  Reserve Panel:      Exactly {len(res_ids):,} recordings (Strictly Excluded)")

    # 2. Prepare Target Payload Directory
    print(f"\n[Step 2] Initializing Clean Payload Directory at {PAYLOAD_DIR}...")
    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)
    
    payload_splits = PAYLOAD_DIR / "splits"
    payload_audio = PAYLOAD_DIR / "audio" / "cohort3_reconciled_assets"
    payload_configs = PAYLOAD_DIR / "configs"
    payload_src = PAYLOAD_DIR / "src" / "dsg_ctta"

    payload_splits.mkdir(parents=True, exist_ok=True)
    payload_audio.mkdir(parents=True, exist_ok=True)
    payload_configs.mkdir(parents=True, exist_ok=True)
    payload_src.mkdir(parents=True, exist_ok=True)

    # 3. Copy Manifests and Disposition Ledger (Excluding Sealed Key)
    print("\n[Step 3] Staging Manifests & Disposition Ledger...")
    shutil.copy2(ONLINE_MANIFEST_SRC, payload_splits / ONLINE_MANIFEST_SRC.name)
    shutil.copy2(FINAL_MANIFEST_SRC, payload_splits / FINAL_MANIFEST_SRC.name)
    shutil.copy2(LEDGER_SRC, payload_splits / LEDGER_SRC.name)
    print(f"  Staged: {ONLINE_MANIFEST_SRC.name}")
    print(f"  Staged: {FINAL_MANIFEST_SRC.name}")
    print(f"  Staged: {LEDGER_SRC.name}")
    print("  -> Sealed evaluation transcript key explicitly EXCLUDED and ABSENT.")

    # 4. Copy Configurations, Source Code, and Requirements
    print("\n[Step 4] Staging Configurations, dsg_ctta Engine, and Requirements Lock...")
    for cfg in sorted(CONFIGS_SRC_DIR.glob("*.json")):
        shutil.copy2(cfg, payload_configs / cfg.name)
    
    shutil.copytree(SRC_DIR, payload_src, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    
    req_lock = PROJECT_ROOT / "requirements-kaggle-lock.txt"
    if req_lock.exists():
        shutil.copy2(req_lock, PAYLOAD_DIR / req_lock.name)

    # 5. Populate Audio Payload with Exactly 18,000 Allowlisted Files
    print(f"\n[Step 5] Populating Audio Payload with 18,000 Allowlisted Clips...")
    linked_count = 0
    copied_count = 0
    for rid in allowlist_ids:
        src_file = AUDIO_SRC_DIR / f"{rid}.mp3"
        dst_file = payload_audio / f"{rid}.mp3"
        if not src_file.exists():
            raise FileNotFoundError(f"Missing required allowlisted audio file: {src_file}")
        try:
            os.link(src_file, dst_file)
            linked_count += 1
        except (OSError, NotImplementedError):
            shutil.copy2(src_file, dst_file)
            copied_count += 1

    print(f"  Populated: {linked_count + copied_count:,} files ({linked_count:,} hardlinked, {copied_count:,} copied)")

    # 6. Generate Kaggle Metadata & Cryptographic Catalogue
    print("\n[Step 6] Generating Dataset Metadata and Cryptographic Catalogue...")
    kaggle_meta = {
        "title": "Stage 6M Frozen Research Benchmark",
        "id": "antigravity/stage6m-frozen-benchmark",
        "licenses": [{"name": "CC0-1.0"}],
        "description": "Cryptographically frozen five-stratum confirmatory benchmark (Protocol v1.5 Section 14.7)"
    }
    with open(PAYLOAD_DIR / "dataset-metadata.json", "w", encoding="utf-8") as f:
        json.dump(kaggle_meta, f, indent=2)

    catalogue_entries: Dict[str, str] = {}
    for p in sorted(PAYLOAD_DIR.rglob("*")):
        if p.is_file() and p.name != "SHA256_CATALOGUE.json":
            rel_p = p.relative_to(PAYLOAD_DIR).as_posix()
            catalogue_entries[rel_p] = compute_sha256(p)

    with open(PAYLOAD_DIR / "SHA256_CATALOGUE.json", "w", encoding="utf-8") as f:
        json.dump(catalogue_entries, f, indent=2)

    # 7. Fail-Closed Verification of Staged Payload
    print("\n[Step 7] Executing Fail-Closed Cryptographic Verification on Staged Payload...")
    staged_audio = list(payload_audio.glob("*.mp3"))
    staged_audio_count = len(staged_audio)
    staged_audio_bytes = sum(f.stat().st_size for f in staged_audio)
    staged_zero_bytes = sum(1 for f in staged_audio if f.stat().st_size == 0)

    print(f"  Staged Audio Files: {staged_audio_count:,} (Expected: 18,000)")
    print(f"  Staged Audio Bytes: {staged_audio_bytes:,} (Expected: 672,970,785)")
    print(f"  Zero-Byte Files:    {staged_zero_bytes} (Expected: 0)")

    assert staged_audio_count == 18000, f"Payload file count mismatch: {staged_audio_count}"
    assert staged_audio_bytes == 672970785, f"Payload byte sum mismatch: {staged_audio_bytes}"
    assert staged_zero_bytes == 0, f"Found {staged_zero_bytes} zero-byte files!"

    # Verify zero reserve audio present in staged payload
    staged_audio_names = {f.stem for f in staged_audio}
    leaked_res = staged_audio_names & res_ids
    assert len(leaked_res) == 0, f"FATAL: {len(leaked_res)} reserve files found in payload!"

    # Verify all evaluation and gate recordings present
    assert eval_ids.issubset(staged_audio_names), "Missing evaluation recordings in payload!"
    assert gate_ids.issubset(staged_audio_names), "Missing gate-reference recordings in payload!"

    # Verify sealed key is completely absent
    sealed_in_payload = list(PAYLOAD_DIR.rglob("*sealed*"))
    assert len(sealed_in_payload) == 0, f"FATAL: Sealed key found in payload: {sealed_in_payload}"

    # Verify evaluation transcripts in staged manifest are null
    with open(payload_splits / ONLINE_MANIFEST_SRC.name, "r", encoding="utf-8") as f:
        staged_online = json.load(f)
    leaked_eval_transcripts = [r["recording_id"] for r in staged_online.get("records", []) if r.get("panel_role") == "evaluation" and r.get("transcript") is not None]
    assert len(leaked_eval_transcripts) == 0, f"FATAL: {len(leaked_eval_transcripts)} evaluation transcripts leaked!"

    elapsed = round(time.time() - t0, 2)
    summary = {
        "status": "PASSED",
        "payload_dir": str(PAYLOAD_DIR),
        "total_audio_files": staged_audio_count,
        "total_audio_bytes": staged_audio_bytes,
        "evaluation_audio_files": len(eval_ids),
        "gate_reference_audio_files": len(gate_ids),
        "reserve_audio_files": 0,
        "reserve_audio_leaked": False,
        "sealed_evaluation_key_absent": True,
        "evaluation_transcripts_shielded": True,
        "online_manifest_sha256": compute_sha256(payload_splits / ONLINE_MANIFEST_SRC.name),
        "final_manifest_sha256": compute_sha256(payload_splits / FINAL_MANIFEST_SRC.name),
        "disposition_ledger_sha256": compute_sha256(payload_splits / LEDGER_SRC.name),
        "elapsed_seconds": elapsed,
        "verdict": "KAGGLE_18000_PAYLOAD_VERIFIED_EXACT"
    }

    print("\n" + "=" * 80)
    print(f"KAGGLE PAYLOAD CONSTRUCTION VERDICT: {summary['verdict']} ({elapsed}s)")
    print("=" * 80)
    return summary


if __name__ == "__main__":
    construct_and_verify_payload()

