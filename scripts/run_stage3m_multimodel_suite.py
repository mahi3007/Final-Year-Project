"""
Stage 3M Multi-Model CTTA Discovery Suite Runner
=================================================
Protocol: v1.1.0-model-expansion
Standard: ADR-005

Executes the frozen 39-cell experimental matrix:
- 3 CTC Development Backbones (wav2vec2_base, data2vec_base, wav2vec2_100h)
  x 4 Adaptation Methods (no_adapt, suta, dsuta, dmsuta)
  x 3 Stream Orderings (ORDER_A, ORDER_B, ORDER_C)
  = 36 conditions
- 3 Seq2Seq Portability Controls (whisper_base, distil_whisper_small, whisper_tiny)
  x static No-Adapt on frozen 60-utterance stream
  = 3 conditions
Total: 39 designated experiment cells.

Outputs are written exclusively to:
- results/stage3_multimodel/
- manifests/stage3m_experiment_manifest.json
Historical Stage 3 artifacts in reports/ctta/ remain strictly immutable.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from rich.console import Console

from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment
from dsg_ctta.offline.bootstrap import paired_speaker_cluster_bootstrap
from dsg_ctta.models.registry import MODEL_CATALOG, create_asr_model
from dsg_ctta.data.normalization import TextNormalizer

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_git_commit() -> str:
    try:
        import subprocess
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "uncommitted_workspace_state"


def run_stage3m_suite():
    split_csv_path = PROJECT_ROOT / "datasets" / "splits" / "final_test.csv"
    assert split_csv_path.exists(), f"Missing split file: {split_csv_path}"
    
    # Compute split hash
    split_hash = hashlib.sha256(split_csv_path.read_bytes()).hexdigest()
    utterances = load_partition_from_csv(str(split_csv_path))
    assert len(utterances) == 60, f"Expected 60 utterances, got {len(utterances)}"
    
    results_base_dir = PROJECT_ROOT / "results" / "stage3_multimodel"
    results_base_dir.mkdir(parents=True, exist_ok=True)
    
    ctc_models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    ctc_methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
    
    seq2seq_models = ["whisper_base", "distil_whisper_small", "whisper_tiny"]
    
    adapter_configs = {
        "no_adapt": {},
        "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
        "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
    }
    
    console.print(f"[bold cyan]================================================================[/bold cyan]")
    console.print(f"[bold cyan]STARTING STAGE 3M MULTI-MODEL EXPERIMENTAL SUITE (39 CELLS)[/bold cyan]")
    console.print(f"[cyan]Protocol: v1.1.0-model-expansion | Dataset: final_test.csv ({len(utterances)} utts)[/cyan]")
    console.print(f"[bold cyan]================================================================[/bold cyan]")
    
    manifest_records = []
    matrix_rows = []
    
    # 1. Run 36 CTC Conditions
    total_ctc_cells = len(ctc_models) * len(ctc_methods) * len(orders)
    cell_idx = 0
    
    for model_name in ctc_models:
        for method in ctc_methods:
            for order_id in orders:
                cell_idx += 1
                exp_id = f"EXP_v1.1.0_STAGE3M_{model_name}_{method}_{order_id.lower()}"
                out_dir = results_base_dir / f"{model_name}_{method}_{order_id.lower()}"
                
                # Check resume capability
                sum_path = out_dir / "summary.json"
                pred_path = out_dir / "predictions.csv"
                if sum_path.exists() and pred_path.exists():
                    console.print(f"[green][{cell_idx}/{total_ctc_cells}] Resuming completed cell: {exp_id}[/green]")
                    with open(sum_path, "r", encoding="utf-8") as f:
                        res = json.load(f)
                    elapsed = 0.0
                else:
                    console.print(f"\n[bold yellow][{cell_idx}/{total_ctc_cells}] Executing CTC Cell: {exp_id}[/bold yellow]")
                    t0 = time.time()
                    res = run_prequential_stream_experiment(
                        utterances=utterances,
                        model_name=model_name,
                        method_name=method,
                        adapter_config=adapter_configs[method],
                        ordering_id=order_id,
                        window_size_k=4,
                        device="cpu",
                        output_dir=str(out_dir),
                        seed=42,
                        experiment_id=exp_id
                    )
                    elapsed = time.time() - t0
                
                with open(sum_path, "r", encoding="utf-8") as f:
                    sum_data = json.load(f)
                pred_df = pd.read_csv(pred_path)
                
                total_words = int(pred_df["reference_length"].sum())
                total_errors = int(pred_df["substitutions"].sum() + pred_df["deletions"].sum() + pred_df["insertions"].sum())
                wer_val = round(float(total_errors / total_words if total_words > 0 else 0.0), 4)
                cer_val = round(float(pred_df["cer"].mean()), 4)
                disp_val = round(float(sum_data["disparity_d"]), 4)
                
                manifest_records.append({
                    "cell_index": cell_idx,
                    "experiment_id": exp_id,
                    "model_key": model_name,
                    "model_id": MODEL_CATALOG[model_name]["model_id"],
                    "architecture": "CTC",
                    "method": method,
                    "ordering_id": order_id,
                    "window_size_k": 4,
                    "total_windows": 15,
                    "reference_words": total_words,
                    "corpus_wer": wer_val,
                    "corpus_cer": cer_val,
                    "disparity_d": disp_val,
                    "elapsed_seconds": round(elapsed, 2),
                    "output_dir": str(out_dir.relative_to(PROJECT_ROOT))
                })
                
                # Record detailed group values
                row_dict = {
                    "model_key": model_name,
                    "architecture": "CTC",
                    "method": method,
                    "ordering_id": order_id,
                    "corpus_wer": wer_val,
                    "corpus_cer": cer_val,
                    "disparity_d": disp_val,
                    "total_errors": total_errors,
                    "reference_words": total_words
                }
                for g_id, g_wer in sum_data["group_wers"].items():
                    row_dict[f"wer_{g_id.lower()}"] = g_wer
                matrix_rows.append(row_dict)
                
    # 2. Run 3 Seq2Seq Static Portability Controls
    seq_idx = 0
    for model_name in seq2seq_models:
        seq_idx += 1
        exp_id = f"EXP_v1.1.0_STAGE3M_{model_name}_static_no_adapt"
        out_dir = results_base_dir / f"{model_name}_static_no_adapt"
        
        sum_path = out_dir / "summary.json"
        pred_path = out_dir / "predictions.csv"
        if sum_path.exists() and pred_path.exists():
            console.print(f"[green][{seq_idx}/{len(seq2seq_models)}] Resuming completed Seq2Seq cell: {exp_id}[/green]")
            elapsed = 0.0
        else:
            console.print(f"\n[bold magenta][{seq_idx}/{len(seq2seq_models)}] Executing Seq2Seq Static Control: {exp_id}[/bold magenta]")
            t0 = time.time()
            res = run_prequential_stream_experiment(
                utterances=utterances,
                model_name=model_name,
                method_name="no_adapt",
                adapter_config={},
                ordering_id="ORDER_A",
                window_size_k=4,
                device="cpu",
                output_dir=str(out_dir),
                seed=42,
                experiment_id=exp_id
            )
            elapsed = time.time() - t0
        
        with open(sum_path, "r", encoding="utf-8") as f:
            sum_data = json.load(f)
        pred_df = pd.read_csv(pred_path)
        
        total_words = int(pred_df["reference_length"].sum())
        total_errors = int(pred_df["substitutions"].sum() + pred_df["deletions"].sum() + pred_df["insertions"].sum())
        wer_val = round(float(total_errors / total_words if total_words > 0 else 0.0), 4)
        cer_val = round(float(pred_df["cer"].mean()), 4)
        disp_val = round(float(sum_data["disparity_d"]), 4)
        
        manifest_records.append({
            "cell_index": cell_idx + seq_idx,
            "experiment_id": exp_id,
            "model_key": model_name,
            "model_id": MODEL_CATALOG[model_name]["model_id"],
            "architecture": "SEQ2SEQ",
            "method": "no_adapt",
            "ordering_id": "ORDER_A (static)",
            "window_size_k": 4,
            "total_windows": 15,
            "reference_words": total_words,
            "corpus_wer": wer_val,
            "corpus_cer": cer_val,
            "disparity_d": disp_val,
            "elapsed_seconds": round(elapsed, 2),
            "output_dir": str(out_dir.relative_to(PROJECT_ROOT)),
            "note": "Static architectural portability baseline (frame-entropy CTTA incompatible)"
        })
        
        row_dict = {
            "model_key": model_name,
            "architecture": "SEQ2SEQ",
            "method": "no_adapt",
            "ordering_id": "ORDER_A",
            "corpus_wer": wer_val,
            "corpus_cer": cer_val,
            "disparity_d": disp_val,
            "total_errors": total_errors,
            "reference_words": total_words
        }
        for g_id, g_wer in sum_data["group_wers"].items():
            row_dict[f"wer_{g_id.lower()}"] = g_wer
        matrix_rows.append(row_dict)
        
    # 3. Verify No-Adapt Stream Order Invariance Control
    console.print("\n[bold cyan]Verifying No-Adapt Order Invariance Invariant across all models...[/bold cyan]")
    df_matrix = pd.DataFrame(matrix_rows)
    for model_name in ctc_models:
        m_na = df_matrix[(df_matrix["model_key"] == model_name) & (df_matrix["method"] == "no_adapt")]
        wers = m_na["corpus_wer"].tolist()
        errors = m_na["total_errors"].tolist()
        assert len(set(errors)) == 1, (
            f"INVARIANT VIOLATION: No-Adapt produced different error counts for {model_name} across orders! {errors}"
        )
        console.print(f"[green]PASS: {model_name} No-Adapt produces identical {errors[0]} errors ({wers[0]:.2f}%) across all 3 orders.[/green]")
        
    # 4. Compute Adaptation Deltas (vs No-Adapt within each model and order)
    extended_rows = []
    for model_name in ctc_models:
        for order_id in orders:
            na_row = df_matrix[(df_matrix["model_key"] == model_name) & (df_matrix["method"] == "no_adapt") & (df_matrix["ordering_id"] == order_id)].iloc[0]
            na_wer = na_row["corpus_wer"]
            na_disp = na_row["disparity_d"]
            
            for method in ctc_methods:
                curr_row = df_matrix[(df_matrix["model_key"] == model_name) & (df_matrix["method"] == method) & (df_matrix["ordering_id"] == order_id)].iloc[0].to_dict()
                curr_wer = curr_row["corpus_wer"]
                curr_disp = curr_row["disparity_d"]
                
                delta_r = curr_wer - na_wer
                delta_d = curr_disp - na_disp
                
                # Compute subgroup deltas
                group_names = ["arabic", "hindi", "korean", "mandarin", "spanish", "vietnamese"]
                max_delta_g = -999.0
                worst_group = ""
                for g in group_names:
                    g_delta = curr_row[f"wer_{g}"] - na_row[f"wer_{g}"]
                    curr_row[f"delta_{g}"] = round(g_delta, 2)
                    if g_delta > max_delta_g:
                        max_delta_g = g_delta
                        worst_group = g.capitalize()
                        
                curr_row["delta_r"] = round(delta_r, 2)
                curr_row["delta_d"] = round(delta_d, 2)
                curr_row["max_delta_g"] = round(max_delta_g, 2)
                curr_row["worst_group"] = worst_group
                extended_rows.append(curr_row)
                
    # Add Seq2Seq rows to extended table
    for model_name in seq2seq_models:
        s_row = df_matrix[(df_matrix["model_key"] == model_name)].iloc[0].to_dict()
        s_row["delta_r"] = 0.00
        s_row["delta_d"] = 0.00
        s_row["max_delta_g"] = 0.00
        s_row["worst_group"] = "N/A (Static)"
        for g in ["arabic", "hindi", "korean", "mandarin", "spanish", "vietnamese"]:
            s_row[f"delta_{g}"] = 0.00
        extended_rows.append(s_row)
        
    df_extended = pd.DataFrame(extended_rows)
    csv_out = results_base_dir / "stage3m_full_results.csv"
    df_extended.to_csv(csv_out, index=False)
    console.print(f"\n[bold green]Saved Stage 3M consolidated results table to: {csv_out}[/bold green]")
    
    # 5. Compute Paired Speaker-Cluster Bootstrap Estimates
    console.print("\n[bold cyan]Computing paired speaker-cluster bootstrap estimates (B=1000)...[/bold cyan]")
    bootstrap_records = []
    
    for model_name in ctc_models:
        for order_id in orders:
            na_dir = results_base_dir / f"{model_name}_no_adapt_{order_id.lower()}"
            na_preds = pd.read_csv(na_dir / "predictions.csv")
            
            for method in ["suta", "dsuta", "dmsuta"]:
                meth_dir = results_base_dir / f"{model_name}_{method}_{order_id.lower()}"
                meth_preds = pd.read_csv(meth_dir / "predictions.csv")
                
                # Run paired speaker bootstrap
                b_res = paired_speaker_cluster_bootstrap(
                    records_base=na_preds.to_dict(orient="records"),
                    records_adapted=meth_preds.to_dict(orient="records"),
                    num_replicates=1000,
                    alpha=0.05,
                    seed=42 + len(bootstrap_records)
                )
                
                delta_r_b = b_res["delta_r"]
                delta_d_b = b_res["delta_d"]
                max_delta_g_b = b_res["max_delta_g"]
                
                bootstrap_records.append({
                    "model_key": model_name,
                    "method": method,
                    "ordering_id": order_id,
                    "point_delta_r": round(delta_r_b.point_estimate, 4),
                    "ci95_delta_r": [round(delta_r_b.ci_lower_95, 4), round(delta_r_b.ci_upper_95, 4)],
                    "ucb95_delta_r": round(delta_r_b.ucb_95, 4),
                    "point_delta_d": round(delta_d_b.point_estimate, 4),
                    "ci95_delta_d": [round(delta_d_b.ci_lower_95, 4), round(delta_d_b.ci_upper_95, 4)],
                    "ucb95_delta_d": round(delta_d_b.ucb_95, 4),
                    "point_max_delta_g": round(max_delta_g_b.point_estimate, 4),
                    "ucb95_max_delta_g": round(max_delta_g_b.ucb_95, 4),
                    "note": "Sensitivity estimate only: stream contains N=6 speakers (1/group). Pop-level inference deferred to Stage 4M."
                })
                
    df_bootstrap = pd.DataFrame(bootstrap_records)
    boot_csv_out = results_base_dir / "stage3m_bootstrap_uncertainty.csv"
    df_bootstrap.to_csv(boot_csv_out, index=False)
    console.print(f"[bold green]Saved Stage 3M bootstrap uncertainty table to: {boot_csv_out}[/bold green]")
    
    # 6. Save Manifest JSON
    manifest_payload = {
        "protocol_version": "v1.1.0-model-expansion",
        "stage": "Stage 3M Multi-Model CTTA Discovery",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": get_git_commit(),
        "dataset": {
            "path": "datasets/splits/final_test.csv",
            "sha256": split_hash,
            "total_utterances": 60,
            "total_speakers": 6,
            "speakers_per_group": 1,
            "reference_words": 552
        },
        "streaming_parameters": {
            "window_size_k": 4,
            "total_windows": 15,
            "orders": orders
        },
        "total_cells": len(manifest_records),
        "ctc_cells": total_ctc_cells,
        "seq2seq_cells": len(seq2seq_models),
        "cells": manifest_records
    }
    
    manifest_path = PROJECT_ROOT / "manifests" / "stage3m_experiment_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)
    console.print(f"[bold green]Saved Stage 3M experiment manifest to: {manifest_path}[/bold green]")
    
    console.print(f"\n[bold green]================================================================[/bold green]")
    console.print(f"[bold green]ALL 39 STAGE 3M EXPERIMENT CELLS COMPLETED SUCCESSFULLY![/bold green]")
    console.print(f"[bold green]================================================================[/bold green]")


if __name__ == "__main__":
    run_stage3m_suite()
