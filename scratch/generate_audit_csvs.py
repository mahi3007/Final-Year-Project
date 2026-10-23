import json
import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(".").resolve()
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5m"
RESULTS_DIR = PROJECT_ROOT / "results" / "stage5m"
CK_DIR = RESULTS_DIR / "checkpoints"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# DELIVERABLE 1: stage5m_run_window_accounting.csv
# -------------------------------------------------------------------------
print("Generating stage5m_run_window_accounting.csv...")
ck_files = sorted(CK_DIR.glob("STAGE5M_*.json"))

accounting_rows = []
for ck in ck_files:
    with open(ck, "r", encoding="utf-8") as f:
        data = json.load(f)
    s = data.get("summary", {})
    preds = data.get("predictions", [])
    ops = data.get("operational_decisions", [])
    
    exp_id = s.get("experiment_id", ck.stem)
    model = s.get("model_key")
    cond = s.get("condition")
    method = s.get("method")
    order = s.get("ordering_id")
    
    expected_windows = 30
    actual_windows = len(ops)
    actual_preds = len(preds)
    
    # Active candidate evaluations
    active_evals = len([d for d in ops if d.get("decision") in ["ACCEPT", "REJECT"]])
    n_accept = len([d for d in ops if d.get("decision") == "ACCEPT"])
    n_reject = len([d for d in ops if d.get("decision") == "REJECT"])
    candidate_proposals = s.get("total_candidates", 0)
    
    # Terminal window action
    if actual_windows >= 30:
        last_op = ops[-1]
        terminal_action = f"PREDICTION_ONLY_NO_UPDATE (window_id={last_op.get('window_id')})"
    elif actual_windows == 2:
        terminal_action = f"TRUNCATED_SMOKE_TEST (stopped_at_window_1)"
    else:
        terminal_action = f"PARTIAL (stopped_at_window_{actual_windows-1})"
        
    missing = expected_windows - actual_windows
    if missing == 0:
        missing_reason = "NONE (Full 30-window stream complete)"
    else:
        missing_reason = f"PREFLIGHT_SMOKE_TEST_CHECKPOINT_NOT_OVERWRITTEN (2 windows evaluated; full run resumed past existing checkpoint)"
        
    accounting_rows.append({
        "run_id": exp_id,
        "model_key": model,
        "acoustic_condition": cond,
        "adaptation_method": method,
        "stream_order": order,
        "expected_windows": expected_windows,
        "actual_windows": actual_windows,
        "actual_prediction_rows": actual_preds,
        "candidate_proposals": candidate_proposals,
        "gate_evaluations": active_evals,
        "accepted_candidates": n_accept,
        "rejected_candidates": n_reject,
        "applied_updates": n_accept,
        "terminal_window_action": terminal_action,
        "missing_records": missing,
        "reconciliation_status": missing_reason,
        "stream_total_words": s.get("total_words"),
        "stream_total_errors": s.get("total_errors"),
        "final_wer": s.get("final_wer"),
        "final_disparity_pp": round(s.get("final_disparity", 0.0) * 100, 2)
    })

df_acc = pd.DataFrame(accounting_rows)
out_acc = REPORTS_DIR / "stage5m_run_window_accounting.csv"
df_acc.to_csv(out_acc, index=False)
print(f"Saved {out_acc} ({len(df_acc)} rows). Total windows: {df_acc['actual_windows'].sum()}, Total gate evals: {df_acc['gate_evaluations'].sum()}")

# -------------------------------------------------------------------------
# DELIVERABLE 2: stage5m_baseline_provenance_reconciliation.csv
# -------------------------------------------------------------------------
print("Generating stage5m_baseline_provenance_reconciliation.csv...")

