import subprocess
import sys
import os
import hashlib
import time

log_path = r"reports\stage6m\test_execution_research_validity_v1_2_0.log"

print("Starting full research validity test suite run...")
start_time = time.time()

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/research_validity/", "-v"],
    capture_output=True,
    text=True
)

elapsed = time.time() - start_time
print(f"Pytest finished in {elapsed:.2f} seconds with exit code {result.returncode}")

with open(log_path, "w", encoding="utf-8") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)

log_bytes = open(log_path, "rb").read()
log_hash = hashlib.sha256(log_bytes).hexdigest()

print(f"Log written to {log_path}")
print(f"Log Size: {len(log_bytes)} bytes")
print(f"Log SHA-256: {log_hash}")

# Print summary lines from stdout
summary_lines = [l for l in result.stdout.splitlines() if "passed" in l or "failed" in l or "collected" in l]
for l in summary_lines[-10:]:
    print("Summary:", l)
