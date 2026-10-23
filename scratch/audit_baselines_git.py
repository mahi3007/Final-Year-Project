import subprocess
import hashlib
import os

files = [
    "reports/stage5/external_speaker_inventory.csv",
    "datasets/splits/stage5_external_eval.csv",
    "datasets/splits/stage5_sentinel_panel.csv",
    "datasets/splits/stage5_sentinel_panel_manifest.json",
    "reports/stage6m/power_simulation_results.json",
    "datasets/splits/stage4_characterization.csv",
    "datasets/splits/calibration.csv"
]

print("==================== AUDIT 3: FROZEN BASELINE & GIT INTEGRITY ====================")

for f in files:
    print(f"\n--- Checking: {f} ---")
    if not os.path.exists(f):
        print("  DISK: FILE NOT FOUND")
        continue
    
    # 1. Disk content
    with open(f, "rb") as fp:
        disk_bytes = fp.read()
    disk_size = len(disk_bytes)
    disk_sha = hashlib.sha256(disk_bytes).hexdigest()
    print(f"  DISK Size: {disk_size} bytes")
    print(f"  DISK SHA-256: {disk_sha}")

    # 2. Git HEAD / Baseline commit content
    git_cmd = ["git", "show", f"HEAD:{f}"]
    res = subprocess.run(git_cmd, capture_output=True)
    if res.returncode == 0:
        git_bytes = res.stdout
        git_size = len(git_bytes)
        git_sha = hashlib.sha256(git_bytes).hexdigest()
        print(f"  GIT HEAD Size: {git_size} bytes")
        print(f"  GIT HEAD SHA-256: {git_sha}")
        print(f"  Current disk matches GIT HEAD: {disk_bytes == git_bytes}")
    else:
        print(f"  GIT HEAD: Not committed in Git (untracked / newly generated artifact)")

    # 3. Git log history
    log_cmd = ["git", "log", "--follow", "--oneline", "--", f]
    log_res = subprocess.run(log_cmd, capture_output=True, text=True)
    commits = log_res.stdout.strip().splitlines()
    print(f"  Git Commit Count: {len(commits)}")
    if commits:
        for c in commits[:3]:
            print(f"    Commit: {c}")
