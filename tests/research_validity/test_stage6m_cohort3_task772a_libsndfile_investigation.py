"""
Research validity test suite for Stage 6M Task 7.7.2A: libsndfile / mpg123 duration estimation investigation.

Verifies:
1. Investigation report deliverables exist and conform to governance structure.
2. 100% of the 130 quarantined recordings are mathematically explained by the mpg123 file-size formula (individual residual = 0).
3. Representative recording (common_voice_en_21552119.mp3) discrepancy is decomposed with 0 residual.
4. Controlled synthetic matrix proves ID3v2 tag inflation and Xing header authority.
5. Invariant boundaries, provisional manifest, and frozen production validator remain untouched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_JSON = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_task772a_libsndfile_investigation.json"
REPORT_MD = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_task772a_libsndfile_investigation.md"
TRIAGE_JSON = PROJECT_ROOT / "reports" / "stage6m" / "stage6m_cohort3_task771_mp3_forensic_triage.json"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "task772a_synthetic"


def test_investigation_deliverables_exist():
    assert REPORT_JSON.exists(), f"Missing investigation JSON report at {REPORT_JSON}"
    assert REPORT_MD.exists(), f"Missing investigation Markdown report at {REPORT_MD}"
    assert REPORT_JSON.stat().st_size > 1000
    assert REPORT_MD.stat().st_size > 1000


def test_investigation_report_structure():
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["task_id"] == "Task 7.7.2A"
    assert data["document_id"] == "STAGE6M-TASK772A-LIBSNDFILE-INVESTIGATION"
    assert data["investigation_conclusions"]["root_cause_established"] is True
    assert "runtime_environments" in data
    assert "representative_recording_analysis" in data
    assert "controlled_synthetic_experiment_matrix" in data
    assert "quarantined_130_recordings_analysis" in data
    assert "malformed_metadata_investigation" in data
    assert "mid_frame_truncation_investigation" in data
    assert "protected_file_invariants" in data
    assert "scientific_limitations_claim_a_vs_claim_b" in data
    assert "synthetic_fixture_inventory" in data
    assert len(data["synthetic_fixture_inventory"]) == 11

    # Verify provenance qualification
    prov = data["runtime_environments"]["provenance_status"]
    assert prov["runtime_dll_identity"] == "verified"
    assert prov["static_linkage"] == "strongly supported"
    assert prov["exact_mpg123_source_revision_and_binary_correspondence"] == "partially verified"

    # Verify Case 7 qualified explanation
    c7_evidence = data["mid_frame_truncation_investigation"]["decoding_analysis"]["pyav_packet_and_decode_evidence"]
    assert c7_evidence["final_packet_size_supplied_to_libavcodec_bytes"] == 109
    assert "unresolved_decoder_mechanism_status" in c7_evidence
    assert "conclusively established" in c7_evidence["unresolved_decoder_mechanism_status"].lower()

    # Verify Case 6a numerical reconciliation and terminology
    c6a_rec = data["malformed_metadata_investigation"]["case6a_zero_frame_count"]["pyav_numerical_reconciliation"]
    assert c6a_rec["soundfile_vs_pyav_difference"] == 1105
    assert c6a_rec["lame_encoder_delay_samples"] == 576
    assert c6a_rec["decoder_filterbank_delay_samples"] == 529
    assert c6a_rec["total_start_skip_samples"] == 1105
    assert c6a_rec["first_decoded_audio_frame_retained_samples"] == 47
    assert c6a_rec["frame_0_decoded_samples"] == 47
    assert "physical MPEG Frame 1" in c6a_rec["frame_origin_clarification"]

    # Verify Case 6b FFmpeg control flow and packet positions
    c6b_meta = data["malformed_metadata_investigation"]["case6b_invalid_magic"]["pyav_demuxer_and_decode_mechanism"]
    assert c6b_meta["packet_0_start_file_pos"] == 208
    assert c6b_meta["malformed_marker"]["magic_bytes"] == "Xung"
    assert c6b_meta["malformed_marker"]["byte_offset_in_file"] == 36
    assert c6b_meta["ffmpeg_control_flow"]["vbr_tags_parser_return_code"] == -1
    assert c6b_meta["ffmpeg_control_flow"]["vbr_tags_seek_restored"] is True
    assert c6b_meta["ffmpeg_control_flow"]["first_physical_mpeg_frame_omitted"] is True

    # Verify DLL size reconciliation
    assert data["runtime_environments"]["libsndfile_dll_size_bytes"] == 2364416
    assert data["runtime_environments"]["libsndfile_dll_sha256"] == "22518c16f9d13eda5ae5adf999c4740d7d16cc2d6b178b36dd4ac2f759a38559"

    # Verify protected file inventory checks
    acq_prot = data["protected_file_invariants"]["acquisition_ledger"]
    assert acq_prot["matches_baseline_lf"] is True
    assert acq_prot["matches_baseline_crlf"] is True
    assert acq_prot["audio_clips_cryptographically_verified"] == 18845
    assert data["protected_file_invariants"]["quarantine_ledger"]["audio_clips_cryptographically_verified"] == 130


def test_representative_recording_mathematical_decomposition():
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    rep = data["representative_recording_analysis"]
    assert rep["clip_filename"] == "common_voice_en_21552119.mp3"
    assert rep["file_sha256"] == "b4f61be7a96876958890f364a8c42beb7c39a0e845a3ad9b13964330ed569613"
    assert rep["sample_rate_hz"] == 44100
    assert rep["physical_mpeg_frames"] == 186
    assert rep["physical_pcm_capacity_samples"] == 214272
    assert rep["soundfile_declared_frames"] == 216249
    assert rep["soundfile_actual_decoded_samples"] == 214272
    assert rep["pyav_decoded_samples"] == 214272
    assert rep["miniaudio_decoded_samples"] == 214272
    assert rep["discrepancy_samples"] == 1977
    assert abs(rep["discrepancy_duration_ms"] - 44.83) < 0.05

    decomp = rep["exact_root_cause_decomposition"]
    assert decomp["id3v2_tag_contribution_samples"] == 969
    assert decomp["audio_padding_rounding_contribution_samples"] == 1008
    assert decomp["reconciled_total_spurious_samples"] == 1977
    assert decomp["residual_unexplained_samples"] == 0


def test_130_quarantined_recordings_100_percent_formula_match():
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    q = data["quarantined_130_recordings_analysis"]
    assert q["total_quarantined_recordings"] == 130
    assert q["count_64kbps_44100hz"] == 78
    assert q["count_48kbps_32000hz"] == 52
    assert q["count_other"] == 0
    assert q["total_formula_matches"] == 130
    assert q["formula_match_rate_percent"] == 100.0

    # Verify per-recording individual formula reconciliation evidence
    assert "per_recording_formula_reconciliation" in q
    recs = q["per_recording_formula_reconciliation"]
    assert len(recs) == 130
    assert all(r["residual"] == 0 for r in recs)
    assert all(r["formula_exact_match"] is True for r in recs)

    # Verify branch evaluation
    cond = q["source_code_conditional"]
    assert cond["mean_framesize_at_call"] == 0.0
    assert cond["active_branch"] == "compute_bpf(mh)"
    assert cond["selected_bpf_64kbps_44100hz"] == 208.0
    assert cond["selected_bpf_48kbps_32000hz"] == 216.0


def test_synthetic_matrix_id3_inflation_invariance():
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    syn = {c["case_id"]: c for c in data["controlled_synthetic_experiment_matrix"]}

    # Baseline headerless CBR
    c1 = syn["case1_cbr_headerless_no_id3"]
    # Tagged variants
    c2_128 = syn["case2_cbr_id3_128b"]
    c2_1024 = syn["case2_cbr_id3_1024b"]
    c2_4096 = syn["case2_cbr_id3_4096b"]

    # Invariance check: actual decoded samples across all 3 decoders must remain invariant
    assert (
        c1["soundfile_actual_decoded_samples"]
        == c2_128["soundfile_actual_decoded_samples"]
        == c2_1024["soundfile_actual_decoded_samples"]
        == c2_4096["soundfile_actual_decoded_samples"]
    )
    assert (
        c1["pyav_decoded_samples"]
        == c2_128["pyav_decoded_samples"]
        == c2_1024["pyav_decoded_samples"]
        == c2_4096["pyav_decoded_samples"]
    )

    # Sensitivity check: SoundFile declared frames must grow strictly with tag size
    assert (
        c1["soundfile_declared_frames"]
        < c2_128["soundfile_declared_frames"]
        < c2_1024["soundfile_declared_frames"]
        < c2_4096["soundfile_declared_frames"]
    )


def test_synthetic_matrix_xing_header_authority():
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    syn = {c["case_id"]: c for c in data["controlled_synthetic_experiment_matrix"]}

    # Valid Info frame cases must have zero shortfall
    assert syn["case3_cbr_valid_info_frame"]["shortfall_declared_vs_decoded"] == 0
    assert syn["case4_vbr_valid_info_frame"]["shortfall_declared_vs_decoded"] == 0
    assert syn["case3_cbr_valid_info_frame"]["soundfile_declared_frames"] == 88200
    assert syn["case4_vbr_valid_info_frame"]["soundfile_declared_frames"] == 88200

    # VBR without Info frame must fall back to first-frame bitrate estimation
    assert syn["case5_vbr_no_info_frame"]["shortfall_declared_vs_decoded"] > 0
    assert syn["case5_vbr_no_info_frame"]["soundfile_declared_frames"] == 90060


def test_production_constraints_preserved():
    # Production validator script must remain unchanged
    validator_path = PROJECT_ROOT / "scripts" / "materialize_stage6m_cohort3_audio.py"
    assert validator_path.exists()
    content = validator_path.read_text(encoding="utf-8")
    assert "MAX_MP3_PADDING_FRAMES = 1152" in content
    assert "def validate_audio_file" in content

    # Provisional manifest must exist and match approved digest
    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_provisional_manifest.json"
    assert manifest_path.exists()
    h = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert h == "b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547"

    # Acquisition and quarantine ledgers must exist and match baseline digests
    quar_ledger_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_quarantine_ledger.csv"
    assert quar_ledger_path.exists()
    assert hashlib.sha256(quar_ledger_path.read_bytes()).hexdigest() == "98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8"

    acq_ledger_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_cohort3_clip_sha256_ledger.csv"
    assert acq_ledger_path.exists()
    assert hashlib.sha256(acq_ledger_path.read_bytes()).hexdigest() == "63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5"
