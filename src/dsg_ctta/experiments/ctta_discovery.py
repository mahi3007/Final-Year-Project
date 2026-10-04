"""
CTTA Discovery Experiment Suite for Stage 3.
Orchestrates:
1. Primary Track A Evaluation on final_test partition (ORDER_A):
   - No-Adaptation Control (no_adapt)
   - SUTA
   - DSUTA
   - DMSUTA
2. Multi-Order Robustness Suite (ORDER_B, ORDER_C)
3. Cross-Method Metric Aggregation & Coupling Assessment
"""

from __future__ import annotations
import os
import json
import time
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from rich.console import Console

from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment

console = Console()


def run_full_stage3_discovery_suite(
    split_csv_path: str = "datasets/splits/final_test.csv",
    window_size_k: int = 4,
    device: str = "cpu",
    output_base_dir: str = "reports/ctta",
    run_multi_order: bool = True
) -> Dict[str, Any]:
    """
    Execute full Stage 3 CTTA discovery experiments across all four methods
    and multiple stream orderings.
    """
    os.makedirs(output_base_dir, exist_ok=True)
    utterances = load_partition_from_csv(split_csv_path)

    console.print(f"[bold green]=====================================================[/bold green]")
    console.print(f"[bold green]Starting DSG-CTTA Stage 3 Discovery Experiment Suite[/bold green]")
    console.print(f"[bold green]=====================================================[/bold green]")
    console.print(f"Partition: [yellow]{split_csv_path}[/yellow] ({len(utterances)} recordings across {len(set(u.speaker_id for u in utterances))} speakers)")

    primary_methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    adapter_configs = {
        "no_adapt": {},
        "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
        "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
    }

    primary_results: Dict[str, Dict[str, Any]] = {}

    # 1. Primary Track A Runs (ORDER_A)
    for method in primary_methods:
        method_out_dir = os.path.join(output_base_dir, method)
        console.print(f"\n[bold cyan]>>> Running Method: {method.upper()} on ORDER_A <<<[/bold cyan]")
        res = run_prequential_stream_experiment(
            utterances=utterances,
            model_name="wav2vec2_base",
            method_name=method,
            adapter_config=adapter_configs[method],
            ordering_id="ORDER_A",
            window_size_k=window_size_k,
            device=device,
            output_dir=method_out_dir,
            seed=42,
            experiment_id=f"stage3_{method}_wav2vec2_order_a"
        )
        primary_results[method] = res

    # 2. Multi-Order Robustness Runs (ORDER_B, ORDER_C for all methods)
    multi_order_results: Dict[str, Dict[str, Any]] = {}
    if run_multi_order:
        orders = ["ORDER_B", "ORDER_C"]
        for ord_id in orders:
            for method in primary_methods:
                exp_key = f"{method}_{ord_id.lower()}"
                ord_out_dir = os.path.join(output_base_dir, f"{method}_{ord_id.lower()}")
                summary_file = os.path.join(ord_out_dir, "summary.json")
                if os.path.exists(summary_file):
                    console.print(f"[green]Loaded existing run: {exp_key}[/green]")
                    with open(summary_file, "r", encoding="utf-8") as sf:
                        multi_order_results[exp_key] = {"summary": json.load(sf)}
                else:
                    console.print(f"\n[bold cyan]>>> Running Robustness: {method.upper()} on {ord_id} <<<[/bold cyan]")
                    res = run_prequential_stream_experiment(
                        utterances=utterances,
                        model_name="wav2vec2_base",
                        method_name=method,
                        adapter_config=adapter_configs[method],
                        ordering_id=ord_id,
                        window_size_k=window_size_k,
                        device=device,
                        output_dir=ord_out_dir,
                        seed=42,
                        experiment_id=f"stage3_{method}_wav2vec2_{ord_id.lower()}"
                    )
                    multi_order_results[exp_key] = res

    # 3. Cross-Method Comparison & Delta Calculations
    no_adapt_summary = primary_results["no_adapt"]["summary"]
    baseline_wer = no_adapt_summary["corpus_wer"]
    baseline_disp = no_adapt_summary["disparity_d"]
    baseline_group_wers = no_adapt_summary["group_wers"]

    comparison_rows: List[Dict[str, Any]] = []

    for method in primary_methods:
        s = primary_results[method]["summary"]
        curr_wer = s["corpus_wer"]
        curr_disp = s["disparity_d"]
        curr_group_wers = s["group_wers"]

        # Delta R = WER(method) - WER(no_adapt)
        delta_r = curr_wer - baseline_wer

        # Per-group deltas: Delta_g = WER_g(method) - WER_g(no_adapt)
        group_deltas = {
            g: curr_group_wers.get(g, 0.0) - baseline_group_wers.get(g, 0.0)
            for g in baseline_group_wers
        }
        max_delta_g = max(group_deltas.values()) if group_deltas else 0.0
        worst_regressed_group = max(group_deltas, key=group_deltas.get) if group_deltas else "none"

        # Disparity change Delta_D = D(method) - D(no_adapt)
        delta_d = curr_disp - baseline_disp

        row = {
            "method": method,
            "ordering": "ORDER_A",
            "corpus_wer": round(curr_wer, 4),
            "delta_r": round(delta_r, 4),
            "speaker_macro_wer": round(s["speaker_macro_wer"], 4),
            "disparity_d": round(curr_disp, 4),
            "delta_d": round(delta_d, 4),
            "max_group_regression": round(max_delta_g, 4),
            "worst_regressed_group": worst_regressed_group,
            "best_group": s["best_group_id"],
            "worst_group": s["worst_group_id"],
            "adaptation_time_sec": round(s["total_adaptation_time_seconds"], 2),
            "num_updates": s["num_updates"],
            "num_resets": s["num_resets"]
        }
        for g, dg in group_deltas.items():
            row[f"delta_g_{g}"] = round(dg, 4)
            row[f"wer_{g}"] = round(curr_group_wers.get(g, 0.0), 4)

        comparison_rows.append(row)

    df_comp = pd.DataFrame(comparison_rows)
    comp_csv_path = os.path.join(output_base_dir, "cross_method_comparison.csv")
    df_comp.to_csv(comp_csv_path, index=False)
    console.print(f"\n[bold green]Saved Cross-Method Comparison Table to: {comp_csv_path}[/bold green]")

    # 4. Multi-Order Sensitivity Table (all methods)
    order_rows = []
    if run_multi_order:
        for ord_name, ord_label in [("ORDER_A", "order_a"), ("ORDER_B", "order_b"), ("ORDER_C", "order_c")]:
            if ord_name == "ORDER_A":
                base_sum = primary_results["no_adapt"]["summary"]
            else:
                base_sum = multi_order_results[f"no_adapt_{ord_label}"]["summary"]

            for meth in primary_methods:
                if ord_name == "ORDER_A":
                    m_sum = primary_results[meth]["summary"]
                else:
                    m_sum = multi_order_results[f"{meth}_{ord_label}"]["summary"]

                d_r = m_sum["corpus_wer"] - base_sum["corpus_wer"]
                d_d = m_sum["disparity_d"] - base_sum["disparity_d"]
                g_deltas = {
                    g: m_sum["group_wers"].get(g, 0.0) - base_sum["group_wers"].get(g, 0.0)
                    for g in base_sum["group_wers"]
                }
                max_dg = max(g_deltas.values()) if g_deltas else 0.0
                worst_g = max(g_deltas, key=g_deltas.get) if g_deltas else "none"

                order_rows.append({
                    "ordering": ord_name,
                    "method": meth,
                    "corpus_wer": round(m_sum["corpus_wer"], 4),
                    "delta_r": round(d_r, 4),
                    "disparity_d": round(m_sum["disparity_d"], 4),
                    "delta_d": round(d_d, 4),
                    "max_group_regression": round(max_dg, 4),
                    "worst_regressed_group": worst_g if max_dg > 0 else "none"
                })

        df_orders = pd.DataFrame(order_rows)
        order_csv_path = os.path.join(output_base_dir, "multi_order_all_methods.csv")
        df_orders.to_csv(order_csv_path, index=False)
        console.print(f"[bold green]Saved Multi-Order Matrix Table to: {order_csv_path}[/bold green]")

    # 5. Load Bootstrap Uncertainty if available
    boot_json_path = os.path.join(output_base_dir, "bootstrap_uncertainty.json")
    bootstrap_data = {}
    if os.path.exists(boot_json_path):
        with open(boot_json_path, "r", encoding="utf-8") as bf:
            bootstrap_data = json.load(bf)

    # 6. Export Summary JSON of Discovery Findings
    discovery_summary = {
        "protocol_version": "v1.0.0-canonical",
        "split": split_csv_path,
        "window_size_k": window_size_k,
        "primary_results": {m: primary_results[m]["summary"] for m in primary_methods},
        "cross_method_comparison": comparison_rows,
        "multi_order_robustness": order_rows if run_multi_order else [],
        "bootstrap_uncertainty": bootstrap_data
    }
    disc_json_path = os.path.join(output_base_dir, "discovery_findings.json")
    with open(disc_json_path, "w", encoding="utf-8") as f:
        json.dump(discovery_summary, f, indent=2)

    console.print(f"[bold green]Stage 3 Discovery Suite Completed Successfully![/bold green]")
    return discovery_summary


if __name__ == "__main__":
    run_full_stage3_discovery_suite()
