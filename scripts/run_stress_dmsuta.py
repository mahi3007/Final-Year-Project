"""
Stage 4.1: Complete Acoustic Stress Suite with DMSUTA Evaluation.
Runs DMSUTA across Clean, Noise Moderate, Noise Severe, Babble Moderate, and Reverberation.
Then recomputes complete 20-cell stress matrix and paired speaker-cluster bootstrap.
"""

import os
import json
import time
import shutil
import pandas as pd
from typing import Dict, List, Any

from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment
from dsg_ctta.offline.bootstrap import paired_speaker_cluster_bootstrap


def run_complete_stress_suite():
    stress_conds = [
        ("clean", "datasets/splits/stage4_characterization.csv"),
        ("noise_moderate", "datasets/splits/stage4_noise_moderate.csv"),
        ("noise_severe", "datasets/splits/stage4_noise_severe.csv"),
        ("babble_moderate", "datasets/splits/stage4_babble_moderate.csv"),
        ("reverberation", "datasets/splits/stage4_reverberation.csv")
    ]

    all_methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    adapter_configs = {
        "no_adapt": {},
        "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
        "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
    }

    output_base_dir = "reports/stage4"
    stress_dir = os.path.join(output_base_dir, "stress_experiments")
    os.makedirs(stress_dir, exist_ok=True)

    # 1. Ensure DMSUTA is run for all conditions
    for cond_name, split_path in stress_conds:
        out_dir = os.path.join(stress_dir, f"{cond_name}_dmsuta")
        sum_path = os.path.join(out_dir, "summary.json")
        recs_path = os.path.join(out_dir, "predictions.csv")

        if cond_name == "clean" and not os.path.exists(sum_path):
            src_dir = os.path.join(output_base_dir, "multi_order_expanded", "dmsuta_order_a")
            if os.path.exists(src_dir):
                os.makedirs(out_dir, exist_ok=True)
                for fname in os.listdir(src_dir):
                    shutil.copy(os.path.join(src_dir, fname), os.path.join(out_dir, fname))
                print("Copied clean_dmsuta from dmsuta_order_a")

        if not (os.path.exists(sum_path) and os.path.exists(recs_path)):
            print(f"Running DMSUTA on {cond_name}...")
            utts = load_partition_from_csv(split_path)
            res = run_prequential_stream_experiment(
                utterances=utts,
                model_name="wav2vec2_base",
                method_name="dmsuta",
                adapter_config=adapter_configs["dmsuta"],
                ordering_id="ORDER_A",
                window_size_k=4,
                device="cpu",
                output_dir=out_dir,
                seed=42,
                experiment_id=f"stress_{cond_name}_dmsuta"
            )
            print(f"Completed DMSUTA on {cond_name}: WER={res['summary']['corpus_wer']:.4f}")
        else:
            print(f"Cached DMSUTA run found for {cond_name}")

    # 2. Build complete 20-cell Acoustic Stress Matrix (5 conditions x 4 methods)
    delta_g_thresh = 0.0200
    delta_d_thresh = 0.0200

    stress_rows = []
    bootstrap_rows = []

    for cond_name, split_path in stress_conds:
        cond_runs = {}
        cond_recs = {}

        for meth in all_methods:
            run_key = f"{cond_name}_{meth}"
            out_dir = os.path.join(stress_dir, run_key)
            sum_path = os.path.join(out_dir, "summary.json")
            recs_path = os.path.join(out_dir, "predictions.csv")

            with open(sum_path, "r", encoding="utf-8") as sf:
                cond_runs[meth] = {"summary": json.load(sf)}
            cond_recs[meth] = pd.read_csv(recs_path).to_dict(orient="records")

        base_sum = cond_runs["no_adapt"]["summary"]
        base_recs = cond_recs["no_adapt"]

        for meth in all_methods:
            m_sum = cond_runs[meth]["summary"]
            m_recs = cond_recs[meth]

            d_r = m_sum["corpus_wer"] - base_sum["corpus_wer"]
            d_d = m_sum["disparity_d"] - base_sum["disparity_d"]
            g_deltas = {
                g: m_sum["group_wers"].get(g, 0.0) - base_sum["group_wers"].get(g, 0.0)
                for g in base_sum["group_wers"]
            }
            max_dg = max(g_deltas.values()) if g_deltas else 0.0
            worst_g = max(g_deltas, key=g_deltas.get) if g_deltas else "none"

            s_row = {
                "condition": cond_name,
                "method": meth,
                "corpus_wer": round(m_sum["corpus_wer"], 4),
                "delta_r": round(d_r, 4),
                "disparity_d": round(m_sum["disparity_d"], 4),
                "delta_d": round(d_d, 4),
                "max_group_regression": round(max_dg, 4),
                "worst_regressed_group": worst_g if max_dg > 0 else "none",
                "exceeds_delta_G": max_dg > delta_g_thresh,
                "exceeds_delta_D": d_d > delta_d_thresh
            }
            for g, val in g_deltas.items():
                s_row[f"delta_g_{g}"] = round(val, 4)
                s_row[f"wer_{g}"] = round(m_sum["group_wers"].get(g, 0.0), 4)

            stress_rows.append(s_row)

            # Paired speaker-cluster bootstrap (B=1000) for adapted methods under stress
            if meth != "no_adapt":
                boot = paired_speaker_cluster_bootstrap(
                    records_base=base_recs,
                    records_adapted=m_recs,
                    num_replicates=1000,
                    seed=42,
                    alpha=0.05
                )
                b_row = {
                    "condition": cond_name,
                    "method": meth,
                    "num_speaker_clusters": len(set(r["speaker_id"] for r in m_recs)),
                    "delta_r_point": round(boot["delta_r"].point_estimate, 4),
                    "delta_r_mean": round(boot["delta_r"].bootstrap_mean, 4),
                    "delta_r_se": round(boot["delta_r"].bootstrap_std, 4),
                    "delta_r_ci95": f"[{boot['delta_r'].ci_lower_95:.4f}, {boot['delta_r'].ci_upper_95:.4f}]",
                    "delta_d_point": round(boot["delta_d"].point_estimate, 4),
                    "delta_d_mean": round(boot["delta_d"].bootstrap_mean, 4),
                    "delta_d_se": round(boot["delta_d"].bootstrap_std, 4),
                    "delta_d_ci95": f"[{boot['delta_d'].ci_lower_95:.4f}, {boot['delta_d'].ci_upper_95:.4f}]",
                    "delta_d_ucb95": round(boot["delta_d"].ucb_95, 4),
                    "max_dg_point": round(boot["max_delta_g"].point_estimate, 4),
                    "max_dg_mean": round(boot["max_delta_g"].bootstrap_mean, 4),
                    "max_dg_se": round(boot["max_delta_g"].bootstrap_std, 4),
                    "max_dg_ci95": f"[{boot['max_delta_g'].ci_lower_95:.4f}, {boot['max_delta_g'].ci_upper_95:.4f}]",
                    "max_dg_ucb95": round(boot["max_delta_g"].ucb_95, 4)
                }
                bootstrap_rows.append(b_row)

    # Save complete 20-cell stress matrix
    df_stress = pd.DataFrame(stress_rows)
    stress_csv = os.path.join(output_base_dir, "stage4e_acoustic_stress_matrix.csv")
    df_stress.to_csv(stress_csv, index=False)
    print(f"Saved complete 20-cell Acoustic Stress Matrix to: {stress_csv}")

    # Save stress bootstrap table
    df_stress_boot = pd.DataFrame(bootstrap_rows)
    stress_boot_csv = os.path.join(output_base_dir, "stage4e_stress_speaker_cluster_bootstrap.csv")
    df_stress_boot.to_csv(stress_boot_csv, index=False)
    print(f"Saved Stress Bootstrap Table to: {stress_boot_csv}")

    # 3. Update 28-cell Factorial Boundary Condition Map
    matrix_csv = os.path.join(output_base_dir, "stage4d_multi_order_matrix.csv")
    df_clean_matrix = pd.read_csv(matrix_csv)

    boundary_records = []
    for _, r in df_clean_matrix.iterrows():
        boundary_records.append({
            "dimension": "Stream Order",
            "condition": r["ordering"],
            "method": r["method"],
            "window_size_k": 4,
            "overall_wer": r["corpus_wer"],
            "delta_r": r["delta_r"],
            "disparity_d": r["disparity_d"],
            "delta_d": r["delta_d"],
            "max_group_regression": r["max_group_regression"],
            "worst_group": r["worst_regressed_group"],
            "exceeds_delta_G": r["max_group_regression"] > delta_g_thresh,
            "exceeds_delta_D": r["delta_d"] > delta_d_thresh,
            "regime_status": "STABLE" if (r["max_group_regression"] <= delta_g_thresh and r["delta_d"] <= delta_d_thresh) else "UNSTABLE"
        })

    for _, r in df_stress.iterrows():
        if r["condition"] != "clean":
            boundary_records.append({
                "dimension": "Acoustic Shift",
                "condition": r["condition"],
                "method": r["method"],
                "window_size_k": 4,
                "overall_wer": r["corpus_wer"],
                "delta_r": r["delta_r"],
                "disparity_d": r["disparity_d"],
                "delta_d": r["delta_d"],
                "max_group_regression": r["max_group_regression"],
                "worst_group": r["worst_regressed_group"],
                "exceeds_delta_G": r["exceeds_delta_G"],
                "exceeds_delta_D": r["exceeds_delta_D"],
                "regime_status": "STABLE" if (not r["exceeds_delta_G"] and not r["exceeds_delta_D"]) else "UNSTABLE"
            })

    df_boundary = pd.DataFrame(boundary_records)
    boundary_csv = os.path.join(output_base_dir, "stage4g_boundary_condition_map.csv")
    df_boundary.to_csv(boundary_csv, index=False)
    print(f"Saved complete 28-cell Boundary Map to: {boundary_csv}")


if __name__ == "__main__":
    run_complete_stress_suite()
