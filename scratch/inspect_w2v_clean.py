import pandas as pd

df = pd.read_csv("results/stage4_multimodel/stage4m_full_results.csv")
w2v_clean = df[(df["model_key"] == "wav2vec2_base") & (df["condition"] == "clean")]
print("=== wav2vec2_base clean rows ===")
print(w2v_clean[["model_key", "condition", "method", "ordering_id", "corpus_wer", "disparity_d"]])

print("\n=== K-sweep rows ===")
df_k = pd.read_csv("results/stage4_multimodel/stage4m_k_sweep_results.csv")
print(df_k)
