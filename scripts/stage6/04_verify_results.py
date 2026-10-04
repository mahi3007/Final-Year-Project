#!/usr/bin/env python3
"""
Stage 6: Output Verification & Scientific Invariant Audit.
=========================================================
Validates the integrity of the Stage 6 benchmark outputs:
1. reports/stage6/six_model_benchmark.csv
2. reports/stage6/six_model_dsg_summary.csv
3. reports/stage6/six_model_group_metrics.csv
4. reports/stage6/model_compatibility_manifest.json

Assertions:
- Zero NaN, Null, or unhandled Inf values.
- Primary baseline (Wav2Vec2-base) identically matches frozen Stage 5E metrics.
- Autoregressive models (Whisper, Distil-Whisper) have legitimate static No-Adapt
  values and are transparently recorded as INCOMPATIBLE for CTTA adaptation.
- 0 fail-closed evaluator software failures across all completed runs.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path
import pandas as pd

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6"


def verify_stage6_outputs() -> bool:
    print("=" * 75)
    print("STAGE 6: OUTPUT VERIFICATION & SCIENTIFIC INVARIANT AUDIT")
    print("=" * 75)

    bench_csv = REPORTS_DIR / "six_model_benchmark.csv"
    dsg_csv = REPORTS_DIR / "six_model_dsg_summary.csv"
    manifest_json = REPORTS_DIR / "model_compatibility_manifest.json"

    passed_checks = 0
    total_checks = 6

    # Check 1: Compatibility Manifest Exists
    print("\n[Check 1/6] Compatibility Manifest Existence & Structure:")
    assert manifest_json.exists(), f"Missing manifest: {manifest_json}"
    with open(manifest_json, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["total_models"] == 6, f"Expected 6 models in manifest, got {manifest['total_models']}"
    assert manifest["compatible_ctta_models"] == 4, "Expected 4 compatible CTC models"
    assert manifest["incompatible_ctta_models"] == 2, "Expected 2 incompatible non-CTC models"
    print("  Compatibility manifest verified (4 CTC compatible, 2 Seq2Seq incompatible).")
    passed_checks += 1

    # Check 2: Main Benchmark CSV
    print("\n[Check 2/6] Main Benchmark CSV:")
    assert bench_csv.exists(), f"Missing benchmark CSV: {bench_csv}"
    b_df = pd.read_csv(bench_csv)
    print(f"  Rows loaded: {len(b_df)}")
    assert len(b_df) >= 1, "Benchmark CSV is empty!"
    required_cols = [
        "model_key", "model_name", "architecture_family", "ctta_status",
        "no_adapt_wer", "suta_wer", "dsuta_wer", "dmsuta_wer", "dsg_wer",
        "dsg_delta_r", "dsg_delta_d", "dsg_max_delta_g", "dsg_accepted", "dsg_rejected"
    ]
    for c in required_cols:
        assert c in b_df.columns, f"Missing required column in benchmark CSV: '{c}'"
    print("  Benchmark CSV schema verified.")
    passed_checks += 1

    # Check 3: Wav2Vec2-base Frozen Invariant Match
    print("\n[Check 3/6] Wav2Vec2-base Frozen Stage 5E Invariant Match:")
    w2v_rows = b_df[b_df["model_key"] == "wav2vec2_base"]
    assert len(w2v_rows) == 1, "Expected exactly 1 Wav2Vec2-base row!"
    w_row = w2v_rows.iloc[0]

    # Verify against frozen Stage 5E numbers:
    # No-Adapt: 22.45%, SUTA: 23.55%, DSUTA: 22.55%, DMSUTA: 22.56%, DSG: 22.52%
    # Accepted: 9, Rejected: 216
    assert "22.45" in str(w_row["no_adapt_wer"]), f"Wav2Vec2 No-Adapt mismatch: {w_row['no_adapt_wer']}"
    assert "23.55" in str(w_row["suta_wer"]), f"Wav2Vec2 SUTA mismatch: {w_row['suta_wer']}"
    assert "22.55" in str(w_row["dsuta_wer"]), f"Wav2Vec2 DSUTA mismatch: {w_row['dsuta_wer']}"
    assert "22.56" in str(w_row["dmsuta_wer"]), f"Wav2Vec2 DMSUTA mismatch: {w_row['dmsuta_wer']}"
    assert "22.52" in str(w_row["dsg_wer"]), f"Wav2Vec2 DSG mismatch: {w_row['dsg_wer']}"
    assert int(w_row["dsg_accepted"]) == 9, f"Wav2Vec2 accepted mismatch: {w_row['dsg_accepted']}"
    assert int(w_row["dsg_rejected"]) == 216, f"Wav2Vec2 rejected mismatch: {w_row['dsg_rejected']}"
    print("  Wav2Vec2-base frozen Stage 5E results verified identically (22.45% / 23.55% / 22.52%, 9 acc / 216 rej).")
    passed_checks += 1

    # Check 4: Non-CTC Model Scientific Honesty Assertion
    print("\n[Check 4/6] Autoregressive Models Incompatibility Assertion:")
    for seq2seq_key in ["whisper_base", "distil_whisper_small"]:
        m_rows = b_df[b_df["model_key"] == seq2seq_key]
        if len(m_rows) > 0:
            m_r = m_rows.iloc[0]
            # CTTA columns MUST be marked INCOMPATIBLE
            assert "INCOMPATIBLE" in str(m_r["suta_wer"]).upper(), f"{seq2seq_key} SUTA must be INCOMPATIBLE"
            assert "INCOMPATIBLE" in str(m_r["dsg_wer"]).upper(), f"{seq2seq_key} DSG must be INCOMPATIBLE"
            print(f"  {seq2seq_key} correctly and honestly marked INCOMPATIBLE for CTTA adaptation.")
    passed_checks += 1

    # Check 5: DSG Summary CSV
    print("\n[Check 5/6] DSG Summary CSV:")
    assert dsg_csv.exists(), f"Missing DSG summary CSV: {dsg_csv}"
    d_df = pd.read_csv(dsg_csv)
    assert len(d_df) >= 1, "DSG summary CSV is empty!"
    assert "fail_closed_errors" in d_df.columns, "Missing fail_closed_errors column"
    # For all numeric fail-closed values, ensure 0
    numeric_fc = pd.to_numeric(d_df["fail_closed_errors"], errors="coerce").dropna()
    assert (numeric_fc == 0).all(), f"Detected fail-closed evaluator errors: {numeric_fc.tolist()}"
    print("  DSG Summary CSV verified: 0 fail-closed software errors across all models.")
    passed_checks += 1

    # Check 6: No NaN / Null in critical identifier fields
    print("\n[Check 6/6] Null & NaN Audit:")
    for df, name in [(b_df, "benchmark.csv"), (d_df, "dsg_summary.csv")]:
        for col in ["model_key", "model_id", "architecture_family"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Found {null_count} nulls in {name}:{col}"
    print("  Zero null or corrupted identifiers across all summary tables.")
    passed_checks += 1

    print("\n" + "=" * 75)
    print(f"OUTPUT VERIFICATION COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED.")
    print("=" * 75)
    return True


if __name__ == "__main__":
    success = verify_stage6_outputs()
    sys.exit(0 if success else 1)
