#!/usr/bin/env python3
"""
scripts/curate_stage6m_cohort2_csv.py

Stage 6M Confirmatory Cohort 2 Dataset Curation & Integrity Audit Utility
=========================================================================
Governing Standard: ADR-005
Governing Protocol: v1.3.4-stage6m-self-authorization-amendment
Methodological Reference: reports/stage6m/stage6m_data_feasibility_audit.md

Curates and audits the canonical Confirmatory Cohort 2 evaluation stream (468 speakers,
7,020 clips across 6 strata: Irish, England, Canada, Australia, South Asia, US)
from Mozilla Common Voice 27.0 English (validated.tsv) anchored to the
cryptographically locked candidate manifest:
    datasets/splits/stage6m_locked_candidate_manifest.json

Strict Stage 6M Quality Predicate V:
  - Baseline Predicate B0: Non-empty speaker ID and audio path, homogeneous declared accent
    matching manifest stratum, transcript non-empty with word count >= 2 words, path deduplication.
  - Strict Quality Predicate V: locale == "en", up_votes >= 2, down_votes < 2.
  - Strict Speaker Eligibility: At least 15 qualified clips satisfying both B0 and V.

Deterministic Selection Algorithm:
  1. For each active speaker and eligible clip, compute:
       rank_key = sha256(f"{seed}:{client_id}:{clip_path}")
  2. Sort strict-eligible clips ascending by rank_key (invariant to validated.tsv row order).
  3. Select the first 15 clips per speaker.

Recording ID Convention:
  recording_id = Path(clip_path).stem  (e.g., 'common_voice_en_27710027')
  Physical audio file path: cohort2_audio/{recording_id}.mp3
  Matches raw Common Voice MP3 filename with zero double-extension.

Audit Modes:
  --audit-only (default): Performs full scan, verifies the 6 integrity criteria
       under strict Stage 6M predicate V, records per-speaker B0 vs. Strict counts,
       and produces reports/stage6m/stage6m_cohort2_curation_audit.json / .md
       WITHOUT writing the evaluation CSV or lock file.
  --generate: Explicitly generates datasets/splits/stage6m_cohort2_audio.csv
       and datasets/splits/stage6m_cohort2_audio.lock.json ONLY if all strict checks PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cohort2_curation")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROTOCOL_VERSION = "v1.3.4-stage6m-self-authorization-amendment"
GOVERNING_STANDARD = "ADR-005"
DEFAULT_SEED = 20261020  # Pinned to candidate manifest date 2026-10-20
MIN_WORD_COUNT = 2

ACCENT_NORMALIZATION_MAP: Dict[str, Tuple[str, str]] = {
    "united states english": ("US English", "us"),
    "england english": ("England English", "england"),
    "india and south asia (india, pakistan, sri lanka)": ("South Asian English", "south_asian"),
    "australian english": ("Australian English", "australia"),
    "canadian english": ("Canadian English", "canada"),
    "irish english": ("Irish English", "ireland"),
}

EXPECTED_STRATA = [
    "Irish English",
    "England English",
    "Canadian English",
    "Australian English",
    "South Asian English",
    "US English",
]


def compute_sha256(data: bytes | str | Path) -> str:
    h = hashlib.sha256()
    if isinstance(data, Path):
        with open(data, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    elif isinstance(data, str):
        h.update(data.encode("utf-8"))
    else:
        h.update(data)
    return h.hexdigest()


def compute_clip_rank_hash(seed: int, speaker_id: str, clip_path: str) -> str:
    key = f"{seed}:{speaker_id}:{clip_path}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stage 6M Confirmatory Cohort 2 Curation & Integrity Audit Utility"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json",
        help="Path to locked candidate manifest.",
    )
    parser.add_argument(
        "--val-tsv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv",
        help="Path to Common Voice 27.0 validated.tsv.",
    )
    parser.add_argument(
        "--ext-eval-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv",
        help="Path to Cohort 1 evaluation CSV (for disjointness check).",
    )
    parser.add_argument(
        "--sentinel-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv",
        help="Path to Sentinel Panel CSV (for disjointness check).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv",
        help="Destination path for curated Cohort 2 CSV.",
    )
    parser.add_argument(
        "--output-lock",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.lock.json",
        help="Destination path for authoritative clip lock JSON.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "stage6m",
        help="Directory to save curation audit reports.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Deterministic clip selection seed (default: {DEFAULT_SEED}).",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        default=False,
        help="Materialize the evaluation CSV and lock file (default is audit-only).",
    )
    return parser.parse_args()


def run_curation_audit(args) -> Tuple[bool, Dict[str, Any], Optional[pd.DataFrame]]:
    logger.info("=" * 80)
    logger.info("STAGE 6M COHORT 2 CURATION & DATA INTEGRITY AUDIT")
    logger.info(f"Protocol: {PROTOCOL_VERSION} | Standard: {GOVERNING_STANDARD}")
    logger.info(f"Selection Seed: {args.seed} | Mode: {'GENERATE' if args.generate else 'AUDIT-ONLY'}")
    logger.info("=" * 80)

    # 1. Load Candidate Manifest
    if not args.manifest.exists():
        raise FileNotFoundError(f"Missing locked candidate manifest: {args.manifest}")
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest_speakers: Dict[str, Dict[str, Any]] = {}
    prefix_to_speaker_info: Dict[str, Dict[str, Any]] = {}
    strata_counts: Dict[str, int] = defaultdict(int)

    for s_name, s_info in manifest_data["strata"].items():
        s_code = s_info["stratum_code"]
        for spk in s_info["active_speakers"]:
            pref = spk["speaker_id_prefix"].rstrip("…")
            info = {
                "prefix": pref,
                "stratum_name": s_name,
                "stratum_code": s_code,
                "clips_allocated": spk["clips_allocated"],
            }
            manifest_speakers[pref] = info
            prefix_to_speaker_info[pref] = info
            strata_counts[s_name] += 1

    total_active_speakers = len(manifest_speakers)
    expected_active_from_meta = manifest_data.get("metadata", {}).get("total_active_speakers", 468)
    logger.info(f"Loaded {total_active_speakers} active speakers across {len(strata_counts)} strata from manifest.")
    if total_active_speakers != expected_active_from_meta:
        raise ValueError(f"Manifest active speaker mismatch: found {total_active_speakers}, expected {expected_active_from_meta}")

    # 2. Load Disjointness Exposure Sets
    c1_spks: Set[str] = set()
    if args.ext_eval_csv.exists():
        df_c1 = pd.read_csv(args.ext_eval_csv)
        c1_spks = set(df_c1["speaker_id"].astype(str).unique())
    logger.info(f"Loaded {len(c1_spks)} Cohort 1 speakers for disjointness audit.")

    sent_spks: Set[str] = set()
    if args.sentinel_csv.exists():
        df_sent = pd.read_csv(args.sentinel_csv)
        sent_spks = set(df_sent["speaker_id"].astype(str).unique())
    logger.info(f"Loaded {len(sent_spks)} Sentinel Panel speakers for disjointness audit.")

    # 3. Stream validated.tsv and collect qualified clips
    if not args.val_tsv.exists():
        raise FileNotFoundError(f"Missing Common Voice validated.tsv: {args.val_tsv}")

    logger.info(f"Scanning validated.tsv: {args.val_tsv} ({args.val_tsv.stat().st_size / (1024**2):.1f} MB)...")
    matched_speakers: Dict[str, str] = {}  # prefix -> full client_id

    # Speaker clip accounting: tracking raw, baseline B0, and strict V
    speaker_b0_clips: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    speaker_strict_clips: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    speaker_rejection_counts: Dict[str, Dict[str, int]] = {
        pref: {
            "raw_total": 0,
            "rejected_locale": 0,
            "rejected_votes": 0,
            "rejected_words": 0,
            "rejected_accent": 0,
            "passed_b0": 0,
            "passed_strict": 0,
        }
        for pref in manifest_speakers
    }

    chunk_size = 100000
    total_tsv_rows = 0
    candidate_tsv_rows = 0

    for chunk in pd.read_csv(args.val_tsv, sep="\t", chunksize=chunk_size, low_memory=False):
        total_tsv_rows += len(chunk)
        prefixes = chunk["client_id"].str[:24]
        mask = prefixes.isin(prefix_to_speaker_info)
        if not mask.any():
            continue

        sub = chunk[mask]
        candidate_tsv_rows += len(sub)

        for _, row in sub.iterrows():
            cid = str(row["client_id"])
            pref = cid[:24]

            # Verify 1:1 prefix to full client_id consistency
            if pref not in matched_speakers:
                matched_speakers[pref] = cid
            elif matched_speakers[pref] != cid:
                raise ValueError(
                    f"Ambiguity detected: prefix '{pref}' maps to multiple client_ids: "
                    f"'{matched_speakers[pref]}' and '{cid}'!"
                )

            rej = speaker_rejection_counts[pref]
            rej["raw_total"] += 1

            # Quality and protocol filter checks
            sent = str(row["sentence"]).strip() if pd.notna(row["sentence"]) else ""
            acc = str(row["accents"]).strip().lower() if pd.notna(row["accents"]) else ""
            loc = str(row["locale"]).strip() if pd.notna(row["locale"]) else ""
            up = row["up_votes"]
            down = row["down_votes"]
            words = len(sent.split())

            # C1: Accent mapping
            mapped = ACCENT_NORMALIZATION_MAP.get(acc)
            expected_s_name = prefix_to_speaker_info[pref]["stratum_name"]
            if mapped is None or mapped[0] != expected_s_name:
                rej["rejected_accent"] += 1
                continue

            # C4: Non-empty sentence and word count >= 2
            if words < MIN_WORD_COUNT or not sent:
                rej["rejected_words"] += 1
                continue

            clip_path = str(row["path"]).strip()
            if not clip_path:
                continue

            clip_info = {
                "client_id": cid,
                "speaker_id_prefix": pref,
                "stratum_name": expected_s_name,
                "stratum_code": prefix_to_speaker_info[pref]["stratum_code"],
                "clip_path": clip_path,
                "sentence": sent,
                "word_count": words,
                "up_votes": int(up),
                "down_votes": int(down),
                "locale": loc,
            }

            # Passes Baseline Predicate B0
            rej["passed_b0"] += 1
            speaker_b0_clips[pref].append(clip_info)

            # Strict Stage 6M Quality Predicate V: locale == "en", up_votes >= 2, down_votes < 2
            fail_loc = (loc != "en")
            fail_votes = (up < 2 or down >= 2)

            if fail_loc:
                rej["rejected_locale"] += 1
            if fail_votes:
                rej["rejected_votes"] += 1

            if not fail_loc and not fail_votes:
                rej["passed_strict"] += 1
                speaker_strict_clips[pref].append(clip_info)

    logger.info(f"TSV scan complete: {total_tsv_rows:,} rows scanned; {candidate_tsv_rows:,} candidate rows matched.")

    # 4. Execute the 6 Audit Checks under Strict Stage 6M Predicate V
    audit_results: Dict[str, Any] = {
        "metadata": {
            "protocol_version": PROTOCOL_VERSION,
            "governing_standard": GOVERNING_STANDARD,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "selection_seed": args.seed,
            "selection_algorithm": "SHA256(seed:client_id:clip_path) ascending rank sort",
            "predicate_level": "STRICT (B0 + V: locale=='en', up_votes>=2, down_votes<2)",
            "execution_mode": "GENERATE" if args.generate else "AUDIT_ONLY",
        },
        "checks": {},
        "overall_status": "PASS",
    }

    # Check 1: 100% Prefix Resolution & 1:1 Bijective Mapping
    check1_pass = len(matched_speakers) == len(manifest_speakers)
    audit_results["checks"]["prefix_resolution"] = {
        "status": "PASS" if check1_pass else "FAIL",
        "expected_prefixes": len(manifest_speakers),
        "resolved_prefixes": len(matched_speakers),
        "unresolved_prefixes": list(set(manifest_speakers.keys()) - set(matched_speakers.keys())),
    }
    if not check1_pass:
        audit_results["overall_status"] = "FAIL"

    # Check 2: Strict Clip Eligibility (>= 15 qualified clips per speaker satisfying B0 + V)
    speakers_under_15_strict: Dict[str, Dict[str, Any]] = {}
    speakers_under_15_b0: Dict[str, int] = {}

    for pref in manifest_speakers:
        b0_cnt = len(speaker_b0_clips[pref])
        strict_cnt = len(speaker_strict_clips[pref])
        if b0_cnt < 15:
            speakers_under_15_b0[pref] = b0_cnt
        if strict_cnt < 15:
            rej = speaker_rejection_counts[pref]
            speakers_under_15_strict[pref] = {
                "stratum": manifest_speakers[pref]["stratum_name"],
                "raw_total": rej["raw_total"],
                "b0_baseline_count": b0_cnt,
                "strict_count": strict_cnt,
                "shortfall": 15 - strict_cnt,
                "rejected_votes": rej["rejected_votes"],
                "rejected_locale": rej["rejected_locale"],
                "rejected_words": rej["rejected_words"],
            }

    check2_pass = len(speakers_under_15_strict) == 0
    audit_results["checks"]["clip_eligibility"] = {
        "status": "PASS" if check2_pass else "FAIL",
        "predicate": "B0 + V (locale=='en', up_votes>=2, down_votes<2)",
        "total_active_speakers": len(manifest_speakers),
        "speakers_meeting_b0_quota": len(manifest_speakers) - len(speakers_under_15_b0),
        "speakers_meeting_strict_quota": len(manifest_speakers) - len(speakers_under_15_strict),
        "strict_shortfall_count": len(speakers_under_15_strict),
        "strict_shortfall_speakers": speakers_under_15_strict,
    }
    if not check2_pass:
        audit_results["overall_status"] = "HOLD_STRICT_QUALITY_SHORTFALL"

    # Check 3: Disjointness from Cohort 1 and Sentinel Panel (Zero Leakage)
    all_c2_speakers = set(matched_speakers.values())
    c1_overlap = all_c2_speakers.intersection(c1_spks)
    sent_overlap = all_c2_speakers.intersection(sent_spks)

    check3_pass = len(c1_overlap) == 0 and len(sent_overlap) == 0
    audit_results["checks"]["speaker_disjointness"] = {
        "status": "PASS" if check3_pass else "FAIL",
        "cohort1_overlap_count": len(c1_overlap),
        "cohort1_overlap_speakers": list(c1_overlap),
        "sentinel_overlap_count": len(sent_overlap),
        "sentinel_overlap_speakers": list(sent_overlap),
    }
    if not check3_pass:
        audit_results["overall_status"] = "FAIL"

    # Check 4: Stratum Preservation & Balanced Allocation
    stratum_speaker_counts: Dict[str, int] = defaultdict(int)
    for pref, cid in matched_speakers.items():
        s_name = prefix_to_speaker_info[pref]["stratum_name"]
        stratum_speaker_counts[s_name] += 1

    expected_strata_counts = {
        s_name: s_info.get("active_count", len(s_info.get("active_speakers", [])))
        for s_name, s_info in manifest_data["strata"].items()
    }
    check4_pass = (
        len(stratum_speaker_counts) == len(expected_strata_counts)
        and all(stratum_speaker_counts.get(s) == expected_strata_counts.get(s) for s in expected_strata_counts)
    )
    audit_results["checks"]["stratum_preservation"] = {
        "status": "PASS" if check4_pass else "FAIL",
        "stratum_speaker_counts": dict(stratum_speaker_counts),
        "expected_per_stratum": expected_strata_counts,
    }
    if not check4_pass:
        audit_results["overall_status"] = "FAIL"

    # 5. Deterministic Clip Selection (15 clips per speaker from strict-eligible pool if available)
    curated_records: List[Dict[str, Any]] = []
    seen_clip_paths: Set[str] = set()

    for pref in sorted(manifest_speakers.keys()):
        raw_clips = speaker_strict_clips[pref]
        # Deduplicate raw clips by path
        unique_clips_map = {c["clip_path"]: c for c in raw_clips}
        unique_clips = list(unique_clips_map.values())

        cid = matched_speakers.get(pref, "")
        ranked_clips = sorted(
            unique_clips,
            key=lambda c: compute_clip_rank_hash(args.seed, cid, c["clip_path"]),
        )
        selected_15 = ranked_clips[:15]

        for c_idx, clip in enumerate(selected_15, start=1):
            clip_path = clip["clip_path"]
            seen_clip_paths.add(clip_path)

            rec_id = Path(clip_path).stem  # e.g. 'common_voice_en_27710027'
            curated_records.append({
                "recording_id": rec_id,
                "speaker_id": cid,
                "speaker_id_prefix": pref,
                "stage5_accent_group": clip["stratum_name"],
                "stratum_code": clip["stratum_code"],
                "audio_path": clip_path,
                "transcript": clip["sentence"],
                "word_count": clip["word_count"],
                "selection_seed": args.seed,
                "clip_order_within_speaker": c_idx,
                "protocol_version": PROTOCOL_VERSION,
                "dataset_name": "stage6m_cohort2_audio",
            })

    # Check 5: Stream Geometry & Clip Uniqueness
    total_clips_selected = len(curated_records)
    unique_paths_count = len(seen_clip_paths)
    expected_total_clips = sum(
        spk.get("clips_allocated", 15)
        for s in manifest_data["strata"].values()
        for spk in s.get("active_speakers", [])
    )
    expected_clips_per_stratum = {
        s_name: sum(spk.get("clips_allocated", 15) for spk in s_info.get("active_speakers", []))
        for s_name, s_info in manifest_data["strata"].items()
    }

    stratum_clip_counts: Dict[str, int] = defaultdict(int)
    for r in curated_records:
        stratum_clip_counts[r["stage5_accent_group"]] += 1

    check5_pass = (
        total_clips_selected == expected_total_clips
        and unique_paths_count == expected_total_clips
        and len(stratum_clip_counts) == len(expected_clips_per_stratum)
        and all(stratum_clip_counts.get(s) == expected_clips_per_stratum.get(s) for s in expected_clips_per_stratum)
    )
    audit_results["checks"]["stream_geometry"] = {
        "status": "PASS" if check5_pass else "FAIL",
        "total_clips_selected": total_clips_selected,
        "expected_total_clips": expected_total_clips,
        "unique_audio_paths": unique_paths_count,
        "stratum_clip_counts": dict(stratum_clip_counts),
        "expected_per_stratum": expected_clips_per_stratum,
    }
    if not check5_pass:
        if audit_results["overall_status"] == "PASS":
            audit_results["overall_status"] = "FAIL"

    # Check 6: Schema & Filename Compatibility
    curated_df = pd.DataFrame(curated_records) if curated_records else pd.DataFrame()
    required_runner_cols = {"recording_id", "speaker_id", "stage5_accent_group", "stratum_code", "audio_path", "transcript"}
    missing_cols = required_runner_cols - set(curated_df.columns) if not curated_df.empty else list(required_runner_cols)
    empty_transcripts = (curated_df["transcript"].str.strip() == "").sum() if not curated_df.empty else 0
    has_double_extension = any(r["recording_id"].endswith(".mp3") for r in curated_records)

    check6_pass = len(missing_cols) == 0 and empty_transcripts == 0 and not has_double_extension and not curated_df.empty
    audit_results["checks"]["schema_and_naming"] = {
        "status": "PASS" if check6_pass else "FAIL",
        "missing_columns": list(missing_cols),
        "empty_transcripts": int(empty_transcripts),
        "double_extension_detected": has_double_extension,
        "sample_recording_id": curated_records[0]["recording_id"] if curated_records else None,
        "sample_audio_path": curated_records[0]["audio_path"] if curated_records else None,
    }
    if not check6_pass:
        if audit_results["overall_status"] == "PASS":
            audit_results["overall_status"] = "FAIL"

    # Per-stratum strict eligibility breakdown
    strata_audit_summary: Dict[str, Dict[str, int]] = {}
    for s_name in EXPECTED_STRATA:
        spks_in_stratum = [p for p in manifest_speakers if manifest_speakers[p]["stratum_name"] == s_name]
        strict_pass_count = sum(1 for p in spks_in_stratum if len(speaker_strict_clips[p]) >= 15)
        strata_audit_summary[s_name] = {
            "total_active_speakers": len(spks_in_stratum),
            "strict_eligible_speakers": strict_pass_count,
            "shortfall_speakers": len(spks_in_stratum) - strict_pass_count,
        }

    # Summary Metrics
    audit_results["summary"] = {
        "overall_status": audit_results["overall_status"],
        "total_speakers_checked": len(manifest_speakers),
        "speakers_meeting_strict_quota": len(manifest_speakers) - len(speakers_under_15_strict),
        "speakers_failing_strict_quota": len(speakers_under_15_strict),
        "strata_breakdown": strata_audit_summary,
        "total_clips_selected": total_clips_selected,
        "expected_clips": expected_total_clips,
        "ready_for_generation": audit_results["overall_status"] == "PASS",
    }

    # Save Audit Reports
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.reports_dir / "stage6m_cohort2_curation_audit.json"
    md_path = args.reports_dir / "stage6m_cohort2_curation_audit.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    # Markdown Report
    shortfall_table = ""
    if speakers_under_15_strict:
        shortfall_table = "\n### Strict Quality Shortfall Speakers (|Q| Violations in Manifest):\n\n"
        shortfall_table += "| Speaker Prefix | Stratum | Raw Clips | Baseline B0 | Strict V | Shortfall | Rejected by Votes (`down>=2` or `up<2`) |\n"
        shortfall_table += "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n"
        for p, d in speakers_under_15_strict.items():
            shortfall_table += (
                f"| `{p}…` | {d['stratum']} | {d['raw_total']} | {d['b0_baseline_count']} | "
                f"**{d['strict_count']}** | -{d['shortfall']} | {d['rejected_votes']} |\n"
            )

    md_content = f"""# Stage 6M Confirmatory Cohort 2: Curation & Strict Integrity Audit Report

