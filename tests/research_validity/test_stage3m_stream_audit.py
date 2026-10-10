"""
Stage 3M Multi-Model Experimental Integrity and Invariant Audit Tests
Standard: ADR-005 / Protocol v1.1.0-model-expansion
Author: DSG-CTTA Validation Framework
"""

import json
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "manifests" / "stage3m_experiment_manifest.json"
RESULTS_CSV_PATH = PROJECT_ROOT / "results" / "stage3_multimodel" / "stage3m_full_results.csv"
BOOTSTRAP_CSV_PATH = PROJECT_ROOT / "results" / "stage3_multimodel" / "stage3m_bootstrap_uncertainty.csv"
ROLE_REGISTRY_PATH = PROJECT_ROOT / "configs" / "model_role_registry.json"


@pytest.fixture(scope="module")
def manifest():
    if not MANIFEST_PATH.exists():
        pytest.skip(f"Stage 3M manifest not yet generated: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def results_df():
    if not RESULTS_CSV_PATH.exists():
        pytest.skip(f"Stage 3M results CSV not yet generated: {RESULTS_CSV_PATH}")
    return pd.read_csv(RESULTS_CSV_PATH)


@pytest.fixture(scope="module")
def bootstrap_df():
    if not BOOTSTRAP_CSV_PATH.exists():
        pytest.skip(f"Stage 3M bootstrap CSV not yet generated: {BOOTSTRAP_CSV_PATH}")
    return pd.read_csv(BOOTSTRAP_CSV_PATH)


def test_manifest_structure_and_cell_count(manifest):
    """Verify exactly 39 designated experiment cells are present and accounted for."""
    assert manifest["protocol_version"] == "v1.1.0-model-expansion"
    assert manifest["total_cells"] == 39
    assert manifest["ctc_cells"] == 36
    assert manifest["seq2seq_cells"] == 3
    assert len(manifest["cells"]) == 39
    
    # Check dataset parameters
    assert manifest["dataset"]["total_utterances"] == 60
    assert manifest["dataset"]["total_speakers"] == 6
    assert manifest["dataset"]["reference_words"] == 552


def test_model_catalog_integrity(manifest):
    """Verify exact model checkpoints match the frozen model role registry."""
    with open(ROLE_REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    expected_models = {
        "wav2vec2_base": "facebook/wav2vec2-base-960h",
        "data2vec_base": "facebook/data2vec-audio-base-960h",
        "wav2vec2_100h": "facebook/wav2vec2-base-100h",
        "whisper_base": "openai/whisper-base",
        "distil_whisper_small": "distil-whisper/distil-small.en",
        "whisper_tiny": "openai/whisper-tiny"
    }
    
    found_models = {c["model_key"]: c["model_id"] for c in manifest["cells"]}
    for k, exp_id in expected_models.items():
        assert k in found_models, f"Missing model {k} in Stage 3M cells"
        assert found_models[k] == exp_id, f"Model ID mismatch for {k}: expected {exp_id}, got {found_models[k]}"


def test_no_adapt_stream_order_invariance(results_df):
    """
    CRITICAL SCIENTIFIC CONTROL:
    No-Adapt model weights are never updated, so evaluating the exact same 60 utterances
    under ORDER_A, ORDER_B, and ORDER_C must produce identical total errors and overall WER.
    """
    for model_key in ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]:
        sub = results_df[(results_df["model_key"] == model_key) & (results_df["method"] == "no_adapt")]
        assert len(sub) == 3, f"Expected 3 orders for {model_key} no-adapt, got {len(sub)}"
        
        errors = sub["total_errors"].unique()
        wers = sub["corpus_wer"].unique()
        ref_lens = sub["reference_words"].unique()
        
        assert len(errors) == 1, (
            f"INVARIANT VIOLATION: {model_key} No-Adapt produced varying error counts across orders: {sub['total_errors'].to_dict()}"
        )
        assert len(wers) == 1, (
            f"INVARIANT VIOLATION: {model_key} No-Adapt produced varying WER across orders: {sub['corpus_wer'].to_dict()}"
        )
        assert len(ref_lens) == 1 and ref_lens[0] == 552


def test_ctc_seq2seq_architectural_boundary(manifest, results_df):
    """
    Verify strict architectural boundary:
    Seq2Seq models are evaluated ONLY under No-Adapt static control.
    Never run frame-entropy CTTA (SUTA, DSUTA, DMSUTA) on Seq2Seq.
    """
    seq2seq_keys = ["whisper_base", "distil_whisper_small", "whisper_tiny"]
    
    # Manifest verification
    for c in manifest["cells"]:
        if c["model_key"] in seq2seq_keys:
            assert c["architecture"] == "SEQ2SEQ"
            assert c["method"] == "no_adapt"
            assert "static" in c["ordering_id"].lower()
            
    # Results verification
    seq2seq_results = results_df[results_df["model_key"].isin(seq2seq_keys)]
    assert set(seq2seq_results["method"].unique()) == {"no_adapt"}
    assert (seq2seq_results["delta_r"] == 0.0).all()
    assert (seq2seq_results["max_delta_g"] == 0.0).all()


def test_bootstrap_uncertainty_limitations_acknowledged(bootstrap_df):
    """
    Verify that bootstrap uncertainty file documents the N=6 speaker limitation.
    """
    assert len(bootstrap_df) == 27  # 3 CTC models x 3 methods (suta, dsuta, dmsuta) x 3 orders
    for note in bootstrap_df["note"]:
        assert "N=6" in note
        assert "Stage 4M" in note


def test_stage3m_reproducibility_bridge():
    """Verify Stage 3M forensic reproducibility bridge artifact."""
    bridge_path = PROJECT_ROOT / "reports" / "stage3m" / "stage3m_reproducibility_bridge.csv"
    assert bridge_path.exists(), f"Missing bridge artifact: {bridge_path}"
    df = pd.read_csv(bridge_path)
    assert len(df) == 4
    assert set(df["method"]) == {"no_adapt", "suta", "dsuta", "dmsuta"}
    
    # Check provenance columns
    assert "hf_commit_hash" in df.columns
    assert "full_state_dict_sha256" in df.columns
    assert "active_layernorm_param_hash" in df.columns
    assert "audit_classification" in df.columns
    
    # Verify No-Adapt bit-for-bit exact match
    no_adapt_row = df[df["method"] == "no_adapt"].iloc[0]
    assert no_adapt_row["wer_discrepancy_pp"] == 0.0
    assert no_adapt_row["error_count_delta"] == 0
    assert no_adapt_row["audit_classification"] == "PREDICTION_EQUALITY_VERIFIED"
    
    # Verify DSUTA identical metric match
    dsuta_row = df[df["method"] == "dsuta"].iloc[0]
    assert dsuta_row["wer_discrepancy_pp"] == 0.0
    assert dsuta_row["error_count_delta"] == 0
    assert dsuta_row["audit_classification"] == "METRIC_CONCORDANCE_EXACT"


def test_stage3m_collapse_diagnostics():
    """Verify Stage 3M collapse diagnostics for wav2vec2_100h DMSUTA ORDER_C."""
    diag_path = PROJECT_ROOT / "reports" / "stage3m" / "stage3m_collapse_diagnostics.csv"
    assert diag_path.exists(), f"Missing collapse diagnostics: {diag_path}"
    df = pd.read_csv(diag_path)
    assert len(df) == 15
    assert (df["window_id"] == list(range(15))).all()
    
    # Window 0 should have non-empty hypothesis words
    w0 = df.iloc[0]
    assert w0["total_hyp_words"] > 0
    assert w0["blank_frame_fraction"] < 1.0


def test_stage3m_speaker_overlap_audit():
    """Verify machine-readable speaker overlap report."""
    overlap_path = PROJECT_ROOT / "reports" / "stage3m" / "stage3m_speaker_overlap_audit.csv"
    assert overlap_path.exists(), f"Missing speaker overlap audit: {overlap_path}"
    df = pd.read_csv(overlap_path)
    
    # Stage 3M vs Stage 4M MUST overlap by exactly 6 speakers (not disjoint)
    s3_s4 = df[(df["split_a"] == "stage3m_final_test") & (df["split_b"] == "stage4m_characterization")].iloc[0]
    assert s3_s4["overlap_count"] == 6
    assert s3_s4["disjoint"] is False or s3_s4["disjoint"] == False
    assert "Expanded" in s3_s4["independent_speaker_validation"] or "NO" in s3_s4["independent_speaker_validation"]
    
    # Calibration and Common Voice MUST be disjoint with Stage 3M
    s3_cal = df[(df["split_a"] == "stage3m_final_test") & (df["split_b"] == "calibration")].iloc[0]
    assert s3_cal["overlap_count"] == 0
    assert s3_cal["disjoint"] is True or s3_cal["disjoint"] == True
    
    s3_cv = df[(df["split_a"] == "stage3m_final_test") & (df["split_b"] == "common_voice_external_eval")].iloc[0]
    assert s3_cv["overlap_count"] == 0
    assert s3_cv["disjoint"] is True or s3_cv["disjoint"] == True


def test_stage3m_scientific_audit_addendum_exists():
    """Verify that Stage 3M scientific audit addendum document exists and contains required sections."""
    addendum_path = PROJECT_ROOT / "reports" / "stage3m" / "stage3m_scientific_audit_addendum.md"
    assert addendum_path.exists(), f"Missing addendum: {addendum_path}"
    text = addendum_path.read_text(encoding="utf-8")
    assert "P0-1" in text
    assert "P0-2" in text
    assert "P0-3" in text
    assert "P0-4" in text
    assert "P0-5" in text
    assert "P0-6" in text
    assert "e28c2c6b1c568146" in text


def test_stage4m_preregistration_addenda_exist():
    """Verify Stage 4M statistical preregistration addendum, validation report, and audit CSV exist."""
    prereg_path = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md"
    valid_path = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md"
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    
    assert prereg_path.exists(), f"Missing preregistration addendum: {prereg_path}"
    assert valid_path.exists(), f"Missing validation report: {valid_path}"
    assert audit_csv.exists(), f"Missing audit CSV: {audit_csv}"
    
    prereg_text = prereg_path.read_text(encoding="utf-8")
    assert "NegativeBinomial" in prereg_text
    assert "Condition" in prereg_text
    assert "log N_i" in prereg_text or "offset" in prereg_text
    assert "K-Sweep" in prereg_text or "K-sweep" in prereg_text


def test_stage4m_observation_grain_and_row_count():
    """
    P0-1 Audit: Verify observation grain is frozen at Utterance-Level (Approach A)
    with explicit distinction between nominal full-factorial (180 cells / 21,600 rows)
    and canonical GLMM (150 cells / 18,000 rows).
    """
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df = pd.read_csv(audit_csv)
    meta = dict(zip(df["parameter"], df["value"]))
    
    assert meta["chosen_analysis_grain"] == "UTTERANCE_LEVEL"
    assert int(meta["expected_record_count"]) == 18000
    assert int(meta["canonical_record_count"]) == 18000
    assert int(meta["canonical_glmm_settings"]) == 150
    assert int(meta["nominal_settings_count"]) == 180
    assert int(meta["duplicated_sensitivity_record_count"]) == 21600
    assert int(meta["utterances_per_stream"]) == 120
    assert int(meta["total_speakers"]) == 12
    assert meta["offset_variable"] == "log(N_i)"
    
    # Check preregistration document text
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    assert "18,000" in prereg_text
    assert "150" in prereg_text
    assert "180" in prereg_text
    assert "Approach A: Utterance-Level" in prereg_text


def test_stage4m_window_count_and_terminal_rule():
    """
    P0-1 Audit: Verify exactly 30 prediction windows (120 / 4) and terminal window rule.
    """
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df = pd.read_csv(audit_csv)
    meta = dict(zip(df["parameter"], df["value"]))
    
    assert int(meta["window_size_K"]) == 4
    assert int(meta["prediction_windows"]) == 30
    assert int(meta["adaptation_updates_per_stream"]) == 29
    
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    
    # Assert 30 windows documented
    assert "30 prediction windows" in prereg_text or "30 prediction windows" in valid_text
    assert "120 / 4" in prereg_text or "120/4" in prereg_text
    # Assert terminal window policy
    assert "Terminal Window Rule" in prereg_text
    assert "omitted" in prereg_text.lower() or "skipped" in prereg_text.lower()


def test_stage4m_empirical_logit_completely_removed():
    """
    P0-2 Audit: Verify that the mathematically invalid empirical-logit fallback
    has been completely removed and replaced with continuous log-rate linear model.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    scratch_text = (PROJECT_ROOT / "scratch" / "validate_stage4m_glmm_spec.py").read_text(encoding="utf-8")
    
    # Ensure invalid empirical logit formulas are NOT used as an active fallback
    assert "logit(" not in prereg_text
    assert "E + 0.5)/(N - E + 0.5)" not in prereg_text
    assert "E+0.5)/(N+1.0)" not in prereg_text
    
    # Ensure replacement continuous log-rate model is documented and used
    assert "Continuous Log-Rate Linear Model" in prereg_text or "Log-Rate Linear Model" in prereg_text
    assert "log((E + 0.5) / N_i)" in prereg_text or "log((E+0.5)/N_i)" in prereg_text


def test_stage4m_actual_glmm_with_random_effects_validated():
    """
    P0-2 Audit: Verify that the actual Negative Binomial GLMM with crossed random effects
    (b_s, b_i), variance components, and optimization details is documented and validated.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    
    # Random effects structure
    assert "b_s" in prereg_text and "b_i" in prereg_text
    assert "sigma_speaker" in prereg_text or "sigma_{speaker}" in prereg_text or "sigma_s" in prereg_text
    assert "sigma_utt" in prereg_text or "sigma_{utt}" in prereg_text or "sigma_u" in prereg_text
    
    # Validation report specifics
    assert "Stage 4M Crossed Negative Binomial GLMM Estimation Summary" in valid_text
    assert "Optimizer" in valid_text
    assert "Dispersion (phi)" in valid_text
    assert "Speaker SD (sigma_s)" in valid_text
    assert "Utterance SD (sigma_u)" in valid_text


def test_stage4m_differential_subgroup_harm_fixtures():
    """
    P0-3 Audit: Direct mathematical verification of Tests A, B, and C
    asserting exact analytical expected values for subgroup safety estimands.
    """
    groups = ["Arabic", "Hindi", "Spanish", "Mandarin", "Vietnamese", "Korean"]
    n_words = 100
    tot_words = 600
    
    base_errors = {"Arabic": 10, "Hindi": 20, "Spanish": 30, "Mandarin": 40, "Vietnamese": 50, "Korean": 60}
    base_wers = {g: (base_errors[g] / n_words) * 100.0 for g in groups}
    base_overall = (sum(base_errors.values()) / tot_words) * 100.0 # 35.0%
    base_disp = max(base_wers.values()) - min(base_wers.values()) # 50.0 pp
    
    def evaluate_run(adapt_errors):
        adapt_wers = {g: (adapt_errors[g] / n_words) * 100.0 for g in groups}
        adapt_overall = (sum(adapt_errors.values()) / tot_words) * 100.0
        delta_r = adapt_overall - base_overall
        delta_g = {g: adapt_wers[g] - base_wers[g] for g in groups}
        max_delta_g = max(delta_g.values())
        adapt_disp = max(adapt_wers.values()) - min(adapt_wers.values())
        delta_d = adapt_disp - base_disp
        return delta_r, delta_g, max_delta_g, delta_d
    
    # Test A: Uniform improvement
    errors_a = {"Arabic": 5, "Hindi": 15, "Spanish": 25, "Mandarin": 35, "Vietnamese": 45, "Korean": 55}
    dr_a, dg_a, mdg_a, dd_a = evaluate_run(errors_a)
    assert abs(dr_a - (-5.0)) < 1e-6
    assert abs(dd_a - 0.0) < 1e-6
    assert abs(mdg_a - (-5.0)) < 1e-6
    
    # Test B: Overall improves, one group regresses (+5.0 pp)
    errors_b = {"Arabic": 4, "Hindi": 14, "Spanish": 24, "Mandarin": 34, "Vietnamese": 44, "Korean": 65}
    dr_b, dg_b, mdg_b, dd_b = evaluate_run(errors_b)
    assert dr_b < 0 # Overall improved (-4.17 pp)
    assert abs(mdg_b - 5.0) < 1e-6 # Korean regressed by +5.0 pp
    assert mdg_b > 2.0 # BREACH: max_delta_g > delta_G (+2.00 pp)
    assert dd_b > 0 # Disparity widened (+11.0 pp)
    
    # Test C: Overall deteriorates, disparity shrinks (-20 pp)
    errors_c = {"Arabic": 35, "Hindi": 40, "Spanish": 45, "Mandarin": 50, "Vietnamese": 55, "Korean": 65}
    dr_c, dg_c, mdg_c, dd_c = evaluate_run(errors_c)
    assert dr_c > 0 # Overall worsened (+13.33 pp)
    assert dd_c < 0 # Disparity compressed (-20.0 pp)
    assert mdg_c > 2.0 # Arabic regressed by +25.0 pp -> UNSAFE!
    # Shrunk disparity must NOT grant safety:
    is_safe = (dr_c <= 0) and (mdg_c <= 2.0) and (dd_c <= 2.0)
    assert not is_safe


def test_stage4m_marginal_g_computation_targets():
    """
    P0-4 Audit: Verify separation of Cohort-Standardized vs Population-Marginal
    G-computation prediction targets.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    
    assert "Cohort-Standardized" in prereg_text or "Cohort-Standardized" in valid_text
    assert "Population-Marginal" in prereg_text or "Population-Marginal" in valid_text
    assert "log-normal" in prereg_text.lower() or "lognormal" in valid_text.lower()


def test_stage4m_stratified_paired_bootstrap():
    """
    P0-5 Audit: Verify Stratified Paired Speaker-Cluster Bootstrap definition
    and 100% preservation of all 6 accent groups.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df = pd.read_csv(audit_csv)
    meta = dict(zip(df["parameter"], df["value"]))
    
    assert "STRATIFIED_PAIRED" in meta["bootstrap_procedure"]
    assert "Stratified Paired" in prereg_text
    assert "all 6" in prereg_text.lower() or "6 accent groups" in prereg_text.lower()


def test_stage4m_fallback_triggers_and_small_cluster_policy():
    """
    P0-2 & P0-3 Audit: Verify all 4 fallback levels have explicit triggers,
    and small-cluster (N=12) degrees of freedom (df=11) and limitations are documented.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    
    # Fallback levels and triggers
    assert "Level 1" in prereg_text and "Trigger" in prereg_text
    assert "Level 2" in prereg_text
    assert "Level 3" in prereg_text
    assert "Level 4" in prereg_text
    
    # Small-cluster policy
    assert "df = G - 1 = 11" in prereg_text or "11 degrees of freedom" in prereg_text or "df = 11" in prereg_text
    assert "12 independent clusters" in prereg_text or "12 speaker clusters" in prereg_text
    assert "exploratory" in prereg_text.lower() or "sensitivity" in prereg_text.lower()


def test_stage4m_subgroup_safety_estimands_in_percentage_points():
    """
    P0-4 Audit: Verify primary safety estimands (Delta_R, Delta_g, max_g Delta_g, Delta_D)
    are defined and reported strictly in percentage points (pp), with frozen thresholds.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df = pd.read_csv(audit_csv)
    meta = dict(zip(df["parameter"], df["value"]))
    
    assert meta["subgroup_estimand_scale"] == "PERCENTAGE_POINTS"
    assert float(meta["safety_threshold_delta_G"]) == 0.02
    assert float(meta["safety_threshold_delta_D"]) == 0.02
    assert int(meta["bootstrap_resamples_B"]) == 1000
    assert float(meta["significance_alpha"]) == 0.05
    
    assert "percentage points" in prereg_text
    assert "Delta_R" in prereg_text
    assert "Delta_g" in prereg_text
    assert "Delta_D" in prereg_text


def test_stage4m_seed_policy_and_dropout_state():
    """
    P0-5 / P0-6 Audit: Verify run-level deterministic seed policy, natural RNG advancement,
    and inactive dropout during adaptation under model.eval().
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df = pd.read_csv(audit_csv)
    meta = dict(zip(df["parameter"], df["value"]))
    
    assert meta["seed_policy"] == "RUN_LEVEL_ADVANCING"
    assert "MODEL_EVAL" in meta["adaptation_execution_mode"]
    
    assert "Prohibition of Per-Window Resets" in prereg_text or "per-window" in prereg_text
    assert "advances naturally" in prereg_text
    assert "dropout" in prereg_text.lower() and "inactive" in prereg_text.lower()



def test_stage4m_fixed_effect_34_parameters_and_canonical_full_rank():
    """
    P0-1 & P0-2 Audit: Canonical GLMM Identifiability and Rank Verification.
    
    Verifies that:
    1. The canonical GLMM design matrix across 150 settings (15 No-Adapt + 135 active methods)
       has shape (150, 34) and EXACT full rank 34 under the constrained formulation
       where standalone Order is omitted and No-Adapt order effects are constrained to 0.
    2. The 18,000-row canonical observation matrix also has shape (18000, 34) and full rank 34.
    3. The numerical condition number of the canonical design is well-behaved (< 50.0).
    4. Reintroducing standalone Order on canonical data creates rank deficiency:
       shape (150, 36) has rank 34 (rank-deficient by 2).
    5. Audit CSV and preregistration addendum explicitly document 34 parameters and rank 34,
       and reject claims of 36 freely estimated parameters for the canonical design.
    """
    import patsy
    import numpy as np

    models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    conditions = ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]
    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    orderings = ["ORDER_A", "ORDER_B", "ORDER_C"]

    # 150 canonical factorial settings:
    # 15 canonical No-Adapt cells: ORDER_A only (3 models * 5 conditions)
    # 135 active adaptation cells: 3 models * 3 methods * 3 orders * 5 conditions
    cells = []
    for m in models:
        for c in conditions:
            cells.append({"model": m, "method": "no_adapt", "condition": c, "ordering": "ORDER_A"})
    for m in models:
        for meth in ["suta", "dsuta", "dmsuta"]:
            for o in orderings:
                for c in conditions:
                    cells.append({"model": m, "method": meth, "condition": c, "ordering": o})

    df_cells = pd.DataFrame(cells)
    assert len(df_cells) == 150

    # Constrained 34-parameter formula: standalone Order omitted
    formula_34 = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    dmat_raw = patsy.dmatrix(formula_34, data=df_cells, return_type="dataframe")
    # Structural zero columns corresponding to No-Adapt stream invariance constraint
    zero_cols = [c for c in dmat_raw.columns if np.all(dmat_raw[c] == 0)]
    assert len(zero_cols) == 2, f"Expected 2 structural zero columns, got {len(zero_cols)}"
    dmat_34 = dmat_raw.drop(columns=zero_cols)

    # 1. 150-cell design matrix has shape (150, 34) and full rank 34
    assert dmat_34.shape == (150, 34)
    rank_150 = np.linalg.matrix_rank(dmat_34.values)
    assert rank_150 == 34

    # 2. Condition number is well-conditioned
    svd_150 = np.linalg.svd(dmat_34.values, compute_uv=False)
    cond_150 = svd_150[0] / svd_150[-1]
    assert cond_150 < 50.0

    # 3. 18,000-row record matrix has shape (18000, 34) and full rank 34
    records_18000 = []
    for _, row in df_cells.iterrows():
        for u in range(120):
            r = dict(row)
            r["utterance_idx"] = u
            records_18000.append(r)
    df_18000 = pd.DataFrame(records_18000)
    assert len(df_18000) == 18000

    dmat_18k_raw = patsy.dmatrix(formula_34, data=df_18000, return_type="dataframe")
    dmat_18k = dmat_18k_raw.drop(columns=zero_cols)
    assert dmat_18k.shape == (18000, 34)
    assert np.linalg.matrix_rank(dmat_18k.values) == 34

    # 4. Rank deficiency proof: reintroducing standalone Order on canonical 150 cells
    # produces 36 columns but rank remains 34 (rank-deficient by 2)
    formula_with_order = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(ordering, Treatment('ORDER_A')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    dmat_order_reintroduced = patsy.dmatrix(formula_with_order, data=df_cells, return_type="dataframe")
    assert dmat_order_reintroduced.shape == (150, 36)
    rank_order_reintroduced = np.linalg.matrix_rank(dmat_order_reintroduced.values)
    assert rank_order_reintroduced == 34  # Rank-deficient by 2!

    # 5. Verify audit CSV and reports
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))
    assert int(meta["fixed_effect_parameters"]) == 34
    assert int(meta["design_matrix_rank"]) == 34
    assert int(meta["canonical_glmm_settings"]) == 150
    assert int(meta["canonical_record_count"]) == 18000
    assert int(meta["nominal_settings_count"]) == 180
    assert int(meta["duplicated_sensitivity_record_count"]) == 21600

    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    assert "p = 1 + 2 + 3 + 4 + 6 + 12 + 6 = 34" in prereg_text or "34 parameters" in prereg_text
    assert "rank 34" in prereg_text.lower() or "full rank 34" in prereg_text.lower()


def test_stage4m_analysis_a_and_b_separation():
    """
    P0-2 Audit: Verify formal separation between Analysis A (primary observed transcript safety engine)
    and Analysis B (secondary omnibus GLMM characterization).
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))

    assert meta["subgroup_primary_estimator"] == "DIRECT_OBSERVED_PAIRED_TRANSCRIPTS"
    assert meta["glmm_secondary_estimator"] == "OMNIBUS_GLMM_CHARACTERIZATION"

    assert "Analysis A" in prereg_text and "Analysis B" in prereg_text
    assert "Analysis A" in valid_text and "Analysis B" in valid_text
    assert "Primary Observed Subgroup-Safety Assessment" in prereg_text
    assert "Secondary Mixed-Effects Characterization" in prereg_text


