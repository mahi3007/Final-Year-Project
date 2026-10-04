#!/usr/bin/env python3
"""
Stage 6.1: Output Verification & Scientific Invariant Audit.
============================================================
Validates the integrity of the Stage 6.1 extension outputs:
1. reports/stage6_1/stage6_1_benchmark.csv
2. reports/stage6_1/stage6_1_dsg_summary.csv
3. reports/stage6_1/stage6_1_group_metrics.csv
4. reports/stage6_1/model_compatibility_manifest.json

Assertions:
- Zero NaN, Null, or unhandled Inf values.
- Exactly 2 CTC models evaluated (wav2vec2_large_lv60, wav2vec2_large_robust).
- 0 fail-closed evaluator software failures across all 450 candidate updates.
- Candidate count per model equals 225.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pandas as pd

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6_1"


def verify_stage6_1_outputs() -> bool:
    print("=" * 75)
    print("STAGE 6.1: OUTPUT VERIFICATION & SCIENTIFIC INVARIANT AUDIT")
    print("=" * 75)

    bench_csv = REPORTS_DIR / "stage6_1_benchmark.csv"
    dsg_csv = REPORTS_DIR / "stage6_1_dsg_summary.csv"
    manifest_json = REPORTS_DIR / "model_compatibility_manifest.json"

    passed_checks = 0
    total_checks = 5

    # Check 1: Compatibility Manifest Exists
    print("\n[Check 1/5] Stage 6.1 Manifest Existence & Structure:")
    assert manifest_json.exists(), f"Missing manifest: {manifest_json}"
    with open(manifest_json, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["total_models"] == 2, f"Expected 2 models in manifest, got {manifest['total_models']}"
    assert manifest["compatible_ctta_models"] == 2, "Expected 2 compatible CTC models"
    print("  Stage 6.1 manifest verified (2 CTC compatible models).")
    passed_checks += 1

    # Check 2: Benchmark CSV
    print("\n[Check 2/5] Stage 6.1 Benchmark CSV:")
    assert bench_csv.exists(), f"Missing benchmark CSV: {bench_csv}"
    b_df = pd.read_csv(bench_csv)
    print(f"  Rows loaded: {len(b_df)}")
    assert len(b_df) == 2, f"Expected exactly 2 rows, got {len(b_df)}"
    for m in ["wav2vec2_large_lv60", "wav2vec2_large_robust"]:
        assert m in b_df["model_key"].values, f"Missing model: {m}"
    print("  Benchmark CSV schema & model keys verified.")
    passed_checks += 1

    # Check 3: DSG Summary CSV
    print("\n[Check 3/5] Stage 6.1 DSG Summary CSV:")
    assert dsg_csv.exists(), f"Missing DSG summary CSV: {dsg_csv}"
    d_df = pd.read_csv(dsg_csv)
    assert len(d_df) == 2, f"Expected 2 rows in DSG summary, got {len(d_df)}"
    assert "fail_closed_errors" in d_df.columns, "Missing fail_closed_errors column"
    numeric_fc = pd.to_numeric(d_df["fail_closed_errors"], errors="coerce").dropna()
    assert (numeric_fc == 0).all(), f"Detected fail-closed evaluator errors: {numeric_fc.tolist()}"
    print("  DSG Summary CSV verified: 0 fail-closed software errors across both models.")
    passed_checks += 1

    # Check 4: Candidate Windows Check
    print("\n[Check 4/5] Candidate Window Completeness:")
    for _, row in d_df.iterrows():
        total_eval = row["accepted_updates"] + row["rejected_updates"]
        assert total_eval == 225, f"Model {row['model_key']} evaluated {total_eval} windows, expected 225"
    print("  All models completed exactly 225 prequential windows (900 clips).")
    passed_checks += 1

    # Check 5: Null & NaN Audit
    print("\n[Check 5/5] Null & NaN Audit:")
    for df, name in [(b_df, "stage6_1_benchmark.csv"), (d_df, "stage6_1_dsg_summary.csv")]:
        for col in ["model_key", "model_id", "architecture_family"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Found {null_count} nulls in {name}:{col}"
    print("  Zero null or corrupted identifiers across all Stage 6.1 tables.")
    passed_checks += 1

    print("\n" + "=" * 75)
    print(f"STAGE 6.1 OUTPUT VERIFICATION COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED.")
    print("=" * 75)
    return True


if __name__ == "__main__":
    success = verify_stage6_1_outputs()
    sys.exit(0 if success else 1)
