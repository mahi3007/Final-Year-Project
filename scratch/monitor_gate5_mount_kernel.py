#!/usr/bin/env python3
"""
scratch/monitor_gate5_mount_kernel.py

Polls Kaggle kernel status for stage-6m-gate-5-runtime-mount-audit
and downloads output upon completion.
"""

import time
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "cloud" / "kaggle" / "gate5_mount_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KERNEL_SLUG = "venkataakhil07/stage-6m-gate-5-runtime-mount-audit"

start_time = time.time()
print(f"Monitoring {KERNEL_SLUG}...")

while True:
    res = subprocess.run(["kaggle", "kernels", "status", KERNEL_SLUG], capture_output=True, text=True)
    status_line = res.stdout.strip()
    elapsed = int(time.time() - start_time)
    print(f"[{elapsed}s] {status_line}")

    if "KernelWorkerStatus.COMPLETE" in status_line:
        print("[SUCCESS] Kernel execution complete! Fetching output files...")
        out_res = subprocess.run(["kaggle", "kernels", "output", KERNEL_SLUG, "-p", str(OUTPUT_DIR)], capture_output=True, text=True)
        print(out_res.stdout)
        break
    elif "KernelWorkerStatus.ERROR" in status_line or "error" in status_line.lower():
        print("[ERROR] Kernel failed! Fetching logs...")
        out_res = subprocess.run(["kaggle", "kernels", "output", KERNEL_SLUG, "-p", str(OUTPUT_DIR)], capture_output=True, text=True)
        print(out_res.stdout)
        sys.exit(1)

    time.sleep(15)

