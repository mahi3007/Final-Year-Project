"""
Blocking Research Validity Test: Historical v1.0.0-canonical Immutability.
Verifies that all historical artifacts, numbers, thresholds, and configurations
remain 100% frozen, bit-exact, and untampered prior to multi-model expansion.
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_historical_artifact_manifest_hash_stability():
    """Verify all 37 historical artifacts match their registered SHA-256 hashes."""
    manifest_path = PROJECT_ROOT / "manifests" / "historical_v1.0_artifact_manifest.json"
    assert manifest_path.exists(), f"Missing manifest: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest_entries = data.get("manifest", [])
    assert len(manifest_entries) == 37, f"Expected 37 historical artifacts, found {len(manifest_entries)}"

    for entry in manifest_entries:
        file_path = PROJECT_ROOT / entry["path"]
        assert file_path.exists(), f"Historical artifact missing: {entry['path']}"
        actual_hash = compute_sha256(file_path)
        assert actual_hash == entry["sha256"], (
            f"HASH MISMATCH on immutable artifact {entry['path']}: "
            f"expected {entry['sha256']}, got {actual_hash}"
        )


def test_historical_stage2_numerical_immutability():
    """Verify Stage 2 static baseline results are exactly preserved."""
    rep_path = PROJECT_ROOT / "reports" / "stage2_final_report.md"
    assert rep_path.exists()
    content = rep_path.read_text(encoding="utf-8")

    expected_models = {
        "wav2vec2_base": ("85.51%", "20.65%"),
        "whisper_base": ("90.40%", "17.39%"),
        "data2vec_base": ("84.06%", "14.13%"),
        "distil_whisper_small": ("81.52%", "21.74%"),
        "whisper_tiny": ("96.38%", "47.83%"),
        "wav2vec2_100h": ("88.04%", "21.74%"),
    }

    for model, (exp_wer, exp_d) in expected_models.items():
        assert f"`{model}`" in content, f"Model {model} missing from Stage 2 report"
        assert exp_wer in content, f"Expected WER {exp_wer} for {model} missing in Stage 2 report"
        assert exp_d in content, f"Expected Disparity {exp_d} for {model} missing in Stage 2 report"


def test_historical_stage3_numerical_immutability():
    """Verify Stage 3 multi-order and method results match historical records."""
    csv_path = PROJECT_ROOT / "reports" / "ctta" / "multi_order_all_methods.csv"
    assert csv_path.exists()
    df = pd.read_csv(csv_path)

    # ORDER_A no_adapt
    oa_no = df[(df["ordering"] == "ORDER_A") & (df["method"] == "no_adapt")].iloc[0]
    assert round(oa_no["corpus_wer"], 4) == 0.8551
    assert round(oa_no["delta_r"], 4) == 0.0
    assert round(oa_no["disparity_d"], 4) == 0.2065
    assert round(oa_no["max_group_regression"], 4) == 0.0

    # ORDER_A suta
    oa_suta = df[(df["ordering"] == "ORDER_A") & (df["method"] == "suta")].iloc[0]
    assert round(oa_suta["corpus_wer"], 4) == 0.8514
    assert round(oa_suta["delta_r"], 4) == -0.0037
    assert round(oa_suta["delta_d"], 4) == -0.0108
    assert round(oa_suta["max_group_regression"], 4) == 0.0

    # ORDER_A dsuta
    oa_dsuta = df[(df["ordering"] == "ORDER_A") & (df["method"] == "dsuta")].iloc[0]
    assert round(oa_dsuta["corpus_wer"], 4) == 0.8533
    assert round(oa_dsuta["delta_r"], 4) == -0.0018
    assert round(oa_dsuta["delta_d"], 4) == -0.0108
    assert round(oa_dsuta["max_group_regression"], 4) == 0.0

    # ORDER_A dmsuta
    oa_dmsuta = df[(df["ordering"] == "ORDER_A") & (df["method"] == "dmsuta")].iloc[0]
    assert round(oa_dmsuta["corpus_wer"], 4) == 0.8551
    assert round(oa_dmsuta["delta_r"], 4) == 0.0
    assert round(oa_dmsuta["disparity_d"], 4) == 0.2065
    assert round(oa_dmsuta["max_group_regression"], 4) == 0.0

    # ORDER_B suta
    ob_suta = df[(df["ordering"] == "ORDER_B") & (df["method"] == "suta")].iloc[0]
    assert round(ob_suta["corpus_wer"], 4) == 0.8569
    assert round(ob_suta["delta_r"], 4) == 0.0018
    assert round(ob_suta["max_group_regression"], 4) == 0.0109

    # ORDER_C suta
    oc_suta = df[(df["ordering"] == "ORDER_C") & (df["method"] == "suta")].iloc[0]
    assert round(oc_suta["corpus_wer"], 4) == 0.8551
    assert round(oc_suta["delta_r"], 4) == 0.0
    assert round(oc_suta["max_group_regression"], 4) == 0.0109


def test_historical_stage4_thresholds_immutability():
    """Verify Stage 4 thresholds remain frozen at delta_G=0.02, delta_D=0.02."""
    cfg_path = PROJECT_ROOT / "configs" / "stage4_thresholds.json"
    assert cfg_path.exists()
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    assert cfg["primary_frozen_thresholds"]["delta_G"] == 0.02
    assert cfg["primary_frozen_thresholds"]["delta_D"] == 0.02
    assert cfg["dataset_used"] == "datasets/splits/calibration.csv"
    assert cfg["bootstrap_replicates"] == 1000


def test_historical_stage5_gate_config_immutability():
    """Verify Stage 5 DSG gate configuration remains frozen at epsilon_R=0.0, epsilon_G=0.02, epsilon_D=0.02."""
    cfg_path = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
    assert cfg_path.exists()
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    tol = cfg["gate_tolerances"]
    assert tol["epsilon_R"] == 0.0000
    assert tol["epsilon_G"] == 0.0200
    assert tol["epsilon_D"] == 0.0200

    boot = cfg["bootstrap"]
    assert boot["B"] == 1000
    assert boot["confidence"] == 0.95
    assert boot["resampling_unit"] == "speaker"
    assert boot["paired"] is True

    fail_closed = cfg["fail_closed_policy"]
    assert fail_closed["enabled"] is True
    assert fail_closed["on_nan_action"] == "REJECT"
    assert fail_closed["on_inf_action"] == "REJECT"
    assert fail_closed["on_missing_group_action"] == "REJECT"
    assert fail_closed["on_empty_sentinel_action"] == "REJECT"
    assert fail_closed["on_exception_action"] == "REJECT"


def test_historical_split_speaker_disjointness():
    """Verify pairwise disjointness of historical dataset partitions."""
    rep_path = PROJECT_ROOT / "reports" / "split_report.json"
    assert rep_path.exists()
    with open(rep_path, "r", encoding="utf-8") as f:
        rep = json.load(f)

    partitions = rep["partitions"]
    part_keys = list(partitions.keys())
    for i in range(len(part_keys)):
        for j in range(i + 1, len(part_keys)):
            s1 = set(partitions[part_keys[i]]["speaker_ids"])
            s2 = set(partitions[part_keys[j]]["speaker_ids"])
            overlap = s1.intersection(s2)
            assert len(overlap) == 0, f"Speaker overlap between {part_keys[i]} and {part_keys[j]}: {overlap}"


def test_historical_stage6_seq2seq_incompatibility_recorded():
    """Verify Stage 6 records whisper_base and distil_whisper_small as static/non-CTC."""
    bench_csv = PROJECT_ROOT / "reports" / "stage6" / "eight_model_benchmark.csv"
    assert bench_csv.exists()
    df = pd.read_csv(bench_csv)

    seq2seq_rows = df[df["architecture_family"].isin(["EncoderDecoder", "Seq2Seq"])]
    assert len(seq2seq_rows) >= 2

    for _, row in seq2seq_rows.iterrows():
        # SUTA/DSG adaptation status must indicate incompatible/static
        assert row["ctta_status"] == "INCOMPATIBLE_NON_CTC"
        assert row["suta_wer"] == "INCOMPATIBLE"
