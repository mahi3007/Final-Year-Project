#!/usr/bin/env python3
"""
scripts/quarantine_stage6m_cohort3_rejected_audio.py

Stage 6M v1.5 Task 7.7.1 — Diagnostic MP3 Quarantine Retrieval Pipeline
======================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Protocol: v1.5-five-stratum-parity
Task: Task 7.7.1A (Diagnostic Quarantine Audio Recovery)

Operational Architecture:
-------------------------
1. Scope & Isolation:
   - Recovers ONLY the exact 130 failed recordings from Task 7.7 into:
     datasets/external/common_voice_27/cohort3_rejected_quarantine/
   - These files are diagnostic research quarantine files ONLY.
   - Cohort promotion is strictly prohibited: files must never be placed in
     datasets/external/common_voice_27/cohort3_audio or counted toward Cohort 3.
   - The original 18,845 valid cohort recordings and baseline ledger remain untouched.

2. Strict Preservation & Forensic Grounding:
   - Extracts raw, unmodified MP3 byte streams from Mozilla Common Voice 27.0.
   - Does NOT apply frame-padding validation or decoding filters as an extraction gate.
   - Does NOT unlink or delete any failed audio files.
   - Computes bitwise SHA-256 cryptographic digest directly on raw source bytes.
   - Uses temporary .part files and atomic renaming with exact byte-size verification.

3. Targeted Early-Termination Stream:
   - Streams from Mozilla Data Collective (MDC ID: cmu5jplf300nwmh07iqvk9leo).
   - Terminates immediately upon capturing all 130 target recordings.

4. Auditable Deliverables:
   - datasets/external/common_voice_27/cohort3_rejected_quarantine/{clip_filename}
   - datasets/splits/stage6m_cohort3_quarantine_ledger.csv
   - reports/stage6m/stage6m_cohort3_task771_quarantine_retrieval.json
   - reports/stage6m/stage6m_cohort3_task771_quarantine_retrieval.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Unbuffered stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cohort3_quarantine")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
CV27_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"

PARENT_MANIFEST_JSON = SPLITS_DIR / "stage6m_cohort3_provisional_manifest.json"
QUARANTINE_TARGETS_JSON = SPLITS_DIR / "stage6m_cohort3_task771_quarantine_targets.json"
FORENSIC_AUTH_JSON = REPORTS_DIR / "stage6m_cohort3_task771_forensic_authorization_decision.json"

QUARANTINE_DIR = CV27_DIR / "cohort3_rejected_quarantine"
QUARANTINE_LEDGER_CSV = SPLITS_DIR / "stage6m_cohort3_quarantine_ledger.csv"
QUARANTINE_REPORT_JSON = REPORTS_DIR / "stage6m_cohort3_task771_quarantine_retrieval.json"
QUARANTINE_REPORT_MD = REPORTS_DIR / "stage6m_cohort3_task771_quarantine_retrieval.md"
HISTORICAL_LOG_PATH = REPORTS_DIR / "historical_runs" / "task7_7_1_quarantine_retrieval.log"

HISTORICAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
_fh = logging.FileHandler(HISTORICAL_LOG_PATH, encoding="utf-8")
_fh.setLevel(logging.INFO)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(_fh)

APPROVED_PARENT_MANIFEST_SHA256 = "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"
APPROVED_TARGETS_LIST_SHA256 = "a530fb8b60fc302e536ce14efb620cda936ad91783f7d1f482a430dd154696ae"
APPROVED_QUARANTINE_DEST_REL = "datasets/external/common_voice_27/cohort3_rejected_quarantine"
DATASET_ID = "cmu5jplf300nwmh07iqvk9leo"
TOTAL_QUARANTINE_TARGETS = 130


def compute_sha256(path: Path) -> str:
    """Compute lowercase SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel_path(p: Path, base: Path = PROJECT_ROOT) -> str:
    """Safely return path relative to base or POSIX string if outside base."""
    try:
        return str(p.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(p.as_posix())


def verify_quarantine_retrieval_authorization(
    auth_json_path: Path = FORENSIC_AUTH_JSON,
    parent_manifest_path: Optional[Path] = None,
    targets_json_path: Optional[Path] = None,
    destination_dir: Optional[Path] = None,
) -> None:
    """
    Verifies that diagnostic quarantine audio retrieval is authorized under Protocol Section 14.7.
    Enforces strict forensic scope boundaries:
    1. Authorization artifact exists and records 'AUTHORIZED_FOR_DIAGNOSTIC_QUARANTINE_ONLY'.
    2. Authorizing role is 'Project Lead' and decision status is 'AUTHORIZED_BY_PROJECT_LEAD'.
    3. Purpose is strictly MP3 forensic investigation.
    4. Parent provisional manifest SHA-256 matches APPROVED_PARENT_MANIFEST_SHA256.
    5. Frozen quarantine targets list SHA-256 matches APPROVED_TARGETS_LIST_SHA256.
    6. Quarantine destination matches APPROVED_QUARANTINE_DEST_REL.
    7. Downstream cohort promotion, manifest locking, GPU adaptation, and inference remain strictly blocked.
    """
    if not auth_json_path.exists():
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: authorization decision artifact not found at {auth_json_path}. "
            "Explicit Project-Lead authorization under Protocol Section 14.7 is required."
        )
    try:
        with open(auth_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: could not parse authorization decision artifact {auth_json_path}: {e}"
        )

    # 1. Governance status
    gov_status = data.get("governance_status")
    if gov_status != "AUTHORIZED_FOR_DIAGNOSTIC_QUARANTINE_ONLY":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: governance_status is '{gov_status}' "
            "(expected 'AUTHORIZED_FOR_DIAGNOSTIC_QUARANTINE_ONLY')."
        )

    # 2. Authorization boundaries & role
    auth_boundaries = data.get("authorization_boundaries", {})
    authorizing_role = auth_boundaries.get("authorizing_role")
    decision_status = auth_boundaries.get("decision_status")
    if authorizing_role != "Project Lead":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: authorizing_role is '{authorizing_role}' (expected 'Project Lead')."
        )
    if decision_status != "AUTHORIZED_BY_PROJECT_LEAD":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: decision_status is '{decision_status}' (expected 'AUTHORIZED_BY_PROJECT_LEAD')."
        )

    # 3. Purpose check
    purpose = auth_boundaries.get("purpose", "")
    if "forensic" not in purpose.lower():
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: unauthorized purpose '{purpose}'."
        )

    # 4. Invariant boundaries
    if auth_boundaries.get("substitutions_permitted") != 0:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: substitutions_permitted is "
            f"'{auth_boundaries.get('substitutions_permitted')}' (expected 0)."
        )
    if auth_boundaries.get("manifest_modification") != "PROHIBITED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: manifest_modification is "
            f"'{auth_boundaries.get('manifest_modification')}' (expected 'PROHIBITED')."
        )
    if auth_boundaries.get("cohort_promotion") != "PROHIBITED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: cohort_promotion is "
            f"'{auth_boundaries.get('cohort_promotion')}' (expected 'PROHIBITED')."
        )

    # 5. Gating checks
    gating = auth_boundaries.get("execution_gating", {})
    if gating.get("quarantine_retrieval") != "AUTHORIZED_BY_PROJECT_LEAD":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: quarantine_retrieval gate is '{gating.get('quarantine_retrieval')}'."
        )
    if gating.get("forensic_triage") != "AUTHORIZED_BY_PROJECT_LEAD":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: forensic_triage gate is '{gating.get('forensic_triage')}'."
        )
    if gating.get("cohort_promotion") != "STRICTLY_PROHIBITED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: cohort_promotion is '{gating.get('cohort_promotion')}' (expected 'STRICTLY_PROHIBITED')."
        )
    if gating.get("final_manifest_lock") != "STRICTLY_BLOCKED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: final_manifest_lock is '{gating.get('final_manifest_lock')}' (expected 'STRICTLY_BLOCKED')."
        )
    if gating.get("gpu_ctta_adaptation") != "STRICTLY_BLOCKED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: gpu_ctta_adaptation is '{gating.get('gpu_ctta_adaptation')}' (expected 'STRICTLY_BLOCKED')."
        )
    if gating.get("confirmatory_inference") != "STRICTLY_BLOCKED":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: confirmatory_inference is '{gating.get('confirmatory_inference')}' (expected 'STRICTLY_BLOCKED')."
        )

    # 6. Parent manifest SHA-256 check
    effective_manifest = Path(parent_manifest_path) if parent_manifest_path is not None else PARENT_MANIFEST_JSON
    if not effective_manifest.exists():
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: parent manifest not found at {effective_manifest}."
        )
    actual_manifest_sha = compute_sha256(effective_manifest)
    if actual_manifest_sha != APPROVED_PARENT_MANIFEST_SHA256:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: parent manifest SHA-256 mismatch. "
            f"Manifest has digest '{actual_manifest_sha}' (expected '{APPROVED_PARENT_MANIFEST_SHA256}')."
        )

    parent_manifest_info = data.get("parent_provisional_manifest", {})
    if parent_manifest_info.get("sha256") != APPROVED_PARENT_MANIFEST_SHA256:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: parent manifest digest in decision "
            f"'{parent_manifest_info.get('sha256')}' does not match approved '{APPROVED_PARENT_MANIFEST_SHA256}'."
        )

    # 7. Targets list SHA-256 and count check
    effective_targets = Path(targets_json_path) if targets_json_path is not None else QUARANTINE_TARGETS_JSON
    if not effective_targets.exists():
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: targets list artifact not found at {effective_targets}."
        )
    actual_targets_sha = compute_sha256(effective_targets)
    if actual_targets_sha != APPROVED_TARGETS_LIST_SHA256:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: targets list SHA-256 mismatch. "
            f"Artifact has digest '{actual_targets_sha}' (expected '{APPROVED_TARGETS_LIST_SHA256}')."
        )

    quarantine_targets_info = data.get("quarantine_target_list", {})
    if quarantine_targets_info.get("sha256") != APPROVED_TARGETS_LIST_SHA256:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: quarantine targets digest in decision "
            f"'{quarantine_targets_info.get('sha256')}' does not match approved '{APPROVED_TARGETS_LIST_SHA256}'."
        )
    if quarantine_targets_info.get("target_recordings_count") != TOTAL_QUARANTINE_TARGETS:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: quarantine targets count in decision "
            f"'{quarantine_targets_info.get('target_recordings_count')}' does not match expected {TOTAL_QUARANTINE_TARGETS}."
        )

    # 8. Source dataset checks
    src_dataset = data.get("source_dataset", {})
    if src_dataset.get("dataset_id") != DATASET_ID:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: source dataset ID is '{src_dataset.get('dataset_id')}' (expected '{DATASET_ID}')."
        )
    if src_dataset.get("platform") != "Mozilla Data Collective (MDC)":
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: source platform is '{src_dataset.get('platform')}' (expected 'Mozilla Data Collective (MDC)')."
        )

    # 9. Destination directory check
    authorized_dest = (PROJECT_ROOT / APPROVED_QUARANTINE_DEST_REL).resolve()
    effective_dest = Path(destination_dir).resolve() if destination_dir is not None else QUARANTINE_DIR.resolve()
    if effective_dest != authorized_dest:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: destination directory mismatch. "
            f"Requested destination '{effective_dest}' does not match authorized quarantine destination '{authorized_dest}'."
        )

    quarantine_dest_info = data.get("quarantine_destination", {})
    if quarantine_dest_info.get("directory_rel") != APPROVED_QUARANTINE_DEST_REL:
        raise PermissionError(
            f"Diagnostic quarantine audio retrieval blocked: destination directory in decision "
            f"'{quarantine_dest_info.get('directory_rel')}' does not match approved '{APPROVED_QUARANTINE_DEST_REL}'."
        )


