#!/usr/bin/env python3
"""
scratch/build_gate5_mount_kernel.py

Constructs the Kaggle kernel package for Gate 5 Runtime Mount Verification
and GPU Preflight Audit (Protocol Section 14.7).
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KERNEL_DIR = PROJECT_ROOT / "cloud" / "kaggle" / "gate5_mount_kernel"
KERNEL_DIR.mkdir(parents=True, exist_ok=True)

# 1. kernel-metadata.json
metadata = {
    "id": "venkataakhil07/stage-6m-gate-5-runtime-mount-audit",
    "title": "Stage 6M Gate 5 Runtime Mount Audit",
    "code_file": "run_gate5_runtime_mount_audit.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": "true",
    "enable_gpu": "true",
    "enable_tpu": "false",
    "enable_internet": "true",
    "dataset_sources": [
        "venkataakhil07/stage6m-frozen-benchmark"
    ],
    "competition_sources": [],
    "kernel_sources": [],
    "model_sources": []
}

with open(KERNEL_DIR / "kernel-metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

# Copy runner and checksums for local hash verification in kernel
runner_dir = KERNEL_DIR / "runner"
runner_dir.mkdir(parents=True, exist_ok=True)
source_runner = PROJECT_ROOT / "releases" / "extracted_verified_gate5_v1.0" / "stage6m_gate5_release_v1.0" / "runner" / "run_stage6m_cohort3_kaggle_benchmark.py"
shutil.copy2(source_runner, runner_dir / "run_stage6m_cohort3_kaggle_benchmark.py")

checksums_file = PROJECT_ROOT / "releases" / "extracted_verified_gate5_v1.0" / "stage6m_gate5_release_v1.0" / "checksums.sha256"
shutil.copy2(checksums_file, KERNEL_DIR / "checksums.sha256")

# 2. Build Notebook Cells
cell_0_md = """# Stage 6M Gate 5: Kaggle Runtime Mount & Hardware Preflight Audit
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Authorization:** `STAGE6M-GATE5-AUTH-DECISION-20261108`  
**Execution Target:** Virtual GPU Cluster (NVIDIA Tesla T4 × 2)  
**Authorized Dataset:** `venkataakhil07/stage6m-frozen-benchmark` (Private)  

This notebook performs all preflight verification checks (Steps 1 through 5) directly inside the live Kaggle worker environment before any model initialization or confirmatory inference."""

cell_1_code = """# ==============================================================================
# STEP 1: VERIFY KAGGLE DATASET MOUNT (FAIL-CLOSED, NO FALLBACK)
# ==============================================================================
import os, sys, json, hashlib, time, zipfile
from pathlib import Path

print("=" * 80)
print("STAGE 6M GATE 5: STEP 1 - KAGGLE DATASET MOUNT VERIFICATION")
print("=" * 80)

input_root = Path("/kaggle/input")
assert input_root.exists(), "FATAL: /kaggle/input directory does not exist!"

print("Scanning complete tree under /kaggle/input:")
for root, dirs, files in os.walk(input_root):
    depth = len(Path(root).relative_to(input_root).parts)
    if depth <= 3:
        indent = "  " * depth
        print(f"{indent}[DIR] {root} (dirs: {len(dirs)}, files: {len(files)})")
        if files and depth <= 2:
            print(f"{indent}      Sample files: {files[:5]}")

# Look for SHA256_CATALOGUE.json anywhere under /kaggle/input
cat_candidates = list(input_root.glob("**/SHA256_CATALOGUE.json"))
print(f"Found catalogue candidates: {cat_candidates}")
assert len(cat_candidates) > 0, f"FATAL FAIL-CLOSED: SHA256_CATALOGUE.json not found anywhere under /kaggle/input!"
DATASET_ROOT = cat_candidates[0].parent
print(f"Mounted Dataset Root Resolved from Catalogue: {DATASET_ROOT.resolve()}")

