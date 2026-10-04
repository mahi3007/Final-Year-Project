#!/usr/bin/env python3
"""
Stage 6.1: Merge Stage 6 and Stage 6.1 into 8-Model Master Suite.
================================================================
Merges the 6 frozen Stage 6 models with the 2 new Stage 6.1 CTC models:
- 6 CTC Models: Wav2Vec2-base, HuBERT-large, Data2Vec-base, XLSR-53, Wav2Vec2-large-lv60, Wav2Vec2-large-robust
- 2 Seq2Seq Static Baselines: Whisper-base, Distil-Whisper-small

Outputs:
- reports/stage6/eight_model_benchmark.csv
- reports/stage6/eight_model_dsg_summary.csv
- reports/stage6/eight_model_group_metrics.csv
- reports/stage6/eight_model_comparative_analysis.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STAGE6_DIR = PROJECT_ROOT / "reports" / "stage6"
STAGE6_1_DIR = PROJECT_ROOT / "reports" / "stage6_1"


def merge_results():
    print("=" * 80)
    print("STAGE 6.1: MERGING INTO 8-MODEL MASTER BENCHMARK SUITE")
    print("=" * 80)

    # 1. Benchmark CSV
    s6_bench = STAGE6_DIR / "six_model_benchmark.csv"
    s6_1_bench = STAGE6_1_DIR / "stage6_1_benchmark.csv"
    assert s6_bench.exists(), f"Missing {s6_bench}"
    assert s6_1_bench.exists(), f"Missing {s6_1_bench}"

    df_b6 = pd.read_csv(s6_bench)
    df_b6_1 = pd.read_csv(s6_1_bench)
    # Deduplicate by model_key
    df_merged_bench = pd.concat([df_b6, df_b6_1]).drop_duplicates(subset=["model_key"], keep="last")
    out_bench = STAGE6_DIR / "eight_model_benchmark.csv"
    df_merged_bench.to_csv(out_bench, index=False)
    print(f"Generated 8-model benchmark CSV ({len(df_merged_bench)} rows): {out_bench}")

    # 2. DSG Summary CSV
    s6_dsg = STAGE6_DIR / "six_model_dsg_summary.csv"
    s6_1_dsg = STAGE6_1_DIR / "stage6_1_dsg_summary.csv"
    assert s6_dsg.exists(), f"Missing {s6_dsg}"
    assert s6_1_dsg.exists(), f"Missing {s6_1_dsg}"

    df_d6 = pd.read_csv(s6_dsg)
    df_d6_1 = pd.read_csv(s6_1_dsg)
    df_merged_dsg = pd.concat([df_d6, df_d6_1]).drop_duplicates(subset=["model_key"], keep="last")
    out_dsg = STAGE6_DIR / "eight_model_dsg_summary.csv"
    df_merged_dsg.to_csv(out_dsg, index=False)
    print(f"Generated 8-model DSG summary CSV ({len(df_merged_dsg)} rows): {out_dsg}")

    # 3. Group Metrics CSV
    s6_grp = STAGE6_DIR / "six_model_group_metrics.csv"
    s6_1_grp = STAGE6_1_DIR / "stage6_1_group_metrics.csv"
    if s6_grp.exists() and s6_1_grp.exists():
        df_g6 = pd.read_csv(s6_grp)
        df_g6_1 = pd.read_csv(s6_1_grp)
        df_merged_grp = pd.concat([df_g6, df_g6_1]).drop_duplicates(subset=["model_key", "method", "accent_stratum"], keep="last")
        out_grp = STAGE6_DIR / "eight_model_group_metrics.csv"
        df_merged_grp.to_csv(out_grp, index=False)
        print(f"Generated 8-model group metrics CSV ({len(df_merged_grp)} rows): {out_grp}")

    # 4. Copy checkpoints from stage6_1 into stage6/checkpoints if desired
    ck_s6 = STAGE6_DIR / "checkpoints"
    ck_s6_1 = STAGE6_1_DIR / "checkpoints"
    if ck_s6_1.exists():
        import shutil
        for f in ck_s6_1.glob("*"):
            shutil.copy(f, ck_s6 / f.name)
        print(f"Mirrored Stage 6.1 checkpoints into {ck_s6}")

    print("\n" + "=" * 80)
    print("8-MODEL MASTER SUITE MERGE COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    merge_results()
