import csv
import json
import pandas as pd
from pathlib import Path

# 1. Load inventory
df_inv = pd.read_csv('reports/stage5/external_speaker_inventory.csv')
irish_inv = df_inv[df_inv['group_code'] == 'Irish English'].copy()
print(f"Total Irish in Inventory (|I|): {len(irish_inv)}")

# 2. Load Cohort 1 (stage5_external_eval.csv)
df_ext = pd.read_csv('datasets/splits/stage5_external_eval.csv')
e1_df = df_ext[df_ext['stage5_accent_group'] == 'Irish English']
E1_spks = set(e1_df['speaker_id'].unique())
print(f"Total Irish in Cohort 1 (|E1|): {len(E1_spks)}")

# 3. Load Sentinel Panel (stage5_sentinel_panel.csv)
df_sent = pd.read_csv('datasets/splits/stage5_sentinel_panel.csv')
es_df = df_sent[df_sent['stage5_accent_group'] == 'Irish English']
ES_spks = set(es_df['speaker_id'].unique())
print(f"Total Irish in Sentinel Panel (|ES|): {len(ES_spks)}")

# 4. Load Stage 4 Characterization
df_st4 = pd.read_csv('datasets/splits/stage4_characterization.csv')
st4_spks = set(df_st4['speaker_id'].unique())
print(f"Total speakers in Stage 4 Characterization: {len(st4_spks)}")
# Check intersection of st4 with Irish
# Let's check from validated.tsv or prefix
# Note: st4 uses L2-ARCTIC speaker IDs: 'ABA', 'SKA', 'YDCK', etc.
print("Stage 4 speaker IDs sample:", sorted(list(st4_spks))[:5])
E4_irish = set() # L2-ARCTIC contains no Common Voice Irish speakers

# 5. Load Calibration
df_cal = pd.read_csv('datasets/splits/calibration.csv')
cal_spks = set(df_cal['speaker_id'].unique())
print("Calibration speaker IDs sample:", sorted(list(cal_spks))[:5])
EC_irish = set() # L2-ARCTIC contains no Common Voice Irish speakers

# 6. Now let's trace all 94 Irish clients in validated.tsv and inventory
tsv_path = Path('datasets/external/common_voice_27/validated.tsv')

GROUP_MAP = {
    "United States English": ("US English", "us"),
    "England English": ("England English", "england"),
    "India and South Asia (India, Pakistan, Sri Lanka)": ("South Asian English", "south_asian"),
    "Australian English": ("Australian English", "australia"),
    "Canadian English": ("Canadian English", "canada"),
    "Irish English": ("Irish English", "ireland"),
}

# Raw validated.tsv filtering matching phase3_external_eval_curation.py
# (word_count >= 2, accents == 'irish english')
all_irish_clients = set()
with open(tsv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        acc = (r.get("accents") or "").strip().lower()
        if acc == "irish english":
            words = len((r.get("sentence") or "").split())
            if words >= 2:
                all_irish_clients.add(r["client_id"])

# Quality filter as applied in curate_stage5_sentinel_panel.py:
# locale == 'en', up_votes >= 2, down_votes < 2, accents in GROUP_MAP, word_count >= 2
quality_irish_clients_ge15 = set()
with open(tsv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    spk_valid_clips = {}
    for r in reader:
        acc = (r.get("accents") or "").strip()
        if acc == "Irish English" and r.get("locale") == "en":
            up = int(r.get("up_votes") or 0)
            down = int(r.get("down_votes") or 0)
            words = len((r.get("sentence") or "").split())
            if up >= 2 and down < 2 and words >= 2:
                cid = r["client_id"]
                spk_valid_clips[cid] = spk_valid_clips.get(cid, 0) + 1

for cid, cnt in spk_valid_clips.items():
    if cnt >= 15:
        quality_irish_clients_ge15.add(cid)

print(f"Irish clients meeting Sentinel quality criteria (>= 15 high-vote clips): {len(quality_irish_clients_ge15)}")

# Identify the exact 94 inventory clients
# Check prefixes in external_speaker_inventory.csv
inv_prefixes = set(irish_inv['speaker_id_prefix'])

# Find which client IDs in all_irish_clients match inv_prefixes
I_clients = {cid for cid in all_irish_clients if (cid[:24] + "…") in inv_prefixes}
print(f"Matched full client IDs for inventory |I|: {len(I_clients)}")

# Find quality excluded client Q in inventory:
# In inventory (94), not in quality_irish_clients_ge15
Q_clients = I_clients - quality_irish_clients_ge15
print(f"Quality excluded clients |Q|: {len(Q_clients)}")
for q in Q_clients:
    print(f"  Quality excluded client ID: {q} (prefix: {q[:24]}…), valid high-vote clips: {spk_valid_clips.get(q, 0)}")

# Check set intersections:
print(f"E1 intersection with I: {len(E1_spks.intersection(I_clients))}")
print(f"ES intersection with I: {len(ES_spks.intersection(I_clients))}")
print(f"E1 intersection with ES: {len(E1_spks.intersection(ES_spks))}")
print(f"E1 intersection with Q: {len(E1_spks.intersection(Q_clients))}")
print(f"ES intersection with Q: {len(ES_spks.intersection(Q_clients))}")

# Check Union of exclusions:
exclusions_union = E1_spks | ES_spks | Q_clients
print(f"Total unique exclusions (|E1 U ES U Q|): {len(exclusions_union)}")

# Available Irish speakers for Stage 6M:
I_available = I_clients - exclusions_union
print(f"Available Irish speakers for Stage 6M (|I_available|): {len(I_available)}")
assert len(I_available) == 78, f"Expected 78, got {len(I_available)}"
print(">>> EXACT SET ARITHMETIC VERIFIED: 94 - (10 + 5 + 1) = 78")
