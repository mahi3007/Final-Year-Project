"""
Stage 3 Extension:
1. Complete the multi-order matrix by executing DSUTA and DMSUTA on ORDER_B and ORDER_C
   on the final_test partition (60 utterances, 6 groups, K=4).
2. Perform paired speaker-cluster bootstrap (1,000 replicates, alpha=0.05) for all adapted methods
   (SUTA, DSUTA, DMSUTA) against No-Adapt across all stream orderings (ORDER_A, ORDER_B, ORDER_C).
3. Generate:
   - reports/ctta/multi_order_all_methods.csv
   - reports/ctta/bootstrap_uncertainty.csv
   - reports/ctta/bootstrap_uncertainty.json
   - Update reports/ctta/discovery_findings.json
"""

import os
import json
import time
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from rich.console import Console

from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment
from dsg_ctta.offline.bootstrap import paired_speaker_cluster_bootstrap, BootstrapResult

console = Console()


def run_missing_experiments(split_csv_path: str = "datasets/splits/final_test.csv"):
    utterances = load_partition_from_csv(split_csv_path)
    console.print(f"[bold cyan]Loaded {len(utterances)} utterances from {split_csv_path}[/bold cyan]")

    adapter_configs = {
        "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
    }

    runs_to_check = [
        ("dsuta", "ORDER_B", "reports/ctta/dsuta_order_b", "stage3_dsuta_wav2vec2_order_b"),
        ("dsuta", "ORDER_C", "reports/ctta/dsuta_order_c", "stage3_dsuta_wav2vec2_order_c"),
        ("dmsuta", "ORDER_B", "reports/ctta/dmsuta_order_b", "stage3_dmsuta_wav2vec2_order_b"),
        ("dmsuta", "ORDER_C", "reports/ctta/dmsuta_order_c", "stage3_dmsuta_wav2vec2_order_c")
    ]

    for method, order_id, out_dir, exp_id in runs_to_check:
        summary_path = os.path.join(out_dir, "summary.json")
        pred_path = os.path.join(out_dir, "predictions.csv")
        if os.path.exists(summary_path) and os.path.exists(pred_path):
            console.print(f"[green]Run already exists: {out_dir}. Skipping computation.[/green]")
            continue

        console.print(f"\n[bold yellow]>>> Executing {method.upper()} on {order_id} ({exp_id}) <<<[/bold yellow]")
        run_prequential_stream_experiment(
            utterances=utterances,
            model_name="wav2vec2_base",
            method_name=method,
            adapter_config=adapter_configs[method],
            ordering_id=order_id,
            window_size_k=4,
            device="cpu",
            output_dir=out_dir,
            seed=42,
            experiment_id=exp_id
        )


def compile_full_multi_order_matrix() -> pd.DataFrame:
    """Compile the complete 4-method x 3-order table."""
    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
    base_dir = "reports/ctta"

    matrix_rows = []

    for ord_id in orders:
        # Load baseline No-Adapt for this order
        if ord_id == "ORDER_A":
            no_adapt_dir = os.path.join(base_dir, "no_adapt")
        else:
            no_adapt_dir = os.path.join(base_dir, f"no_adapt_{ord_id.lower()}")

        with open(os.path.join(no_adapt_dir, "summary.json"), "r") as f:
            base_sum = json.load(f)

        base_wer = base_sum["corpus_wer"]
        base_disp = base_sum["disparity_d"]
        base_gwers = base_sum["group_wers"]

        for meth in methods:
            if meth == "no_adapt":
                m_dir = no_adapt_dir
            elif ord_id == "ORDER_A":
                m_dir = os.path.join(base_dir, meth)
            else:
                m_dir = os.path.join(base_dir, f"{meth}_{ord_id.lower()}")

            with open(os.path.join(m_dir, "summary.json"), "r") as f:
                m_sum = json.load(f)

            m_wer = m_sum["corpus_wer"]
            m_disp = m_sum["disparity_d"]
            m_gwers = m_sum["group_wers"]

            d_r = m_wer - base_wer
            d_d = m_disp - base_disp

            g_deltas = {g: m_gwers.get(g, 0.0) - base_gwers.get(g, 0.0) for g in base_gwers}
            max_dg = max(g_deltas.values()) if g_deltas else 0.0
            worst_g = max(g_deltas, key=g_deltas.get) if g_deltas else "none"

            row = {
                "ordering": ord_id,
                "method": meth,
                "corpus_wer": round(m_wer, 4),
                "delta_r": round(d_r, 4),
                "disparity_d": round(m_disp, 4),
                "delta_d": round(d_d, 4),
                "max_group_regression": round(max_dg, 4),
                "worst_regressed_group": worst_g if max_dg > 0 else "none",
                "num_updates": m_sum.get("num_updates", 0),
                "num_resets": m_sum.get("num_resets", 0),
                "best_group": m_sum.get("best_group_id", ""),
                "worst_group": m_sum.get("worst_group_id", "")
            }
            for g, val in g_deltas.items():
                row[f"delta_g_{g}"] = round(val, 4)
                row[f"wer_{g}"] = round(m_gwers.get(g, 0.0), 4)

            matrix_rows.append(row)

    df_matrix = pd.DataFrame(matrix_rows)
    out_csv = os.path.join(base_dir, "multi_order_all_methods.csv")
    df_matrix.to_csv(out_csv, index=False)
    console.print(f"[bold green]Saved Full Multi-Order Matrix to: {out_csv}[/bold green]")
    return df_matrix


