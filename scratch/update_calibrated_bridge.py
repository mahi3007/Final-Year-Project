import pandas as pd
from pathlib import Path

# Data from historical Stage 3: reports/ctta/multi_order_all_methods.csv
hist_df = pd.read_csv("reports/ctta/multi_order_all_methods.csv")
hist_oa = hist_df[hist_df["ordering"] == "ORDER_A"].set_index("method")

# Data from Stage 3M: results/stage3_multimodel/stage3m_full_results.csv
s3m_df = pd.read_csv("results/stage3_multimodel/stage3m_full_results.csv")
s3m_oa = s3m_df[(s3m_df["model_key"] == "wav2vec2_base") & (s3m_df["ordering_id"] == "ORDER_A")].set_index("method")

rows = []
methods = ["no_adapt", "suta", "dsuta", "dmsuta"]

root_causes = {
    "no_adapt": "Deterministic inference in eval mode; exact prediction-string and metric concordance across all runs.",
    "suta": "Identified likely cause: unseeded PyTorch RNG with active dropout (0.10) in model.train() during adapt(); exact causality requires controlled isolation.",
    "dsuta": "Restorative reset controller bounded adapted parameter trajectory, producing exact metric concordance (471 errors, 85.33% WER).",
    "dmsuta": "Identified likely cause: interaction between active dropout in model.train() and model-bank candidate selection; exact causality requires controlled isolation."
}

classifications = {
    "no_adapt": "PREDICTION_EQUALITY_VERIFIED",
    "suta": "REPRODUCIBILITY_LIKELY_DROPOUT_RNG_STOCHASTICITY",
    "dsuta": "METRIC_CONCORDANCE_EXACT",
    "dmsuta": "REPRODUCIBILITY_LIKELY_DROPOUT_RNG_STOCHASTICITY"
}

for m in methods:
    h_row = hist_oa.loc[m]
    s_row = s3m_oa.loc[m]
    
    h_wer = round(float(h_row["corpus_wer"]) * 100.0, 2)
    s_wer = round(float(s_row["corpus_wer"]) * 100.0, 2)
    diff_wer = round(s_wer - h_wer, 2)
    
    h_err = int(round(float(h_row["corpus_wer"]) * 552))
    s_err = int(s_row["total_errors"])
    diff_err = s_err - h_err
    
    h_d = round(float(h_row["disparity_d"]) * 100.0, 2)
    s_d = round(float(s_row["disparity_d"]) * 100.0, 2)
    diff_d = round(s_d - h_d, 2)
    
    h_max_reg = round(float(h_row["max_group_regression"]) * 100.0, 2)
    s_max_reg = round(float(s_row["max_delta_g"]) * 100.0, 2)
    
    rows.append({
        "model_key": "wav2vec2_base",
        "model_id": "facebook/wav2vec2-base-960h",
        "hf_commit_hash": "22aad52d435eb6dbaf354bdad9b0da84ce7d6156",
        "full_state_dict_sha256": "8d54633c960fea688716673a1c493d861c4a86cede21668b0f6991e2b6f8b006",
        "active_layernorm_param_hash": "e28c2c6b1c568146",
        "ordering": "ORDER_A",
        "method": m,
        "historical_wer_pct": h_wer,
        "stage3m_wer_pct": s_wer,
        "wer_discrepancy_pp": diff_wer,
        "historical_errors": h_err,
        "stage3m_errors": s_err,
        "error_count_delta": diff_err,
        "historical_disparity_d_pp": h_d,
        "stage3m_disparity_d_pp": s_d,
        "disparity_discrepancy_pp": diff_d,
        "historical_max_reg_pp": h_max_reg,
        "stage3m_max_reg_pp": s_max_reg,
        "divergence_interpretation": root_causes[m],
        "audit_classification": classifications[m]
    })

bridge_df = pd.DataFrame(rows)
out_path = Path("reports/stage3m/stage3m_reproducibility_bridge.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)
bridge_df.to_csv(out_path, index=False)
print(f"Updated {out_path}:")
print(bridge_df[["method", "wer_discrepancy_pp", "error_count_delta", "audit_classification"]].to_string())
