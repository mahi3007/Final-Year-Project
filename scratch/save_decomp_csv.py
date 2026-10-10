import pandas as pd
from pathlib import Path

results_base = Path("results/stage4_multimodel")

# Collect all 15 static Seq2Seq controls
seq_records = []
for d in list(results_base.glob("whisper_*_static_no_adapt")) + list(results_base.glob("distil_whisper_*_static_no_adapt")):
    parts = d.name.split("_")
    model = "_".join(parts[:2])
    cond = parts[2]
    if parts[2] in ["noise", "babble", "reverb"]:
        cond = f"{parts[2]}_{parts[3]}"
        if parts[2] == "reverb":
            cond = f"{parts[2]}_{parts[3]}_{parts[4]}"
    if "distil" in d.name:
        model = "distil_whisper_small"
        
    df = pd.read_csv(d / "predictions.csv")
    sub = int(df["substitutions"].sum())
    dele = int(df["deletions"].sum())
    ins = int(df["insertions"].sum())
    ref_len = int(df["reference_length"].sum())
    hyp_words = df["hypothesis_normalized"].str.split().apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
    len_ratio = round(hyp_words / ref_len, 4) if ref_len > 0 else 1.0
    wer = round((sub + dele + ins) / ref_len, 4) if ref_len > 0 else 0.0
    
    seq_records.append({
        "architecture": "SEQ2SEQ",
        "model_key": model,
        "condition": cond,
        "method": "no_adapt",
        "ordering_id": "ORDER_A (static)",
        "reference_words": ref_len,
        "hypothesis_words": hyp_words,
        "length_ratio": len_ratio,
        "substitutions": sub,
        "deletions": dele,
        "insertions": ins,
        "corpus_wer": wer
    })

# Collect all 15 static CTC baselines (no_adapt, ORDER_A)
ctc_records = []
for m in ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]:
    for c in ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]:
        d = results_base / f"{m}_{c}_no_adapt_order_a"
        df = pd.read_csv(d / "predictions.csv")
        sub = int(df["substitutions"].sum())
        dele = int(df["deletions"].sum())
        ins = int(df["insertions"].sum())
        ref_len = int(df["reference_length"].sum())
        hyp_words = df["hypothesis_normalized"].str.split().apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
        len_ratio = round(hyp_words / ref_len, 4) if ref_len > 0 else 1.0
        wer = round((sub + dele + ins) / ref_len, 4) if ref_len > 0 else 0.0
        ctc_records.append({
            "architecture": "CTC",
            "model_key": m,
            "condition": c,
            "method": "no_adapt",
            "ordering_id": "ORDER_A",
            "reference_words": ref_len,
            "hypothesis_words": hyp_words,
            "length_ratio": len_ratio,
            "substitutions": sub,
            "deletions": dele,
            "insertions": ins,
            "corpus_wer": wer
        })

df_all_decomp = pd.DataFrame(ctc_records + seq_records)
out_csv = results_base / "stage4m_error_decomposition_audit.csv"
df_all_decomp.to_csv(out_csv, index=False)
print(f"Saved {len(df_all_decomp)} error decomposition records to: {out_csv}")
