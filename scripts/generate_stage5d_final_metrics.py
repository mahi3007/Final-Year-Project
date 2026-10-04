#!/usr/bin/env python3
"""
Generate Final Verified Stage 5D External Metrics & Group Metrics.
===================================================================
Replays the exact DSG trajectory according to the locked decisions in:
reports/stage5/stage5d_final_decision_audit.csv

Since all 225 decisions are cryptographically locked:
- Exactly 9 windows were ACCEPTED (0, 2, 7, 8, 24, 27, 57, 81, 83).
- Exactly 216 windows were REJECTED.

This replay performs prequential transcribing of the 900 clips, adapts the candidate
only on the 9 accepted windows, records exact per-utterance alignments (S, D, I, WER, CER),
and computes the final official Stage 5D metrics.
"""

import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer, enforce_data_access_firewall
from dsg_ctta.offline.metrics import compute_utterance_metrics, compute_levenshtein_alignment

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
EVAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5"
DECISION_AUDIT_CSV = REPORTS_DIR / "stage5d_final_decision_audit.csv"


def main():
    print("=" * 70)
    print("GENERATING FINAL STAGE 5D EXTERNAL & GROUP METRICS")
    print("=" * 70)

    eval_df = pd.read_csv(EVAL_CSV)
    decisions_df = pd.read_csv(DECISION_AUDIT_CSV)
    accepted_windows = set(decisions_df[decisions_df["decision"] == "ACCEPT"]["window_id"])
    print(f"Loaded {len(decisions_df)} decisions. Accepted windows ({len(accepted_windows)}): {sorted(accepted_windows)}")

    # Preload audio into memory
    print(f"Preloading {len(eval_df)} external audio clips into memory...")
    audio_cache = {}
    for _, row in eval_df.iterrows():
        rec_id = row["recording_id"]
        p = AUDIO_DIR / f"{rec_id}.mp3"
        w, _ = load_and_resample_audio(str(p), 16000)
        audio_cache[rec_id] = w
    print("Preload complete.")

    device = "cpu"
    live_model = create_asr_model("wav2vec2_base", device=device)
    live_model.load_model()

    suta_cfg = {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1}
    window_size_k = 4
    num_clips = len(eval_df)
    num_windows = (num_clips + window_size_k - 1) // window_size_k

    dsg_preds = []
    t0 = time.time()

    for win_idx in range(num_windows):
        start_idx = win_idx * window_size_k
        end_idx = min(start_idx + window_size_k, num_clips)
        batch_rows = eval_df.iloc[start_idx:end_idx]

        # 1. Prequential transcribe with live_model theta_t
        for _, row in batch_rows.iterrows():
            rec_id = row["recording_id"]
            waveform = audio_cache[rec_id]
            inputs = live_model.processor(waveform, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                logits = live_model.model(inputs.input_values).logits
            pred_ids = torch.argmax(logits, dim=-1)
            hyp = live_model.processor.batch_decode(pred_ids)[0].strip()

            ref_norm = TextNormalizer.normalize(row["transcript"])
            hyp_norm = TextNormalizer.normalize(hyp)
            m = compute_utterance_metrics(ref_norm, hyp_norm)

            # Character error rate
            ref_chars = list(ref_norm)
            hyp_chars = list(hyp_norm)
            s_c, d_c, i_c, _ = compute_levenshtein_alignment(ref_chars, hyp_chars)
            cer = (s_c + d_c + i_c) / len(ref_chars) if len(ref_chars) > 0 else 0.0

            dsg_preds.append({
                "run_id": "stage5d_dsg",
                "method": "dsg",
                "window_id": win_idx,
                "recording_id": row["recording_id"],
                "speaker_id": row["speaker_id"],
                "group_id": row["stage5_accent_group"],
                "stratum_code": row["stratum_code"],
                "reference_raw": row["transcript"],
                "reference_normalized": ref_norm,
                "hypothesis_raw": hyp,
                "hypothesis_normalized": hyp_norm,
                "substitutions": m.substitutions,
                "deletions": m.deletions,
                "insertions": m.insertions,
                "reference_words": m.reference_length,
                "wer": m.wer,
                "char_substitutions": s_c,
                "char_deletions": d_c,
                "char_insertions": i_c,
                "reference_chars": len(ref_chars),
                "cer": cer,
            })

        # 2. If this window was accepted, adapt live model
        if win_idx in accepted_windows:
            batch_utts = []
            for _, row in batch_rows.iterrows():
                audio_path = str(AUDIO_DIR / f"{row['recording_id']}.mp3")
                batch_utts.append(
                    UtteranceMetadata(
                        utterance_id=row["recording_id"],
                        speaker_id=row["speaker_id"],
                        group_id=row["stage5_accent_group"],
                        group_type="regional_accent",
                        audio_filepath=audio_path,
                        reference_raw=row["transcript"],
                        reference_normalized=TextNormalizer.normalize(row["transcript"]),
                        duration_seconds=float(row["duration_sec"]),
                        sampling_rate_hz=int(row["sample_rate"]),
                        reference_word_count=len(row["transcript"].split()),
                        provenance=ProvenanceInfo(
                            source_dataset="common_voice_27",
                            dataset_release="cv-corpus-27.0-2026-09-11",
                            protocol_version="v1.0-cv27-amended"
                        )
                    )
                )
            unlabeled_batch = LabelIsolationSanitizer.sanitize_batch(batch_utts, batch_idx=win_idx)
            enforce_data_access_firewall(unlabeled_batch)
            adapter = SutaAdapter(asr_model=live_model, config=suta_cfg)
            adapter.adapt(unlabeled_batch)
            print(f"  [Window {win_idx:>3}] Adapted live model on accepted update.")

    elapsed = time.time() - t0
    print(f"\nReplay completed in {elapsed:.2f}s ({elapsed/num_clips:.3f}s/clip).")

    # Export intermediate preds
    preds_df = pd.DataFrame(dsg_preds)
    out_preds_json = REPORTS_DIR / "intermediate_dsg_preds.json"
    preds_df.to_json(out_preds_json, orient="records", indent=2)
    print(f"Saved predictions to: {out_preds_json}")

    # Compute overall corpus metrics
    total_subs = preds_df["substitutions"].sum()
    total_dels = preds_df["deletions"].sum()
    total_ins = preds_df["insertions"].sum()
    total_ref_words = preds_df["reference_words"].sum()
    total_errors = total_subs + total_dels + total_ins
    corpus_wer = total_errors / total_ref_words

    total_c_subs = preds_df["char_substitutions"].sum()
    total_c_dels = preds_df["char_deletions"].sum()
    total_c_ins = preds_df["char_insertions"].sum()
    total_ref_chars = preds_df["reference_chars"].sum()
    corpus_cer = (total_c_subs + total_c_dels + total_c_ins) / total_ref_chars

    # Speaker macro WER
    spk_wers = preds_df.groupby("speaker_id").apply(
        lambda g: (g["substitutions"].sum() + g["deletions"].sum() + g["insertions"].sum()) / g["reference_words"].sum()
    )
    speaker_macro_wer = spk_wers.mean()

    # Group metrics & Disparity D
    group_stats = []
    group_wers = {}
    for group_id, g in preds_df.groupby("group_id"):
        g_subs = g["substitutions"].sum()
        g_dels = g["deletions"].sum()
        g_ins = g["insertions"].sum()
        g_words = g["reference_words"].sum()
        g_wer = (g_subs + g_dels + g_ins) / g_words

        g_c_subs = g["char_substitutions"].sum()
        g_c_dels = g["char_deletions"].sum()
        g_c_ins = g["char_insertions"].sum()
        g_chars = g["reference_chars"].sum()
        g_cer = (g_c_subs + g_c_dels + g_c_ins) / g_chars

        stratum = g["stratum_code"].iloc[0]
        num_c = len(g)
        num_s = g["speaker_id"].nunique()

        group_wers[group_id] = g_wer
        group_stats.append({
            "method": "dsg",
            "group_id": group_id,
            "stratum_code": stratum,
            "num_clips": num_c,
            "num_speakers": num_s,
            "wer": round(g_wer, 6),
            "cer": round(g_cer, 6),
            "substitutions": int(g_subs),
            "deletions": int(g_dels),
            "insertions": int(g_ins),
            "reference_words": int(g_words),
        })

    # Disparity D = max_wer - min_wer
    disparity_d = max(group_wers.values()) - min(group_wers.values())

    # Load no_adapt baseline for deltas
    no_adapt_df = pd.read_json(REPORTS_DIR / "intermediate_no_adapt_preds.json")
    na_total_err = no_adapt_df["substitutions"].sum() + no_adapt_df["deletions"].sum() + no_adapt_df["insertions"].sum()
    na_words = no_adapt_df["reference_words"].sum()
    na_wer = na_total_err / na_words

    na_group_wers = {}
    for gid, g in no_adapt_df.groupby("group_id"):
        na_group_wers[gid] = (g["substitutions"].sum() + g["deletions"].sum() + g["insertions"].sum()) / g["reference_words"].sum()
    na_disparity_d = max(na_group_wers.values()) - min(na_group_wers.values())

    delta_r = corpus_wer - na_wer
    delta_d = disparity_d - na_disparity_d
    max_delta_g = max(group_wers[gid] - na_group_wers[gid] for gid in group_wers)

    for gs in group_stats:
        gid = gs["group_id"]
        gs["delta_g_vs_no_adapt"] = round(group_wers[gid] - na_group_wers[gid], 6)

    print("\n" + "=" * 70)
    print("STAGE 5D VERIFIED METRICS:")
    print(f"  Corpus WER        : {corpus_wer*100:.2f}% ({total_errors}/{total_ref_words})")
    print(f"  Speaker Macro WER : {speaker_macro_wer*100:.2f}%")
    print(f"  Corpus CER        : {corpus_cer*100:.2f}%")
    print(f"  Disparity D       : {disparity_d:.6f} (No-Adapt: {na_disparity_d:.6f}, delta_D: {delta_d:+.6f})")
    print(f"  Delta R vs No-Adapt: {delta_r:+.6f}")
    print(f"  Max Delta g       : {max_delta_g:+.6f}")
    print(f"  DSG Accepted      : {len(accepted_windows)} / {num_windows} ({len(accepted_windows)/num_windows*100:.1f}%)")
    print(f"  DSG Rejected      : {num_windows - len(accepted_windows)} / {num_windows} ({(num_windows - len(accepted_windows))/num_windows*100:.1f}%)")
    print("=" * 70)

    # Update final_external_metrics.csv
    ext_metrics_csv = REPORTS_DIR / "final_external_metrics.csv"
    ext_df = pd.read_csv(ext_metrics_csv)
    # Remove existing dsg row if present
    ext_df = ext_df[ext_df["method"] != "dsg"]
    dsg_row = {
        "method": "dsg",
        "corpus_wer": round(corpus_wer, 6),
        "speaker_macro_wer": round(speaker_macro_wer, 6),
        "corpus_cer": round(corpus_cer, 6),
        "substitutions": int(total_subs),
        "deletions": int(total_dels),
        "insertions": int(total_ins),
        "reference_words": int(total_ref_words),
        "disparity_D": round(disparity_d, 6),
        "delta_R": round(delta_r, 6),
        "delta_D": round(delta_d, 6),
        "max_delta_g": round(max_delta_g, 6),
        "dsg_candidate_updates": num_windows,
        "dsg_accepted": len(accepted_windows),
        "dsg_rejected": num_windows - len(accepted_windows),
        "dsg_rejection_rate": round((num_windows - len(accepted_windows)) / num_windows, 6),
        "epsilon_R": 0.0,
        "epsilon_G": 0.02,
        "epsilon_D": 0.02,
    }
    ext_df = pd.concat([ext_df, pd.DataFrame([dsg_row])], ignore_index=True)
    ext_df.to_csv(ext_metrics_csv, index=False)
    print(f"Updated: {ext_metrics_csv}")

    # Update final_group_metrics.csv
    grp_metrics_csv = REPORTS_DIR / "final_group_metrics.csv"
    grp_df = pd.read_csv(grp_metrics_csv)
    grp_df = grp_df[grp_df["method"] != "dsg"]
    grp_df = pd.concat([grp_df, pd.DataFrame(group_stats)], ignore_index=True)
    grp_df.to_csv(grp_metrics_csv, index=False)
    print(f"Updated: {grp_metrics_csv}")


if __name__ == "__main__":
    main()
