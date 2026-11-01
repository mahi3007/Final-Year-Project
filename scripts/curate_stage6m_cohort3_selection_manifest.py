#!/usr/bin/env python3
"""
scripts/curate_stage6m_cohort3_selection_manifest.py

Stage 6M v1.5 — Milestone 7.1-7.3: Cohort 3 Source Audit & Provisional Manifest Curation
========================================================================================
Governing Standards: Protocol Section 14.7 (Project-Lead Academic Authorization)
Governing Base: Commit 06cf833
Governance State: AUTHORIZED_FOR_DATA_PREPARATION (Confirmatory Adaptation Separately GATED)

Authoritative Tasks:
  Task A: Bitwise audit and verification of source corpus (validated.tsv).
  Task B: Historical exposure audit against Cohort 1, Sentinel, and Cohort 2 (558 speakers).
  Task C: Reconcile strictly eligible unexposed speaker capacity across canonical strata.
  Task D: Deterministic panel selection (220 eval + 20 gate per confirmatory stratum, 65 Australian reserve).
  Task E: Generate machine-readable provisional selection manifests (JSON and CSV, UNLOCKED).
  Task F: Validate exact counts, strict disjointness, and clip predicates.
  Task G: Produce authoritative audit reports in Markdown and JSON.
  Task H: Preserve separate execution gating (GPU adaptation strictly blocked).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import subprocess
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
logger = logging.getLogger("cohort3_selection")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# Protocol v1.5 Approved Constants
# ------------------------------------------------------------------------------
PROTOCOL_VERSION = "v1.5-five-stratum-parity"
GOVERNING_STANDARD = "Protocol Section 14.7 (Project-Lead Academic Authorization)"
PREDICATE_VERSION = "V1.5-Strict"

SELECTION_SEED = 20261101  # Date of formal Project-Lead Academic Authorization

TARGET_EVAL_SPEAKERS_PER_STRATUM = 220
TARGET_GATE_SPEAKERS_PER_STRATUM = 20
TARGET_CLIPS_PER_SPEAKER = 15

EXPECTED_SOURCE_IDENTITY = {
    "file_path": "datasets/external/common_voice_27/validated.tsv",
    "rows": 1929267,
    "bytes": 614927262,
    "sha256": "733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a",
}

EXPECTED_HISTORICAL_PARTITIONS = {
    "stage5_external_eval.csv": 60,
    "stage5_sentinel_panel.csv": 30,
    "stage6m_cohort2_audio.csv": 468,
}
EXPECTED_TOTAL_HISTORICAL_SPEAKERS = 558

EXPECTED_UNEXPOSED_CAPACITIES = {
    "Australian English": 305,
    "Canadian English": 418,
    "England English": 1120,
    "South Asian English": 653,
    "US English": 3791,
    "Irish English": 0,
}

CONFIRMATORY_STRATA = [
    "Australian English",
    "Canadian English",
    "England English",
    "South Asian English",
    "US English",
]

STRATUM_CODES = {
    "Australian English": "australia",
    "Canadian English": "canada",
    "England English": "england",
    "South Asian English": "south_asian",
    "US English": "us",
    "Irish English": "ireland",
}

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
    """Compute lowercase SHA-256 hex digest for Path, bytes, or str."""
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


def get_git_commit_sha(repo_root: Path) -> str:
    """Retrieve current Git commit SHA via git rev-parse HEAD (fail-closed)."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        sha = res.stdout.strip()
        if not sha or len(sha) != 40:
            raise RuntimeError(f"Invalid git commit SHA resolved: '{sha}'")
        return sha
    except Exception as exc:
        raise RuntimeError(
            f"Fail-Closed Git Resolution: Unable to resolve HEAD commit SHA: {exc}"
        ) from exc