top_level_items = sorted(os.listdir(DATASET_ROOT))
print(f"Top-Level Inventory ({len(top_level_items)} items):")
for item in top_level_items:
    item_path = DATASET_ROOT / item
    if item_path.is_dir():
        sub_count = len(os.listdir(item_path))
        print(f"  [DIR]  {item}/ ({sub_count} items)")
    else:
        sz = item_path.stat().st_size
        print(f"  [FILE] {item} ({sz:,} bytes)")

# Determine archive vs extracted state
is_audio_extracted = (DATASET_ROOT / "audio" / "cohort3_reconciled_assets").exists()
is_audio_zip = (DATASET_ROOT / "audio.zip").exists()
print(f"Audio directory status: extracted={is_audio_extracted}, zip_archive={is_audio_zip}")
assert is_audio_extracted or is_audio_zip, "FATAL: Neither audio directory nor audio.zip found!"
print("STEP 1 VERIFIED: Kaggle dataset mount confirmed.")
"""

cell_2_code = """# ==============================================================================
# STEP 2: VERIFY AUDIO AVAILABILITY, EXACTNESS & RESERVE ISOLATION
# ==============================================================================
print("=" * 80)
print("STAGE 6M GATE 5: STEP 2 - AUDIO AVAILABILITY & INVARIANT AUDIT")
print("=" * 80)

working_extracted = Path("/kaggle/working/stage6m_extracted")

if (DATASET_ROOT / "audio" / "cohort3_reconciled_assets").exists():
    audio_dir = DATASET_ROOT / "audio" / "cohort3_reconciled_assets"
    print(f"Using pre-extracted audio directory: {audio_dir}")
elif (DATASET_ROOT / "audio.zip").exists():
    print("Extracting audio.zip into controlled working directory...")
    working_extracted.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DATASET_ROOT / "audio.zip", "r") as z:
        z.extractall(working_extracted)
    audio_dir = working_extracted / "audio" / "cohort3_reconciled_assets"
    if not audio_dir.exists():
        audio_dir = working_extracted / "cohort3_reconciled_assets"
    print(f"Extracted audio directory: {audio_dir}")
else:
    raise FileNotFoundError("Audio directory not resolvable!")

audio_files = sorted(audio_dir.glob("*.mp3"))
audio_count = len(audio_files)
total_bytes = sum(f.stat().st_size for f in audio_files)
print(f"Physical Audio Files Count: {audio_count:,} (Expected: 18,000)")
print(f"Total Physical Audio Bytes:  {total_bytes:,} (Expected: 672,970,785)")

assert audio_count == 18000, f"FATAL: Audio count mismatch: got {audio_count}, expected 18,000"
assert total_bytes == 672970785, f"FATAL: Audio bytes mismatch: got {total_bytes}, expected 672,970,785"

# Load SHA256 Catalogue
cat_path = DATASET_ROOT / "SHA256_CATALOGUE.json"
assert cat_path.exists(), f"FATAL: Missing catalogue at {cat_path}"
with open(cat_path, "r", encoding="utf-8") as f:
    catalogue = json.load(f)
audio_cat = {k: v for k, v in catalogue.items() if k.startswith("audio/")}
print(f"Catalogue Audio Entries: {len(audio_cat):,} (Expected: 18,000)")
assert len(audio_cat) == 18000, f"Catalogue count mismatch: {len(audio_cat)}"

# Verify all 18,000 hashes bitwise
print("Verifying 18,000 physical audio SHA-256 digests against frozen catalogue...")
t0 = time.time()
hash_mismatches = []
for f in audio_files:
    rel_key = f"audio/cohort3_reconciled_assets/{f.name}"
    expected_hash = audio_cat.get(rel_key)
    if not expected_hash:
        hash_mismatches.append((f.name, "MISSING_IN_CATALOGUE", None))
        continue
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        while chunk := fh.read(65536):
            h.update(chunk)
    actual_hash = h.hexdigest()
    if actual_hash != expected_hash:
        hash_mismatches.append((f.name, actual_hash, expected_hash))
