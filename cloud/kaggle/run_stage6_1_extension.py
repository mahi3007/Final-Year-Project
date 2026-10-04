#!/usr/bin/env python3
"""
Stage 6.1: Cloud Virtual GPU Extension Runner (Kaggle / Colab).
==============================================================
Runs the two new CTC models:
1. facebook/wav2vec2-large-960h-lv60 (Wav2Vec2 Large, 315.5M params)
2. facebook/wav2vec2-large-robust-ft-libri-960h (Multi-Domain Robust, 315.5M params)

Steps:
1. Audio dataset & preflight verification.
2. Stage 6.1 compatibility audit (verifies AutoModelForCTC, logits, entropy, SUTA, DSUTA, DMSUTA, DSG shadow).
3. Sequential prequential evaluation across 225 windows for both models on GPU.
4. Output verification & invariant assertions.
5. Export results bundle to /kaggle/working/stage6_1_results_bundle.zip.
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
    print("STAGE 6.1: TWO-MODEL SCALE & ROBUSTNESS CTC EXTENSION (KAGGLE / COLAB)")
    print("=" * 80)
    t_start = time.time()

    # Detect Accelerator
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

    # Step 2: Stage 6.1 Preflight Compatibility Audit
    print("\n>>> STEP 2/5: AUDITING NEW CTC MODELS (AutoModelForCTC, SUTA, DSG Shadow)...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "06_stage6_1_preflight_audit.py")])

    # Step 3: Run Sequential Benchmark for the 2 Models
    print("\n>>> STEP 3/5: EXECUTING PREQUENTIAL BENCHMARK ON GPU...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "07_run_stage6_1.py"), "--device", device])

    # Step 4: Output Verification
    print("\n>>> STEP 4/5: VERIFYING STAGE 6.1 OUTPUT INTEGRITY & INVARIANTS...")
    subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "08_verify_stage6_1_results.py")])

    # Step 5: Package Results Bundle
    print("\n>>> STEP 5/5: PACKAGING STAGE 6.1 RESULTS BUNDLE FOR EXPORT...")
    subprocess.check_call([sys.executable, str(CLOUD_DIR / "export_stage6_1_results.py")])

    t_total = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"STAGE 6.1 EXTENSION COMPLETE! Total duration: {t_total:.1f}s ({t_total/60:.2f} mins)")
    print("=" * 80)


if __name__ == "__main__":
    main()