def load_historical_speakers(
    partitions: Dict[str, Path],
) -> Tuple[Set[str], Dict[str, Set[str]], Dict[str, Dict[str, Any]]]:
    """
    Fail-closed loader for historical partition CSV files.
    Verifies file existence, headers, and exact speaker counts.
    """
    all_speakers: Set[str] = set()
    partition_speakers: Dict[str, Set[str]] = {}
    partition_provenance: Dict[str, Dict[str, Any]] = {}

    for fname, exp_count in EXPECTED_HISTORICAL_PARTITIONS.items():
        fpath = partitions.get(fname)
        if not fpath or not fpath.exists():
            raise FileNotFoundError(
                f"Fail-Closed Check: Missing historical partition file: {fpath}"
            )

        spks: Set[str] = set()
        rows = 0
        with open(fpath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "speaker_id" not in reader.fieldnames:
                raise ValueError(
                    f"Malformed historical partition '{fname}': missing 'speaker_id' column."
                )
            for r in reader:
                rows += 1
                sid = r.get("speaker_id", "").strip()
                if sid:
                    spks.add(sid)

        if len(spks) != exp_count:
            raise ValueError(
                f"Historical count mismatch in '{fname}': expected {exp_count}, found {len(spks)}"
            )

        fbytes = fpath.stat().st_size
        fsha = compute_sha256(fpath)
        partition_speakers[fname] = spks
        partition_provenance[fname] = {
            "file_name": fname,
            "file_path": str(fpath.relative_to(PROJECT_ROOT).as_posix()),
            "file_bytes": fbytes,
            "file_sha256": fsha,
            "row_count": rows,
            "unique_speakers": len(spks),
        }
        all_speakers.update(spks)

    # Verify pairwise disjointness
    names = list(partition_speakers.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            overlap = partition_speakers[p1].intersection(partition_speakers[p2])
            if overlap:
                raise ValueError(
                    f"Historical Disjointness Failure: {len(overlap)} overlapping speakers between {p1} and {p2}"
                )

    if len(all_speakers) != EXPECTED_TOTAL_HISTORICAL_SPEAKERS:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_HISTORICAL_SPEAKERS} total historical speakers, found {len(all_speakers)}"
        )

    return all_speakers, partition_speakers, partition_provenance