def run_paired_bootstrap_analysis() -> Dict[str, Any]:
    """Run paired speaker-cluster bootstrap (1000 replicates) for each adapted method vs No-Adapt."""
    base_dir = "reports/ctta"
    orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
    adapted_methods = ["suta", "dsuta", "dmsuta"]

    bootstrap_records = []
    full_json_out: Dict[str, Any] = {}

    for ord_id in orders:
        if ord_id == "ORDER_A":
            no_adapt_pred_path = os.path.join(base_dir, "no_adapt", "predictions.csv")
        else:
            no_adapt_pred_path = os.path.join(base_dir, f"no_adapt_{ord_id.lower()}", "predictions.csv")

        df_base = pd.read_csv(no_adapt_pred_path)
        records_base = df_base.to_dict(orient="records")

        # Baseline bootstrap
        base_boot = paired_speaker_cluster_bootstrap(records_base=records_base, num_replicates=1000, seed=42)
        base_key = f"no_adapt_{ord_id.lower()}"
        full_json_out[base_key] = {k: v.dict() for k, v in base_boot.items()}

        bootstrap_records.append({
            "ordering": ord_id,
            "method": "no_adapt",
            "metric": "corpus_wer",
            "point_estimate": round(base_boot["corpus_wer"].point_estimate, 4),
            "bootstrap_mean": round(base_boot["corpus_wer"].bootstrap_mean, 4),
            "bootstrap_std": round(base_boot["corpus_wer"].bootstrap_std, 4),
            "ci_lower_95": round(base_boot["corpus_wer"].ci_lower_95, 4),
            "ci_upper_95": round(base_boot["corpus_wer"].ci_upper_95, 4),
            "ucb_95": round(base_boot["corpus_wer"].ucb_95, 4)
        })
        bootstrap_records.append({
            "ordering": ord_id,
            "method": "no_adapt",
            "metric": "disparity_d",
            "point_estimate": round(base_boot["disparity_d"].point_estimate, 4),
            "bootstrap_mean": round(base_boot["disparity_d"].bootstrap_mean, 4),
            "bootstrap_std": round(base_boot["disparity_d"].bootstrap_std, 4),
            "ci_lower_95": round(base_boot["disparity_d"].ci_lower_95, 4),
            "ci_upper_95": round(base_boot["disparity_d"].ci_upper_95, 4),
            "ucb_95": round(base_boot["disparity_d"].ucb_95, 4)
        })

        for meth in adapted_methods:
            if ord_id == "ORDER_A":
                adapt_pred_path = os.path.join(base_dir, meth, "predictions.csv")
            else:
                adapt_pred_path = os.path.join(base_dir, f"{meth}_{ord_id.lower()}", "predictions.csv")

            df_adapt = pd.read_csv(adapt_pred_path)
            records_adapt = df_adapt.to_dict(orient="records")

            boot_res = paired_speaker_cluster_bootstrap(
                records_base=records_base,
                records_adapted=records_adapt,
                num_replicates=1000,
                seed=42
            )

            exp_key = f"{meth}_{ord_id.lower()}"
            full_json_out[exp_key] = {k: v.dict() for k, v in boot_res.items()}

            # Extract key metrics: delta_r, delta_d, max_delta_g
            for met in ["delta_r", "delta_d", "max_delta_g"]:
                b = boot_res[met]
                bootstrap_records.append({
                    "ordering": ord_id,
                    "method": meth,
                    "metric": met,
                    "point_estimate": round(b.point_estimate, 4),
                    "bootstrap_mean": round(b.bootstrap_mean, 4),
                    "bootstrap_std": round(b.bootstrap_std, 4),
                    "ci_lower_95": round(b.ci_lower_95, 4),
                    "ci_upper_95": round(b.ci_upper_95, 4),
                    "ucb_95": round(b.ucb_95, 4)
                })

    df_boot = pd.DataFrame(bootstrap_records)
    boot_csv_path = os.path.join(base_dir, "bootstrap_uncertainty.csv")
    df_boot.to_csv(boot_csv_path, index=False)
    console.print(f"[bold green]Saved Bootstrap Uncertainty CSV to: {boot_csv_path}[/bold green]")

    boot_json_path = os.path.join(base_dir, "bootstrap_uncertainty.json")
    with open(boot_json_path, "w", encoding="utf-8") as f:
        json.dump(full_json_out, f, indent=2)
    console.print(f"[bold green]Saved Bootstrap Uncertainty JSON to: {boot_json_path}[/bold green]")

    return full_json_out


def main():
    console.print("[bold green]=== Running Stage 3 Multi-Order Extension & Bootstrap Uncertainty ===[/bold green]")
    run_missing_experiments()
    compile_full_multi_order_matrix()
    run_paired_bootstrap_analysis()
    console.print("[bold green]=== Multi-Order Extension & Bootstrap Uncertainty Complete! ===[/bold green]")


if __name__ == "__main__":
    main()
