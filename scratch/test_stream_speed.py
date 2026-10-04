import os
import sys
import time
import urllib.request
from dotenv import load_dotenv

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE
from pathlib import Path

plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
url = plan.download_url

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
t0 = time.time()
bytes_read = 0
chunk_size = 1024 * 1024  # 1 MB

with urllib.request.urlopen(req) as resp:
    for _ in range(50):  # read 50 MB
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        bytes_read += len(chunk)

elapsed = time.time() - t0
speed_mb_s = (bytes_read / (1024*1024)) / elapsed
print(f"Read {bytes_read / (1024*1024):.1f} MB in {elapsed:.2f}s ({speed_mb_s:.2f} MB/s)")
