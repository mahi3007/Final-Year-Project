import csv
import json
import time
from pathlib import Path
from collections import defaultdict
import pandas as pd

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")
TSV_PATH = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv"
INV_CSV = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
EXT_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
SENT_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
ST4_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv"
CAL_CSV = PROJECT_ROOT / "datasets" / "splits" / "calibration.csv"

# Load inventory
inv_df = pd.read_csv(INV_CSV)
inv_prefixes = set(inv_df["speaker_id_prefix"])
inv_prefix_to_group = dict(zip(inv_df["speaker_id_prefix"], inv_df["group_code"]))

# Load exposures
ext_df = pd.read_csv(EXT_CSV)
e1_spks = set(ext_df["speaker_id"].unique())
e1_prefixes = {s[:24] + "…" for s in e1_spks}

sent_df = pd.read_csv(SENT_CSV)
es_spks = set(sent_df["speaker_id"].unique())
es_prefixes = {s[:24] + "…" for s in es_spks}

st4_df = pd.read_csv(ST4_CSV)
st4_spks = set(st4_df["speaker_id"].unique())
st4_prefixes = {s[:24] + "…" for s in st4_spks}

cal_df = pd.read_csv(CAL_CSV)
cal_spks = set(cal_df["speaker_id"].unique())
cal_prefixes = {s[:24] + "…" for s in cal_spks}

ACCENT_NORMALIZATION_MAP = {
    "united states english": "US English",
    "england english": "England English",
    "india and south asia (india, pakistan, sri lanka)": "South Asian English",
    "australian english": "Australian English",
    "canadian english": "Canadian English",
    "irish english": "Irish English",
}

def normalize_accent(raw: str):
    if not raw or "|" in raw:
        return None
    return ACCENT_NORMALIZATION_MAP.get(raw.strip().lower())

print("Scanning validated.tsv...")
t0 = time.time()

