import json

with open('cloud/kaggle/run_stage6m_cohort3_confirmatory_kaggle.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb.get('cells', []))}")
for i, c in enumerate(nb.get('cells', [])[:10]):
    src = "".join(c.get('source', []))
    first_line = src.split('\n')[0] if src else ""
    print(f"Cell {i} ({c.get('cell_type')}): {first_line[:80]}")
