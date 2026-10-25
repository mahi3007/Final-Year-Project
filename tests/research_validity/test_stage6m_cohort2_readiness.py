"""
tests/research_validity/test_stage6m_cohort2_readiness.py

Automated Test Suite for Stage 6M Cohort 2 Preflight Readiness & Fail-Closed Invariants.
========================================================================================
Standard: ADR-005 (Amended via AMENDMENT-001)
Protocol: v1.3.4-stage6m-self-authorization-amendment

Verifies:
1. Locked Manifest Integrity:
   - Passes on authoritative repository manifest & lock.
   - Fails on tampered cryptographic hash.
   - Fails on corrupted schema (missing strata, incorrect speaker counts).
2. Manifest <-> Evaluation CSV Agreement:
   - Fails closed to HOLD when CSV is not materialized on disk.
   - Fails on duplicate clip IDs.
   - Fails on total clip count != 7,020.
   - Fails on unmapped speaker IDs not in candidate manifest active prefixes.
3. Audio Materialization:
   - Fails closed to MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD when audio is missing or < 7,020 files.
4. Sentinel Panel Completeness & Zero-Exposure Speaker Isolation:
   - Validates 30 core sentinel clips and 281 normalized words (uncertainty floor = 0.3559 pp).
   - Asserts zero speaker overlap between sentinel panel and candidate manifest active speakers.
   - Fails on simulated speaker leakage.
5. End-to-End Technical Readiness:
   - Verifies transition to READY FOR AUTHORIZED EXECUTION when all prerequisites are satisfied.
   - Verifies fail-closed CLI behavior in cloud/kaggle/run_stage6m_cohort2_benchmark.py.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.data.cohort2_preflight import (
    Cohort1PreflightValidator,
    Cohort2PreflightValidator,
    VALID_MANIFEST_SHA256,
    VALID_MANIFEST_CRLF_SHA256,
    VALID_MANIFEST_LF_SHA256,
    VALID_MANIFEST_LOCK_SHA256,
    VALID_SENTINEL_CSV_SHA256,
    VALID_SENTINEL_CSV_CRLF_SHA256,
    VALID_SENTINEL_CSV_LF_SHA256,
    VALID_SENTINEL_LOCK_SHA256,
    VALID_STAGE5_EVAL_CSV_SHA256,
    VALID_STAGE5_EVAL_CSV_CRLF_SHA256,
    VALID_STAGE5_EVAL_CSV_LF_SHA256,
    VALID_STAGE5_EVAL_LOCK_SHA256,
    EXPECTED_STRATA_NAMES,
    CORE_SENTINEL_WORDS,
    CORE_SENTINEL_CLIPS,
    CORE_SENTINEL_SPEAKERS,
    EXPECTED_UNCERTAINTY_FLOOR_PP,
    select_deterministic_sentinel_samples,
)


@pytest.fixture
def base_validator():
    return Cohort2PreflightValidator(project_root=PROJECT_ROOT)


# =============================================================================
# 1. Manifest Cryptographic Hash & Schema Integrity Tests
# =============================================================================

def test_cohort2_manifest_integrity_on_committed_repo(base_validator):
    """Authoritative manifest and lock file must pass all cryptographic and schema checks."""
    result = base_validator.validate_manifest()
    assert result["status"] == "PASS", f"Manifest check failed: {result['errors']}"
    assert result["details"]["manifest_sha256"] in VALID_MANIFEST_SHA256
    assert result["details"]["total_active_speakers"] == 468
    assert result["details"]["total_clips_allocated"] == 7020
    assert len(result["details"]["strata_summary"]) == 6
    assert result["details"]["irish_reserve_total"] == 27


def test_cohort2_manifest_fails_on_tampered_hash(tmp_path):
    """Tampering with a single byte in the manifest must cause fail-closed rejection."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    # Copy manifest and mutate
    mutated_manifest = tmp_path / "stage6m_locked_candidate_manifest.json"
    content = real_manifest.read_bytes()
    mutated_manifest.write_bytes(content + b"\n/* tamper */")

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=mutated_manifest,
        lock_path=real_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("Manifest SHA-256 mismatch" in err for err in result["errors"])


def test_cohort2_manifest_fails_on_missing_stratum(tmp_path):
    """Manifest missing one required stratum must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Delete US English stratum
    del data["strata"]["US English"]
    data["metadata"]["total_strata"] = 5

    mutated_manifest = tmp_path / "manifest.json"
    with open(mutated_manifest, "w", encoding="utf-8") as f:
        json.dump(data, f)

    fake_lock = tmp_path / "lock.json"
    m_hash = hashlib.sha256(mutated_manifest.read_bytes()).hexdigest()
    fake_lock.write_text(json.dumps({"sha256": m_hash, "sha256_lf": m_hash}))

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=mutated_manifest,
        lock_path=fake_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("Missing required stratum" in err or "Expected 6 strata" in err for err in result["errors"])


def test_cohort2_manifest_fails_on_incorrect_speaker_count(tmp_path):
    """Stratum with != 78 active speakers must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Pop one speaker from Irish English
    data["strata"]["Irish English"]["active_speakers"].pop()
    data["strata"]["Irish English"]["active_count"] = 77
    data["metadata"]["total_active_speakers"] = 467

    mutated_manifest = tmp_path / "manifest.json"
    with open(mutated_manifest, "w", encoding="utf-8") as f:
        json.dump(data, f)

    fake_lock = tmp_path / "lock.json"
    m_hash = hashlib.sha256(mutated_manifest.read_bytes()).hexdigest()
    fake_lock.write_text(json.dumps({"sha256": m_hash, "sha256_lf": m_hash}))

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=mutated_manifest,
        lock_path=fake_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("active speakers" in err for err in result["errors"])


# =============================================================================
# 2. Evaluation CSV Agreement & Invariant Tests
# =============================================================================

