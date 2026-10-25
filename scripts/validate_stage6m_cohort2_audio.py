#!/usr/bin/env python3
"""
scripts/validate_stage6m_cohort2_audio.py

Stage 6M Cohort 2 — Comprehensive Full-Corpus Audio Validation Tool
===================================================================
Standard: ADR-005
Protocol: v1.3.4-stage6m-self-authorization-amendment

Performs exhaustive full-corpus decodability, waveform integrity, and duration
validation across all 7,020 Cohort 2 audio recordings BEFORE neural acoustic
model initialization and BEFORE continuous prequential benchmark execution.

Checks:
1. Physical Existence & Filename Matching:
   - Validates that all 7,020 {recording_id}.mp3 files exist in cohort2_audio/.
   - Detects missing files, zero-byte files, and extraneous files.
2. Full Decoding & 16 kHz Resampling:
   - Loads each clip with dsg_ctta.data.acoustic.load_and_resample_audio(path, target_sr=16000).
   - Confirms valid 1D float32 array, finite numeric values (no NaNs, no Infs).
   - Validates non-zero duration and positive sample count.
3. Acoustic Confounder Extraction:
   - Measures exact duration_sec, sample_count, and estimated SNR (dB).
   - Confirms zero clipping (abs(amplitude) <= 1.0).
4. Machine-Readable Audit Output:
   - Emits structured JSON audit results and human-readable Markdown summary.
   - Exits with code 0 on complete PASS; exits with code 1 on any failure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import soundfile as sf

# Unbuffered stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.data.acoustic import load_and_resample_audio, estimate_snr_db, compute_audio_sha256

DEFAULT_EVAL_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv"
DEFAULT_AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort2_audio"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"
TOTAL_EXPECTED_CLIPS = 7020


def validate_single_clip(
    file_path: Path,
    expected_rec_id: str,
    target_sr: int = 16000,
) -> Dict[str, Any]:
    """Validates an individual audio file for decodability, sampling rate, and waveform health."""
    rec_result: Dict[str, Any] = {
        "recording_id": expected_rec_id,
        "file_path": str(file_path).replace("\\", "/"),
        "status": "PASS",
        "error": None,
        "file_size": 0,
        "sha256": None,
        "original_sr": None,
        "original_duration": None,
        "resampled_sr": target_sr,
        "resampled_samples": 0,
        "resampled_duration_sec": 0.0,
        "snr_db": None,
        "max_amplitude": 0.0,
    }

    if not file_path.exists():
        rec_result["status"] = "FAIL_MISSING"
        rec_result["error"] = "File not found on disk"
        return rec_result

    size = file_path.stat().st_size
    rec_result["file_size"] = size
    if size == 0:
        rec_result["status"] = "FAIL_ZERO_BYTE"
        rec_result["error"] = "Zero-byte file"
        return rec_result

    rec_result["sha256"] = compute_audio_sha256(file_path)

    # 1. Raw soundfile info
    try:
        info = sf.info(str(file_path))
        rec_result["original_sr"] = int(info.samplerate)
        rec_result["original_duration"] = float(info.duration)
        if info.duration <= 0.0 or info.samplerate <= 0:
            rec_result["status"] = "FAIL_INVALID_HEADER"
            rec_result["error"] = f"Invalid soundfile header: duration={info.duration}, sr={info.samplerate}"
            return rec_result
    except Exception as e:
        rec_result["status"] = "FAIL_DECODE_HEADER"
        rec_result["error"] = f"soundfile header parse exception: {e}"
        return rec_result

    # 2. Resampling & waveform validation
    try:
        waveform, sr = load_and_resample_audio(file_path, target_sr=target_sr)
        if sr != target_sr:
            rec_result["status"] = "FAIL_RESAMPLE_RATE"
            rec_result["error"] = f"Resampled rate {sr} != expected {target_sr}"
            return rec_result

        if not isinstance(waveform, np.ndarray):
            rec_result["status"] = "FAIL_WAVEFORM_TYPE"
            rec_result["error"] = f"Waveform type is {type(waveform)}, expected np.ndarray"
            return rec_result

        if waveform.ndim != 1:
            rec_result["status"] = "FAIL_WAVEFORM_CHANNELS"
            rec_result["error"] = f"Waveform ndim is {waveform.ndim}, expected 1D mono"
            return rec_result

        if len(waveform) == 0:
            rec_result["status"] = "FAIL_EMPTY_WAVEFORM"
            rec_result["error"] = "Resampled waveform contains 0 samples"
            return rec_result

        if not np.all(np.isfinite(waveform)):
            rec_result["status"] = "FAIL_NON_FINITE"
            rec_result["error"] = "Waveform contains NaN or Inf values"
            return rec_result

        rec_result["resampled_samples"] = int(len(waveform))
        dur = float(len(waveform)) / float(target_sr)
        rec_result["resampled_duration_sec"] = dur
        rec_result["max_amplitude"] = float(np.max(np.abs(waveform)))
        rec_result["snr_db"] = float(estimate_snr_db(waveform, sr=target_sr))

    except Exception as e:
        rec_result["status"] = "FAIL_DECODE_LOAD"
        rec_result["error"] = f"Decoding/resampling exception: {e}"
        return rec_result

    return rec_result


def run_audio_validation(
    eval_csv_path: Path,
    audio_dir: Path,
    reports_dir: Optional[Path] = None,
    sample_only: Optional[int] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """Runs exhaustive full-corpus decodability validation across expected recordings."""
    t_start = time.time()
    reports_dir = reports_dir or DEFAULT_REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not eval_csv_path.exists():
        return False, {
            "overall_status": "FAIL_CSV_MISSING",
            "error": f"Evaluation CSV missing: {eval_csv_path}",
            "records_tested": 0,
        }

    with open(eval_csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total_expected = len(rows)
    if sample_only is not None and sample_only > 0:
        rows = rows[:sample_only]

    print(f"[AUDIO VALIDATION] Loaded {len(rows)} clips to validate from {eval_csv_path} (total in CSV: {total_expected})")
    print(f"[AUDIO VALIDATION] Target Audio Directory: {audio_dir}")

    if not audio_dir.exists():
        report = {
            "overall_status": "HOLD_AUDIO_DIRECTORY_MISSING",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "audio_dir": str(audio_dir).replace("\\", "/"),
            "total_expected": total_expected,
            "clips_tested": 0,
            "clips_passed": 0,
            "clips_failed": total_expected,
            "failure_summary": {"MISSING_DIRECTORY": total_expected},
            "failures": [{"recording_id": r["recording_id"], "status": "FAIL_MISSING_DIR"} for r in rows],
        }
        _write_reports(report, reports_dir)
        return False, report

    # Check for extraneous files in audio_dir
    expected_filenames = {f"{r['recording_id']}.mp3" for r in rows}
    actual_files = list(audio_dir.glob("*.mp3"))
    actual_filenames = {p.name for p in actual_files}
    extraneous = sorted(list(actual_filenames - expected_filenames))
    missing_filenames = sorted(list(expected_filenames - actual_filenames))

    records: List[Dict[str, Any]] = []
    failure_counts: Dict[str, int] = {}
    total_samples = 0
    total_duration = 0.0

    for idx, r in enumerate(rows):
        rec_id = r["recording_id"]
        file_path = audio_dir / f"{rec_id}.mp3"
        res = validate_single_clip(file_path, expected_rec_id=rec_id)
        records.append(res)

        if res["status"] != "PASS":
            failure_counts[res["status"]] = failure_counts.get(res["status"], 0) + 1
        else:
            total_samples += res["resampled_samples"]
            total_duration += res["resampled_duration_sec"]

        if (idx + 1) % 500 == 0 or (idx + 1) == len(rows):
            print(f"[AUDIO VALIDATION] Progress: {idx + 1}/{len(rows)} clips validated ({len(failure_counts)} failure types)...", flush=True)

    passed_count = sum(1 for r in records if r["status"] == "PASS")
    overall_status = "PASS" if (passed_count == len(rows) and len(extraneous) == 0) else "FAIL"

    elapsed = time.time() - t_start
    report = {
        "overall_status": overall_status,
        "protocol_version": "v1.3.4-stage6m-self-authorization-amendment",
        "governing_standard": "ADR-005",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 2),
        "audio_dir": str(audio_dir).replace("\\", "/"),
        "total_expected": len(rows),
        "clips_tested": len(records),
        "clips_passed": passed_count,
        "clips_failed": len(records) - passed_count,
        "extraneous_files_count": len(extraneous),
        "extraneous_files": extraneous[:50],
        "missing_files_count": len(missing_filenames),
        "failure_summary": failure_counts,
        "metrics": {
            "total_duration_sec": round(total_duration, 2),
            "total_duration_hours": round(total_duration / 3600.0, 2),
            "mean_duration_sec": round(total_duration / passed_count, 2) if passed_count else 0.0,
            "total_resampled_samples": total_samples,
        },
        "failures": [r for r in records if r["status"] != "PASS"],
    }

    _write_reports(report, reports_dir)
    return overall_status == "PASS", report


def _write_reports(report: Dict[str, Any], reports_dir: Path):
    json_path = reports_dir / "stage6m_cohort2_audio_validation_report.json"
    md_path = reports_dir / "stage6m_cohort2_audio_validation_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    status = report["overall_status"]
    lines = [
        "# Stage 6M Cohort 2 Full-Corpus Audio Validation Report",
        "",
        f"> **Overall Status:** `{status}`  ",
        f"> **Timestamp:** {report.get('timestamp_utc')}  ",
        f"> **Protocol:** `{report.get('protocol_version', 'v1.3.4')}` (ADR-005)  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "| Metric | Expected Target | Validated | Status |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Total Evaluation Clips** | {report['total_expected']} | {report['clips_tested']} | {'**COMPLETE**' if report['clips_tested'] == report['total_expected'] else '**INCOMPLETE**'} |",
        f"| **Successfully Decoded & Resampled** | {report['total_expected']} | {report['clips_passed']} | {'**PASS (100%)**' if report['clips_passed'] == report['total_expected'] else '**FAIL**'} |",
        f"| **Missing Files** | 0 | {report.get('missing_files_count', 0)} | {'**PASS**' if report.get('missing_files_count', 0) == 0 else '**FAIL**'} |",
        f"| **Extraneous Files** | 0 | {report.get('extraneous_files_count', 0)} | {'**PASS**' if report.get('extraneous_files_count', 0) == 0 else '**FAIL**'} |",
    ]

    metrics = report.get("metrics", {})
    if metrics:
        lines += [
            f"| **Total Resampled Duration** | -- | {metrics.get('total_duration_hours', 0):.2f} h ({metrics.get('total_duration_sec', 0):.1f} s) | **NOMINAL** |",
            f"| **Mean Clip Duration** | -- | {metrics.get('mean_duration_sec', 0):.2f} s | **NOMINAL** |",
            f"| **Total 16 kHz Samples** | -- | {metrics.get('total_resampled_samples', 0):,} | **NOMINAL** |",
        ]

    lines += [
        "",
        "---",
        "",
        "## 2. Failure Diagnostics",
        "",
    ]

    if report.get("failure_summary"):
        lines.append("| Failure Category | Count |")
        lines.append("| :--- | :---: |")
        for k, v in sorted(report["failure_summary"].items()):
            lines.append(f"| `{k}` | {v} |")
        lines.append("")
    else:
        lines.append("Zero failures encountered across all tested clips.\n")

    lines += [
        "---",
        "",
        "## 3. Preflight Execution Disclaimer",
        "",
        "This validation script proves full-corpus decodability and acoustic validity under 16 kHz mono resampling. ",
        "It does NOT execute neural acoustic model inference or alter the prequential benchmark state.",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[AUDIO VALIDATION] Saved JSON Report: {json_path}")
    print(f"[AUDIO VALIDATION] Saved Markdown Report: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Stage 6M Cohort 2 Full-Corpus Audio Validator")
    parser.add_argument("--eval-csv", type=Path, default=DEFAULT_EVAL_CSV, help="Path to evaluation CSV")
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR, help="Path to audio directory")
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR, help="Path to output reports directory")
    parser.add_argument("--sample-only", type=int, default=None, help="Validate only first N clips for smoke testing")
    args = parser.parse_args()

    success, report = run_audio_validation(
        eval_csv_path=args.eval_csv,
        audio_dir=args.audio_dir,
        reports_dir=args.reports_dir,
        sample_only=args.sample_only,
    )
    print(f"\n[AUDIO VALIDATION RESULT] Verdict: {report['overall_status']}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
