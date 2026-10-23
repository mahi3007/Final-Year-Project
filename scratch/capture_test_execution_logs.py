import datetime
import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
S6_DIR = PROJECT_ROOT / "reports" / "stage6m"

def run_and_log(cmd, log_path, title):
    print(f"Executing: {' '.join(cmd)}")
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    log_content = (
        f"================================================================================\n"
        f"TEST EXECUTION AUDIT RECORD: {title}\n"
        f"Command: {' '.join(cmd)}\n"
        f"Working Directory: {PROJECT_ROOT}\n"
        f"Start Timestamp (UTC): {start_time}\n"
        f"End Timestamp (UTC):   {end_time}\n"
        f"Exit Code: {result.returncode}\n"
        f"Execution Status: {'SUCCESS' if result.returncode == 0 else 'FAILURE'}\n"
        f"================================================================================\n\n"
        f"--- STDOUT ---\n{result.stdout}\n\n"
        f"--- STDERR ---\n{result.stderr}\n\n"
        f"================================================================================\n"
        f"END OF AUDIT RECORD\n"
        f"================================================================================\n"
    )
    
    log_path.write_text(log_content, encoding="utf-8")
    
    # Compute SHA-256
    sha256 = hashlib.sha256(log_content.encode("utf-8")).hexdigest()
    print(f"Saved {log_path} ({len(log_content)} bytes, exit {result.returncode})")
    print(f"SHA-256: {sha256}")
    return sha256, len(log_content), result.returncode

if __name__ == "__main__":
    # 1. Full research-validity directory
    h1, sz1, c1 = run_and_log(
        [sys.executable, "-m", "pytest", "tests/research_validity/", "-v"],
        S6_DIR / "test_execution_research_validity_full.log",
        "Full Research Validity Test Suite (tests/research_validity/)"
    )
    
    # 2. Stage 6M specific module
    h2, sz2, c2 = run_and_log(
        [sys.executable, "-m", "pytest", "tests/research_validity/test_stage6m_protocol_proposal.py", "-v"],
        S6_DIR / "test_execution_stage6m_proposal.log",
        "Stage 6M Protocol Proposal Test Module (test_stage6m_protocol_proposal.py)"
    )
    
    print("\nSummary:")
    print(f"Full Suite: exit={c1}, sha256={h1}")
    print(f"Stage 6M:   exit={c2}, sha256={h2}")
