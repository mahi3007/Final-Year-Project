#!/usr/bin/env python3
"""
Master Cloud Result Export & Packaging Tool
===========================================
Packages all Stage 5M, Stage 5D, Stage 6, and Stage 6.1 research artifacts into
a single portable zip archive for 1-click download from Kaggle or Google Colab:
- /kaggle/working/stage5_stage6_results_bundle.zip (on Kaggle)
- reports/stage5_stage6_results_bundle.zip (locally)

Included Artifacts:
1. Stage 5M Closed-Loop Online Control:
   - results/stage5m/stage5m_closed_loop_results.csv
   - results/stage5m/stage5m_operational_decisions.csv
   - results/stage5m/stage5m_decision_agreement_matrix.csv
   - reports/stage5m/stage5m_closed_loop_report.md
   - results/stage5m/checkpoints/*.json
2. Stage 5D Common Voice DSG Re-execution:
   - reports/stage5/stage5d_final_decision_audit.csv
   - reports/stage5/stage5d_dsg_reexecution.md
3. Stage 6 Six-Model Benchmark:
   - reports/stage6/six_model_benchmark.csv
   - reports/stage6/six_model_dsg_summary.csv
   - reports/stage6/six_model_group_metrics.csv
   - reports/stage6/six_model_comparative_analysis.md
   - reports/stage6/model_compatibility_matrix.md
   - reports/stage6/model_compatibility_manifest.json
   - reports/stage6/checkpoints/*.*
4. Stage 6.1 Two-Model CTC Extension:
   - reports/stage6_1/stage6_1_benchmark.csv
   - reports/stage6_1/stage6_1_dsg_summary.csv
   - reports/stage6_1/eight_model_benchmark.csv
   - reports/stage6_1/eight_model_dsg_summary.csv
"""

from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def package_all_results() -> Path:
    print("=" * 80)
    print("PACKAGING STAGE 5 & STAGE 6 BENCHMARK RESULTS BUNDLE")
    print("=" * 80)

    out_zip = PROJECT_ROOT / "reports" / "stage5_stage6_results_bundle.zip"
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    kaggle_out = Path("/kaggle/working/stage5_stage6_results_bundle.zip")

    # Collect all existing result files
    search_dirs = [
        (PROJECT_ROOT / "results" / "stage5m", "stage5m_results"),
        (PROJECT_ROOT / "reports" / "stage5m", "stage5m_reports"),
        (PROJECT_ROOT / "reports" / "stage5", "stage5d_reports"),
        (PROJECT_ROOT / "reports" / "stage6", "stage6_reports"),
        (PROJECT_ROOT / "reports" / "stage6_1", "stage6_1_reports"),
    ]

    total_packed = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for base_dir, arc_prefix in search_dirs:
            if not base_dir.exists():
                print(f"  Notice: Directory not yet generated: {base_dir.name}")
                continue
            for f in base_dir.rglob("*"):
                if f.is_file() and not f.name.endswith(".zip"):
                    rel_path = f.relative_to(base_dir)
                    arc_name = f"{arc_prefix}/{rel_path}".replace("\\", "/")
                    zf.write(f, arcname=arc_name)
                    total_packed += 1

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print(f"\nCreated unified archive: {out_zip} ({size_mb:.2f} MB, {total_packed} files packed)")

    # If running in Kaggle environment, copy to /kaggle/working for 1-click download
    if Path("/kaggle/working").exists():
        shutil.copyfile(out_zip, kaggle_out)
        print(f"Copied to Kaggle download directory: {kaggle_out}")
        print("\n--> In Kaggle: Look in the right-hand panel under 'Output' -> Click 'Download' on 'stage5_stage6_results_bundle.zip'")

    return out_zip


if __name__ == "__main__":
    package_all_results()
