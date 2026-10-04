#!/usr/bin/env python3
"""
Stage 5A Sentinel Panel Curation Script
======================================
Deterministically curates an expanded, model-blind, air-gapped Sentinel Panel
with 5 independent speakers per stratum (30 speakers total, 300 clips) from
Mozilla Common Voice 27.0 English (validated.tsv).

Resolution: OPTION 3 (Expanding Sentinel Panel to eliminate group-level bootstrap degeneracy).
Guarantees:
- Zero overlap with the 60 Stage 5 external evaluation speakers
- Zero overlap with L2-ARCTIC calibration or adaptation speakers
- 5 independent speakers per each of the 6 Stage-5 evaluation strata
- 10 clips per speaker (300 clips total)
- Purely deterministic, model-blind pseudo-random selection
"""

import hashlib
import json
import random
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAL_PATH = PROJECT_ROOT / "datasets" / "external" / "common_voice_27_intermediate" / "validated.tsv"
EXT_EVAL_PATH = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
OUT_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
OUT_MANIFEST = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel_manifest.json"
OUT_LOCK = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json"

GROUP_MAP = {
    "United States English": ("US English", "us"),
    "England English": ("England English", "england"),
    "India and South Asia (India, Pakistan, Sri Lanka)": ("South Asian English", "south_asian"),
    "Australian English": ("Australian English", "australia"),
    "Canadian English": ("Canadian English", "canada"),
    "Irish English": ("Irish English", "ireland"),
}

BASE_SEED = 20261002


def curate_sentinel_panel():
    print(f"Loading external evaluation set from {EXT_EVAL_PATH} to enforce disjointness...")
    ext_eval = pd.read_csv(EXT_EVAL_PATH)
    ext_eval_spks = set(ext_eval["speaker_id"].unique())
    print(f"Loaded {len(ext_eval_spks)} external evaluation speakers to exclude.")

    print(f"Loading validated metadata from {VAL_PATH}...")
    df = pd.read_csv(VAL_PATH, sep="\t", low_memory=False)

    # 1. Standard quality filters
    df = df[
        (df["locale"] == "en")
        & (df["up_votes"] >= 2)
        & (df["down_votes"] < 2)
        & (df["accents"].isin(GROUP_MAP.keys()))
    ].copy()

    df["stage5_accent_group"] = df["accents"].apply(lambda a: GROUP_MAP[a][0])
    df["stratum_code"] = df["accents"].apply(lambda a: GROUP_MAP[a][1])

    # 2. Exclude all external evaluation speakers
    df = df[~df["client_id"].isin(ext_eval_spks)].copy()

    # 3. Minimum sentence word count >= 2
    df["word_count"] = df["sentence"].fillna("").apply(lambda s: len(s.split()))
    df = df[df["word_count"] >= 2].copy()

    # 4. Speaker homogeneity: 100% of validated clips must have the same accent
    spk_groups = df.groupby("client_id")["stage5_accent_group"].nunique()
    homog_spks = set(spk_groups[spk_groups == 1].index)
    df = df[df["client_id"].isin(homog_spks)].copy()

    # 5. Eligible speakers must have at least 15 valid clips to allow sampling 10
    spk_clip_cnt = df.groupby(["stage5_accent_group", "client_id"]).size()
    eligible_spks = spk_clip_cnt[spk_clip_cnt >= 15]

    strata = sorted(list(set(v[0] for v in GROUP_MAP.values())))
    selected_rows = []
    manifest_data = {
        "panel_id": "stage5_sentinel_v2_expanded",
        "description": "Expanded 30-speaker model-blind sentinel panel for Stage 5A DSG Controller",
        "base_seed": BASE_SEED,
        "total_speakers": 30,
        "speakers_per_group": 5,
        "clips_per_speaker": 10,
        "total_clips": 300,
        "strata": {},
    }

    for s_idx, stratum in enumerate(strata):
        spk_pool = sorted(eligible_spks.loc[stratum].index.tolist())
        rng = random.Random(BASE_SEED + s_idx * 100)
        sampled_spks = sorted(rng.sample(spk_pool, 5))
        manifest_data["strata"][stratum] = {
            "stratum_code": GROUP_MAP[
                [k for k, v in GROUP_MAP.items() if v[0] == stratum][0]
            ][1],
            "pool_size": len(spk_pool),
            "speakers": sampled_spks,
        }
        print(f"Stratum {stratum}: pool={len(spk_pool)}, sampled 5 speakers.")

        for spk_order, spk_id in enumerate(sampled_spks):
            spk_clips_df = df[df["client_id"] == spk_id].sort_values("path")
            c_rng = random.Random(
                BASE_SEED
                + int(hashlib.sha256(spk_id.encode()).hexdigest()[:8], 16) % 100000
            )
            clip_indices = sorted(c_rng.sample(range(len(spk_clips_df)), 10))
            sampled_clips = spk_clips_df.iloc[clip_indices].copy()

            for c_idx, (_, r) in enumerate(sampled_clips.iterrows()):
                sentinel_id = f"sentinel_{s_idx+1:02d}_{spk_order+1:02d}_{c_idx+1:02d}"
                selected_rows.append(
                    {
                        "sentinel_id": sentinel_id,
                        "speaker_id": spk_id,
                        "stage5_accent_group": stratum,
                        "stratum_code": GROUP_MAP[r["accents"]][1],
                        "source_accent_raw": r["accents"],
                        "audio_path": r["path"],
                        "transcript": r["sentence"],
                        "word_count": r["word_count"],
                        "source_dataset": "Mozilla Common Voice 27.0",
                    }
                )

    sent_df = pd.DataFrame(selected_rows)
    assert len(sent_df) == 300, f"Expected 300 rows, got {len(sent_df)}"
    assert sent_df["speaker_id"].nunique() == 30, f"Expected 30 speakers, got {sent_df['speaker_id'].nunique()}"

    # Invariant: 0 overlap with external eval
    overlap = set(sent_df["speaker_id"]).intersection(ext_eval_spks)
    assert len(overlap) == 0, f"CRITICAL LEAKAGE: Sentinel overlaps external eval: {overlap}"

    # Save CSV
    sent_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"Wrote canonical sentinel CSV: {OUT_CSV}")

    # Compute CSV SHA-256
    with open(OUT_CSV, "rb") as f:
        csv_hash = hashlib.sha256(f.read()).hexdigest()

    manifest_data["csv_sha256"] = csv_hash
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Wrote sentinel manifest: {OUT_MANIFEST}")

    # Lock file
    lock_data = {
        "protocol_version": "v1.0-cv27-amended",
        "component": "stage5_sentinel_panel",
        "panel_id": "stage5_sentinel_v2_expanded",
        "csv_path": str(OUT_CSV.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "csv_sha256": csv_hash,
        "total_rows": len(sent_df),
        "total_speakers": 30,
        "speakers_per_group": 5,
        "clips_per_speaker": 10,
        "frozen_timestamp": "2026-10-02T20:55:00Z",
    }
    with open(OUT_LOCK, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)
    print(f"Wrote sentinel cryptographic lock: {OUT_LOCK}")
    print("Sentinel curation complete and locked.")


if __name__ == "__main__":
    curate_sentinel_panel()
