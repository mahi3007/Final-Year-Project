#!/usr/bin/env python3
"""
scripts/deploy_stage6m_kaggle_dataset.py

Stage 6M Gate 5 Phase 2: Live Kaggle Private Dataset Deployment
==============================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
Dataset ID:         venkataakhil07/stage6m-frozen-benchmark (Private)
Payload Directory:  dist/kaggle_dataset
Audio Allowlist:    Exactly 18,000 files (16,500 eval + 1,500 gate-reference)
Reserve Clips:      0 files in payload (100% physically excluded)
"""

from __future__ import annotations

import glob
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi, ResumableUploadContext
from kagglesdk.blobs.types.blob_api_service import ApiBlobType
from kagglesdk.datasets.types.dataset_api_service import (
    ApiCreateDatasetRequest,
    ApiDatasetNewFile,
    ApiGetDatasetStatusRequest,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAYLOAD_DIR = PROJECT_ROOT / "dist" / "kaggle_dataset"
LOG_FILE = PROJECT_ROOT / "reports" / "stage6m" / "kaggle_deployment_live.log"

EXPECTED_CATALOGUE_SHA256 = "e7187136c5004623f1f3044eb60587efbd201f4c9006bb081d91a94efa8ebaf8"
EXPECTED_AUDIO_COUNT = 18000
EXPECTED_AUDIO_BYTES = 672970785
EXPECTED_ONLINE_SHA256 = "0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1"


def log(msg: str) -> None:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now_iso}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_payload_invariants() -> None:
    log("=" * 80)
    log("STAGE 6M GATE 5: PRE-DEPLOYMENT PAYLOAD INVARIANT VERIFICATION")
    log("=" * 80)

    # 1. Verify catalogue existence and hash
    cat_path = PAYLOAD_DIR / "SHA256_CATALOGUE.json"
    if not cat_path.exists():
        raise RuntimeError(f"FATAL: Missing catalogue at {cat_path}")
    cat_sha = sha256_file(cat_path)
    log(f"Catalogue SHA-256: {cat_sha}")
    if cat_sha != EXPECTED_CATALOGUE_SHA256:
        raise RuntimeError(f"FATAL: Catalogue SHA mismatch: got {cat_sha}, expected {EXPECTED_CATALOGUE_SHA256}")
    log("[PASS] Catalogue SHA-256 matches expected frozen digest.")

    # 2. Verify audio files count and bytes
    audio_dir = PAYLOAD_DIR / "audio" / "cohort3_reconciled_assets"
    audio_files = list(audio_dir.glob("*.mp3"))
    audio_count = len(audio_files)
    audio_bytes = sum(f.stat().st_size for f in audio_files)
    log(f"Audio files count: {audio_count:,} (Expected: {EXPECTED_AUDIO_COUNT:,})")
    log(f"Audio byte sum:   {audio_bytes:,} (Expected: {EXPECTED_AUDIO_BYTES:,})")
    if audio_count != EXPECTED_AUDIO_COUNT:
        raise RuntimeError(f"FATAL: Audio count mismatch: {audio_count}")
    if audio_bytes != EXPECTED_AUDIO_BYTES:
        raise RuntimeError(f"FATAL: Audio byte sum mismatch: {audio_bytes}")
    log("[PASS] Audio payload exactness verified: 18,000 files, 672,970,785 bytes.")

    # 3. Verify zero reserve audio clips
    reserve_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_final_manifest.json"
    with open(reserve_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    records = manifest_data.get("records", [])
    reserve_ids = {
        item["recording_id"] for item in records
        if item.get("panel_role") == "australian_reserve"
    }
    log(f"Identified reserve sample IDs in final manifest: {len(reserve_ids):,}")
    leakage = [f.stem for f in audio_files if f.stem in reserve_ids]
    if leakage:
        raise RuntimeError(f"FATAL: {len(leakage)} reserve recordings found in payload! Breach detected: {leakage[:5]}")
    log("[PASS] Zero reserve recordings present in payload (100% disjoint).")

    # 4. Verify online inference manifest
    online_mf = PAYLOAD_DIR / "splits" / "stage6m_cohort3_online_inference_manifest.json"
    online_sha = sha256_file(online_mf)
    log(f"Online inference manifest SHA-256: {online_sha}")
    if online_sha != EXPECTED_ONLINE_SHA256:
        raise RuntimeError(f"FATAL: Online manifest SHA mismatch: got {online_sha}, expected {EXPECTED_ONLINE_SHA256}")
    log("[PASS] Online inference manifest verified.")

    # 5. Verify sealed transcripts key is NOT present
    sealed_path = PAYLOAD_DIR / "splits" / "stage6m_cohort3_sealed_evaluation_transcripts.json"
    if sealed_path.exists():
        raise RuntimeError("FATAL: Sealed evaluation transcript key found in payload!")
    log("[PASS] Sealed transcript key strictly excluded.")


def get_cached_token(filename_pattern: str) -> Optional[str]:
    temp_dir = os.path.join(tempfile.gettempdir(), ".kaggle", "uploads")
    if not os.path.exists(temp_dir):
        return None
    for f in os.listdir(temp_dir):
        if filename_pattern in f and f.endswith(".json"):
            try:
                with open(os.path.join(temp_dir, f), "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                if data.get("upload_complete") and "start_blob_upload_response" in data:
                    token = data["start_blob_upload_response"].get("token")
                    if token:
                        log(f"Found cached upload token for {filename_pattern}: {token[:24]}...")
                        return token
            except Exception as e:
                log(f"Warning reading cached upload info {f}: {e}")
    return None


def zip_and_upload_dir(api: KaggleApi, dir_path: Path, archive_name: str, ctx: ResumableUploadContext) -> str:
    log(f"Archiving {dir_path.name} to {archive_name}...")
    temp_dir = tempfile.mkdtemp()
    try:
        base_name = os.path.join(temp_dir, archive_name.replace(".zip", ""))
        archive_path = shutil.make_archive(base_name, "zip", str(dir_path))
        file_size = os.path.getsize(archive_path)
        log(f"Archive created: {archive_path} ({file_size:,} bytes). Uploading blob...")
        token = api._upload_blob(archive_path, False, ApiBlobType.DATASET, ctx)
        if not token:
            raise RuntimeError(f"Failed to upload {archive_name}")
        log(f"Uploaded {archive_name} successfully. Token: {token[:24]}...")
        return token
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def upload_single_file(api: KaggleApi, file_path: Path, ctx: ResumableUploadContext) -> str:
    file_size = os.path.getsize(str(file_path))
    log(f"Uploading file {file_path.name} ({file_size:,} bytes)...")
    token = api._upload_blob(str(file_path), False, ApiBlobType.DATASET, ctx)
    if not token:
        raise RuntimeError(f"Failed to upload {file_path.name}")
    log(f"Uploaded {file_path.name} successfully. Token: {token[:24]}...")
    return token


def deploy_dataset() -> None:
    verify_payload_invariants()

    log("=" * 80)
    log("STAGE 6M GATE 5: INITIALIZING KAGGLE CLIENT & AUTHENTICATION")
    log("=" * 80)

    api = KaggleApi()
    api.authenticate()
    user = api.config_values[api.CONFIG_NAME_USER]
    log(f"Authenticated as Kaggle user: {user}")

    # Check if dataset already exists
    dataset_ref = "venkataakhil07/stage6m-frozen-benchmark"
    try:
        current_status = api.dataset_status(dataset_ref)
        log(f"Dataset {dataset_ref} already exists on Kaggle. Current status: {current_status}")
        if current_status == "ready":
            log("[SUCCESS] Dataset is already uploaded and READY.")
            return
    except Exception as e:
        log(f"Dataset {dataset_ref} not yet created on Kaggle ({e}). Proceeding with initial creation.")

    # Read dataset metadata
    with open(PAYLOAD_DIR / "dataset-metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    title = meta["title"]
    ref = meta["id"]
    owner_slug, dataset_slug = ref.split("/")
    license_name = meta["licenses"][0]["name"]
    description = meta.get("description", "")

    # Gather upload tokens
    files_tokens: Dict[str, str] = {}

    with ResumableUploadContext() as ctx:
        # Check audio token
        audio_token = get_cached_token("audio.zip")
        if audio_token:
            files_tokens["audio.zip"] = audio_token
        else:
            log("No cached audio.zip token found. Zipping and uploading audio directory (18,000 files)...")
            files_tokens["audio.zip"] = zip_and_upload_dir(
                api, PAYLOAD_DIR / "audio", "audio.zip", ctx
            )

        # Check configs token
        configs_token = get_cached_token("configs.zip")
        if configs_token:
            files_tokens["configs.zip"] = configs_token
        else:
            log("Zipping and uploading configs directory...")
            files_tokens["configs.zip"] = zip_and_upload_dir(
                api, PAYLOAD_DIR / "configs", "configs.zip", ctx
            )

        # Splits
        log("Zipping and uploading splits directory...")
        files_tokens["splits.zip"] = zip_and_upload_dir(
            api, PAYLOAD_DIR / "splits", "splits.zip", ctx
        )

        # Src
        log("Zipping and uploading src directory...")
        files_tokens["src.zip"] = zip_and_upload_dir(
            api, PAYLOAD_DIR / "src", "src.zip", ctx
        )

        # Requirements
        req_path = PAYLOAD_DIR / "requirements-kaggle-lock.txt"
        files_tokens["requirements-kaggle-lock.txt"] = upload_single_file(api, req_path, ctx)

        # Catalogue
        cat_path = PAYLOAD_DIR / "SHA256_CATALOGUE.json"
        files_tokens["SHA256_CATALOGUE.json"] = upload_single_file(api, cat_path, ctx)

        # Attempt to create dataset
        log("=" * 80)
        log("STAGE 6M GATE 5: SUBMITTING CREATE DATASET REQUEST TO KAGGLE")
        log("=" * 80)
        log(f"Dataset Title:    {title}")
        log(f"Dataset Slug:     {owner_slug}/{dataset_slug}")
        log(f"License:          {license_name}")
        log(f"Visibility:       PRIVATE (is_private=True)")
        log(f"Attached Files:   {len(files_tokens)} items")
        for fname, tok in files_tokens.items():
            log(f"  - {fname}: token={tok[:20]}...")

        request = ApiCreateDatasetRequest()
        request.title = title
        request.slug = dataset_slug
        request.owner_slug = owner_slug
        request.license_name = license_name
        request.description = description
        request.is_private = True
        request.category_ids = []

        file_objs = []
        for fname, tok in files_tokens.items():
            f_obj = ApiDatasetNewFile()
            f_obj.token = tok
            file_objs.append(f_obj)
        request.files = file_objs

        def submit_create(req: ApiCreateDatasetRequest) -> bool:
            with api.build_kaggle_client() as client:
                try:
                    resp = client.datasets.dataset_api_client.create_dataset(req)
                    log(f"Kaggle API create_dataset response: {resp}")
                    return True
                except Exception as ex:
                    log(f"ERROR from Kaggle create_dataset API: {ex}")
                    return False

        success = submit_create(request)
        if not success:
            log("[WARNING] Initial submission failed (possibly stale cached audio token). Re-zipping and re-uploading audio...")
            files_tokens["audio.zip"] = zip_and_upload_dir(
                api, PAYLOAD_DIR / "audio", "audio.zip", ctx
            )
            file_objs = []
            for fname, tok in files_tokens.items():
                f_obj = ApiDatasetNewFile()
                f_obj.token = tok
                file_objs.append(f_obj)
            request.files = file_objs
            log("Retrying create_dataset with fresh audio.zip...")
            retry_success = submit_create(request)
            if not retry_success:
                raise RuntimeError("FATAL: Kaggle create_dataset API failed on retry.")

    # Poll status until ready
    log("=" * 80)
    log("STAGE 6M GATE 5: MONITORING DATASET STATUS UNTIL READY")
    log("=" * 80)
    max_wait_seconds = 1800  # 30 minutes
    poll_interval = 10
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            status = api.dataset_status(dataset_ref)
            elapsed = int(time.time() - start_time)
            log(f"[{elapsed}s] Dataset status: {status}")
            if status == "ready":
                log("=" * 80)
                log(f"[SUCCESS] Dataset {dataset_ref} is READY on Kaggle!")
                log(f"Kaggle Dataset URL: https://www.kaggle.com/datasets/{dataset_ref}")
                log("=" * 80)
                return
            elif status == "error":
                raise RuntimeError(f"FATAL: Kaggle dataset processing ended in 'error' state.")
        except Exception as e:
            log(f"Status check exception: {e}")
        time.sleep(poll_interval)

    raise TimeoutError(f"Dataset status did not reach 'ready' within {max_wait_seconds} seconds.")


if __name__ == "__main__":
    try:
        deploy_dataset()
    except Exception as exc:
        log(f"CRITICAL ERROR: {exc}")
        sys.exit(1)
