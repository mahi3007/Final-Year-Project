#!/usr/bin/env python3
"""
Stage 5M Cloud Execution: Master Closed-Loop Online Control Runner
==================================================================
Orchestrates Stage 5M Closed-Loop Online Control on free virtual GPUs (Tesla P100 / T4):
1. Verifies hardware accelerator and audio assets.
2. Executes prequential closed-loop adaptation across preregistered CTC models.
3. Decides candidate updates via operational Sentinel Panel (N=30) under frozen DSG thresholds.
4. Quarantines test-stream labels during online adaptation.
5. Scores agreement/disagreement against retrospective ground truth.
6. Packages Stage 5M artifacts for download.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
import torch

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CLOUD_DIR = PROJECT_ROOT / "cloud" / "kaggle"


def ensure_audio_ready(project_root: Path):
    sentinel_dir = project_root / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
    primary_dir = project_root / "datasets" / "primary" / "audio"
    has_sent = sentinel_dir.exists() and len(list(sentinel_dir.glob("*.mp3"))) >= 300
    has_prim = primary_dir.exists() and len(list(primary_dir.glob("*.wav"))) >= 240
    if has_sent and has_prim:
        return

    import shutil
    import tarfile

    print(">>> PRE-RUN CHECK: Resolving audio dataset assets (sentinel & primary)...")

    # Check parent dir
    parent_sent = project_root.parent / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
    if parent_sent.exists() and len(list(parent_sent.glob("*.mp3"))) >= 300 and not has_sent:
        print(f"Linking sentinel audio from {project_root.parent}...")
        sentinel_dir.mkdir(parents=True, exist_ok=True)
        for f in parent_sent.glob("*.mp3"):
            target_f = sentinel_dir / f.name
            if not target_f.exists():
                try:
                    os.symlink(f, target_f)
                except Exception:
                    shutil.copy2(f, target_f)
        has_sent = len(list(sentinel_dir.glob("*.mp3"))) >= 300

    parent_prim = project_root.parent / "datasets" / "primary" / "audio"
    if parent_prim.exists() and len(list(parent_prim.glob("*.wav"))) >= 240 and not has_prim:
        print(f"Linking primary audio from {project_root.parent}...")
        primary_dir.mkdir(parents=True, exist_ok=True)
        for f in parent_prim.glob("*.wav"):
            target_f = primary_dir / f.name
            if not target_f.exists():
                try:
                    os.symlink(f, target_f)
                except Exception:
                    shutil.copy2(f, target_f)
        has_prim = len(list(primary_dir.glob("*.wav"))) >= 240

    parent_corr = project_root.parent / "datasets" / "corrupted"
    target_corr = project_root / "datasets" / "corrupted"
    if parent_corr.exists() and not (target_corr.exists() and any(target_corr.iterdir())):
        target_corr.mkdir(parents=True, exist_ok=True)
        for sub in parent_corr.rglob("*.wav"):
            rel = sub.relative_to(parent_corr)
            dest = target_corr / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                try:
                    os.symlink(sub, dest)
                except Exception:
                    shutil.copy2(sub, dest)

    if has_sent and has_prim:
        print("Audio assets verified.")
        return

    # Search candidate locations for bundles
    candidate_roots = [
        project_root,
        project_root.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path("/kaggle/working"),
        Path("/kaggle/working/project"),
        Path("/kaggle/input"),
    ]
    seen = set()
    for root in candidate_roots:
        if not root.exists():
            continue
        candidates = (
            list(root.glob("*audio*bundle*.tar.gz"))
            + list(root.rglob("stage5m_audio_bundle.tar.gz"))
            + list(root.glob("*.tar.gz"))
        )
        for arch in candidates:
            if arch.is_file() and not arch.name.startswith("dateutil") and arch not in seen:
                seen.add(arch)
                print(f"Auto-extracting {arch.name} into {project_root}...")
                try:
                    with tarfile.open(arch, "r:gz") as tar:
                        tar.extractall(path=project_root)
                    print(f"Successfully unpacked {arch.name}.")
                except Exception as e:
                    print(f"Notice: Failed to extract {arch.name}: {e}")
                if sentinel_dir.exists() and len(list(sentinel_dir.glob("*.mp3"))) >= 300:
                    print("Audio assets verified.")
                    return


def main():
    parser = argparse.ArgumentParser(description="Run Stage 5M Online Control on Cloud GPU")
    parser.add_argument("--models", nargs="+", default=None, help="ASR model keys (e.g. wav2vec2_base data2vec_base)")
    parser.add_argument("--conditions", nargs="+", default=None, help="Acoustic conditions (e.g. clean noise_5db)")
    parser.add_argument("--methods", nargs="+", default=None, help="Adaptation methods (e.g. suta dsuta dmsuta)")
    parser.add_argument("--orders", nargs="+", default=None, help="Stream orders (e.g. ORDER_A)")
    parser.add_argument("--smoke-test", action="store_true", help="Run fast 1-cell smoke test")
    parser.add_argument("--device", default=None, help="Execution device (cuda or cpu)")
    args = parser.parse_args()

    print("=" * 80)
    print("STAGE 5M: CLOUD GPU CLOSED-LOOP ONLINE CONTROL (KAGGLE / COLAB)")
    print("=" * 80)

    # Ensure audio dataset is extracted and ready
    ensure_audio_ready(PROJECT_ROOT)

    device = args.device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Detected Device: {device}")
    if device == "cuda":
        print(f"GPU Hardware   : {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory     : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB VRAM")

    script_path = SCRIPTS_DIR / "run_stage5m_online_control.py"
    cmd = [sys.executable, str(script_path), "--device", device]

    if args.models:
        cmd += ["--models"] + args.models
    if args.conditions:
        cmd += ["--conditions"] + args.conditions
    if args.methods:
        cmd += ["--methods"] + args.methods
    if args.orders:
        cmd += ["--orders"] + args.orders
    if args.smoke_test:
        cmd += ["--smoke-test"]

    print(f"\nExecuting: {' '.join(cmd)}\n")
    subprocess.check_call(cmd)

    # Package results
    print("\n>>> PACKAGING RESULTS BUNDLE...")
    subprocess.check_call([sys.executable, str(CLOUD_DIR / "export_results.py")])
    print("\nStage 5M cloud execution complete!")


if __name__ == "__main__":
    main()