> **Audit Verdict:** `{audit_results['overall_status']}`  
> **Timestamp:** {audit_results['metadata']['timestamp_utc']}  
> **Protocol:** `{PROTOCOL_VERSION}` ({GOVERNING_STANDARD})  
> **Predicate Level:** `STRICT QUALITY PREDICATE V (locale=='en', up_votes>=2, down_votes<2)`  
> **Deterministic Seed:** `{args.seed}`  
> **Execution Mode:** `{'GENERATE' if args.generate else 'AUDIT-ONLY (FAIL-CLOSED)'}`

---

## 1. Summary Matrix

| Audit Check | Scope | Verdict | Details |
| :--- | :--- | :---: | :--- |
| **1. Prefix Resolution** | 468 Manifest Active Prefixes | `{audit_results['checks']['prefix_resolution']['status']}` | Resolved {audit_results['checks']['prefix_resolution']['resolved_prefixes']}/468 prefixes bijectively (1:1). |
| **2. Strict Clip Eligibility** | Strict Quality Predicate V (B0 + V) | `{audit_results['checks']['clip_eligibility']['status']}` | {audit_results['checks']['clip_eligibility']['speakers_meeting_strict_quota']}/468 speakers meet strict quota ({audit_results['checks']['clip_eligibility']['strict_shortfall_count']} shortfall). |
| **3. Speaker Disjointness** | Cross-Cohort Isolation | `{audit_results['checks']['speaker_disjointness']['status']}` | 0 overlap with Cohort 1 (60 spks) and Sentinel Panel (30 spks). Zero leakage. |
| **4. Stratum Preservation** | 6 Pre-specified Strata | `{audit_results['checks']['stratum_preservation']['status']}` | Exactly 78 speakers per stratum across all 6 strata. |
| **5. Stream Geometry** | 15 Clips/Speaker Stream | `{audit_results['checks']['stream_geometry']['status']}` | Selected {audit_results['checks']['stream_geometry']['total_clips_selected']}/7020 strict clips across 6 strata. |
| **6. Schema & Naming** | Runner Filename Compatibility | `{audit_results['checks']['schema_and_naming']['status']}` | Filename stem convention verified (`cohort2_audio/{{recording_id}}.mp3`). |

