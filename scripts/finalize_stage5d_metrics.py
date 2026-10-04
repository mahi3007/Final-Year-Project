#!/usr/bin/env python3
"""
Finalize Stage 5D External & Group Metrics from intermediate_dsg_preds.json.
=============================================================================
Reads the exact per-clip predictions generated during the Stage 5D prequential stream,
computes overall and group metrics, updates CSV artifacts, and prints the summary.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5"
PREDS_JSON = REPORTS_DIR / "intermediate_dsg_preds.json"
DECISION_CSV = REPORTS_DIR / "stage5d_final_decision_audit.csv"
EXT_METRICS_CSV = REPORTS_DIR / "final_external_metrics.csv"
GRP_METRICS_CSV = REPORTS_DIR / "final_group_metrics.csv"


def main():
    print("=" * 70)
    print("FINALIZING STAGE 5D EXTERNAL AND GROUP METRICS")
    print("=" * 70)

    preds_df = pd.read_json(PREDS_JSON)
    decisions_df = pd.read_csv(DECISION_CSV)
    num_windows = len(decisions_df)
    accepted_windows = (decisions_df["decision"] == "ACCEPT").sum()
    rejected_windows = (decisions_df["decision"] == "REJECT").sum()

    print(f"Loaded {len(preds_df)} utterance predictions.")
    print(f"Decisions: {accepted_windows} ACCEPT, {rejected_windows} REJECT.")

    # 1. Corpus metrics
    total_subs = int(preds_df["substitutions"].sum())
    total_dels = int(preds_df["deletions"].sum())
    total_ins = int(preds_df["insertions"].sum())
    total_ref_words = int(preds_df["reference_words"].sum())
    total_errors = total_subs + total_dels + total_ins
    corpus_wer = total_errors / total_ref_words

    total_c_subs = int(preds_df["char_substitutions"].sum())
    total_c_dels = int(preds_df["char_deletions"].sum())
    total_c_ins = int(preds_df["char_insertions"].sum())
    total_ref_chars = int(preds_df["reference_chars"].sum())
    corpus_cer = (total_c_subs + total_c_dels + total_c_ins) / total_ref_chars

    # Speaker macro WER
    spk_wers = []
    for _, g in preds_df.groupby("speaker_id"):
        spk_err = g["substitutions"].sum() + g["deletions"].sum() + g["insertions"].sum()
        spk_words = g["reference_words"].sum()
        spk_wers.append(spk_err / spk_words)
    speaker_macro_wer = float(pd.Series(spk_wers).mean())

    # 2. Baseline No-Adapt values from final_external_metrics.csv & final_group_metrics.csv
    ext_df = pd.read_csv(EXT_METRICS_CSV)
    na_row = ext_df[ext_df["method"] == "no_adapt"].iloc[0]
    na_wer = float(na_row["corpus_wer"])

    grp_df = pd.read_csv(GRP_METRICS_CSV)
    na_grp_df = grp_df[grp_df["method"] == "no_adapt"].set_index("group_id")
    na_group_wers = na_grp_df["wer"].to_dict()
    na_disparity_d = max(na_group_wers.values()) - min(na_group_wers.values())

    # 3. Group metrics
    group_stats = []
    group_wers = {}
    for group_id, g in preds_df.groupby("group_id"):
        g_subs = int(g["substitutions"].sum())
        g_dels = int(g["deletions"].sum())
        g_ins = int(g["insertions"].sum())
        g_words = int(g["reference_words"].sum())
        g_wer = (g_subs + g_dels + g_ins) / g_words

        g_c_subs = int(g["char_substitutions"].sum())
        g_c_dels = int(g["char_deletions"].sum())
        g_c_ins = int(g["char_insertions"].sum())
        g_chars = int(g["reference_chars"].sum())
        g_cer = (g_c_subs + g_c_dels + g_c_ins) / g_chars

        stratum = g["stratum_code"].iloc[0]
        num_c = len(g)
        num_s = g["speaker_id"].nunique()

        delta_g = g_wer - na_group_wers[group_id]
        group_wers[group_id] = g_wer

        group_stats.append({
            "method": "dsg",
            "group_id": group_id,
            "stratum_code": stratum,
            "num_clips": num_c,
            "num_speakers": num_s,
            "wer": round(g_wer, 6),
            "cer": round(g_cer, 6),
            "substitutions": g_subs,
            "deletions": g_dels,
            "insertions": g_ins,
            "reference_words": g_words,
            "delta_g_vs_no_adapt": round(delta_g, 6),
        })

    disparity_d = max(group_wers.values()) - min(group_wers.values())
    delta_r = corpus_wer - na_wer
    delta_d = disparity_d - na_disparity_d
    max_delta_g = max(group_wers[gid] - na_group_wers[gid] for gid in group_wers)

    print("\n" + "=" * 70)
    print("STAGE 5D OFFICIAL VERIFIED METRICS:")
    print(f"  Corpus WER        : {corpus_wer*100:.2f}% ({total_errors}/{total_ref_words})")
    print(f"  Speaker Macro WER : {speaker_macro_wer*100:.2f}%")
    print(f"  Corpus CER        : {corpus_cer*100:.2f}%")
    print(f"  Disparity D       : {disparity_d*100:.2f}% (No-Adapt: {na_disparity_d*100:.2f}%, delta_D: {delta_d*100:+.2f}%)")
    print(f"  Delta R vs No-Adapt: {delta_r*100:+.2f}% ({total_errors - int(na_row['substitutions'] + na_row['deletions'] + na_row['insertions']):+d} words)")
    print(f"  Max Delta g       : {max_delta_g*100:+.2f}%")
    print(f"  DSG Accepted      : {accepted_windows} / {num_windows} ({accepted_windows/num_windows*100:.1f}%)")
    print(f"  DSG Rejected      : {rejected_windows} / {num_windows} ({rejected_windows/num_windows*100:.1f}%)")
    print("=" * 70)

    # 4. Update final_external_metrics.csv
    ext_df = ext_df[ext_df["method"] != "dsg"]
    dsg_row = {
        "method": "dsg",
        "corpus_wer": round(corpus_wer, 6),
        "speaker_macro_wer": round(speaker_macro_wer, 6),
        "corpus_cer": round(corpus_cer, 6),
        "substitutions": total_subs,
        "deletions": total_dels,
        "insertions": total_ins,
        "reference_words": total_ref_words,
        "disparity_D": round(disparity_d, 6),
        "delta_R": round(delta_r, 6),
        "delta_D": round(delta_d, 6),
        "max_delta_g": round(max_delta_g, 6),
        "dsg_candidate_updates": num_windows,
        "dsg_accepted": accepted_windows,
        "dsg_rejected": rejected_windows,
        "dsg_rejection_rate": round(rejected_windows / num_windows, 6),
        "epsilon_R": 0.0,
        "epsilon_G": 0.02,
        "epsilon_D": 0.02,
    }
    ext_df = pd.concat([ext_df, pd.DataFrame([dsg_row])], ignore_index=True)
    ext_df.to_csv(EXT_METRICS_CSV, index=False)
    print(f"Successfully updated: {EXT_METRICS_CSV}")

    # 5. Update final_group_metrics.csv
    grp_df = grp_df[grp_df["method"] != "dsg"]
    grp_df = pd.concat([grp_df, pd.DataFrame(group_stats)], ignore_index=True)
    grp_df.to_csv(GRP_METRICS_CSV, index=False)
    print(f"Successfully updated: {GRP_METRICS_CSV}")


if __name__ == "__main__":
    main()
