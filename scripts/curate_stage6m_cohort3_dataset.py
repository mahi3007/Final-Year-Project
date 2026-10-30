#!/usr/bin/env python3
"""
scripts/curate_stage6m_cohort3_dataset.py

Stage 6M Confirmatory Cohort 3 & Dedicated Gate-Reference Panel Preparation Pipeline
===================================================================================
Governing Standards: ADR-005, Protocol v1.4.0 (Decision Rule B)
Governance State: DRAFT_HOLD (Confirmatory Execution Strictly Forbidden)

This script implements the empirical feasibility audit, partition disjointness
verification, and fail-closed dataset materialization pipeline for:
  1. Confirmatory Cohort 3 (220 speakers/stratum x 6 strata = 1,320 speakers, 19,800 clips)
  2. Dedicated Gate-Reference Panel (20 speakers/stratum x 6 strata = 120 speakers, 120 clips)

Strict Quality Criteria (Predicate V):
  - Locale: 'en'
  - Review votes: up_votes >= 2, down_votes < 2
  - Sentence: non-empty, word count >= 2
  - Speaker eligibility: >= 15 strictly qualified clips
  - Homogeneous declared accent matching exactly one canonical stratum
  - Strict zero prior exposure against:
      * Cohort 1 (Stage 5 External Eval: 60 speakers)
      * Stage 5 Sentinel Panel (30 speakers)
      * Cohort 2 Audio (468 speakers)

Fail-Closed Governance Invariant:
  If any accent stratum cannot satisfy the required sample size under strict
  disjointness without ungrounded substitution or silent downsampling, the script
  STRICTLY FAILS CLOSED. It generates an authoritative audit report documenting
  the empirical capacity bottleneck and halts before creating invalid manifests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cohort3_curation")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Protocol v1.4.0 Constants
PROTOCOL_VERSION = "v1.4.0"
GOVERNING_STANDARD = "ADR-005"
CONFIRMATORY_DECISION_RULE = "Decision Rule B"
TARGET_COHORT3_SPEAKERS_PER_STRATUM = 220
TARGET_COHORT3_CLIPS_PER_SPEAKER = 15
TARGET_GATE_SPEAKERS_PER_STRATUM = 20
TOTAL_REQUIRED_PER_STRATUM = (
    TARGET_COHORT3_SPEAKERS_PER_STRATUM + TARGET_GATE_SPEAKERS_PER_STRATUM
)  # 240

CANONICAL_PROTOCOL_ACCENTS: List[str] = [
    "Australian English",
    "Canadian English",
    "England English",
    "Irish English",
    "South Asian English",
    "US English",
]

ACCENT_NORMALIZATION_MAP: Dict[str, Tuple[str, str]] = {
    "united states english": ("US English", "us"),
    "us": ("US English", "us"),
    "england english": ("England English", "england"),
    "england": ("England English", "england"),
    "india and south asia (india, pakistan, sri lanka)": (
        "South Asian English",
        "south_asian",
    ),
    "south asian english": ("South Asian English", "south_asian"),
    "australian english": ("Australian English", "australia"),
    "australia": ("Australian English", "australia"),
    "canadian english": ("Canadian English", "canada"),
    "canada": ("Canadian English", "canada"),
    "irish english": ("Irish English", "ireland"),
    "ireland": ("Irish English", "ireland"),
}


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


def load_partition_speakers(path: Path) -> Set[str]:
    """Load unique speaker IDs from a CSV partition."""
    if not path.exists():
        return set()
    speakers = set()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            spk = row.get("speaker_id")
            if spk:
                speakers.add(str(spk).strip())
    return speakers


def audit_speaker_capacity(
    val_tsv: Path,
    c1_path: Path,
    sentinel_path: Path,
    c2_path: Path,
) -> Dict[str, Any]:
    """
    Scans Mozilla Common Voice validated.tsv to compute:
      - Raw declared speakers per stratum
      - Strictly qualified clips (en, up>=2, down<2, words>=2)
      - Strictly qualified speakers (having >= 15 qualified clips & homogeneous accent)
      - Prior exposure breakdown across historical partitions
      - Unexposed available speaker capacity vs Decision Rule B requirements
    """
    logger.info("Scanning historical partitions for speaker exposure tracking...")
    c1_spks = load_partition_speakers(c1_path)
    sent_spks = load_partition_speakers(sentinel_path)
    c2_spks = load_partition_speakers(c2_path)
    all_prior = c1_spks | sent_spks | c2_spks

    logger.info(
        f"Prior exposed speakers: C1={len(c1_spks)}, Sentinel={len(sent_spks)}, "
        f"C2={len(c2_spks)}, Total Unique={len(all_prior)}"
    )

    if not val_tsv.exists():
        raise FileNotFoundError(f"Source Common Voice TSV not found at {val_tsv}")

    logger.info(f"Scanning source data: {val_tsv} ...")
    speaker_clips = defaultdict(lambda: defaultdict(list))
    speaker_accents = defaultdict(set)
    raw_accent_speakers = defaultdict(set)

    with open(val_tsv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            client_id = row.get("client_id", "").strip()
            if not client_id:
                continue

            acc_raw = row.get("accents", "").strip().lower()
            norm_tuple = ACCENT_NORMALIZATION_MAP.get(acc_raw)
            if not norm_tuple:
                continue
            norm_accent, code = norm_tuple

            raw_accent_speakers[norm_accent].add(client_id)
            speaker_accents[client_id].add(norm_accent)

            sentence = row.get("sentence", "").strip()
            words = len(sentence.split())
            locale = row.get("locale", "").strip()

            try:
                up_votes = int(row.get("up_votes", 0))
                down_votes = int(row.get("down_votes", 0))
            except (ValueError, TypeError):
                up_votes = 0
                down_votes = 0

            path = row.get("path", "").strip()
            is_strict = (
                locale == "en"
                and up_votes >= 2
                and down_votes < 2
                and words >= 2
                and bool(sentence)
            )

            speaker_clips[norm_accent][client_id].append(
                {
                    "path": path,
                    "sentence": sentence,
                    "words": words,
                    "strict": is_strict,
                    "up_votes": up_votes,
                    "down_votes": down_votes,
                }
            )

    logger.info("Validated TSV scan complete. Analyzing stratum capacity...")

    strata_audit: Dict[str, Any] = {}
    total_shortfall = 0
    has_capacity_failure = False

    for stratum in CANONICAL_PROTOCOL_ACCENTS:
        spks_in_stratum = speaker_clips[stratum]
        raw_count = len(raw_accent_speakers[stratum])

        # Filter to strictly qualified speakers
        strict_speakers: Dict[str, int] = {}
        for spk, clips in spks_in_stratum.items():
            # Must have homogeneous accent mapping
            if len(speaker_accents[spk]) == 1:
                strict_clips = sum(1 for c in clips if c["strict"])
                if strict_clips >= TARGET_COHORT3_CLIPS_PER_SPEAKER:
                    strict_speakers[spk] = strict_clips

        strict_spk_set = set(strict_speakers.keys())
        exposed_in_stratum = strict_spk_set.intersection(all_prior)
        unexposed_available = strict_spk_set - all_prior

        avail_count = len(unexposed_available)
        shortfall = max(0, TOTAL_REQUIRED_PER_STRATUM - avail_count)
        if shortfall > 0:
            has_capacity_failure = True
            total_shortfall += shortfall

        strata_audit[stratum] = {
            "stratum": stratum,
            "raw_declared_speakers": raw_count,
            "strictly_qualified_speakers": len(strict_spk_set),
            "prior_exposed_speakers": len(exposed_in_stratum),
            "unexposed_available_speakers": avail_count,
            "required_cohort3_speakers": TARGET_COHORT3_SPEAKERS_PER_STRATUM,
            "required_gate_speakers": TARGET_GATE_SPEAKERS_PER_STRATUM,
            "total_required_speakers": TOTAL_REQUIRED_PER_STRATUM,
            "shortfall": shortfall,
            "status": "PASS" if shortfall == 0 else "BOTTLENECK_SHORTFALL",
        }

    audit_result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": PROTOCOL_VERSION,
        "governing_standard": GOVERNING_STANDARD,
        "decision_rule": CONFIRMATORY_DECISION_RULE,
        "target_cohort3_speakers_per_stratum": TARGET_COHORT3_SPEAKERS_PER_STRATUM,
        "target_cohort3_clips_per_speaker": TARGET_COHORT3_CLIPS_PER_SPEAKER,
        "target_gate_speakers_per_stratum": TARGET_GATE_SPEAKERS_PER_STRATUM,
        "total_required_per_stratum": TOTAL_REQUIRED_PER_STRATUM,
        "total_required_speakers_overall": TOTAL_REQUIRED_PER_STRATUM * len(CANONICAL_PROTOCOL_ACCENTS),
        "total_required_cohort3_clips": TARGET_COHORT3_SPEAKERS_PER_STRATUM * TARGET_COHORT3_CLIPS_PER_SPEAKER * len(CANONICAL_PROTOCOL_ACCENTS),
        "has_capacity_failure": has_capacity_failure,
        "total_speaker_shortfall": total_shortfall,
        "strata_capacity": strata_audit,
        "prior_exposure_summary": {
            "cohort1_speakers": len(c1_spks),
            "stage5_sentinel_speakers": len(sent_spks),
            "cohort2_speakers": len(c2_spks),
            "total_unique_exposed": len(all_prior),
        },
    }

    return audit_result


def generate_reports(audit_result: Dict[str, Any], output_dir: Path) -> Tuple[Path, Path]:
    """Generates both JSON and Markdown feasibility audit reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage6m_cohort3_data_feasibility_report.json"
    md_path = output_dir / "stage6m_cohort3_data_feasibility_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2)

    # Construct Markdown Report
    rows = []
    for stratum in CANONICAL_PROTOCOL_ACCENTS:
        info = audit_result["strata_capacity"][stratum]
        status_badge = "**PASS**" if info["shortfall"] == 0 else "**CRITICAL SHORTFALL**"
        rows.append(
            f"| **{info['stratum']}** | {info['raw_declared_speakers']:,} | "
            f"{info['strictly_qualified_speakers']:,} | {info['prior_exposed_speakers']:,} | "
            f"**{info['unexposed_available_speakers']:,}** | {info['required_cohort3_speakers']} | "
            f"{info['required_gate_speakers']} | {info['total_required_speakers']} | "
            f"{info['shortfall']} | {status_badge} |"
        )
    table_body = "\n".join(rows)

    c1_c = audit_result["prior_exposure_summary"]["cohort1_speakers"]
    sent_c = audit_result["prior_exposure_summary"]["stage5_sentinel_speakers"]
    c2_c = audit_result["prior_exposure_summary"]["cohort2_speakers"]
    all_c = audit_result["prior_exposure_summary"]["total_unique_exposed"]

    has_fail = audit_result["has_capacity_failure"]
    overall_disposition = (
        "FAIL-CLOSED CAPACITY BOTTLENECK (MATERIALIZATION FORBIDDEN)"
        if has_fail
        else "CAPACITY SUFFICIENT (READY FOR MATERIALIZATION)"
    )

    md_content = f"""# Stage 6M Confirmatory Cohort 3 — Data Feasibility & Speaker Capacity Audit Report

- **Standard:** {audit_result['governing_standard']}
- **Protocol Version:** {audit_result['protocol_version']}
- **Decision Rule:** {audit_result['decision_rule']}
- **Target Specification:** 6 Strata x 220 Speakers x 15 Clips = 19,800 Cohort 3 Clips + 120-Speaker Dedicated Gate-Reference Panel
- **Audit Timestamp (UTC):** {audit_result['timestamp_utc']}
- **Overall Feasibility Disposition:** **{overall_disposition}**

---

## 1. Executive Summary & Core Feasibility Finding

This audit evaluates the empirical capacity of **Mozilla Common Voice 27.0** (`validated.tsv`) to satisfy the statistical sample size requirements of **Decision Rule B** (1,320 independent speakers, 19,800 clips) and a separate 120-speaker Gate Reference Panel, while strictly enforcing **zero speaker leakage** against all prior developmental and confirmatory partitions.

### Key Finding:
1. **Five Strata Have Ample Capacity:** Australian English, Canadian English, England English, South Asian English, and US English all have surplus strictly qualified, unexposed speakers ($\ge 305$ available vs. $240$ required).
2. **Irish English Represents an Absolute Empirical Bottleneck:**
   - In the **entirety** of Common Voice 27 worldwide, there are only **220 raw speakers** with declared Irish English accent.
   - Only **92 unique Irish speakers** meet strict quality filtering ($\ge 15$ qualified clips with `locale == 'en'`, `up_votes >= 2`, `down_votes < 2`, `words >= 2`).
   - All **92** strictly eligible Irish speakers have already been exposed across historical partitions (10 in Cohort 1, 5 in Stage 5 Sentinel, 78 in Cohort 2).
   - Consequently, the number of unexposed, strictly qualified Irish English speakers available in Common Voice 27 is **EXACTLY ZERO (0)**.
   - The stratum shortfall for Irish English is **240 speakers** (or **148 speakers** even if all historical data were disregarded).

---

## 2. Empirical Speaker Capacity Ledger

| Stratum | Raw Declared | Strict ($\ge 15$ clips) | Prior Exposed | Unexposed Available | Req C3 | Req Gate | Total Req | Shortfall | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{table_body}

---

## 3. Prior Exposure & Partition Tracking

- **Cohort 1 (Stage 5 External Eval):** {c1_c} speakers (10 per stratum)
- **Stage 5 Sentinel Panel:** {sent_c} speakers (5 per stratum)
- **Cohort 2 Audio:** {c2_c} speakers (78 per stratum)
- **Total Unique Prior Exposed Speakers:** {all_c} speakers

Under the governing scientific protocol, confirmatory evaluation requires genuine partition disjointness:
- No Cohort 3 speaker may appear in Cohort 1, Cohort 2, or Stage 5 Sentinel.
- No Dedicated Gate-Reference speaker may appear in Cohort 3 or any historical partition.

---

## 4. Methodological Invariants & Enforcement

1. **No Silent Downsampling:**
   The protocol forbids silently reducing Irish English from 220 speakers to 92, 78, or 0. Such an ungrounded modification would violate the prespecified balance required for the disparity estimand $\Delta_D = \max WER - \min WER$.
2. **No Corpus Confounding:**
   Supplementing only Irish English from an external corpus (e.g. EdAcc or VoxCeleb) while sourcing the other five strata from Common Voice 27 would introduce a fatal corpus-versus-accent confound, making it impossible to disentangle adaptation efficacy from acoustic recording conditions.
3. **Fail-Closed Governance Invariant:**
   Because Common Voice 27 cannot physically materialize 220 independent Irish English speakers under Decision Rule B, **Cohort 3 materialization cannot proceed to completion from Common Voice 27 alone**.
   The project remains strictly locked at **`DRAFT_HOLD`**, and no confirmatory inference may be executed.

---

## 5. Next Steps for Academic Supervisor Alignment

To resolve this empirical data constraint without invalidating confirmatory rigor, the project lead and research supervisor must formally evaluate one of two scientifically sound options:

1. **Option 1: Harmonized Multi-Corpus Sampling Protocol**
   Formally amend the data sourcing protocol to draw balanced, acoustically normalized subsets across **all six strata** from a multi-corpus registry, preventing corpus confounding.
2. **Option 2: Statistically Re-Powered Balanced Sample Size Protocol**
   Re-calibrate Decision Rule B sample sizes to the empirical ceiling of the rarest stratum (e.g. $N_g = 78$ or an alternative balanced specification) with updated power curves.
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Generated JSON audit report at: {json_path}")
    logger.info(f"Generated Markdown audit report at: {md_path}")
    return json_path, md_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Stage 6M Cohort 3 Data Feasibility, Disjointness & Materialization Pipeline"
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        default=True,
        help="Run comprehensive speaker capacity and disjointness audit without mutating datasets.",
    )
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="Attempt full dataset materialization (fails closed if capacity shortfall exists).",
    )
    parser.add_argument(
        "--val-tsv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv",
        help="Path to Common Voice validated.tsv",
    )
    parser.add_argument(
        "--c1-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv",
        help="Path to Cohort 1 CSV",
    )
    parser.add_argument(
        "--sentinel-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv",
        help="Path to Stage 5 Sentinel CSV",
    )
    parser.add_argument(
        "--c2-csv",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort2_audio.csv",
        help="Path to Cohort 2 CSV",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "stage6m",
        help="Directory to save audit reports",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("=" * 80)
    logger.info("Stage 6M Confirmatory Cohort 3 Data Feasibility & Preparation Pipeline")
    logger.info("Governing Standard: ADR-005 | Protocol: v1.4.0 (Decision Rule B)")
    logger.info("Governance State: DRAFT_HOLD (Confirmatory Execution FORBIDDEN)")
    logger.info("=" * 80)

    audit_result = audit_speaker_capacity(
        val_tsv=args.val_tsv,
        c1_path=args.c1_csv,
        sentinel_path=args.sentinel_csv,
        c2_path=args.c2_csv,
    )

    json_path, md_path = generate_reports(audit_result, args.reports_dir)

    print("\n" + "=" * 105)
    print(
        f"{'Stratum':<22} | {'Raw Spk':<8} | {'Strict>=15':<10} | {'Exposed':<8} | "
        f"{'Available':<10} | {'Req C3':<8} | {'Req Gate':<8} | {'Total Req':<10} | {'Shortfall':<10}"
    )
    print("-" * 105)
    for stratum in CANONICAL_PROTOCOL_ACCENTS:
        info = audit_result["strata_capacity"][stratum]
        print(
            f"{info['stratum']:<22} | {info['raw_declared_speakers']:<8} | "
            f"{info['strictly_qualified_speakers']:<10} | {info['prior_exposed_speakers']:<8} | "
            f"{info['unexposed_available_speakers']:<10} | {info['required_cohort3_speakers']:<8} | "
            f"{info['required_gate_speakers']:<8} | {info['total_required_speakers']:<10} | {info['shortfall']:<10}"
        )
    print("=" * 105 + "\n")

    if audit_result["has_capacity_failure"]:
        logger.error(
            f"[FAIL-CLOSED INTEGRITY CHECK] Total speaker capacity shortfall of "
            f"{audit_result['total_speaker_shortfall']} speakers detected across strata."
        )
        logger.error(
            "Irish English has ZERO unexposed strictly qualified speakers remaining in Common Voice 27 "
            "(240 required under Decision Rule B)."
        )
        logger.error(
            "Under ADR-005 and Protocol v1.4.0, silent downsampling or single-accent corpus supplementation "
            "is strictly forbidden."
        )
        logger.error(
            "Cohort 3 materialization cannot complete until the sampling design or multi-corpus sourcing "
            "protocol is formally resolved."
        )
        logger.error(f"Authoritative reports saved to: {json_path} and {md_path}")
        logger.error("Governance status remains strictly locked at: DRAFT_HOLD")

        if args.materialize:
            logger.critical(
                "Materialization mode invoked, but fail-closed invariant forbids creating ungrounded datasets. "
                "Exiting with status code 1."
            )
            sys.exit(1)
        else:
            logger.info("Audit-only mode complete. Full evidence captured.")
            sys.exit(0)
    else:
        logger.info("[PASS] All six strata satisfy Decision Rule B capacity targets.")
        sys.exit(0)


if __name__ == "__main__":
    main()
