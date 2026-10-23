"""Script to investigate and reconcile inventory provenance from Common Voice 27.0."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TSV_PATH = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv"
INV_CSV = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"
COUNTS_CSV = PROJECT_ROOT / "reports" / "stage5" / "external_selection_counts.csv"


def analyze():
    print(f"Loading {INV_CSV}...")
    df_inv = pd.read_csv(INV_CSV)
    print(f"Inventory total rows: {len(df_inv)}")
    print(f"Inventory unique speakers: {df_inv['speaker_id_prefix'].nunique()}")
    print("\nInventory breakdown by group_code:")
    for grp, cnt in df_inv["group_code"].value_counts().items():
        print(f"  {grp}: {cnt}")
    print(f"Total: {len(df_inv)}")

    print(f"\nLoading {COUNTS_CSV}...")
    df_counts = pd.read_csv(COUNTS_CSV)
    print(df_counts[["group_code", "total_speakers_found", "eligible_speakers", "selected_speakers"]])

    if TSV_PATH.exists():
        print(f"\nScanning {TSV_PATH}...")
        # Check speakers and clips
        spk_clips = defaultdict(lambda: defaultdict(int))
        spk_clips_valid_len = defaultdict(lambda: defaultdict(int))

        target_codes = ["us", "england", "indian", "canada", "australia", "ireland"]

        with open(TSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for r in reader:
                acc = (r.get("accents") or r.get("accent") or "").strip()
                client = r.get("client_id", "").strip()
                sentence = (r.get("sentence") or "").strip()
                words = sentence.split()

                if acc in target_codes and client:
                    spk_clips[acc][client] += 1
                    if len(words) >= 2:
                        spk_clips_valid_len[acc][client] += 1

        print("\nCounts from validated.tsv:")
        print(f"{'Code':<12} | {'Total Speakers':<15} | {'Speakers >= 15 clips':<22} | {'Speakers >= 15 (words >= 2)':<25}")
        print("-" * 80)
        for c in target_codes:
            tot = len(spk_clips[c])
            ge15 = sum(1 for n in spk_clips[c].values() if n >= 15)
            ge15_w = sum(1 for n in spk_clips_valid_len[c].values() if n >= 15)
            print(f"{c:<12} | {tot:<15} | {ge15:<22} | {ge15_w:<25}")


if __name__ == "__main__":
    analyze()