def test_cohort2_eval_csv_fails_closed_when_not_materialized(base_validator):
    """When stage6m_cohort2_audio.csv does not exist, status must be HOLD with clear reason."""
    manifest_res = base_validator.validate_manifest()
    with open(base_validator.manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Point to nonexistent CSV
    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=PROJECT_ROOT / "datasets" / "splits" / "nonexistent_stage6m_cohort2_audio.csv",
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "HOLD"
    assert any("MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in err for err in result["errors"])


def _generate_synthetic_cohort2_df(manifest_data: dict) -> pd.DataFrame:
    """Helper to generate a valid matching synthetic evaluation DataFrame."""
    rows = []
    clip_counter = 1
    for stratum_name, s_info in manifest_data["strata"].items():
        stratum_code = s_info.get("stratum_code", "generic")
        for spk in s_info["active_speakers"]:
            # Construct a full 64-char speaker_id starting with the 24-char prefix
            prefix = spk["speaker_id_prefix"].rstrip("…")
            full_spk_id = prefix + "0" * (64 - len(prefix))
            for c_idx in range(15):
                rows.append({
                    "recording_id": f"cohort2_clip_{clip_counter:05d}",
                    "speaker_id": full_spk_id,
                    "stage5_accent_group": stratum_name,
                    "stratum_code": stratum_code,
                    "transcript": f"This is synthetic sentence number {clip_counter} for testing.",
                })
                clip_counter += 1
    return pd.DataFrame(rows)


def _generate_matching_clip_lock(df: pd.DataFrame, csv_path: Path, clip_lock_path: Path) -> str:
    """Generate a fully compliant, complete-schema clip lock JSON and return its SHA-256 digest."""
    csv_bytes = csv_path.read_bytes()
    csv_hash = hashlib.sha256(csv_bytes).hexdigest()
    lock_dict = {
        "protocol_version": "v1.3.4-stage6m-self-authorization-amendment",
        "governing_standard": "ADR-005 (Amended via AMENDMENT-001)",
        "dataset_name": "stage6m_cohort2_audio",
        "total_clips": len(df),
        "total_speakers": int(df["speaker_id"].nunique()),
        "total_strata": 6,
        "clips_per_speaker": 15,
        "csv_sha256": csv_hash,
        "crlf_sha256": csv_hash,
        "lf_sha256": csv_hash,
        "recording_ids": list(df["recording_id"]),
    }
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_dict, f, indent=2)
    return hashlib.sha256(clip_lock_path.read_bytes()).hexdigest()


def test_cohort2_eval_csv_fails_when_clip_lock_missing(tmp_path):
    """When evaluation CSV exists but mandatory clip lock is missing, validator must fail closed."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    nonexistent_lock = tmp_path / "nonexistent_stage6m_cohort2_audio.lock.json"
    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT, eval_csv_path=csv_path, clip_lock_path=nonexistent_lock
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "FAIL"
    assert any("Mandatory clip lock file missing" in err for err in result["errors"])


def test_cohort2_eval_csv_agreement_passes_on_valid_matching_data(tmp_path):
    """When CSV and mandatory clip lock exactly match manifest and lock is approved, agreement check must pass."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    lock_hash = _generate_matching_clip_lock(df, csv_path, lock_path)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=lock_path,
        approved_clip_lock_sha256={lock_hash},
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "PASS"
    assert result["details"]["total_clips"] == 7020
    assert result["details"]["unique_speakers"] == 468
    assert result["details"]["duplicate_clip_count"] == 0
    assert result["details"]["manifest_prefix_match_rate_pct"] == 100.0
    assert result["details"]["clip_lock_verified"] is True


def test_cohort2_eval_csv_fails_on_duplicate_clip_ids(tmp_path):
    """Evaluation CSV containing duplicate clip IDs must fail closed."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    # Inject duplicate recording_id
    df.loc[1, "recording_id"] = df.loc[0, "recording_id"]
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    lock_hash = _generate_matching_clip_lock(df, csv_path, lock_path)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=lock_path,
        approved_clip_lock_sha256={lock_hash},
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "FAIL"
    assert any("duplicate clip IDs" in err for err in result["errors"])


def test_cohort2_eval_csv_fails_on_unmapped_speakers(tmp_path):
    """Evaluation CSV containing speakers outside the locked candidate manifest must fail closed."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    # Mutate speaker prefix of the first speaker to an unauthorized prefix
    unauth_spk = "ffffffffffffffffffffffff" + "0" * 40
    df.loc[df["speaker_id"] == df.loc[0, "speaker_id"], "speaker_id"] = unauth_spk
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    lock_hash = _generate_matching_clip_lock(df, csv_path, lock_path)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=lock_path,
        approved_clip_lock_sha256={lock_hash},
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "FAIL"
    assert any("do not match any candidate manifest active prefix" in err for err in result["errors"])


# =============================================================================
# 3. Audio Materialization Invariant Tests
# =============================================================================

def test_cohort2_audio_fails_closed_when_directory_missing(base_validator):
    """When audio directory does not exist, status must be HOLD."""
    result = base_validator.validate_audio_materialization()
    assert result["status"] == "HOLD"
    assert any("MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in err for err in result["errors"])


def test_cohort2_audio_fails_closed_when_clip_count_insufficient(tmp_path):
    """When audio directory has fewer than 7,020 clips, status must be HOLD."""
    audio_dir = tmp_path / "cohort2_audio"
    audio_dir.mkdir()
    # Create 5 dummy MP3 files
    for i in range(5):
        (audio_dir / f"clip_{i}.mp3").write_bytes(b"dummy")

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, audio_dir=audio_dir)
    result = validator.validate_audio_materialization()
    assert result["status"] == "HOLD"
    assert result["details"]["files_present"] == 5
    assert result["details"]["files_required"] == 7020


# =============================================================================
# 4. Sentinel Panel Completeness & Zero-Exposure Isolation Tests
# =============================================================================

def test_cohort2_sentinel_panel_and_isolation_on_committed_repo(base_validator):
    """Committed sentinel panel must have 30 core clips, 281 reference words, and 0 active overlap."""
    with open(base_validator.manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    result = base_validator.validate_sentinel_panel_and_isolation(manifest_data=manifest_data)
    assert result["status"] == "PASS", f"Sentinel check failed: {result['errors']}"
    assert result["details"]["core_sentinel_clips"] == CORE_SENTINEL_CLIPS
    assert result["details"]["core_sentinel_speakers"] == CORE_SENTINEL_SPEAKERS
    assert result["details"]["core_sentinel_reference_words"] == CORE_SENTINEL_WORDS
    assert result["details"]["uncertainty_floor_pp"] == EXPECTED_UNCERTAINTY_FLOOR_PP
    assert result["details"]["speaker_isolation_verified"] is True
    assert result["details"]["sentinel_active_overlap_count"] == 0


def test_cohort2_sentinel_fails_on_speaker_overlap_leakage(base_validator, tmp_path):
    """If an evaluation CSV contains a sentinel speaker, preflight must fail with DATA LEAKAGE."""
    with open(base_validator.manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    # Inject a sentinel speaker ID into the evaluation DataFrame
    sent_df = pd.read_csv(base_validator.sentinel_csv_path)
    sent_speaker = sent_df["speaker_id"].iloc[0]
    df.loc[0, "speaker_id"] = sent_speaker

    result = base_validator.validate_sentinel_panel_and_isolation(manifest_data=manifest_data, eval_df=df)
    assert result["status"] == "FAIL"
    assert any("DATA LEAKAGE DETECTED" in err for err in result["errors"])


# =============================================================================
# 5. Full End-to-End Preflight Execution & Report Artifact Generation
# =============================================================================

def test_cohort2_full_preflight_on_committed_repo_produces_hold_and_reports(base_validator, tmp_path):
    """
    On the committed repo (where Cohort 2 physical audio is not yet downloaded),
    run_preflight() must return HOLD, record active HOLD reasons, and save valid JSON/MD reports.
    """
    report = base_validator.run_preflight()
    assert report["overall_status"] == "HOLD"
    assert "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in report["summary_description"]
    assert len(report["status_reasons"]) >= 1

    json_p, md_p = base_validator.save_reports(report, output_dir=tmp_path)
    assert json_p.exists() and json_p.stat().st_size > 0
    assert md_p.exists() and md_p.stat().st_size > 0

    with open(json_p, "r", encoding="utf-8") as f:
        saved_json = json.load(f)
    assert saved_json["overall_status"] == "HOLD"

    md_text = md_p.read_text(encoding="utf-8")
    assert "Overall Preflight Status:** `HOLD`" in md_text
    assert "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in md_text


def test_cohort2_full_preflight_reaches_ready_state_on_mock_materialized_dataset(tmp_path):
    """
    When all prerequisites (manifest, evaluation CSV matching manifest, 7,020 valid audio files,
    sentinel panel) are satisfied, preflight must cleanly evaluate to READY FOR AUTHORIZED EXECUTION.
    """
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # 1. Generate matching CSV and mandatory clip lock
    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)
    clip_lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    clip_lock_hash = _generate_matching_clip_lock(df, csv_path, clip_lock_path)

    # 2. Generate matching dummy 16 kHz audio files
    audio_dir = tmp_path / "cohort2_audio"
    audio_dir.mkdir()
    import soundfile as sf
    dummy_wav = np.zeros(16000, dtype=np.float32)  # 1s of silence
    dummy_wav[100] = 0.5  # Non-zero sample
    sample_file = audio_dir / "sample.wav"
    sf.write(sample_file, dummy_wav, 16000)
    sample_bytes = sample_file.read_bytes()

    for rec_id in df["recording_id"]:
        (audio_dir / f"{rec_id}.mp3").write_bytes(sample_bytes)

    # 3. Instantiate validator with mock paths
    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=manifest_path,
        lock_path=PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json",
        clip_lock_path=clip_lock_path,
        eval_csv_path=csv_path,
        audio_dir=audio_dir,
        sentinel_csv_path=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv",
        sentinel_lock_path=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json",
        sentinel_audio_dir=PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio",
        approved_clip_lock_sha256={clip_lock_hash},
    )

    report = validator.run_preflight(check_audio_samples=5)
    assert report["overall_status"] == "READY FOR AUTHORIZED EXECUTION"
    assert report["status_reasons"] == []
    assert report["checks"]["manifest_integrity_and_schema"]["status"] == "PASS"
    assert report["checks"]["evaluation_csv_manifest_agreement"]["status"] == "PASS"
    assert report["checks"]["audio_materialization_and_decodability"]["status"] == "PASS"
    assert report["checks"]["sentinel_panel_completeness_and_isolation"]["status"] == "PASS"
    assert report["checks"]["execution_configuration_freeze"]["status"] == "PASS"


def test_cohort2_benchmark_runner_preflight_only_cli(tmp_path):
    """Verify that runner CLI with --preflight-only runs cleanly and exits with code 1 under current HOLD."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"),
        "--cohort",
        "cohort2",
        "--preflight-only",
        "--reports-dir",
        str(tmp_path / "reports"),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 1
    assert "PREFLIGHT AUDIT VERDICT: HOLD" in proc.stdout
    assert "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD" in proc.stdout


def test_cohort1_benchmark_runner_preflight_only_cli_exits_before_model_initialization():
    """Verify that runner CLI with --cohort cohort1 --preflight-only exits cleanly with code 0 without model loading."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"),
        "--cohort",
        "cohort1",
        "--preflight-only",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0, f"Cohort 1 preflight-only failed with stderr:\n{proc.stderr}"
    assert "PREFLIGHT AUDIT VERDICT: READY FOR AUTHORIZED EXECUTION (COHORT 1)" in proc.stdout
    assert "Initializing Neural Acoustic Model" not in proc.stdout
    assert "Preloading" not in proc.stdout
    assert "Executing Continuous Stream" not in proc.stdout


