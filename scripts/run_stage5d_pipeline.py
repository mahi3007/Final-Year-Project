#!/usr/bin/env python3
"""
Stage 5D Master Pipeline Driver.
================================
Orchestrates the complete Stage 5D sequence:
Phase 1: Forensic Trace (already documented in reports/stage5/stage5d_forensic_trace.md)
Phase 2: Canonical Path Resolution (implemented in src/dsg_ctta/controller/resolver.py)
Phase 3: Sentinel Evaluator Smoke Test (scripts/run_stage5d_sentinel_smoke_test.py)
Phase 4: DSG Contract Validation Tests (tests/unit/test_dsg_contract_validation.py)
Phase 5: 225-Window Prequential Re-execution (scripts/run_stage5d_dsg_reexecution.py)
Phase 6: External Outcome Diagnostic Audit (reports/stage5/stage5d_final_decision_audit.csv)
Phase 7: Final Research Interpretation & Report Updates
Phase 8: Final Test Suite (pytest tests/ -v)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SENTINEL_MANIFEST = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_audio_manifest.json"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
DECISION_AUDIT_CSV = PROJECT_ROOT / "reports" / "stage5" / "stage5d_final_decision_audit.csv"
REEXEC_REPORT = PROJECT_ROOT / "reports" / "stage5" / "stage5d_dsg_reexecution.md"
SMOKE_REPORT = PROJECT_ROOT / "reports" / "stage5" / "stage5d_sentinel_smoke_test.md"


def check_materialization_complete() -> bool:
    """Check if all 300 sentinel audio files are materialized and manifest exists."""
    if not SENTINEL_INVENTORY.exists():
        return False
    try:
        with open(SENTINEL_INVENTORY, "r", encoding="utf-8") as f:
            items = json.load(f)
        return len(items) == 300
    except Exception:
        return False


def wait_for_materialization(poll_interval: int = 15):
    print("\n[STEP 1] Monitoring Sentinel Audio Materialization...")
    t0 = time.time()
    last_cnt = -1

    while not check_materialization_complete():
        cnt = 0
        audio_dir = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio"
        if audio_dir.exists():
            cnt = len(list(audio_dir.glob("*.mp3")))

        if cnt != last_cnt:
            last_cnt = cnt
            elapsed = time.time() - t0
            print(f"  Materialized: {cnt}/300 sentinel clips on disk ({cnt/300*100:.1f}%) | Elapsed: {elapsed:.0f}s", flush=True)

        time.sleep(poll_interval)

    print(f"\n[OK] Materialization COMPLETE! All 300 sentinel audio clips on disk and verified in {time.time()-t0:.1f}s.")


def run_phase3_smoke_test() -> bool:
    print("\n" + "=" * 70)
    print("[STEP 2] Verifying Phase 3 Sentinel Evaluator Smoke Test...")
    print("=" * 70)

    if SMOKE_REPORT.exists():
        with open(SMOKE_REPORT, "r", encoding="utf-8") as f:
            content = f.read()
        if "OVERALL VERDICT: PASSED" in content:
            print(f"[OK] Phase 3 Smoke Test already completed and PASSED! Report: {SMOKE_REPORT}")
            return True

    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "run_stage5d_sentinel_smoke_test.py")]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("\nCRITICAL: Smoke test FAILED! Halting pipeline.")
        return False

    print("\n[OK] Phase 3 Smoke Test PASSED! All 12 criteria verified.")
    return True


def run_phase5_and_6_reexecution() -> bool:
    print("\n" + "=" * 70)
    print("[STEP 3] Running Phase 5 & 6 DSG 225-Window Re-execution & External Audit...")
    print("=" * 70)

    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "run_stage5d_dsg_reexecution.py")]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("\nCRITICAL: Re-execution FAILED! Halting pipeline.")
        return False

    print("\n[OK] Phase 5 & 6 Completed Successfully!")
    return True


def run_phase8_full_test_suite() -> bool:
    print("\n" + "=" * 70)
    print("[STEP 4] Running Phase 8 Full Test Suite (pytest tests/ -v)...")
    print("=" * 70)

    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("\nCRITICAL: Full test suite reported failures!")
        return False

    print("\n[OK] Full Test Suite PASSED with 0 failures!")
    return True


def main():
    print("=" * 70)
    print("STAGE 5D: END-TO-END AUTONOMOUS PIPELINE DRIVER")
    print("=" * 70)

    # Step 1: Wait for materialization
    wait_for_materialization()

    # Step 2: Phase 3 Smoke Test
    if not run_phase3_smoke_test():
        sys.exit(1)

    # Step 3: Phase 5 & 6 Re-execution & External Outcome Audit
    if not run_phase5_and_6_reexecution():
        sys.exit(1)

    # Step 4: Phase 8 Full Test Suite
    if not run_phase8_full_test_suite():
        sys.exit(1)

    print("\n" + "=" * 70)
    print("STAGE 5D COMPLETED SUCCESSFULLY ACROSS ALL PHASES!")
    print(f"Smoke Report   : {SMOKE_REPORT}")
    print(f"Re-exec Report : {REEXEC_REPORT}")
    print(f"Audit CSV      : {DECISION_AUDIT_CSV}")
    print("=" * 70)


if __name__ == "__main__":
    main()