t1 = time.time()
print(f"Hashed and verified 18,000 files in {t1 - t0:.2f} seconds.")
assert len(hash_mismatches) == 0, f"FATAL: {len(hash_mismatches)} hash mismatches detected!"
print("[PASS] All 18,000 audio hashes match the frozen catalogue bitwise exact.")

# Verify role division and reserve isolation
manifest_path = DATASET_ROOT / "splits" / "stage6m_cohort3_final_manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    mf = json.load(f)
records = mf.get("records", [])

eval_ids = {r["recording_id"] for r in records if r.get("panel_role") == "evaluation"}
gate_ids = {r["recording_id"] for r in records if r.get("panel_role") == "gate_reference"}
reserve_ids = {r["recording_id"] for r in records if r.get("panel_role") == "australian_reserve"}

print(f"Manifest Records: {len(records):,} total (16,500 eval, 1,500 gate, 975 reserve)")
assert len(eval_ids) == 16500, f"Eval ID count mismatch: {len(eval_ids)}"
assert len(gate_ids) == 1500, f"Gate ID count mismatch: {len(gate_ids)}"
assert len(reserve_ids) == 975, f"Reserve ID count mismatch: {len(reserve_ids)}"

mounted_stems = {f.stem for f in audio_files}
assert len(mounted_stems & eval_ids) == 16500, "FATAL: Evaluation audio missing from mounted payload!"
assert len(mounted_stems & gate_ids) == 1500, "FATAL: Gate-reference audio missing from mounted payload!"
reserve_overlap = mounted_stems & reserve_ids
print(f"Mounted Reserve Recordings Overlap: {len(reserve_overlap)} (Expected: 0)")
assert len(reserve_overlap) == 0, f"FATAL SECURITY BREACH: {len(reserve_overlap)} reserve clips in payload!"
print("STEP 2 VERIFIED: 16,500 eval + 1,500 gate present; exactly 0 reserve recordings.")
"""

cell_3_code = """# ==============================================================================
# STEP 3: VERIFY TRANSCRIPT ISOLATION & ZERO LABEL EXPOSURE
# ==============================================================================
print("=" * 80)
print("STAGE 6M GATE 5: STEP 3 - TRANSCRIPT ISOLATION AUDIT")
print("=" * 80)

# Check online inference manifest
online_path = DATASET_ROOT / "splits" / "stage6m_cohort3_online_inference_manifest.json"
assert online_path.exists(), f"FATAL: Missing online manifest at {online_path}"
with open(online_path, "r", encoding="utf-8") as f:
    online_mf = json.load(f)

online_records = online_mf.get("records", [])
eval_online = [r for r in online_records if r.get("panel_role") == "evaluation"]
print(f"Online Manifest Evaluation Records: {len(eval_online):,}")
assert len(eval_online) == 16500, f"Online eval record count mismatch: {len(eval_online)}"

exposed_transcripts = [r for r in eval_online if r.get("transcript") is not None and r.get("transcript") != ""]
print(f"Exposed Evaluation Transcripts in Online Manifest: {len(exposed_transcripts)}")
assert len(exposed_transcripts) == 0, f"FATAL BREACH: {len(exposed_transcripts)} evaluation transcripts exposed!"

# Search entire input and working trees for sealed transcript key
print("Scanning file system for unauthorized sealed transcript key...")
sealed_key_filename = "stage6m_cohort3_sealed_evaluation_transcripts.json"
search_roots = [Path("/kaggle/input"), Path("/kaggle/working")]
found_sealed = []
for sroot in search_roots:
    if sroot.exists():
        for r, _, files in os.walk(sroot):
            if sealed_key_filename in files:
                found_sealed.append(os.path.join(r, sealed_key_filename))

