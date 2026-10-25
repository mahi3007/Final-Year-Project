"""
src/dsg_ctta/data/cohort2_preflight.py

Stage 6M Confirmatory Cohort 2 Preflight Readiness & Integrity Validator.
========================================================================
Governing Standard: ADR-005 (Amended via AMENDMENT-001)
Protocol Version: v1.3.4-stage6m-self-authorization-amendment

Performs exhaustive preflight validation before any GPU compute is spent:
1. Locked Manifest Integrity: Validates SHA-256 against lock, schema (6 strata, 468 speakers,
   78/stratum, 15 clips/speaker), and Option 1B Irish reserve tiers.
2. Manifest <-> CSV Agreement: Asserts exact agreement between manifest active speakers and
   evaluation CSV clip IDs, zero duplicate clip IDs, exact strata counts (1,170 clips/stratum),
   and zero missing/orphan speakers.
3. Audio Materialization: Verifies existence, read/decode integrity, and 16 kHz resampling.
   Fails closed to MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD when physical audio is not materialized.
4. Sentinel Panel Completeness & Speaker Isolation: Validates 30 core sentinel clips (281 words,
   uncertainty floor = 0.3559 pp), audio decodability, and strictly disjoint speaker sets (zero exposure).
5. Frozen Execution Configuration: Freezes model, protocol, Lan-DeMets OBF alpha spending, gate
   thresholds, uncertainty floor, hardware environment, and runtime budget.

Produces auditable JSON and Markdown readiness reports in reports/stage6m/.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import torch

from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.data.normalization import TextNormalizer


# Canonical Manifest Digests
VALID_MANIFEST_CRLF_SHA256 = "610649e8f634e21c0236f18e9461f865721c7864703fb87d597df7968f912895"
VALID_MANIFEST_LF_SHA256 = "2e59a75c40abd165ee1689773c1a95409be29636079c0f714d51236dd54dcef0"
VALID_MANIFEST_SHA256 = {VALID_MANIFEST_CRLF_SHA256, VALID_MANIFEST_LF_SHA256}

# Canonical Manifest Lock Digests
VALID_MANIFEST_LOCK_CRLF_SHA256 = "3b00d31140488ad614e175c3585130af50c07677a89ef5630a6feea5e28b6c64"
VALID_MANIFEST_LOCK_LF_SHA256 = "9081c40cb31e8c6ff8a6925b49b26a95e83c030f356131ef4066273a90475330"
VALID_MANIFEST_LOCK_SHA256 = {VALID_MANIFEST_LOCK_CRLF_SHA256, VALID_MANIFEST_LOCK_LF_SHA256}

# Canonical Sentinel Panel CSV Digests
VALID_SENTINEL_CSV_CRLF_SHA256 = "665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543"
VALID_SENTINEL_CSV_LF_SHA256 = "612b7045e3e68326d00a963f9ade44b197a53e2c2640a13f8ee5162b2efc3691"
VALID_SENTINEL_CSV_SHA256 = {VALID_SENTINEL_CSV_CRLF_SHA256, VALID_SENTINEL_CSV_LF_SHA256}

# Canonical Sentinel Panel Lock Digests
VALID_SENTINEL_LOCK_CRLF_SHA256 = "4792ce49cc0e5a5c588f6e30cf0cee6b7a512fabdae6dadee117912927ec167d"
VALID_SENTINEL_LOCK_LF_SHA256 = "5e2ea1709ab9ab8031e82f4a5513538d6653d1cf11594ff437860a1eb3a58980"
VALID_SENTINEL_LOCK_SHA256 = {VALID_SENTINEL_LOCK_CRLF_SHA256, VALID_SENTINEL_LOCK_LF_SHA256}

# Canonical Stage 5 External Evaluation (Cohort 1) CSV Digests
VALID_STAGE5_EVAL_CSV_CRLF_SHA256 = "41cec79d913a96aae40d8c275340b28be4dee1d4be959940a80cde2c9128fd32"
VALID_STAGE5_EVAL_CSV_LF_SHA256 = "56cb4f9fc7ab7b8b959a65d19f195d9d8b1751a6bca26f474a6304dd47559093"
VALID_STAGE5_EVAL_CSV_SHA256 = {VALID_STAGE5_EVAL_CSV_CRLF_SHA256, VALID_STAGE5_EVAL_CSV_LF_SHA256}

# Canonical Stage 5 External Evaluation (Cohort 1) Lock Digests
VALID_STAGE5_EVAL_LOCK_CRLF_SHA256 = "194a95f7303038775321ef58298d611cfcf83021f34a5cd31bc39c37d066d309"
VALID_STAGE5_EVAL_LOCK_LF_SHA256 = "5c589e637ef04eb02f6b1fa0242f8838c563e51a82b6f0e81fb039c67dc1be2f"
VALID_STAGE5_EVAL_LOCK_SHA256 = {VALID_STAGE5_EVAL_LOCK_CRLF_SHA256, VALID_STAGE5_EVAL_LOCK_LF_SHA256}

# Cohort 2 Clip Lock Allowlist (empty by default until committed/approved)
VALID_COHORT2_CLIP_LOCK_SHA256: Set[str] = set()

EXPECTED_STRATA_NAMES = [
    "Irish English",
    "England English",
    "Canadian English",
    "Australian English",
    "South Asian English",
    "US English",
]

CORE_SENTINEL_WORDS = 281
CORE_SENTINEL_CLIPS = 30
CORE_SENTINEL_SPEAKERS = 30
EXPECTED_UNCERTAINTY_FLOOR_PP = round(100.0 / CORE_SENTINEL_WORDS, 4)  # 0.3559 pp


def compute_sha256(filepath: Path | str) -> str:
    """Compute hex SHA-256 digest of file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_revision(project_root: Path) -> str:
    """Retrieve current Git commit SHA."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(project_root), stderr=subprocess.DEVNULL
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "UNKNOWN_OR_UNTRACKED"


class Cohort2PreflightValidator:
    """
    Exhaustive preflight validator for Stage 6M Cohort 2 confirmatory benchmark.
    Guarantees fail-closed behavior before allocating compute resources.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        manifest_path: Optional[Path] = None,
        lock_path: Optional[Path] = None,
        clip_lock_path: Optional[Path] = None,
        eval_csv_path: Optional[Path] = None,
        audio_dir: Optional[Path] = None,
        sentinel_csv_path: Optional[Path] = None,
        sentinel_lock_path: Optional[Path] = None,
        sentinel_audio_dir: Optional[Path] = None,
        approved_manifest_sha256: Optional[Set[str]] = None,
        approved_manifest_lock_sha256: Optional[Set[str]] = None,
        approved_sentinel_csv_sha256: Optional[Set[str]] = None,
        approved_sentinel_lock_sha256: Optional[Set[str]] = None,
        approved_clip_lock_sha256: Optional[Set[str]] = None,
        expected_manifest_crlf_sha256: Optional[str] = None,
        expected_manifest_lf_sha256: Optional[str] = None,
        expected_sentinel_csv_crlf_sha256: Optional[str] = None,
        expected_sentinel_csv_lf_sha256: Optional[str] = None,
    ):
        self.root = project_root or Path(__file__).resolve().parent.parent.parent.parent
        self.manifest_path = manifest_path or (self.root / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json")
        self.lock_path = lock_path or (self.root / "datasets" / "splits" / "stage6m_locked_candidate_manifest.lock.json")
        self.clip_lock_path = clip_lock_path or (self.root / "datasets" / "splits" / "stage6m_cohort2_audio.lock.json")
        self.eval_csv_path = eval_csv_path or (self.root / "datasets" / "splits" / "stage6m_cohort2_audio.csv")
        self.audio_dir = audio_dir or (self.root / "datasets" / "external" / "common_voice_27" / "cohort2_audio")
        self.sentinel_csv_path = sentinel_csv_path or (self.root / "datasets" / "splits" / "stage5_sentinel_panel.csv")
        self.sentinel_lock_path = sentinel_lock_path or (self.root / "datasets" / "splits" / "stage5_sentinel_panel.lock.json")
        self.sentinel_audio_dir = sentinel_audio_dir or (self.root / "datasets" / "external" / "common_voice_27" / "sentinel_audio")

        self.approved_manifest_sha256 = (
            approved_manifest_sha256 if approved_manifest_sha256 is not None else VALID_MANIFEST_SHA256
        )
        self.approved_manifest_lock_sha256 = (
            approved_manifest_lock_sha256 if approved_manifest_lock_sha256 is not None else VALID_MANIFEST_LOCK_SHA256
        )
        self.approved_sentinel_csv_sha256 = (
            approved_sentinel_csv_sha256 if approved_sentinel_csv_sha256 is not None else VALID_SENTINEL_CSV_SHA256
        )
        self.approved_sentinel_lock_sha256 = (
            approved_sentinel_lock_sha256 if approved_sentinel_lock_sha256 is not None else VALID_SENTINEL_LOCK_SHA256
        )
        self.approved_clip_lock_sha256 = (
            approved_clip_lock_sha256 if approved_clip_lock_sha256 is not None else VALID_COHORT2_CLIP_LOCK_SHA256
        )

        self.expected_manifest_crlf_sha256 = (
            expected_manifest_crlf_sha256 or VALID_MANIFEST_CRLF_SHA256
        )
        self.expected_manifest_lf_sha256 = (
            expected_manifest_lf_sha256 or VALID_MANIFEST_LF_SHA256
        )
        self.expected_sentinel_csv_crlf_sha256 = (
            expected_sentinel_csv_crlf_sha256 or VALID_SENTINEL_CSV_CRLF_SHA256
        )
        self.expected_sentinel_csv_lf_sha256 = (
            expected_sentinel_csv_lf_sha256 or VALID_SENTINEL_CSV_LF_SHA256
        )

    def validate_manifest(self) -> Dict[str, Any]:
        """
        Check 1: Manifest Integrity & Schema.
        Validates cryptographic hash against lock file, protocol version, and exact stratum allocation.
        Reconciles historical immutable manifest state against the v1.3.4 authorization amendment.
        """
        result: Dict[str, Any] = {
            "check_name": "manifest_integrity_and_schema",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.manifest_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Manifest file missing: {self.manifest_path}")
            return result

        if not self.lock_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Manifest lock file missing: {self.lock_path}")
            return result

        # 1. Cryptographic Hash & Lock Authorization Check on Disk
        lock_file_hash = compute_sha256(self.lock_path)
        if lock_file_hash not in self.approved_manifest_lock_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Manifest lock file records unauthorized SHA-256 digest '{lock_file_hash}' not in canonical allowlist {self.approved_manifest_lock_sha256}."
            )

        with open(self.lock_path, "r", encoding="utf-8") as f:
            try:
                lock_data = json.load(f)
            except Exception as e:
                result["status"] = "FAIL"
                result["errors"].append(f"Malformed manifest lock JSON: {e}")
                return result

        # 2. Enforce that EVERY populated digest in lock matches its specific expected canonical line-ending variant!
        lock_sha256 = lock_data.get("sha256")
        lock_sha256_lf = lock_data.get("sha256_lf")

        if not lock_sha256:
            result["status"] = "FAIL"
            result["errors"].append("Manifest lock file missing required 'sha256' field.")
        elif lock_sha256 != self.expected_manifest_crlf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Manifest lock records unauthorized CRLF 'sha256' digest '{lock_sha256}' (expected canonical CRLF '{self.expected_manifest_crlf_sha256}')."
            )

        if not lock_sha256_lf:
            result["status"] = "FAIL"
            result["errors"].append("Manifest lock file missing required 'sha256_lf' field.")
        elif lock_sha256_lf != self.expected_manifest_lf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Manifest lock records unauthorized LF 'sha256_lf' digest '{lock_sha256_lf}' (expected canonical LF '{self.expected_manifest_lf_sha256}')."
            )

        # 3. Check physical manifest file against allowlist and lock's declared digests
        manifest_hash = compute_sha256(self.manifest_path)
        if manifest_hash not in self.approved_manifest_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Manifest SHA-256 mismatch! Computed '{manifest_hash}' not in authorized digests {self.approved_manifest_sha256}."
            )
        lock_declared_hashes = {h for h in [lock_sha256, lock_sha256_lf] if h}
        if manifest_hash not in lock_declared_hashes:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Manifest SHA-256 '{manifest_hash}' does not match lock declared digests {lock_declared_hashes}."
            )

        # Parse Manifest
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Malformed manifest JSON: {e}")
            return result

        meta = manifest.get("metadata", {})
        strata = manifest.get("strata", {})

        # Reconcile Authority Model: Immutable Historical Manifest vs. Lock Amendment
        hist_protocol = meta.get("protocol_version", "")
        hist_standard = meta.get("governing_standard", "")
        hist_gov_status = meta.get("governance_status", "")
        hist_exec_auth = meta.get("execution_authorized")

        if hist_gov_status != "LOCKED_CANDIDATE_HOLD_NOT_AUTHORIZED":
            result["status"] = "FAIL"
            result["errors"].append(
                f"Historical manifest governance_status mismatch: expected 'LOCKED_CANDIDATE_HOLD_NOT_AUTHORIZED', got '{hist_gov_status}'."
            )

        if hist_exec_auth is not False:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Historical manifest execution_authorized mismatch: expected False, got {hist_exec_auth}."
            )

        if "stage6m" not in hist_protocol:
            result["status"] = "FAIL"
            result["errors"].append(f"Unexpected historical protocol version in manifest: '{hist_protocol}'")

        if hist_standard != "ADR-005":
            result["status"] = "FAIL"
            result["errors"].append(f"Unexpected historical governing standard in manifest: '{hist_standard}'")

        # Validate Lock Amendment Authorization Record
        lock_protocol = lock_data.get("protocol_version", "")
        lock_standard = lock_data.get("governing_standard", "")
        lock_gov_status = lock_data.get("governance_status", "")
        lock_exec_auth = lock_data.get("execution_authorized")
        auth_record = lock_data.get("authorization_record", {})

        if "v1.3.4" not in lock_protocol:
            result["status"] = "FAIL"
            result["errors"].append(f"Lock file protocol version mismatch: expected v1.3.4 amendment, got '{lock_protocol}'.")

        if "AMENDMENT-001" not in lock_standard:
            result["status"] = "FAIL"
            result["errors"].append(f"Lock file governing standard mismatch: expected AMENDMENT-001 reference, got '{lock_standard}'.")

        if lock_gov_status != "AUTHORIZED_UNDER_AMENDMENT_v1.3.4":
            result["status"] = "FAIL"
            result["errors"].append(
                f"Lock file governance_status mismatch: expected 'AUTHORIZED_UNDER_AMENDMENT_v1.3.4', got '{lock_gov_status}'."
            )

        if lock_exec_auth is not True:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Lock file execution_authorized mismatch: expected True under amendment, got {lock_exec_auth}."
            )

        expected_token = "AUTH-20261020-STAGE6M-AMEND-V134-EXECUTE-PERMITTED"
        actual_token = auth_record.get("token")
        if actual_token != expected_token:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Invalid or missing authorization token in lock record: expected '{expected_token}', got '{actual_token}'."
            )

        if auth_record.get("authorizing_authority") != "Designated Project Lead":
            result["status"] = "FAIL"
            result["errors"].append(
                f"Invalid authorizing authority in lock record: '{auth_record.get('authorizing_authority')}'."
            )

        total_active_spk = meta.get("total_active_speakers")
        if total_active_spk != 468:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 468 total active speakers, got {total_active_spk}")

        total_strata = meta.get("total_strata")
        if total_strata != 6 or len(strata) != 6:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 6 strata, got {len(strata)}")

        # Strata-level verification
        strata_summary = {}
        all_active_prefixes: List[str] = []
        for s_name in EXPECTED_STRATA_NAMES:
            if s_name not in strata:
                result["status"] = "FAIL"
                result["errors"].append(f"Missing required stratum in manifest: '{s_name}'")
                continue

            s_info = strata[s_name]
            active_list = s_info.get("active_speakers", [])
            if len(active_list) != 78 or s_info.get("active_count") != 78:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Stratum '{s_name}' has {len(active_list)} active speakers (expected exactly 78)."
                )

            for spk in active_list:
                pref = spk.get("speaker_id_prefix", "").rstrip("…")
                if len(pref) < 20:
                    result["status"] = "FAIL"
                    result["errors"].append(f"Invalid speaker prefix '{pref}' in stratum '{s_name}'")
                all_active_prefixes.append(pref)
                if spk.get("clips_allocated") != 15:
                    result["status"] = "FAIL"
                    result["errors"].append(f"Speaker {pref} allocated {spk.get('clips_allocated')} clips (expected 15).")

            strata_summary[s_name] = {
                "stratum_code": s_info.get("stratum_code"),
                "active_speakers": len(active_list),
                "clips_allocated": len(active_list) * 15,
            }

        # Check prefix uniqueness across all 468 speakers
        if len(all_active_prefixes) == 468 and len(set(all_active_prefixes)) != 468:
            result["status"] = "FAIL"
            result["errors"].append("Duplicate speaker prefixes detected within manifest active speakers!")

        # Option 1B Irish Reserve Check
        irish = strata.get("Irish English", {})
        if irish.get("reserve_tier_1_count") != 14 or irish.get("reserve_tier_2_count") != 13:
            result["status"] = "FAIL"
            result["errors"].append("Irish English Option 1B reserve pool count mismatch (expected 14 T1 + 13 T2).")

        result["details"] = {
            "manifest_sha256": manifest_hash,
            "total_active_speakers": total_active_spk,
            "total_clips_allocated": 468 * 15,
            "strata_summary": strata_summary,
            "irish_reserve_total": irish.get("total_reserve_count", 0),
            "provenance_reconciliation": {
                "historical_manifest_protocol": hist_protocol,
                "historical_governance_status": hist_gov_status,
                "historical_execution_authorized": hist_exec_auth,
                "amendment_protocol_version": lock_protocol,
                "amendment_governance_status": lock_gov_status,
                "amendment_execution_authorized": lock_exec_auth,
                "authorization_token": actual_token,
                "authority_reconciliation_verdict": "RECONCILED_AMENDMENT_V134",
            },
        }
        return result

    def validate_eval_csv(self, manifest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check 2: Manifest <-> Evaluation CSV Agreement.
        Checks duplicate clip IDs, speaker counts, strata breakdown, speaker-stratum preservation,
        and optional clip-level manifest/lock equality.
        """
        result: Dict[str, Any] = {
            "check_name": "evaluation_csv_manifest_agreement",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        # Check prerequisite existence: Evaluation CSV and Mandatory Clip Lock
        csv_exists = self.eval_csv_path.exists()
        clip_lock_exists = self.clip_lock_path.exists()

        if not csv_exists:
            result["status"] = "HOLD"
            result["errors"].append(
                "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Evaluation CSV not materialized: datasets/splits/stage6m_cohort2_audio.csv"
            )
            if not clip_lock_exists:
                result["errors"].append(
                    "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Authoritative clip lock file not materialized: datasets/splits/stage6m_cohort2_audio.lock.json"
                )
            return result

        if not clip_lock_exists:
            result["status"] = "FAIL"
            result["errors"].append(
                "Mandatory clip lock file missing: datasets/splits/stage6m_cohort2_audio.lock.json"
            )
            return result

        try:
            df = pd.read_csv(self.eval_csv_path)
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Failed to parse evaluation CSV: {e}")
            return result

        required_cols = {"recording_id", "speaker_id", "transcript"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            result["status"] = "FAIL"
            result["errors"].append(f"Missing required columns in CSV: {missing_cols}")
            return result

        stratum_col = (
            "stage5_accent_group"
            if "stage5_accent_group" in df.columns
            else ("stratum" if "stratum" in df.columns else ("stratum_code" if "stratum_code" in df.columns else None))
        )
        if not stratum_col:
            result["status"] = "FAIL"
            result["errors"].append("No stratum identification column found in evaluation CSV.")
            return result

        # Clip duplicate check
        dup_clips = df["recording_id"].duplicated().sum()
        if dup_clips > 0:
            result["status"] = "FAIL"
            result["errors"].append(f"Evaluation CSV contains {dup_clips} duplicate clip IDs!")

        # Total clip count check
        total_clips = len(df)
        if total_clips != 7020:
            result["status"] = "FAIL"
            result["errors"].append(f"Evaluation CSV has {total_clips} clips (expected exactly 7,020).")

        # Speaker count check
        unique_speakers = df["speaker_id"].nunique()
        if unique_speakers != 468:
            result["status"] = "FAIL"
            result["errors"].append(f"Evaluation CSV has {unique_speakers} speakers (expected exactly 468).")

        # Clips per speaker check
        clips_per_spk = df.groupby("speaker_id")["recording_id"].count()
        if not (clips_per_spk == 15).all():
            mismatched = (clips_per_spk != 15).sum()
            result["status"] = "FAIL"
            result["errors"].append(f"{mismatched} speakers do not have exactly 15 clips allocated.")

        # Strata breakdown check
        strata_counts = df.groupby(stratum_col)["recording_id"].count().to_dict()
        if len(strata_counts) != 6:
            result["status"] = "FAIL"
            result["errors"].append(f"Evaluation CSV has {len(strata_counts)} strata (expected 6).")

        for s_key, count in strata_counts.items():
            if count != 1170:
                result["status"] = "FAIL"
                result["errors"].append(f"Stratum '{s_key}' has {count} clips (expected 1,170 = 78*15).")

        # Speaker-to-Stratum Mapping & Locked Stratum Preservation
        strata_manifest = manifest_data.get("strata", {})
        prefix_to_stratum: Dict[str, Tuple[str, str]] = {}
        for s_name, s_info in strata_manifest.items():
            s_code = s_info.get("stratum_code", "")
            for spk in s_info.get("active_speakers", []):
                pref = spk["speaker_id_prefix"].rstrip("…")
                prefix_to_stratum[pref] = (s_name, s_code)

        unmatched_spks: List[str] = []
        stratum_swaps: List[str] = []

        for spk_id, spk_df in df.groupby("speaker_id"):
            spk_str = str(spk_id)
            matched_prefix = None
            for pref in prefix_to_stratum:
                if spk_str.startswith(pref):
                    matched_prefix = pref
                    break

            if matched_prefix is None:
                unmatched_spks.append(spk_str)
                continue

            expected_s_name, expected_s_code = prefix_to_stratum[matched_prefix]
            assigned_strata = set(spk_df[stratum_col].unique())
            # Check if assigned stratum matches expected name or code
            matches_expected = (expected_s_name in assigned_strata) or (expected_s_code in assigned_strata)
            if not matches_expected or len(assigned_strata) != 1:
                stratum_swaps.append(
                    f"Speaker '{spk_str[:12]}...' (prefix '{matched_prefix[:10]}...'): "
                    f"locked to '{expected_s_name}', but assigned to {list(assigned_strata)} in CSV."
                )

        if unmatched_spks:
            result["status"] = "FAIL"
            result["errors"].append(
                f"{len(unmatched_spks)} speakers in evaluation CSV do not match any candidate manifest active prefix."
            )

        if stratum_swaps:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Speaker stratum preservation violation! {len(stratum_swaps)} speakers were redistributed/swapped between strata: {stratum_swaps[:3]}"
            )

        # Mandatory Clip-Level Lock / Manifest Agreement Check
        clip_lock_verified = False
        try:
            clip_lock_hash = compute_sha256(self.clip_lock_path)
            if not self.approved_clip_lock_sha256 or clip_lock_hash not in self.approved_clip_lock_sha256:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock file '{self.clip_lock_path}' SHA-256 '{clip_lock_hash}' is not in approved allowlist {self.approved_clip_lock_sha256}."
                )

            with open(self.clip_lock_path, "r", encoding="utf-8") as f:
                clip_lock_data = json.load(f)

            # Validate complete lock schema
            required_schema_keys = [
                "protocol_version",
                "governing_standard",
                "dataset_name",
                "total_clips",
                "total_speakers",
                "total_strata",
                "clips_per_speaker",
                "recording_ids",
            ]
            missing_schema_keys = [k for k in required_schema_keys if k not in clip_lock_data]
            if missing_schema_keys:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock schema incomplete! Missing required keys: {missing_schema_keys}"
                )

            if clip_lock_data.get("total_clips") != 7020:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock schema total_clips is {clip_lock_data.get('total_clips')} (expected 7020)."
                )

            if clip_lock_data.get("total_speakers") != 468:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock schema total_speakers is {clip_lock_data.get('total_speakers')} (expected 468)."
                )

            if clip_lock_data.get("total_strata") != 6:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock schema total_strata is {clip_lock_data.get('total_strata')} (expected 6)."
                )

            if clip_lock_data.get("clips_per_speaker") != 15:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Clip lock schema clips_per_speaker is {clip_lock_data.get('clips_per_speaker')} (expected 15)."
                )

            # Exact recording-ID set equality
            raw_rec_ids = clip_lock_data.get("recording_ids")
            if not isinstance(raw_rec_ids, list):
                result["status"] = "FAIL"
                result["errors"].append("Clip lock 'recording_ids' field must be a list of recording IDs.")
            else:
                expected_rec_ids = set(raw_rec_ids)
                actual_rec_ids = set(df["recording_id"])
                missing_rec_ids = expected_rec_ids - actual_rec_ids
                extra_rec_ids = actual_rec_ids - expected_rec_ids
                if len(raw_rec_ids) != 7020 or len(expected_rec_ids) != 7020:
                    result["status"] = "FAIL"
                    result["errors"].append(
                        f"Clip lock contains {len(raw_rec_ids)} recording IDs ({len(expected_rec_ids)} unique, expected exactly 7,020 unique)."
                    )
                if missing_rec_ids or extra_rec_ids:
                    result["status"] = "FAIL"
                    result["errors"].append(
                        f"Clip-set exact equality failed! {len(missing_rec_ids)} missing clips, {len(extra_rec_ids)} extra clips compared to locked clip manifest."
                    )

            # Matching CSV digest
            csv_hash = compute_sha256(self.eval_csv_path)
            csv_allowlist = {
                clip_lock_data.get("csv_sha256"),
                clip_lock_data.get("crlf_sha256"),
                clip_lock_data.get("lf_sha256"),
            } - {None}
            if not csv_allowlist:
                result["status"] = "FAIL"
                result["errors"].append(
                    "Clip lock does not contain any CSV digest fields ('csv_sha256', 'crlf_sha256', 'lf_sha256')."
                )
            elif csv_hash not in csv_allowlist:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"Evaluation CSV SHA-256 '{csv_hash}' not in clip lock declared digests {csv_allowlist}."
                )

            if result["status"] == "PASS":
                clip_lock_verified = True
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Failed to parse clip lock file '{self.clip_lock_path}': {e}")

        result["details"] = {
            "total_clips": total_clips,
            "unique_speakers": unique_speakers,
            "strata_counts": strata_counts,
            "duplicate_clip_count": int(dup_clips),
            "manifest_prefix_match_rate_pct": round(
                100.0 * (unique_speakers - len(unmatched_spks)) / max(1, unique_speakers), 2
            ),
            "speaker_stratum_preservation_verified": len(stratum_swaps) == 0 and len(unmatched_spks) == 0,
            "clip_lock_verified": clip_lock_verified,
        }
        return result

    def validate_audio_materialization(
        self, eval_df: Optional[pd.DataFrame] = None, check_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Check 3: Audio Materialization & 16 kHz Decodability.
        Verifies existence on disk, enforces non-empty files, rejects missing/extra clips,
        and tests sampled 16 kHz mono float32 decoding.
        """
        result: Dict[str, Any] = {
            "check_name": "audio_materialization_and_decodability",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.audio_dir.exists():
            result["status"] = "HOLD"
            result["errors"].append(
                "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Cohort 2 audio directory not found: datasets/external/common_voice_27/cohort2_audio"
            )
            return result

        mp3_files = list(self.audio_dir.glob("*.mp3"))
        if len(mp3_files) < 7020:
            result["status"] = "HOLD"
            result["errors"].append(
                f"MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Found {len(mp3_files)} MP3 files in datasets/external/common_voice_27/cohort2_audio (required: 7,020)."
            )
            result["details"] = {"files_present": len(mp3_files), "files_required": 7020}
            return result

        # Enforce Non-Empty Files
        empty_files = [f.name for f in mp3_files if f.stat().st_size == 0]
        if empty_files:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Materialization integrity failure: {len(empty_files)} audio files have zero bytes (e.g. {empty_files[:3]})."
            )

        # Exact Audio File Set Verification Against Evaluation CSV
        missing_clips: List[str] = []
        extra_clips: List[str] = []
        if eval_df is not None:
            expected_names = set(f"{rec_id}.mp3" for rec_id in eval_df["recording_id"])
            actual_names = set(f.name for f in mp3_files)
            missing_clips = list(expected_names - actual_names)
            extra_clips = list(actual_names - expected_names)

            if missing_clips:
                result["status"] = "FAIL"
                result["errors"].append(f"{len(missing_clips)} clips in evaluation CSV lack matching physical audio files.")

            if extra_clips:
                result["status"] = "FAIL"
                result["errors"].append(f"{len(extra_clips)} extraneous audio files found in audio directory not listed in evaluation CSV.")

        # Sample decode & resample test to verify genuine acoustic decodability
        decode_tested = 0
        decode_failed = 0
        sample_files = mp3_files[:check_samples]
        for f in sample_files:
            try:
                waveform, sr = load_and_resample_audio(f, target_sr=16000)
                decode_tested += 1
                if sr != 16000 or len(waveform) == 0 or np.isnan(waveform).any() or np.isinf(waveform).any():
                    decode_failed += 1
            except Exception:
                decode_failed += 1

        if decode_failed > 0:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Audio decoding failure: {decode_failed}/{decode_tested} sampled audio files failed 16 kHz conversion."
            )

        result["details"] = {
            "total_audio_files": len(mp3_files),
            "expected_audio_files": 7020,
            "empty_files_count": len(empty_files),
            "missing_clip_count": len(missing_clips),
            "extra_clip_count": len(extra_clips),
            "decodability_audit_type": "PREFLIGHT_SAMPLE_AUDIT",
            "decode_sample_tested": decode_tested,
            "decode_sample_failed": decode_failed,
            "target_sample_rate_hz": 16000,
            "decodability_scope_note": (
                f"Preflight validates sampled decodability ({decode_tested} files tested). "
                "Full-corpus decodability is verified during waveform preloading before model initialization."
            ),
        }
        return result

    def validate_sentinel_panel_and_isolation(
        self, manifest_data: Dict[str, Any], eval_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Check 4: Sentinel Panel Completeness & Zero-Exposure Speaker Isolation.
        Validates core panel (30 clips, 281 words, uncertainty floor = 0.3559 pp), audio decodability,
        and asserts that sentinel speakers are strictly disjoint from Cohort 2 evaluation speakers.
        """
        result: Dict[str, Any] = {
            "check_name": "sentinel_panel_completeness_and_isolation",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.sentinel_csv_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel panel CSV missing: {self.sentinel_csv_path}")
            return result

        if not self.sentinel_lock_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel panel lock missing: {self.sentinel_lock_path}")
            return result

        # 1. Check physical sentinel lock file on disk against authorized lock allowlist
        sent_lock_hash = compute_sha256(self.sentinel_lock_path)
        if sent_lock_hash not in self.approved_sentinel_lock_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock file '{self.sentinel_lock_path}' SHA-256 '{sent_lock_hash}' not in approved lock allowlist {self.approved_sentinel_lock_sha256}."
            )

        with open(self.sentinel_lock_path, "r", encoding="utf-8") as f:
            try:
                lock = json.load(f)
            except Exception as e:
                result["status"] = "FAIL"
                result["errors"].append(f"Malformed sentinel lock JSON: {e}")
                return result

        # 2. Validate EVERY populated digest in sentinel lock against exact canonical line-ending variant!
        lock_csv_sha256 = lock.get("csv_sha256")
        lock_crlf_sha256 = lock.get("crlf_sha256")
        lock_lf_sha256 = lock.get("lf_sha256")

        if lock_csv_sha256 and lock_csv_sha256 not in self.approved_sentinel_csv_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock records unauthorized 'csv_sha256' '{lock_csv_sha256}' not in authorized digests {self.approved_sentinel_csv_sha256}."
            )
        if lock_crlf_sha256 and lock_crlf_sha256 != self.expected_sentinel_csv_crlf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock records unauthorized 'crlf_sha256' '{lock_crlf_sha256}' (expected canonical CRLF '{self.expected_sentinel_csv_crlf_sha256}')."
            )
        if lock_lf_sha256 and lock_lf_sha256 != self.expected_sentinel_csv_lf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock records unauthorized 'lf_sha256' '{lock_lf_sha256}' (expected canonical LF '{self.expected_sentinel_csv_lf_sha256}')."
            )

        # 3. Check sentinel CSV on disk against approved allowlist and lock's declared digests
        sent_hash = compute_sha256(self.sentinel_csv_path)
        if sent_hash not in self.approved_sentinel_csv_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel panel CSV hash '{sent_hash}' not in approved allowlist {self.approved_sentinel_csv_sha256}."
            )

        valid_sent_hashes = {h for h in [lock_csv_sha256, lock_crlf_sha256, lock_lf_sha256] if h}
        if sent_hash not in valid_sent_hashes:
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel panel CSV hash altered! ({sent_hash} not in declared digests {valid_sent_hashes})")

        sent_df = pd.read_csv(self.sentinel_csv_path)
        if len(sent_df) != 300:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 300 sentinel panel records, got {len(sent_df)}")

        sent_spk_count = sent_df["speaker_id"].nunique()
        if sent_spk_count != CORE_SENTINEL_SPEAKERS:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 30 sentinel speakers, got {sent_spk_count}")

        # Core panel extraction (1 clip per speaker)
        core_sentinel_df = sent_df.groupby("speaker_id").first().reset_index()
        core_word_count = sum(len(TextNormalizer.normalize(str(t)).split()) for t in core_sentinel_df["transcript"])

        # Word count and engineering uncertainty floor
        uncertainty_floor = round(100.0 / core_word_count, 4) if core_word_count > 0 else 0.0
        if core_word_count != CORE_SENTINEL_WORDS:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Core sentinel panel reference word count is {core_word_count} (expected {CORE_SENTINEL_WORDS})."
            )

        # Sentinel audio existence and preflight decodability
        missing_sent_audio = 0
        sent_decode_tested = 0
        sent_decode_failed = 0
        for _, row in core_sentinel_df.iterrows():
            s_id = str(row.get("sentinel_id") or row.get("recording_id"))
            p = self.sentinel_audio_dir / f"{s_id}.mp3"
            if not p.exists():
                p = self.root / str(row.get("audio_filepath", ""))
            if not p.exists():
                missing_sent_audio += 1
            else:
                if sent_decode_tested < 5:
                    try:
                        wf, sr = load_and_resample_audio(p, target_sr=16000)
                        sent_decode_tested += 1
                        if sr != 16000 or len(wf) == 0 or np.isnan(wf).any():
                            sent_decode_failed += 1
                    except Exception:
                        sent_decode_tested += 1
                        sent_decode_failed += 1

        if missing_sent_audio > 0:
            result["status"] = "FAIL"
            result["errors"].append(f"{missing_sent_audio}/30 core sentinel audio clips are missing on disk.")

        if sent_decode_failed > 0:
            result["status"] = "FAIL"
            result["errors"].append(f"{sent_decode_failed}/{sent_decode_tested} sampled sentinel audio clips failed 16 kHz decoding.")

        # STRICT SPEAKER ISOLATION / ZERO EXPOSURE CHECK
        sentinel_prefixes = set(s[:24] for s in sent_df["speaker_id"].unique())

        # 1. Check against manifest active speakers
        manifest_active_prefs = set()
        for s_info in manifest_data.get("strata", {}).values():
            for spk in s_info.get("active_speakers", []):
                manifest_active_prefs.add(spk["speaker_id_prefix"].rstrip("…")[:24])

        active_overlap = sentinel_prefixes.intersection(manifest_active_prefs)
        if active_overlap:
            result["status"] = "FAIL"
            result["errors"].append(
                f"DATA LEAKAGE DETECTED! {len(active_overlap)} sentinel speakers overlap with manifest active speakers: {active_overlap}"
            )

        # 2. Check against evaluation CSV if provided
        csv_overlap: Set[str] = set()
        if eval_df is not None:
            eval_spk_ids = set(eval_df["speaker_id"].unique())
            sent_spk_ids = set(sent_df["speaker_id"].unique())
            csv_overlap = eval_spk_ids.intersection(sent_spk_ids)
            if csv_overlap:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"DATA LEAKAGE DETECTED! {len(csv_overlap)} evaluation CSV speakers overlap with sentinel panel!"
                )

        result["details"] = {
            "total_sentinel_records": len(sent_df),
            "core_sentinel_speakers": sent_spk_count,
            "core_sentinel_clips": len(core_sentinel_df),
            "core_sentinel_reference_words": core_word_count,
            "uncertainty_floor_pp": uncertainty_floor,
            "speaker_isolation_verified": bool(len(active_overlap) == 0 and len(csv_overlap) == 0),
            "sentinel_active_overlap_count": len(active_overlap),
            "sentinel_decode_sample_tested": sent_decode_tested,
            "sentinel_decode_sample_failed": sent_decode_failed,
        }
        return result

    def freeze_execution_configuration(self, model_name: str = "wav2vec2_base") -> Dict[str, Any]:
        """
        Check 5: Freeze Execution Configuration & Hardware Specification.
        Freezes gate thresholds, Lan-DeMets schedule parameters, hardware attributes, and runtime budget.
        """
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "None (CPU Execution)"
        vram_gb = (
            round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            if cuda_avail
            else 0.0
        )

        config_payload = {
            "check_name": "execution_configuration_freeze",
            "status": "PASS",
            "governing_protocol": "v1.3.4-stage6m-self-authorization-amendment",
            "governing_standard": "ADR-005",
            "model_architecture": model_name,
            "huggingface_backbone": (
                "facebook/wav2vec2-base-960h" if model_name == "wav2vec2_base" else "facebook/hubert-large-ls960-ft"
            ),
            "stream_geometry": {
                "cohort": "cohort2",
                "total_evaluation_clips": 7020,
                "window_size_k": 4,
                "total_stream_windows_w": 1755,
                "adaptation_updates_u": 1754,
                "terminal_window_index": 1754,
                "terminal_window_mode": "PREDICTION_ONLY_INVARIANT",
            },
            "gate_parameters": {
                "epsilon_r_pp": 0.0000,
                "epsilon_g_pp": 2.0000,
                "epsilon_d_pp": 2.0000,
                "alpha_target": 0.05,
                "spending_function": "Lan-DeMets O'Brien-Fleming",
                "effective_uncertainty_floor_pp": EXPECTED_UNCERTAINTY_FLOOR_PP,
                "tie_breaker_rule": "REJECT_TIE_STRICT_INEQUALITY",
                "rollback_guarantee": "BITWISE_EXACT_PARAMETER_HASH",
            },
            "hardware_environment": {
                "cuda_available": cuda_avail,
                "device_type": "cuda" if cuda_avail else "cpu",
                "device_name": gpu_name,
                "total_vram_gb": vram_gb,
                "pytorch_version": torch.__version__,
            },
            "compute_budget_estimate": {
                "evaluation_clip_forward_passes": 7020 * 3,  # 3 arms
                "sentinel_forward_passes": 1755 * CORE_SENTINEL_CLIPS,  # 52,650
                "suta_backward_passes": 1754 * 2,  # Arm 2 + Arm 3 candidates
                "estimated_runtime_hours_p100": 3.8,
                "recommended_accelerator": "Kaggle NVIDIA Tesla P100 (16 GB VRAM)",
            },
            "output_locations": {
                "results_dir": "results/stage6m_kaggle",
                "reports_dir": "reports/stage6m",
            },
        }
        return config_payload

    def run_preflight(
        self, model_name: str = "wav2vec2_base", check_audio_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Execute complete 5-stage preflight validation.
        Returns auditable report payload with overall status 'READY FOR AUTHORIZED EXECUTION' or 'HOLD'.
        """
        t0 = datetime.now(timezone.utc)
        git_rev = get_git_revision(self.root)

        # 1. Manifest
        manifest_res = self.validate_manifest()

        # Load manifest data for downstream checks if valid
        manifest_data = {}
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except Exception:
                pass

        # 2. Evaluation CSV
        csv_res = self.validate_eval_csv(manifest_data)

        # Load eval_df if present
        eval_df = None
        if self.eval_csv_path.exists() and csv_res["status"] == "PASS":
            try:
                eval_df = pd.read_csv(self.eval_csv_path)
            except Exception:
                pass

        # 3. Audio Materialization
        audio_res = self.validate_audio_materialization(eval_df=eval_df, check_samples=check_audio_samples)

        # 4. Sentinel Panel & Isolation
        sent_res = self.validate_sentinel_panel_and_isolation(manifest_data=manifest_data, eval_df=eval_df)

        # 5. Configuration Freeze
        cfg_res = self.freeze_execution_configuration(model_name=model_name)

        # Compute Overall Status
        all_checks = [manifest_res, csv_res, audio_res, sent_res, cfg_res]
        all_statuses = [c["status"] for c in all_checks]
        all_errors = [err for c in all_checks for err in c.get("errors", [])]

        if "FAIL" in all_statuses:
            overall_status = "HOLD"
            summary_desc = "FAIL_CLOSED_VALIDATION_ERROR: One or more technical integrity checks failed."
        elif "HOLD" in all_statuses:
            overall_status = "HOLD"
            summary_desc = "MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD: Confirmatory data prerequisites not yet materialized on disk."
        else:
            overall_status = "READY FOR AUTHORIZED EXECUTION"
            summary_desc = "All 5 preflight integrity checks verified. Technical readiness established."

        report: Dict[str, Any] = {
            "report_title": "Stage 6M Confirmatory Cohort 2 Preflight Readiness Audit",
            "overall_status": overall_status,
            "summary_description": summary_desc,
            "status_reasons": all_errors,
            "timestamp_utc": t0.isoformat(),
            "git_commit": git_rev,
            "governing_standard": "ADR-005",
            "protocol_version": "v1.3.4-stage6m-self-authorization-amendment",
            "checks": {
                "manifest_integrity_and_schema": manifest_res,
                "evaluation_csv_manifest_agreement": csv_res,
                "audio_materialization_and_decodability": audio_res,
                "sentinel_panel_completeness_and_isolation": sent_res,
                "execution_configuration_freeze": cfg_res,
            },
            "governance_note": (
                "Passing technical preflight checks establishes scientific feasibility; "
                "it does NOT constitute authorization of compute expenditure or confirmatory benchmark execution. "
                "Hardware execution requires designated project lead or supervisory signoff."
            ),
        }
        return report

    @staticmethod
    def _format_checklist_metrics(check_key: str, check_data: Dict[str, Any]) -> str:
        status = check_data.get("status", "UNKNOWN")
        errors = check_data.get("errors", [])
        details = check_data.get("details", {})

        if check_key == "manifest_integrity_and_schema":
            if status == "PASS":
                sha = details.get("manifest_sha256", "")[:10]
                reconciled = details.get("provenance_reconciliation", {}).get("authority_reconciliation_verdict", "RECONCILED")
                return (
                    f"SHA-256 locked ({sha}...); 468 speakers across 6 strata (78/stratum); "
                    f"Option 1B reserve verified ({details.get('irish_reserve_total', 27)} reserve); "
                    f"authority reconciled ({reconciled})."
                )
            return f"Manifest check failed: {errors[0] if errors else 'Integrity violation detected'}."

        elif check_key == "evaluation_csv_manifest_agreement":
            if status == "PASS":
                return (
                    f"0 duplicate clip IDs; {details.get('total_clips', 7020):,} clips across 6 strata "
                    f"(1,170/stratum); 468 speakers mapped to locked strata (zero swaps)."
                )
            elif status == "HOLD":
                return "Validation could not be completed: evaluation CSV not materialized on disk (prerequisite missing)."
            return f"CSV agreement failed: {errors[0] if errors else 'Integrity violation detected'}."

        elif check_key == "audio_materialization_and_decodability":
            if status == "PASS":
                return (
                    f"{details.get('total_audio_files', 7020):,} physical audio files materialized; "
                    f"sampled 16 kHz decodability verified ({details.get('decode_sample_tested', 0)} tested, 0 errors). "
                    "Full-corpus preloading required prior to model execution."
                )
            elif status == "HOLD":
                err_msg = errors[0] if errors else "audio directory not materialized on disk"
                return f"Validation could not be completed: physical audio files not materialized ({err_msg})."
            return f"Audio validation failed: {errors[0] if errors else 'Materialization error'}."

        elif check_key == "sentinel_panel_completeness_and_isolation":
            if status == "PASS":
                return (
                    f"30 core clips (281 words, uncertainty floor = {details.get('uncertainty_floor_pp', 0.3559):.4f} pp); "
                    "sampled audio decodability verified; 0 speaker overlap (zero leakage)."
                )
            return f"Sentinel validation failed: {errors[0] if errors else 'Integrity violation detected'}."

        elif check_key == "execution_configuration_freeze":
            if status == "PASS":
                return (
                    f"Model ({details.get('model_architecture', 'wav2vec2_base')}), thresholds, Lan-DeMets spending, "
                    f"{details.get('stream_geometry', {}).get('adaptation_updates_u', 1754)} candidate updates, and compute budget frozen."
                )
            return f"Configuration freeze failed: {errors[0] if errors else 'Freeze error'}."

        return f"Status: {status}"

    def save_reports(
        self, report: Dict[str, Any], output_dir: Optional[Path] = None
    ) -> Tuple[Path, Path]:
        """
        Save auditable JSON and Markdown preflight readiness reports.
        """
        out_dir = output_dir or (self.root / "reports" / "stage6m")
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "stage6m_cohort2_readiness_report.json"
        md_path = out_dir / "stage6m_cohort2_readiness_report.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Build Markdown
        status = report["overall_status"]
        alert_type = "NOTE" if status == "READY FOR AUTHORIZED EXECUTION" else "WARNING"

        desc_1 = self._format_checklist_metrics("manifest_integrity_and_schema", report["checks"]["manifest_integrity_and_schema"])
        desc_2 = self._format_checklist_metrics("evaluation_csv_manifest_agreement", report["checks"]["evaluation_csv_manifest_agreement"])
        desc_3 = self._format_checklist_metrics("audio_materialization_and_decodability", report["checks"]["audio_materialization_and_decodability"])
        desc_4 = self._format_checklist_metrics("sentinel_panel_completeness_and_isolation", report["checks"]["sentinel_panel_completeness_and_isolation"])
        desc_5 = self._format_checklist_metrics("execution_configuration_freeze", report["checks"]["execution_configuration_freeze"])

        md_content = f"""# Stage 6M Confirmatory Cohort 2 Preflight Readiness Report

> [!{alert_type}]
> **Overall Preflight Status:** `{status}`  
> **Summary:** {report['summary_description']}  
> **Timestamp:** {report['timestamp_utc']}  
> **Git Commit:** `{report['git_commit'][:10]}`  
> **Protocol:** `{report['protocol_version']}` ({report['governing_standard']})

---

## 1. Governance & Execution Disclaimer

{report['governance_note']}

---

## 2. Preflight Checklist Verification Matrix

| Checklist Item | Scope | Status | Key Metrics / Evidence |
| :--- | :--- | :---: | :--- |
| **1. Manifest Integrity & Schema** | `stage6m_locked_candidate_manifest.json` | `{report['checks']['manifest_integrity_and_schema']['status']}` | {desc_1} |
| **2. Manifest <-> CSV Agreement** | `stage6m_cohort2_audio.csv` | `{report['checks']['evaluation_csv_manifest_agreement']['status']}` | {desc_2} |
| **3. Audio Materialization & Decodability** | `cohort2_audio/*.mp3` | `{report['checks']['audio_materialization_and_decodability']['status']}` | {desc_3} |
| **4. Sentinel Panel Completeness & Isolation** | `stage5_sentinel_panel.csv` | `{report['checks']['sentinel_panel_completeness_and_isolation']['status']}` | {desc_4} |
| **5. Configuration & Budget Freeze** | Prequential Lan-DeMets Gating | `{report['checks']['execution_configuration_freeze']['status']}` | {desc_5} |

---

## 3. Status Reasons and Action Items

"""
        if report["status_reasons"]:
            md_content += "The following items currently hold confirmatory execution:\n\n"
            for r in report["status_reasons"]:
                md_content += f"- **{r}**\n"
            md_content += "\n### Required Steps to Lift HOLD:\n"
            md_content += "1. Materialize `datasets/splits/stage6m_cohort2_audio.csv` matching the locked candidate manifest.\n"
            md_content += "2. Download/extract the 7,020 physical MP3 audio files into `datasets/external/common_voice_27/cohort2_audio/`.\n"
            md_content += "3. Verify compute allocation (e.g. Kaggle Tesla P100 GPU session).\n"
            md_content += "4. Rerun preflight validation to verify transition to `READY FOR AUTHORIZED EXECUTION`.\n"
        else:
            md_content += "All technical preflight checks have passed with zero integrity violations.\n"

        md_content += f"""
---

## 4. Frozen Execution Configuration

```json
{json.dumps(report['checks']['execution_configuration_freeze'], indent=2)}
```
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path


class Cohort1PreflightValidator:
    """
    Exhaustive preflight validator for Stage 6M Cohort 1 benchmark (900 physical clips).
    Guarantees fail-closed behavior before allocating compute resources or preloading waveforms.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        eval_csv_path: Optional[Path] = None,
        eval_lock_path: Optional[Path] = None,
        audio_dir: Optional[Path] = None,
        sentinel_csv_path: Optional[Path] = None,
        sentinel_lock_path: Optional[Path] = None,
        sentinel_audio_dir: Optional[Path] = None,
        approved_eval_csv_sha256: Optional[Set[str]] = None,
        approved_eval_lock_sha256: Optional[Set[str]] = None,
        approved_sentinel_csv_sha256: Optional[Set[str]] = None,
        approved_sentinel_lock_sha256: Optional[Set[str]] = None,
        expected_eval_csv_crlf_sha256: Optional[str] = None,
        expected_eval_csv_lf_sha256: Optional[str] = None,
        expected_sentinel_csv_crlf_sha256: Optional[str] = None,
        expected_sentinel_csv_lf_sha256: Optional[str] = None,
    ):
        self.root = project_root or Path(__file__).resolve().parent.parent.parent.parent
        self.eval_csv_path = eval_csv_path or (self.root / "datasets" / "splits" / "stage5_external_eval.csv")
        self.eval_lock_path = eval_lock_path or (self.root / "datasets" / "splits" / "stage5_external_eval.lock.json")
        self.audio_dir = audio_dir or (self.root / "datasets" / "external" / "common_voice_27" / "audio")
        self.sentinel_csv_path = sentinel_csv_path or (self.root / "datasets" / "splits" / "stage5_sentinel_panel.csv")
        self.sentinel_lock_path = sentinel_lock_path or (self.root / "datasets" / "splits" / "stage5_sentinel_panel.lock.json")
        self.sentinel_audio_dir = sentinel_audio_dir or (self.root / "datasets" / "external" / "common_voice_27" / "sentinel_audio")

        self.approved_eval_csv_sha256 = (
            approved_eval_csv_sha256 if approved_eval_csv_sha256 is not None else VALID_STAGE5_EVAL_CSV_SHA256
        )
        self.approved_eval_lock_sha256 = (
            approved_eval_lock_sha256 if approved_eval_lock_sha256 is not None else VALID_STAGE5_EVAL_LOCK_SHA256
        )
        self.approved_sentinel_csv_sha256 = (
            approved_sentinel_csv_sha256 if approved_sentinel_csv_sha256 is not None else VALID_SENTINEL_CSV_SHA256
        )
        self.approved_sentinel_lock_sha256 = (
            approved_sentinel_lock_sha256 if approved_sentinel_lock_sha256 is not None else VALID_SENTINEL_LOCK_SHA256
        )

        self.expected_eval_csv_crlf_sha256 = (
            expected_eval_csv_crlf_sha256 or VALID_STAGE5_EVAL_CSV_CRLF_SHA256
        )
        self.expected_eval_csv_lf_sha256 = (
            expected_eval_csv_lf_sha256 or VALID_STAGE5_EVAL_CSV_LF_SHA256
        )
        self.expected_sentinel_csv_crlf_sha256 = (
            expected_sentinel_csv_crlf_sha256 or VALID_SENTINEL_CSV_CRLF_SHA256
        )
        self.expected_sentinel_csv_lf_sha256 = (
            expected_sentinel_csv_lf_sha256 or VALID_SENTINEL_CSV_LF_SHA256
        )

    def validate_eval_dataset(self) -> Dict[str, Any]:
        """
        Check 1: Cohort 1 Evaluation CSV & Lock Cryptographic Integrity and Schema.
        """
        result: Dict[str, Any] = {
            "check_name": "cohort1_eval_dataset_integrity",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.eval_lock_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 evaluation lock missing: {self.eval_lock_path}")
            return result

        if not self.eval_csv_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 evaluation CSV missing: {self.eval_csv_path}")
            return result

        # Verify lock file on disk against allowlist
        lock_hash = compute_sha256(self.eval_lock_path)
        if lock_hash not in self.approved_eval_lock_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 evaluation lock file records unauthorized SHA-256 '{lock_hash}' not in {self.approved_eval_lock_sha256}."
            )

        with open(self.eval_lock_path, "r", encoding="utf-8") as f:
            try:
                lock_data = json.load(f)
            except Exception as e:
                result["status"] = "FAIL"
                result["errors"].append(f"Malformed Cohort 1 evaluation lock JSON: {e}")
                return result

        # Check declared lock digests
        declared_csv_hashes = {
            lock_data.get("csv_sha256"),
            lock_data.get("crlf_sha256"),
            lock_data.get("lf_sha256"),
            lock_data.get("csv_hash"),
        } - {None}
        if not declared_csv_hashes.intersection(self.approved_eval_csv_sha256):
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 evaluation lock declared digests {declared_csv_hashes} do not intersect approved CSV allowlist {self.approved_eval_csv_sha256}."
            )

        lock_crlf = lock_data.get("crlf_sha256")
        lock_lf = lock_data.get("lf_sha256")
        if lock_crlf and lock_crlf != self.expected_eval_csv_crlf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 evaluation lock records unauthorized 'crlf_sha256' '{lock_crlf}' (expected canonical CRLF '{self.expected_eval_csv_crlf_sha256}')."
            )
        if lock_lf and lock_lf != self.expected_eval_csv_lf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 evaluation lock records unauthorized 'lf_sha256' '{lock_lf}' (expected canonical LF '{self.expected_eval_csv_lf_sha256}')."
            )

        # Check lock schema numbers
        if lock_data.get("num_rows") != 900:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 lock specifies num_rows={lock_data.get('num_rows')} (expected 900).")
        if lock_data.get("num_speakers") != 60:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 lock specifies num_speakers={lock_data.get('num_speakers')} (expected 60).")
        if lock_data.get("num_groups") != 6:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 lock specifies num_groups={lock_data.get('num_groups')} (expected 6).")
        if lock_data.get("clips_per_speaker") != 15:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 lock specifies clips_per_speaker={lock_data.get('clips_per_speaker')} (expected 15).")

        # Verify CSV hash on disk
        csv_hash = compute_sha256(self.eval_csv_path)
        if csv_hash not in self.approved_eval_csv_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 CSV SHA-256 '{csv_hash}' not in approved allowlist {self.approved_eval_csv_sha256}."
            )
        if csv_hash not in declared_csv_hashes:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 CSV SHA-256 '{csv_hash}' does not match declared lock digests {declared_csv_hashes}."
            )

        # Parse CSV
        try:
            df = pd.read_csv(self.eval_csv_path)
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Failed to parse Cohort 1 evaluation CSV: {e}")
            return result

        if len(df) != 900:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 CSV contains {len(df)} rows (expected exactly 900).")

        dup_clips = df["recording_id"].duplicated().sum()
        if dup_clips > 0:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 CSV contains {dup_clips} duplicate recording IDs!")

        unique_speakers = df["speaker_id"].nunique()
        if unique_speakers != 60:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 CSV contains {unique_speakers} speakers (expected exactly 60).")

        clips_per_spk = df.groupby("speaker_id")["recording_id"].count()
        if not (clips_per_spk == 15).all():
            mismatched = (clips_per_spk != 15).sum()
            result["status"] = "FAIL"
            result["errors"].append(f"{mismatched} speakers do not have exactly 15 clips allocated.")

        stratum_col = (
            "stage5_accent_group"
            if "stage5_accent_group" in df.columns
            else ("stratum" if "stratum" in df.columns else ("group" if "group" in df.columns else None))
        )
        if not stratum_col:
            result["status"] = "FAIL"
            result["errors"].append("No stratum column found in Cohort 1 evaluation CSV.")
        else:
            strata_counts = df.groupby(stratum_col)["recording_id"].count().to_dict()
            if len(strata_counts) != 6:
                result["status"] = "FAIL"
                result["errors"].append(f"Cohort 1 CSV contains {len(strata_counts)} strata (expected 6).")
            for s_key, count in strata_counts.items():
                if count != 150:
                    result["status"] = "FAIL"
                    result["errors"].append(f"Stratum '{s_key}' has {count} clips (expected 150 = 10*15).")

        result["details"] = {
            "total_clips": len(df),
            "unique_speakers": unique_speakers,
            "duplicate_clip_count": int(dup_clips),
            "csv_sha256": csv_hash,
            "lock_sha256": lock_hash,
        }
        return result

    def validate_audio_materialization(
        self, eval_df: Optional[pd.DataFrame] = None, check_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Check 2: Cohort 1 Audio Materialization & 16 kHz Decodability.
        """
        result: Dict[str, Any] = {
            "check_name": "cohort1_audio_materialization",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.audio_dir.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 audio directory missing: {self.audio_dir}")
            return result

        mp3_files = list(self.audio_dir.glob("*.mp3"))
        if len(mp3_files) < 900:
            result["status"] = "FAIL"
            result["errors"].append(f"Cohort 1 audio directory contains {len(mp3_files)} files (expected >= 900).")

        # Zero-byte file check
        empty_files = [f.name for f in mp3_files if f.stat().st_size == 0]
        if empty_files:
            result["status"] = "FAIL"
            result["errors"].append(f"{len(empty_files)} Cohort 1 audio files have zero bytes (e.g. {empty_files[:3]}).")

        # Missing clips from evaluation CSV
        missing_clips: List[str] = []
        if eval_df is not None:
            actual_names = set(f.name for f in mp3_files)
            for rec_id in eval_df["recording_id"]:
                if f"{rec_id}.mp3" not in actual_names:
                    missing_clips.append(str(rec_id))

            if missing_clips:
                result["status"] = "FAIL"
                result["errors"].append(f"{len(missing_clips)} clips in Cohort 1 CSV lack physical audio files (e.g. {missing_clips[:3]}).")

        # Sample decode & resample test
        decode_tested = 0
        decode_failed = 0
        sample_files = mp3_files[:check_samples]
        for f in sample_files:
            try:
                waveform, sr = load_and_resample_audio(f, target_sr=16000)
                decode_tested += 1
                if sr != 16000 or len(waveform) == 0 or np.isnan(waveform).any() or np.isinf(waveform).any():
                    decode_failed += 1
            except Exception:
                decode_failed += 1

        if decode_failed > 0:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Cohort 1 audio decoding failure: {decode_failed}/{decode_tested} sampled audio files failed 16 kHz conversion."
            )

        result["details"] = {
            "total_audio_files": len(mp3_files),
            "expected_audio_files": 900,
            "empty_files_count": len(empty_files),
            "missing_clip_count": len(missing_clips),
            "decode_sample_tested": decode_tested,
            "decode_sample_failed": decode_failed,
        }
        return result

    def validate_sentinel_panel_and_isolation(
        self, eval_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Check 3: Sentinel Panel Integrity & Zero Speaker Leakage against Cohort 1.
        """
        result: Dict[str, Any] = {
            "check_name": "cohort1_sentinel_panel_and_isolation",
            "status": "PASS",
            "errors": [],
            "warnings": [],
            "details": {},
        }

        if not self.sentinel_csv_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel panel CSV missing: {self.sentinel_csv_path}")
            return result

        if not self.sentinel_lock_path.exists():
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel panel lock missing: {self.sentinel_lock_path}")
            return result

        sent_lock_hash = compute_sha256(self.sentinel_lock_path)
        if sent_lock_hash not in self.approved_sentinel_lock_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock file records unauthorized SHA-256 '{sent_lock_hash}' not in {self.approved_sentinel_lock_sha256}."
            )

        with open(self.sentinel_lock_path, "r", encoding="utf-8") as f:
            try:
                sent_lock = json.load(f)
            except Exception as e:
                result["status"] = "FAIL"
                result["errors"].append(f"Malformed sentinel lock JSON: {e}")
                return result

        sent_hash = compute_sha256(self.sentinel_csv_path)
        if sent_hash not in self.approved_sentinel_csv_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel panel CSV hash '{sent_hash}' not in approved allowlist {self.approved_sentinel_csv_sha256}."
            )

        valid_sent_hashes = {
            sent_lock.get("csv_sha256"),
            sent_lock.get("crlf_sha256"),
            sent_lock.get("lf_sha256"),
        } - {None}
        if sent_hash not in valid_sent_hashes:
            result["status"] = "FAIL"
            result["errors"].append(f"Sentinel CSV hash '{sent_hash}' not in lock declared digests {valid_sent_hashes}.")

        sent_crlf = sent_lock.get("crlf_sha256")
        sent_lf = sent_lock.get("lf_sha256")
        if sent_crlf and sent_crlf != self.expected_sentinel_csv_crlf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock records unauthorized 'crlf_sha256' '{sent_crlf}' (expected canonical CRLF '{self.expected_sentinel_csv_crlf_sha256}')."
            )
        if sent_lf and sent_lf != self.expected_sentinel_csv_lf_sha256:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Sentinel lock records unauthorized 'lf_sha256' '{sent_lf}' (expected canonical LF '{self.expected_sentinel_csv_lf_sha256}')."
            )

        try:
            sent_df = pd.read_csv(self.sentinel_csv_path)
        except Exception as e:
            result["status"] = "FAIL"
            result["errors"].append(f"Failed to parse sentinel CSV: {e}")
            return result

        if len(sent_df) != 300:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 300 sentinel panel records, got {len(sent_df)}")

        sent_spk_count = sent_df["speaker_id"].nunique()
        if sent_spk_count != CORE_SENTINEL_SPEAKERS:
            result["status"] = "FAIL"
            result["errors"].append(f"Expected 30 sentinel speakers, got {sent_spk_count}")

        # Core panel word count
        core_sentinel_df = sent_df.groupby("speaker_id").first().reset_index()
        core_word_count = sum(len(TextNormalizer.normalize(str(t)).split()) for t in core_sentinel_df["transcript"])
        if core_word_count != CORE_SENTINEL_WORDS:
            result["status"] = "FAIL"
            result["errors"].append(
                f"Core sentinel panel reference word count is {core_word_count} (expected {CORE_SENTINEL_WORDS})."
            )

        # Strict Speaker Isolation against Cohort 1
        overlap: Set[str] = set()
        if eval_df is not None:
            eval_spks = set(eval_df["speaker_id"].unique())
            sent_spks = set(sent_df["speaker_id"].unique())
            overlap = eval_spks.intersection(sent_spks)
            if overlap:
                result["status"] = "FAIL"
                result["errors"].append(
                    f"DATA LEAKAGE DETECTED! {len(overlap)} Cohort 1 evaluation speakers overlap with sentinel panel: {overlap}"
                )

        result["details"] = {
            "total_sentinel_records": len(sent_df),
            "core_sentinel_speakers": sent_spk_count,
            "core_sentinel_reference_words": core_word_count,
            "speaker_isolation_verified": len(overlap) == 0,
            "speaker_leakage_count": len(overlap),
        }
        return result

    def freeze_execution_configuration(self, model_name: str = "wav2vec2_base") -> Dict[str, Any]:
        """
        Check 4: Freeze Cohort 1 Execution Configuration.
        """
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "None (CPU Execution)"
        return {
            "check_name": "cohort1_execution_configuration_freeze",
            "status": "PASS",
            "governing_standard": "ADR-005",
            "model_architecture": model_name,
            "cohort": "cohort1",
            "total_evaluation_clips": 900,
            "window_size_k": 4,
            "total_stream_windows_w": 225,
            "hardware_device": gpu_name,
        }

    def run_preflight(
        self, model_name: str = "wav2vec2_base", check_audio_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Run all Cohort 1 preflight checks and generate overall status.
        """
        t0 = datetime.now(timezone.utc)
        git_rev = get_git_revision(self.root)

        # 1. Dataset & Lock Check
        dataset_res = self.validate_eval_dataset()

        # Load eval_df if valid
        eval_df = None
        if self.eval_csv_path.exists() and dataset_res["status"] == "PASS":
            try:
                eval_df = pd.read_csv(self.eval_csv_path)
            except Exception:
                pass

        # 2. Audio Materialization
        audio_res = self.validate_audio_materialization(eval_df=eval_df, check_samples=check_audio_samples)

        # 3. Sentinel Panel & Isolation
        sent_res = self.validate_sentinel_panel_and_isolation(eval_df=eval_df)

        # 4. Config Freeze
        cfg_res = self.freeze_execution_configuration(model_name=model_name)

        all_checks = [dataset_res, audio_res, sent_res, cfg_res]
        all_statuses = [c["status"] for c in all_checks]
        all_errors = [err for c in all_checks for err in c.get("errors", [])]

        if "FAIL" in all_statuses:
            overall_status = "HOLD"
            summary_desc = "FAIL_CLOSED_VALIDATION_ERROR: One or more technical integrity checks failed for Cohort 1."
        elif "HOLD" in all_statuses:
            overall_status = "HOLD"
            summary_desc = "COHORT1_PREREQUISITE_HOLD: One or more Cohort 1 prerequisites not materialized."
        else:
            overall_status = "READY FOR AUTHORIZED EXECUTION (COHORT 1)"
            summary_desc = "All Cohort 1 preflight integrity checks verified. Technical readiness established."

        return {
            "report_title": "Stage 6M Physical Cohort 1 Preflight Readiness Audit",
            "overall_status": overall_status,
            "summary_description": summary_desc,
            "status_reasons": all_errors,
            "timestamp_utc": t0.isoformat(),
            "git_commit": git_rev,
            "governing_standard": "ADR-005",
            "checks": {
                "cohort1_eval_dataset_integrity": dataset_res,
                "cohort1_audio_materialization": audio_res,
                "cohort1_sentinel_panel_and_isolation": sent_res,
                "cohort1_execution_configuration_freeze": cfg_res,
            },
        }

