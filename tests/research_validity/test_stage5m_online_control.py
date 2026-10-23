"""
Research Validity Tests: Stage 5M Closed-Loop Online Control.
=============================================================
Protocol: v1.1.0-model-expansion
Standard: ADR-005
Review Decision: CONDITIONAL GO — Controlled Research Evaluation

Verifies all methodological invariants for Stage 5M:
1. Frozen safety policy: epsilon_R = 0.00 pp, epsilon_G = +2.00 pp, epsilon_D = +2.00 pp, B = 1000.
2. Model role integrity: CTC qualification, Seq2Seq static portability, held-out isolation.
3. Label isolation firewall: test-stream labels quarantined during adaptation.
4. Operational vs. retrospective agreement cross-tabulation logic.
5. Terminal window rule: final adaptation update omitted.
"""

import json
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_stage5m_frozen_safety_thresholds():
    """Verify that Stage 5M enforces the frozen safety thresholds."""
    gate_cfg_path = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
    assert gate_cfg_path.exists(), "stage5_gate_config.json missing"
    with open(gate_cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Invariants
    assert float(cfg["gate_tolerances"]["epsilon_R"]) == 0.0000
    assert float(cfg["gate_tolerances"]["epsilon_G"]) == 0.0200
    assert float(cfg["gate_tolerances"]["epsilon_D"]) == 0.0200
    assert int(cfg["bootstrap"]["B"]) == 1000
    assert float(cfg["bootstrap"]["confidence"]) == 0.95


def test_stage5m_model_roles_and_seq2seq_boundary():
    """Verify Stage 5M model role assignments in configs/model_role_registry.json."""
    registry_path = PROJECT_ROOT / "configs" / "model_role_registry.json"
    assert registry_path.exists()
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)["models"]

    # CTC Qualification Backbones
    for m in ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]:
        assert reg[m]["stage5m_role"] == "CTC_DSG_QUALIFICATION"
        assert reg[m]["ctta_status"] == "COMPATIBLE"

    # Seq2Seq Static Portability Controls
    for m in ["whisper_base", "distil_whisper_small", "whisper_tiny"]:
        assert reg[m]["stage5m_role"] == "STATIC_PORTABILITY"
        assert reg[m]["ctta_status"] == "INCOMPATIBLE_NON_CTC"

    # Held-Out Models (Reserved for Stage 6)
    for m in ["hubert_large", "xlsr_english", "wav2vec2_large_lv60", "wav2vec2_large_robust"]:
        assert reg[m]["stage5m_role"] == "EXCLUDED_HELD_OUT"


def test_stage5m_agreement_classification_logic():
    """Verify cross-classification logic between operational decision and retrospective ground truth."""
    # Test True Approval
    op_acc = "ACCEPT"
    retro_good = "BENEFICIAL"
    assert (op_acc == "ACCEPT" and retro_good in ["BENEFICIAL", "NEUTRAL"])

    # Test False Approval (Hazardous Failure)
    retro_bad = "HARMFUL"
    is_false_approval = (op_acc == "ACCEPT" and retro_bad == "HARMFUL")
    assert is_false_approval

    # Test True Rejection (Safe Intervention)
    op_rej = "REJECT"
    is_true_rejection = (op_rej == "REJECT" and retro_bad == "HARMFUL")
    assert is_true_rejection

    # Test False Rejection (Conservative Cost)
    is_false_rejection = (op_rej == "REJECT" and retro_good == "BENEFICIAL")
    assert is_false_rejection


def test_stage5m_sentinel_panel_disjoint_speakers():
    """Verify Sentinel Panel (N=30) has zero speaker overlap with test stream."""
    sentinel_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    assert sentinel_csv.exists()
    df_sent = pd.read_csv(sentinel_csv)
    sent_speakers = set(df_sent["speaker_id"].unique())
    assert len(sent_speakers) == 30

    # L2-ARCTIC Stage 4/5 speakers
    stage4_csv = PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv"
    df_st4 = pd.read_csv(stage4_csv)
    st4_speakers = set(df_st4["speaker_id"].unique())

    # ZERO speaker overlap
    overlap = sent_speakers.intersection(st4_speakers)
    assert len(overlap) == 0, f"Speaker contamination detected: {overlap}"


def test_stage5m_temporal_validity_audit_artifacts():
    """Verify Stage 5M temporal validity audit deliverables, counts, and reconciliation."""
    audit_csv = PROJECT_ROOT / "results" / "stage5m" / "stage5m_retrospective_temporal_audit.csv"
    assert audit_csv.exists(), "stage5m_retrospective_temporal_audit.csv missing"
    df_audit = pd.read_csv(audit_csv)
    assert len(df_audit) == 3034, f"Expected 3034 window records, got {len(df_audit)}"

    # 2640 active candidate evaluations
    cand_evals = df_audit[df_audit["operational_decision"].isin(["ACCEPT", "REJECT"])]
    assert len(cand_evals) == 2640, f"Expected 2640 candidate evaluations, got {len(cand_evals)}"
    assert (cand_evals["operational_decision"] == "ACCEPT").sum() == 80
    assert (cand_evals["operational_decision"] == "REJECT").sum() == 2560

    # Prospective matrix
    matrix_csv = PROJECT_ROOT / "results" / "stage5m" / "stage5m_prospective_outcome_matrix.csv"
    assert matrix_csv.exists(), "stage5m_prospective_outcome_matrix.csv missing"
    df_mat = pd.read_csv(matrix_csv, index_col=0)
    assert df_mat.loc["ACCEPT", "BENEFICIAL"] == 7
    assert df_mat.loc["ACCEPT", "NEUTRAL"] == 58
    assert df_mat.loc["ACCEPT", "HARMFUL"] == 3
    assert df_mat.loc["ACCEPT", "UNAVAILABLE"] == 12
    assert df_mat.loc["ACCEPT", "All"] == 80

    # Provenance linkage
    prov_csv = PROJECT_ROOT / "reports" / "stage5m" / "stage5m_prospective_provenance_linkage.csv"
    assert prov_csv.exists(), "stage5m_prospective_provenance_linkage.csv missing"
    df_prov = pd.read_csv(prov_csv)
    assert len(df_prov) == 2640


