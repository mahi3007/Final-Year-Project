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
    Cohort2PreflightValidator,
    VALID_MANIFEST_SHA256,
    EXPECTED_STRATA_NAMES,
    CORE_SENTINEL_WORDS,
    CORE_SENTINEL_CLIPS,
    CORE_SENTINEL_SPEAKERS,
    EXPECTED_UNCERTAINTY_FLOOR_PP,
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


def test_cohort2_eval_csv_agreement_passes_on_valid_matching_data(tmp_path):
    """When CSV exactly matches manifest, agreement check must pass."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, eval_csv_path=csv_path)
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "PASS"
    assert result["details"]["total_clips"] == 7020
    assert result["details"]["unique_speakers"] == 468
    assert result["details"]["duplicate_clip_count"] == 0
    assert result["details"]["manifest_prefix_match_rate_pct"] == 100.0


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

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, eval_csv_path=csv_path)
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

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, eval_csv_path=csv_path)
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

    # 1. Generate matching CSV
    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

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
        eval_csv_path=csv_path,
        audio_dir=audio_dir,
        sentinel_csv_path=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv",
        sentinel_lock_path=PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.lock.json",
        sentinel_audio_dir=PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio",
    )

    report = validator.run_preflight(check_audio_samples=5)
    assert report["overall_status"] == "READY FOR AUTHORIZED EXECUTION"
    assert report["status_reasons"] == []
    assert report["checks"]["manifest_integrity_and_schema"]["status"] == "PASS"
    assert report["checks"]["evaluation_csv_manifest_agreement"]["status"] == "PASS"
    assert report["checks"]["audio_materialization_and_decodability"]["status"] == "PASS"
    assert report["checks"]["sentinel_panel_completeness_and_isolation"]["status"] == "PASS"
    assert report["checks"]["execution_configuration_freeze"]["status"] == "PASS"


def test_cohort2_benchmark_runner_preflight_only_cli():
    """Verify that runner CLI with --preflight-only runs cleanly and exits with code 1 under current HOLD."""
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "cloud" / "kaggle" / "run_stage6m_cohort2_benchmark.py"),
        "--cohort",
        "cohort2",
        "--preflight-only",
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

    validator = Cohort2PreflightValidator(project_root=PROJECT_ROOT, eval_csv_path=csv_path)
    result = validator.validate_eval_csv(manifest_data)
    assert result["status"] == "FAIL"
    assert any("Speaker stratum preservation violation" in err for err in result["errors"])


def test_cohort2_eval_csv_clip_lock_exact_set_equality(tmp_path):
    """Clip lock file must enforce exact clip-set equality with evaluation CSV."""
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    df = _generate_synthetic_cohort2_df(manifest_data)
    csv_path = tmp_path / "stage6m_cohort2_audio.csv"
    df.to_csv(csv_path, index=False)

    # 1. Matching clip lock -> PASS
    clip_lock_path = tmp_path / "stage6m_cohort2_audio.lock.json"
    all_rec_ids = list(df["recording_id"])
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump({"recording_ids": all_rec_ids}, f)

    validator = Cohort2PreflightValidator(
        project_root=PROJECT_ROOT, eval_csv_path=csv_path, clip_lock_path=clip_lock_path
    )
    res_pass = validator.validate_eval_csv(manifest_data)
    assert res_pass["status"] == "PASS"
    assert res_pass["details"]["clip_lock_verified"] is True

    # 2. Mismatched clip lock (omit one clip ID, add one bogus ID) -> FAIL
    all_rec_ids_tampered = all_rec_ids[:-1] + ["bogus_extra_clip_99999"]
    with open(clip_lock_path, "w", encoding="utf-8") as f:
        json.dump({"recording_ids": all_rec_ids_tampered}, f)

    res_fail = validator.validate_eval_csv(manifest_data)
    assert res_fail["status"] == "FAIL"
    assert any("Clip-set exact equality failed" in err for err in res_fail["errors"])


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

def test_cohort2_markdown_report_avoids_contradictory_claims_under_hold(base_validator, tmp_path):
    """
    Under HOLD, the checklist matrix must state that validation could not be completed
    and never claim completed decodability or clip counts.
    """
    report = base_validator.run_preflight()
    assert report["overall_status"] == "HOLD"

    _, md_p = base_validator.save_reports(report, output_dir=tmp_path)
    md_text = md_p.read_text(encoding="utf-8")

    # Positive assertions: must state validation could not be completed
    assert "Validation could not be completed: evaluation CSV not materialized on disk (prerequisite missing)." in md_text
    assert "Validation could not be completed: physical audio files not materialized" in md_text

    # Negative assertions: must NOT make false success claims
    assert "7,020 physical 16 kHz audio files materialized and decodable" not in md_text
    assert "0 duplicate clip IDs; 7,020 clips (1,170/stratum); prefix mapping complete." not in md_text

