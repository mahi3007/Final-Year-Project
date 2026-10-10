import pandas as pd
from pathlib import Path
import json

results_base = Path("results/stage4_multimodel")

# Inspect Seq2Seq predictions
seq2seq_dirs = list(results_base.glob("whisper_*_static_no_adapt")) + list(results_base.glob("distil_whisper_*_static_no_adapt"))

records = []
for d in seq2seq_dirs:
    parts = d.name.split("_")
    # e.g. whisper_base_clean_static_no_adapt
    model = "_".join(parts[:2])
    cond = parts[2]
    if parts[2] in ["noise", "babble", "reverb"]:
        cond = f"{parts[2]}_{parts[3]}"
        if parts[2] == "reverb":
            cond = f"{parts[2]}_{parts[3]}_{parts[4]}"
    
    df = pd.read_csv(d / "predictions.csv")
    sub = int(df["substitutions"].sum())
    dele = int(df["deletions"].sum())
    ins = int(df["insertions"].sum())
    ref_len = int(df["reference_length"].sum())
    hyp_words = df["hypothesis_normalized"].str.split().apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
    len_ratio = round(hyp_words / ref_len, 4) if ref_len > 0 else 1.0
    wer = round((sub + dele + ins) / ref_len, 4) if ref_len > 0 else 0.0
    
    # Check repeated tokens (e.g. repeated n-grams or repeated words)
    repeated_words_count = 0
    for h in df["hypothesis_normalized"].fillna(""):
        words = h.split()
        for i in range(len(words) - 2):
            if words[i] == words[i+1] == words[i+2]:
                repeated_words_count += 1
                break
                
    records.append({
        "model": model,
        "condition": cond,
        "ref_words": ref_len,
        "hyp_words": hyp_words,
        "len_ratio": len_ratio,
        "substitutions": sub,
        "deletions": dele,
        "insertions": ins,
        "corpus_wer": wer,
        "repeated_utterances": repeated_words_count
    })

df_err = pd.DataFrame(records).sort_values(by=["condition", "model"])
print("=== SEQ2SEQ ERROR DECOMPOSITION ===")
print(df_err.to_string(index=False))

# Now check CTC models on noise_5db vs clean
ctc_dirs = [
    results_base / "wav2vec2_base_clean_no_adapt_order_a",
    results_base / "wav2vec2_base_noise_5db_no_adapt_order_a",
    results_base / "data2vec_base_clean_no_adapt_order_a",
    results_base / "data2vec_base_noise_5db_no_adapt_order_a",
    results_base / "wav2vec2_100h_clean_no_adapt_order_a",
    results_base / "wav2vec2_100h_noise_5db_no_adapt_order_a",
]

ctc_records = []
for d in ctc_dirs:
    parts = d.name.split("_")
    model = f"{parts[0]}_{parts[1]}"
    cond = "clean" if "clean" in d.name else "noise_5db"
    df = pd.read_csv(d / "predictions.csv")
    sub = int(df["substitutions"].sum())
    dele = int(df["deletions"].sum())
    ins = int(df["insertions"].sum())
    ref_len = int(df["reference_length"].sum())
    hyp_words = df["hypothesis_normalized"].str.split().apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
    len_ratio = round(hyp_words / ref_len, 4) if ref_len > 0 else 1.0
    wer = round((sub + dele + ins) / ref_len, 4) if ref_len > 0 else 0.0
    ctc_records.append({
        "model": model,
        "condition": cond,
        "ref_words": ref_len,
        "hyp_words": hyp_words,
        "len_ratio": len_ratio,
        "substitutions": sub,
        "deletions": dele,
        "insertions": ins,
        "corpus_wer": wer
    })

df_ctc_err = pd.DataFrame(ctc_records)
print("\n=== CTC BASELINE ERROR DECOMPOSITION (Clean vs Noise 5dB) ===")
print(df_ctc_err.to_string(index=False))
