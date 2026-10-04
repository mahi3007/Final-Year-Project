import os
import sys
import tarfile
import urllib.request
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

# Unbuffer stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

print("Fetching download plan...", flush=True)
plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
url = plan.download_url

req = urllib.request.Request(
    url,
    headers={"User-Agent": "datacollective-python/0.1.0"}
)

import io
print("Connecting to stream...", flush=True)
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    print(f"Connected in {time.time()-t0:.2f}s. Parsing tar stream...", flush=True)
    buffered_resp = io.BufferedReader(resp, buffer_size=16 * 1024 * 1024)
    with tarfile.open(fileobj=buffered_resp, mode="r|gz") as tar:
        member_count = 0
        clip_count = 0
        for m in tar:
            member_count += 1
            if member_count <= 15:
                print(f"  [{member_count}] {m.name} ({m.size} bytes)", flush=True)
            elif "clips/" in m.name and m.isfile():
                clip_count += 1
                if clip_count <= 20:
                    print(f"  [Clip {clip_count} / total member {member_count}] {Path(m.name).name} ({m.size} bytes)", flush=True)
                if clip_count >= 20:
                    print("Reached 20 clips! Exiting inspect.", flush=True)
                    break
            elif member_count % 5 == 0 and clip_count == 0:
                print(f"  [{member_count}] {m.name} ({m.size} bytes)", flush=True)
