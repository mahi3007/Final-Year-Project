import pandas as pd

df_full = pd.read_csv("results/stage4_multimodel/stage4m_full_results.csv")

# 1. Canonical No-Adapt Baseline on ORDER_A
df_base = df_full[(df_full["method"] == "no_adapt") & (df_full["ordering_id"].str.contains("ORDER_A"))].copy()

print("=== CANONICAL NO-ADAPT BASELINE (ORDER_A, 120 utts, 12 speakers) ===")
cols = ["model_key", "architecture", "condition", "corpus_wer", "disparity_d", "total_errors", "reference_words"]
print(df_base[cols].to_string())

# Pivot table for clean presentation
piv_wer = df_base.pivot(index="model_key", columns="condition", values="corpus_wer")
piv_d = df_base.pivot(index="model_key", columns="condition", values="disparity_d")

print("\n--- BASELINE WER (%) ---")
print((piv_wer * 100.0).round(2).to_string())

print("\n--- BASELINE DISPARITY D (pp) ---")
print((piv_d * 100.0).round(2).to_string())

# 2. Macro-average across all 12 nominal settings for CTC vs single static control for Seq2Seq
piv_macro_wer = df_full.groupby(["model_key", "condition"])["corpus_wer"].mean().unstack()
piv_macro_d = df_full.groupby(["model_key", "condition"])["disparity_d"].mean().unstack()

print("\n--- MACRO-AVERAGE WER (%) ---")
print((piv_macro_wer * 100.0).round(2).to_string())

print("\n--- MACRO-AVERAGE DISPARITY D (pp) ---")
print((piv_macro_d * 100.0).round(2).to_string())