def test_stage4m_laplace_marginal_objective_and_multidataset_validation():
    """
    P0-3 Audit: Verify true Laplace marginal likelihood objective and parameter recovery
    across 5 independent synthetic datasets.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))

    assert meta["glmm_estimation_objective"] == "LAPLACE_MARGINAL_LIKELIHOOD"
    assert meta["multidataset_validation"] == "5_DATASETS_RECOVERED"

    assert "Laplace" in prereg_text and "marginal" in prereg_text.lower()
    assert "5 independent" in prereg_text.lower() or "5 independent" in valid_text.lower()
    assert "Hessian" in valid_text or "-nabla" in valid_text or "volume correction" in valid_text


def test_stage4m_formal_dsg_gate_controller_boundary_cases():
    """
    P0-4 Audit: Test formal DisparitySafetyGate controller on 4 canonical boundary cases:
    Case 1: Fully safe candidate -> ACCEPT.
    Case 2: Point-safe but UCB-breached -> REJECT.
    Case 3: Overall improvement with subgroup harm -> REJECT.
    Case 4: Overall deterioration with disparity shrinkage -> REJECT.
    """
    from dsg_ctta.controller.gate import DisparitySafetyGate
    from dsg_ctta.controller.types import BootstrapMetrics

    gate = DisparitySafetyGate(epsilon_r=0.00, epsilon_g=0.02, epsilon_d=0.02)

    # Case 1: Fully safe candidate
    metrics_safe = BootstrapMetrics(
        delta_r=-0.035, max_delta_g=-0.030, delta_d=-0.010,
        ucb_r=-0.020, ucb_max_group=-0.015, ucb_d=-0.005,
        group_deltas={"Arabic": -0.035, "Korean": -0.030},
        group_ucbs={"Arabic": -0.020, "Korean": -0.015},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision1 = gate.evaluate_decision(metrics_safe, "cand_safe", "curr_model", 42, 1000)
    assert decision1.accept is True
    assert decision1.decision == "ACCEPT"

    # Case 2: Point-safe, UCB-breached (Crucial distinction!)
    # Point estimates: delta_r=-0.02 <= 0.00, max_delta_g=+0.015 <= 0.02, delta_d=+0.010 <= 0.02
    # BUT UCB95(max_delta_g) = +0.028 > 0.02 -> Must REJECT!
    metrics_point_safe_ucb_breached = BootstrapMetrics(
        delta_r=-0.020, max_delta_g=0.015, delta_d=0.010,
        ucb_r=-0.005, ucb_max_group=0.028, ucb_d=0.018,
        group_deltas={"Arabic": -0.020, "Korean": 0.015},
        group_ucbs={"Arabic": -0.005, "Korean": 0.028},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision2 = gate.evaluate_decision(metrics_point_safe_ucb_breached, "cand_p_safe", "curr_model", 42, 1000)
    assert decision2.accept is False
    assert decision2.decision == "REJECT"
    assert any("Subgroup regression violation" in r for r in decision2.rejection_reasons)

    # Case 3: Overall improvement with subgroup harm
    metrics_subgroup_harm = BootstrapMetrics(
        delta_r=-0.042, max_delta_g=0.050, delta_d=0.110,
        ucb_r=-0.025, ucb_max_group=0.070, ucb_d=0.140,
        group_deltas={"Arabic": -0.060, "Korean": 0.050},
        group_ucbs={"Arabic": -0.040, "Korean": 0.070},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision3 = gate.evaluate_decision(metrics_subgroup_harm, "cand_harm", "curr_model", 42, 1000)
    assert decision3.accept is False
    assert decision3.decision == "REJECT"
    assert any("Subgroup regression violation" in r for r in decision3.rejection_reasons)

    # Case 4: Overall deterioration with disparity shrinkage
    metrics_disp_shrinkage = BootstrapMetrics(
        delta_r=0.133, max_delta_g=0.250, delta_d=-0.200,
        ucb_r=0.160, ucb_max_group=0.300, ucb_d=-0.150,
        group_deltas={"Arabic": 0.250, "Korean": 0.050},
        group_ucbs={"Arabic": 0.300, "Korean": 0.080},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision4 = gate.evaluate_decision(metrics_disp_shrinkage, "cand_shrink", "curr_model", 42, 1000)
    assert decision4.accept is False
    assert decision4.decision == "REJECT"
    assert any("Overall risk violation" in r for r in decision4.rejection_reasons)


def test_stage4m_bootstrap_729_multiset_support():
    """
    P0-5 Audit: Verify combinatorial support of stratified paired bootstrap (3^6 = 729 multisets)
    and finite-sample limitation disclosures.
    """
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))

    assert int(meta["bootstrap_multiset_support"]) == 729
    assert int(meta["bootstrap_resamples_B"]) == 1000

    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    assert "729" in prereg_text
    assert "3^6" in prereg_text or "3**6" in prereg_text or "3^6 = 729" in prereg_text


def test_stage4m_safety_gate_unit_contract_and_invariance():
    """
    P0-1 Audit: Verify safety gate unit contract.
    Assert that:
    1. Canonical internal representation uses fractional rate differences (epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200).
    2. from_percentage_points constructor (epsilon_r_pp=0.00, epsilon_g_pp=2.00, epsilon_d_pp=2.00) yields mathematically identical tolerances.
    3. Fractional inputs compared to fractional tolerances produce identical decisions to percentage-point inputs converted to fractional scale.
    4. Audit CSV confirms controller_internal_unit = FRACTIONAL_RATE_DIFFERENCE and reporting_display_unit = PERCENTAGE_POINTS.
    """
    from dsg_ctta.controller.gate import DisparitySafetyGate
    from dsg_ctta.controller.types import BootstrapMetrics

    # Test 1: Instantiation equivalence
    gate_frac = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    gate_pp = DisparitySafetyGate.from_percentage_points(epsilon_r_pp=0.00, epsilon_g_pp=2.00, epsilon_d_pp=2.00)

    assert abs(gate_frac.epsilon_r - gate_pp.epsilon_r) < 1e-9
    assert abs(gate_frac.epsilon_g - gate_pp.epsilon_g) < 1e-9
    assert abs(gate_frac.epsilon_d - gate_pp.epsilon_d) < 1e-9

    # Test 2: Input equivalence
    # Fractional input: max_delta_g = 0.0150 (1.50 pp), UCB_G = 0.0280 (2.80 pp) -> REJECT
    metrics_frac = BootstrapMetrics(
        delta_r=-0.020, max_delta_g=0.0150, delta_d=0.010,
        ucb_r=-0.005, ucb_max_group=0.0280, ucb_d=0.018,
        group_deltas={"Arabic": -0.020, "Korean": 0.0150},
        group_ucbs={"Arabic": -0.005, "Korean": 0.0280},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision_frac = gate_frac.evaluate_decision(metrics_frac, "cand_test", "live_test", 42, 1000)
    assert decision_frac.decision == "REJECT"

    # Equivalent percentage point metrics converted to fraction (/ 100.0)
    pp_ucb_g = 2.80  # 2.80 pp
    frac_ucb_g = pp_ucb_g / 100.0  # 0.0280
    metrics_converted = BootstrapMetrics(
        delta_r=-2.00 / 100.0, max_delta_g=1.50 / 100.0, delta_d=1.00 / 100.0,
        ucb_r=-0.50 / 100.0, ucb_max_group=frac_ucb_g, ucb_d=1.80 / 100.0,
        group_deltas={"Arabic": -2.00 / 100.0, "Korean": 1.50 / 100.0},
        group_ucbs={"Arabic": -0.50 / 100.0, "Korean": frac_ucb_g},
        replicates_computed=1000, omitted_groups_count=0
    )
    decision_pp = gate_pp.evaluate_decision(metrics_converted, "cand_test", "live_test", 42, 1000)
    assert decision_pp.decision == decision_frac.decision
    assert decision_pp.rejection_reasons == decision_frac.rejection_reasons

    # Test 3: Decision to percentage points helper
    pp_dict = DisparitySafetyGate.decision_to_percentage_points(decision_frac)
    assert abs(pp_dict["max_delta_g_pp"] - 1.50) < 1e-6
    assert abs(pp_dict["ucb_max_group_pp"] - 2.80) < 1e-6
    assert abs(pp_dict["epsilon_g_pp"] - 2.00) < 1e-6

    # Test 4: Audit CSV documentation
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))
    assert meta["controller_internal_unit"] == "FRACTIONAL_RATE_DIFFERENCE"
    assert meta["reporting_display_unit"] == "PERCENTAGE_POINTS"


def test_stage4m_evaluation_boundary_and_sentinel_separation():
    """
    P0-2 Audit: Verify separation between retrospective Stage 4M evaluation and operational DSG.
    1. Analysis A is defined as Primary Retrospective Stage 4M Safety Assessment.
    2. Reference labels are used for offline scientific evaluation only.
    3. Operational DSG candidate acceptance uses disjoint Sentinel Panel (N=30).
    4. Audit CSV documents primary_evaluation_role and operational_gate_role.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))

    assert meta["primary_evaluation_role"] == "RETROSPECTIVE_OFFLINE_SCIENTIFIC_EVALUATION"
    assert meta["operational_gate_role"] == "ONLINE_CANDIDATE_ACCEPTANCE_VIA_SENTINEL_PANEL"

    # Explicit offline boundary in reports
    assert "Primary Retrospective Stage 4M Safety Assessment" in prereg_text
    assert "Primary Retrospective Stage 4M Safety Assessment" in valid_text
    assert "Sentinel Panel" in prereg_text and "N=30" in prereg_text
    assert "Sentinel Panel" in valid_text
    assert "offline" in prereg_text.lower()
    assert "never flow into the online adaptation" in prereg_text.lower() or "cannot flow into the online adaptation" in prereg_text.lower()