print(f"Sealed Transcript Key Locations Found: {len(found_sealed)}")
assert len(found_sealed) == 0, f"FATAL BREACH: Sealed key detected on Kaggle node at: {found_sealed}"
print("STEP 3 VERIFIED: 100% transcript shielding confirmed; zero sealed keys present.")
"""

cell_4_code = """# ==============================================================================
# STEP 4: VERIFY EXECUTION ENVIRONMENT (NVIDIA TESLA T4 x2)
# ==============================================================================
import torch, platform

print("=" * 80)
print("STAGE 6M GATE 5: STEP 4 - HARDWARE ACCELERATOR & ENVIRONMENT AUDIT")
print("=" * 80)

py_ver = platform.python_version()
torch_ver = torch.__version__
cuda_ver = getattr(torch.version, "cuda", "N/A")
print(f"Python Version:   {py_ver}")
print(f"PyTorch Version:  {torch_ver}")
print(f"CUDA Version:     {cuda_ver}")
print(f"CUDA Available:   {torch.cuda.is_available()}")

assert torch.cuda.is_available(), "FATAL: CUDA accelerator not available!"
dev_count = torch.cuda.device_count()
print(f"Device Count:     {dev_count} (Expected: 2 for T4 x2 topology)")
assert dev_count == 2, f"FATAL: Device count {dev_count} != 2 (Approved T4 x2 required)"

gpu_records = []
for i in range(dev_count):
    name = torch.cuda.get_device_name(i)
    total_mem_gb = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)
    print(f"  GPU {i}: {name} ({total_mem_gb:.2f} GB VRAM)")
    assert "Tesla T4" in name or "T4" in name, f"FATAL: GPU {i} model {name} is not Tesla T4!"
    assert total_mem_gb >= 14.0, f"FATAL: GPU {i} VRAM {total_mem_gb:.2f} GB < 14.0 GB!"
    gpu_records.append({"device": i, "model": name, "vram_gb": round(total_mem_gb, 2)})

print("STEP 4 VERIFIED: NVIDIA Tesla T4 x2 dual topology confirmed.")
"""

cell_5_code = """# ==============================================================================
# STEP 5: VERIFY FROZEN EXECUTION IDENTITY & CRYPTOGRAPHIC MATRIX
# ==============================================================================
print("=" * 80)
print("STAGE 6M GATE 5: STEP 5 - FROZEN EXECUTION ARTIFACT HASH AUDIT")
print("=" * 80)

EXPECTED_HASHES = {
    "online_manifest": "0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1",
    "final_manifest": "171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0",
    "ledger": "b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5",
    "catalogue": "e7187136c5004623f1f3044eb60587efbd201f4c9006bb081d91a94efa8ebaf8",
    "runner": "728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1",
    "notebook": "c5628b62918ca65772d7ca21045793ae65e674a9cd4c248d70592cf3427d2b14"
}

def get_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

online_mf_path = DATASET_ROOT / "splits" / "stage6m_cohort3_online_inference_manifest.json"
final_mf_path = DATASET_ROOT / "splits" / "stage6m_cohort3_final_manifest.json"
ledger_path = DATASET_ROOT / "splits" / "stage6m_cohort3_materialization_disposition_ledger.csv"
cat_path = DATASET_ROOT / "SHA256_CATALOGUE.json"
runner_path = Path("/kaggle/working/runner/run_stage6m_cohort3_kaggle_benchmark.py")
if not runner_path.exists():
    runner_path = Path("runner/run_stage6m_cohort3_kaggle_benchmark.py")

h_online = get_sha256(online_mf_path)
h_final = get_sha256(final_mf_path)
h_ledger = get_sha256(ledger_path)
h_cat = get_sha256(cat_path)

print(f"Online Manifest SHA256: {h_online} [{'PASS' if h_online == EXPECTED_HASHES['online_manifest'] else 'FAIL'}]")
print(f"Final Manifest SHA256:  {h_final} [{'PASS' if h_final == EXPECTED_HASHES['final_manifest'] else 'FAIL'}]")
print(f"Ledger CSV SHA256:      {h_ledger} [{'PASS' if h_ledger == EXPECTED_HASHES['ledger'] else 'FAIL'}]")
print(f"Catalogue SHA256:       {h_cat} [{'PASS' if h_cat == EXPECTED_HASHES['catalogue'] else 'FAIL'}]")