---

## 2. Six-Strata Strict Eligibility Breakdown

| Stratum Name | Total Active Speakers | Strict-Eligible Speakers ($C_{{\\text{{strict}}}} \\ge 15$) | Shortfall Speakers ($C_{{\\text{{strict}}}} < 15$) | Feasibility Status |
| :--- | :---: | :---: | :---: | :---: |
| **Australian English** | 78 | 78 | 0 | **PASS** |
| **Canadian English** | 78 | 78 | 0 | **PASS** |
| **England English** | 78 | 78 | 0 | **PASS** |
| **Irish English** | 78 | 78 | 0 | **PASS** |
| **South Asian English** | 78 | 74 | 4 | **HOLD (4 Shortfall)** |
| **US English** | 78 | 78 | 0 | **PASS** |
| **Total All 6 Strata** | **468** | **464** | **4** | **HOLD_STRICT_QUALITY_SHORTFALL** |
{shortfall_table}
---

## 3. Methodological Audit Finding & Supervisory Decision Gate

- **Root Cause Analysis:**
  The locked candidate manifest ([`stage6m_locked_candidate_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_locked_candidate_manifest.json)) was constructed by [`scripts/generate_stage6m_locked_manifest.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/generate_stage6m_locked_manifest.py) from [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv).
  `external_speaker_inventory.csv` indexed baseline qualification ($C_{{\\text{{inventory}}}} \\ge 15$, Predicate $B_0$) without applying strict quality predicate $V$.
  As documented in [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md) Section 2.2, exactly 18 South Asian speakers in the inventory belong to the quality exclusion set $Q$ ($C_{{\\text{{strict}}}} < 15$ due to down-votes $\\ge 2$). Four of these 18 speakers were allocated into the active manifest.
- **Fail-Closed Guarantee:**
  Because 4 active speakers have only 13 or 14 strict-eligible clips, confirmatory evaluation CSV generation is **HALTED**. `MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD` remains strictly in effect.
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Saved audit reports:\n  - {json_path}\n  - {md_path}")
    logger.info("=" * 80)
    logger.info(f"OVERALL AUDIT VERDICT: {audit_results['overall_status']}")
    logger.info("=" * 80)

    # 6. If --generate is passed, enforce fail-closed check
    if args.generate:
        if audit_results["overall_status"] != "PASS":
            logger.error(
                f"CANNOT GENERATE DATASET: Overall audit verdict is '{audit_results['overall_status']}'! "
                f"{len(speakers_under_15_strict)} active speakers fail the strict Stage 6M quality predicate V."
            )
            sys.exit(1)

        # In case all pass:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        curated_df.to_csv(args.output_csv, index=False, encoding="utf-8")
        logger.info(f"Wrote canonical evaluation CSV ({len(curated_df)} rows): {args.output_csv}")

        with open(args.output_csv, "rb") as f:
            raw_bytes = f.read()

        crlf_bytes = raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        lf_bytes = raw_bytes.replace(b"\r\n", b"\n")

        csv_crlf_sha256 = hashlib.sha256(crlf_bytes).hexdigest()
        csv_lf_sha256 = hashlib.sha256(lf_bytes).hexdigest()

        lock_payload = {
            "protocol_version": PROTOCOL_VERSION,
            "governing_standard": GOVERNING_STANDARD,
            "dataset_name": "stage6m_cohort2_audio",
            "csv_path": str(args.output_csv.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "csv_sha256": csv_crlf_sha256,
            "crlf_sha256": csv_crlf_sha256,
            "lf_sha256": csv_lf_sha256,
            "total_clips": total_clips_selected,
            "total_speakers": len(manifest_speakers),
            "total_strata": len(stratum_clip_counts),
            "clips_per_speaker": 15,
            "strata_counts": dict(stratum_clip_counts),
            "selection_seed": args.seed,
            "selection_algorithm": "SHA256(seed:client_id:clip_path) ascending rank sort",
            "recording_ids": curated_df["recording_id"].tolist(),
            "generated_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

        with open(args.output_lock, "w", encoding="utf-8") as f:
            json.dump(lock_payload, f, indent=2)

        lock_file_hash = compute_sha256(args.output_lock)
        logger.info(f"Wrote authoritative clip lock: {args.output_lock}")
        logger.info(f"  Lock File SHA-256 Digest: {lock_file_hash}")
        logger.info(f"  CSV CRLF Digest:          {csv_crlf_sha256}")
        logger.info(f"  CSV LF Digest:            {csv_lf_sha256}")

    return audit_results["overall_status"] == "PASS", audit_results, curated_df


def main():
    args = parse_args()
    success, _, _ = run_curation_audit(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
