import os
from pathlib import Path

p = Path("scratch/kaggle_run_output_full")
if p.exists():
    files = list(p.rglob("*"))
    print(f"Total entries in kaggle_run_output_full: {len(files)}")
    non_wav = [f for f in files if f.is_file() and not f.name.endswith(".wav")]
    print(f"Non-wav files ({len(non_wav)}):")
    for f in non_wav[-20:]:
        print(f"  {f.relative_to(p)} ({f.stat().st_size/1024:.1f} KB)")
