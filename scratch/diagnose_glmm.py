import torch
import numpy as np
import pandas as pd
import json
import patsy
from pathlib import Path

# Load canonical dataset
results_base = Path("results/stage4_multimodel")

pred_dfs = []
# 150 canonical settings
for p in results_base.glob("*_order_a/predictions.csv"):
    if "static" not in p.parent.name:
        parts = p.parent.name.split("_")
        # e.g. wav2vec2_base_clean_no_adapt_order_a
        # model is first 2 parts (wav2vec2_base, data2vec_base, wav2vec2_100h)
        model = f"{parts[0]}_{parts[1]}"
        cond = parts[2]
        if parts[2] == "noise" or parts[2] == "babble" or parts[2] == "reverb":
            cond = f"{parts[2]}_{parts[3]}"
            meth = parts[4]
            order = f"{parts[5]}_{parts[6]}".upper()
            if parts[2] == "reverb":
                cond = f"{parts[2]}_{parts[3]}_{parts[4]}"
                meth = parts[5]
                order = f"{parts[6]}_{parts[7]}".upper()
        else:
            cond = parts[2]
            meth = parts[3]
            order = f"{parts[4]}_{parts[5]}".upper()
            
        df = pd.read_csv(p)
        df["model"] = model
        df["condition"] = cond
        df["method"] = meth
        df["ordering"] = order
        pred_dfs.append(df)

for p in list(results_base.glob("*_order_b/predictions.csv")) + list(results_base.glob("*_order_c/predictions.csv")):
    if "no_adapt" not in p.parent.name and "static" not in p.parent.name:
        parts = p.parent.name.split("_")
        model = f"{parts[0]}_{parts[1]}"
        if parts[2] == "noise" or parts[2] == "babble" or parts[2] == "reverb":
            cond = f"{parts[2]}_{parts[3]}"
            meth = parts[4]
            order = f"{parts[5]}_{parts[6]}".upper()
            if parts[2] == "reverb":
                cond = f"{parts[2]}_{parts[3]}_{parts[4]}"
                meth = parts[5]
                order = f"{parts[6]}_{parts[7]}".upper()
        else:
            cond = parts[2]
            meth = parts[3]
            order = f"{parts[4]}_{parts[5]}".upper()
            
        df = pd.read_csv(p)
        df["model"] = model
        df["condition"] = cond
        df["method"] = meth
        df["ordering"] = order
        pred_dfs.append(df)

df_canonical = pd.concat(pred_dfs, ignore_index=True)
print(f"Loaded canonical records: {len(df_canonical)}")
assert len(df_canonical) == 18000

# Speaker and Utterance Empirical Distributions
df_canonical["errors"] = df_canonical["substitutions"] + df_canonical["deletions"] + df_canonical["insertions"]
df_canonical["wer_utt"] = df_canonical["errors"] / df_canonical["reference_length"]

spk_stats = df_canonical.groupby("speaker_id")["wer_utt"].agg(["mean", "std", "count"])
print("\nSpeaker empirical WER stats across all 18,000 observations:")
print(spk_stats)

utt_stats = df_canonical.groupby("utterance_id")["wer_utt"].agg(["mean", "std", "count"])
print(f"\nAcross 120 utterances, utterance mean WER ranges from {utt_stats['mean'].min():.4f} to {utt_stats['mean'].max():.4f} (SD={utt_stats['mean'].std():.4f})")
print(f"Across 12 speakers, speaker mean WER ranges from {spk_stats['mean'].min():.4f} to {spk_stats['mean'].max():.4f} (SD={spk_stats['mean'].std():.4f})")

# Load existing GLMM results
with open(results_base / "stage4m_canonical_glmm_results.json", "r") as f:
    glmm_res = json.load(f)

canon_res = glmm_res["canonical_specification"]
print("\nGLMM Parameters:")
print(f"phi: {canon_res['dispersion_phi']}")
print(f"sigma_s: {canon_res['speaker_sd_sigma_s']}")
print(f"sigma_u: {canon_res['utterance_sd_sigma_u']}")
print(f"Coefficients count: {len(canon_res['coefficients'])}")
