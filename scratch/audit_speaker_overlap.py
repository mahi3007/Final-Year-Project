import pandas as pd
from pathlib import Path

splits = {
    "stage3m_final_test": "datasets/splits/final_test.csv",
    "stage4m_characterization": "datasets/splits/stage4_characterization.csv",
    "calibration": "datasets/splits/calibration.csv",
    "sentinel_panel": "datasets/splits/stage5_sentinel_panel.csv",
    "common_voice_external_eval": "datasets/splits/stage5_external_eval.csv"
}

speaker_sets = {}
speaker_groups = {}
counts = {}

for name, path in splits.items():
    p = Path(path)
    if p.exists():
        df = pd.read_csv(p)
        spk_col = "speaker_id" if "speaker_id" in df.columns else ("client_id" if "client_id" in df.columns else None)
        grp_col = "accent_group" if "accent_group" in df.columns else ("group_id" if "group_id" in df.columns else None)
        
        spks = set(df[spk_col].unique()) if spk_col else set()
        speaker_sets[name] = spks
        counts[name] = len(df)
        print(f"Split {name}: {len(df)} rows, {len(spks)} unique speakers")
    else:
        print(f"Split {name} does not exist at {path}")

# Pairwise comparisons
rows = []
split_names = list(splits.keys())

for i, s1 in enumerate(split_names):
    set1 = speaker_sets.get(s1, set())
    for j, s2 in enumerate(split_names):
        set2 = speaker_sets.get(s2, set())
        overlap = set1.intersection(set2)
        jaccard = len(overlap) / len(set1.union(set2)) if (set1 or set2) else 0.0
        disjoint = (len(overlap) == 0)
        independent_validation = "YES (Disjoint)" if disjoint else "NO (Overlapping)"
        
        rows.append({
            "split_a": s1,
            "split_b": s2,
            "speakers_a": len(set1),
            "speakers_b": len(set2),
            "overlap_count": len(overlap),
            "overlapping_speakers": ";".join(sorted(list(overlap))) if overlap else "none",
            "jaccard_similarity": round(jaccard, 4),
            "disjoint": disjoint,
            "independent_speaker_validation": independent_validation
        })

df_overlap = pd.DataFrame(rows)
out_csv = "reports/stage3m/stage3m_speaker_overlap_audit.csv"
Path("reports/stage3m").mkdir(parents=True, exist_ok=True)
df_overlap.to_csv(out_csv, index=False)
print(f"\nSaved speaker overlap audit to {out_csv}")
for r in rows:
    if r["split_a"] < r["split_b"]:
        print(f"{r['split_a']} vs {r['split_b']}: overlap={r['overlap_count']} speakers ({r['overlapping_speakers']}) -> {r['independent_speaker_validation']}")