assert h_online == EXPECTED_HASHES["online_manifest"], "Online manifest hash mismatch!"
assert h_final == EXPECTED_HASHES["final_manifest"], "Final manifest hash mismatch!"
assert h_ledger == EXPECTED_HASHES["ledger"], "Ledger hash mismatch!"
assert h_cat == EXPECTED_HASHES["catalogue"], "Catalogue hash mismatch!"

if runner_path.exists():
    h_runner = get_sha256(runner_path)
    print(f"Audited Runner SHA256:  {h_runner} [{'PASS' if h_runner == EXPECTED_HASHES['runner'] else 'FAIL'}]")
    assert h_runner == EXPECTED_HASHES["runner"], "Runner hash mismatch!"

print("STEP 5 VERIFIED: Frozen cryptographic identity matrix authenticated.")
"""

cell_6_code = """# ==============================================================================
# STEP 6: COMPILE MACHINE-READABLE AUDIT EVIDENCE & FINAL VERDICT
# ==============================================================================
from datetime import datetime, timezone

audit_result = {
    "report_id": "STAGE6M-GATE5-KAGGLE-MOUNT-AUDIT-20261108",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "governing_protocol": "Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)",
    "governing_authorization": "STAGE6M-GATE5-AUTH-DECISION-20261108",
    "dataset_source": "venkataakhil07/stage6m-frozen-benchmark",
    "verdict": "RUNTIME_PREFLIGHT_PASSED",
    "step1_mount": {
        "status": "PASSED",
        "root": str(DATASET_ROOT),
        "top_level_items": top_level_items,
        "is_audio_extracted": is_audio_extracted
    },
    "step2_audio": {
        "status": "PASSED",
        "audio_files_count": audio_count,
        "audio_bytes": total_bytes,
        "catalogue_matches": len(audio_cat),
        "catalogue_mismatches": 0,
        "eval_recordings_count": len(eval_ids),
        "gate_recordings_count": len(gate_ids),
        "reserve_recordings_count": 0
    },
    "step3_transcripts": {
        "status": "PASSED",
        "eval_transcripts_shielded": True,
        "sealed_key_present": False
    },
    "step4_hardware": {
        "status": "PASSED",
        "python_version": py_ver,
        "pytorch_version": torch_ver,
        "cuda_version": cuda_ver,
        "device_count": dev_count,
        "gpus": gpu_records
    },
    "step5_cryptographic_hashes": {
        "status": "PASSED",
        "online_manifest_sha256": h_online,
        "final_manifest_sha256": h_final,
        "ledger_sha256": h_ledger,
        "catalogue_sha256": h_cat
    }
}

out_path = Path("/kaggle/working/stage6m_gate5_runtime_mount_audit.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(audit_result, f, indent=2)

print("=" * 80)
print(f"FINAL RUNTIME PREFLIGHT VERDICT: {audit_result['verdict']}")
print(f"Evidence written to: {out_path} ({out_path.stat().st_size:,} bytes)")
print("=" * 80)
"""

def make_cell(cell_type: str, source: str) -> dict:
    return {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }

notebook = {
    "cells": [
        make_cell("markdown", cell_0_md),
        make_cell("code", cell_1_code),
        make_cell("code", cell_2_code),
        make_cell("code", cell_3_code),
        make_cell("code", cell_4_code),
        make_cell("code", cell_5_code),
        make_cell("code", cell_6_code)
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(KERNEL_DIR / "run_gate5_runtime_mount_audit.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print(f"Successfully constructed kernel at: {KERNEL_DIR}")
print(f"Files: {os.listdir(KERNEL_DIR)}")
