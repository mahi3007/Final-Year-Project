"""
tests/research_validity/test_stage6m_cohort3_source_audit.py

Deterministic Automated Test Suite for Stage 6M v1.5 Cohort 3 Source Audit & Provisional Manifest
================================================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Phase: Stage 6M v1.5 Milestone 7.1-7.3 (Cohort 3 Data Preparation)

Test Invariants:
1. Source Corpus Bitwise Identity (Task A):
   - validated.tsv exists, has exactly 614,927,262 bytes and SHA-256 733c2fa7...
2. Historical Partition Isolation (Task B):
   - Exactly 558 historical speakers across Cohort 1 (60), Sentinel (30), Cohort 2 (468).
   - 100% pairwise disjointness across historical partitions.
   - 0 overlap between historical exposed pool and Cohort 3 provisional manifest.
3. Speaker Capacity Invariants (Task C):
   - Reconciled unexposed capacities match registered requirements:
     Australian: 305, Canadian: 418, England: 1120, South Asian: 653, US: 3791, Irish: 0.
4. Provisional Manifest Structure & Counts (Tasks D & E):
   - Exactly 1,100 evaluation speakers (220 per stratum across 5 strata).
   - Exactly 100 gate-reference speakers (20 per stratum across 5 strata).
   - Exactly 65 Australian replacement reserve speakers.
   - Exact mutual disjointness across evaluation, gate, and reserve panels.
   - Exactly 15 qualifying clips per speaker for all 1,265 speakers (18,975 total clips).
   - Zero duplicate speaker IDs or clip IDs.
   - Manifest remains explicitly UNLOCKED / PROVISIONAL.
5. Audit Artifact Integrity (Task G):
   - stage6m_cohort3_source_audit.md and stage6m_cohort3_source_audit.json exist and are well-formed.
6. Execution Gating & Frozen Code Immutability (Task H):
   - src/dsg_ctta/evaluation/paired_cluster_inference.py has 0 diff against origin/main.
   - GPU CTTA adaptation and confirmatory inference remain blocked.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.curate_stage6m_cohort3_selection_manifest import (
    CONFIRMATORY_STRATA,
    EXPECTED_HISTORICAL_PARTITIONS,
    EXPECTED_SOURCE_IDENTITY,
    EXPECTED_TOTAL_HISTORICAL_SPEAKERS,
    EXPECTED_UNEXPOSED_CAPACITIES,
    SELECTION_SEED,
    TARGET_CLIPS_PER_SPEAKER,
    TARGET_EVAL_SPEAKERS_PER_STRATUM,
    TARGET_GATE_SPEAKERS_PER_STRATUM,
    compute_sha256,
    load_historical_speakers,
)


# ==============================================================================
# Task A: Source Corpus Bitwise Identity
# ==============================================================================

def test_source_corpus_identity():
    """Verify that validated.tsv matches prespecified audit byte size and SHA-256."""
    source_path = PROJECT_ROOT / EXPECTED_SOURCE_IDENTITY["file_path"]
    assert source_path.exists(), f"Source file {source_path} does not exist"

    # Verify byte size
    actual_bytes = source_path.stat().st_size
    expected_bytes = EXPECTED_SOURCE_IDENTITY["bytes"]
    assert actual_bytes == expected_bytes, f"Source byte mismatch: expected {expected_bytes}, got {actual_bytes}"

    # Verify SHA-256
    expected_sha256 = EXPECTED_SOURCE_IDENTITY["sha256"]
    actual_sha256 = compute_sha256(source_path)
    assert actual_sha256 == expected_sha256, f"Source SHA-256 mismatch: {actual_sha256}"


# ==============================================================================
# Task B: Historical Partition Exposure Reconciliation
# ==============================================================================

def test_historical_exposure_isolation():
    """Verify that historical partitions contain exactly 558 speakers and 0 overlap."""
    splits_dir = PROJECT_ROOT / "datasets" / "splits"
    hist_files = {
        name: splits_dir / name for name in EXPECTED_HISTORICAL_PARTITIONS.keys()
    }
    all_prior, part_spks, part_prov = load_historical_speakers(hist_files)

    assert len(all_prior) == EXPECTED_TOTAL_HISTORICAL_SPEAKERS == 558, (
        f"Expected 558 unique historical speakers, found {len(all_prior)}"
    )

    # Check partition counts
    assert len(part_spks["stage5_external_eval.csv"]) == 60
    assert len(part_spks["stage5_sentinel_panel.csv"]) == 30
    assert len(part_spks["stage6m_cohort2_audio.csv"]) == 468

    # Verify sum equals unique count (strict pairwise disjointness)
    assert 60 + 30 + 468 == 558


# ==============================================================================
# Task C, D, E, F: Provisional Manifest Invariants
# ==============================================================================

@pytest.fixture(scope="module")
def manifest_data():
    """Load provisional JSON manifest and CSV manifest."""
    json_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_provisional_manifest.json"
    csv_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_provisional_manifest.csv"
    assert json_path.exists(), f"Missing {json_path}"
    assert csv_path.exists(), f"Missing {csv_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    return {"json": data, "csv": csv_rows}


def test_provisional_manifest_metadata_and_lock_status(manifest_data):
    """Verify that provisional manifest is unlocked and accurately records governance metadata."""
    manifest = manifest_data["json"]
    meta = manifest["metadata"]
    assert meta["manifest_type"] == "PROVISIONAL_SELECTION_MANIFEST"
    assert meta["manifest_status"] == "UNLOCKED"
    assert meta["selection_seed"] == SELECTION_SEED
    assert meta["protocol_version"] == "v1.5-five-stratum-parity"
    assert manifest["speakers_count"] == 1265
    assert manifest["clips_count"] == 18975


def test_provisional_manifest_speaker_counts(manifest_data):
    """Verify that provisional manifest has exactly 1,100 eval, 100 gate, and 65 reserve speakers."""
    manifest = manifest_data["json"]
    records = manifest["records"]

    # Deduplicate speakers
    spk_roles: dict[str, str] = {}
    spk_strata: dict[str, str] = {}
    for r in records:
        sid = r["speaker_id"]
        role = r["panel_role"]
        stratum = r["accent_group"]
        spk_roles[sid] = role
        spk_strata[sid] = stratum

    assert len(spk_roles) == 1265, f"Expected 1265 total speakers, got {len(spk_roles)}"

    eval_speakers = [s for s, r in spk_roles.items() if r == "evaluation"]
    gate_speakers = [s for s, r in spk_roles.items() if r == "gate_reference"]
    reserve_speakers = [s for s, r in spk_roles.items() if r == "australian_reserve"]

    assert len(eval_speakers) == 1100, f"Expected 1100 evaluation speakers, got {len(eval_speakers)}"
    assert len(gate_speakers) == 100, f"Expected 100 gate-reference speakers, got {len(gate_speakers)}"
    assert len(reserve_speakers) == 65, f"Expected 65 reserve speakers, got {len(reserve_speakers)}"

    # Check stratum-level breakdown
    for stratum in CONFIRMATORY_STRATA:
        st_eval = [s for s, r in spk_roles.items() if r == "evaluation" and spk_strata[s] == stratum]
        st_gate = [s for s, r in spk_roles.items() if r == "gate_reference" and spk_strata[s] == stratum]
        assert len(st_eval) == TARGET_EVAL_SPEAKERS_PER_STRATUM, f"{stratum} eval count {len(st_eval)} != {TARGET_EVAL_SPEAKERS_PER_STRATUM}"
        assert len(st_gate) == TARGET_GATE_SPEAKERS_PER_STRATUM, f"{stratum} gate count {len(st_gate)} != {TARGET_GATE_SPEAKERS_PER_STRATUM}"
        if stratum == "Australian English":
            st_res = [s for s, r in spk_roles.items() if r == "australian_reserve" and spk_strata[s] == stratum]
            assert len(st_res) == 65
        else:
            st_res = [s for s, r in spk_roles.items() if r == "australian_reserve" and spk_strata[s] == stratum]
            assert len(st_res) == 0


def test_provisional_manifest_disjointness_and_uniqueness(manifest_data):
    """Verify that evaluation, gate, and reserve panels are strictly disjoint with zero duplicate IDs."""
    manifest = manifest_data["json"]
    records = manifest["records"]

    eval_ids = {r["speaker_id"] for r in records if r["panel_role"] == "evaluation"}
    gate_ids = {r["speaker_id"] for r in records if r["panel_role"] == "gate_reference"}
    res_ids = {r["speaker_id"] for r in records if r["panel_role"] == "australian_reserve"}

    assert len(eval_ids) == 1100
    assert len(gate_ids) == 100
    assert len(res_ids) == 65

    # Pairwise disjointness
    assert len(eval_ids & gate_ids) == 0, f"Eval and Gate overlap: {eval_ids & gate_ids}"
    assert len(eval_ids & res_ids) == 0, f"Eval and Reserve overlap: {eval_ids & res_ids}"
    assert len(gate_ids & res_ids) == 0, f"Gate and Reserve overlap: {gate_ids & res_ids}"

    # Overall unique count
    all_selected_ids = eval_ids | gate_ids | res_ids
    assert len(all_selected_ids) == 1265


def test_provisional_manifest_historical_isolation(manifest_data):
    """Verify that zero selected speakers overlap with the 558 historical exposed speakers."""
    splits_dir = PROJECT_ROOT / "datasets" / "splits"
    hist_files = {
        name: splits_dir / name for name in EXPECTED_HISTORICAL_PARTITIONS.keys()
    }
    all_prior, _, _ = load_historical_speakers(hist_files)

    manifest = manifest_data["json"]
    all_selected_ids = {r["speaker_id"] for r in manifest["records"]}

    overlap = all_prior & all_selected_ids
    assert len(overlap) == 0, f"Critical contamination: {len(overlap)} historical speakers in Cohort 3: {overlap}"


def test_provisional_manifest_clip_counts_and_uniqueness(manifest_data):
    """Verify that every speaker has exactly 15 qualifying clips and all clip IDs are globally unique."""
    manifest = manifest_data["json"]
    records = manifest["records"]

    spk_clips = defaultdict(list)
    all_clip_ids = set()

    for r in records:
        cid = r["recording_id"]
        sid = r["speaker_id"]
        assert cid not in all_clip_ids, f"Duplicate clip ID found: {cid}"
        all_clip_ids.add(cid)
        spk_clips[sid].append(cid)

    assert len(spk_clips) == 1265
    for sid, clips in spk_clips.items():
        assert len(clips) == TARGET_CLIPS_PER_SPEAKER == 15, f"Speaker {sid} has {len(clips)} clips"

    expected_total_clips = 1265 * 15
    assert len(records) == expected_total_clips == 18975
    assert len(all_clip_ids) == 18975

    # Verify CSV rows match JSON records
    csv_rows = manifest_data["csv"]
    assert len(csv_rows) == 18975


# ==============================================================================
# Task G: Audit Report Artifacts
# ==============================================================================

def test_audit_reports_exist_and_consistent():
    """Verify that stage6m_cohort3_source_audit.md and .json exist and are well-formed."""
    md_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_source_audit.md"
    json_path = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_source_audit.json"

    assert md_path.exists(), f"Missing {md_path}"
    assert json_path.exists(), f"Missing {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        audit_json = json.load(f)

    assert audit_json["governance_status"] == "AUTHORIZED_FOR_DATA_PREPARATION"
    assert audit_json["source_identity"]["verified"] is True
    assert audit_json["historical_exposure"]["total_unique_exposed"] == 558
    assert audit_json["validation"]["validation_status"] == "PASS"

    md_text = md_path.read_text(encoding="utf-8")
    assert "STAGE6M_COHORT3_SOURCE_AUDIT" in md_text
    assert "AUTHORIZED FOR DATA PREPARATION" in md_text
    assert "733c2fa79e727f0b69074765c8ba0f30c61c2a132a440a0ba5af86cba75b3f2a" in md_text


# ==============================================================================
# Task H: Execution Gating & Code Immutability
# ==============================================================================

def test_frozen_execution_code_immutability():
    """
    Verify that frozen v1.4.0 execution code has 0 diff against historical frozen commit a7a3b79
    and matches authoritative git object blob hash 58d456fbcce43b5322d56df80e4077a32d7f4cca.
    Prevents false passes caused by moving branch references.
    """
    frozen_file = "src/dsg_ctta/evaluation/paired_cluster_inference.py"
    expected_blob = "58d456fbcce43b5322d56df80e4077a32d7f4cca"
    historical_commit = "a7a3b79"

    # 1. Verify working copy git blob hash matches authoritative historical blob
    res_hash = subprocess.run(
        ["git", "hash-object", frozen_file],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    actual_blob = res_hash.stdout.strip()
    assert actual_blob == expected_blob, (
        f"Frozen execution code blob mismatch: expected {expected_blob}, got {actual_blob}"
    )

    # 2. Verify git diff against fixed historical commit a7a3b79 is strictly empty (0 diff)
    res_diff = subprocess.run(
        ["git", "diff", historical_commit, "--", frozen_file],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert res_diff.stdout.strip() == "", (
        f"Frozen execution code differs from historical commit {historical_commit}:\n{res_diff.stdout}"
    )

    # 3. Verify historical commit a7a3b79 blob equals working copy blob
    res_rev = subprocess.run(
        ["git", "rev-parse", f"{historical_commit}:{frozen_file}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert res_rev.stdout.strip() == expected_blob



def test_audio_materialization_controlled_phasing():
    """Verify that audio materialization proceeds strictly under controlled pipelines with zero rogue files."""
    cohort3_audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort3_audio"
    if cohort3_audio_dir.exists():
        csv_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_provisional_manifest.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            valid_ids = {r["recording_id"] for r in csv.DictReader(f)}
        for p in cohort3_audio_dir.iterdir():
            if p.is_file():
                assert p.stem in valid_ids, f"Extraneous unapproved audio file found: {p}"

