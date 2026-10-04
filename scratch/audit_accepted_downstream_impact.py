#!/usr/bin/env python3
"""
Diagnostic Audit: Downstream Cumulative Effects of the 9 Accepted DSG Updates.
=============================================================================
Traces:
1. The 9 accepted adaptation windows (0, 2, 7, 8, 24, 27, 57, 81, 83).
2. The model state epochs defined by each acceptance:
   - Epoch 0: Window 0 (initial No-Adapt weights theta_0)
   - Epoch 1: Windows 1-2 (theta_1, adapted on Win 0)
   - Epoch 2: Windows 3-7 (theta_3, adapted on Win 2)
   - Epoch 3: Window 8 (theta_8, adapted on Win 7)
   - Epoch 4: Windows 9-24 (theta_9, adapted on Win 8)
   - Epoch 5: Windows 25-27 (theta_25, adapted on Win 24)
   - Epoch 6: Windows 28-57 (theta_28, adapted on Win 27)
   - Epoch 7: Windows 58-81 (theta_58, adapted on Win 57)
   - Epoch 8: Windows 82-83 (theta_82, adapted on Win 81)
   - Epoch 9: Windows 84-224 (theta_84, adapted on Win 83, frozen for remaining 141 windows!)
3. Comparison of DSG per-clip errors vs No-Adapt per-clip errors across these epochs and accent groups.
"""

from pathlib import Path
import json
import pandas as pd
from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.data.normalization import TextNormalizer

PROJECT_ROOT = Path(".").resolve()
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5"
DSG_PREDS_JSON = REPORTS_DIR / "intermediate_dsg_preds.json"
NO_ADAPT_PREDS_JSON = REPORTS_DIR / "intermediate_no_adapt_preds.json"
DECISIONS_CSV = REPORTS_DIR / "stage5d_final_decision_audit.csv"
EXT_AUDIT_CSV = REPORTS_DIR / "stage5d_external_outcome_audit.csv"

dsg_df = pd.read_json(DSG_PREDS_JSON)
na_df = pd.read_json(NO_ADAPT_PREDS_JSON)
dec_df = pd.read_csv(DECISIONS_CSV)
ext_df = pd.read_csv(EXT_AUDIT_CSV)

print("=" * 70)
print("STAGE 5E DIAGNOSTIC AUDIT: DOWNSTREAM CUMULATIVE EFFECTS OF ACCEPTED UPDATES")
print("=" * 70)

# 1. Inspect the 9 accepted windows
acc_wins = dec_df[dec_df["decision"] == "ACCEPT"]["window_id"].tolist()
print(f"Accepted Window IDs: {acc_wins}")

for w in acc_wins:
    d_row = dec_df[dec_df["window_id"] == w].iloc[0]
    e_row = ext_df[ext_df["window_id"] == w].iloc[0]
    w_clips = dsg_df[dsg_df["window_id"] == w]
    groups = w_clips["group_id"].unique().tolist()
    print(f"\nWindow {w:>3} | Groups in batch: {groups}")
    print(f"  Sentinel Gate: Delta_R={d_row['delta_R']:+.6f}, UCB_R={d_row['UCB_R']:+.6f}, UCB_max={d_row['UCB_max_group']:+.6f}, UCB_D={d_row['UCB_D']:+.6f}")
    print(f"  Immediate Ext: Live={e_row['ext_live_errors']}, Cand={e_row['ext_cand_errors']}, Delta={e_row['ext_word_delta']:+d} ({e_row['external_nature']})")

# 2. Add No-Adapt metrics to dsg_df for direct comparison
na_metrics = []
for _, r in na_df.iterrows():
    ref = TextNormalizer.normalize(r["reference_raw"])
    hyp = TextNormalizer.normalize(r["hypothesis_raw"])
    m = compute_utterance_metrics(ref, hyp)
    na_metrics.append({
        "recording_id": r["recording_id"],
        "na_subs": m.substitutions,
        "na_dels": m.deletions,
        "na_ins": m.insertions,
        "na_errors": m.total_errors,
        "na_words": m.reference_length
    })
na_m_df = pd.DataFrame(na_metrics)
merged = pd.merge(dsg_df, na_m_df, on="recording_id")
merged["dsg_errors"] = merged["substitutions"] + merged["deletions"] + merged["insertions"]
merged["error_delta"] = merged["dsg_errors"] - merged["na_errors"]  # positive = DSG worse, negative = DSG better

print("\n" + "=" * 70)
print("DOWNSTREAM CUMULATIVE IMPACT BY ACCENT GROUP")
print("=" * 70)

for gid, g in merged.groupby("group_id"):
    total_words = g["reference_words"].sum()
    na_err = g["na_errors"].sum()
    dsg_err = g["dsg_errors"].sum()
    diff = dsg_err - na_err
    clips_better = (g["error_delta"] < 0).sum()
    clips_worse = (g["error_delta"] > 0).sum()
    clips_same = (g["error_delta"] == 0).sum()
    print(f"\nGroup: {gid}")
    print(f"  No-Adapt Errors : {na_err} ({na_err/total_words*100:.2f}%)")
    print(f"  DSG Errors      : {dsg_err} ({dsg_err/total_words*100:.2f}%)")
    print(f"  Net Difference  : {diff:+d} words ({(dsg_err-na_err)/total_words*100:+.2f} pp)")
    print(f"  Clips breakdown : Better={clips_better}, Worse={clips_worse}, Identical={clips_same} (Total {len(g)})")

