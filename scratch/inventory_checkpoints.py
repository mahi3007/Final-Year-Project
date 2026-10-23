import json
from pathlib import Path
from collections import defaultdict

ck_dir = Path("results/stage5m/checkpoints")
checkpoints = list(ck_dir.glob("STAGE5M_*.json"))

print(f"Total checkpoint files: {len(checkpoints)}")

by_model = defaultdict(lambda: defaultdict(list))
all_summaries = []
all_decisions = []

for ck in checkpoints:
    with open(ck, "r") as f:
        data = json.load(f)
    s = data.get("summary", {})
    all_summaries.append(s)
    all_decisions.extend(data.get("operational_decisions", []))
    
    m = s.get("model_key")
    cond = s.get("condition")
    method = s.get("method")
    order = s.get("ordering_id")
    by_model[m][cond].append((method, order))

for m, conds in sorted(by_model.items()):
    print(f"\nModel: {m} (Total runs: {sum(len(v) for v in conds.values())})")
    for cond, runs in sorted(conds.items()):
        print(f"  Condition: {cond} ({len(runs)} runs) -> methods: {sorted(set(r[0] for r in runs))}")

print(f"\nTotal completed cell runs: {len(all_summaries)}")
print(f"Total operational decisions recorded: {len(all_decisions)}")