# Pass 1: Speaker accent homogeneity across validated.tsv
speaker_accents = defaultdict(set)
with open(TSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        spk = row["client_id"].strip()
        raw_accent = (row.get("accents") or row.get("accent") or "").strip()
        norm = normalize_accent(raw_accent)
        if norm and spk:
            speaker_accents[spk].add(norm)

ambiguous_speakers = {spk for spk, accs in speaker_accents.items() if len(accs) > 1}
print(f"Ambiguous speakers: {len(ambiguous_speakers)} (scan took {time.time() - t0:.1f}s)")

# Pass 2: Clip counts for inventory speakers
# Track C_inventory(s) and C_strict(s)
# Each speaker is identified by client_id.
# Note: we check each unique clip path once globally as per phase3_external_eval_curation.py

seen_paths = set()
spk_inv_counts = defaultdict(int)
spk_strict_counts = defaultdict(int)
spk_full_id_to_prefix = {}
spk_group = {}

t1 = time.time()
with open(TSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        spk = row["client_id"].strip()
        if not spk or spk in ambiguous_speakers:
            continue
        
        raw_accent = (row.get("accents") or row.get("accent") or "").strip()
        accent = normalize_accent(raw_accent)
        if not accent:
            continue

        path = (row.get("path") or "").strip()
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)

        sentence = (row.get("sentence") or "").strip()
        words = sentence.split()
        if len(words) < 2:
            continue

        prefix = spk[:24] + "…"
        spk_full_id_to_prefix[spk] = prefix
        spk_group[spk] = accent

        # Passes B0(r)
        spk_inv_counts[spk] += 1

        # Check V(r): locale == 'en', up_votes >= 2, down_votes < 2
        locale = (row.get("locale") or "en").strip()
        try:
            up = int(row.get("up_votes") or 0)
        except ValueError:
            up = 0
        try:
            down = int(row.get("down_votes") or 0)
        except ValueError:
            down = 0

        if locale == "en" and up >= 2 and down < 2:
            spk_strict_counts[spk] += 1

print(f"Pass 2 complete in {time.time() - t1:.1f}s. Total speakers encountered: {len(spk_inv_counts)}")

# Now evaluate for all speakers in external_speaker_inventory.csv
# Match by prefix (since inventory has 6,905 prefixes)
prefix_to_full_id = {v: k for k, v in spk_full_id_to_prefix.items()}

# Analyze per group
GROUPS = [
    "Australian English",
    "Canadian English",
    "England English",
    "Irish English",
    "South Asian English",
    "US English",
]

results = {}

for g in GROUPS:
    g_df = inv_df[inv_df["group_code"] == g]
    g_prefixes = set(g_df["speaker_id_prefix"])
    n_inv = len(g_prefixes)
    
    # Check strict counts for each speaker in inventory
    fail_strict = []
    pass_strict = []
    
    for prefix in g_prefixes:
        full_id = prefix_to_full_id.get(prefix)
        if full_id is None:
            # Maybe find by prefix match
            matching = [k for k in spk_inv_counts if k.startswith(prefix[:24])]
            if matching:
                full_id = matching[0]
        
        c_inv = spk_inv_counts.get(full_id, 0)
        c_strict = spk_strict_counts.get(full_id, 0)
        
        if c_strict < 15:
            fail_strict.append((prefix, full_id, c_inv, c_strict))
        else:
            pass_strict.append((prefix, full_id, c_inv, c_strict))
            
    fail_strict_prefixes = {x[0] for x in fail_strict}
    pass_strict_prefixes = {x[0] for x in pass_strict}
    
    # Check exposure for this group
    g_e1 = g_prefixes.intersection(e1_prefixes)
    g_es = g_prefixes.intersection(es_prefixes)
    g_st4 = g_prefixes.intersection(st4_prefixes)
    g_cal = g_prefixes.intersection(cal_prefixes)
    
    # Overlap between fail_strict and exposures
    q_overlap_e1 = fail_strict_prefixes.intersection(g_e1)
    q_overlap_es = fail_strict_prefixes.intersection(g_es)
    
    # Strict eligible exposed
    strict_exposed = pass_strict_prefixes.intersection(g_e1 | g_es)
    
    # Net available unexposed strict eligible speakers:
    # S_available = pass_strict_prefixes - (g_e1 | g_es | g_st4 | g_cal)
    net_available = pass_strict_prefixes - (g_e1 | g_es | g_st4 | g_cal)
    
    results[g] = {
        "baseline_inventory": n_inv,
        "failing_strict_count": len(fail_strict),
        "failing_strict_details": [(x[0], x[2], x[3]) for x in fail_strict],
        "strictly_eligible_total": len(pass_strict),
        "strictly_eligible_exposed": len(strict_exposed),
        "q_overlap_e1": len(q_overlap_e1),
        "q_overlap_es": len(q_overlap_es),
        "e1_count": len(g_e1),
        "es_count": len(g_es),
        "other_exclusions": len(g_prefixes.intersection(st4_prefixes | cal_prefixes)),
        "net_available_unexposed_strict": len(net_available),
    }

print("\n" + "="*80)
print("SIX-GROUP STRICT ELIGIBILITY RECONCILIATION RESULTS:")
print("="*80)
for g in GROUPS:
    r = results[g]
    print(f"\nGroup: {g}")
    print(f"  Baseline Inventory |I_g|: {r['baseline_inventory']}")
    print(f"  Failing Strict Clip Eligibility (|Q_g|): {r['failing_strict_count']}")
    if r['failing_strict_count'] > 0:
        for p, cinv, cstr in r['failing_strict_details']:
            print(f"    - {p}: C_inv={cinv}, C_strict={cstr}")
    print(f"  Strictly Eligible Total: {r['strictly_eligible_total']}")
    print(f"  Exposed to Cohort 1 (E1): {r['e1_count']} (Q overlap: {r['q_overlap_e1']})")
    print(f"  Exposed to Sentinel (ES): {r['es_count']} (Q overlap: {r['q_overlap_es']})")
    print(f"  Strictly Eligible Exposed (E1 U ES strictly eligible): {r['strictly_eligible_exposed']}")
    print(f"  Other Exclusions (Stage 4 / Calib): {r['other_exclusions']}")
    print(f"  Net Available Unexposed Strictly Eligible: {r['net_available_unexposed_strict']}")
    
    # Feasibility checks:
    # Active requirement: 75 CV speakers
    # Policy A reserve: 0 reserve for non-Irish (total 75), 3 for Irish (total 78)
    # Policy B reserve: 18 reserve for each (total 93)
    print(f"  Feasibility for Active Sample (75 required): {'PASS' if r['net_available_unexposed_strict'] >= 75 else 'FAIL'} ({r['net_available_unexposed_strict']} available)")
    print(f"  Feasibility for Policy A (CV: 75 active + {3 if g == 'Irish English' else 0} res): {'PASS' if r['net_available_unexposed_strict'] >= (78 if g == 'Irish English' else 75) else 'FAIL'} (need {78 if g == 'Irish English' else 75})")
    print(f"  Feasibility for Policy B (CV: 75 active + 18 res = 93): {'PASS' if r['net_available_unexposed_strict'] >= 93 else 'FAIL'} (need 93)")

with open(PROJECT_ROOT / "scratch" / "six_group_strict_results.json", "w") as f:
    json.dump(results, f, indent=2)
