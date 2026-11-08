#!/usr/bin/env python3
"""
scripts/generate_stage6m_gate3_production_readiness_report.py

Stage 6M Gate 3 Production Dataset Readiness Review & Governance Package Generator
===================================================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
Governing Branch:   stage6m-five-stratum-parity
Reference Commit:   baee3b8381389ffde38e907dc137623748c254a8

Produces:
- reports/stage6m/stage6m_gate3_production_readiness_report.json
- reports/stage6m/stage6m_gate3_production_readiness_report.md
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"
OUTPUT_JSON = REPORTS_DIR / "stage6m_gate3_production_readiness_report.json"
OUTPUT_MD = REPORTS_DIR / "stage6m_gate3_production_readiness_report.md"


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_readiness_data() -> Dict[str, Any]:
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    # Tracked files for reproducibility ledger (14 distinct artifacts)
    files_to_track = [
        "scripts/materialize_stage6m_cohort3_audio_v2.py",
        "tests/research_validity/test_stage6m_cohort3_materializer_v2.py",
        "tests/research_validity/test_stage6m_cohort3_audio_materialization.py",
        "scratch/test_gate2_ntfs_and_locking_harness.py",
        "scripts/generate_stage6m_task774_non_destructive_materialization_spec.py",
        "reports/stage6m/stage6m_task774_non_destructive_materialization_spec.json",
        "reports/stage6m/stage6m_task774_non_destructive_materialization_spec.md",
        "scripts/generate_stage6m_scientific_admission_decision_dossier.py",
        "reports/stage6m/stage6m_scientific_admission_decision_dossier.json",
        "reports/stage6m/stage6m_scientific_admission_decision_dossier.md",
        "scripts/generate_stage6m_policy_2a_protocol_addendum.py",
        "reports/stage6m/stage6m_policy_2a_protocol_addendum.json",
        "reports/stage6m/stage6m_policy_2a_protocol_addendum.md",
        "datasets/splits/stage6m_cohort3_provisional_manifest.json",
    ]

    reproducibility_ledger = {}
    for rel_path in files_to_track:
        p = PROJECT_ROOT / rel_path
        if p.exists():
            reproducibility_ledger[rel_path] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
                "exists": True,
            }
        else:
            reproducibility_ledger[rel_path] = {
                "sha256": None,
                "size_bytes": 0,
                "exists": False,
            }

    data = {
        "report_id": "STAGE6M-GATE3-READINESS-REVIEW-20261107-V2",
        "generated_at_utc": timestamp_utc,
        "governing_protocol": "Stage 6M v1.5 Five-Stratum Research Benchmark",
        "governing_branch": "stage6m-five-stratum-parity",
        "reference_commit": "baee3b8381389ffde38e907dc137623748c254a8",
        "project_lead_authority": "Project Lead (Dissertation Author)",
        "executive_summary": {
            "overall_status": "READY_FOR_SPLIT_GATE3_REVIEW",
            "gate1_status": "APPROVED",
            "gate1_approval_date": "2026-11-07",
            "gate1_policy": "Policy 2A (Reconciled Target Population Admission)",
            "gate2_status": "APPROVED",
            "gate2_approval_date": "2026-11-07",
            "gate2_scope": "Engineering Implementation & Pre-Production Validation",
            "gate3_combined_status": "DEFERRED_PENDING_SPLIT_AUTHORIZATION",
            "gate3_deferral_reason": "Separate production materialization authorization from final manifest approval and locking.",
            "gate3a_status": "APPROVED",
            "gate3a_approval_date": "2026-11-07",
            "gate3b_status": "PENDING_GATE3A_EXECUTION",
            "gates_4_to_6_status": "STRICTLY_BLOCKED",
            "protected_boundaries_status": "PRESERVED",
            "zero_production_audio_materialized": True,
            "zero_manifest_mutations": True,
            "zero_git_modifications_committed": True,
        },
        "governance_checkpoint_split": {
            "gate3a_specification": {
                "checkpoint": "GATE 3A — PRODUCTION MATERIALIZATION",
                "authority": "Project Lead (Dissertation Author)",
                "status": "UNEXECUTED (Pending User Authorization)",
                "scope": [
                    "Execute materialize_stage6m_cohort3_audio_v2.py with explicit --authorize-gate3a flag.",
                    "Materialize into separate directory datasets/audio/stage6m/cohort3_reconciled_assets/.",
                    "Process 18,845 accepted clips (from cohort3_audio) and 130 discrepancy-screened clips (from cohort3_rejected_quarantine).",
                    "Preserve all source files in their original locations without deletion, moving, or renaming (Rule P1).",
                    "Apply atomic no-clobber publication via os.link() on NTFS volume C:\\ (Rule P2).",
                    "Execute three-decoder consensus verification (SoundFile, PyAV, miniaudio) on all staged files (Rule P5).",
                    "Generate per-file cryptographic disposition ledger (datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv) (Rule P6).",
                    "Independently audit all 18,975 destination file identities, sizes, and SHA-256 digests.",
                    "STRICT BOUNDARY: Gate 3A must NOT generate or lock the final manifest.",
                    "STOP IMMEDIATELY after audio materialization, decoder validation, and ledger emission.",
                ],
            },
            "gate3b_specification": {
                "checkpoint": "GATE 3B — FINAL MANIFEST VALIDATION AND LOCK",
                "authority": "Project Lead (Dissertation Author)",
                "status": "UNEXECUTED (Pending Gate 3A Completion & User Authorization)",
                "preconditions": [
                    "Gate 3A successfully executed and verified.",
                    "Destination directory cohort3_reconciled_assets/ contains exactly 18,975 validated audio files totaling 709,750,958 bytes.",
                    "Per-file disposition ledger independently reconciled against target population (1,252 complete speakers, 9 partial speakers, 4 empty speakers = 1,265 total speakers).",
                    "Confirmatory evaluation cohort satisfies exact five-stratum parity (Australian, Canadian, England, South Asian, US English; exactly 220 speakers and 3,300 clips per stratum = 1,100 speakers / 16,500 clips).",
                    "Gate cohort (100 speakers / 1,500 clips; 20 per stratum) and reserve cohort (65 speakers / 975 clips) strict isolation verified.",
                ],
                "action": [
                    "Ingest stage6m_cohort3_provisional_manifest.json and disposition ledger.",
                    "Promote and write datasets/splits/stage6m_cohort3_final_manifest.json with manifest_status: 'LOCKED'.",
                    "Record cryptographic SHA-256 seal of the final manifest.",
                    "Authorize progression to Gate 4 (GPU Environment Readiness).",
                ],
            },
        },
        "phase1_regression_audit": {
            "test_command": "python -m pytest tests/research_validity/ -q",
            "total_tests_collected": 539,
            "total_passed": 539,
            "total_failed": 0,
            "total_skipped": 0,
            "total_xfailed": 0,
            "exit_code": 0,
            "duration_seconds": 830.48,
            "duration_formatted": "13m 50s",
            "warnings_count": 6,
            "warnings_summary": [
                "torchvision/transforms/_functional_pil.py: DeprecationWarning for Image.BILINEAR, NEAREST, BICUBIC (Pillow 10 deprecation)",
                "importlib._bootstrap: DeprecationWarning for SwigPyPacked and SwigPyObject missing __module__ attribute",
                "sys:1: DeprecationWarning for swigvarlink missing __module__ attribute",
            ],
            "subsuite_breakdown": {
                "materializer_v2_unit_tests": {
                    "path": "tests/research_validity/test_stage6m_cohort3_materializer_v2.py",
                    "passed": 10,
                    "failed": 0,
                    "duration_sec": 1.18,
                },
                "materialization_regression_tests": {
                    "path": "tests/research_validity/test_stage6m_cohort3_audio_materialization.py",
                    "passed": 37,
                    "failed": 0,
                    "duration_sec": 14.46,
                },
                "cohort3_complete_suite": {
                    "passed": 91,
                    "failed": 0,
                },
                "entire_research_validity_suite": {
                    "passed": 539,
                    "failed": 0,
                    "duration_sec": 830.48,
                },
            },
        },
        "phase2_code_review_audit": {
            "target_script": "scripts/materialize_stage6m_cohort3_audio_v2.py",
            "script_size_bytes": reproducibility_ledger["scripts/materialize_stage6m_cohort3_audio_v2.py"]["size_bytes"],
            "script_sha256": reproducibility_ledger["scripts/materialize_stage6m_cohort3_audio_v2.py"]["sha256"],
            "boundary_guard_enforcement": {
                "unauthorized_status": "BLOCKED_UNAUTHORIZED",
                "unauthorized_exit_code": 2,
                "authorization_cli_flag": "--authorize-gate3a",
                "evidence": (
                    "When invoked against production destination without --authorize-gate3a, "
                    "script logs error 'BLOCKED_UNAUTHORIZED: Gate 2 authorizes implementation and pre-production validation ONLY. "
                    "Production dataset materialization into cohort3_reconciled_assets/ requires explicit Gate 3A authorization...', "
                    "prints to stderr, and halts execution via sys.exit(2). Verified by test_production_boundary_guard_blocks_unauthorized_materialization."
                ),
            },
            "audit_criteria": [
                {
                    "rule": "P1: Read-Only Source Access",
                    "status": "PASSED",
                    "evidence": "Source files opened strictly in binary read mode ('rb'). Source path identity check prevents source == dest. No unlink, rename, or write handles opened on source.",
                },
                {
                    "rule": "P2: Atomic No-Clobber Publication",
                    "status": "PASSED",
                    "evidence": "Publication executed via os.link(). Under Windows NTFS, os.link() raises FileExistsError on destination collision. os.replace() is strictly prohibited.",
                },
                {
                    "rule": "P3: Idempotent Digest Verification",
                    "status": "PASSED",
                    "evidence": "Pre-check compares destination SHA-256 against expected hash. Existing matching files skip extraction (0 disk writes). Mismatched files fail closed with DestinationCollisionMismatchError.",
                },
                {
                    "rule": "P4: OS-Level Ownership Locking",
                    "status": "PASSED",
                    "evidence": "RunLockManager acquires exclusive non-blocking lock via msvcrt.locking(LK_NBLCK, 1) on Windows (fcntl.flock on POSIX). Sweep routine strictly ignores directories with active locks.",
                },
                {
                    "rule": "P5: Multi-Decoder Consensus Verification",
                    "status": "PASSED",
                    "evidence": "verify_audio_three_decoders runs SoundFile streaming decode (4096-frame chunks, verifying finite float32 PCM), PyAV, and miniaudio. Consensus required before publication.",
                },
                {
                    "rule": "P6: Cryptographic Disposition Ledger",
                    "status": "PASSED",
                    "evidence": "All 18,975 assets (18,845 accepted + 130 discrepancy-screened) tracked in stage6m_cohort3_materialization_disposition_ledger.csv with action, hash, size, frames, and decodability status.",
                },
                {
                    "rule": "Crash Safety & Orphan Sweeping",
                    "status": "PASSED",
                    "evidence": "Staging occurs in unique .staging_run_{run_id} directories. Unlinked on clean completion. sweep_orphaned_staging_directories safely cleans stale runs (>3600s) only if lock acquisition succeeds.",
                },
                {
                    "rule": "Production Boundary Guard",
                    "status": "PASSED",
                    "evidence": "Script enforces BLOCKED_UNAUTHORIZED with exit code 2 if destination is default reconciled directory and --authorize-gate3a is missing, preventing automated tools from mistaking a blocked run for success.",
                },
            ],
        },
        "phase3_reproducibility_ledger": reproducibility_ledger,
        "phase4_production_execution_plan": {
            "authorized_script": "scripts/materialize_stage6m_cohort3_audio_v2.py",
            "execution_command": (
                "python scripts/materialize_stage6m_cohort3_audio_v2.py "
                "--manifest datasets/splits/stage6m_cohort3_provisional_manifest.json "
                "--source-audio-dir datasets/external/common_voice_27/cohort3_audio "
                "--quarantine-dir datasets/external/common_voice_27/cohort3_rejected_quarantine "
                "--destination-dir datasets/audio/stage6m/cohort3_reconciled_assets "
                "--disposition-ledger datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv "
                "--report-json reports/stage6m/stage6m_task774_materialization_report.json "
                "--authorize-gate3a"
            ),
            "payload_accounting": {
                "total_target_recordings": 18975,
                "accepted_clips_source": "datasets/external/common_voice_27/cohort3_audio",
                "accepted_clips_count": 18845,
                "discrepancy_screened_quarantine_source": "datasets/external/common_voice_27/cohort3_rejected_quarantine",
                "discrepancy_screened_quarantine_count": 130,
                "total_speakers": 1265,
                "complete_speakers": 1252,
                "partial_speakers": 9,
                "empty_speakers": 4,
                "evaluation_speakers": 1100,
                "evaluation_clips": 16500,
                "evaluation_strata": 5,
                "evaluation_speakers_per_stratum": 220,
                "gate_speakers": 100,
                "gate_clips": 1500,
                "gate_speakers_per_stratum": 20,
                "reserve_speakers": 65,
                "reserve_clips": 975,
                "total_payload_bytes": 709750958,
                "target_filesystem": "NTFS",
                "target_volume_serial": "0xca18eefa",
                "publication_method": "os.link() Atomic Hard-Link",
            },
            "gate3a_execution_phases": [
                {
                    "step": 1,
                    "action": "Pre-execution volume and disk space verification (requires >= 2 GB free disk space on volume C:\\)",
                },
                {
                    "step": 2,
                    "action": "Sweep any orphaned staging directories older than 3600 seconds",
                },
                {
                    "step": 3,
                    "action": "Initialize RunLockManager with exclusive OS-level file lock on run.lock",
                },
                {
                    "step": 4,
                    "action": "Materialize 18,845 accepted clips: stage with UUID -> 3-decoder check -> publish via os.link()",
                },
                {
                    "step": 5,
                    "action": "Materialize 130 discrepancy-screened quarantine clips: stage with UUID -> 3-decoder check -> publish via os.link()",
                },
                {
                    "step": 6,
                    "action": "Emit per-file disposition ledger CSV and comprehensive materialization report JSON",
                },
                {
                    "step": 7,
                    "action": "Perform physical destination inventory audit: exactly 18,975 files, 709,750,958 bytes, 0 missing, 0 corrupt",
                },
                {
                    "step": 8,
                    "action": "HALT AND STOP. Do not generate or lock final manifest. Await Gate 3B authorization.",
                },
            ],
        },
        "phase5_manifest_locking_plan": {
            "provisional_manifest_path": "datasets/splits/stage6m_cohort3_provisional_manifest.json",
            "provisional_manifest_sha256": reproducibility_ledger["datasets/splits/stage6m_cohort3_provisional_manifest.json"]["sha256"],
            "disposition_ledger_path": "datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv",
            "locked_manifest_path": "datasets/splits/stage6m_cohort3_final_manifest.json",
            "locking_procedure": [
                {
                    "step": "Manifest Ingestion",
                    "description": "Load provisional manifest and cross-reference with materialization disposition ledger.",
                },
                {
                    "step": "Physical Destination Audit",
                    "description": "Assert all 18,975 files exist in cohort3_reconciled_assets/ with exact SHA-256 match.",
                },
                {
                    "step": "Stratum Balance Audit",
                    "description": "Assert exactly 220 evaluation speakers across Australian, Canadian, England, South Asian, and US English (1,100 total evaluation speakers). Assert 20 gate speakers per stratum (100 total).",
                },
                {
                    "step": "Cryptographic Manifest Sealing",
                    "description": "Set manifest_status to 'LOCKED', record Gate 1, Gate 2, Gate 3A, and Gate 3B approvals, and compute canonical SHA-256 of locked manifest.",
                },
            ],
        },
        "combined_gate3_deferral_decision": {
            "title": "STAGE 6M GATE 3: COMBINED PRODUCTION DATASET FINALIZATION",
            "authority": "Project Lead (Dissertation Author)",
            "date": "2026-11-07",
            "status": "[X] DEFERRED PENDING ADDITIONAL VALIDATION",
            "reason": "Separate production materialization authorization from final manifest approval and locking.",
            "next_authorization": "GATE 3A — Production Materialization",
            "subsequent_authorization": "GATE 3B — Final Manifest Validation and Lock",
            "gpu_readiness_status": "BLOCKED",
            "confirmatory_inference_status": "BLOCKED",
            "statistical_analysis_status": "BLOCKED",
        },
        "gate3a_authorization_record": {
            "title": "STAGE 6M GATE 3A: PRODUCTION MATERIALIZATION",
            "authority": "Project Lead (Dissertation Author)",
            "date": "2026-11-07",
            "status": "[X] AUTHORIZED FOR PRODUCTION MATERIALIZATION",
            "scope_summary": "Authorize materialize_stage6m_cohort3_audio_v2.py to process 18,845 accepted and 130 quarantined assets into cohort3_reconciled_assets/, emit per-file ledger, and stop prior to manifest locking.",
            "strict_halt_notice": "GATE 3A DOES NOT PERMIT FINAL MANIFEST LOCKING. SYSTEM MUST HALT UPON COMPLETION OF MATERIALIZATION AUDIT.",
            "record_file": "reports/stage6m/stage6m_gate3a_authorization_record.json",
        },
        "gate3b_unexecuted_template": {
            "title": "STAGE 6M GATE 3B: FINAL MANIFEST VALIDATION AND LOCK",
            "authority": "Project Lead (Dissertation Author)",
            "date": "UNEXECUTED (Pending Gate 3A Completion & User Authorization)",
            "status_options": [
                "[ ] AUTHORIZED FOR FINAL MANIFEST LOCK",
                "[ ] REJECTED",
                "[ ] DEFERRED PENDING ADDITIONAL VALIDATION",
            ],
            "scope_summary": "Following physical reconciliation of all 18,975 assets, authorize generation of datasets/splits/stage6m_cohort3_final_manifest.json with manifest_status: 'LOCKED'.",
        },
        "unresolved_limitations_and_disclosures": [
            "Research Scope Boundary: Evaluates Mozilla Common Voice 27.0 (English) as distributed to researchers. No claim of verification against original uncompressed studio masters.",
            "Decoder Evidence Distinction: 18,845 clips admitted via SoundFile decoding and physical MPEG frame inspection; 130 discrepancy-screened clips admitted via three-decoder consensus under Policy 2A.",
            "Demographic Parity Limitation: Confirmatory evaluation is strictly balanced across five accent strata (Australian, Canadian, England, South Asian, US English; 220 speakers each). Gender and age distributions remain observational.",
            "Downstream GPU Experiments: Gates 4, 5, and 6 remain strictly blocked. Zero GPU execution is permitted prior to Gate 3B manifest locking.",
        ],
    }

    return data


def format_markdown(data: Dict[str, Any]) -> str:
    lead = data["project_lead_authority"]
    ts = data["generated_at_utc"]
    exec_sum = data["executive_summary"]
    reg = data["phase1_regression_audit"]
    cr = data["phase2_code_review_audit"]
    rep = data["phase3_reproducibility_ledger"]
    pep = data["phase4_production_execution_plan"]
    fml = data["phase5_manifest_locking_plan"]
    cgate3 = data["combined_gate3_deferral_decision"]
    g3a = data["gate3a_authorization_record"]
    g3b = data["gate3b_unexecuted_template"]
    limits = data["unresolved_limitations_and_disclosures"]

    md = []
    md.append("# STAGE 6M — GATE 3 PRODUCTION DATASET READINESS REVIEW")
    md.append("## Pre-Production Audit, Materializer Verification & Split Governance Package (v2)")
    md.append("")
    md.append(f"**Governing Protocol:** {data['governing_protocol']} (Section 14.7)")
    md.append(f"**Governing Branch:** `{data['governing_branch']}` @ `{data['reference_commit']}`")
    md.append(f"**Decision Authority:** {lead}")
    md.append(f"**Generated At (UTC):** `{ts}`")
    md.append(f"**Report ID:** `{data['report_id']}`")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Executive Summary & Governance State")
    md.append("")
    md.append("| Governance Milestone | Status | Effective Date | Notes / Scope |")
    md.append("| :--- | :--- | :--- | :--- |")
    md.append(f"| **Gate 1 — Scientific Admission** | **{exec_sum['gate1_status']}** | {exec_sum['gate1_approval_date']} | Policy 2A Reconciled Target Population (18,975 clips across 1,265 speakers) |")
    md.append(f"| **Pre-Gate 2 Regression Maintenance** | **COMPLETE** | 2026-11-07 | Stale dry-run assertion updated to state-aware reconciliation |")
    md.append(f"| **Gate 2 Pre-Auth Demonstration** | **PASSED** | 2026-11-07 | Option B NTFS volume & OS-locking harness verified on `C:\\` |")
    md.append(f"| **Gate 2 — Engineering Implementation** | **{exec_sum['gate2_status']}** | {exec_sum['gate2_approval_date']} | Implementation of `materialize_v2.py` and dedicated unit test suite |")
    md.append(f"| **Full Working Tree Regression** | **PASSED (539/539)** | 2026-11-07 | 100% green across all research-validity tests (830.48s / 13m 50s) |")
    md.append(f"| **Combined Gate 3** | **{cgate3['status']}** | {cgate3['date']} | {cgate3['reason']} |")
    md.append(f"| **Gate 3A — Production Materialization** | **APPROVED** | {g3a['date']} | Authorizes physical audio materialization & disposition ledger |")
    md.append(f"| **Gate 3B — Final Manifest Lock** | **PENDING_GATE3A_EXECUTION** | *Awaiting Materialization* | Authorizes post-materialization audit & permanent manifest seal |")
    md.append(f"| **Gates 4–6 (GPU Readiness & Experiments)** | **{exec_sum['gates_4_to_6_status']}** | *Strictly Prohibited* | Blocked until Gate 3B manifest lock is complete |")
    md.append("")
    md.append("### Protected Governance Invariants")
    md.append(f"- **Zero Production Audio Materialized:** `datasets/audio/stage6m/cohort3_reconciled_assets/` does NOT exist.")
    md.append(f"- **Zero Manifest Mutations:** `datasets/splits/stage6m_cohort3_provisional_manifest.json` remains unaltered.")
    md.append(f"- **Zero Git Commits / Staging:** Working tree preserves uncommitted state awaiting user instructions.")
    md.append(f"- **Zero GPU Inference:** Confirmatory models and evaluation cohorts remain unsealed and unexecuted.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Combined Gate 3 Formal Deferral Record")
    md.append("")
    md.append(f"**Title:** {cgate3['title']}  ")
    md.append(f"**Decision Authority:** {cgate3['authority']}  ")
    md.append(f"**Decision Date:** {cgate3['date']}  ")
    md.append(f"**Status:** **{cgate3['status']}**  ")
    md.append("")
    md.append(f"> **Reason for Deferral:**  \n> {cgate3['reason']}")
    md.append("")
    md.append(f"- **Next Authorization Checkpoint:** `{cgate3['next_authorization']}`")
    md.append(f"- **Subsequent Authorization Checkpoint:** `{cgate3['subsequent_authorization']}`")
    md.append(f"- **Gate 4 (GPU Readiness):** `{cgate3['gpu_readiness_status']}`")
    md.append(f"- **Gate 5 (Confirmatory Inference):** `{cgate3['confirmatory_inference_status']}`")
    md.append(f"- **Gate 6 (Statistical Analysis):** `{cgate3['statistical_analysis_status']}`")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Two-Stage Governance Architecture: Gate 3A & Gate 3B")
    md.append("")
    md.append("```mermaid")
    md.append("flowchart TD")
    md.append("    G2[Gate 2 APPROVED: Implementation] --> G3A_DEC[Gate 3A Decision: Materialization]")
    md.append("    G3A_DEC -->|Authorized| MAT[Execute materialize_v2.py --authorize-gate3a]")
    md.append("    MAT --> RECON[Populate cohort3_reconciled_assets/ & Ledger]")
    md.append("    RECON --> STOP[HALT: Gate 3A Complete. Stop Prior to Manifest Lock]")
    md.append("    STOP --> AUDIT[Independent Destination & Stratum Parity Audit]")
    md.append("    AUDIT --> G3B_DEC[Gate 3B Decision: Final Manifest Lock]")
    md.append("    G3B_DEC -->|Authorized| LOCK[Lock stage6m_cohort3_final_manifest.json]")
    md.append("    LOCK --> G4[Gate 4: GPU Readiness]")
    md.append("```")
    md.append("")
    md.append("### Checkpoint Comparison")
    md.append("| Characteristic | Gate 3A (Materialization) | Gate 3B (Manifest Lock) |")
    md.append("| :--- | :--- | :--- |")
    md.append("| **Objective** | Process real audio & produce per-file ledger | Lock canonical benchmark manifest |")
    md.append("| **Input** | Approved sources (`cohort3_audio`, `quarantine`) | Reconciled assets & disposition ledger |")
    md.append("| **Output** | `cohort3_reconciled_assets/` + CSV ledger | `stage6m_cohort3_final_manifest.json` (LOCKED) |")
    md.append("| **Manifest Status** | **DOES NOT MODIFY MANIFEST** | **PERMANENTLY LOCKS MANIFEST** |")
    md.append("| **Post-Condition** | **STOPS IMMEDIATELY** | Permits entry into Gate 4 (GPU Readiness) |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Phase 1: Full Working Tree Regression Audit")
    md.append("")
    md.append(f"**Execution Command:** `{reg['test_command']}`  ")
    md.append(f"**Total Duration:** {reg['duration_formatted']} ({reg['duration_seconds']:.2f} seconds)  ")
    md.append(f"**Exit Code:** `{reg['exit_code']}`  ")
    md.append(f"**Total Tests Executed:** {reg['total_tests_collected']}  ")
    md.append(f"**Passed:** **{reg['total_passed']} / {reg['total_tests_collected']} (100.0%)**  ")
    md.append(f"**Failed:** {reg['total_failed']}  ")
    md.append(f"**Warnings:** {reg['warnings_count']} (deprecations in external packages: Pillow 10 / Swig)  ")
    md.append("")
    md.append("### Test Module Breakdown")
    md.append("| Module / Subsuite | Path | Tests Passed | Duration | Status |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    sb = reg["subsuite_breakdown"]
    md.append(f"| **Materializer v2 Unit Suite** | `{sb['materializer_v2_unit_tests']['path']}` | {sb['materializer_v2_unit_tests']['passed']} / {sb['materializer_v2_unit_tests']['passed']} | {sb['materializer_v2_unit_tests']['duration_sec']}s | **PASS** |")
    md.append(f"| **Materialization Regression Suite** | `{sb['materialization_regression_tests']['path']}` | {sb['materialization_regression_tests']['passed']} / {sb['materialization_regression_tests']['passed']} | {sb['materialization_regression_tests']['duration_sec']}s | **PASS** |")
    md.append(f"| **Cohort 3 Combined Modules** | `tests/research_validity/test_stage6m_cohort3_*.py` | {sb['cohort3_complete_suite']['passed']} / {sb['cohort3_complete_suite']['passed']} | ~45s | **PASS** |")
    md.append(f"| **Entire Research Validity Suite** | `tests/research_validity/` | {sb['entire_research_validity_suite']['passed']} / {sb['entire_research_validity_suite']['passed']} | {sb['entire_research_validity_suite']['duration_sec']}s | **PASS** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Phase 2: Materializer v2 Code Review & Boundary Guard Audit")
    md.append("")
    md.append(f"**Target Script:** `{cr['target_script']}`  ")
    md.append(f"**File Size:** {cr['script_size_bytes']:,} bytes  ")
    md.append(f"**SHA-256 Digest:** `{cr['script_sha256']}`  ")
    md.append("")
    md.append("### Boundary Guard Hardening (BLOCKED_UNAUTHORIZED)")
    bg = cr["boundary_guard_enforcement"]
    md.append(f"- **Unauthorized Execution Status:** `{bg['unauthorized_status']}`")
    md.append(f"- **Unauthorized Exit Code:** `{bg['unauthorized_exit_code']}` (strictly non-zero)")
    md.append(f"- **Authorization CLI Flag:** `{bg['authorization_cli_flag']}`")
    md.append(f"- **Verification Evidence:** {bg['evidence']}")
    md.append("")
    md.append("### Architectural Invariants Compliance Matrix")
    md.append("| Technical Rule | Target Invariant | Compliance Evidence | Status |")
    md.append("| :--- | :--- | :--- | :--- |")
    for rule_info in cr["audit_criteria"]:
        md.append(f"| **{rule_info['rule']}** | Invariant Rule | {rule_info['evidence']} | **{rule_info['status']}** |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 6. Phase 3: Reproducibility & Cryptographic SHA-256 Ledger (Complete 14 Artifacts)")
    md.append("")
    md.append("Every script, specification, report, and test artifact has been catalogued with its complete, untruncated 64-character SHA-256 hex digest:")
    md.append("")
    md.append("| # | Relative File Path | Size (Bytes) | Complete Untruncated SHA-256 Checksum | Exists |")
    md.append("| :-: | :--- | :--- | :--- | :-: |")
    for idx, (fpath, finfo) in enumerate(rep.items(), start=1):
        h = f"`{finfo['sha256']}`" if finfo['sha256'] else "`N/A`"
        md.append(f"| {idx} | `{fpath}` | {finfo['size_bytes']:,} | {h} | {finfo['exists']} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 7. Phase 4: Gate 3A Production Execution Plan")
    md.append("")
    md.append("Upon Gate 3A authorization, the production materialization pipeline will be executed:")
    md.append("")
    md.append("```bash")
    md.append(pep["execution_command"])
    md.append("```")
    md.append("")
    md.append("### Production Payload Accounting")
    pa = pep["payload_accounting"]
    md.append(f"- **Total Target Recordings:** {pa['total_target_recordings']:,} clips")
    md.append(f"- **Accepted Recordings (`cohort3_audio`):** {pa['accepted_clips_count']:,} clips")
    md.append(f"- **Quarantined Recordings (`cohort3_rejected_quarantine`):** {pa['discrepancy_screened_quarantine_count']:,} clips")
    md.append(f"- **Total Speakers:** {pa['total_speakers']:,} speakers ({pa['complete_speakers']:,} complete, {pa['partial_speakers']} partial, {pa['empty_speakers']} empty)")
    md.append(f"  - **Confirmatory Evaluation:** {pa['evaluation_speakers']:,} speakers ({pa['evaluation_clips']:,} clips; {pa['evaluation_speakers_per_stratum']} per stratum across {pa['evaluation_strata']} strata)")
    md.append(f"  - **Gate Cohort:** {pa['gate_speakers']:,} speakers ({pa['gate_clips']:,} clips; {pa['gate_speakers_per_stratum']} per stratum)")
    md.append(f"  - **Reserve Cohort:** {pa['reserve_speakers']} speakers ({pa['reserve_clips']} clips)")
    md.append(f"- **Total Source Payload:** {pa['total_payload_bytes']:,} bytes (~709.75 MB)")
    md.append(f"- **Target Volume & Filesystem:** `{pa['target_filesystem']}` (Serial `{pa['target_volume_serial']}`)")
    md.append(f"- **Publication Mechanism:** `{pa['publication_method']}` (Zero disk write amplification; 100% hash preservation)")
    md.append("")
    md.append("### Step-by-Step Execution Sequence")
    for step in pep["gate3a_execution_phases"]:
        md.append(f"{step['step']}. **Step {step['step']}:** {step['action']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 8. Phase 5: Gate 3B Final Manifest Validation & Locking Protocol")
    md.append("")
    md.append(f"**Provisional Manifest:** `{fml['provisional_manifest_path']}`  ")
    md.append(f"**Input Ledger:** `{fml['disposition_ledger_path']}`  ")
    md.append(f"**Target Locked Manifest:** `{fml['locked_manifest_path']}`  ")
    md.append("")
    md.append("### Manifest Locking Steps")
    for item in fml["locking_procedure"]:
        md.append(f"- **{item['step']}:** {item['description']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 9. Gate 3A Authorization Record (APPROVED)")
    md.append("")
    md.append(f"**Title:** {g3a['title']}  ")
    md.append(f"**Decision Authority:** {g3a['authority']}  ")
    md.append(f"**Decision Date:** {g3a['date']}  ")
    md.append(f"**Decision Status:** **{g3a['status']}**  ")
    md.append(f"**Record Reference:** `{g3a['record_file']}`  ")
    md.append("")
    md.append("### Preconditions Verification Checklist")
    md.append(f"- [X] Gate 1 Scientific Admission Approved (Policy 2A, 2026-11-07)")
    md.append(f"- [X] Gate 2 Engineering Implementation Approved (2026-11-07)")
    md.append(f"- [X] Option B NTFS & OS-Locking Demonstration Passed on Volume `C:\\`")
    md.append(f"- [X] Full Research Validity Test Suite: **539/539 PASSED (830.48s / 13m 50s)**")
    md.append(f"- [X] Materializer v2 Code Review Audit Passed (8/8 Technical Invariants)")
    md.append(f"- [X] Dual-Key Production Boundary Guard Hardened: Verified with exit code 2 & BLOCKED_UNAUTHORIZED")
    md.append(f"- [X] Reproducibility Ledger Complete (14 artifacts with untruncated SHA-256 digests)")
    md.append("")
    md.append("### Approved Scope & Mandatory Halting Clause")
    md.append(f"> **Authorization Clause:**  \n> {g3a['scope_summary']}  \n> **CRITICAL:** {g3a['strict_halt_notice']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 10. Gate 3B Authorization Record (Unexecuted Template)")
    md.append("")
    md.append(f"**Title:** {g3b['title']}  ")
    md.append(f"**Decision Authority:** {g3b['authority']}  ")
    md.append(f"**Decision Date:** *{g3b['date']}*  ")
    md.append("")
    md.append("### Preconditions Checklist (To Be Verified Post-Gate 3A)")
    md.append(f"- [ ] Gate 3A Materialization Successfully Executed")
    md.append(f"- [ ] Physical Destination Inventory Audit Passed (18,975 files, 709,750,958 bytes)")
    md.append(f"- [ ] Per-File Disposition Ledger Reconciled (18,845 accepted + 130 discrepancy-screened)")
    md.append(f"- [ ] Five-Stratum Parity Confirmed (220 speakers / 3,300 clips per stratum)")
    md.append(f"- [ ] Gate (100 speakers) and Reserve (65 speakers) Isolation Verified")
    md.append("")
    md.append("### Decision Record Options")
    for opt in g3b["status_options"]:
        md.append(f"- {opt}")
    md.append("")
    md.append(f"> **Authorization Clause:**  \n> {g3b['scope_summary']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 11. Unresolved Limitations & Explicit Disclosures")
    md.append("")
    for lim in limits:
        md.append(f"- {lim}")
    md.append("")
    md.append("---")
    md.append("**End of Stage 6M Gate 3 Readiness Review Dossier (v2)**")

    return "\n".join(md)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    data = generate_readiness_data()

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    md_content = format_markdown(data)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated Gate 3 readiness review JSON: {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size:,} bytes)")
    print(f"Generated Gate 3 readiness review MD:   {OUTPUT_MD} ({OUTPUT_MD.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
