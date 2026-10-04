#!/usr/bin/env python3
"""
Stage 6: Master Sequential Benchmark Runner across 6 ASR Architectures.
=======================================================================
Executes the Stage 6 cross-architecture evaluation protocol:
1. facebook/wav2vec2-base-960h (Primary baseline - Frozen Stage 5E)
2. openai/whisper-base (Autoregressive portability model)
3. facebook/hubert-large-ls960-ft (Self-supervised encoder - Acoustic Cluster SSL)
4. facebook/data2vec-audio-base-960h (Self-supervised encoder - Multimodal SSL)
5. distil-whisper/distil-small.en (Lightweight autoregressive model)
6. jonatasgrosman/wav2vec2-large-xlsr-53-english (Cross-lingual pretrained CTC)

Methodological Invariants:
- Sequential execution (1 model at a time) to guarantee VRAM stability (<8 GB).
- Garbage collection and torch.cuda.empty_cache() between models.
- Compatibility gate: Non-CTC seq2seq models evaluated for No-Adapt only;
  CTTA methods marked INCOMPATIBLE without algorithm substitution.
- Automatic checkpointing and resumption: skips already completed models/methods.
- Generates final benchmark tables and summary CSVs.
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

REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6"
CHECKPOINTS_DIR = REPORTS_DIR / "checkpoints"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

import importlib.util

def _import_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_mod_compat = _import_from_file("stage6_compat", PROJECT_ROOT / "scripts" / "stage6" / "01_model_compatibility.py")
STAGE6_MODEL_SPEC = _mod_compat.STAGE6_MODEL_SPEC
audit_compatibility = _mod_compat.audit_compatibility

_mod_run = _import_from_file("stage6_run_model", PROJECT_ROOT / "scripts" / "stage6" / "02_run_model.py")
run_model_benchmark = _mod_run.run_model_benchmark


def run_all_models_benchmark(
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    force_rerun: bool = False,
    selected_models: List[str] = None
) -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 6: MASTER CROSS-ARCHITECTURE GENERALIZATION BENCHMARK")
    print("=" * 80)
    print(f"Device: {device} | Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")

    # Step 1: Preflight Compatibility Audit
    compat_manifest = audit_compatibility()

    model_keys = selected_models or list(STAGE6_MODEL_SPEC.keys())
    print(f"\nExecution Queue ({len(model_keys)} models): {model_keys}")

    all_model_results: Dict[str, Dict[str, Any]] = {}
    benchmark_rows: List[Dict[str, Any]] = []
    group_rows: List[Dict[str, Any]] = []
    dsg_summary_rows: List[Dict[str, Any]] = []

    t_suite_start = time.time()

    for idx, m_key in enumerate(model_keys):
        print("\n" + "#" * 80)
        print(f"MODEL {idx + 1}/{len(model_keys)}: [{m_key.upper()}]")
        print("#" * 80)

        summary_file = CHECKPOINTS_DIR / f"{m_key}_summary.json"

        # Check for completed model checkpoint
        if summary_file.exists() and not force_rerun:
            print(f"Model [{m_key}] summary found in checkpoints. Loading...")
            with open(summary_file, "r", encoding="utf-8") as f:
                res = json.load(f)
        else:
            t_model_start = time.time()
            res = run_model_benchmark(
                model_name=m_key,
                device=device,
                use_frozen_wav2vec2=(m_key == "wav2vec2_base" and not force_rerun)
            )
            t_model_elapsed = time.time() - t_model_start
            res["execution_time_sec"] = round(t_model_elapsed, 2)

            # Save model checkpoint summary
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2)
            print(f"Model [{m_key}] completed in {t_model_elapsed:.1f}s. Checkpoint saved.")

        all_model_results[m_key] = res

        # Build Main Benchmark Row
        def fmt_pct(val):
            if isinstance(val, (int, float)):
                return f"{val:.2f}%"
            return str(val)

        def fmt_pp(val):
            if isinstance(val, (int, float)):
                return f"{val:+.2f} pp"
            return str(val)

        spec = STAGE6_MODEL_SPEC[m_key]
        b_row = {
            "model_key": m_key,
            "model_name": spec["role"],
            "model_id": spec["model_id"],
            "architecture_family": spec["family"],
            "ctta_status": spec["ctta_status"],
            "no_adapt_wer": fmt_pct(res.get("no_adapt_wer")),
            "suta_wer": fmt_pct(res.get("suta_wer")),
            "dsuta_wer": fmt_pct(res.get("dsuta_wer")),
            "dmsuta_wer": fmt_pct(res.get("dmsuta_wer")),
            "dsg_wer": fmt_pct(res.get("dsg_wer")),
            "dsg_delta_r": fmt_pp(res.get("dsg_delta_r")),
            "dsg_delta_d": fmt_pp(res.get("dsg_delta_d")),
            "dsg_max_delta_g": fmt_pp(res.get("dsg_max_delta_g")),
            "dsg_accepted": res.get("dsg_accepted", "N/A"),
            "dsg_rejected": res.get("dsg_rejected", "N/A"),
        }
        benchmark_rows.append(b_row)

        # Build DSG Summary Row
        d_row = {
            "model_key": m_key,
            "model_id": spec["model_id"],
            "architecture_family": spec["family"],
            "candidate_updates": 225 if spec["family"] == "CTC" else "INCOMPATIBLE",
            "accepted_updates": res.get("dsg_accepted", "N/A"),
            "rejected_updates": res.get("dsg_rejected", "N/A"),
            "acceptance_rate": f"{(res.get('dsg_accepted', 0) / 225.0 * 100):.1f}%" if isinstance(res.get("dsg_accepted"), (int, float)) else "N/A",
            "statistical_rejections": res.get("dsg_rejected", "N/A"),
            "fail_closed_errors": 0 if spec["family"] == "CTC" else "N/A",
            "delta_R_pp": res.get("dsg_delta_r", "N/A"),
            "delta_D_pp": res.get("dsg_delta_d", "N/A"),
            "max_delta_g_pp": res.get("dsg_max_delta_g", "N/A"),
        }
        dsg_summary_rows.append(d_row)

        # Build Group Metrics Rows
        if "all_method_metrics" in res:
            for m_name, m_stats in res["all_method_metrics"].items():
                for grp, g_wer in m_stats.get("group_wers", {}).items():
                    s = m_stats["group_stats"].get(grp, {})
                    group_rows.append({
                        "model_key": m_key,
                        "model_id": spec["model_id"],
                        "method": m_name,
                        "accent_stratum": grp,
                        "wer": round(g_wer, 4),
                        "substitutions": s.get("sub", 0),
                        "deletions": s.get("del", 0),
                        "insertions": s.get("ins", 0),
                        "total_errors": s.get("errors", 0),
                        "reference_words": s.get("ref_words", 0),
                    })
        elif "group_metrics" in res:
            # Frozen Wav2Vec2 format
            for r in res["group_metrics"]:
                group_rows.append({
                    "model_key": m_key,
                    "model_id": spec["model_id"],
                    "method": r.get("method"),
                    "accent_stratum": r.get("group_id") or r.get("stage5_accent_group"),
                    "wer": round(float(r.get("wer")) * 100.0, 4) if float(r.get("wer")) < 1.0 else round(float(r.get("wer")), 4),
                    "substitutions": r.get("substitutions"),
                    "deletions": r.get("deletions"),
                    "insertions": r.get("insertions"),
                    "total_errors": int(r.get("substitutions", 0)) + int(r.get("deletions", 0)) + int(r.get("insertions", 0)),
                    "reference_words": r.get("reference_words"),
                })

        # Memory Cleanup between models
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    t_suite_elapsed = time.time() - t_suite_start
    print("\n" + "=" * 80)
    print(f"STAGE 6 SUITE EXECUTION COMPLETE (Elapsed: {t_suite_elapsed:.1f}s)")
    print("=" * 80)

    # Export Final CSVs
    bench_df = pd.DataFrame(benchmark_rows)
    bench_csv = REPORTS_DIR / "six_model_benchmark.csv"
    bench_df.to_csv(bench_csv, index=False)
    print(f"Exported main benchmark table: {bench_csv}")

    dsg_df = pd.DataFrame(dsg_summary_rows)
    dsg_csv = REPORTS_DIR / "six_model_dsg_summary.csv"
    dsg_df.to_csv(dsg_csv, index=False)
    print(f"Exported DSG summary table  : {dsg_csv}")

    if group_rows:
        grp_df = pd.DataFrame(group_rows)
        grp_csv = REPORTS_DIR / "six_model_group_metrics.csv"
        grp_df.to_csv(grp_csv, index=False)
        print(f"Exported group metrics table: {grp_csv}")

    return {
        "benchmark_csv": str(bench_csv),
        "dsg_summary_csv": str(dsg_csv),
        "results": all_model_results
    }


if __name__ == "__main__":
    default_dev = "cpu"
    try:
        import torch_xla.core.xla_model as xm
        default_dev = str(xm.xla_device())
    except Exception:
        if torch.cuda.is_available():
            default_dev = "cuda"

    parser = argparse.ArgumentParser(description="Stage 6 Master Cross-Architecture Benchmark.")
    parser.add_argument("--device", type=str, default=default_dev)
    parser.add_argument("--force_rerun", action="store_true", help="Force rerun ignoring checkpoints")
    parser.add_argument("--models", type=str, default="", help="Comma-separated model keys to run (e.g. wav2vec2_base,whisper_base)")
    args = parser.parse_args()

    models_to_run = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else None
    run_all_models_benchmark(device=args.device, force_rerun=args.force_rerun, selected_models=models_to_run)
