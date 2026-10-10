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
