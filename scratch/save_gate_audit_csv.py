import pandas as pd
from pathlib import Path

results_base = Path("results/stage4_multimodel")
df_boot = pd.read_csv(results_base / "stage4m_bootstrap_uncertainty.csv")

audit_rows = []
for idx, r in df_boot.iterrows():
    audit_rows.append({
        "setting_id": f"{r['model_key']}_{r['condition']}_{r['method']}_{r['ordering_id'].lower()}",
        "model_key": r["model_key"],
        "condition": r["condition"],
        "method": r["method"],
        "ordering_id": r["ordering_id"],
        "decision_type": "RETROSPECTIVE_SAFETY_CLASSIFICATION",
        "eval_data_source": "STAGE4M_GROUND_TRUTH_TRANSCRIPTS",
        "decision_timing": "POST_RUN_RETROSPECTIVE",
        "unit_of_analysis": "COMPLETED_RUN_120_UTTERANCES",
        "reference_words": 1104,
        "speakers_count": 12,
        "bootstrap_replicates_b": 1000,
        "gate_decision": r["gate_decision"],
        "point_delta_r_pp": r["point_delta_r_pp"],
        "ucb95_delta_r_pp": r["ucb95_delta_r_pp"],
        "point_max_delta_g_pp": r["point_max_delta_g_pp"],
        "ucb95_max_delta_g_pp": r["ucb95_max_delta_g_pp"],
        "point_delta_d_pp": r["point_delta_d_pp"],
        "ucb95_delta_d_pp": r["ucb95_delta_d_pp"],
        "rejection_reasons": r["rejection_reasons"],
        "operational_sentinel_isolation": "PRESERVED_NO_ONLINE_LEAKAGE"
    })

df_audit = pd.DataFrame(audit_rows)
out_csv = results_base / "stage4m_retrospective_vs_operational_audit.csv"
df_audit.to_csv(out_csv, index=False)
print(f"Saved {len(df_audit)} retrospective safety audit records to: {out_csv}")
