import pandas as pd
from pathlib import Path

results_base = Path("results/stage4_multimodel")
df_k = pd.read_csv(results_base / "stage4m_k_sweep_results.csv")
df_canon = pd.read_csv(results_base / "stage4m_canonical_results.csv")

# Extract corresponding K=4 standard runs from canonical results
k4_clean = df_canon[(df_canon["model_key"] == "wav2vec2_base") & (df_canon["condition"] == "clean") & (df_canon["method"] == "suta") & (df_canon["ordering_id"] == "ORDER_A")].iloc[0]
k4_noise5 = df_canon[(df_canon["model_key"] == "wav2vec2_base") & (df_canon["condition"] == "noise_5db") & (df_canon["method"] == "suta") & (df_canon["ordering_id"] == "ORDER_A")].iloc[0]
k4_reverb = df_canon[(df_canon["model_key"] == "wav2vec2_base") & (df_canon["condition"] == "reverb_t60_04") & (df_canon["method"] == "suta") & (df_canon["ordering_id"] == "ORDER_A")].iloc[0]

k_rows = []
# K=2
for idx, r in df_k[df_k["window_size_k"] == 2].iterrows():
    k_rows.append({
        "model_key": r["model_key"],
        "method": r["method"],
        "ordering_id": "ORDER_A",
        "condition": r["condition"],
        "window_size_k": 2,
        "total_windows": 60,
        "utterances_count": 120,
        "reference_words": 1104,
        "speakers_count": 12,
        "corpus_wer_fraction": r["corpus_wer"],
        "corpus_wer_pct": round(r["corpus_wer"] * 100.0, 2),
        "disparity_d_fraction": r["disparity_d"],
        "disparity_d_pp": round(r["disparity_d"] * 100.0, 2),
        "protocol_classification": "EXPLORATORY_SENSITIVITY",
        "historical_k_protocol": "Stage 4 used K={1,4,5,10}; Stage 4M Preregistration Addendum line 34 documented exploratory K={2,4,8}"
    })

# K=4 (Standard canonical run)
for k4_r in [k4_clean, k4_noise5, k4_reverb]:
    k_rows.append({
        "model_key": k4_r["model_key"],
        "method": k4_r["method"],
        "ordering_id": "ORDER_A",
        "condition": k4_r["condition"],
        "window_size_k": 4,
        "total_windows": 30,
        "utterances_count": 120,
        "reference_words": 1104,
        "speakers_count": 12,
        "corpus_wer_fraction": k4_r["corpus_wer"],
        "corpus_wer_pct": round(k4_r["corpus_wer"] * 100.0, 2),
        "disparity_d_fraction": k4_r["disparity_d"],
        "disparity_d_pp": round(k4_r["disparity_d"] * 100.0, 2),
        "protocol_classification": "CANONICAL_BENCHMARK_K4",
        "historical_k_protocol": "Preregistered standard streaming window size K=4 across all 150 canonical settings"
    })

# K=8
for idx, r in df_k[df_k["window_size_k"] == 8].iterrows():
    k_rows.append({
        "model_key": r["model_key"],
        "method": r["method"],
        "ordering_id": "ORDER_A",
        "condition": r["condition"],
        "window_size_k": 8,
        "total_windows": 15,
        "utterances_count": 120,
        "reference_words": 1104,
        "speakers_count": 12,
        "corpus_wer_fraction": r["corpus_wer"],
        "corpus_wer_pct": round(r["corpus_wer"] * 100.0, 2),
        "disparity_d_fraction": r["disparity_d"],
        "disparity_d_pp": round(r["disparity_d"] * 100.0, 2),
        "protocol_classification": "EXPLORATORY_SENSITIVITY",
        "historical_k_protocol": "Stage 4 used K={1,4,5,10}; Stage 4M Preregistration Addendum line 34 documented exploratory K={2,4,8}"
    })

df_k_audit = pd.DataFrame(k_rows).sort_values(by=["condition", "window_size_k"])
out_csv = results_base / "stage4m_k_sweep_audit.csv"
df_k_audit.to_csv(out_csv, index=False)
print(f"Saved {len(df_k_audit)} K-sweep audit records to: {out_csv}")
print(df_k_audit[["condition", "window_size_k", "corpus_wer_pct", "disparity_d_pp", "protocol_classification"]].to_string(index=False))
