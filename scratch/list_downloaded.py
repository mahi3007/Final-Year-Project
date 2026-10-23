import os
from pathlib import Path

out_dir = Path("scratch/kaggle_run_output")
print(f"Exists: {out_dir.exists()}")
if out_dir.exists():
    for root, dirs, files in os.walk(out_dir):
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(out_dir)
            size_kb = p.stat().st_size / 1024
            if not f.endswith(".wav"): # don't spam audio files
                print(f"{rel} ({size_kb:.2f} KB)")
