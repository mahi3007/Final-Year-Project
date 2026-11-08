#!/usr/bin/env python3
"""
scratch/monitor_confirmatory_kernel.py

Polls Kaggle kernel status for stage-6m-gate-5-confirmatory-benchmark
and streams output / downloads results.
"""

import time
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "cloud" / "kaggle" / "gate5_execution_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KERNEL_SLUG = "venkataakhil07/stage-6m-gate-5-confirmatory-benchmark"

start_time = time.time()
print(f"Monitoring live kernel {KERNEL_SLUG}...")

last_status = None
while True:
    res = subprocess.run(["kaggle", "kernels", "status", KERNEL_SLUG], capture_output=True, text=True)
    status_line = res.stdout.strip()
    elapsed = int(time.time() - start_time)

    # Print status when changed or periodically
    clean_line = status_line.replace("\r", " ").replace("\n", " ")
    print(f"[{elapsed}s] {clean_line}", flush=True)

    if "KernelWorkerStatus.COMPLETE" in status_line:
        print("[SUCCESS] Kernel execution complete! Fetching output deliverables...", flush=True)
        out_res = subprocess.run(["kaggle", "kernels", "output", KERNEL_SLUG, "-p", str(OUTPUT_DIR)], capture_output=True, text=True)
        print(out_res.stdout, flush=True)
        break
    elif "KernelWorkerStatus.ERROR" in status_line or "error" in status_line.lower():
        print("[ERROR] Kernel failed! Fetching logs...", flush=True)
        out_res = subprocess.run(["kaggle", "kernels", "output", KERNEL_SLUG, "-p", str(OUTPUT_DIR)], capture_output=True, text=True)
        print(out_res.stdout, flush=True)
        sys.exit(1)

    time.sleep(20)

