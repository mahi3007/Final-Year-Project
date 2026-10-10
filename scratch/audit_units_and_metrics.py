import json
import pandas as pd
import numpy as np
from pathlib import Path

def audit_full_results_units_and_values():
    results_dir = Path("results/stage3_multimodel")
    summary_csv = results_dir / "stage3m_full_results.csv"
    assert summary_csv.exists()
    
    df_summary = pd.read_csv(summary_csv)
    discrepancies = []
    audited_rows = []
    
    for idx, row in df_summary.iterrows():
        model_key = row["model_key"]
        method = row["method"]
        ord_id = row["ordering_id"]
        arch = row["architecture"]
        
        if arch == "Seq2Seq":
            cell_dir = results_dir / f"{model_key}_static_no_adapt"
        else:
            cell_dir = results_dir / f"{model_key}_{method}_{ord_id.lower()}"
            
        pred_csv = cell_dir / "predictions.csv"
        sum_json = cell_dir / "summary.json"
        
        if not pred_csv.exists():
            discrepancies.append(f"Missing predictions.csv for {cell_dir.name}")
            continue
            
        pdf = pd.read_csv(pred_csv)
        with open(sum_json, "r", encoding="utf-8") as f:
            sdata = json.load(f)
            
        tot_ref_words = int(pdf["reference_length"].sum())
        tot_subs = int(pdf["substitutions"].sum())
        tot_dels = int(pdf["deletions"].sum())
        tot_ins = int(pdf["insertions"].sum())
        tot_errs = tot_subs + tot_dels + tot_ins
        
        recomputed_wer_fraction = tot_errs / tot_ref_words if tot_ref_words > 0 else 0.0
        recomputed_wer_pct = recomputed_wer_fraction * 100.0
        
        mean_cer_fraction = float(pdf["cer"].mean())
        mean_cer_pct = mean_cer_fraction * 100.0
        
        groups = sorted(list(pdf["group_id"].unique()))
        grp_wers_pct = {}
        for g in groups:
            g_df = pdf[pdf["group_id"] == g]
            g_ref = int(g_df["reference_length"].sum())
            g_err = int(g_df["substitutions"].sum() + g_df["deletions"].sum() + g_df["insertions"].sum())
            grp_wers_pct[g] = (g_err / g_ref * 100.0) if g_ref > 0 else 0.0
            
        disp_d_pct = max(grp_wers_pct.values()) - min(grp_wers_pct.values())
        disp_d_fraction = disp_d_pct / 100.0
        
        row_wer = float(row["corpus_wer"])
        row_cer = float(row["corpus_cer"])
        row_d = float(row["disparity_d"])
        
        if abs(row_wer - recomputed_wer_fraction) > 1e-4:
            discrepancies.append({
                "cell": cell_dir.name,
                "metric": "corpus_wer",
                "table_val": row_wer,
                "recomputed_fraction": recomputed_wer_fraction
            })
            
        if abs(row_cer - mean_cer_fraction) > 1e-4:
            discrepancies.append({
                "cell": cell_dir.name,
                "metric": "corpus_cer",
                "table_val": row_cer,
                "recomputed_fraction": mean_cer_fraction
            })
            
        audited_rows.append({
            "cell": cell_dir.name,
            "model": model_key,
            "method": method,
            "order": ord_id,
            "architecture": arch,
            "raw_words": tot_ref_words,
            "raw_errors": tot_errs,
            "wer_pct": round(recomputed_wer_pct, 2),
            "cer_pct": round(mean_cer_pct, 2),
            "disparity_d_pp": round(disp_d_pct, 2),
            "stored_wer_fraction": row_wer,
            "stored_cer_fraction": row_cer,
            "stored_d_fraction": row_d
        })
        
    df_audit = pd.DataFrame(audited_rows)
    print(f"Total cells audited: {len(df_audit)} / 39")
    print(f"Discrepancies found: {len(discrepancies)}")
    if discrepancies:
        print("Discrepancies:", discrepancies)
    else:
        print("PERFECT AUDIT: ALL 39 CELLS EXACTLY MATCH RAW PREDICTIONS!")
        
    print("\nTail (Seq2Seq models):")
    print(df_audit.tail(4)[["cell", "model", "architecture", "wer_pct", "cer_pct", "disparity_d_pp"]].to_string())

if __name__ == "__main__":
    audit_full_results_units_and_values()
