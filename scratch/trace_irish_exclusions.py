import csv
import json
import pandas as pd
from pathlib import Path

# Load external eval speakers
df_ext = pd.read_csv('datasets/splits/stage5_external_eval.csv')
ext_eval_spks = set(df_ext['speaker_id'].unique())

# Load validated.tsv
tsv_path = Path('datasets/external/common_voice_27/validated.tsv')

GROUP_MAP = {
    "united states english": ("US English", "us"),
    "england english": ("England English", "england"),
    "india and south asia (india, pakistan, sri lanka)": ("South Asian English", "south_asian"),
    "australian english": ("Australian English", "australia"),
    "canadian english": ("Canadian English", "canada"),
    "irish english": ("Irish English", "ireland"),
}

records = []
with open(tsv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        accent_raw = (row.get("accents") or "").strip().lower()
        if accent_raw in GROUP_MAP:
            records.append({
                "client_id": row["client_id"],
                "path": row["path"],
                "sentence": row["sentence"],
                "accents": accent_raw,
            })

df = pd.DataFrame(records)
print("Initial CV27 records for target accents:", len(df))

# 1. Map groups
df["stage5_accent_group"] = df["accents"].apply(lambda a: GROUP_MAP[a][0])
df["stratum_code"] = df["accents"].apply(lambda a: GROUP_MAP[a][1])

# Check Irish before ext exclusion
irish_before_ext = set(df[df["stage5_accent_group"] == "Irish English"]["client_id"])
print("Total unique Irish speakers in TSV:", len(irish_before_ext))

# 2. Exclude external evaluation speakers
df = df[~df["client_id"].isin(ext_eval_spks)].copy()
irish_after_ext = set(df[df["stage5_accent_group"] == "Irish English"]["client_id"])
print("Irish speakers after excluding ext_eval (60 speakers total, 10 Irish):", len(irish_after_ext))

# 3. Minimum sentence word count >= 2
df["word_count"] = df["sentence"].fillna("").apply(lambda s: len(s.split()))
df = df[df["word_count"] >= 2].copy()

# 4. Speaker homogeneity: 100% of validated clips must have the same accent
spk_groups = df.groupby("client_id")["stage5_accent_group"].nunique()
homog_spks = set(spk_groups[spk_groups == 1].index)
non_homog_irish = (irish_after_ext - homog_spks)
print("Irish speakers failing homogeneity (multi-accent declarations in CV27):", len(non_homog_irish), non_homog_irish)

df = df[df["client_id"].isin(homog_spks)].copy()

# 5. Eligible speakers must have at least 15 valid clips
spk_clip_cnt = df.groupby(["stage5_accent_group", "client_id"]).size()
eligible_spks = spk_clip_cnt[spk_clip_cnt >= 15]

irish_pool = eligible_spks.loc["Irish English"].index.tolist()
print("Irish eligible pool for Sentinel (pool_size):", len(irish_pool))

# Load Sentinel manifest
manifest = json.load(open("datasets/splits/stage5_sentinel_panel_manifest.json"))
sent_irish = set(manifest["strata"]["Irish English"]["speakers"])
print("Sentinel sampled Irish speakers:", len(sent_irish))
print("Sentinel pool_size in manifest:", manifest["strata"]["Irish English"]["pool_size"])

# Remaining Irish speakers available for Stage 6M Cohort 2:
available_for_stage6m = set(irish_pool) - sent_irish
print("\n>>> REMAINING ELIGIBLE UNEXPOSED IRISH SPEAKERS FOR STAGE 6M:", len(available_for_stage6m))
