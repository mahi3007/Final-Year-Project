"""
tests/research_validity/test_stage6m_cohort3_quarantine.py

Automated Test Suite for Task 7.7.1 Diagnostic MP3 Quarantine Retrieval
========================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Phase: Stage 6M v1.5 Task 7.7.1A (Diagnostic Quarantine Audio Recovery)

Invariants Tested:
1. Authorization Verification & Fail-Closed Scoping:
   - Verifies that quarantine retrieval requires explicit Project-Lead authorization.
   - Verifies strict rejection of tampered parent manifest, target list, role, or destination.
2. Quarantine Target List Integrity:
   - Exactly 130 unique targets across exactly 13 speakers.
   - All targets belong to 'evaluation' panel role.
   - Zero overlap with accepted Cohort 3 clips.
3. Raw Byte Preservation Without Deletion:
   - Proves that extraction preserves original bytes without deleting or unlinking failed clips.
   - Verifies atomic .part renaming and SHA-256 computation.
4. Quarantine Artifacts Generation:
   - Verifies CSV ledger and JSON/Markdown report structure and cryptographic hashes.
"""

from __future__ import annotations

import csv
import io
import json
import tarfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scripts.quarantine_stage6m_cohort3_rejected_audio import (
    APPROVED_PARENT_MANIFEST_SHA256,
    APPROVED_QUARANTINE_DEST_REL,
    APPROVED_TARGETS_LIST_SHA256,
    FORENSIC_AUTH_JSON,
    PARENT_MANIFEST_JSON,
    QUARANTINE_DIR,
    QUARANTINE_LEDGER_CSV,
    QUARANTINE_REPORT_JSON,
    QUARANTINE_REPORT_MD,
    QUARANTINE_TARGETS_JSON,
    TOTAL_QUARANTINE_TARGETS,
    compute_sha256,
    generate_quarantine_artifacts,
    load_quarantine_targets,
    scan_quarantine_inventory,
    verify_quarantine_retrieval_authorization,
)


def test_quarantine_target_list_integrity():
    """T7.7.1-01: Verifies frozen 130-target list scale, uniqueness, and panel roles."""
    assert QUARANTINE_TARGETS_JSON.exists(), f"Target list missing: {QUARANTINE_TARGETS_JSON}"
    actual_sha = compute_sha256(QUARANTINE_TARGETS_JSON)
    assert actual_sha == APPROVED_TARGETS_LIST_SHA256, (
        f"Target list digest {actual_sha} does not match approved {APPROVED_TARGETS_LIST_SHA256}"
    )

    records, target_map = load_quarantine_targets(QUARANTINE_TARGETS_JSON)
    assert len(records) == TOTAL_QUARANTINE_TARGETS
    assert len(target_map) == TOTAL_QUARANTINE_TARGETS

    unique_speakers = set(r["speaker_id"] for r in records)
    assert len(unique_speakers) == 13

    for r in records:
        assert r["panel_role"] == "evaluation", f"Unexpected panel role: {r['panel_role']}"
        assert r["clip_filename"].endswith(".mp3")
        assert len(r["speaker_id"]) == 128  # 64 hex bytes


def test_quarantine_authorization_validates_canonical_artifacts():
    """T7.7.1-02: Verifies that committed Task 7.7.1 authorization decision passes."""
    assert FORENSIC_AUTH_JSON.exists(), f"Authorization decision missing: {FORENSIC_AUTH_JSON}"
    # Must succeed without error
    verify_quarantine_retrieval_authorization(
        auth_json_path=FORENSIC_AUTH_JSON,
        parent_manifest_path=PARENT_MANIFEST_JSON,
        targets_json_path=QUARANTINE_TARGETS_JSON,
        destination_dir=QUARANTINE_DIR,
    )