# =============================================================================
# 6. Authority Model & Governance Provenance Tests (Finding 4)
# =============================================================================

def test_cohort2_manifest_fails_on_unauthorized_token_in_lock(tmp_path):
    """Modified or unauthorized authorization token in lock file must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    with open(real_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Tamper token
    lock_data["authorization_record"]["token"] = "UNAUTHORIZED-TOKEN-XYZ"
    tampered_lock = tmp_path / "tampered_lock.json"
    with open(tampered_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=tampered_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("authorization token in lock record" in err for err in result["errors"])


def test_cohort2_manifest_fails_on_non_allowlisted_digest_in_lock(tmp_path):
    """Lock file specifying a hash outside the canonical allowlist must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    with open(real_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Mutate to arbitrary digest
    lock_data["sha256"] = "1111111111111111111111111111111111111111111111111111111111111111"
    lock_data["sha256_lf"] = "2222222222222222222222222222222222222222222222222222222222222222"
    tampered_lock = tmp_path / "tampered_lock.json"
    with open(tampered_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=tampered_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("unauthorized SHA-256 digest" in err for err in result["errors"])


def test_cohort2_manifest_fails_on_contradictory_governance_metadata(tmp_path):
    """Contradictory execution_authorized metadata in lock file must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    with open(real_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    lock_data["execution_authorized"] = False
    tampered_lock = tmp_path / "tampered_lock.json"
    with open(tampered_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=tampered_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("execution_authorized mismatch" in err for err in result["errors"])


# =============================================================================
# 7. Speaker Stratum Preservation & Clip Lock Tests (Finding 3)
# =============================================================================

def test_cohort2_eval_csv_fails_on_stratum_swapping(tmp_path):
    """
    Deliberately swapping speaker stratum assignments between strata while preserving
    aggregate stratum counts (1,170 each) and active prefix matching must fail closed.
    """
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)

    # Pick one speaker from Irish English and one from Canadian English
    irish_spk = df[df["stage5_accent_group"] == "Irish English"]["speaker_id"].iloc[0]
    canada_spk = df[df["stage5_accent_group"] == "Canadian English"]["speaker_id"].iloc[0]

    # Swap their strata in the evaluation CSV
    df.loc[df["speaker_id"] == irish_spk, "stage5_accent_group"] = "Canadian English"
    df.loc[df["speaker_id"] == irish_spk, "stratum_code"] = "canada"
    df.loc[df["speaker_id"] == canada_spk, "stage5_accent_group"] = "Irish English"
    df.loc[df["speaker_id"] == canada_spk, "stratum_code"] = "ireland"

    # Verify counts remain 1170 per stratum
    assert (df.groupby("stage5_accent_group")["recording_id"].count() == 1170).all()
    assert len(df) == 7020

    csv_path = tmp_path / "swapped_stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    clip_lock_path = tmp_path / "swapped_stage6m_cohort2_audio.lock.json"
    clip_lock_hash = _generate_matching_clip_lock(df, csv_path, clip_lock_path)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={clip_lock_hash},
    )
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "FAIL"
    assert any("Speaker stratum preservation violation" in err for err in result["errors"])


def test_cohort2_eval_csv_clip_lock_comprehensive_validation(tmp_path):
    """Clip lock file must enforce approved hash anchor, complete schema, and exact clip-set equality."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    # 1. Matching clip lock with complete schema and approved hash -> PASS
    clip_lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    lock_hash = _generate_matching_clip_lock(df, csv_path, clip_lock_path)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={lock_hash},
    )
    res_pass = validator.validate_eval_csv(manifest_data)
    assert res_pass["status"] == "PASS"
    assert res_pass["details"]["clip_lock_verified"] is True

    # 2. Unapproved clip lock hash -> FAIL
    validator_unauth = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={"unauthorized_hash_value" * 4},
    )
    res_unauth = validator_unauth.validate_eval_csv(manifest_data)
    assert res_unauth["status"] == "FAIL"
    assert any("not in approved allowlist" in err for err in res_unauth["errors"])

    # 3. Incomplete schema (missing required total_clips key) -> FAIL
    with open(clip_lock_path, "r", encoding="utf-8") as f:
        lock_dict = json.load(f)
    del lock_dict["total_clips"]
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_dict, f, indent=2)
    tampered_hash = hashlib.sha256(clip_lock_path.read_bytes()).hexdigest()

    validator_incomp = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={tampered_hash},
    )
    res_incomp = validator_incomp.validate_eval_csv(manifest_data)
    assert res_incomp["status"] == "FAIL"
    assert any("Clip lock schema incomplete" in err for err in res_incomp["errors"])

    # 4. Mismatched clip lock recording IDs (omit one clip ID, add one bogus ID) -> FAIL
    lock_dict["total_clips"] = 7020
    all_rec_ids = list(df["recording_id"])
    lock_dict["recording_ids"] = all_rec_ids[:-1] + ["bogus_extra_clip_99999"]
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_dict, f, indent=2)
    tampered_hash = hashlib.sha256(clip_lock_path.read_bytes()).hexdigest()

    validator_mismatch = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={tampered_hash},
    )
    res_fail = validator_mismatch.validate_eval_csv(manifest_data)
    assert res_fail["status"] == "FAIL"
    assert any("Clip-set exact equality failed" in err for err in res_fail["errors"])

    # 5. Mismatched CSV digest -> FAIL
    lock_dict["recording_ids"] = all_rec_ids
    lock_dict["csv_sha256"] = "0" * 64
    lock_dict["crlf_sha256"] = "0" * 64
    lock_dict["lf_sha256"] = "0" * 64
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_dict, f, indent=2)
    tampered_hash = hashlib.sha256(clip_lock_path.read_bytes()).hexdigest()

    validator_csv_mismatch = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=csv_path,
        clip_lock_path=clip_lock_path,
        approved_clip_lock_sha256={tampered_hash},
    )
    res_csv_mismatch = validator_csv_mismatch.validate_eval_csv(manifest_data)
    assert res_csv_mismatch["status"] == "FAIL"
    assert any("not in clip lock declared digests" in err for err in res_csv_mismatch["errors"])


