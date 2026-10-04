import time
import io
import zlib
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

DATASET_ID = "cmu5jplf300nwmh07iqvk9leo"

def main():
    print("Getting presigned URL from MDC...", flush=True)
    plan = _get_download_plan(DATASET_ID, Path("temp.tar.gz"), DOWNLOAD_SOURCE_SAVE)
    url = plan.download_url
    print(f"Obtained presigned URL. Connecting with Range 0-50MB...", flush=True)

    t0 = time.time()
    req = urllib.request.Request(url, headers={"Range": "bytes=0-52428800"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    elapsed = time.time() - t0
    mb = len(data) / (1024 * 1024)
    speed = mb / elapsed if elapsed > 0 else 0
    print(f"Downloaded {mb:.2f} MB in {elapsed:.2f}s ({speed:.2f} MB/s)", flush=True)

if __name__ == "__main__":
    main()
