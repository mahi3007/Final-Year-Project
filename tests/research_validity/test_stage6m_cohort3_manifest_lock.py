"""
tests/research_validity/test_stage6m_cohort3_manifest_lock.py

Research-validity test suite for Stage 6M Gate 3B Manifest Validation and Lock.
==============================================================================
Validates:
1. Locked production manifest existence, integrity, and locked status.
2. Cryptographic external SHA-256 digest agreement.
3. Candidate manifest version preservation chain (v1, v2, v3).
4. Decoupled Claim A and Claim B field semantics across all 18,975 records.
5. Invariant speaker accounting: 1,265 speakers x 15 clips = 18,975 recordings.
6. Five strata balance (220 eval speakers each = 1,100 eval speakers).
7. Zero overlap across evaluation, gate-reference, and reserve panels.
8. Physical asset and disposition ledger reconciliation.
9. Provisional manifest immutability.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"
DEST_AUDIO_DIR = PROJECT_ROOT / "datasets" / "audio" / "stage6m" / "cohort3_reconciled_assets"
CANDIDATE_DIR = PROJECT_ROOT / "scratch" / "candidate_manifest"

FINAL_MANIFEST_PATH = SPLITS_DIR / "stage6m_cohort3_final_manifest.json"
EXPECTED_FINAL_MANIFEST_SHA256 = "171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0"
EXPECTED_FINAL_MANIFEST_BYTES = 26680115

CANDIDATE_V1_PATH = CANDIDATE_DIR / "stage6m_cohort3_candidate_final_manifest_v1_legacy_claim_b.json"
EXPECTED_CANDIDATE_V1_SHA256 = "44747c12297a257bfeb7da496e34b8d1d04c44c595b3a639695ac293581bb117"

CANDIDATE_V2_PATH = CANDIDATE_DIR / "stage6m_cohort3_candidate_final_manifest_v2_unverified_boolean_only.json"
EXPECTED_CANDIDATE_V2_SHA256 = "718426757691c88b56e6371c425e6fbd1c757d9f42c648d1cc09d3182e84256e"

CANDIDATE_V3_PATH = CANDIDATE_DIR / "stage6m_cohort3_candidate_final_manifest.json"
EXPECTED_CANDIDATE_V3_SHA256 = "c09edaf82d62645293b51d70152b326008f42832a21fbdd765ef2218c4f0fb89"

PROV_MANIFEST_PATH = SPLITS_DIR / "stage6m_cohort3_provisional_manifest.json"
EXPECTED_PROV_SHA256 = "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"

LEDGER_PATH = SPLITS_DIR / "stage6m_cohort3_materialization_disposition_ledger.csv"
LOCK_AUDIT_JSON = REPORTS_DIR / "stage6m_gate3b_lock_audit_report.json"
AUTH_RECORD_JSON = REPORTS_DIR / "stage6m_gate3b_authorization_record.json"


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def locked_manifest_data():
    assert FINAL_MANIFEST_PATH.exists(), f"Final manifest missing: {FINAL_MANIFEST_PATH}"
    with open(FINAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_gate3b_final_manifest_existence_and_digest():
    """Verify final locked manifest exists and matches registered SHA-256 and byte size."""
    assert FINAL_MANIFEST_PATH.exists()
    assert FINAL_MANIFEST_PATH.stat().st_size == EXPECTED_FINAL_MANIFEST_BYTES
    actual_sha256 = _compute_sha256(FINAL_MANIFEST_PATH)
    assert actual_sha256 == EXPECTED_FINAL_MANIFEST_SHA256


def test_gate3b_candidate_version_chain_preserved():
    """Verify candidate manifest versions v1, v2, and v3 are preserved with exact digests."""
    assert CANDIDATE_V1_PATH.exists()
    assert _compute_sha256(CANDIDATE_V1_PATH) == EXPECTED_CANDIDATE_V1_SHA256

    assert CANDIDATE_V2_PATH.exists()
    assert _compute_sha256(CANDIDATE_V2_PATH) == EXPECTED_CANDIDATE_V2_SHA256

    assert CANDIDATE_V3_PATH.exists()
    assert _compute_sha256(CANDIDATE_V3_PATH) == EXPECTED_CANDIDATE_V3_SHA256


def test_gate3b_manifest_header_and_governance_metadata(locked_manifest_data):
    """Verify locked manifest header status, authority, and lack of self-referential hash."""
    meta = locked_manifest_data["metadata"]
    assert meta["manifest_type"] == "FINAL_RECONCILED_COHORT_MANIFEST"
    assert meta["manifest_status"] == "LOCKED"
    assert meta["lock_authority"] == "Project Lead (Dissertation Author)"
    assert meta["governing_policy"] == "Policy 2A (Reconciled Target Population Admission)"
    assert meta["candidate_sha256"] == EXPECTED_CANDIDATE_V3_SHA256
    # Ensure manifest does not circularly embed its own final SHA-256
    assert "manifest_sha256" not in meta


def test_gate3b_claim_a_and_claim_b_semantics(locked_manifest_data):
    """Verify decoupled Claim A and Claim B semantics across all 18,975 records."""
    records = locked_manifest_data["records"]
    assert len(records) == 18975

    accepted_count = 0
    quarantined_count = 0

    for r in records:
        assert r["current_file_structural_validity_passed"] is True
        assert r["decoder_validation_passed"] is True
        assert r["source_origin_completeness_verified"] is False
        assert r["source_origin_completeness_status"] == "UNVERIFIED"
        assert r["policy_2a_admitted"] is True

        disp = r["admission_disposition"]
        discrep = r["duration_estimation_discrepancy"]
        if disp == "ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED":
            assert discrep is False
            accepted_count += 1
        elif disp == "ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY":
            assert discrep is True
            quarantined_count += 1
        else:
            pytest.fail(f"Unexpected admission_disposition: {disp}")

    assert accepted_count == 18845
    assert quarantined_count == 130


def test_gate3b_scientific_panels_and_strata_balance(locked_manifest_data):
    """Verify 1,265 unique speakers (15 clips each), 5 balanced strata, and 0 panel overlap."""
    records = locked_manifest_data["records"]
    spk_clips = defaultdict(list)
    spk_roles = defaultdict(set)
    spk_strata = defaultdict(set)

    for r in records:
        sid = r["speaker_id"]
        spk_clips[sid].append(r["recording_id"])
        spk_roles[sid].add(r["panel_role"])
        spk_strata[sid].add(r["stratum_code"])

    assert len(spk_clips) == 1265
    assert all(len(clips) == 15 for clips in spk_clips.values())
    assert all(len(roles) == 1 for roles in spk_roles.values())
    assert all(len(strata) == 1 for strata in spk_strata.values())

    eval_spks = {s for s, roles in spk_roles.items() if "evaluation" in roles}
    gate_spks = {s for s, roles in spk_roles.items() if "gate_reference" in roles}
    res_spks = {s for s, roles in spk_roles.items() if "australian_reserve" in roles}

    assert len(eval_spks) == 1100
    assert len(gate_spks) == 100
    assert len(res_spks) == 65

    # Zero overlap
    assert len(eval_spks & gate_spks) == 0
    assert len(eval_spks & res_spks) == 0
    assert len(gate_spks & res_spks) == 0

    # 220 eval speakers per stratum
    eval_strata = Counter(list(spk_strata[s])[0] for s in eval_spks)
    expected_strata = {"australia", "canada", "england", "south_asian", "us"}
    assert set(eval_strata.keys()) == expected_strata
    assert all(count == 220 for count in eval_strata.values())

    # 20 gate speakers per stratum
    gate_strata = Counter(list(spk_strata[s])[0] for s in gate_spks)
    assert set(gate_strata.keys()) == expected_strata
    assert all(count == 20 for count in gate_strata.values())


def test_gate3b_physical_and_ledger_agreement(locked_manifest_data):
    """Verify all 18,975 records match physical destination files and disposition ledger."""
    records = locked_manifest_data["records"]

    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        ledger = {r["recording_id"]: r for r in csv.DictReader(f)}
    assert len(ledger) == 18975

    for r in records:
        rec_id = r["recording_id"]
        assert rec_id in ledger
        assert ledger[rec_id]["sha256"] == r["sha256"]

        audio_file = DEST_AUDIO_DIR / f"{rec_id}.mp3"
        assert audio_file.exists()
        assert audio_file.stat().st_size == r["file_size_bytes"]


def test_gate3b_audit_and_authorization_records():
    """Verify lock audit report and authorization record are complete and approved."""
    assert LOCK_AUDIT_JSON.exists()
    with open(LOCK_AUDIT_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["audit_verdict"] == "PASSED_AND_LOCKED"
    assert audit["locked_manifest_specification"]["manifest_sha256"] == EXPECTED_FINAL_MANIFEST_SHA256

    assert AUTH_RECORD_JSON.exists()
    with open(AUTH_RECORD_JSON, "r", encoding="utf-8") as f:
        auth = json.load(f)
    assert auth["status"] == "APPROVED"
    assert auth["target_production_manifest"]["status"] == "LOCKED"
    assert auth["target_production_manifest"]["sha256"] == EXPECTED_FINAL_MANIFEST_SHA256


def test_gate3b_provisional_manifest_untouched():
    """Verify provisional manifest remains unchanged."""
    assert PROV_MANIFEST_PATH.exists()
    assert _compute_sha256(PROV_MANIFEST_PATH) == EXPECTED_PROV_SHA256


def test_gate4_transcript_isolation_manifests():
    """Verify restricted online manifest shields evaluation labels and sealed key is intact."""
    online_manifest_path = SPLITS_DIR / "stage6m_cohort3_online_inference_manifest.json"
    assert online_manifest_path.exists()
    expected_online_hash = "0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1"
    assert _compute_sha256(online_manifest_path) == expected_online_hash

    with open(online_manifest_path, "r", encoding="utf-8") as f:
        online_data = json.load(f)

    online_records = online_data["records"]
    assert len(online_records) == 18975

    eval_records = [r for r in online_records if r["panel_role"] == "evaluation"]
    gate_records = [r for r in online_records if r["panel_role"] == "gate_reference"]
    res_records = [r for r in online_records if r["panel_role"] == "australian_reserve"]

    assert len(eval_records) == 16500
    assert len(gate_records) == 1500
    assert len(res_records) == 975

    # Assert 100% label shielding for evaluation records
    for r in eval_records:
        assert r["transcript"] is None
        assert r["word_count"] is None
        assert r["transcript_sealed"] is True

    # Assert gate-reference labels active for Sentinel Gate
    for r in gate_records:
        assert r["transcript"] is not None and len(r["transcript"]) > 0
        assert r["transcript_sealed"] is False

    # Assert sealed key
    sealed_key_path = SPLITS_DIR / "stage6m_cohort3_sealed_evaluation_transcripts.json"
    assert sealed_key_path.exists()
    expected_sealed_hash = "f427ae7fbf386f77b0795cc1fa33b2f7831c89f89ecfce7fa30036cde5c5223e"
    assert _compute_sha256(sealed_key_path) == expected_sealed_hash

    with open(sealed_key_path, "r", encoding="utf-8") as f:
        sealed_data = json.load(f)
    assert len(sealed_data["transcripts"]) == 16500 + 975

    # Audit report
    audit_json_path = REPORTS_DIR / "stage6m_transcript_isolation_audit.json"
    assert audit_json_path.exists()
    with open(audit_json_path, "r", encoding="utf-8") as f:
        audit_rep = json.load(f)
    assert audit_rep["verification_verdict"] == "ZERO_LABEL_EXPOSURE_CONFIRMED"