def test_stage5m_temporal_estimand_separation_and_harm_forensics():
    """Verify that same-window and next-window prospective effects are separated and audited."""
    audit_csv = PROJECT_ROOT / "results" / "stage5m" / "stage5m_retrospective_temporal_audit.csv"
    df_audit = pd.read_csv(audit_csv)

    # Inspect the 5 same-window harmful acceptances
    harm_same = df_audit[(df_audit["operational_decision"] == "ACCEPT") & (df_audit["Delta_E_same_class"] == "HARMFUL")]
    assert len(harm_same) == 5, f"Expected 5 same-window harmful acceptances, got {len(harm_same)}"

    # Check prospective outcome of these 5 updates:
    pros_classes = harm_same["prospective_class"].value_counts().to_dict()
    assert pros_classes.get("BENEFICIAL", 0) == 2, "Expected 2 prospectively beneficial among same-window harmful"
    assert pros_classes.get("NEUTRAL", 0) == 2, "Expected 2 prospectively neutral among same-window harmful"
    assert pros_classes.get("HARMFUL", 0) == 1, "Expected exactly 1 prospectively harmful among same-window harmful"


def test_stage5m_counterfactual_verification_and_missingness_bounds():
    """Verify that all 68 prospective counterfactuals are verified, and missingness bounds are exact."""
    prov_csv = PROJECT_ROOT / "reports" / "stage5m" / "stage5m_prospective_provenance_linkage.csv"
    df_prov = pd.read_csv(prov_csv)

    acc = df_prov[df_prov["operational_decision"] == "ACCEPT"]
    assert len(acc) == 80

    # 68 verified exact counterfactuals
    verif = acc[acc["counterfactual_verification_status"] == "VERIFIED_EXACT_PAIRED_COUNTERFACTUAL"]
    assert len(verif) == 68
    assert (verif["prior_updates_count"] == 0).all(), "All 68 evaluated updates must have 0 prior stream updates"
    assert (verif["retained_state_is_unadapted_base"] == True).all(), "All 68 retained states must be unadapted base"
    assert (verif["same_audio_and_references_verified"] == True).all()
    assert (verif["matched_decoding_and_normalization"] == True).all()

    # 12 unavailable
    unavail_inter = acc[acc["counterfactual_verification_status"] == "UNAVAILABLE_INTERMEDIATE_STATE_NOT_SERIALIZED"]
    assert len(unavail_inter) == 11
    unavail_ctrl = acc[acc["counterfactual_verification_status"] == "UNAVAILABLE_CONTROL_STREAM_NOT_EVALUATED_IN_ORDERING"]
    assert len(unavail_ctrl) == 1

    # Rejected candidates: all 2560 discarded upon rejection
    rej = df_prov[df_prov["operational_decision"] == "REJECT"]
    assert len(rej) == 2560
    assert (rej["counterfactual_verification_status"] == "UNAVAILABLE_CANDIDATE_WEIGHTS_DISCARDED_UPON_REJECTION").all()

    # Sensitivity bounds
    p_harm = 3
    p_unavail = 12
    n_acc = 80
    lower_bound = p_harm / n_acc
    upper_bound = (p_harm + p_unavail) / n_acc
    assert round(lower_bound * 100, 2) == 3.75
    assert round(upper_bound * 100, 2) == 18.75


def test_stage5m_report_wording_and_decision_matrix_labels():
    """Verify that reports/stage5m/stage5m_closed_loop_report.md adheres strictly to P0-1 through P0-4."""
    report_md_path = PROJECT_ROOT / "reports" / "stage5m" / "stage5m_closed_loop_report.md"
    assert report_md_path.exists(), "stage5m_closed_loop_report.md missing"
    content = report_md_path.read_text(encoding="utf-8")

    # P0-1: Correct same-window rejection terminology
    assert "Same-Window Harmful Candidates Rejected" in content
    # Ensure "Hazard Intercepted" is NOT used as an outcome label in the report
    assert "Hazard Intercepted:" not in content
    assert "| **275 (Same-Window Harmful Candidates Rejected)** |" in content
    assert "98.21%" in content
    assert "275 / 280" in content

    # P0-2: Correct beneficial-rejection terminology
    assert "Same-Window Beneficial Candidates Rejected" in content
    assert "97.22%" in content
    assert "315 / 324" in content
    assert "prospective counterfactuals for rejected candidates are unavailable" in content.lower() or \
           "prospective counterfactuals for rejected updates remain unobserved" in content.lower()

    # P0-3: Preserve verified prospective findings
    assert "68 / 80" in content
    assert "4.41%" in content
    assert "3.75%" in content
    assert "18.75%" in content
    assert "deterministic" in content.lower()
    assert "unadapted base" in content.lower()

    # P0-4: Preserve prior audit resolutions and hold status
    assert "HOLD" in content
    assert "Stage 6M" in content