# 3. Model State Epoch Analysis
# Epoch boundaries:
# Epoch 0: Window 0
# Epoch 1: Windows 1-2 (after Win 0 accept)
# Epoch 2: Windows 3-7 (after Win 2 accept)
# Epoch 3: Window 8 (after Win 7 accept)
# Epoch 4: Windows 9-24 (after Win 8 accept)
# Epoch 5: Windows 25-27 (after Win 24 accept)
# Epoch 6: Windows 28-57 (after Win 27 accept)
# Epoch 7: Windows 58-81 (after Win 57 accept)
# Epoch 8: Windows 82-83 (after Win 81 accept)
# Epoch 9: Windows 84-224 (after Win 83 accept)

epochs = [
    ("Epoch 0 (theta_0)", 0, 0),
    ("Epoch 1 (theta_1)", 1, 2),
    ("Epoch 2 (theta_3)", 3, 7),
    ("Epoch 3 (theta_8)", 8, 8),
    ("Epoch 4 (theta_9)", 9, 24),
    ("Epoch 5 (theta_25)", 25, 27),
    ("Epoch 6 (theta_28)", 28, 57),
    ("Epoch 7 (theta_58)", 58, 81),
    ("Epoch 8 (theta_82)", 82, 83),
    ("Epoch 9 (theta_84, Final Frozen)", 84, 224),
]

print("\n" + "=" * 70)
print("DOWNSTREAM CUMULATIVE IMPACT BY MODEL STATE EPOCH")
print("=" * 70)

for name, w_start, w_end in epochs:
    sub = merged[(merged["window_id"] >= w_start) & (merged["window_id"] <= w_end)]
    words = sub["reference_words"].sum()
    na_err = sub["na_errors"].sum()
    dsg_err = sub["dsg_errors"].sum()
    diff = dsg_err - na_err
    print(f"{name:<35} | Windows {w_start:>3}-{w_end:>3} ({len(sub):>3} clips) | NA: {na_err} | DSG: {dsg_err} | Diff: {diff:+d}")

# 4. Specifically audit Irish English and South Asian English clips
print("\n" + "=" * 70)
print("DETAILED TRACE: IRISH ENGLISH CLIPS WHERE DSG IMPROVED OVER NO-ADAPT")
print("=" * 70)
irish_improved = merged[(merged["group_id"] == "Irish English") & (merged["error_delta"] < 0)]
for _, r in irish_improved.iterrows():
    print(f"Window {r['window_id']:>3} | Clip {r['recording_id']} | NA err: {r['na_errors']} -> DSG err: {r['dsg_errors']} (diff {r['error_delta']:+d})")
    print(f"  Ref:  '{r['reference_normalized']}'")
    print(f"  DSG:  '{r['hypothesis_normalized']}'")

print("\n" + "=" * 70)
print("DETAILED TRACE: SOUTH ASIAN ENGLISH CLIPS WHERE DSG IMPROVED OVER NO-ADAPT")
print("=" * 70)
sa_improved = merged[(merged["group_id"] == "South Asian English") & (merged["error_delta"] < 0)]
for _, r in sa_improved.iterrows():
    print(f"Window {r['window_id']:>3} | Clip {r['recording_id']} | NA err: {r['na_errors']} -> DSG err: {r['dsg_errors']} (diff {r['error_delta']:+d})")
    print(f"  Ref:  '{r['reference_normalized']}'")
    print(f"  DSG:  '{r['hypothesis_normalized']}'")

# 5. Detail the 1 accepted harmful update (Window 81)
print("\n" + "=" * 70)
print("DETAILED TRACE: THE 1 ACCEPTED-BUT-HARMFUL UPDATE (WINDOW 81)")
print("=" * 70)
w81_dec = dec_df[dec_df["window_id"] == 81].iloc[0]
w81_ext = ext_df[ext_df["window_id"] == 81].iloc[0]
w81_clips = merged[merged["window_id"] == 81]
print(f"Window 81 Sentinel Assessment:")
print(f"  Delta_R={w81_dec['delta_R']:+.6f}, UCB_R={w81_dec['UCB_R']:+.6f} (threshold <= {w81_dec['epsilon_R']:.4f})")
print(f"  max_delta_g={w81_dec['max_delta_g']:+.6f}, UCB_max={w81_dec['UCB_max_group']:+.6f} (threshold <= {w81_dec['epsilon_G']:.4f})")
print(f"  Delta_D={w81_dec['delta_D']:+.6f}, UCB_D={w81_dec['UCB_D']:+.6f} (threshold <= {w81_dec['epsilon_D']:.4f})")
print(f"Window 81 External Outcome:")
print(f"  Live errors: {w81_ext['ext_live_errors']}, Cand errors: {w81_ext['ext_cand_errors']}, Delta: {w81_ext['ext_word_delta']:+d}")
for _, r in w81_clips.iterrows():
    print(f"  Clip: {r['recording_id']} ({r['group_id']})")
    print(f"    Ref: {r['reference_normalized']}")
    print(f"    Hyp: {r['hypothesis_normalized']}")