baseline_rows = [
    {
        "evaluation_stage": "Stage 4M (Canonical Multi-Model Characterization)",
        "model_key": "wav2vec2_base",
        "acoustic_condition": "clean",
        "adaptation_method": "no_adapt",
        "stream_order": "ORDER_A",
        "checkpoint_revision": "facebook/wav2vec2-base-960h (HuggingFace)",
        "source_dataset_partition": "datasets/splits/stage4_characterization.csv",
        "speakers_evaluated": 12,
        "accents_represented": 6,
        "utterances_evaluated": 120,
        "reference_words": 1104,
        "substitutions": 768,
        "deletions": 135,
        "insertions": 67,
        "total_errors": 970,
        "wer_percent": 87.86,
        "disparity_pp": 8.15,
        "provenance_notes": "Canonical full 120-utterance static baseline across 12 speakers and 6 accent groups."
    },
    {
        "evaluation_stage": "Stage 5M (Raw Checkpoint: STAGE5M_wav2vec2_base_clean_no_adapt_order_a_k4.json)",
        "model_key": "wav2vec2_base",
        "acoustic_condition": "clean",
        "adaptation_method": "no_adapt",
        "stream_order": "ORDER_A",
        "checkpoint_revision": "facebook/wav2vec2-base-960h (HuggingFace)",
        "source_dataset_partition": "datasets/splits/stage4_characterization.csv (truncated to 2 windows)",
        "speakers_evaluated": 1,
        "accents_represented": 1,
        "utterances_evaluated": 8,
        "reference_words": 74,
        "substitutions": 58,
        "deletions": 1,
        "insertions": 4,
        "total_errors": 63,
        "wer_percent": 85.14,
        "disparity_pp": 0.00,
        "provenance_notes": "PROVENANCE DEFECT: Checkpoint generated during preflight '--smoke-test' (2 windows / 8 utterances of speaker ABA only). Kaggle master benchmark resumed past existing checkpoint and did not overwrite it."
    },
    {
        "evaluation_stage": "Stage 5M (Zero-Update Control: STAGE5M_wav2vec2_base_clean_dsuta_order_a_k4.json)",
        "model_key": "wav2vec2_base",
        "acoustic_condition": "clean",
        "adaptation_method": "dsuta (0 updates accepted -> 100% static weights)",
        "stream_order": "ORDER_A",
        "checkpoint_revision": "facebook/wav2vec2-base-960h (HuggingFace)",
        "source_dataset_partition": "datasets/splits/stage4_characterization.csv",
        "speakers_evaluated": 12,
        "accents_represented": 6,
        "utterances_evaluated": 120,
        "reference_words": 1104,
        "substitutions": 768,
        "deletions": 135,
        "insertions": 67,
        "total_errors": 970,
        "wer_percent": 87.86,
        "disparity_pp": 8.15,
        "provenance_notes": "RECONCILED STATIC CONTROL: Under closed-loop control, dsuta accepted 0/29 updates (theta_hash: 5272cc15fda04952 frozen throughout). Raw utterance hypotheses and error counts are 100.0% identical to Stage 4M."
    },
    {
        "evaluation_stage": "Stage 4M (Canonical Multi-Model Characterization)",
        "model_key": "data2vec_base",
        "acoustic_condition": "clean",
        "adaptation_method": "no_adapt",
        "stream_order": "ORDER_A",
        "checkpoint_revision": "facebook/data2vec-audio-base-960h (HuggingFace)",
        "source_dataset_partition": "datasets/splits/stage4_characterization.csv",
        "speakers_evaluated": 12,
        "accents_represented": 6,
        "utterances_evaluated": 120,
        "reference_words": 1104,
        "substitutions": 738,
        "deletions": 141,
        "insertions": 46,
        "total_errors": 925,
        "wer_percent": 83.79,
        "disparity_pp": 13.59,
        "provenance_notes": "Canonical full 120-utterance static baseline."
    },
    {
        "evaluation_stage": "Stage 5M (Logged Checkpoint: STAGE5M_data2vec_base_clean_no_adapt_order_a_k4.json)",
        "model_key": "data2vec_base",
        "acoustic_condition": "clean",
        "adaptation_method": "no_adapt",
        "stream_order": "ORDER_A",
        "checkpoint_revision": "facebook/data2vec-audio-base-960h (HuggingFace)",
        "source_dataset_partition": "datasets/splits/stage4_characterization.csv",
        "speakers_evaluated": 12,
        "accents_represented": 6,
        "utterances_evaluated": 120,
        "reference_words": 1104,
        "substitutions": 738,
        "deletions": 141,
        "insertions": 46,
        "total_errors": 925,
        "wer_percent": 83.79,
        "disparity_pp": 13.59,
        "provenance_notes": "100% exact match between Stage 4M and Stage 5M (run completed in full benchmark without smoke-test truncation)."
    }
]

df_base = pd.DataFrame(baseline_rows)
out_base = REPORTS_DIR / "stage5m_baseline_provenance_reconciliation.csv"
df_base.to_csv(out_base, index=False)
print(f"Saved {out_base} ({len(df_base)} rows).")

# -------------------------------------------------------------------------
# DELIVERABLE 3: stage5m_retrospective_label_definition.csv
# -------------------------------------------------------------------------
print("Generating stage5m_retrospective_label_definition.csv...")

