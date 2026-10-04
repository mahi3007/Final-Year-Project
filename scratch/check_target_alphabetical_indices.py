import csv
import pandas as pd

eval_df = pd.read_csv('datasets/splits/stage5_external_eval.csv')
target_paths = set(eval_df['audio_path'])

print("Reading and sorting paths from validated.tsv...", flush=True)
all_paths = []
with open('datasets/external/common_voice_27/validated.tsv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for r in reader:
        all_paths.append(r['path'])

all_paths.sort()
print(f"Total validated paths sorted: {len(all_paths):,}", flush=True)

target_indices = []
for idx, p in enumerate(all_paths):
    if p in target_paths:
        target_indices.append((idx, p))

print(f"Found all {len(target_indices)} targets in alphabetical stream!")
print(f"  First target: index {target_indices[0][0]:,} ({target_indices[0][1]})")
print(f"  Target #100:  index {target_indices[99][0]:,} ({target_indices[99][1]})")
print(f"  Target #300:  index {target_indices[299][0]:,} ({target_indices[299][1]})")
print(f"  Target #500:  index {target_indices[499][0]:,} ({target_indices[499][1]})")
print(f"  Target #700:  index {target_indices[699][0]:,} ({target_indices[699][1]})")
print(f"  Target #800:  index {target_indices[799][0]:,} ({target_indices[799][1]})")
print(f"  Target #850:  index {target_indices[849][0]:,} ({target_indices[849][1]})")
print(f"  Target #900:  index {target_indices[899][0]:,} ({target_indices[899][1]})")