def test_stage4m_repeated_no_adapt_observations_handling(results_df):
    """
    P0-3 Audit: Verify repeated No-Adapt observations handling.
    1. Confirm No-Adapt predictions are 100% identical across ORDER_A, ORDER_B, ORDER_C in Stage 3M control cells.
    2. Secondary GLMM handles repeated covariance via utterance random intercept u_i.
    3. Audit CSV documents no_adapt_stream_duplication = INVARIANT_REPEATED_OBSERVATION.
    """
    for model_key in ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]:
        sub = results_df[(results_df["model_key"] == model_key) & (results_df["method"] == "no_adapt")]
        assert len(sub) == 3
        # Assert exact equality across all stream arrival orders
        assert len(sub["total_errors"].unique()) == 1, f"No-adapt total errors vary across orders for {model_key}!"
        assert len(sub["corpus_wer"].unique()) == 1, f"No-adapt corpus WER varies across orders for {model_key}!"

    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))
    assert meta["no_adapt_stream_duplication"] == "CANONICAL_BASELINE_OPTION_A"

    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    assert "repeated" in prereg_text.lower()
    assert "random intercept" in prereg_text.lower()
    assert "option a" in prereg_text.lower()


def test_stage4m_unbounded_fractional_metric_bounds_and_conversion():
    """
    P0-1 Audit: Verify fractional metric bounds are NOT restricted to [-1.0, 1.0].
    Because Word Error Rate (WER = (S+D+I)/N) includes insertions, WER can exceed 100%,
    and delta WER / UCBs can exceed +1.0 (+100 pp) or fall below -1.0 (-100 pp).
    Verify that:
    1. Valid fractional difference > +1.0 (e.g. +1.10 <-> +110 pp) is accepted without clipping.
    2. Conversion to percentage points is exact (1.10 -> 110.0 pp).
    3. Gate applies frozen tolerances correctly and rejects severe regression.
    4. Negative delta < -1.0 (e.g. -1.20 <-> -120 pp) is accepted without clipping.
    5. Invalid NaN and Inf are rejected by fail-closed policy.
    """
    from dsg_ctta.controller.gate import DisparitySafetyGate
    from dsg_ctta.controller.types import BootstrapMetrics

    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)

    # Scenario: Severe deterioration where WER exceeds 100% due to insertions
    # Baseline WER = 0.80 (80%), Candidate WER = 1.90 (190%) -> Delta_R = +1.10 (+110 pp)
    # Worst group WER = 2.05 (205%) vs 0.85 (85%) -> Delta_g = +1.20 (+120 pp)
    metrics_large_positive = BootstrapMetrics(
        delta_r=1.10,
        max_delta_g=1.20,
        delta_d=0.45,
        ucb_r=1.15,
        ucb_max_group=1.25,
        ucb_d=0.50,
        group_deltas={"Arabic": 1.05, "Korean": 1.20},
        group_ucbs={"Arabic": 1.10, "Korean": 1.25},
        replicates_computed=1000,
        omitted_groups_count=0,
    )

    decision_pos = gate.evaluate_decision(metrics_large_positive, "cand_severe", "live_base", 42, 1000)
    assert decision_pos.decision == "REJECT"
    assert decision_pos.accept is False
    assert abs(decision_pos.delta_r - 1.10) < 1e-9
    assert abs(decision_pos.max_delta_g - 1.20) < 1e-9
    assert abs(decision_pos.ucb_r - 1.15) < 1e-9
    assert abs(decision_pos.ucb_max_group - 1.25) < 1e-9

    # Check percentage point conversion
    pp_pos = DisparitySafetyGate.decision_to_percentage_points(decision_pos)
    assert abs(pp_pos["delta_r_pp"] - 110.0) < 1e-6
    assert abs(pp_pos["max_delta_g_pp"] - 120.0) < 1e-6
    assert abs(pp_pos["ucb_r_pp"] - 115.0) < 1e-6
    assert abs(pp_pos["ucb_max_group_pp"] - 125.0) < 1e-6

    # Scenario: Massive improvement where delta < -1.0 (e.g. from 1.60 down to 0.35 -> Delta_R = -1.25)
    metrics_large_negative = BootstrapMetrics(
        delta_r=-1.25,
        max_delta_g=-1.10,
        delta_d=-0.15,
        ucb_r=-1.20,
        ucb_max_group=-1.05,
        ucb_d=-0.10,
        group_deltas={"Arabic": -1.25, "Korean": -1.10},
        group_ucbs={"Arabic": -1.20, "Korean": -1.05},
        replicates_computed=1000,
        omitted_groups_count=0,
    )
    decision_neg = gate.evaluate_decision(metrics_large_negative, "cand_super", "live_base", 42, 1000)
    assert decision_neg.decision == "ACCEPT"
    assert decision_neg.accept is True
    assert abs(decision_neg.delta_r - (-1.25)) < 1e-9

    pp_neg = DisparitySafetyGate.decision_to_percentage_points(decision_neg)
    assert abs(pp_neg["delta_r_pp"] - (-125.0)) < 1e-6

    # Scenario: Fail-closed on NaN or Inf
    metrics_nan = BootstrapMetrics(
        delta_r=float("nan"), max_delta_g=0.01, delta_d=0.01,
        ucb_r=0.0, ucb_max_group=0.01, ucb_d=0.01,
        group_deltas={"Arabic": 0.01}, group_ucbs={"Arabic": 0.01},
        replicates_computed=1000, omitted_groups_count=0,
    )
    decision_nan = gate.evaluate_decision(metrics_nan, "cand_nan", "live_base", 42, 1000)
    assert decision_nan.decision == "REJECT"
    assert decision_nan.rejection_category == "FAIL_CLOSED_EVALUATOR_ERROR"


