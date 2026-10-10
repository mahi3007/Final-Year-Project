import pandas as pd

df_k = pd.read_csv("results/stage4_multimodel/stage4m_k_sweep_results.csv")
print("=== K-SWEEP RAW TABLE ===")
print(df_k.to_string())

df_canon = pd.read_csv("results/stage4_multimodel/stage4m_canonical_results.csv")
w2v_suta = df_canon[(df_canon["model_key"] == "wav2vec2_base") & (df_canon["method"] == "suta") & (df_canon["ordering_id"] == "ORDER_A")]
print("\n=== K=4 (Standard SUTA ORDER_A) in Canonical Table ===")
print(w2v_suta[["model_key", "condition", "method", "ordering_id", "corpus_wer", "disparity_d"]].to_string())
