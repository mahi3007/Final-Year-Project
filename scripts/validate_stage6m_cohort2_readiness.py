#!/usr/bin/env python3
"""
scripts/validate_stage6m_cohort2_readiness.py

Standalone CLI utility for Stage 6M Cohort 2 Preflight Readiness & Integrity Validation.
========================================================================================
Protocol: v1.3.4-stage6m-self-authorization-amendment (ADR-005)

Executes all 5 preflight integrity checks:
1. Manifest cryptographic hash & schema integrity.
2. Manifest <-> evaluation CSV agreement (zero duplicates, exact strata allocation, prefix matching).
3. Audio materialization & 16 kHz decodability.
4. Sentinel panel completeness & zero-exposure speaker isolation.
5. Execution configuration freeze & compute budget estimation.

Produces:
- reports/stage6m/stage6m_cohort2_readiness_report.json
- reports/stage6m/stage6m_cohort2_readiness_report.md

Exit Code:
- 0: READY FOR AUTHORIZED EXECUTION
- 1: HOLD (e.g. MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD or validation failure)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.data.cohort2_preflight import Cohort2PreflightValidator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stage 6M Cohort 2 Preflight Readiness & Integrity Validator"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to locked candidate manifest (defaults to datasets/splits/stage6m_locked_candidate_manifest.json).",
    )
    parser.add_argument(
        "--eval-csv",
        type=Path,
        default=None,
        help="Path to evaluation CSV (defaults to datasets/splits/stage6m_cohort2_audio.csv).",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=None,
        help="Path to audio directory (defaults to datasets/external/common_voice_27/cohort2_audio).",
    )
    parser.add_argument(
        "--sentinel-csv",
        type=Path,
        default=None,
        help="Path to sentinel panel CSV (defaults to datasets/splits/stage5_sentinel_panel.csv).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write JSON and Markdown readiness reports (defaults to reports/stage6m).",
    )
    parser.add_argument(
        "--model",
        default="wav2vec2_base",
        choices=["wav2vec2_base", "hubert_large"],
        help="Target acoustic model architecture.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 80)
    print("STAGE 6M CONFIRMATORY COHORT 2: PREFLIGHT READINESS AUDIT")
    print("=" * 80)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=args.manifest,
        eval_csv_path=args.eval_csv,
        audio_dir=args.audio_dir,
        sentinel_csv_path=args.sentinel_csv,
    )

    report = validator.run_preflight(model_name=args.model)
    json_path, md_path = validator.save_reports(report, output_dir=args.output_dir)

    print(f"\n[READINESS AUDIT COMPLETE]")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Summary:        {report['summary_description']}")
    print(f"Saved JSON:     {json_path}")
    print(f"Saved Markdown: {md_path}")

    if report["status_reasons"]:
        print("\nActive HOLD Conditions:")
        for r in report["status_reasons"]:
            print(f"  - {r}")

    print("\nGovernance Check:")
    print("  Passing technical readiness checks establishes scientific feasibility;")
    print("  it does NOT constitute approval of compute expenditure or experimental execution.")
    print("=" * 80)

    if report["overall_status"] == "READY FOR AUTHORIZED EXECUTION":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
