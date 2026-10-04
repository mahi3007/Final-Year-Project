#!/usr/bin/env python3
"""
Stage 6 Audio Data Packager: Bundles minimal external eval audio and manifests.
=============================================================================
Creates a lightweight (~40 MB) self-contained archive containing ONLY:
1. datasets/splits/ (*.csv, *.json)
2. datasets/external/common_voice_27/audio/ (900 external evaluation clips)
3. datasets/external/common_voice_27/sentinel_audio/ (300 sentinel panel clips)
4. datasets/external/common_voice_27/*_inventory.json
5. configs/stage5_gate_config.json

Allows instant ingestion into Kaggle Notebooks or Google Colab without uploading
large repositories.
"""

from __future__ import annotations

import os
import sys
import tarfile
import time
from pathlib import Path

# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def create_audio_bundle() -> Path:
    print("=" * 75)
    print("STAGE 6: PACKAGING MINIMAL AUDIO & MANIFEST BUNDLE")
    print("=" * 75)

    bundle_path = PROJECT_ROOT / "stage6_audio_bundle.tar.gz"

    items_to_pack = [
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

    print(f"Creating archive: {bundle_path.name}...")
    t_start = time.time()

    with tarfile.open(bundle_path, "w:gz") as tar:
        # Add metadata and configs
        for rel_path in items_to_pack:
            p = PROJECT_ROOT / rel_path
            if p.exists():
                tar.add(p, arcname=rel_path)
                print(f"  Added metadata: {rel_path}")
            else:
                print(f"  WARNING: Missing metadata file: {rel_path}")

        # Add 900 external eval audio clips
        eval_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"
        eval_clips = list(eval_audio_dir.glob("*.mp3"))
        print(f"  Adding {len(eval_clips)} external evaluation clips...")
        for c in eval_clips:
            arcname = f"datasets/external/common_voice_27/audio/{c.name}"
            tar.add(c, arcname=arcname)

        # Add 300 sentinel audio clips
        sentinel_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
        sentinel_clips = list(sentinel_audio_dir.glob("*.mp3"))
        print(f"  Adding {len(sentinel_clips)} sentinel panel clips...")
        for c in sentinel_clips:
            arcname = f"datasets/external/common_voice_27/sentinel_audio/{c.name}"
            tar.add(c, arcname=arcname)

    elapsed = time.time() - t_start
    size_mb = bundle_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 75)
    print(f"BUNDLE CREATED: {bundle_path} ({size_mb:.2f} MB in {elapsed:.1f}s)")
    print(f"Total audio files packaged: {len(eval_clips) + len(sentinel_clips)} clips")
    print("=" * 75)
    return bundle_path


if __name__ == "__main__":
    create_audio_bundle()