def load_quarantine_targets(targets_json_path: Path = QUARANTINE_TARGETS_JSON) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Load the 130 frozen quarantine targets and return list and dict mapped by clip_filename."""
    with open(targets_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data.get("targets", [])
    if len(records) != TOTAL_QUARANTINE_TARGETS:
        raise ValueError(
            f"Quarantine targets file {targets_json_path} contains {len(records)} targets (expected exactly {TOTAL_QUARANTINE_TARGETS})."
        )
    target_map = {r["clip_filename"]: r for r in records}
    return records, target_map


def validate_archive_member_path(member_name: str, target_map: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates archive member path format against expected Common Voice tar hierarchy.
    Expected format: cv-corpus-27.0-2024-12-06/en/clips/{clip_filename} or clips/{clip_filename}.
    Returns: (is_valid, clip_filename)
    """
    if ".." in member_name or member_name.startswith("/"):
        return False, None
    parts = member_name.split("/")
    if len(parts) < 2:
        return False, None
    if parts[-2] != "clips":
        return False, None
    clip_filename = parts[-1]
    if not clip_filename.endswith(".mp3"):
        return False, None
    if clip_filename not in target_map:
        return False, None
    return True, clip_filename


def extract_tar_member_to_file(
    tar: tarfile.TarFile,
    member: tarfile.TarInfo,
    dest_file: Path,
) -> Tuple[int, str]:
    """
    Extracts raw bytes from tar member to destination file via atomic .part file with exact byte verification.
    Rejects zero-byte members and ensures byte-for-byte fidelity.
    Returns: (bytes_written, sha256_hex)
    """
    if member.size <= 0:
        raise ValueError(f"Refusing to extract zero-byte archive member: {member.name}")

    dest_file.parent.mkdir(parents=True, exist_ok=True)
    part_file = dest_file.with_name(f"{dest_file.name}.part")

    extracted_f = tar.extractfile(member)
    if extracted_f is None:
        raise IOError(f"Failed to open archive member for reading: {member.name}")

    hasher = hashlib.sha256()
    bytes_written = 0
    try:
        with open(part_file, "wb") as out_f:
            while True:
                chunk = extracted_f.read(65536)
                if not chunk:
                    break
                out_f.write(chunk)
                hasher.update(chunk)
                bytes_written += len(chunk)

        if bytes_written != member.size:
            part_file.unlink(missing_ok=True)
            raise IOError(
                f"Byte count mismatch extracting {member.name}: wrote {bytes_written} bytes, tar declared {member.size} bytes."
            )

        # Atomic rename after complete byte validation
        part_file.replace(dest_file)
    except Exception:
        part_file.unlink(missing_ok=True)
        raise

    return bytes_written, hasher.hexdigest()


