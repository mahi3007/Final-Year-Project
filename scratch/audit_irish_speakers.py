import pandas as pd
from pathlib import Path
import json

p_inv = Path('reports/stage5/external_speaker_inventory.csv')
p_ext = Path('datasets/splits/stage5_external_eval.csv')
p_sent = Path('datasets/splits/stage5_sentinel_panel.csv')
p_st4 = Path('datasets/splits/stage4_characterization.csv')
p_cal = Path('datasets/splits/calibration.csv')

df_inv = pd.read_csv(p_inv)
print("=== INVENTORY GROUPS ===")
print(df_inv['group_code'].value_counts())

df_ext = pd.read_csv(p_ext)
print("\n=== EXTERNAL EVAL (Cohort 1) ===")
for grp, dfg in df_ext.groupby('stage5_accent_group'):
    print(f"  {grp}: {dfg['speaker_id'].nunique()} speakers, {len(dfg)} clips")

df_sent = pd.read_csv(p_sent)
print("\n=== SENTINEL PANEL ===")
for grp, dfg in df_sent.groupby('stage5_accent_group'):
    print(f"  {grp}: {dfg['speaker_id'].nunique()} speakers, {len(dfg)} clips")

df_st4 = pd.read_csv(p_st4)
print("\n=== STAGE 4 CHARACTERIZATION ===")
for grp, dfg in df_st4.groupby('group_id'):
    print(f"  {grp}: {dfg['speaker_id'].nunique()} speakers, {len(dfg)} clips")

df_cal = pd.read_csv(p_cal)
print("\n=== CALIBRATION ===")
for grp, dfg in df_cal.groupby('group_id'):
    print(f"  {grp}: {dfg['speaker_id'].nunique()} speakers, {len(dfg)} clips")