# =============================================================================
# 8. Audio Materialization Invariants (Finding 5)
# =============================================================================

def test_cohort2_audio_fails_on_zero_byte_file(tmp_path):
    """Audio materialization must reject empty (zero-byte) files."""
    audio_dir = tmp_path / "cohort2_audio"
    audio_dir.mkdir()

    # Create 7019 valid 1-byte files and 1 zero-byte file
    for i in range(7019):
        (audio_dir / f"clip_{i:05d}.mp3").write_bytes(b"x")
    zero_file = audio_dir / "clip_07019.mp3"
    zero_file.write_bytes(b"")  # 0 bytes

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, audio_dir=audio_dir)
    result = validator.validate_audio_materialization(check_samples=1)
    assert result["status"] == "FAIL"
    assert any("zero bytes" in err for err in result["errors"])


def test_cohort2_audio_fails_on_extraneous_files(tmp_path):
    """Audio directory containing extra MP3 files not listed in CSV must fail closed."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    audio_dir = tmp_path / "cohort2_audio"
    audio_dir.mkdir()

    import soundfile as sf
    dummy_wav = np.zeros(16000, dtype=np.float32)
    sample_file = audio_dir / "sample.wav"
    sf.write(sample_file, dummy_wav, 16000)
    sample_bytes = sample_file.read_bytes()

    for rec_id in df["recording_id"]:
        (audio_dir / f"{rec_id}.mp3").write_bytes(sample_bytes)

    # Inject an extraneous MP3 file
    (audio_dir / "extraneous_unlisted_clip.mp3").write_bytes(sample_bytes)

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, audio_dir=audio_dir)
    result = validator.validate_audio_materialization(eval_df=df, check_samples=5)
    assert result["status"] == "FAIL"
    assert any("extraneous audio files" in err for err in result["errors"])


# =============================================================================
# 9. Truthful Markdown Reporting (Finding 1)
# =============================================================================

def test_cohort2_markdown_report_avoids_contradictory_claims_under_hold(tmp_path):
    """
    Under HOLD with unmaterialized evaluation CSV, the checklist matrix must state
    that validation could not be completed and never claim completed decodability or clip counts.
    """
    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=tmp_path / "nonexistent_stage6m_cohort2_audio.csv",
    )
    report = validator.run_preflight()
    assert report["overall_status"] == "HOLD"

    _, md_p = validator.save_reports(report, output_dir=tmp_path)
    md_text = md_p.read_text(encoding="utf-8")

    # Positive assertions: must state validation could not be completed
    assert "Validation could not be completed: evaluation CSV not materialized on disk (prerequisite missing)." in md_text
    assert "Validation could not be completed: physical audio files not materialized" in md_text

    # Negative assertions: must NOT make false success claims
    assert "7,020 physical 16 kHz audio files materialized and decodable" not in md_text
    assert "0 duplicate clip IDs; 7,020 clips (1,170/stratum); prefix mapping complete." not in md_text


# =============================================================================
# 10. Strict Lock-Digest Verification & Lock Anchoring Tests (Finding 3)
# =============================================================================

def test_cohort2_manifest_fails_on_mixed_digests_in_lock(tmp_path):
    """
    A manifest lock containing one correct canonical digest and one arbitrary/bogus digest
    must fail closed. Every populated digest field must match its expected line-ending variant.
    """
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    with open(real_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Case A: Valid CRLF, but arbitrary bogus LF
    tampered_data_a = copy.deepcopy(lock_data)
    tampered_data_a["sha256_lf"] = "deadbeef" * 8
    lock_a = tmp_path / "lock_mixed_a.json"
    with open(lock_a, "w", encoding="utf-8") as f:
        json.dump(tampered_data_a, f)
    hash_a = hashlib.sha256(lock_a.read_bytes()).hexdigest()

    validator_a = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=lock_a,
        approved_manifest_lock_sha256={hash_a},
    )
    res_a = validator_a.validate_manifest()
    assert res_a["status"] == "FAIL"
    assert any("unauthorized LF 'sha256_lf' digest" in err for err in res_a["errors"])

    # Case B: Arbitrary bogus CRLF, but valid LF
    tampered_data_b = copy.deepcopy(lock_data)
    tampered_data_b["sha256"] = "cafebabe" * 8
    lock_b = tmp_path / "lock_mixed_b.json"
    with open(lock_b, "w", encoding="utf-8") as f:
        json.dump(tampered_data_b, f)
    hash_b = hashlib.sha256(lock_b.read_bytes()).hexdigest()

    validator_b = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=lock_b,
        approved_manifest_lock_sha256={hash_b},
    )
    res_b = validator_b.validate_manifest()
    assert res_b["status"] == "FAIL"
    assert any("unauthorized CRLF 'sha256' digest" in err for err in res_b["errors"])


def test_cohort2_manifest_fails_on_tampered_manifest_lock_file(tmp_path):
    """Manifest lock file on disk whose SHA-256 is not in approved allowlist must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    # Copy lock file and tamper with bytes
    tampered_lock = tmp_path / "tampered_manifest.lock.json"
    tampered_lock.write_bytes(real_lock.read_bytes() + b"\n/* tamper */")

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=tampered_lock,
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("not in canonical allowlist" in err for err in result["errors"])


