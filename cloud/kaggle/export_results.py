#!/usr/bin/env python3
"""
Stage 6 Cloud Execution: Result Export & Artifact Packaging Tool.
================================================================
Packages all Stage 6 research artifacts into a single portable zip archive:
- reports/stage6/six_model_benchmark.csv
- reports/stage6/six_model_dsg_summary.csv
- reports/stage6/six_model_group_metrics.csv
- reports/stage6/six_model_comparative_analysis.md
- reports/stage6/model_compatibility_matrix.md
- reports/stage6/model_compatibility_manifest.json
- reports/stage6/checkpoints/ (*.json, *.csv)

Provides ready-to-download outputs in /kaggle/working/stage6_results_bundle.zip.
"""

from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6"
CHECKPOINTS_DIR = REPORTS_DIR / "checkpoints"


def package_results() -> Path:
    print("=" * 75)
    print("STAGE 6: PACKAGING BENCHMARK RESULTS")
    print("=" * 75)

    out_zip = REPORTS_DIR / "stage6_results_bundle.zip"
    kaggle_out = Path("/kaggle/working/stage6_results_bundle.zip")

    files_to_pack = [
        REPORTS_DIR / "six_model_benchmark.csv",
        REPORTS_DIR / "six_model_dsg_summary.csv",
        REPORTS_DIR / "six_model_group_metrics.csv",
        REPORTS_DIR / "six_model_comparative_analysis.md",
        REPORTS_DIR / "model_compatibility_matrix.md",
        REPORTS_DIR / "model_compatibility_manifest.json",
    ]

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files_to_pack:
            if f.exists():
                arcname = f"stage6_results/{f.name}"
                zf.write(f, arcname=arcname)
                print(f"  Added: {f.name}")
            else:
                print(f"  Notice: {f.name} not found (may not have been generated yet).")

        # Also pack checkpoint summary jsons
        if CHECKPOINTS_DIR.exists():
            for ck in CHECKPOINTS_DIR.glob("*.*"):
                arcname = f"stage6_results/checkpoints/{ck.name}"
                zf.write(ck, arcname=arcname)
                print(f"  Added checkpoint: {ck.name}")

    sz_kb = out_zip.stat().st_size / 1024
    print(f"\nCreated local archive: {out_zip} ({sz_kb:.1f} KB)")

    # If running in Kaggle environment, copy to root working directory for 1-click download
    if Path("/kaggle/working").exists():
        shutil.copyfile(out_zip, kaggle_out)
        print(f"Copied to Kaggle download directory: {kaggle_out}")
        print("\n--> In Kaggle: Look in the right-hand panel under 'Output' -> Click 'Download' on 'stage6_results_bundle.zip'")

    return out_zip


if __name__ == "__main__":
    package_results()
