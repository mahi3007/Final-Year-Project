#!/usr/bin/env python3
"""
Master Cloud Runner: Stage 5M & Stage 6 Benchmark Suite
========================================================
Single unified execution engine for running Stage 5M (Closed-Loop Online Control)
and Stage 6 (Cross-Architecture Generalization Benchmark) on free virtual GPUs (Tesla P100 / T4).

Usage:
  python cloud/kaggle/run_stage5_and_stage6.py --stage 5m
  python cloud/kaggle/run_stage5_and_stage6.py --stage 6
  python cloud/kaggle/run_stage5_and_stage6.py --stage 6.1
  python cloud/kaggle/run_stage5_and_stage6.py --stage all
"""

from __future__ import annotations

import argparse
import gc
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


def purge_gpu_memory():
    """Aggressively purges GPU VRAM between stages."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()


def run_stage_5m(device: str, smoke_test: bool = False):
    print("\n" + "#" * 80)
    print("### EXECUTING STAGE 5M: CLOSED-LOOP ONLINE CONTROL SUITE ###")
    print("#" * 80)
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_stage5m_online_control.py"),
        "--device", device,
    ]
    if smoke_test:
        cmd.append("--smoke-test")
    subprocess.check_call(cmd)
    purge_gpu_memory()


def run_stage_5d():
    print("\n" + "#" * 80)
    print("### EXECUTING STAGE 5D: COMMON VOICE 27.0 DSG RE-EXECUTION ###")
    print("#" * 80)
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_stage5d_dsg_reexecution.py"),
    ]
    subprocess.check_call(cmd)
    purge_gpu_memory()


def run_stage_6():
    print("\n" + "#" * 80)
    print("### EXECUTING STAGE 6: SIX-MODEL DSG GENERALIZATION BENCHMARK ###")
    print("#" * 80)
    cmd = [
        sys.executable,
        str(CLOUD_DIR / "run_six_model_benchmark.py"),
    ]
    subprocess.check_call(cmd)
    purge_gpu_memory()


def run_stage_6_1():
    print("\n" + "#" * 80)
    print("### EXECUTING STAGE 6.1: TWO-MODEL LARGE CTC EXTENSION ###")
    print("#" * 80)
    cmd = [
        sys.executable,
        str(CLOUD_DIR / "run_stage6_1_extension.py"),
    ]
    subprocess.check_call(cmd)
    purge_gpu_memory()


def main():
    parser = argparse.ArgumentParser(description="Master Stage 5 & 6 Cloud Benchmark Runner")
    parser.add_argument(
        "--stage",
        choices=["5m", "5d", "6", "6.1", "all"],
        default="all",
        help="Stage to execute ('5m', '5d', '6', '6.1', or 'all')"
    )
    parser.add_argument("--smoke-test", action="store_true", help="Run fast 1-cell smoke test for Stage 5M")
    parser.add_argument("--device", default=None, help="Hardware device ('cuda' or 'cpu')")
    args = parser.parse_args()

    t_start = time.time()
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 80)
    print("MASTER STAGE 5 & STAGE 6 BENCHMARK SUITE (KAGGLE / COLAB)")
    print("=" * 80)
    print(f"Target Stage    : {args.stage.upper()}")
    print(f"Compute Device  : {device}")
    if device == "cuda":
        print(f"GPU Model       : {torch.cuda.get_device_name(0)}")
        print(f"GPU VRAM        : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")

    if args.stage in ["5m", "all"]:
        run_stage_5m(device=device, smoke_test=args.smoke_test)

    if args.stage == "5d":
        run_stage_5d()

    if args.stage in ["6", "all"]:
        run_stage_6()

    if args.stage in ["6.1", "all"]:
        run_stage_6_1()

    # Package unified results
    print("\n" + "=" * 80)
    print("PACKAGING UNIFIED BENCHMARK RESULTS BUNDLE...")
    print("=" * 80)
    subprocess.check_call([sys.executable, str(CLOUD_DIR / "export_results.py")])

    t_total = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"ALL BENCHMARK TASKS COMPLETED SUCCESSFULLY in {t_total:.1f}s ({t_total/60:.2f} mins)")
    print("Output archive is ready at: /kaggle/working/stage5_stage6_results_bundle.zip")
    print("=" * 80)


if __name__ == "__main__":
    main()