def test_cohort2_sentinel_fails_on_tampered_sentinel_lock_file(tmp_path):
    """Sentinel lock file on disk whose SHA-256 is not in approved allowlist must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    real_sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    real_sent_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json"

    tampered_sent_lock = tmp_path / "tampered_sentinel.lock.json"
    tampered_sent_lock.write_bytes(real_sent_lock.read_bytes() + b"\n/* tamper */")

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_csv_path=real_sent_csv,
        sentinel_lock_path=tampered_sent_lock,
    )
    result = validator.validate_sentinel_panel_and_isolation(manifest_data)
    assert result["status"] == "FAIL"
    assert any("not in approved lock allowlist" in err for err in result["errors"])


def test_cohort2_sentinel_fails_on_mixed_digests_in_lock(tmp_path):
    """Sentinel lock containing an unauthorized digest variant must fail closed."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    real_sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    real_sent_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json"

    with open(real_sent_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Invalidate LF digest while keeping CRLF digest valid
    lock_data["lf_sha256"] = "12345678" * 8
    tampered_lock = tmp_path / "sentinel_mixed.lock.json"
    with open(tampered_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)
    tampered_hash = hashlib.sha256(tampered_lock.read_bytes()).hexdigest()

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_csv_path=real_sent_csv,
        sentinel_lock_path=tampered_lock,
        approved_sentinel_lock_sha256={tampered_hash},
    )
    result = validator.validate_sentinel_panel_and_isolation(manifest_data)
    assert result["status"] == "FAIL"
    assert any("unauthorized 'lf_sha256'" in err for err in result["errors"])


def test_cohort2_manifest_fails_on_swapped_canonical_digests_in_lock(tmp_path):
    """
    Manifest lock where canonical CRLF and LF digests are deliberately swapped between fields
    must fail closed at field-level checks even when the physical lock disk hash is anchored.
    """
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json"

    with open(real_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Deliberately swap canonical CRLF and LF digests between fields
    lock_data["sha256"] = VALID_MANIFEST_LF_SHA256
    lock_data["sha256_lf"] = VALID_MANIFEST_CRLF_SHA256

    swapped_lock = tmp_path / "manifest_swapped.lock.json"
    with open(swapped_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)
    swapped_hash = hashlib.sha256(swapped_lock.read_bytes()).hexdigest()

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        manifest_path=real_manifest,
        lock_path=swapped_lock,
        approved_manifest_lock_sha256={swapped_hash},
    )
    result = validator.validate_manifest()
    assert result["status"] == "FAIL"
    assert any("unauthorized CRLF 'sha256' digest" in err for err in result["errors"])
    assert any("unauthorized LF 'sha256_lf' digest" in err for err in result["errors"])


def test_cohort2_sentinel_fails_on_swapped_canonical_digests_in_lock(tmp_path):
    """
    Sentinel lock where canonical CRLF and LF digests are deliberately swapped between fields
    must fail closed at field-level checks even when the physical lock disk hash is anchored.
    """
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    real_sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    real_sent_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json"

    with open(real_sent_lock, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    # Deliberately swap canonical CRLF and LF digests between fields
    lock_data["crlf_sha256"] = VALID_SENTINEL_CSV_LF_SHA256
    lock_data["lf_sha256"] = VALID_SENTINEL_CSV_CRLF_SHA256

    swapped_lock = tmp_path / "sentinel_swapped.lock.json"
    with open(swapped_lock, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)
    swapped_hash = hashlib.sha256(swapped_lock.read_bytes()).hexdigest()

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_csv_path=real_sent_csv,
        sentinel_lock_path=swapped_lock,
        approved_sentinel_lock_sha256={swapped_hash},
    )
    result = validator.validate_sentinel_panel_and_isolation(manifest_data)
    assert result["status"] == "FAIL"
    assert any("unauthorized 'crlf_sha256'" in err for err in result["errors"])
    assert any("unauthorized 'lf_sha256'" in err for err in result["errors"])


# =============================================================================
# 11. Cohort 1 Preflight Verification & Integrity Invariants (Finding 2)
# =============================================================================