def audit_source_and_extract_eligible(
    val_tsv: Path,
    all_prior: Set[str],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, List[Dict[str, Any]]]]]:
    """
    Audits validated.tsv, verifies bitwise identity, and extracts all strictly eligible
    unexposed speakers and their qualifying clips.
    """
    logger.info("Computing bitwise SHA-256 for source validated.tsv...")
    tsv_bytes = val_tsv.stat().st_size
    tsv_sha256 = compute_sha256(val_tsv)

    if tsv_bytes != EXPECTED_SOURCE_IDENTITY["bytes"]:
        raise ValueError(
            f"Source byte size mismatch: expected {EXPECTED_SOURCE_IDENTITY['bytes']}, got {tsv_bytes}"
        )
    if tsv_sha256 != EXPECTED_SOURCE_IDENTITY["sha256"]:
        raise ValueError(
            f"Source SHA-256 mismatch: expected {EXPECTED_SOURCE_IDENTITY['sha256']}, got {tsv_sha256}"
        )

    logger.info(f"Source verified: {tsv_bytes:,} bytes, SHA-256={tsv_sha256}")

    # Track speaker data
    # speaker_clips: stratum -> client_id -> list of clip dicts
    speaker_clips: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    speaker_distinct_paths: Dict[str, Dict[str, Set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    speaker_accents: Dict[str, Set[str]] = defaultdict(set)
    raw_accent_speakers: Dict[str, Set[str]] = defaultdict(set)

    rows_scanned = 0
    with open(val_tsv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows_scanned += 1
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

            path_raw = row.get("path", "").strip()
            sentence = row.get("sentence", "").strip()
            words = len(sentence.split())
            locale = row.get("locale", "").strip()

            try:
                up_votes = int(row.get("up_votes", 0))
                down_votes = int(row.get("down_votes", 0))
            except (ValueError, TypeError):
                up_votes = 0
                down_votes = 0

            # Predicate V1.5-Strict
            is_strict = (
                bool(path_raw)
                and path_raw.endswith(".mp3")
                and locale == "en"
                and up_votes >= 2
                and down_votes < 2
                and words >= 2
                and bool(sentence)
            )

            if is_strict:
                if path_raw not in speaker_distinct_paths[norm_accent][client_id]:
                    speaker_distinct_paths[norm_accent][client_id].add(path_raw)
                    clip_info = {
                        "path": path_raw,
                        "recording_id": Path(path_raw).stem,
                        "sentence": sentence,
                        "word_count": words,
                        "up_votes": up_votes,
                        "down_votes": down_votes,
                    }
                    speaker_clips[norm_accent][client_id].append(clip_info)

    if rows_scanned != EXPECTED_SOURCE_IDENTITY["rows"]:
        raise ValueError(
            f"Source row count mismatch: expected {EXPECTED_SOURCE_IDENTITY['rows']}, got {rows_scanned}"
        )

    logger.info(f"Scanned {rows_scanned:,} rows. Evaluating eligibility...")

    # Filter for strictly eligible and unexposed speakers
    eligible_unexposed: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(dict)
    capacity_audit: Dict[str, Any] = {}

    all_strata = CONFIRMATORY_STRATA + ["Irish English"]
    for stratum in all_strata:
        raw_count = len(raw_accent_speakers[stratum])
        strict_speakers: Dict[str, List[Dict[str, Any]]] = {}

        for spk, clips in speaker_clips[stratum].items():
            if len(speaker_accents[spk]) == 1:  # homogeneous accent
                if len(clips) >= TARGET_CLIPS_PER_SPEAKER:  # at least 15 qualifying clips
                    strict_speakers[spk] = clips

        strict_set = set(strict_speakers.keys())
        exposed_in_stratum = strict_set.intersection(all_prior)
        unexposed_set = strict_set - all_prior

        expected_cap = EXPECTED_UNEXPOSED_CAPACITIES[stratum]
        if len(unexposed_set) != expected_cap:
            raise ValueError(
                f"Capacity mismatch for {stratum}: expected {expected_cap}, found {len(unexposed_set)}"
            )

        for spk in unexposed_set:
            eligible_unexposed[stratum][spk] = strict_speakers[spk]

        capacity_audit[stratum] = {
            "stratum": stratum,
            "raw_declared_speakers": raw_count,
            "strictly_qualified_speakers": len(strict_set),
            "prior_exposed_speakers": len(exposed_in_stratum),
            "unexposed_available_speakers": len(unexposed_set),
            "expected_unexposed_capacity": expected_cap,
            "capacity_verified": True,
        }
        logger.info(
            f"Capacity verified for {stratum}: {len(unexposed_set)} available (expected {expected_cap})"
        )

    source_provenance = {
        "file_path": EXPECTED_SOURCE_IDENTITY["file_path"],
        "rows_scanned": rows_scanned,
        "bytes": tsv_bytes,
        "sha256": tsv_sha256,
        "verified": True,
    }

    return (
        {
            "source_provenance": source_provenance,
            "capacity_audit": capacity_audit,
        },
        eligible_unexposed,
    )


def select_cohort3_panels(
    eligible_unexposed: Dict[str, Dict[str, List[Dict[str, Any]]]],
    seed: int = SELECTION_SEED,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Deterministically selects evaluation, gate-reference, and reserve panels.
    Selects exactly 15 qualifying clips per speaker.
    """
    logger.info(f"Selecting panels with deterministic seed {seed}...")

    manifest_metadata: Dict[str, Any] = {
        "manifest_type": "PROVISIONAL_SELECTION_MANIFEST",
        "manifest_status": "UNLOCKED",
        "protocol_version": PROTOCOL_VERSION,
        "governing_standard": GOVERNING_STANDARD,
        "selection_seed": seed,
        "predicate_version": PREDICATE_VERSION,
        "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_selected_speakers": 0,
        "total_selected_clips": 0,
        "panels_summary": {},
    }

    selected_rows: List[Dict[str, Any]] = []
    selected_speakers_by_role: Dict[str, Dict[str, Set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )

    for stratum in CONFIRMATORY_STRATA:
        spk_dict = eligible_unexposed[stratum]
        # Deterministic speaker ranking
        # rank_key = sha256(seed : speaker : stratum : client_id)
        ranked_speakers = sorted(
            spk_dict.keys(),
            key=lambda sid: hashlib.sha256(
                f"{seed}:speaker:{stratum}:{sid}".encode("utf-8")
            ).hexdigest(),
        )

        n_avail = len(ranked_speakers)
        n_eval = TARGET_EVAL_SPEAKERS_PER_STRATUM  # 220
        n_gate = TARGET_GATE_SPEAKERS_PER_STRATUM  # 20

        eval_spks = ranked_speakers[:n_eval]
        gate_spks = ranked_speakers[n_eval : n_eval + n_gate]
        reserve_spks = ranked_speakers[n_eval + n_gate :]

        if len(eval_spks) != n_eval:
            raise ValueError(
                f"Failed to select {n_eval} evaluation speakers for {stratum}"
            )
        if len(gate_spks) != n_gate:
            raise ValueError(
                f"Failed to select {n_gate} gate speakers for {stratum}"
            )

        if stratum == "Australian English":
            if len(reserve_spks) != 65:
                raise ValueError(
                    f"Expected 65 Australian reserve speakers, got {len(reserve_spks)}"
                )

        selected_speakers_by_role["evaluation"][stratum] = set(eval_spks)
        selected_speakers_by_role["gate_reference"][stratum] = set(gate_spks)
        roles_to_process = [
            ("evaluation", eval_spks),
            ("gate_reference", gate_spks),
        ]
        if stratum == "Australian English":
            roles_to_process.append(("australian_reserve", reserve_spks))
            selected_speakers_by_role["australian_reserve"][stratum] = set(reserve_spks)

        stratum_code = STRATUM_CODES[stratum]

        # Process each speaker and select exactly 15 clips
        for role, spk_list in roles_to_process:
            for spk_id in spk_list:
                clips = spk_dict[spk_id]
                # Deterministic clip ranking: sha256(seed : clip : spk_id : clip_path)
                ranked_clips = sorted(
                    clips,
                    key=lambda c: hashlib.sha256(
                        f"{seed}:clip:{spk_id}:{c['path']}".encode("utf-8")
                    ).hexdigest(),
                )
                chosen_clips = ranked_clips[:TARGET_CLIPS_PER_SPEAKER]
                if len(chosen_clips) != TARGET_CLIPS_PER_SPEAKER:
                    raise ValueError(
                        f"Speaker {spk_id} has only {len(chosen_clips)} clips, requires {TARGET_CLIPS_PER_SPEAKER}"
                    )

                for clip_order, c in enumerate(chosen_clips, start=1):
                    rec_id = c["recording_id"]
                    row = {
                        "recording_id": rec_id,
                        "speaker_id": spk_id,
                        "speaker_id_prefix": spk_id[:24],
                        "accent_group": stratum,
                        "stratum_code": stratum_code,
                        "panel_role": role,
                        "source_path": f"datasets/external/common_voice_27/clips/{c['path']}",
                        "clip_filename": c["path"],
                        "expected_audio_path": f"datasets/cohort3_audio/{c['path']}",
                        "transcript": c["sentence"],
                        "word_count": c["word_count"],
                        "up_votes": c["up_votes"],
                        "down_votes": c["down_votes"],
                        "selection_seed": seed,
                        "clip_order_within_speaker": clip_order,
                        "protocol_version": PROTOCOL_VERSION,
                        "dataset_name": "stage6m_cohort3_provisional",
                    }
                    selected_rows.append(row)

    # Compute panel summaries
    total_eval_spks = sum(
        len(s) for s in selected_speakers_by_role["evaluation"].values()
    )
    total_gate_spks = sum(
        len(s) for s in selected_speakers_by_role["gate_reference"].values()
    )
    total_reserve_spks = sum(
        len(s) for s in selected_speakers_by_role["australian_reserve"].values()
    )
    total_spks = total_eval_spks + total_gate_spks + total_reserve_spks

    manifest_metadata["total_selected_speakers"] = total_spks
    manifest_metadata["total_selected_clips"] = len(selected_rows)
    manifest_metadata["panels_summary"] = {
        "evaluation_speakers_per_accent": TARGET_EVAL_SPEAKERS_PER_STRATUM,
        "confirmatory_strata_count": len(CONFIRMATORY_STRATA),
        "total_evaluation_speakers": total_eval_spks,
        "gate_reference_speakers_per_accent": TARGET_GATE_SPEAKERS_PER_STRATUM,
        "total_gate_reference_speakers": total_gate_spks,
        "australian_replacement_reserve_speakers": total_reserve_spks,
        "clips_per_speaker": TARGET_CLIPS_PER_SPEAKER,
        "total_evaluation_clips": total_eval_spks * TARGET_CLIPS_PER_SPEAKER,
        "total_gate_clips": total_gate_spks * TARGET_CLIPS_PER_SPEAKER,
        "total_reserve_clips": total_reserve_spks * TARGET_CLIPS_PER_SPEAKER,
        "grand_total_clips": len(selected_rows),
    }

    return manifest_metadata, selected_rows


def validate_selected_manifest(
    metadata: Dict[str, Any],
    rows: List[Dict[str, Any]],
    all_prior: Set[str],
) -> Dict[str, Any]:
    """
    Exhaustively validates Task F invariants:
      - Exact speaker counts
      - Exact panel disjointness
      - Historical exposure disjointness
      - Required clips per speaker
      - No duplicate speaker or clip IDs
      - Australian reserve count
      - Zero overlap between panels
    """
    logger.info("Validating provisional manifest invariants...")

    spk_roles: Dict[str, str] = {}
    spk_strata: Dict[str, str] = {}
    spk_clips: Dict[str, List[str]] = defaultdict(list)
    clip_ids: Set[str] = set()

    for r in rows:
        sid = r["speaker_id"]
        role = r["panel_role"]
        stratum = r["accent_group"]
        cid = r["recording_id"]

        if sid in spk_roles and spk_roles[sid] != role:
            raise ValueError(f"Speaker {sid} assigned multiple roles: {spk_roles[sid]} and {role}")
        spk_roles[sid] = role

        if sid in spk_strata and spk_strata[sid] != stratum:
            raise ValueError(f"Speaker {sid} assigned multiple strata: {spk_strata[sid]} and {stratum}")
        spk_strata[sid] = stratum

        if cid in clip_ids:
            raise ValueError(f"Duplicate clip ID detected: {cid}")
        clip_ids.add(cid)
        spk_clips[sid].append(cid)

    # 1. Historical exposure disjointness
    current_spks = set(spk_roles.keys())
    hist_overlap = current_spks.intersection(all_prior)
    if hist_overlap:
        raise ValueError(
            f"Historical Exposure Violation: {len(hist_overlap)} selected speakers overlap with historical partitions!"
        )

    # 2. Panel counts
    eval_spks = [s for s, r in spk_roles.items() if r == "evaluation"]
    gate_spks = [s for s, r in spk_roles.items() if r == "gate_reference"]
    reserve_spks = [s for s, r in spk_roles.items() if r == "australian_reserve"]

    if len(eval_spks) != 1100:
        raise ValueError(f"Expected 1,100 evaluation speakers, got {len(eval_spks)}")
    if len(gate_spks) != 100:
        raise ValueError(f"Expected 100 gate speakers, got {len(gate_spks)}")
    if len(reserve_spks) != 65:
        raise ValueError(f"Expected 65 Australian reserve speakers, got {len(reserve_spks)}")

    # 3. Panel disjointness
    s_eval = set(eval_spks)
    s_gate = set(gate_spks)
    s_reserve = set(reserve_spks)

    if s_eval.intersection(s_gate):
        raise ValueError("Overlap detected between evaluation and gate panels!")
    if s_eval.intersection(s_reserve):
        raise ValueError("Overlap detected between evaluation and reserve panels!")
    if s_gate.intersection(s_reserve):
        raise ValueError("Overlap detected between gate and reserve panels!")

    # 4. Clip counts per speaker
    for sid, c_list in spk_clips.items():
        if len(c_list) != TARGET_CLIPS_PER_SPEAKER:
            raise ValueError(
                f"Speaker {sid} has {len(c_list)} clips, expected exactly {TARGET_CLIPS_PER_SPEAKER}"
            )

    # 5. Stratum breakdown
    strata_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for sid, role in spk_roles.items():
        strata_counts[spk_strata[sid]][role] += 1

    for stratum in CONFIRMATORY_STRATA:
        if strata_counts[stratum]["evaluation"] != 220:
            raise ValueError(f"{stratum} eval count is {strata_counts[stratum]['evaluation']}, expected 220")
        if strata_counts[stratum]["gate_reference"] != 20:
            raise ValueError(f"{stratum} gate count is {strata_counts[stratum]['gate_reference']}, expected 20")
        if stratum == "Australian English" and strata_counts[stratum]["australian_reserve"] != 65:
            raise ValueError(f"Australian reserve count is {strata_counts[stratum]['australian_reserve']}, expected 65")

    validation_result = {
        "validation_status": "PASS",
        "total_unique_speakers": len(current_spks),
        "total_unique_clips": len(clip_ids),
        "historical_exposure_overlap": 0,
        "panel_disjointness_verified": True,
        "clips_per_speaker_verified": True,
        "speaker_counts": {
            "evaluation_speakers": len(eval_spks),
            "gate_reference_speakers": len(gate_spks),
            "australian_reserve_speakers": len(reserve_spks),
            "total_selected": len(current_spks),
        },
        "clip_counts": {
            "evaluation_clips": len(eval_spks) * TARGET_CLIPS_PER_SPEAKER,
            "gate_reference_clips": len(gate_spks) * TARGET_CLIPS_PER_SPEAKER,
            "australian_reserve_clips": len(reserve_spks) * TARGET_CLIPS_PER_SPEAKER,
            "total_clips": len(rows),
        },
        "strata_counts": dict(strata_counts),
    }

    logger.info("Validation PASSED across all criteria.")
    return validation_result


def write_manifest_files(
    metadata: Dict[str, Any],
    rows: List[Dict[str, Any]],
    output_dir: Path,
) -> Tuple[Path, Path, str, str]:
    """Writes provisional JSON and CSV manifests and returns paths and SHA-256."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage6m_cohort3_provisional_manifest.json"
    csv_path = output_dir / "stage6m_cohort3_provisional_manifest.csv"

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    csv_sha = compute_sha256(csv_path)

    # Attach CSV hash to JSON metadata
    metadata["provisional_csv_filename"] = csv_path.name
    metadata["provisional_csv_sha256"] = csv_sha
    manifest_data = {
        "metadata": metadata,
        "speakers_count": metadata["total_selected_speakers"],
        "clips_count": metadata["total_selected_clips"],
        "records": rows,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    json_sha = compute_sha256(json_path)
    logger.info(f"Wrote provisional JSON manifest: {json_path} (SHA-256: {json_sha})")
    logger.info(f"Wrote provisional CSV manifest: {csv_path} (SHA-256: {csv_sha})")

    return json_path, csv_path, json_sha, csv_sha


def generate_audit_reports(
    audit_data: Dict[str, Any],
    output_dir: Path,
) -> Tuple[Path, Path]:
    """Generates stage6m_cohort3_source_audit.md and .json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "stage6m_cohort3_source_audit.json"
    md_path = output_dir / "stage6m_cohort3_source_audit.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    src = audit_data["source_identity"]
    hist = audit_data["historical_exposure"]
    cap = audit_data["speaker_capacity"]
    sel = audit_data["panel_selection"]
    val = audit_data["validation"]
    man = audit_data["provisional_manifest"]

    table_rows = []
    for stratum in CONFIRMATORY_STRATA + ["Irish English"]:
        c = cap.get(stratum, {})
        s = val["strata_counts"].get(stratum, {})
        ev = s.get("evaluation", 0)
        gt = s.get("gate_reference", 0)
        res = s.get("australian_reserve", 0)
        avail = c.get("unexposed_available_speakers", 0)
        table_rows.append(
            f"| **{stratum}** | {c.get('raw_declared_speakers', 0):,} | "
            f"{c.get('strictly_qualified_speakers', 0):,} | {c.get('prior_exposed_speakers', 0):,} | "
            f"**{avail:,}** | {ev} | {gt} | {res} | **VERIFIED** |"
        )
    cap_table = "\n".join(table_rows)

    md_content = f"""# Stage 6M v1.5 — Cohort 3 Source Identity & Selection Manifest Audit Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_SOURCE_AUDIT`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **GOVERNANCE DISPOSITION:** **AUTHORIZED FOR DATA PREPARATION** (Confirmatory GPU Adaptation Separately Gated)  
> **AUDIT TIMESTAMP (UTC):** {audit_data['timestamp_utc']}  
> **SELECTION SEED:** `{SELECTION_SEED}`  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  

---

## 1. Executive Summary

In accordance with formal Project-Lead Academic Authorization executed under Protocol Section 14.7, this audit establishes the empirical source data integrity, historical partition disjointness, and provisional panel selection for **Cohort 3 Data Preparation**:

1. **Source Identity Verified:** Mozilla Common Voice 27.0 `validated.tsv` matches its authoritative audit hash and size with bitwise exactness (**0 byte difference**).
2. **Historical Exposure Fully Excluded:** All 558 historical speakers across Cohort 1 (60), Stage 5 Sentinel (30), and Cohort 2 (468) are verified as pairwise disjoint and 100% excluded from the Cohort 3 selection pool (**0 speaker overlap**).
3. **Canonical Capacity Confirmed:** Eligible unexposed capacities match registered requirements across all strata, including 305 Australian speakers and 0 unexposed Irish speakers.
4. **Provisional Panels Selected:** Exactly 1,100 confirmatory evaluation speakers ($220 \times 5$), 100 separate gate-reference speakers ($20 \times 5$), and 65 Australian replacement reserve speakers are deterministically selected with seed `{SELECTION_SEED}`.
5. **Provisional Manifest Generated:** An unlocked machine-readable selection manifest (JSON and CSV) is constructed containing 18,975 qualifying clips across 1,265 unique speakers.
6. **Execution Gating Preserved:** Model loading, GPU test-time adaptation, and confirmatory inference remain **STRICTLY BLOCKED** under a separate execution gate pending physical audio download, decode validation, and final manifest locking.

---

## 2. Task A — Source Corpus Bitwise Identity

| Metric | Prespecified Audit Target | Actual Measured Value | Verdict |
| :--- | :--- | :--- | :---: |
| **Source File** | `datasets/external/common_voice_27/validated.tsv` | `datasets/external/common_voice_27/validated.tsv` | **PASS** |
| **Row Count** | 1,929,267 rows | {src['rows_scanned']:,} rows | **PASS** |
| **Byte Size** | 614,927,262 bytes | {src['bytes']:,} bytes | **PASS** |
| **SHA-256 Digest** | `{EXPECTED_SOURCE_IDENTITY['sha256']}` | `{src['sha256']}` | **PASS (BITWISE)** |

---

## 3. Task B — Historical Partition Exposure Reconciliation

| Historical Partition | File Name | Unique Speakers | Historical Exposure Excluded | Overlap with Cohort 3 |
| :--- | :--- | :---: | :---: | :---: |
| **Cohort 1** | `stage5_external_eval.csv` | 60 | 60 | **0** |
| **Stage 5 Sentinel** | `stage5_sentinel_panel.csv` | 30 | 30 | **0** |
| **Cohort 2** | `stage6m_cohort2_audio.csv` | 468 | 468 | **0** |
| **Total Unique Prior** | — | **558** | **558** | **EXACTLY ZERO (0)** |

---

## 4. Task C — Reconciled Speaker Capacity Ledger

| Stratum | Raw Declared | Strict ($\\ge 15$ clips) | Prior Exposed | Available Unexposed | Selected Eval | Selected Gate | Selected Reserve | Capacity Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{cap_table}

---

## 5. Task D & E — Provisional Panel Selection Architecture

- **Selection Seed:** `{SELECTION_SEED}` (Date of Project-Lead Authorization)
- **Selection Algorithm:**
  1. Candidate unexposed eligible speakers ranked by `sha256("{SELECTION_SEED}:speaker:<stratum>:<speaker_id>")`.
  2. First 220 speakers allocated to `evaluation`.
  3. Next 20 speakers allocated to `gate_reference`.
  4. For Australian English, remaining 65 speakers allocated to `australian_reserve`.
  5. For each speaker, qualifying clips ranked by `sha256("{SELECTION_SEED}:clip:<speaker_id>:<clip_path>")`; first 15 selected.

### Selected Population Totals:
- **Confirmatory Evaluation Speakers:** $1,100$ ($220 \times 5$ strata)
- **Gate-Reference Speakers:** $100$ ($20 \times 5$ strata)
- **Australian Replacement Reserve:** $65$ speakers (+21.3% buffer)
- **Total Unique Selected Speakers:** $1,265$ speakers
- **Clips per Speaker:** Exactly $15$ strictly qualifying clips (Predicate V1.5-Strict)
- **Total Selected Clips:** $18,975$ clips ($16,500$ evaluation, $1,500$ gate-reference, $975$ reserve)

---

## 6. Task F — Validation Summary

- **Speaker Counts:** Exactly $1,100$ evaluation, $100$ gate-reference, $65$ Australian reserve (**PASS**).
- **Panel Disjointness:** Zero overlap between evaluation, gate-reference, and reserve panels (**PASS**).
- **Historical Disjointness:** Zero overlap between selected speakers and 558 prior exposed speakers (**PASS**).
- **Clip Balance:** Exactly 15 clips per speaker across all 1,265 speakers (**PASS**).
- **ID Deduplication:** Exactly zero duplicate clip IDs or speaker IDs (**PASS**).
- **Provisional Manifest Hashes:**
  - JSON Manifest (`{man['json_filename']}`): `{man['json_sha256']}`
  - CSV Manifest (`{man['csv_filename']}`): `{man['csv_sha256']}`

---

## 7. Task H — Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Source audit, capacity reconciliation, and provisional manifest are COMPLETE.    ║
║  2. Audio downloading and physical validation are AUTHORIZED under controlled        ║
║     pipelines with bitwise SHA-256 verification.                                     ║
║  3. Confirmatory GPU CTTA adaptation and model inference remain STRICTLY BLOCKED     ║
║     under a separate execution gate pending final manifest locking.                  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Wrote audit report JSON: {json_path}")
    logger.info(f"Wrote audit report MD: {md_path}")
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(
        description="Stage 6M v1.5 Cohort 3 Source Audit & Provisional Manifest Curation"
    )
    parser.add_argument(
        "--val-tsv",
        type=Path,
        default=PROJECT_ROOT
        / "datasets"
        / "external"
        / "common_voice_27"
        / "validated.tsv",
        help="Path to validated.tsv",
    )
    parser.add_argument(
        "--splits-dir",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "splits",
        help="Path to datasets/splits directory",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "stage6m",
        help="Path to reports/stage6m directory",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SELECTION_SEED,
        help="Deterministic selection seed",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Stage 6M v1.5 — Cohort 3 Source Audit & Selection Manifest Utility")
    logger.info(f"Governing Standard: {GOVERNING_STANDARD}")
    logger.info("=" * 80)

    # Task B: Historical Exposure
    hist_files = {
        "stage5_external_eval.csv": args.splits_dir / "stage5_external_eval.csv",
        "stage5_sentinel_panel.csv": args.splits_dir / "stage5_sentinel_panel.csv",
        "stage6m_cohort2_audio.csv": args.splits_dir / "stage6m_cohort2_audio.csv",
    }
    all_prior, part_spks, part_prov = load_historical_speakers(hist_files)
    logger.info(
        f"Historical exposure verified: {len(all_prior)} unique speakers across 3 disjoint partitions."
    )

    # Task A & C: Source Identity & Capacity
    audit_meta, eligible_unexposed = audit_source_and_extract_eligible(
        args.val_tsv, all_prior
    )

    # Task D: Panel Selection
    manifest_metadata, selected_rows = select_cohort3_panels(
        eligible_unexposed, seed=args.seed
    )

    # Task F: Validation
    validation_res = validate_selected_manifest(
        manifest_metadata, selected_rows, all_prior
    )

    # Task E: Write Provisional Manifest
    json_path, csv_path, json_sha, csv_sha = write_manifest_files(
        manifest_metadata, selected_rows, args.splits_dir
    )

    # Task G: Generate Reports
    full_audit_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": PROTOCOL_VERSION,
        "governing_standard": GOVERNING_STANDARD,
        "governance_status": "AUTHORIZED_FOR_DATA_PREPARATION",
        "selection_seed": args.seed,
        "source_identity": audit_meta["source_provenance"],
        "historical_exposure": {
            "total_unique_exposed": len(all_prior),
            "partitions": part_prov,
        },
        "speaker_capacity": audit_meta["capacity_audit"],
        "panel_selection": manifest_metadata["panels_summary"],
        "validation": validation_res,
        "provisional_manifest": {
            "json_filename": json_path.name,
            "json_sha256": json_sha,
            "csv_filename": csv_path.name,
            "csv_sha256": csv_sha,
            "status": "UNLOCKED",
        },
    }

    json_rep, md_rep = generate_audit_reports(full_audit_data, args.reports_dir)

    print("\n" + "=" * 95)
    print("STAGE 6M v1.5 COHORT 3 SOURCE AUDIT & SELECTION MANIFEST SUMMARY")
    print("=" * 95)
    print(f"Source validated.tsv: {audit_meta['source_provenance']['bytes']:,} bytes | SHA-256: {audit_meta['source_provenance']['sha256']}")
    print(f"Historical Exposed Pool: {len(all_prior)} unique speakers (Cohort 1: 60, Sentinel: 30, Cohort 2: 468)")
    print(f"Historical Overlap: 0 speakers (100% disjoint)")
    print("-" * 95)
    for stratum in CONFIRMATORY_STRATA:
        ev = validation_res["strata_counts"][stratum]["evaluation"]
        gt = validation_res["strata_counts"][stratum]["gate_reference"]
        res = validation_res["strata_counts"][stratum].get("australian_reserve", 0)
        tot_avail = audit_meta["capacity_audit"][stratum]["unexposed_available_speakers"]
        print(f"  {stratum:<22}: Available={tot_avail:<5} | Eval={ev:<4} | Gate={gt:<3} | Reserve={res:<3}")
    print("-" * 95)
    print(f"Total Selected Speakers: {validation_res['speaker_counts']['total_selected']:,} (1,100 eval + 100 gate + 65 reserve)")
    print(f"Total Selected Clips:    {validation_res['clip_counts']['total_clips']:,} (15 clips/speaker)")
    print(f"Provisional Manifest JSON: {json_path} (SHA-256: {json_sha})")
    print(f"Provisional Manifest CSV:  {csv_path} (SHA-256: {csv_sha})")
    print(f"Audit Report MD:           {md_rep}")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    main()