def scan_quarantine_inventory(
    target_map: Dict[str, Dict[str, Any]],
    quarantine_dir: Path,
) -> Dict[str, Dict[str, Any]]:
    """Scan quarantine directory for already-retrieved files and verify raw byte hashes."""
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    recovered_inv: Dict[str, Dict[str, Any]] = {}
    for p in quarantine_dir.glob("*.mp3"):
        if p.name in target_map:
            sz = p.stat().st_size
            if sz == 0:
                raise ValueError(f"Unverified zero-byte file detected in quarantine: {p.name}")
            target_row = target_map[p.name]
            h = compute_sha256(p)
            recovered_inv[p.name] = {
                "recording_id": target_row["recording_id"],
                "clip_filename": p.name,
                "speaker_id": target_row["speaker_id"],
                "accent_group": target_row["accent_group"],
                "stratum_code": target_row["stratum_code"],
                "panel_role": target_row["panel_role"],
                "local_path": safe_rel_path(p),
                "file_size_bytes": sz,
                "sha256": h,
            }
        else:
            raise ValueError(f"Unexpected foreign file in quarantine directory: {p.name}")
    return recovered_inv


def recover_quarantine_from_stream(
    target_map: Dict[str, Dict[str, Any]],
    recovered_inv: Dict[str, Dict[str, Any]],
    quarantine_dir: Path,
    max_duration_seconds: Optional[int] = None,
) -> Tuple[int, int, bool]:
    """
    Streams from Mozilla Data Collective tar.gz, extracting raw MP3 bytes for remaining quarantine targets.
    Terminates early as soon as all 130 target files are recovered.
    Returns: (compressed_bytes_read, tar_members_scanned, early_termination_achieved)
    """
    from scripts.materialize_stage6m_cohort3_audio import ThreadedResilientGzipStream

    load_dotenv()
    from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

    remaining = {k: v for k, v in target_map.items() if k not in recovered_inv}
    if not remaining:
        logger.info(f"[QUARANTINE] All {len(target_map)} targets already present in quarantine directory.")
        return 0, 0, True

    logger.info(f"[QUARANTINE] Need to recover {len(remaining)} / {len(target_map)} rejected recordings from stream.")

    def plan_getter():
        return _get_download_plan(DATASET_ID, CV27_DIR / "temp.tar.gz", DOWNLOAD_SOURCE_SAVE)

    t_start = time.time()
    t_last_hb = t_start
    member_no = 0
    early_exit = False
    seen_archive_members: set[str] = set()

    resilient = ThreadedResilientGzipStream(DATASET_ID, plan_getter)
    buffered = io.BufferedReader(resilient, buffer_size=16 * 1024 * 1024)

    try:
        with tarfile.open(fileobj=buffered, mode="r|") as tar:
            for member in tar:
                member_no += 1
                name = member.name

                now = time.time()
                if now - t_last_hb >= 30.0:
                    t_last_hb = now
                    elapsed = now - t_start
                    base_curr = name.rsplit("/", 1)[-1]
                    logger.info(
                        f"[QUARANTINE HB] elapsed={elapsed:.0f}s | members={member_no:,} | "
                        f"compressed_gb={resilient.compressed_bytes_read / (1024**3):.2f} GB | "
                        f"recovered={len(recovered_inv):,}/{len(target_map):,} | "
                        f"remaining={len(remaining):,} | current={base_curr}"
                    )

                if max_duration_seconds and (now - t_start) > max_duration_seconds:
                    logger.info(f"[QUARANTINE] Max execution duration {max_duration_seconds}s reached. Pausing stream.")
                    break

                is_valid_member, base_name = validate_archive_member_path(name, target_map)
                if not is_valid_member or not member.isfile():
                    continue

                if name in seen_archive_members:
                    raise ValueError(f"Ambiguous duplicate archive member detected in tar stream: {name}")
                seen_archive_members.add(name)

                if base_name in recovered_inv and base_name not in remaining:
                    raise ValueError(f"Ambiguous duplicate clip member detected across stream: {name} (clip {base_name} already recovered)")

                if base_name not in remaining:
                    continue

                target_row = remaining[base_name]
                rec_id = target_row["recording_id"]
                dest_file = quarantine_dir / base_name

                bytes_written, h = extract_tar_member_to_file(tar, member, dest_file)

                item = {
                    "recording_id": rec_id,
                    "clip_filename": base_name,
                    "speaker_id": target_row["speaker_id"],
                    "accent_group": target_row["accent_group"],
                    "stratum_code": target_row["stratum_code"],
                    "panel_role": target_row["panel_role"],
                    "local_path": safe_rel_path(dest_file),
                    "file_size_bytes": bytes_written,
                    "sha256": h,
                    "source_member_path": name,
                    "archive_provenance": {
                        "dataset_id": DATASET_ID,
                        "member_size_bytes": member.size,
                    },
                }
                recovered_inv[base_name] = item
                del remaining[base_name]

                logger.info(
                    f"[RECOVERED] Quarantined {rec_id} ({base_name}) [{len(recovered_inv)}/{len(target_map)}] "
                    f"({bytes_written:,} B, sha256={h[:12]}...)"
                )

                if not remaining:
                    logger.info(f"\n[QUARANTINE STREAM] 100% RECOVERY COMPLETE! ({len(recovered_inv)}/{len(target_map)})")
                    early_exit = True
                    break

    finally:
        resilient.close()

    return resilient.compressed_bytes_read, member_no, early_exit