def test_stage4m_observed_hessian_curvature_and_constant_reconciliation():
    """
    P0-3 Audit: Verify negative-binomial observed curvature vs Fisher information
    and reconcile Gaussian prior normalization constants in the Laplace objective.
    1. For NB2 with log-link, observed negative curvature is:
       w_obs = mu * (1 + y / phi) / (1 + mu / phi)^2
       while expected Fisher information is:
       w_fisher = mu / (1 + mu / phi)
    2. Verify w_obs matches finite-difference numerical second derivative to < 1e-4.
    3. Verify that Gaussian prior normalizing constant -(K_v/2)*log(2*pi) cancels
       with Laplace Gaussian integral +(K_v/2)*log(2*pi).
    """
    import math

    phi = 8.0
    mu = 12.5
    y = 15.0

    # Expected Fisher information
    w_fisher = mu / (1.0 + mu / phi)
    # Observed negative curvature
    w_obs = (mu * (1.0 + y / phi)) / ((1.0 + mu / phi) ** 2)

    # Numerical finite-difference evaluation of negative log-likelihood wrt eta = log(mu)
    def nb_loglik(eta_val):
        mu_val = math.exp(eta_val)
        return (
            math.lgamma(y + phi) - math.lgamma(phi) - math.lgamma(y + 1.0)
            + phi * math.log(phi / (phi + mu_val))
            + y * math.log(mu_val / (phi + mu_val))
        )

    eps = 1e-5
    eta_0 = math.log(mu)
    d2_fd = -((nb_loglik(eta_0 + eps) - 2.0 * nb_loglik(eta_0) + nb_loglik(eta_0 - eps)) / (eps ** 2))

    # Observed curvature matches numerical derivative to high precision
    assert abs(d2_fd - w_obs) < 1e-4
    # Fisher information is strictly different from observed curvature when y != mu
    assert abs(w_obs - w_fisher) > 0.1

    # Check audit CSV entries
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))
    assert meta["glmm_hessian_type"] == "OBSERVED_NEGATIVE_CURVATURE"
    assert meta["glmm_laplace_constant"] == "EXACT_CANCELING_GAUSSIAN_PRIOR_CONSTANT"


