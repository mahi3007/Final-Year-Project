"""
Research Validity Test Runner with Provenance Capture
=====================================================
Standard: ADR-005 | Protocol: v1.4.0-stage6m-selective-adaptation-draft

Wraps pytest for the tests/research_validity/ suite and writes a provenance
header (Git commit SHA, pre-run working-tree cleanliness, execution timestamp,
Python version, exact command) to the saved log file together with the test
run output, AFTER pytest has executed against the untouched checkout.

Usage:
    python scripts/run_research_validity_tests.py [extra pytest args ...]

The log file is written to:
    reports/stage6m/research_validity_pytest_run.log
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "reports" / "stage6m" / "research_validity_pytest_run.log"


def _git(*args, cwd=PROJECT_ROOT) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def main():
    extra_args = sys.argv[1:]

    # 1. Capture repository state BEFORE launching pytest
    # Note: The tracked log file is NOT opened or written prior to execution,
    # ensuring that git working tree cleanliness is preserved during the test run.
    sha = _git("rev-parse", "HEAD")
    status_output_pre = _git("status", "--porcelain")
    clean_status_pre = "UNKNOWN" if status_output_pre == "UNKNOWN" else ("true" if status_output_pre == "" else "false")
    describe = _git("describe", "--tags", "--always", "--dirty")
    timestamp_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    python_ver = sys.version.replace("\n", " ")

    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/research_validity/",
        "-v",
        "--tb=short",
        *extra_args,
    ]
    cmd_display = "python -m pytest tests/research_validity/ -v --tb=short" + ((" " + " ".join(extra_args)) if extra_args else "")

    print(f"[runner] Repository state pre-run:")
    print(f"         git_commit_sha: {sha}")
    print(f"         git_working_tree_clean_pre_run: {clean_status_pre}")
    print(f"         git_describe: {describe}")
    print(f"         timestamp_utc: {timestamp_utc}")
    print(f"         command: {cmd_display}\n")
    print("[runner] Executing pytest against untouched working tree...")

    # 2. Execute pytest while working tree remains untouched
    proc = subprocess.run(
        pytest_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # 3. Capture post-execution working tree status before writing log
    status_output_post = _git("status", "--porcelain")
    clean_status_post = "UNKNOWN" if status_output_post == "UNKNOWN" else ("true" if status_output_post == "" else "false")

    cmd_exact = subprocess.list2cmdline(pytest_cmd)

    # 4. Construct complete provenance header
    header_lines = [
        "=== PROVENANCE HEADER ===",
        f"git_commit_sha: {sha}",
        f"git_working_tree_clean_pre_run: {clean_status_pre}",
        f"git_working_tree_clean_post_run: {clean_status_post}",
        "cleanliness_verification_scope: checked immediately before and immediately after subprocess execution; does not monitor in-flight transient filesystem modifications during execution",
        f"git_describe: {describe}",
        f"execution_timestamp_utc: {timestamp_utc}",
        f"python_version: {python_ver}",
        f"executable_path: {sys.executable}",
        f"command: {cmd_exact}",
        "=== END PROVENANCE HEADER ===",
        "",
    ]
    header_text = "\n".join(header_lines)

    # 5. Write provenance header and pytest results to log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(header_text + proc.stdout, encoding="utf-8")

    # 6. Stream captured output to stdout
    print(proc.stdout, end="")
    print(f"\n[runner] Log written to: {LOG_PATH.relative_to(PROJECT_ROOT)}")
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
