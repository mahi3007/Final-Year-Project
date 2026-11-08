import subprocess

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"ERROR: {e}"

print("=== Commit Info for 5062e50 ===")
print(run('git log -1 --format="Commit: %H%nDate: %ai%nSubject: %s" 5062e50'))

print("\n=== File Blob Info ===")
print(run('git ls-tree 5062e50 datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json'))

print("\n=== Branches containing commit 5062e50 ===")
print(run('git branch -a --contains 5062e50'))

print("\n=== Tags containing commit 5062e50 ===")
res_tags = run('git tag --contains 5062e50')
print(res_tags if res_tags else "None")

print("\n=== Commits in Git History Touching this File ===")
print(run('git log --format="%h %ai %s" -- datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json'))

print("\n=== Is file present in release archive? ===")
print(run('tar -ztvf releases/stage6m_gate5_release_v1.0.tar.gz | grep sealed || echo "NOT in release tarball"'))

