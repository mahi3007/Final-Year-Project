"""
Inspect complete primary corpus and split allocation.
"""
import json
import os
import pandas as pd

def inspect_corpus():
    manifest_path = "datasets/primary/dataset_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    df_manifest = pd.DataFrame(manifest)
    print(f"Total primary recordings in manifest: {len(df_manifest)}")
    print(f"Columns: {df_manifest.columns.tolist()}")
    
    unique_speakers = sorted(df_manifest["speaker_id"].unique())
    unique_groups = sorted(df_manifest["group_id"].unique())
    print(f"Total speakers: {len(unique_speakers)}")
    print(f"Total groups: {len(unique_groups)} -> {unique_groups}")
    
    spk_per_group = df_manifest.groupby("group_id")["speaker_id"].nunique()
    print("\nSpeakers per group:")
    print(spk_per_group)

    print("\nSpeaker list per group:")
    for g, spks in df_manifest.groupby("group_id")["speaker_id"].unique().items():
        print(f"  {g}: {list(spks)}")

    print("\nUtterances per speaker:")
    print(df_manifest.groupby(["group_id", "speaker_id"]).size())

    # Reference word lengths
    print("\nReference words summary per group:")
    print(df_manifest.groupby("group_id")["reference_word_count"].agg(["count", "sum", "mean", "std"]))

    # Inspect splits
    print("\n================ SPLITS INSPECTION ================")
    splits_dir = "datasets/splits"
    split_files = [f for f in os.listdir(splits_dir) if f.endswith(".csv")]
    
    all_split_spks = {}
    for sf in sorted(split_files):
        df_sp = pd.read_csv(os.path.join(splits_dir, sf))
        spks = sorted(df_sp["speaker_id"].unique())
        grps = sorted(df_sp["group_id"].unique())
        all_split_spks[sf] = spks
        print(f"\nSplit: {sf}")
        print(f"  Utterances: {len(df_sp)}")
        print(f"  Speakers ({len(spks)}): {spks}")
        print(f"  Groups ({len(grps)}): {grps}")
        print(f"  Speakers/Group:")
        print(df_sp.groupby("group_id")["speaker_id"].unique().to_dict())

    # Acoustic metadata summary
    print("\n================ ACOUSTIC & DEVICE METADATA ================")
    print("\nDevices per group:")
    print(df_manifest.groupby(["group_id", "device_id"]).size().unstack(fill_value=0))
    print("\nSNR dB summary per group:")
    print(df_manifest.groupby("group_id")["snr_db"].agg(["mean", "std", "min", "max"]))
    print("\nSpeech Rate WPM summary per group:")
    print(df_manifest.groupby("group_id")["speech_rate_wpm"].agg(["mean", "std", "min", "max"]))
    print("\nDuration seconds summary per group:")
    print(df_manifest.groupby("group_id")["duration_seconds"].agg(["count", "sum", "mean", "std"]))

if __name__ == "__main__":
    inspect_corpus()
