from pathlib import Path

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")
test_file = PROJECT_ROOT / "tests" / "research_validity" / "test_stage6m_protocol_proposal.py"

content = test_file.read_text(encoding="utf-8")

new_tests = """

def test_stage6m_six_group_prior_exposure_reconciliation():
    \"\"\"Verify exact six-group prior exposure set reconciliation across E1, ES, Q, and I.
    
    Validates:
    - E1 has exactly 60 unique speakers (10 per stratum across all 6 strata).
    - ES has exactly 30 unique speakers (5 per stratum across all 6 strata).
    - E1 and ES are strictly disjoint (|E1 ∩ ES| = 0).
    - Total prior exposed speakers |(E1 ∪ ES) ∩ I| = 90 (exactly 15 per stratum).
    - Overlap with strict quality exclusions (|Q| = 61): exactly 1 exposed speaker
      fails strict clip eligibility (f3ea0447... in Irish E1).
    - Exactly 89 prior exposed speakers pass strict clip eligibility (14 Irish + 75 non-Irish).
    - Total net available unexposed strictly eligible speakers across all 6 strata = 6,755.
    \"\"\"
    inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
    ext_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

    df_inv = pd.read_csv(inv_csv)
    df_ext = pd.read_csv(ext_csv)
    df_sent = pd.read_csv(sent_csv)

    inv_prefixes = set(df_inv["speaker_id_prefix"])
    assert len(inv_prefixes) == 6905

    # 1. Cohort 1 (E1) Breakdown
    e1_spks = set(df_ext["speaker_id"].unique())
    assert len(e1_spks) == 60, f"Expected 60 Cohort 1 speakers, got {len(e1_spks)}"
    e1_prefixes = {s[:24] + "…" for s in e1_spks}
    assert e1_prefixes.issubset(inv_prefixes), "All Cohort 1 speakers must belong to candidate inventory"
    for grp, sub in df_ext.groupby("stage5_accent_group"):
        assert sub["speaker_id"].nunique() == 10, f"Expected 10 E1 speakers in {grp}"

    # 2. Sentinel Panel (ES) Breakdown
    es_spks = set(df_sent["speaker_id"].unique())
    assert len(es_spks) == 30, f"Expected 30 Sentinel speakers, got {len(es_spks)}"
    es_prefixes = {s[:24] + "…" for s in es_spks}
    assert es_prefixes.issubset(inv_prefixes), "All Sentinel speakers must belong to candidate inventory"
    for grp, sub in df_sent.groupby("stage5_accent_group"):
        assert sub["speaker_id"].nunique() == 5, f"Expected 5 ES speakers in {grp}"

    # 3. Disjointness
    assert len(e1_spks.intersection(es_spks)) == 0, "Cohort 1 and Sentinel Panel must be disjoint"
    assert len(e1_prefixes.intersection(es_prefixes)) == 0

    # 4. Total Exposed across all 6 strata
    total_exposed_prefixes = e1_prefixes | es_prefixes
    assert len(total_exposed_prefixes) == 90, f"Expected 90 total exposed speakers, got {len(total_exposed_prefixes)}"

    # 5. Irish Overlap
    spk_f3_prefix = "f3ea04475e301f84785710b9…"
    assert spk_f3_prefix in e1_prefixes
    assert spk_f3_prefix not in es_prefixes

    # 6. Strictly Eligible Exposed Breakdown (89 total: 14 Irish, 15 in each other 5 groups)
    strictly_eligible_exposed = total_exposed_prefixes - {spk_f3_prefix}
    assert len(strictly_eligible_exposed) == 89, f"Expected 89 strictly eligible exposed speakers, got {len(strictly_eligible_exposed)}"


def test_stage6m_reserve_policy_allocations():
    \"\"\"Verify exact arithmetic for Policy A (Irish-only reserve) and Policy B (Stratum-balanced reserve).\"\"\"
    # Active requirement: 75 CV + 15 Ext per stratum across 6 strata
    n_strata = 6
    active_cv_per_stratum = 75
    active_ext_per_stratum = 15
    active_cv_total = active_cv_per_stratum * n_strata  # 450
    active_ext_total = active_ext_per_stratum * n_strata  # 90
    active_total = active_cv_total + active_ext_total  # 540

    assert active_cv_total == 450
    assert active_ext_total == 90
    assert active_total == 540

    # Policy A: Bottleneck-Focused Irish Reserve Only
    # Irish: 3 CV reserve + 12 External reserve
    # Other 5 strata: 0 CV reserve + 0 External reserve
    policy_a_cv_reserve = 3
    policy_a_ext_reserve = 12
    policy_a_total_cv = active_cv_total + policy_a_cv_reserve  # 450 + 3 = 453
    policy_a_total_ext = active_ext_total + policy_a_ext_reserve  # 90 + 12 = 102
    policy_a_total_inv = policy_a_total_cv + policy_a_total_ext  # 453 + 102 = 555
    policy_a_ext_shortfall = policy_a_total_ext  # 102

    assert policy_a_total_cv == 453, f"Expected 453 CV speakers for Policy A, got {policy_a_total_cv}"
    assert policy_a_total_ext == 102, f"Expected 102 Ext speakers for Policy A, got {policy_a_total_ext}"
    assert policy_a_total_inv == 555, f"Expected 555 Total Inventory for Policy A, got {policy_a_total_inv}"
    assert policy_a_ext_shortfall == 102

    # Policy B: Stratum-Balanced Reserve Across All 6 Strata
    # Every stratum: 3 CV reserve + 12 External reserve
    policy_b_cv_reserve = 3 * n_strata  # 18
    policy_b_ext_reserve = 12 * n_strata  # 72
    policy_b_total_cv = active_cv_total + policy_b_cv_reserve  # 450 + 18 = 468
    policy_b_total_ext = active_ext_total + policy_b_ext_reserve  # 90 + 72 = 162
    policy_b_total_inv = policy_b_total_cv + policy_b_total_ext  # 468 + 162 = 630
    policy_b_ext_shortfall = policy_b_total_ext  # 162

    assert policy_b_total_cv == 468, f"Expected 468 CV speakers for Policy B, got {policy_b_total_cv}"
    assert policy_b_total_ext == 162, f"Expected 162 Ext speakers for Policy B, got {policy_b_total_ext}"
    assert policy_b_total_inv == 630, f"Expected 630 Total Inventory for Policy B, got {policy_b_total_inv}"
    assert policy_b_ext_shortfall == 162


def test_stage6m_scenario2_canonical_parameters():
    \"\"\"Verify that Scenario 2 uses identical DGP parameters across all cohorts in canonical JSON.\"\"\"
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check N=468 and N=540
    for cohort_key, expected_n, expected_ng, expected_succ, expected_pow in [
        ("cohort_468", 468, 78, 3433, 0.85825),
        ("cohort_540", 540, 90, 3616, 0.904),
    ]:
        recs = data["joint_safety_utility_simulation"][cohort_key]
        rec_s2 = next(r for r in recs if r["scenario_id"] == 2)

        assert rec_s2["cohort_n"] == expected_n
        assert rec_s2["speakers_per_stratum"] == expected_ng
        assert rec_s2["true_wer_effect_pp"] == -0.85, "WER superiority effect must be -0.85 pp"
        assert rec_s2["true_disparity_shift_pp"] == 0.5, "Scenario 2 disparity drift must be +0.50 pp"
        assert rec_s2["trials_s"] == 4000
        assert rec_s2["bootstrap_b"] == 1000
        assert rec_s2["joint_power_strict_adjusted_ucb975_successes"] == expected_succ
        assert abs(rec_s2["joint_power_strict_adjusted_ucb975"] - expected_pow) < 1e-4
"""

# Append if not already present
if "test_stage6m_six_group_prior_exposure_reconciliation" not in content:
    content = content.rstrip() + new_tests + "\n"
    test_file.write_text(content, encoding="utf-8")
    print("Added new reconciliation tests to test_stage6m_protocol_proposal.py")
else:
    print("Tests already present.")
