import io
import sys
import tarfile
import urllib.request
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
req = urllib.request.Request(plan.download_url, headers={"User-Agent": "datacollective-python/0.1.0"})

print("Connecting to stream...", flush=True)
with urllib.request.urlopen(req, timeout=120) as resp:
    buffered = io.BufferedReader(resp, buffer_size=16 * 1024 * 1024)
    with tarfile.open(fileobj=buffered, mode="r|gz") as tar:
        member_count = 0
        clip_count = 0
        t0 = None
        for m in tar:
            member_count += 1
            if member_count <= 12:
                continue
            if t0 is None:
                t0 = time.time()
                print("Starting clip scan benchmark...", flush=True)
            clip_count += 1
            if clip_count % 1000 == 0:
                elapsed = time.time() - t0
                print(f"Scanned {clip_count} clips in {elapsed:.2f}s ({clip_count/elapsed:.1f} clips/s, {Path(m.name).name})", flush=True)
            if clip_count >= 5000:
                break
