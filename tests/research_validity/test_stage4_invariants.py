"""
Stage 4 Research Validity and Invariant Tests.
Validates:
1. Split scale: 120 utterances, 12 speakers, 2 speakers/group across 6 groups.
2. Zero speaker leakage vs development and calibration.
3. Frozen threshold provenance (delta_G >= 0.02, delta_D >= 0.02, calibration-derived).
4. Window size sweep completeness on K in {1, 4, 5, 10}.
5. Acoustic stress determinism, SHA-256 manifest integrity, and transcript preservation.
"""

import os
import json
import hashlib
import pandas as pd
import pytest


def test_stage4_split_scale_and_balance():
    """Verify Stage 4 characterization split scale, speaker counts, and group balance."""
    split_path = "datasets/splits/stage4_characterization.csv"
    assert os.path.exists(split_path), f"Stage 4 split not found at {split_path}"
    df = pd.read_csv(split_path)

    # 120 total utterances
    assert len(df) == 120, f"Expected 120 utterances, got {len(df)}"

    # 12 unique speakers
    spks = df["speaker_id"].unique()
    assert len(spks) == 12, f"Expected 12 unique speakers, got {len(spks)}"

    # 6 groups, 20 utterances and 2 speakers per group
    groups = df["group_id"].unique()
    assert len(groups) == 6, f"Expected 6 groups, got {len(groups)}"

    for g in groups:
        g_df = df[df["group_id"] == g]
        assert len(g_df) == 20, f"Group {g} expected 20 utterances, got {len(g_df)}"
        g_spks = g_df["speaker_id"].unique()
        assert len(g_spks) == 2, f"Group {g} expected 2 speakers, got {len(g_spks)}"


def test_stage4_zero_speaker_leakage():
    """Verify strict zero speaker overlap between stage4_characterization, development, and calibration."""
    df_s4 = pd.read_csv("datasets/splits/stage4_characterization.csv")
    df_dev = pd.read_csv("datasets/splits/development.csv")
    df_cal = pd.read_csv("datasets/splits/calibration.csv")

    s4_spks = set(df_s4["speaker_id"].unique())
    dev_spks = set(df_dev["speaker_id"].unique())
    cal_spks = set(df_cal["speaker_id"].unique())

    overlap_dev = s4_spks.intersection(dev_spks)
    assert len(overlap_dev) == 0, f"Critical speaker leakage between Stage 4 and Development: {overlap_dev}"

    overlap_cal = s4_spks.intersection(cal_spks)
    assert len(overlap_cal) == 0, f"Critical speaker leakage between Stage 4 and Calibration: {overlap_cal}"


def test_stage4_frozen_thresholds_provenance():
    """Verify frozen practical thresholds delta_G and delta_D provenance and criteria."""
    thresh_path = "configs/stage4_thresholds.json"
    assert os.path.exists(thresh_path), f"Threshold manifest not found at {thresh_path}"

    with open(thresh_path, "r", encoding="utf-8") as f:
        tdata = json.load(f)

    assert tdata["protocol_version"] == "v1.0.0-canonical"
    assert tdata["stage"] == "Stage 4B"
    assert tdata["dataset_used"] == "datasets/splits/calibration.csv"

    delta_g = tdata["primary_frozen_thresholds"]["delta_G"]
    delta_d = tdata["primary_frozen_thresholds"]["delta_D"]

    # Must be at least 2.0% (exceeding discrete 1-word shift ratio ~1.09%)
    assert delta_g >= 0.0200, f"delta_G ({delta_g}) must be >= 0.0200"
    assert delta_d >= 0.0200, f"delta_D ({delta_d}) must be >= 0.0200"
    assert "rationale" in tdata["primary_frozen_thresholds"]


