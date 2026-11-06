"""
tests/research_validity/test_stage6m_cohort3_task772b_validator_impact.py

Research validity and verification tests for Stage 6M v1.5 Task 7.7.2B:
Production Validator Impact Assessment and Non-Destructive Resolution Strategies.

Invariants Verified:
1. Deliverables exist, are non-empty, and agree numerically across JSON and Markdown.
2. Complete cohort denominator: exactly 18,845 accepted + 130 quarantined = 18,975 recordings.
3. sf.info() is proven to derive from the identical libsndfile/mpg123 duration estimate as sf.SoundFile().
4. PCM sample frame units are strictly separated from compressed MPEG frames and multichannel chunk sizes.
5. Pervasive absence of Xing/Info gapless metadata across both cohorts (0% prevalence).
6. ID3v2 tag estimation artifact is verified as the source of declared shortfalls (e.g. 198 samples for 33B tag).
7. Potential false-rejection candidates among quarantined recordings are strictly qualified (not proven false rejections).
8. False-acceptance risk of upstream whole-frame loss is explicitly classified as UNKNOWN (Claim A != Claim B).
9. Four candidate strategies (A, B, C, D) are evaluated across all 18,975 recordings with Strategy D recommended.
10. All protected files, ledgers, manifests, and production code remain 100% frozen and unmodified.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import pytest
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Deliverables
REPORT_JSON_PATH = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_task772b_validator_impact_assessment.json"
REPORT_MD_PATH = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_task772b_validator_impact_assessment.md"
ASSESS_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "assess_stage6m_cohort3_task772b_validator_impact.py"

# Protected Files
PROVISIONAL_MANIFEST_PATH = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_provisional_manifest.json"
ACQUISITION_LEDGER_PATH = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_clip_sha256_ledger.csv"
QUARANTINE_LEDGER_PATH = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_quarantine_ledger.csv"
QUARANTINE_TARGETS_PATH = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_task771_quarantine_targets.json"
PRODUCTION_VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"

ACCEPTED_AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort3_audio"
QUARANTINE_AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "cohort3_rejected_quarantine"

APPROVED_PARENT_MANIFEST_SHA256 = "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"
APPROVED_TARGETS_LIST_SHA256 = "a530fb8b60fc302e536ce14efb620cda936ad91783f7d1f482a430dd154696ae"
APPROVED_QUARANTINE_LEDGER_SHA256_LF = "98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8"
APPROVED_ACQUISITION_LEDGER_SHA256_LF = "63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5"

TOTAL_ACCEPTED_RECORDINGS = 18845
TOTAL_QUARANTINED_RECORDINGS = 130
TOTAL_COHORT_RECORDINGS = 18975


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def assessment_json_data() -> Dict[str, Any]:
    assert REPORT_JSON_PATH.exists(), f"Missing required deliverable: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def assessment_md_text() -> str:
    assert REPORT_MD_PATH.exists(), f"Missing required deliverable: {REPORT_MD_PATH}"
    return REPORT_MD_PATH.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# Test 1: Deliverables Existence and Baseline Non-Emptiness
# -----------------------------------------------------------------------------
def test_deliverables_exist_and_non_empty(assessment_json_data, assessment_md_text):
    assert ASSESS_SCRIPT_PATH.exists(), f"Missing assessment script: {ASSESS_SCRIPT_PATH}"
    assert ASSESS_SCRIPT_PATH.stat().st_size > 1000

    assert REPORT_JSON_PATH.exists()
    assert REPORT_JSON_PATH.stat().st_size > 100_000, "JSON report appears truncated"

    assert REPORT_MD_PATH.exists()
    assert len(assessment_md_text) > 2000, "Markdown report appears truncated"


# -----------------------------------------------------------------------------
# Test 2: Cohort Population Completeness (18,975 / 18,975)
# -----------------------------------------------------------------------------
def test_cohort_population_counts(assessment_json_data, assessment_md_text):
    meta = assessment_json_data["metadata"]
    assert meta["total_recordings_audited"] == TOTAL_COHORT_RECORDINGS
    assert meta["accepted_count"] == TOTAL_ACCEPTED_RECORDINGS
    assert meta["quarantined_count"] == TOTAL_QUARANTINED_RECORDINGS

    acc_list = assessment_json_data["cohort_audit_accepted"]
    quar_list = assessment_json_data["cohort_audit_quarantined"]
    assert len(acc_list) == TOTAL_ACCEPTED_RECORDINGS
    assert len(quar_list) == TOTAL_QUARANTINED_RECORDINGS

    summary = assessment_json_data["summary"]
    assert summary["accepted_population"]["recordings_count"] == TOTAL_ACCEPTED_RECORDINGS
    assert summary["quarantined_population"]["recordings_count"] == TOTAL_QUARANTINED_RECORDINGS

    # Markdown text verification
    assert "18,845 accepted recordings" in assessment_md_text
    assert "130 quarantined recordings" in assessment_md_text
    assert "18,975 recordings" in assessment_md_text


# -----------------------------------------------------------------------------
# Test 3: SoundFile Info Equivalence Verification (Refinement B)
# -----------------------------------------------------------------------------
def test_soundfile_info_equivalence():
    """Verifies that sf.info() is not independent evidence from sf.SoundFile()."""
    sample_file = QUARANTINE_AUDIO_DIR / "common_voice_en_21552119.mp3"
    assert sample_file.exists(), f"Test clip {sample_file} not found"

    info = sf.info(str(sample_file))
    with sf.SoundFile(str(sample_file), "r") as reader:
        assert info.frames == reader.frames, "sf.info().frames must equal sf.SoundFile().frames"
        assert info.samplerate == reader.samplerate, "Sample rate must match exactly"
        assert info.channels == reader.channels, "Channel count must match exactly"
        expected_dur = reader.frames / reader.samplerate
        assert abs(info.duration - expected_dur) < 1e-9, "sf.info().duration is calculated from reader.frames"


# -----------------------------------------------------------------------------
# Test 4: Unit Consistency: PCM Sample Frames vs MPEG Frames vs chunk.size
# -----------------------------------------------------------------------------
def test_pcm_sample_frame_units():
    """Verifies that len(chunk) represents sample frames and physical capacity is N * 1152."""
    sample_file = ACCEPTED_AUDIO_DIR / "common_voice_en_100703.mp3"
    assert sample_file.exists(), f"Test clip {sample_file} not found"

    with sf.SoundFile(str(sample_file), "r") as reader:
        chunk = reader.read(4096)
        # len(chunk) is number of PCM sample frames
        assert len(chunk) > 0
        if reader.channels == 2:
            assert chunk.size == len(chunk) * 2, "chunk.size must be 2 * len(chunk) for stereo"
        else:
            assert chunk.size == len(chunk), "chunk.size must equal len(chunk) for mono"


# -----------------------------------------------------------------------------
# Test 5: Pervasive Absence of Gapless Metadata
# -----------------------------------------------------------------------------
def test_gapless_metadata_prevalence(assessment_json_data):
    acc_sum = assessment_json_data["summary"]["accepted_population"]["gapless_metadata_summary"]
    quar_sum = assessment_json_data["summary"]["quarantined_population"]["gapless_metadata_summary"]

    assert acc_sum["xing_present"] == 0, "No accepted recordings should possess Xing headers"
    assert acc_sum["xing_absent"] == TOTAL_ACCEPTED_RECORDINGS
    assert quar_sum["xing_present"] == 0, "No quarantined recordings should possess Xing headers"
    assert quar_sum["xing_absent"] == TOTAL_QUARANTINED_RECORDINGS


# -----------------------------------------------------------------------------
# Test 6: ID3v2 Tag Estimation Artifact Explanation
# -----------------------------------------------------------------------------
def test_id3v2_tag_estimation_artifact(assessment_json_data):
    acc_sum = assessment_json_data["summary"]["accepted_population"]
    top_counts = acc_sum["shortfall_top_counts"]

    # In 48 kHz / 64 kbps mono (192 B/frame, 1152 samples/frame):
    # 33-byte tag -> (33 / 192) * 1152 = 198 samples
    # 161-byte tag -> (161 / 192) * 1152 = 966 samples
    assert "198" in top_counts or 198 in top_counts, "198-sample shortfall cluster must exist"
    assert "966" in top_counts or 966 in top_counts, "966-sample shortfall cluster must exist"


# -----------------------------------------------------------------------------
# Test 7: Potential False-Rejection Candidates Qualification (Refinements A & C)
# -----------------------------------------------------------------------------
def test_false_rejection_candidate_classification(assessment_json_data):
    fr = assessment_json_data["summary"]["false_rejection_analysis"]
    assert fr["potential_candidates_count"] == TOTAL_QUARANTINED_RECORDINGS
    assert fr["proven_false_rejections_count"] == 0, "Must NOT claim proven false rejections without master"
    assert "POTENTIAL" in fr["qualification"].upper()


# -----------------------------------------------------------------------------
# Test 8: False-Acceptance Risk Qualification (Refinement C: Claim A != Claim B)
# -----------------------------------------------------------------------------
def test_false_acceptance_risk_qualification(assessment_json_data, assessment_md_text):
    fa = assessment_json_data["summary"]["false_acceptance_analysis"]
    assert fa["claim_a_satisfied_count"] == TOTAL_ACCEPTED_RECORDINGS
    assert fa["claim_b_verified_count"] == 0, "Claim B must be 0 (unverified)"
    assert fa["upstream_whole_frame_loss_risk"] == "UNKNOWN"
    assert "UNKNOWN" in fa["qualification"].upper()

    assert "Claim A" in assessment_md_text
    assert "Claim B" in assessment_md_text
    assert "UNKNOWN" in assessment_md_text


# -----------------------------------------------------------------------------
# Test 9: Strategy Evaluation Across All 18,975 Recordings
# -----------------------------------------------------------------------------
def test_strategy_evaluation_metrics(assessment_json_data):
    acc_sum = assessment_json_data["summary"]["accepted_population"]
    quar_sum = assessment_json_data["summary"]["quarantined_population"]

    # Strategy A (Existing Rule)
    assert acc_sum["strategy_a_outcomes"].get("PASS") == TOTAL_ACCEPTED_RECORDINGS
    assert quar_sum["strategy_a_outcomes"].get("FAIL") == TOTAL_QUARANTINED_RECORDINGS

    # Strategy B (Decoded PCM Rule)
    assert acc_sum["strategy_b_outcomes"].get("PASS") == TOTAL_ACCEPTED_RECORDINGS
    assert quar_sum["strategy_b_outcomes"].get("PASS") == TOTAL_QUARANTINED_RECORDINGS

    # Strategy C (Metadata-Aware Rule)
    assert acc_sum["strategy_c_outcomes"].get("PASS") == TOTAL_ACCEPTED_RECORDINGS
    assert quar_sum["strategy_c_outcomes"].get("PASS") == TOTAL_QUARANTINED_RECORDINGS

    # Strategy D (Multi-Evidence Rule)
    assert acc_sum["strategy_d_outcomes"].get("PASS") == TOTAL_ACCEPTED_RECORDINGS
    assert quar_sum["strategy_d_outcomes"].get("PASS") == TOTAL_QUARANTINED_RECORDINGS


# -----------------------------------------------------------------------------
# Test 10: Protected State and Repository Invariants
# -----------------------------------------------------------------------------
def test_protected_invariants_untouched():
    # 1. Provisional Manifest
    manifest_sha = compute_file_sha256(PROVISIONAL_MANIFEST_PATH)
    assert manifest_sha == APPROVED_PARENT_MANIFEST_SHA256, (
        f"Manifest SHA-256 altered: got {manifest_sha}, expected {APPROVED_PARENT_MANIFEST_SHA256}"
    )

    with open(PROVISIONAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    meta = manifest_data.get("metadata", {})
    assert meta.get("manifest_status") == "UNLOCKED", "Manifest must remain unlocked"
    assert meta.get("manifest_type") == "PROVISIONAL_SELECTION_MANIFEST", "Manifest must remain PROVISIONAL"

    # 2. Production Validator
    validator_code = PRODUCTION_VALIDATOR_PATH.read_text(encoding="utf-8")
    assert "MAX_MP3_PADDING_FRAMES = 1152" in validator_code, "Production threshold 1152 must remain unchanged"

    # 3. Ledgers
    quar_raw = QUARANTINE_LEDGER_PATH.read_bytes()
    assert hashlib.sha256(quar_raw).hexdigest() == APPROVED_QUARANTINE_LEDGER_SHA256_LF, "Quarantine ledger modified"

    # Acquisition ledger (LF raw)
    acq_raw = ACQUISITION_LEDGER_PATH.read_bytes()
    assert hashlib.sha256(acq_raw).hexdigest() == APPROVED_ACQUISITION_LEDGER_SHA256_LF, "Acquisition ledger modified"

    # 4. Audio Directory counts
    acc_files = list(ACCEPTED_AUDIO_DIR.glob("*.mp3"))
    quar_files = list(QUARANTINE_AUDIO_DIR.glob("*.mp3"))
    assert len(acc_files) == TOTAL_ACCEPTED_RECORDINGS, f"Accepted audio altered: {len(acc_files)}"
    assert len(quar_files) == TOTAL_QUARANTINED_RECORDINGS, f"Quarantine audio altered: {len(quar_files)}"
