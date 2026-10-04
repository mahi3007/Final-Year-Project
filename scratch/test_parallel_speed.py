import concurrent.futures
import time
import urllib.request
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
url = plan.download_url

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB per worker
NUM_WORKERS = 8

def fetch_chunk(i):
    start = i * CHUNK_SIZE
    end = start + CHUNK_SIZE - 1
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "datacollective-python/0.1.0",
            "Range": f"bytes={start}-{end}"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return len(data)

print(f"Starting {NUM_WORKERS} parallel connections ({NUM_WORKERS * 10} MB total)...", flush=True)
t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = [executor.submit(fetch_chunk, i) for i in range(NUM_WORKERS)]
    total_bytes = sum(f.result() for f in futures)

elapsed = time.time() - t0
mb = total_bytes / (1024 * 1024)
print(f"Downloaded {mb:.2f} MB in {elapsed:.2f}s ({mb/elapsed:.2f} MB/s total throughput across {NUM_WORKERS} workers)!")