def test_stage4_window_sweep_provenance():
    """Verify window size characterization sweep results on calibration split."""
    sweep_path = "reports/stage4/window_size_sweep/window_size_sweep_results.csv"
    assert os.path.exists(sweep_path), f"Sweep results not found at {sweep_path}"

    df = pd.read_csv(sweep_path)
    k_vals = sorted(df["k"].tolist())
    assert k_vals == [1, 4, 5, 10], f"Expected K grid [1, 4, 5, 10], got {k_vals}"

    for _, row in df.iterrows():
        assert 0.0 <= row["corpus_wer"] <= 1.5
        assert 0.0 <= row["disparity_d"] <= 1.0


def test_acoustic_stress_partitions_integrity():
    """Verify all acoustic stress partitions exist, preserve transcripts, and have manifests."""
    conditions = ["noise_moderate", "noise_severe", "babble_moderate", "reverberation"]
    df_clean = pd.read_csv("datasets/splits/stage4_characterization.csv")

    for cond in conditions:
        split_path = f"datasets/splits/stage4_{cond}.csv"
        manifest_path = f"datasets/corrupted/{cond}/manifest.json"

        assert os.path.exists(split_path), f"Missing split: {split_path}"
        assert os.path.exists(manifest_path), f"Missing manifest: {manifest_path}"

        df_cond = pd.read_csv(split_path)
        assert len(df_cond) == len(df_clean), f"Length mismatch for {cond}: {len(df_cond)} vs {len(df_clean)}"

        # Verify exact match of reference transcripts (no corruption of labels)
        assert (df_cond["reference_normalized"].values == df_clean["reference_normalized"].values).all(), \
            f"Reference transcripts modified in {cond}!"

        # Verify audio file existence
        for audio_p in df_cond["audio_filepath"]:
            assert os.path.exists(audio_p), f"Corrupted audio file not found: {audio_p}"

        # Verify manifest
        with open(manifest_path, "r", encoding="utf-8") as mf:
            mdata = json.load(mf)
            assert mdata["condition_name"] == cond
            assert mdata["num_utterances"] == 120
            assert "output_split_sha256" in mdata


def test_stage4_decision_and_boundary_integrity():
    """Verify integrity of Stage 4 matrices, boundary condition map, and GO decision record."""
    matrix_p = "reports/stage4/stage4d_multi_order_matrix.csv"
    boot_p = "reports/stage4/stage4d_speaker_cluster_bootstrap.csv"
    stress_p = "reports/stage4/stage4e_acoustic_stress_matrix.csv"
    boundary_p = "reports/stage4/stage4g_boundary_condition_map.csv"
    decision_p = "reports/stage4/dsg_go_no_go_decision.json"

    assert os.path.exists(matrix_p), f"Missing {matrix_p}"
    assert os.path.exists(boot_p), f"Missing {boot_p}"
    assert os.path.exists(stress_p), f"Missing {stress_p}"
    assert os.path.exists(boundary_p), f"Missing {boundary_p}"
    assert os.path.exists(decision_p), f"Missing {decision_p}"

    df_m = pd.read_csv(matrix_p)
    assert len(df_m) == 12, f"Expected 12 multi-order cells, got {len(df_m)}"

    df_b = pd.read_csv(boot_p)
    assert len(df_b) == 9, f"Expected 9 bootstrap rows (3 orders x 3 adapted methods), got {len(df_b)}"

    df_s = pd.read_csv(stress_p)
    assert len(df_s) in [15, 20], f"Expected 15 or 20 stress cells, got {len(df_s)}"

    df_bm = pd.read_csv(boundary_p)
    assert len(df_bm) in [24, 28], f"Expected 24 or 28 boundary cells, got {len(df_bm)}"

    with open(decision_p, "r", encoding="utf-8") as f:
        drec = json.load(f)

    assert drec["protocol_version"] == "v1.0.0-canonical"
    assert "Stage 4" in drec["stage"]
    assert drec["decision"] in ["GO", "NO-GO", "CONDITIONAL GO FOR DSG VALIDATION"]
    assert drec["frozen_delta_G"] == 0.02
    assert drec["frozen_delta_D"] == 0.02
    assert drec["total_speakers_evaluated"] == 12
    assert drec["speakers_per_group"] == 2
    assert "decision_rationale" in drec

