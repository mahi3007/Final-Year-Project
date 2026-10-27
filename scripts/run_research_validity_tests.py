"""
Research Validity Test Runner with Provenance Capture
=====================================================
Standard: ADR-005 | Protocol: v1.4.0-stage6m-selective-adaptation-draft

Wraps pytest for the tests/research_validity/ suite and prepends a provenance
header (Git commit SHA, working-tree cleanliness, execution timestamp, Python
version) to the saved log file so that every test run is reproducibly bound to
an exact repository state.

Usage:
    python scripts/run_research_validity_tests.py [extra pytest args ...]

The log file is always written to:
    reports/stage6m/research_validity_pytest_run.log

The provenance header format is:
    === PROVENANCE HEADER ===
    git_commit_sha: <40-char SHA or UNKNOWN>
    git_working_tree_clean: <true|false|UNKNOWN>
    git_describe: <describe output>
    execution_timestamp_utc: <ISO 8601>
    python_version: <version>
    command: <full command string>
    === END PROVENANCE HEADER ===
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "reports" / "stage6m" / "research_validity_pytest_run.log"


def _git(*args, cwd=PROJECT_ROOT):
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def build_provenance_header(extra_args):
    sha = _git("rev-parse", "HEAD")
    status_output = _git("status", "--porcelain")
    clean_status = "UNKNOWN" if status_output == "UNKNOWN" else ("true" if status_output == "" else "false")
    describe = _git("describe", "--tags", "--always", "--dirty")
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    python_ver = sys.version.replace("\n", " ")
    cmd = " ".join(["python -m pytest tests/research_validity/", "-v"] + list(extra_args))
    lines = [
        "=== PROVENANCE HEADER ===",
        f"git_commit_sha: {sha}",
        f"git_working_tree_clean: {clean_status}",
        f"git_describe: {describe}",
        f"execution_timestamp_utc: {timestamp}",
        f"python_version: {python_ver}",
        f"command: {cmd}",
        "=== END PROVENANCE HEADER ===",
        "",
    ]
    return "\n".join(lines)


def main():
    extra_args = sys.argv[1:]
    provenance = build_provenance_header(extra_args)
    print(provenance)
    pytest_cmd = [sys.executable, "-m", "pytest", "tests/research_validity/", "-v", "--tb=short"] + list(extra_args)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as log_fh:
        log_fh.write(provenance + "\n")
        log_fh.flush()
        proc = subprocess.run(pytest_cmd, cwd=str(PROJECT_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log_fh.write(proc.stdout)
        print(proc.stdout, end="")
    print(f"\n[runner] Log written to: {LOG_PATH.relative_to(PROJECT_ROOT)}")
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
