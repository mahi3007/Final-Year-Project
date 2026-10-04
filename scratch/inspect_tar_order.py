import os
import sys
import tarfile
import urllib.request
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE
from pathlib import Path

plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
url = plan.download_url

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

print("Opening stream...")
resp = urllib.request.urlopen(req)
tf = tarfile.open(fileobj=resp, mode="r|gz")

print("Iterating first 30 members:")
for i, member in enumerate(tf):
    print(f"[{i:3d}] {member.name} (size: {member.size} bytes)")
    if i >= 30:
        break
tf.close()
resp.close()
