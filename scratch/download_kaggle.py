import subprocess
import os
import sys

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUTF8"] = "1"

kaggle_exe = r"C:\Users\venka\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\kaggle.exe"

out_dir = r"scratch\kaggle_run_output_full"
os.makedirs(out_dir, exist_ok=True)

cmd = [kaggle_exe, "kernels", "output", "venkataakhil07/notebook840244cb83", "-p", out_dir]
print("Running:", " ".join(cmd))
res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("Returncode:", res.returncode)
print("STDOUT tail:")
print("\n".join(res.stdout.splitlines()[-30:]))
if res.stderr:
    print("STDERR:")
    print(res.stderr[:1000])