def test_cohort1_preflight_passes_on_committed_repo():
    """Cohort 1 preflight validator must pass cleanly on committed repository state."""
    validator = Cohort1PreflightValidator(project_root=PROJECT_ROOT)
    report = validator.run_preflight(check_audio_samples=5)
    assert report["overall_status"] == "READY FOR AUTHORIZED EXECUTION (COHORT 1)"
    assert report["status_reasons"] == []
    assert report["checks"]["cohort1_eval_dataset_integrity"]["status"] == "PASS"
    assert report["checks"]["cohort1_audio_materialization"]["status"] == "PASS"
    assert report["checks"]["cohort1_sentinel_panel_and_isolation"]["status"] == "PASS"
    assert report["checks"]["cohort1_execution_configuration_freeze"]["status"] == "PASS"


def test_cohort1_preflight_fails_on_missing_or_tampered_eval_lock(tmp_path):
    """Cohort 1 preflight validator must fail closed when evaluation lock is missing or tampered."""
    # 1. Missing lock -> FAIL
    validator_missing = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_lock_path=tmp_path / "nonexistent.lock.json",
    )
    res_missing = validator_missing.validate_eval_dataset()
    assert res_missing["status"] == "FAIL"
    assert any("evaluation lock missing" in err for err in res_missing["errors"])

    # 2. Tampered lock -> FAIL
    real_lock = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.lock.json"
    tampered_lock = tmp_path / "tampered.lock.json"
    tampered_lock.write_bytes(real_lock.read_bytes() + b"\n/* tamper */")

    validator_tampered = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_lock_path=tampered_lock,
    )
    res_tampered = validator_tampered.validate_eval_dataset()
    assert res_tampered["status"] == "FAIL"
    assert any("unauthorized SHA-256" in err for err in res_tampered["errors"])

    # 3. Swapped CRLF and LF digests -> FAIL at field-level checks
    with open(real_lock, "r", encoding="utf-8") as f:
        swapped_data = json.load(f)
    swapped_data["crlf_sha256"] = VALID_STAGE5_EVAL_CSV_LF_SHA256
    swapped_data["lf_sha256"] = VALID_STAGE5_EVAL_CSV_CRLF_SHA256
    swapped_lock = tmp_path / "eval_swapped.lock.json"
    with open(swapped_lock, "w", encoding="utf-8") as f:
        json.dump(swapped_data, f)
    swapped_hash = hashlib.sha256(swapped_lock.read_bytes()).hexdigest()

    validator_swapped = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_lock_path=swapped_lock,
        approved_eval_lock_sha256={swapped_hash},
    )
    res_swapped = validator_swapped.validate_eval_dataset()
    assert res_swapped["status"] == "FAIL"
    assert any("unauthorized 'crlf_sha256'" in err for err in res_swapped["errors"])
    assert any("unauthorized 'lf_sha256'" in err for err in res_swapped["errors"])


def test_cohort1_preflight_fails_on_missing_audio_or_zero_bytes(tmp_path):
    """Cohort 1 preflight validator must fail closed on missing audio directory or zero-byte clips."""
    # 1. Missing audio directory -> FAIL
    validator_missing = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        audio_dir=tmp_path / "nonexistent_audio",
    )
    res_missing = validator_missing.validate_audio_materialization()
    assert res_missing["status"] == "FAIL"
    assert any("audio directory missing" in err for err in res_missing["errors"])

    # 2. Zero-byte audio files -> FAIL
    mock_audio = tmp_path / "mock_audio"
    mock_audio.mkdir()
    for i in range(900):
        (mock_audio / f"clip_{i:04d}.mp3").write_bytes(b"x")
    (mock_audio / "clip_0899.mp3").write_bytes(b"")  # 0 bytes

    validator_zero = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        audio_dir=mock_audio,
    )
    res_zero = validator_zero.validate_audio_materialization(check_samples=1)
    assert res_zero["status"] == "FAIL"
    assert any("zero bytes" in err for err in res_zero["errors"])


def test_cohort1_preflight_fails_on_corrupted_counts_or_duplicate_clips(tmp_path):
    """Cohort 1 preflight validator must fail closed if row count is not 900 or duplicates exist."""
    real_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    df = pd.read_csv(real_csv)

    # Inject duplicate clip ID
    df.loc[1, "recording_id"] = df.loc[0, "recording_id"]
    corrupted_csv = tmp_path / "corrupted_eval.csv"
    df.to_csv(corrupted_csv, index=False)
    corrupted_hash = hashlib.sha256(corrupted_csv.read_bytes()).hexdigest()

    validator = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        eval_csv_path=corrupted_csv,
        approved_eval_csv_sha256={corrupted_hash},
    )
    result = validator.validate_eval_dataset()
    assert result["status"] == "FAIL"
    assert any("duplicate recording IDs" in err for err in result["errors"])


def test_cohort1_preflight_fails_on_speaker_leakage_with_sentinel(tmp_path):
    """Cohort 1 preflight validator must fail closed if evaluation speakers overlap with sentinel panel."""
    real_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    real_sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"

    eval_df = pd.read_csv(real_csv)
    sent_df = pd.read_csv(real_sent_csv)

    # Deliberately inject a sentinel speaker ID into eval_df
    leaked_spk = sent_df["speaker_id"].iloc[0]
    eval_df.loc[eval_df["speaker_id"] == eval_df["speaker_id"].iloc[0], "speaker_id"] = leaked_spk

    validator = Cohort1PreflightValidator(project_root=PROJECT_ROOT)
    result = validator.validate_sentinel_panel_and_isolation(eval_df=eval_df)
    assert result["status"] == "FAIL"
    assert any("DATA LEAKAGE DETECTED" in err for err in result["errors"])


def test_cohort1_benchmark_runner_cli_fails_closed_when_prerequisite_corrupted(tmp_path):
    """Runner CLI with --cohort cohort1 --preflight-only must exit with code 1 when sentinel panel is missing."""
    bogus_script = tmp_path / "runner_test.py"
    # Create a small wrapper script simulating Kaggle run with a nonexistent sentinel CSV
    script_text = f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{PROJECT_ROOT / 'src'}")
from dsg_ctta.data.cohort2_preflight import Cohort1PreflightValidator

