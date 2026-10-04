#!/usr/bin/env python3
"""
Stage 6 Cloud Execution: Master Virtual GPU Benchmark Runner.
=============================================================
Orchestrates the entire Stage 6 evaluation pipeline on Kaggle (Tesla P100) or Colab (T4):
1. Preflight integrity check (manifests, SHA-256 locks, 900+300 audio clips).
2. Model compatibility audit (CTC vs Seq2Seq).
3. Sequential prequential execution across all 6 models with GPU memory purging.
4. Output verification & invariant assertion (0 fail-closed errors, frozen baseline lock).
5. Synthesis & Comparative Analysis report generation.
6. Automatic export of results bundle to /kaggle/working/stage6_results_bundle.zip.
"""

from __future__ import annotations

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

SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "stage6"
CLOUD_DIR = PROJECT_ROOT / "cloud" / "kaggle"


def main():
    print("=" * 80)
    print("STAGE 6: MASTER CLOUD GPU BENCHMARK EXECUTION (KAGGLE / COLAB)")
    print("=" * 80)
    t_start = time.time()

    # Detect Accelerator (TPU or GPU)
    device = "cpu"
    accelerator_type = "CPU"
    try:
        import importlib
        if importlib.util.find_spec("torch_xla") is not None:
            xm = importlib.import_module("torch_xla.core.xla_model")
            device = str(xm.xla_device())
            accelerator_type = f"TPU ({device})"
    except Exception:
        pass

    if device == "cpu" and torch.cuda.is_available():
        device = "cuda"
        vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        accelerator_type = f"GPU ({torch.cuda.get_device_name(0)}, {vram:.2f} GB VRAM)"

    print(f"Accelerator Device: {device} [{accelerator_type}]")

    # Step 1: Preflight Verification
    print("\n>>> STEP 1/5: RUNNING PREFLIGHT INTEGRITY AUDIT...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "00_gpu_preflight.py")])

    # Step 2: Compatibility Manifest
    print("\n>>> STEP 2/5: AUDITING ARCHITECTURAL COMPATIBILITY...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "01_model_compatibility.py")])

    # Step 3: Run Sequential Cross-Model Benchmark
    print("\n>>> STEP 3/5: EXECUTING MULTI-MODEL PREQUENTIAL BENCHMARK...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "03_run_all_models.py"), "--device", device])

    # Step 4: Output Verification
    print("\n>>> STEP 4/5: VERIFYING OUTPUT INTEGRITY & INVARIANTS...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "04_verify_results.py")])

    # Step 5: Comparative Analysis Synthesis
    print("\n>>> STEP 5/5: SYNTHESIZING COMPARATIVE ANALYSIS REPORT...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "05_generate_comparison.py")])

    # Step 6: Package Results Bundle
    print("\n>>> PACKAGING RESULTS BUNDLE FOR LOCAL EXPORT...")
    subprocess.check_call([sys.executable, str(CLOUD_DIR / "export_results.py")])

    t_total = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"STAGE 6 CLOUD BENCHMARK COMPLETE! Total duration: {t_total:.1f}s ({t_total/60:.2f} mins)")
    print("=" * 80)


if __name__ == "__main__":
    main()
