import pandas as pd, json

inv = pd.read_csv('reports/stage5/external_speaker_inventory.csv')
c1 = pd.read_csv('datasets/splits/stage5_external_eval.csv')
sent = pd.read_csv('datasets/splits/stage5_sentinel_panel.csv')

print("=== Inventory Stratum Counts (Eligible) ===")
print(inv[inv['eligible'] == True]['group_code'].value_counts())

print("\n=== Cohort 1 Stratum Speaker Counts ===")
print(c1.groupby('stratum_code')['speaker_id'].nunique())

print("\n=== Sentinel Panel Stratum Speaker Counts ===")
print(sent.groupby('stratum_code')['speaker_id'].nunique())

inv_irish = set(inv[(inv['group_code'] == 'ireland') & (inv['eligible'] == True)]['speaker_id_prefix'])
c1_irish = set(c1[c1['stratum_code'] == 'ireland']['speaker_id'])
sent_irish = set(sent[sent['stratum_code'] == 'ireland']['speaker_id'])

print(f"\nTotal Eligible Irish in inventory: {len(inv_irish)}")
print(f"Cohort 1 Unique Irish Speakers: {len(c1_irish)}")
print(f"Sentinel Unique Irish Speakers: {len(sent_irish)}")
print(f"Overlap between Cohort 1 and Sentinel: {len(c1_irish.intersection(sent_irish))}")

with open('datasets/splits/stage5_sentinel_panel_manifest.json') as f:
    sent_man = json.load(f)

print("\n=== Sentinel Panel Manifest Irish Accounting ===")
for k, v in sent_man.get('accents', {}).items():
    if 'ire' in k.lower():
        print(k, v)
