#!/usr/bin/env python3
"""
Stage 6.1: Package and Export Stage 6.1 Results Bundle.
======================================================
Zips all reports, manifests, CSVs, and checkpoints from reports/stage6_1/
into a clean results bundle for download from Kaggle / Colab:
- /kaggle/working/stage6_1_results_bundle.zip (on Kaggle)
- stage6_1_results_bundle.zip (locally)
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGE6_1_DIR = PROJECT_ROOT / "reports" / "stage6_1"


def export_bundle():
    print("=" * 70)
    print("STAGE 6.1: PACKAGING RESULTS BUNDLE FOR EXPORT")
    print("=" * 70)

    # Determine export destination
    if Path("/kaggle/working").exists():
        out_zip = Path("/kaggle/working/stage6_1_results_bundle.zip")
    elif Path("/content").exists():
        out_zip = Path("/content/stage6_1_results_bundle.zip")
    else:
        out_zip = PROJECT_ROOT / "stage6_1_results_bundle.zip"

    assert STAGE6_1_DIR.exists(), f"Source directory not found: {STAGE6_1_DIR}"

    files_to_zip = [f for f in STAGE6_1_DIR.rglob("*") if f.is_file() and not f.name.endswith(".zip")]
    print(f"Archiving {len(files_to_zip)} Stage 6.1 files from {STAGE6_1_DIR}...")

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in files_to_zip:
            rel_path = f.relative_to(STAGE6_1_DIR)
            arc_name = f"stage6_1_results/{rel_path}".replace("\\", "/")
            z.write(f, arcname=arc_name)

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print(f"\nBundle successfully created: {out_zip} ({size_mb:.2f} MB)")
    print("You can now download this file from Kaggle / Colab and extract it locally.")
    print("=" * 70)
    return str(out_zip)


if __name__ == "__main__":
    export_bundle()
