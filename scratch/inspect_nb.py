import json

with open("scratch/kaggle_kernel/notebook840244cb83.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb.get('cells', []))}")
for i, cell in enumerate(nb.get('cells', [])):
    cell_type = cell.get('cell_type')
    source = "".join(cell.get('source', []))
    outputs = cell.get('outputs', [])
    print(f"\n--- Cell {i} ({cell_type}) ---")
    print("Source:\n", source[:300])
    if outputs:
        print(f"Outputs count: {len(outputs)}")
        for out in outputs:
            out_type = out.get('output_type')
            text = "".join(out.get('text', [])) if 'text' in out else str(out)
            print(f"Output ({out_type}):\n{text[:400]}")
