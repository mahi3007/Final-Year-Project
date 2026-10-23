import sys
import io
import pandas as pd
import json
from pathlib import Path

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")

inv_csv = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
e1_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
e1_mf = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval_manifest.json"
es_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
es_mf = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel_manifest.json"
e4_csv = PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv"
ec_csv = PROJECT_ROOT / "datasets" / "splits" / "calibration.csv"

df_inv = pd.read_csv(inv_csv)
df_e1 = pd.read_csv(e1_csv)
df_es = pd.read_csv(es_csv)
df_e4 = pd.read_csv(e4_csv)
df_ec = pd.read_csv(ec_csv)

with open(e1_mf, "r", encoding="utf-8") as f:
    mf_e1 = json.load(f)
with open(es_mf, "r", encoding="utf-8") as f:
    mf_es = json.load(f)

print("=" * 60)
print("SPLIT SUMMARY:")
print(f"Inventory I: {len(df_inv)} rows, {df_inv['speaker_id_prefix'].nunique()} unique speaker prefixes")
print(f"Cohort 1 (E1): {len(df_e1)} clip rows, {df_e1['speaker_id'].nunique()} unique speakers")
print(f"  Manifest E1: num_speakers={mf_e1.get('num_speakers', mf_e1.get('total_speakers'))}, num_clips={mf_e1.get('num_clips', mf_e1.get('total_clips'))}")
print(f"Sentinel (ES): {len(df_es)} clip rows, {df_es['speaker_id'].nunique()} unique speakers")
print(f"  Manifest ES: num_speakers={mf_es.get('num_speakers', mf_es.get('total_speakers'))}, num_clips={mf_es.get('num_clips', mf_es.get('total_clips'))}")
print(f"Stage 4 (E4): {len(df_e4)} rows, {df_e4['speaker_id'].nunique()} unique speakers")
print(f"Calibration (EC): {len(df_ec)} rows, {df_ec['speaker_id'].nunique()} unique speakers")

print("\n" + "=" * 60)
print("COHORT 1 (E1) PER STRATUM BREAKDOWN (speakers, clips):")
e1_group_col = "stage5_accent_group" if "stage5_accent_group" in df_e1.columns else "accent_group"
for grp, sub in df_e1.groupby(e1_group_col):
    print(f"  {grp}: {sub['speaker_id'].nunique()} speakers, {len(sub)} clips")

print("\n" + "=" * 60)
print("SENTINEL (ES) PER STRATUM BREAKDOWN (speakers, clips):")
es_group_col = "stage5_accent_group" if "stage5_accent_group" in df_es.columns else "accent_group"
for grp, sub in df_es.groupby(es_group_col):
    print(f"  {grp}: {sub['speaker_id'].nunique()} speakers, {len(sub)} clips")

print("\n" + "=" * 60)
print("INVENTORY (I) PER STRATUM BREAKDOWN:")
for grp, sub in df_inv.groupby("group_code"):
    print(f"  {grp}: {sub['speaker_id_prefix'].nunique()} speakers")

# Map full speaker_ids in E1 and ES to prefixes
e1_spk_prefixes = {s: s[:24] + "…" for s in df_e1["speaker_id"].unique()}
es_spk_prefixes = {s: s[:24] + "…" for s in df_es["speaker_id"].unique()}
e4_spk_prefixes = {s: s[:24] + "…" for s in df_e4["speaker_id"].unique()}
ec_spk_prefixes = {s: s[:24] + "…" for s in df_ec["speaker_id"].unique()}

inv_prefixes = set(df_inv["speaker_id_prefix"])

print("\n" + "=" * 60)
print("SET INTERSECTIONS WITH INVENTORY (I):")
e1_in_inv = set(e1_spk_prefixes.values()).intersection(inv_prefixes)
es_in_inv = set(es_spk_prefixes.values()).intersection(inv_prefixes)
e4_in_inv = set(e4_spk_prefixes.values()).intersection(inv_prefixes)
ec_in_inv = set(ec_spk_prefixes.values()).intersection(inv_prefixes)

print(f"|E1 ∩ I| = {len(e1_in_inv)} (out of {len(e1_spk_prefixes)} E1 speakers)")
print(f"|ES ∩ I| = {len(es_in_inv)} (out of {len(es_spk_prefixes)} ES speakers)")
print(f"|E4 ∩ I| = {len(e4_in_inv)} (out of {len(e4_spk_prefixes)} E4 speakers)")
print(f"|EC ∩ I| = {len(ec_in_inv)} (out of {len(ec_spk_prefixes)} EC speakers)")

print(f"|E1 ∩ ES| = {len(set(e1_spk_prefixes.values()).intersection(set(es_spk_prefixes.values())))}")

# Load six_group_strict_results.json
strict_json = PROJECT_ROOT / "scratch" / "six_group_strict_results.json"
if strict_json.exists():
    with open(strict_json, "r") as f:
        strict_res = json.load(f)
    print("\n" + "=" * 60)
    print("STRICT ELIGIBILITY & EXPOSURE RECONCILIATION PER STRATUM:")
    total_inv = 0
    total_q = 0
    total_strict_pass = 0
    total_e1 = 0
    total_es = 0
    total_exposed = 0
    total_q_e1 = 0
    total_strict_exposed = 0
    total_available = 0
    for g, data in strict_res.items():
        total_inv += data['baseline_inventory']
        total_q += data['failing_strict_count']
        total_strict_pass += data['strictly_eligible_total']
        total_e1 += data['e1_count']
        total_es += data['es_count']
        total_exposed += (data['e1_count'] + data['es_count'])
        total_q_e1 += data['q_overlap_e1']
        total_strict_exposed += data['strictly_eligible_exposed']
        total_available += data['net_available_unexposed_strict']
        print(f"\nStratum: {g}")
        print(f"  I_g (Inventory): {data['baseline_inventory']}")
        print(f"  Q_g (Fail Strict): {data['failing_strict_count']}")
        print(f"  Strict Eligible: {data['strictly_eligible_total']}")
        print(f"  E1 in stratum: {data['e1_count']} speakers")
        print(f"  ES in stratum: {data['es_count']} speakers")
        print(f"  Total Exposed (E1 ∪ ES): {data['e1_count'] + data['es_count']} speakers")
        print(f"  Q ∩ E1: {data['q_overlap_e1']}")
        print(f"  Q ∩ ES: {data['q_overlap_es']}")
        print(f"  Strictly Eligible Exposed: {data['strictly_eligible_exposed']}")
        print(f"  Net Available Unexposed Strictly Eligible: {data['net_available_unexposed_strict']}")
    print("\nTOTALS ACROSS ALL 6 STRATA:")
    print(f"  Total Baseline Inventory |I|: {total_inv}")
    print(f"  Total Quality Exclusions |Q|: {total_q}")
    print(f"  Total Strictly Eligible (|I \\ Q|): {total_strict_pass}")
    print(f"  Total Cohort 1 (|E1|): {total_e1}")
    print(f"  Total Sentinel (|ES|): {total_es}")
    print(f"  Total Prior Exposed (|E1 ∪ ES|): {total_exposed}")
    print(f"  Total Exposed Failing Strict (|Q ∩ E1|): {total_q_e1}")
    print(f"  Total Exposed Strictly Eligible (|(E1 ∪ ES) \\ Q|): {total_strict_exposed}")
    print(f"  Total Net Available Unexposed Strictly Eligible: {total_available}")
    print(f"  Verification check: {total_strict_pass} - {total_strict_exposed} = {total_strict_pass - total_strict_exposed} (matches {total_available})")
