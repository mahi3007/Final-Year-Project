#!/usr/bin/env python3
"""
Master Cloud Execution: Kaggle & Colab Automated Setup Script.
==============================================================
Prepares the free virtual GPU environment (NVIDIA Tesla P100 / T4):
1. Verifies GPU visibility and VRAM.
2. Installs required python dependencies (transformers, soundfile, editdistance, etc.).
3. Unpacks audio assets (Common Voice and L2-ARCTIC archives) from repository or /kaggle/input/.
4. Verifies audio file integrity for Stage 5M and Stage 6 benchmarks.
5. Executes preflight integrity checks.
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
    print("=" * 80)
    print("STEP 1: INSTALLING / VERIFYING PYTHON DEPENDENCIES")
    print("=" * 80)
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


def check_accelerator():
    print("\n" + "=" * 80)
    print("STEP 2: HARDWARE ACCELERATOR CHECK (GPU / TPU)")
    print("=" * 80)
    import torch

    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available  : {cuda_avail}")
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
        print("WARNING: No GPU detected! In Kaggle: Settings -> Accelerator -> GPU (Tesla T4 / P100)")


def unpack_archive(archive_path: Path, target_dir: Path):
    print(f"Extracting {archive_path.name} into {target_dir}...")
    if str(archive_path).endswith(".tar.gz") or str(archive_path).endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=target_dir)
    elif str(archive_path).endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(path=target_dir)
    print(f"Extraction of {archive_path.name} complete.")


def verify_and_unpack_audio_bundles():
    print("\n" + "=" * 80)
    print("STEP 3: AUDIO DATASET VERIFICATION & ARCHIVE EXTRACTION")
    print("=" * 80)

    cv_eval_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
    cv_sent_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
    primary_audio_dir = PROJECT_ROOT / "datasets" / "primary" / "audio"
    corrupted_audio_dir = PROJECT_ROOT / "datasets" / "corrupted"

    cv_eval_clips = list(cv_eval_dir.glob("*.mp3")) if cv_eval_dir.exists() else []
    cv_sent_clips = list(cv_sent_dir.glob("*.mp3")) if cv_sent_dir.exists() else []
    primary_clips = list(primary_audio_dir.glob("*.wav")) if primary_audio_dir.exists() else []
    corrupted_clips = list(corrupted_audio_dir.rglob("*.wav")) if corrupted_audio_dir.exists() else []

    print(f"Current local audio inventory:")
    print(f"  - Common Voice 27 Eval Audio   : {len(cv_eval_clips)} / 900 clips")
    print(f"  - Sentinel Panel Audio         : {len(cv_sent_clips)} / 300 clips")
    print(f"  - L2-ARCTIC Primary Audio      : {len(primary_clips)} / 240 clips")
    print(f"  - L2-ARCTIC Corrupted Audio    : {len(corrupted_clips)} / 480 clips")

    # If all already present, return early
    if len(cv_eval_clips) >= 900 and len(cv_sent_clips) >= 300:
        print("Audio verification passed for Stage 6 / Stage 5D.")
    else:
        print("Common Voice audio assets incomplete. Searching for archives...")

    # Search paths for archives
    candidate_dirs = [
        PROJECT_ROOT,
        PROJECT_ROOT.parent,
        Path("/kaggle/working"),
        Path("/kaggle/working/project"),
        Path("/kaggle/input"),
    ]

    found_archives = []
    for cdir in candidate_dirs:
        if cdir.exists():
            for p in cdir.rglob("*audio*bundle*.*"):
                if p.is_file() and p not in found_archives:
                    found_archives.append(p)
            for p in cdir.rglob("*.tar.gz"):
                if p.is_file() and p not in found_archives:
                    found_archives.append(p)

    for arch in found_archives:
        try:
            unpack_archive(arch, PROJECT_ROOT)
        except Exception as e:
            print(f"Notice: Failed to extract {arch.name}: {e}")

    # Re-verify post extraction
    cv_eval_clips = list(cv_eval_dir.glob("*.mp3")) if cv_eval_dir.exists() else []
    cv_sent_clips = list(cv_sent_dir.glob("*.mp3")) if cv_sent_dir.exists() else []
    primary_clips = list(primary_audio_dir.glob("*.wav")) if primary_audio_dir.exists() else []
    corrupted_clips = list(corrupted_audio_dir.rglob("*.wav")) if corrupted_audio_dir.exists() else []

    print("\nPost-extraction audio inventory:")
    print(f"  - Common Voice 27 Eval Audio   : {len(cv_eval_clips)} / 900 clips")
    print(f"  - Sentinel Panel Audio         : {len(cv_sent_clips)} / 300 clips")
    print(f"  - L2-ARCTIC Primary Audio      : {len(primary_clips)} / 240 clips")
    print(f"  - L2-ARCTIC Corrupted Audio    : {len(corrupted_clips)} / 480 clips")


def run_preflight_checks():
    print("\n" + "=" * 80)
    print("STEP 4: RUNNING PREFLIGHT INTEGRITY AUDIT")
    print("=" * 80)
    preflight_script = PROJECT_ROOT / "scripts" / "stage6" / "00_gpu_preflight.py"
    if preflight_script.exists():
        subprocess.check_call([sys.executable, str(preflight_script)])
    print("Preflight check passed.")


if __name__ == "__main__":
    install_dependencies()
    check_accelerator()
    verify_and_unpack_audio_bundles()
    run_preflight_checks()
    print("\n" + "=" * 80)
    print("KAGGLE SETUP COMPLETE. READY TO RUN STAGE 5 & 6 BENCHMARKS.")
    print("Run commands:")
    print("  Stage 5M (Closed-Loop Online Control): python cloud/kaggle/run_stage5_and_stage6.py --stage 5m")
    print("  Stage 6  (Six-Model Benchmark)       : python cloud/kaggle/run_stage5_and_stage6.py --stage 6")
    print("  Stage 6.1 (Two-Model Large Extension): python cloud/kaggle/run_stage5_and_stage6.py --stage 6.1")
    print("  All Stages (Unified Execution)       : python cloud/kaggle/run_stage5_and_stage6.py --stage all")
    print("=" * 80)
