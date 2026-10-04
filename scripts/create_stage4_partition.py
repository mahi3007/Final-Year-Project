"""
Generate the Stage 4 Characterization partition: datasets/splits/stage4_characterization.csv
Combines the 6 final_test speakers and 6 sentinel_candidates speakers into a 12-speaker,
120-utterance stream (2 speakers per group: 1M, 1F).
Maintains strict disjointness from development.csv and calibration.csv.
"""
import os
import hashlib
import pandas as pd

def generate_stage4_partition():
    splits_dir = "datasets/splits"
    df_test = pd.read_csv(os.path.join(splits_dir, "final_test.csv"))
    df_sentinel = pd.read_csv(os.path.join(splits_dir, "sentinel_candidates.csv"))
    df_dev = pd.read_csv(os.path.join(splits_dir, "development.csv"))
    df_cal = pd.read_csv(os.path.join(splits_dir, "calibration.csv"))

    # Concatenate test and sentinel
    df_stage4 = pd.concat([df_test, df_sentinel], ignore_index=True)
    df_stage4["partition"] = "stage4_characterization"

    # Sort deterministically by group_id and utterance_id
    df_stage4 = df_stage4.sort_values(by=["group_id", "speaker_id", "utterance_id"]).reset_index(drop=True)

    out_csv = os.path.join(splits_dir, "stage4_characterization.csv")
    df_stage4.to_csv(out_csv, index=False)
    print(f"Generated {out_csv} with {len(df_stage4)} utterances.")

    # Compute SHA-256
    with open(out_csv, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    print(f"File SHA-256: {file_hash}")

    # Verify disjointness
    stage4_spks = set(df_stage4["speaker_id"].unique())
    dev_spks = set(df_dev["speaker_id"].unique())
    cal_spks = set(df_cal["speaker_id"].unique())

    overlap_dev = stage4_spks.intersection(dev_spks)
    overlap_cal = stage4_spks.intersection(cal_spks)

    print(f"Stage 4 Speakers ({len(stage4_spks)}): {sorted(stage4_spks)}")
    print(f"Speakers per group: {df_stage4.groupby('group_id')['speaker_id'].nunique().to_dict()}")
    print(f"Utterances per group: {df_stage4.groupby('group_id').size().to_dict()}")
    print(f"Disjointness vs Development: {'PASS (0 overlap)' if not overlap_dev else f'FAIL ({overlap_dev})'}")
    print(f"Disjointness vs Calibration: {'PASS (0 overlap)' if not overlap_cal else f'FAIL ({overlap_cal})'}")

if __name__ == "__main__":
    generate_stage4_partition()
