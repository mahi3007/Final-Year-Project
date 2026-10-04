#!/usr/bin/env python3
"""
Stage 6.1: Two-Model Scale & Robustness CTC Extension Runner.
============================================================
Evaluates two additional CTC ASR models on the frozen prequential stream:
1. facebook/wav2vec2-large-960h-lv60 (Wav2Vec2 Large, 315.5M params)
2. facebook/wav2vec2-large-robust-ft-libri-960h (Multi-Domain Robust, 315.5M params)

Methodological Invariants:
- Preserves all Stage 5E and Stage 6 artifacts untouched.
- Saves results into reports/stage6_1/ and reports/stage6_1/checkpoints/.
- Identical 900-clip holdout stream and 300-clip sentinel panel.
- Identical paired bootstrap B=1,000, epsilon_R=0.0000, epsilon_G=0.0200, epsilon_D=0.0200.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import torch

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6_1"
CHECKPOINTS_DIR = REPORTS_DIR / "checkpoints"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

import importlib.util

def _import_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_mod_run = _import_from_file("stage6_run_model", PROJECT_ROOT / "scripts" / "stage6" / "02_run_model.py")
run_model_benchmark = _mod_run.run_model_benchmark

STAGE6_1_MODEL_SPEC: Dict[str, Dict[str, Any]] = {
    "wav2vec2_large_lv60": {
        "model_id": "facebook/wav2vec2-large-960h-lv60",
        "family": "CTC",
        "role": "Larger Pretrained Wav2Vec2 (Libri-Light 60k + LibriSpeech 960h FT)",
        "expected_commit": "8e7d14742e8f98c6bbb24e5231406af321a8f9ce",
        "params": 315471520,
        "is_frozen_baseline": False,
        "ctta_status": "COMPATIBLE",
        "notes": "Large 24-layer Wav2Vec2 pretrained on Libri-Light (60k hours) and fine-tuned on LibriSpeech 960h. Full CTC frame logits + LayerNorms."
    },
    "wav2vec2_large_robust": {
        "model_id": "facebook/wav2vec2-large-robust-ft-libri-960h",
        "family": "CTC",
        "role": "Multi-Domain Robust Pretrained Wav2Vec2 (LibriSpeech 960h FT)",
        "expected_commit": "5d28473cc25ef7b338c9f731fe55626c4b082f58",
        "params": 315471520,
        "is_frozen_baseline": False,
        "ctta_status": "COMPATIBLE",
        "notes": "Large 24-layer Wav2Vec2 with multi-domain robust pretraining (CommonVoice, Switchboard, Fisher) fine-tuned on LibriSpeech 960h. Full CTC frame logits + LayerNorms."
    }
}


def run_stage6_1_benchmark(
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    force_rerun: bool = False,
    selected_models: List[str] = None
) -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 6.1: TWO-MODEL SCALE & ROBUSTNESS CTC EXTENSION BENCHMARK")
    print("=" * 80)
    print(f"Device: {device} | Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")

    # Generate Manifest
    manifest_path = REPORTS_DIR / "model_compatibility_manifest.json"
    manifest_data = {
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": "6.1",
        "protocol_version": "v1.0-cv27-amended",
        "total_models": len(STAGE6_1_MODEL_SPEC),
        "compatible_ctta_models": len(STAGE6_1_MODEL_SPEC),
        "incompatible_ctta_models": 0,
        "models": STAGE6_1_MODEL_SPEC
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Saved Stage 6.1 compatibility manifest: {manifest_path}")

    model_keys = selected_models or list(STAGE6_1_MODEL_SPEC.keys())
    print(f"\nExecution Queue ({len(model_keys)} models): {model_keys}")

    all_model_results: Dict[str, Dict[str, Any]] = {}
    benchmark_rows: List[Dict[str, Any]] = []
    group_rows: List[Dict[str, Any]] = []
    dsg_summary_rows: List[Dict[str, Any]] = []

    t_suite_start = time.time()

    for idx, m_key in enumerate(model_keys):
        print("\n" + "#" * 80)
        print(f"STAGE 6.1 MODEL {idx + 1}/{len(model_keys)}: [{m_key.upper()}]")
        print("#" * 80)

        summary_file = CHECKPOINTS_DIR / f"{m_key}_summary.json"

        # Check for completed model checkpoint
        if summary_file.exists() and not force_rerun:
            print(f"Model [{m_key}] summary found in checkpoints. Loading...")
            with open(summary_file, "r", encoding="utf-8") as f:
                res = json.load(f)
        else:
            t_mod_start = time.time()
            res = run_model_benchmark(
                model_name=m_key,
                device=device,
                use_frozen_wav2vec2=False,
                checkpoints_dir=CHECKPOINTS_DIR
            )
            res["execution_time_sec"] = round(time.time() - t_mod_start, 2)

            # Save checkpoint summary
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            print(f"Saved model summary checkpoint: {summary_file}")

        all_model_results[m_key] = res
        spec = STAGE6_1_MODEL_SPEC[m_key]

        # Benchmark table row
        benchmark_rows.append({
            "model_key": m_key,
            "model_name": spec["role"],
            "model_id": spec["model_id"],
            "architecture_family": spec["family"],
            "ctta_status": spec["ctta_status"],
            "no_adapt_wer": f"{res['no_adapt_wer']:.2f}%",
            "suta_wer": f"{res['suta_wer']:.2f}%",
            "dsuta_wer": f"{res['dsuta_wer']:.2f}%",
            "dmsuta_wer": f"{res['dmsuta_wer']:.2f}%",
            "dsg_wer": f"{res['dsg_wer']:.2f}%",
            "dsg_delta_r": f"{res['dsg_delta_r']:+.2f} pp",
            "dsg_delta_d": f"{res['dsg_delta_d']:+.2f} pp",
            "dsg_max_delta_g": f"{res['dsg_max_delta_g']:+.2f} pp",
            "dsg_accepted": res["dsg_accepted"],
            "dsg_rejected": res["dsg_rejected"],
        })

        # DSG summary row
        acc = res["dsg_accepted"]
        rej = res["dsg_rejected"]
        rate = (acc / (acc + rej) * 100.0) if (acc + rej) > 0 else 0.0
        dsg_summary_rows.append({
            "model_key": m_key,
            "model_id": spec["model_id"],
            "architecture_family": spec["family"],
            "candidate_updates": acc + rej,
            "accepted_updates": acc,
            "rejected_updates": rej,
            "acceptance_rate": f"{rate:.1f}%",
            "statistical_rejections": rej,
            "fail_closed_errors": 0,
            "delta_R_pp": res["dsg_delta_r"],
            "delta_D_pp": res["dsg_delta_d"],
            "max_delta_g_pp": res["dsg_max_delta_g"]
        })

        # Group metrics rows
        if "all_method_metrics" in res:
            for method_name, m_data in res["all_method_metrics"].items():
                for group_name, g_wer in m_data.get("group_wers", {}).items():
                    st = m_data.get("group_stats", {}).get(group_name, {})
                    group_rows.append({
                        "model_key": m_key,
                        "model_id": spec["model_id"],
                        "method": method_name,
                        "accent_stratum": group_name,
                        "wer": round(g_wer, 4),
                        "substitutions": st.get("sub", 0),
                        "deletions": st.get("del", 0),
                        "insertions": st.get("ins", 0),
                        "total_errors": st.get("errors", 0),
                        "reference_words": st.get("ref_words", 0)
                    })

        # Aggressive memory cleanup between models
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    t_suite_total = time.time() - t_suite_start
    print("\n" + "=" * 80)
    print(f"STAGE 6.1 EXECUTION COMPLETE ({t_suite_total:.1f}s / {t_suite_total/60:.2f} mins)")
    print("=" * 80)

    # Export CSVs
    bench_df = pd.DataFrame(benchmark_rows)
    bench_csv = REPORTS_DIR / "stage6_1_benchmark.csv"
    bench_df.to_csv(bench_csv, index=False)
    print(f"Saved: {bench_csv}")

    dsg_df = pd.DataFrame(dsg_summary_rows)
    dsg_csv = REPORTS_DIR / "stage6_1_dsg_summary.csv"
    dsg_df.to_csv(dsg_csv, index=False)
    print(f"Saved: {dsg_csv}")

    if group_rows:
        grp_df = pd.DataFrame(group_rows)
        grp_csv = REPORTS_DIR / "stage6_1_group_metrics.csv"
        grp_df.to_csv(grp_csv, index=False)
        print(f"Saved: {grp_csv}")

    print("\nSTAGE 6.1 BENCHMARK SUMMARY:")
    print(bench_df.to_string(index=False))

    return {
        "benchmark_csv": str(bench_csv),
        "dsg_summary_csv": str(dsg_csv),
        "results": all_model_results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Stage 6.1 Two-Model CTC Extension.")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--force_rerun", action="store_true", help="Force rerun even if checkpointed")
    parser.add_argument("--models", type=str, default="", help="Comma-separated model keys")
    args = parser.parse_args()

    sel_models = [m.strip() for m in args.models.split(",") if m.strip()] or None
    run_stage6_1_benchmark(
        device=args.device,
        force_rerun=args.force_rerun,
        selected_models=sel_models
    )