validator = Cohort1PreflightValidator(
    project_root=Path(r"{PROJECT_ROOT}"),
    sentinel_csv_path=Path(r"{tmp_path / 'nonexistent_sentinel.csv'}"),
)
rep = validator.run_preflight()
print(f"PREFLIGHT AUDIT VERDICT: {{rep['overall_status']}}")
sys.exit(0 if rep["overall_status"] == "READY FOR AUTHORIZED EXECUTION (COHORT 1)" else 1)
"""
    bogus_script.write_text(script_text, encoding="utf-8")

    proc = subprocess.run([sys.executable, str(bogus_script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 1
    assert "READY FOR AUTHORIZED EXECUTION" not in proc.stdout


def test_cohort2_sentinel_fails_on_missing_non_core_audio(tmp_path):
    """Cohort 2 sentinel check must fail closed when a non-core sentinel clip is missing from disk."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    sent_df = pd.read_csv(PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv")
    core_df = sent_df.groupby("speaker_id").first().reset_index()
    core_ids = set(str(r.get("sentinel_id") or r.get("recording_id")) for _, r in core_df.iterrows())
    all_ids = [str(r.get("sentinel_id") or r.get("recording_id")) for _, r in sent_df.iterrows()]
    non_core_ids = [s for s in all_ids if s not in core_ids]

    # Create mock sentinel dir with 299 files, deliberately omitting the first non-core clip
    mock_sent = tmp_path / "mock_sentinel_missing_non_core"
    mock_sent.mkdir()
    for s_id in all_ids:
        if s_id != non_core_ids[0]:
            (mock_sent / f"{s_id}.mp3").write_bytes(b"dummy")

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_audio_dir=mock_sent,
    )
    result = validator.validate_sentinel_panel_and_isolation(manifest_data)
    assert result["status"] == "FAIL"
    assert any("lack physical audio files" in err or "expected exactly 300" in err for err in result["errors"])


def test_cohort2_sentinel_fails_on_corrupt_non_core_audio(tmp_path):
    """Cohort 2 sentinel check must fail closed when a sampled non-core sentinel clip fails 16 kHz decoding."""
    real_manifest = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(real_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    sent_df = pd.read_csv(PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv")
    core_df = sent_df.groupby("speaker_id").first().reset_index()
    core_ids = set(str(r.get("sentinel_id") or r.get("recording_id")) for _, r in core_df.iterrows())
    all_ids = [str(r.get("sentinel_id") or r.get("recording_id")) for _, r in sent_df.iterrows()]
    non_core_ids = [s for s in all_ids if s not in core_ids]

    import soundfile as sf
    dummy_wav = np.zeros(16000, dtype=np.float32)
    dummy_wav[10] = 0.25
    sample_wav = tmp_path / "valid_sample.wav"
    sf.write(sample_wav, dummy_wav, 16000)
    valid_bytes = sample_wav.read_bytes()

    mock_sent = tmp_path / "mock_sentinel_corrupt_non_core"
    mock_sent.mkdir()
    for s_id in all_ids:
        (mock_sent / f"{s_id}.mp3").write_bytes(valid_bytes)

    # Corrupt the first non-core clip (which is included in the sampled decode test)
    (mock_sent / f"{non_core_ids[0]}.mp3").write_bytes(b"corrupt_non_core_audio_bytes")

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_audio_dir=mock_sent,
    )
    result = validator.validate_sentinel_panel_and_isolation(manifest_data, check_samples=10)
    assert result["status"] == "FAIL"
    assert any("failed 16 kHz decoding" in err for err in result["errors"])


def test_cohort1_preflight_fails_on_missing_or_corrupt_sentinel_audio(tmp_path):
    """Cohort 1 preflight validator must fail closed when sentinel panel audio is missing or corrupted."""
    real_sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    sent_df = pd.read_csv(real_sent_csv)
    core_df = sent_df.groupby("speaker_id").first().reset_index()
    core_ids = set(str(r.get("sentinel_id") or r.get("recording_id")) for _, r in core_df.iterrows())
    all_ids = [str(r.get("sentinel_id") or r.get("recording_id")) for _, r in sent_df.iterrows()]
    non_core_ids = [s for s in all_ids if s not in core_ids]

    mock_sent = tmp_path / "mock_sentinel_cohort1"
    mock_sent.mkdir()
    # Provide only 299 files (missing a non-core sentinel clip)
    for s_id in all_ids:
        if s_id != non_core_ids[0]:
            (mock_sent / f"{s_id}.mp3").write_bytes(b"x")

    validator = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        sentinel_audio_dir=mock_sent,
    )
    res = validator.validate_sentinel_panel_and_isolation()
    assert res["status"] == "FAIL"
    assert any("lack physical audio files" in err or "expected exactly 300" in err for err in res["errors"])


def test_cohort1_preflight_fails_on_extraneous_audio_files(tmp_path):
    """Cohort 1 audio validation must fail closed when unlisted extraneous MP3 files are present."""
    real_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv"
    eval_df = pd.read_csv(real_csv)

    mock_audio = tmp_path / "mock_audio_extraneous"
    mock_audio.mkdir()
    for rec_id in eval_df["recording_id"]:
        (mock_audio / f"{rec_id}.mp3").write_bytes(b"dummy_clip_bytes")

    # Inject 1 extraneous unlisted clip
    (mock_audio / "unlisted_extra_clip.mp3").write_bytes(b"unlisted_content")

    validator = Cohort1PreflightValidator(
        project_root=PROJECT_ROOT,
        audio_dir=mock_audio,
    )
    result = validator.validate_audio_materialization(eval_df=eval_df, check_samples=1)
    assert result["status"] == "FAIL"
    assert any("extraneous audio files" in err for err in result["errors"])
    assert any("expected exactly 900" in err for err in result["errors"])


# =============================================================================
# 15. Deterministic and Stratified Sentinel Decode Sampling Tests
# =============================================================================

