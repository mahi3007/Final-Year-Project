import csv

with open('datasets/splits/stage5_external_eval.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    paths = [r['audio_path'] for r in reader]

paths_sorted = sorted(paths)
print("Total paths:", len(paths_sorted))
print("First 10 lexicographically:")
for p in paths_sorted[:10]:
    print(" ", p)

print("\nLast 10 lexicographically:")
for p in paths_sorted[-10:]:
    print(" ", p)