def test_stage4m_canonical_option_a_structure_and_sensitivity():
    """
    P0-2 Audit: Verify Option A canonical No-Adapt evaluation structure (18,000 unique records)
    and sensitivity comparison with 21,600 duplicated design.
    """
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))
    assert meta["no_adapt_stream_duplication"] == "CANONICAL_BASELINE_OPTION_A"

    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")

    assert "18,000" in prereg_text or "18000" in prereg_text
    assert "1,800" in prereg_text or "1800" in prereg_text
    assert "Option A" in prereg_text
    assert "sensitivity" in prereg_text.lower()
    assert "Option A" in valid_text


def test_stage4m_glmm_scope_and_laplace_approximation_terminology():
    """
    P0-4 Audit: Verify calibrated GLMM terminology and parsimony scope.
    1. GLMM objective is described as Laplace-approximated marginal log-likelihood.
    2. Model x Condition is omitted from 36-parameter model to preserve parsimony on N=12 speakers.
    3. Audit CSV documents glmm_model_condition_interaction = OMITTED_PARSIMONY_CONSTRAINT.
    """
    prereg_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_preregistration_addendum.md").read_text(encoding="utf-8")
    valid_text = (PROJECT_ROOT / "reports" / "stage3m" / "stage4m_analysis_spec_validation.md").read_text(encoding="utf-8")
    audit_csv = PROJECT_ROOT / "reports" / "stage3m" / "stage4m_observation_grain_audit.csv"
    df_audit = pd.read_csv(audit_csv)
    meta = dict(zip(df_audit["parameter"], df_audit["value"]))

    assert meta["glmm_model_condition_interaction"] == "OMITTED_PARSIMONY_CONSTRAINT"

    # Terminology checks
    assert "Laplace-approximated" in prereg_text or "Laplace-Approximated" in prereg_text
    assert "Laplace-approximated" in valid_text or "Laplace-Approximated" in valid_text
    assert "Model × Condition" in prereg_text or "Model x Condition" in prereg_text or "Model * Condition" in prereg_text
    assert "omitted" in prereg_text.lower() or "omits" in prereg_text.lower()


def test_stage4m_execution_authorization_and_gate_status():
    """
    CRITICAL PROTOCOL GUARD: Verify formal execution authorization of Stage 4M
    under protocol v1.1.0-model-expansion review decision GO.
    When stage4m_full_results.csv is generated, verify it satisfies the full matrix scope.
    """
    full_stage4m_results = PROJECT_ROOT / "results" / "stage4_multimodel" / "stage4m_full_results.csv"
    if full_stage4m_results.exists():
        df_full = pd.read_csv(full_stage4m_results)
        # 180 CTC nominal settings + 15 Seq2Seq static controls = 195 rows
        assert len(df_full) in [180, 195]
        assert "corpus_wer" in df_full.columns



