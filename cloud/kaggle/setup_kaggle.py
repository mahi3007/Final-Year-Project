#!/usr/bin/env python3
"""
Stage 6 Cloud Execution: Kaggle & Colab Automated Setup Script.
==============================================================
Prepares the free virtual GPU environment (NVIDIA Tesla P100 / T4):
1. Verifies GPU visibility and VRAM.
2. Installs required python dependencies (transformers, soundfile, editdistance, etc.).
3. Unpacks audio assets (if provided as an archive) or validates local datasets.
4. Executes Stage 6 GPU preflight to ensure 100% integrity before starting computation.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def install_dependencies():
    print("=" * 75)
    print("STEP 1: INSTALLING / VERIFYING PYTHON DEPENDENCIES")
    print("=" * 75)
    packages = [
        "transformers>=4.30.0",
        "soundfile>=0.12.1",
        "librosa>=0.10.0",
        "editdistance>=0.6.2",
        "statsmodels>=0.14.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
    ]
    cmd = [sys.executable, "-m", "pip", "install", "-q"] + packages
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("Dependencies successfully installed / verified.")


def check_gpu():
    print("\n" + "=" * 75)
    print("STEP 2: HARDWARE ACCELERATOR CHECK")
    print("=" * 75)
    import torch
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_avail}")
    if cuda_avail:
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"GPU Accelerator : {name}")
        print(f"Total VRAM      : {vram:.2f} GB")
        if "P100" in name or "T4" in name or vram >= 14.0:
            print("GPU Assessment  : EXCELLENT (Tesla P100 / T4 confirmed, 16GB VRAM)")
        else:
            print(f"GPU Assessment  : Supported ({name})")
    else:
        print("WARNING: No GPU detected! Kaggle session: Settings -> Accelerator -> GPU (Tesla P100)")


def unpack_audio_bundle_if_present():
    print("\n" + "=" * 75)
    print("STEP 3: AUDIO DATASET VERIFICATION & EXTRACTION")
    print("=" * 75)
    audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
    sentinel_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"

    eval_clips = list(audio_dir.glob("*.mp3")) if audio_dir.exists() else []
    sent_clips = list(sentinel_dir.glob("*.mp3")) if sentinel_dir.exists() else []

    if len(eval_clips) >= 900 and len(sent_clips) >= 300:
        print(f"Verified {len(eval_clips)} external eval clips and {len(sent_clips)} sentinel clips present on disk.")
        return

    print(f"Audio clips incomplete on disk: eval={len(eval_clips)}/900, sentinel={len(sent_clips)}/300.")
    print("Searching for stage6_audio_bundle archive...")

    candidate_paths = [
        PROJECT_ROOT / "stage6_audio_bundle.tar.gz",
        PROJECT_ROOT / "stage6_audio_bundle.zip",
        PROJECT_ROOT.parent / "stage6_audio_bundle.tar.gz",
        Path("/kaggle/working/stage6_audio_bundle.tar.gz"),
        Path("/kaggle/working/project/stage6_audio_bundle.tar.gz"),
    ]

    # Search /kaggle/input/ recursively for Kaggle Dataset uploads
    kaggle_input = Path("/kaggle/input")
    if kaggle_input.exists():
        for p in kaggle_input.glob("**/*audio*bundle*.*"):
            candidate_paths.append(p)
        for p in kaggle_input.glob("**/*.tar.gz"):
            candidate_paths.append(p)

    archive_found = None
    for p in candidate_paths:
        if p.exists() and p.is_file():
            archive_found = p
            break

    if archive_found:
        print(f"Found archive: {archive_found} ({archive_found.stat().st_size / (1024*1024):.2f} MB)")
        print(f"Extracting into {PROJECT_ROOT}...")
        if str(archive_found).endswith(".tar.gz") or str(archive_found).endswith(".tgz"):
            with tarfile.open(archive_found, "r:gz") as tar:
                tar.extractall(path=PROJECT_ROOT)
        elif str(archive_found).endswith(".zip"):
            with zipfile.ZipFile(archive_found, "r") as zf:
                zf.extractall(path=PROJECT_ROOT)
        print("Extraction complete.")
    else:
        print("\nERROR: stage6_audio_bundle.tar.gz not found!")
        print("To provide the required 40MB audio bundle on Kaggle, use one of these two options:")
        print("  Option 1 (Git): Commit and push stage6_audio_bundle.tar.gz to your GitHub repo, then run `!git pull` in Kaggle.")
        print("  Option 2 (Kaggle Dataset): Click '+ Add Input' in the right sidebar of Kaggle -> Upload `stage6_audio_bundle.tar.gz` from your local machine.")
        raise FileNotFoundError("Missing stage6_audio_bundle.tar.gz (40.39 MB audio archive required).")

    # Verify post-extraction
    eval_clips = list(audio_dir.glob("*.mp3")) if audio_dir.exists() else []
    sent_clips = list(sentinel_dir.glob("*.mp3")) if sentinel_dir.exists() else []
    print(f"Post-extraction verification: eval={len(eval_clips)}/900, sentinel={len(sent_clips)}/300.")
    assert len(eval_clips) >= 900, f"Extraction failed: only found {len(eval_clips)}/900 eval clips!"
    assert len(sent_clips) >= 300, f"Extraction failed: only found {len(sent_clips)}/300 sentinel clips!"


def run_preflight_check():
    print("\n" + "=" * 75)
    print("STEP 4: RUNNING STAGE 6 PREFLIGHT INTEGRITY AUDIT")
    print("=" * 75)
    preflight_script = PROJECT_ROOT / "scripts" / "stage6" / "00_gpu_preflight.py"
    subprocess.check_call([sys.executable, str(preflight_script)])


if __name__ == "__main__":
    install_dependencies()
    check_gpu()
    unpack_audio_bundle_if_present()
    run_preflight_check()
    print("\n" + "=" * 75)
    print("KAGGLE SETUP COMPLETE. READY TO RUN BENCHMARK.")
    print("Run command: python cloud/kaggle/run_six_model_benchmark.py")
    print("=" * 75)