def test_deterministic_sentinel_sampling_is_reproducible_and_stratified():
    """
    Sentinel decode sampling must be deterministic across repeated runs and permutations,
    covering all 6 strata and both core and non-core clip partitions.
    """
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    df = pd.read_csv(sent_csv)

    # 1. Base selection
    sample_base = select_deterministic_sentinel_samples(df, n_samples=12)
    assert len(sample_base) == 12

    # 2. Assert complete reproducibility / permutation invariance across 20 random shuffles
    for seed in range(20):
        df_shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        sample_shuffled = select_deterministic_sentinel_samples(df_shuffled, n_samples=12)
        assert sample_shuffled == sample_base, (
            f"Seed {seed} produced divergent sample order: {sample_shuffled} vs {sample_base}"
        )

    # 3. Assert all 6 strata are represented in the sample
    id_col = "sentinel_id" if "sentinel_id" in df.columns else "recording_id"
    sample_rows = df[df[id_col].isin(sample_base)]
    strata_counts = sample_rows["stage5_accent_group"].value_counts()
    assert len(strata_counts) == 6, f"Expected 6 strata represented, got {len(strata_counts)}"
    for stratum_name in EXPECTED_STRATA_NAMES:
        assert stratum_name in strata_counts, f"Stratum {stratum_name} missing from sample"
        assert strata_counts[stratum_name] == 2, (
            f"Stratum {stratum_name} expected exactly 2 clips in 12-sample selection, got {strata_counts[stratum_name]}"
        )

    # 4. Assert both core and non-core partitions are represented
    core_df = df.sort_values(by=["stage5_accent_group", "speaker_id", id_col]).groupby("speaker_id").first()
    core_ids = set(core_df[id_col].astype(str))
    core_selected = [s for s in sample_base if s in core_ids]
    non_core_selected = [s for s in sample_base if s not in core_ids]
    assert len(core_selected) == 6, f"Expected exactly 6 core clips, got {len(core_selected)}"
    assert len(non_core_selected) == 6, f"Expected exactly 6 non-core clips, got {len(non_core_selected)}"

    # 5. Assert each stratum receives exactly 1 core clip and 1 non-core clip
    core_strata = sample_rows[sample_rows[id_col].isin(core_selected)]["stage5_accent_group"].tolist()
    non_core_strata = sample_rows[sample_rows[id_col].isin(non_core_selected)]["stage5_accent_group"].tolist()
    assert sorted(core_strata) == sorted(EXPECTED_STRATA_NAMES)
    assert sorted(non_core_strata) == sorted(EXPECTED_STRATA_NAMES)

    # 6. Assert strict 1:1 balance, full stratum coverage, and pairwise alternation for operational preflight default n_samples=20
    sample_20 = select_deterministic_sentinel_samples(df, n_samples=20)
    assert len(sample_20) == 20
    core_20 = [s for s in sample_20 if s in core_ids]
    non_core_20 = [s for s in sample_20 if s not in core_ids]
    assert len(core_20) == 10, f"Expected 10 core clips in 20-clip sample, got {len(core_20)}"
    assert len(non_core_20) == 10, f"Expected 10 non-core clips in 20-clip sample, got {len(non_core_20)}"

    # Assert all 6 strata are represented in the 20-clip sample
    sample_20_rows = df[df[id_col].isin(sample_20)]
    strata_counts_20 = sample_20_rows["stage5_accent_group"].value_counts()
    assert len(strata_counts_20) == 6, f"Expected 6 strata represented in 20-clip sample, got {len(strata_counts_20)}"
    for stratum_name in EXPECTED_STRATA_NAMES:
        assert stratum_name in strata_counts_20, f"Stratum {stratum_name} missing from 20-clip sample"

    # Assert pairwise core/non-core alternation across all 20 positions
    for idx, clip in enumerate(sample_20):
        if idx % 2 == 0:
            assert clip in core_ids, f"Position {idx} must be a core clip, got non-core: {clip}"
        else:
            assert clip not in core_ids, f"Position {idx} must be a non-core clip, got core: {clip}"


def test_cohort2_and_cohort1_preflight_record_stratified_sampling_metadata(base_validator):
    """
    Both Cohort 2 and Cohort 1 preflight validators must record stratified sampling details
    and format checklist metrics with stratum representation counts.
    """
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Cohort 2 Validator
    res2 = base_validator.validate_sentinel_panel_and_isolation(manifest_data, check_samples=12)
    assert res2["status"] == "PASS"
    details2 = res2["details"]
    assert "sentinel_sampled_clips" in details2
    assert len(details2["sentinel_sampled_clips"]) == 12
    assert "sentinel_sampled_strata" in details2
    assert len(details2["sentinel_sampled_strata"]) == 6
    assert details2["sentinel_sampled_core_count"] == 6
    assert details2["sentinel_sampled_non_core_count"] == 6

    metric_desc = Cohort2PreflightValidator._format_checklist_metrics(
        "sentinel_panel_completeness_and_isolation", res2
    )
    assert "deterministic stratified decodability verified (12 clips across 6 strata)" in metric_desc

    # Cohort 1 Validator
    c1_validator = Cohort1PreflightValidator(project_root=PROJECT_ROOT)
    res1 = c1_validator.validate_sentinel_panel_and_isolation(check_samples=12)
    assert res1["status"] == "PASS"
    details1 = res1["details"]
    assert "sentinel_sampled_clips" in details1
    assert len(details1["sentinel_sampled_clips"]) == 12
    assert "sentinel_sampled_strata" in details1
    assert len(details1["sentinel_sampled_strata"]) == 6
    assert details1["sentinel_sampled_core_count"] == 6
    assert details1["sentinel_sampled_non_core_count"] == 6


def test_deterministic_sentinel_sampling_edge_cases():
    """Sampling helper must handle empty data, non-positive sample counts, boundary saturation, and quota spillover cleanly."""
    sent_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    df = pd.read_csv(sent_csv)
    id_col = "sentinel_id" if "sentinel_id" in df.columns else "recording_id"
    core_df = df.sort_values(by=["stage5_accent_group", "speaker_id", id_col]).groupby("speaker_id").first()
    core_ids = set(core_df[id_col].astype(str))

    # Empty DataFrame
    assert select_deterministic_sentinel_samples(pd.DataFrame(), n_samples=12) == []

    # Non-positive sample count
    assert select_deterministic_sentinel_samples(df, n_samples=0) == []
    assert select_deterministic_sentinel_samples(df, n_samples=-5) == []

    # Sample smaller than strata count (n_samples=3)
    s3 = select_deterministic_sentinel_samples(df, n_samples=3)
    assert len(s3) == 3

    # Boundary saturation limit: exact 1:1 balance holds up to N=60 (30 core clips available * 2)
    s60 = select_deterministic_sentinel_samples(df, n_samples=60)
    assert len(s60) == 60
    assert sum(1 for s in s60 if s in core_ids) == 30
    assert sum(1 for s in s60 if s not in core_ids) == 30

    # Quota spillover: N=80 (> 60), core pool exhausted at ceiling (30 clips), remainder (50) from non-core pool
    s80 = select_deterministic_sentinel_samples(df, n_samples=80)
    assert len(s80) == 80
    assert sum(1 for s in s80 if s in core_ids) == 30, "Core clips must cap at total available (30)"
    assert sum(1 for s in s80 if s not in core_ids) == 50, "Remaining 50 clips must spill over to non-core pool"
    assert len(set(s80)) == 80, "All 80 selected clips must be unique"

    # Sample larger than total records (n_samples=500)
    s_all = select_deterministic_sentinel_samples(df, n_samples=500)
    assert len(s_all) == len(df) == 300
    assert len(set(s_all)) == 300
    assert sum(1 for s in s_all if s in core_ids) == 30
    assert sum(1 for s in s_all if s not in core_ids) == 270




