#!/usr/bin/env python3
"""
Master Audio Bundle Packager for Cloud GPU Execution
====================================================
Creates minimal, self-contained compressed archives containing audio assets and metadata
for executing Stage 5M and Stage 6 on free cloud GPUs (Kaggle Tesla P100 / Colab T4):

1. `stage6_audio_bundle.tar.gz` (~42 MB):
   - Common Voice 27.0 (900 external eval clips + 300 sentinel panel clips)
   - configs/stage5_gate_config.json
   - datasets/splits/stage5_*.csv, *.json

2. `stage5m_audio_bundle.tar.gz` (~67 MB):
   - L2-ARCTIC primary audio (240 clips)
   - L2-ARCTIC corrupted audio (480 clips across 4 conditions)
   - datasets/splits/stage4_*.csv

3. `stage5_stage6_audio_bundle.tar.gz` (~109 MB):
   - Complete combined archive with both Stage 5M and Stage 6 audio assets.
"""

from __future__ import annotations

import argparse
import os
import sys
import tarfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def package_stage6_bundle() -> Path:
    bundle_path = PROJECT_ROOT / "stage6_audio_bundle.tar.gz"
    print(f"Creating Stage 6 audio bundle: {bundle_path.name}...")
    t0 = time.time()

    items = [
        "datasets/splits/stage5_external_eval.csv",
        "datasets/splits/stage5_external_eval.lock.json",
        "datasets/splits/stage5_external_eval_manifest.json",
        "datasets/splits/stage5_sentinel_panel.csv",
        "datasets/splits/stage5_sentinel_panel.lock.json",
        "datasets/splits/stage5_sentinel_audio_manifest.json",
        "datasets/splits/calibration.csv",
        "datasets/splits/development.csv",
        "datasets/splits/final_test.csv",
        "datasets/external/common_voice_27/audio_inventory.json",
        "datasets/external/common_voice_27/sentinel_audio_inventory.json",
        "configs/stage5_gate_config.json",
    ]

    with tarfile.open(bundle_path, "w:gz") as tar:
        for it in items:
            p = PROJECT_ROOT / it
            if p.exists():
                tar.add(p, arcname=it)

        # 900 eval clips
        eval_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
        for c in eval_dir.glob("*.mp3"):
            tar.add(c, arcname=f"datasets/external/common_voice_27/audio/{c.name}")

        # 300 sentinel clips
        sent_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
        for c in sent_dir.glob("*.mp3"):
            tar.add(c, arcname=f"datasets/external/common_voice_27/sentinel_audio/{c.name}")

    sz = bundle_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {bundle_path} ({sz:.2f} MB in {time.time()-t0:.1f}s)")
    return bundle_path


def package_stage5m_bundle() -> Path:
    bundle_path = PROJECT_ROOT / "stage5m_audio_bundle.tar.gz"
    print(f"Creating Stage 5M audio bundle: {bundle_path.name}...")
    t0 = time.time()

    items = [
        "datasets/splits/stage4_characterization.csv",
        "datasets/splits/stage4_noise_moderate.csv",
        "datasets/splits/stage4_noise_severe.csv",
        "datasets/splits/stage4_babble_moderate.csv",
        "datasets/splits/stage4_reverberation.csv",
        "datasets/splits/stage5_sentinel_panel.csv",
        "configs/stage5_gate_config.json",
    ]

    with tarfile.open(bundle_path, "w:gz") as tar:
        for it in items:
            p = PROJECT_ROOT / it
            if p.exists():
                tar.add(p, arcname=it)

        # Primary audio (240 clips)
        primary_dir = PROJECT_ROOT / "datasets" / "primary" / "audio"
        if primary_dir.exists():
            for c in primary_dir.glob("*.wav"):
                tar.add(c, arcname=f"datasets/primary/audio/{c.name}")

        # Corrupted audio (480 clips)
        corrupted_dir = PROJECT_ROOT / "datasets" / "corrupted"
        if corrupted_dir.exists():
            for c in corrupted_dir.rglob("*.wav"):
                rel = c.relative_to(PROJECT_ROOT)
                tar.add(c, arcname=str(rel).replace("\\", "/"))

        # Sentinel audio (300 clips)
        sent_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
        if sent_dir.exists():
            for c in sent_dir.glob("*.mp3"):
                tar.add(c, arcname=f"datasets/external/common_voice_27/sentinel_audio/{c.name}")

    sz = bundle_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {bundle_path} ({sz:.2f} MB in {time.time()-t0:.1f}s)")
    return bundle_path


def package_combined_bundle() -> Path:
    bundle_path = PROJECT_ROOT / "stage5_stage6_audio_bundle.tar.gz"
    print(f"Creating Combined Stage 5 & 6 audio bundle: {bundle_path.name}...")
    t0 = time.time()

    with tarfile.open(bundle_path, "w:gz") as tar:
        # Splits and configs
        splits_dir = PROJECT_ROOT / "datasets" / "splits"
        for s in splits_dir.glob("*.*"):
            tar.add(s, arcname=f"datasets/splits/{s.name}")

        gate_cfg = PROJECT_ROOT / "configs" / "stage5_gate_config.json"
        if gate_cfg.exists():
            tar.add(gate_cfg, arcname="configs/stage5_gate_config.json")

        # Primary audio
        primary_dir = PROJECT_ROOT / "datasets" / "primary" / "audio"
        if primary_dir.exists():
            for c in primary_dir.glob("*.wav"):
                tar.add(c, arcname=f"datasets/primary/audio/{c.name}")

        # Corrupted audio
        corrupted_dir = PROJECT_ROOT / "datasets" / "corrupted"
        if corrupted_dir.exists():
            for c in corrupted_dir.rglob("*.wav"):
                rel = c.relative_to(PROJECT_ROOT)
                tar.add(c, arcname=str(rel).replace("\\", "/"))

        # Common Voice eval audio
        eval_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
        if eval_dir.exists():
            for c in eval_dir.glob("*.mp3"):
                tar.add(c, arcname=f"datasets/external/common_voice_27/audio/{c.name}")

        # Common Voice sentinel audio
        sent_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
        if sent_dir.exists():
            for c in sent_dir.glob("*.mp3"):
                tar.add(c, arcname=f"datasets/external/common_voice_27/sentinel_audio/{c.name}")

        inv_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27"
        for inv in inv_dir.glob("*_inventory.json"):
            tar.add(inv, arcname=f"datasets/external/common_voice_27/{inv.name}")

    sz = bundle_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {bundle_path} ({sz:.2f} MB in {time.time()-t0:.1f}s)")
    return bundle_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package audio archives for Kaggle")
    parser.add_argument("--stage", choices=["5m", "6", "combined", "all"], default="all")
    args = parser.parse_args()

    if args.stage in ["6", "all"]:
        package_stage6_bundle()
    if args.stage in ["5m", "all"]:
        package_stage5m_bundle()
    if args.stage in ["combined", "all"]:
        package_combined_bundle()