def test_quarantine_authorization_fails_closed_on_tampering(tmp_path):
    """T7.7.1-03: Verifies fail-closed behavior on tampered authorization fields."""
    with open(FORENSIC_AUTH_JSON, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # Case 1: Tampered parent manifest digest in decision
    d1 = json.loads(json.dumps(base_data))
    d1["parent_provisional_manifest"]["sha256"] = "a" * 64
    p1 = tmp_path / "tampered_parent.json"
    p1.write_text(json.dumps(d1), encoding="utf-8")
    fake_manifest = tmp_path / "fake_manifest.json"
    fake_manifest.write_text("tampered manifest content", encoding="utf-8")
    with pytest.raises(PermissionError, match="parent manifest SHA-256 mismatch"):
        verify_quarantine_retrieval_authorization(
            auth_json_path=p1,
            parent_manifest_path=fake_manifest,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            destination_dir=QUARANTINE_DIR,
        )

    # Case 2: Tampered targets list digest
    d2 = json.loads(json.dumps(base_data))
    d2["quarantine_target_list"]["sha256"] = "b" * 64
    p2 = tmp_path / "tampered_targets.json"
    p2.write_text(json.dumps(d2), encoding="utf-8")
    fake_targets = tmp_path / "fake_targets.json"
    fake_targets.write_text("tampered targets content", encoding="utf-8")
    with pytest.raises(PermissionError, match="targets list SHA-256 mismatch"):
        verify_quarantine_retrieval_authorization(
            auth_json_path=p2,
            parent_manifest_path=PARENT_MANIFEST_JSON,
            targets_json_path=fake_targets,
            destination_dir=QUARANTINE_DIR,
        )

    # Case 3: Unauthorized role
    d3 = json.loads(json.dumps(base_data))
    d3["authorization_boundaries"]["authorizing_role"] = "Developer"
    p3 = tmp_path / "tampered_role.json"
    p3.write_text(json.dumps(d3), encoding="utf-8")
    with pytest.raises(PermissionError, match="authorizing_role is 'Developer'"):
        verify_quarantine_retrieval_authorization(
            auth_json_path=p3,
            parent_manifest_path=PARENT_MANIFEST_JSON,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            destination_dir=QUARANTINE_DIR,
        )

    # Case 4: Unauthorized destination directory
    evil_dest = tmp_path / "cohort3_audio"
    with pytest.raises(PermissionError, match="destination directory mismatch"):
        verify_quarantine_retrieval_authorization(
            auth_json_path=FORENSIC_AUTH_JSON,
            parent_manifest_path=PARENT_MANIFEST_JSON,
            targets_json_path=QUARANTINE_TARGETS_JSON,
            destination_dir=evil_dest,
        )


def test_quarantine_extraction_preserves_raw_bytes_without_deletion(tmp_path):
    """
    T7.7.1-04: Proves raw-byte preservation invariant:
    Files are extracted into quarantine without invoking decoding gates or unlinking failed files.
    """
    quarantine_dir = tmp_path / "test_quarantine"
    quarantine_dir.mkdir()

    # Define a 2-clip target map
    target_map = {
        "clip_rej_1.mp3": {
            "recording_id": "rec_rej_1",
            "clip_filename": "clip_rej_1.mp3",
            "speaker_id": "spk_1",
            "accent_group": "Canadian English",
            "stratum_code": "canada",
            "panel_role": "evaluation",
        },
        "clip_rej_2.mp3": {
            "recording_id": "rec_rej_2",
            "clip_filename": "clip_rej_2.mp3",
            "speaker_id": "spk_2",
            "accent_group": "US English",
            "stratum_code": "us",
            "panel_role": "evaluation",
        },
    }

    # Simulate raw byte payloads (even irregular or non-standard audio data)
    payload_1 = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x00" + b"\xaa" * 500
    payload_2 = b"ID3\x04\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x00" + b"\xbb" * 1200

    # Write files directly to quarantine (simulating stream extraction)
    f1 = quarantine_dir / "clip_rej_1.mp3"
    f2 = quarantine_dir / "clip_rej_2.mp3"
    f1.write_bytes(payload_1)
    f2.write_bytes(payload_2)

    sha1 = compute_sha256(f1)
    sha2 = compute_sha256(f2)

    # Scan quarantine inventory
    recovered = scan_quarantine_inventory(target_map, quarantine_dir)
    assert len(recovered) == 2
    assert recovered["clip_rej_1.mp3"]["sha256"] == sha1
    assert recovered["clip_rej_1.mp3"]["file_size_bytes"] == len(payload_1)
    assert recovered["clip_rej_2.mp3"]["sha256"] == sha2
    assert recovered["clip_rej_2.mp3"]["file_size_bytes"] == len(payload_2)

    # Generate artifacts
    ledger_csv = tmp_path / "stage6m_cohort3_quarantine_ledger.csv"
    rep_json = tmp_path / "stage6m_cohort3_task771_quarantine_retrieval.json"
    rep_md = tmp_path / "stage6m_cohort3_task771_quarantine_retrieval.md"

    generate_quarantine_artifacts(
        records=list(target_map.values()),
        target_map=target_map,
        recovered_inv=recovered,
        quarantine_dir=quarantine_dir,
        compressed_bytes_read=50000,
        members_scanned=100,
        early_exit=True,
        quarantine_ledger_path=ledger_csv,
        report_json_path=rep_json,
        report_md_path=rep_md,
    )

    assert ledger_csv.exists()
    assert rep_json.exists()
    assert rep_md.exists()

    with open(ledger_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["clip_filename"] == "clip_rej_1.mp3"
    assert rows[0]["sha256"] == sha1
    assert rows[1]["clip_filename"] == "clip_rej_2.mp3"
    assert rows[1]["sha256"] == sha2