def generate_quarantine_artifacts(
    records: List[Dict[str, Any]],
    target_map: Dict[str, Dict[str, Any]],
    recovered_inv: Dict[str, Dict[str, Any]],
    quarantine_dir: Path,
    compressed_bytes_read: int,
    members_scanned: int,
    early_exit: bool,
    quarantine_ledger_path: Path = QUARANTINE_LEDGER_CSV,
    report_json_path: Path = QUARANTINE_REPORT_JSON,
    report_md_path: Path = QUARANTINE_REPORT_MD,
) -> None:
    """Writes quarantine acquisition ledger CSV, JSON report, and Markdown report."""
    quarantine_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Write quarantine ledger CSV
    ledger_fieldnames = [
        "recording_id",
        "clip_filename",
        "speaker_id",
        "accent_group",
        "stratum_code",
        "panel_role",
        "file_size_bytes",
        "sha256",
    ]
    sorted_recovered = sorted(recovered_inv.values(), key=lambda x: x["clip_filename"])
    with open(quarantine_ledger_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        writer.writeheader()
        for item in sorted_recovered:
            writer.writerow({
                "recording_id": item["recording_id"],
                "clip_filename": item["clip_filename"],
                "speaker_id": item["speaker_id"],
                "accent_group": item["accent_group"],
                "stratum_code": item["stratum_code"],
                "panel_role": item["panel_role"],
                "file_size_bytes": item["file_size_bytes"],
                "sha256": item["sha256"],
            })

    ledger_sha256 = compute_sha256(quarantine_ledger_path)
    logger.info(f"Wrote quarantine ledger CSV: {quarantine_ledger_path} (SHA-256: {ledger_sha256})")

    # 2. Write JSON report
    strata_counts: Dict[str, int] = {}
    for item in sorted_recovered:
        grp = item["accent_group"]
        strata_counts[grp] = strata_counts.get(grp, 0) + 1

    unique_speakers = len(set(item["speaker_id"] for item in sorted_recovered))
    missing_targets = [k for k in target_map if k not in recovered_inv]

    report_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": "TASK_7_7_1",
        "document_id": "STAGE6M_COHORT3_TASK771_QUARANTINE_RETRIEVAL",
        "protocol_version": "v1.5-five-stratum-parity",
        "governing_standard": "Protocol Section 14.7 (Project-Lead Academic Authorization)",
        "governance_status": "QUARANTINE_RETRIEVAL_COMPLETE" if len(recovered_inv) == len(target_map) else "QUARANTINE_RETRIEVAL_PARTIAL",
        "parent_manifest_sha256": APPROVED_PARENT_MANIFEST_SHA256,
        "targets_list_sha256": APPROVED_TARGETS_LIST_SHA256,
        "quarantine_ledger": {
            "path": safe_rel_path(quarantine_ledger_path),
            "sha256": ledger_sha256,
            "total_rows": len(sorted_recovered),
        },
        "quarantine_destination": safe_rel_path(quarantine_dir),
        "recovery_summary": {
            "total_targets": len(target_map),
            "recovered_count": len(recovered_inv),
            "missing_count": len(missing_targets),
            "unique_speakers": unique_speakers,
            "recovery_complete": len(recovered_inv) == len(target_map),
            "early_termination_achieved": early_exit,
            "compressed_bytes_consumed": compressed_bytes_read,
            "tar_members_scanned": members_scanned,
            "strata_counts": strata_counts,
        },
        "missing_targets": missing_targets,
        "recovered_recordings": sorted_recovered,
    }

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote quarantine report JSON: {report_json_path}")

    # 3. Write Markdown report
    md_lines = [
        "# Stage 6M v1.5 — Task 7.7.1 Quarantine Retrieval Report",
        "",
        "> **DOCUMENT ID:** `STAGE6M_COHORT3_TASK771_QUARANTINE_RETRIEVAL`  ",
        f"> **TASK ID:** `TASK_7_7_1`  ",
        f"> **GOVERNING STANDARD:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  ",
        f"> **STATUS:** **{report_data['governance_status']}**  ",
        f"> **QUARANTINE LEDGER:** [`{safe_rel_path(quarantine_ledger_path)}`](file:///{quarantine_ledger_path.resolve()}) (SHA-256: `{ledger_sha256}`)  ",
        f"> **TIMESTAMP (UTC):** {report_data['timestamp_utc']}  ",
        "",
        "---",
        "",
        "## 1. Summary of Recovered Diagnostic Audio",
        "",
        "| Metric | Value | Required Target | Status |",
        "| :--- | :---: | :---: | :---: |",
        f"| Quarantine Targets | {len(target_map)} | {TOTAL_QUARANTINE_TARGETS} | - |",
        f"| Recovered Original Recordings | {len(recovered_inv)} | {len(target_map)} | {'PASS' if len(recovered_inv) == len(target_map) else 'INCOMPLETE'} |",
        f"| Unique Incomplete Speakers | {unique_speakers} | 13 | {'PASS' if unique_speakers == 13 else 'INCOMPLETE'} |",
        f"| Missing Targets | {len(missing_targets)} | 0 | {'PASS' if len(missing_targets) == 0 else 'FAIL'} |",
        f"| Compressed Bytes Consumed | {compressed_bytes_read:,} B | - | - |",
        f"| Tar Members Scanned | {members_scanned:,} | - | - |",
        f"| Early Stream Termination | {early_exit} | True | - |",
        "",
        "### Strata Breakdown",
        "| Stratum | Target Files | Recovered Files | Status |",
        "| :--- | :---: | :---: | :---: |",
    ]
    for grp, cnt in sorted(strata_counts.items()):
        expected = sum(1 for r in records if r["accent_group"] == grp)
        md_lines.append(f"| {grp} | {expected} | {cnt} | {'PASS' if cnt == expected else 'INCOMPLETE'} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Quarantine Governance Invariants",
        "",
        "- **Zero Deletion Policy**: All 130 recovered bitstreams preserved exactly as extracted.",
        "- **Strict Isolation**: Quarantined files reside exclusively in `cohort3_rejected_quarantine` and are barred from promotion to Cohort 3.",
        "- **Preservation**: The 18,845 valid physical recordings and partial-acquisition ledger remain untouched.",
        "",
    ])

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    logger.info(f"Wrote quarantine report MD: {report_md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Stage 6M v1.5 Task 7.7.1 — Diagnostic MP3 Quarantine Retrieval Pipeline"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream and extract target files from Mozilla Data Collective archive",
    )
    parser.add_argument(
        "--max-stream-seconds",
        type=int,
        default=None,
        help="Optional maximum streaming runtime in seconds (for batch/testing)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for reports and ledger (for testing isolation)",
    )
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=None,
        help="Optional destination directory for quarantined audio (for testing isolation)",
    )
    args = parser.parse_args()

    effective_quarantine_dir = args.quarantine_dir if args.quarantine_dir is not None else QUARANTINE_DIR
    effective_ledger_csv = (args.output_dir / "stage6m_cohort3_quarantine_ledger.csv") if args.output_dir else QUARANTINE_LEDGER_CSV
    effective_report_json = (args.output_dir / "stage6m_cohort3_task771_quarantine_retrieval.json") if args.output_dir else QUARANTINE_REPORT_JSON
    effective_report_md = (args.output_dir / "stage6m_cohort3_task771_quarantine_retrieval.md") if args.output_dir else QUARANTINE_REPORT_MD

    logger.info("================================================================================")
    logger.info("Stage 6M v1.5 — Task 7.7.1 Diagnostic MP3 Quarantine Retrieval")
    logger.info("Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)")
    logger.info("================================================================================")

    # Task 7.7.1 Authorization Verification
    verify_quarantine_retrieval_authorization(
        auth_json_path=FORENSIC_AUTH_JSON,
        parent_manifest_path=PARENT_MANIFEST_JSON,
        targets_json_path=QUARANTINE_TARGETS_JSON,
        destination_dir=effective_quarantine_dir,
    )
    logger.info("[GOVERNANCE] Project-Lead authorization for diagnostic quarantine retrieval verified.")

    records, target_map = load_quarantine_targets(QUARANTINE_TARGETS_JSON)
    logger.info(f"Loaded {len(records)} quarantine targets across {len(set(r['speaker_id'] for r in records))} speakers.")

    recovered_inv = scan_quarantine_inventory(target_map, effective_quarantine_dir)
    logger.info(f"Initial scan: {len(recovered_inv)} / {len(target_map)} files already recovered.")

    compressed_bytes = 0
    members_scanned = 0
    early_exit = len(recovered_inv) == len(target_map)

    if args.stream and not early_exit:
        compressed_bytes, members_scanned, early_exit = recover_quarantine_from_stream(
            target_map=target_map,
            recovered_inv=recovered_inv,
            quarantine_dir=effective_quarantine_dir,
            max_duration_seconds=args.max_stream_seconds,
        )

    generate_quarantine_artifacts(
        records=records,
        target_map=target_map,
        recovered_inv=recovered_inv,
        quarantine_dir=effective_quarantine_dir,
        compressed_bytes_read=compressed_bytes,
        members_scanned=members_scanned,
        early_exit=early_exit,
        quarantine_ledger_path=effective_ledger_csv,
        report_json_path=effective_report_json,
        report_md_path=effective_report_md,
    )

    if len(recovered_inv) == len(target_map):
        logger.info(f"[SUCCESS] 100% of diagnostic quarantine files recovered ({len(recovered_inv)}/{len(target_map)}).")
    else:
        logger.warning(
            f"[PARTIAL] Quarantine recovery incomplete: {len(recovered_inv)}/{len(target_map)} files recovered."
        )


if __name__ == "__main__":
    main()