label_def_rows = [
    {
        "dimension": "ACCURACY_EFFECT",
        "classification_category": "BENEFICIAL",
        "operational_scope": "Candidate-level update vs current deployed live model theta_t",
        "evaluation_data": "Quarantined test-stream window (K=4 utterances)",
        "mathematical_rule": "Delta_Errors = cand_test_errors - live_test_errors < 0 (Delta_WER < 0.0 pp)",
        "uncertainty_policy": "Point estimate on window word count",
        "neutrality_interval": "Strictly Delta_Errors == 0",
        "subgroup_constraints": "None (pure accuracy effect on local window)",
        "description": "Candidate model produces strictly fewer word errors than live model on the quarantined test window."
    },
    {
        "dimension": "ACCURACY_EFFECT",
        "classification_category": "NEUTRAL",
        "operational_scope": "Candidate-level update vs current deployed live model theta_t",
        "evaluation_data": "Quarantined test-stream window (K=4 utterances)",
        "mathematical_rule": "Delta_Errors = cand_test_errors - live_test_errors == 0 (Delta_WER == 0.0 pp)",
        "uncertainty_policy": "Point estimate on window word count",
        "neutrality_interval": "Strictly Delta_Errors == 0",
        "subgroup_constraints": "None (pure accuracy effect on local window)",
        "description": "Candidate model produces exactly identical word error count as live model on the quarantined test window."
    },
    {
        "dimension": "ACCURACY_EFFECT",
        "classification_category": "HARMFUL",
        "operational_scope": "Candidate-level update vs current deployed live model theta_t",
        "evaluation_data": "Quarantined test-stream window (K=4 utterances)",
        "mathematical_rule": "Delta_Errors = cand_test_errors - live_test_errors > 0 (Delta_WER > 0.0 pp)",
        "uncertainty_policy": "Point estimate on window word count",
        "neutrality_interval": "Strictly Delta_Errors == 0",
        "subgroup_constraints": "None (pure accuracy effect on local window)",
        "description": "Candidate model produces strictly more word errors than live model on the quarantined test window."
    },
    {
        "dimension": "TRIPARTITE_SAFETY_GATE",
        "classification_category": "OPERATIONAL_ACCEPT",
        "operational_scope": "Frozen Sentinel Panel (N=30 speakers, 300 clips, Common Voice 27.0)",
        "evaluation_data": "Pre-adaptation sentinel panel vs Candidate on sentinel panel",
        "mathematical_rule": "(UCB_R <= 0.00 pp) AND (UCB_max_g <= +2.00 pp) AND (UCB_D <= +2.00 pp)",
        "uncertainty_policy": "B=1000 paired speaker-clustered bootstrap, 95% one-sided upper confidence bound",
        "neutrality_interval": "epsilon_R = 0.00 pp, epsilon_G = +2.00 pp, epsilon_D = +2.00 pp",
        "subgroup_constraints": "Enforces overall risk, maximum group degradation, and disparity expansion bounds simultaneously",
        "description": "Operational candidate meets all three frozen safety criteria with 95% bootstrap confidence; model updated."
    },
    {
        "dimension": "TRIPARTITE_SAFETY_GATE",
        "classification_category": "OPERATIONAL_REJECT",
        "operational_scope": "Frozen Sentinel Panel (N=30 speakers, 300 clips, Common Voice 27.0)",
        "evaluation_data": "Pre-adaptation sentinel panel vs Candidate on sentinel panel",
        "mathematical_rule": "(UCB_R > 0.00 pp) OR (UCB_max_g > +2.00 pp) OR (UCB_D > +2.00 pp)",
        "uncertainty_policy": "B=1000 paired speaker-clustered bootstrap, 95% one-sided upper confidence bound",
        "neutrality_interval": "epsilon_R = 0.00 pp, epsilon_G = +2.00 pp, epsilon_D = +2.00 pp",
        "subgroup_constraints": "Any single violation triggers fail-closed statistical rejection",
        "description": "Operational candidate exceeds one or more frozen risk thresholds; candidate discarded, live model retained."
    }
]

df_label = pd.DataFrame(label_def_rows)
out_label = REPORTS_DIR / "stage5m_retrospective_label_definition.csv"
df_label.to_csv(out_label, index=False)
print(f"Saved {out_label} ({len(df_label)} rows).")

print("\nAll 3 audit deliverables generated successfully!")
