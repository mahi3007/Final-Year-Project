import json
from pathlib import Path
import pandas as pd

ck_dir = Path("results/stage5m/checkpoints")
ck_files = sorted(ck_dir.glob("STAGE5M_*.json"))

records = []
for ck in ck_files:
    with open(ck, "r", encoding="utf-8") as f:
        data = json.load(f)
    s = data.get("summary", {})
    preds = data.get("predictions", [])
    ops = data.get("operational_decisions", [])
    
    exp_id = s.get("experiment_id", ck.stem)
    model = s.get("model_key")
    cond = s.get("condition")
    method = s.get("method")
    order = s.get("ordering_id")
    
    expected_windows = 30
    actual_windows = len(ops)
    actual_preds = len(preds)
    
    # Analyze operational decisions
    # In each run, how many candidate proposals, gate evaluations, accepts, rejects?
    n_accept = len([d for d in ops if d.get("decision") == "ACCEPT"])
    n_reject = len([d for d in ops if d.get("decision") == "REJECT"])
    # Terminal window
    terminal_action = "N/A"
    if ops:
        last_op = ops[-1]
        terminal_action = f"win_{last_op.get('window_id')}:{last_op.get('state_action', last_op.get('decision'))}"
    
    # Are any records missing?
    missing = expected_windows - actual_windows
    status = "COMPLETE" if missing == 0 else f"PARTIAL_SMOKE_TEST (missing {missing} windows)"
    
    # Candidates evaluated vs applied
    # In no_adapt, candidates=0, evaluations=0
    # In active methods, candidates evaluated = actual_windows - 1 (or actual_windows if terminal evaluated)
    # Let's count how many had active decision in ops
    active_evals = len([d for d in ops if d.get("decision") in ["ACCEPT", "REJECT"]])
    
    records.append({
        "run_id": exp_id,
        "model_key": model,
        "condition": cond,
        "method": method,
        "order": order,
        "expected_windows": expected_windows,
        "actual_windows": actual_windows,
        "actual_prediction_rows": actual_preds,
        "candidate_proposals": s.get("total_candidates", 0),
        "gate_evaluations": active_evals,
        "accepted_candidates": n_accept,
        "rejected_candidates": n_reject,
        "applied_updates": n_accept, # in online CTTA, each ACCEPT applies the update to live model
        "terminal_window_action": terminal_action,
        "missing_windows": missing,
        "status": status,
        "words": s.get("total_words"),
        "errors": s.get("total_errors"),
        "wer": s.get("final_wer"),
        "disparity": s.get("final_disparity")
    })

df = pd.DataFrame(records)
print(f"Total runs audited: {len(df)}")
print(f"Total actual windows: {df['actual_windows'].sum()} (Expected: {len(df)*30})")
print(f"Total missing windows: {df['missing_windows'].sum()}")
print(f"Runs with missing windows ({len(df[df['missing_windows'] > 0])}):")
for _, r in df[df["missing_windows"] > 0].iterrows():
    print(f"  {r['run_id']}: actual_windows={r['actual_windows']}, actual_preds={r['actual_prediction_rows']}, status={r['status']}")

print("\nBreakdown by method:")
for method, grp in df.groupby("method"):
    print(f"  Method {method}: {len(grp)} runs, total windows: {grp['actual_windows'].sum()}, total gate evals: {grp['gate_evaluations'].sum()}, total candidates: {grp['candidate_proposals'].sum()}")
