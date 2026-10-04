import io
import time
import urllib.request
import urllib.error
import zlib
import tarfile
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

def get_plan_with_retry(dataset_id: str, max_retries: int = 5):
    for attempt in range(1, max_retries + 1):
        try:
            return _get_download_plan(dataset_id, Path("temp.tar.gz"), DOWNLOAD_SOURCE_SAVE)
        except Exception as e:
            print(f"[WARN] _get_download_plan attempt {attempt} failed: {e}. Retrying in {attempt * 2}s...", flush=True)
            time.sleep(attempt * 2)
    raise RuntimeError(f"Failed to fetch download plan after {max_retries} attempts.")

class ResilientGzipStream(io.RawIOBase):
    def __init__(self, dataset_id: str):
        super().__init__()
        self.dataset_id = dataset_id
        self.compressed_bytes_read = 0
        self.decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self.resp = None
        self.download_url = None
        self.url_timestamp = 0
        self.uncompressed_buffer = bytearray()
        self._refresh_url()
        self._open_connection()

    def _refresh_url(self):
        plan = get_plan_with_retry(self.dataset_id)
        self.download_url = plan.download_url
        self.url_timestamp = time.time()

    def _open_connection(self):
        if self.resp is not None:
            try:
                self.resp.close()
            except Exception:
                pass
            self.resp = None

        # Re-fetch URL if older than 10 hours
        if time.time() - self.url_timestamp > 36000:
            self._refresh_url()

        for attempt in range(1, 20):
            try:
                headers = {"User-Agent": "datacollective-python/0.1.0"}
                if self.compressed_bytes_read > 0:
                    headers["Range"] = f"bytes={self.compressed_bytes_read}-"
                    print(f"\n[AUTO-RESUME] Reconnecting at compressed byte offset {self.compressed_bytes_read:,} (attempt {attempt})...", flush=True)
                else:
                    print("\n[AUTO-RESUME] Opening initial connection from byte 0...", flush=True)

                req = urllib.request.Request(self.download_url, headers=headers)
                self.resp = urllib.request.urlopen(req, timeout=120)
                return
            except urllib.error.HTTPError as he:
                if he.code == 403:
                    print("[AUTO-RESUME] Presigned URL expired (403). Refreshing plan...", flush=True)
                    self._refresh_url()
                print(f"[AUTO-RESUME] HTTP error {he.code}: {he.reason}. Retrying in 5s...", flush=True)
                time.sleep(5)
            except Exception as e:
                print(f"[AUTO-RESUME] Connection error: {e}. Retrying in 5s...", flush=True)
                time.sleep(5)
        raise RuntimeError("Failed to connect after 20 attempts.")

    def readable(self):
        return True

    def seekable(self):
        return False

    def writable(self):
        return False

    def readinto(self, b):
        while len(self.uncompressed_buffer) == 0:
            try:
                chunk = self.resp.read(524288) # 512 KB
                if not chunk:
                    flushed = self.decompressor.flush()
                    if flushed:
                        self.uncompressed_buffer.extend(flushed)
                        break
                    print(f"\n[AUTO-RESUME] Socket returned EOF at compressed byte {self.compressed_bytes_read:,}. Reconnecting...", flush=True)
                    time.sleep(2)
                    self._open_connection()
                    continue
                
                self.compressed_bytes_read += len(chunk)
                decomp = self.decompressor.decompress(chunk)
                if decomp:
                    self.uncompressed_buffer.extend(decomp)
            except Exception as e:
                print(f"\n[AUTO-RESUME] Socket exception ({e}) at byte {self.compressed_bytes_read:,}. Reconnecting...", flush=True)
                time.sleep(3)
                self._open_connection()

        n = min(len(b), len(self.uncompressed_buffer))
        b[:n] = self.uncompressed_buffer[:n]
        del self.uncompressed_buffer[:n]
        return n

if __name__ == "__main__":
    print("Testing resilient stream unit...", flush=True)
    stream = ResilientGzipStream("cmu5jplf300nwmh07iqvk9leo")
    buffered = io.BufferedReader(stream, buffer_size=4 * 1024 * 1024)

    print("Opening tarfile in 'r|' mode...", flush=True)
    with tarfile.open(fileobj=buffered, mode="r|") as tar:
        for i in range(3):
            m = tar.next()
            if m is None:
                break
            print(f"  Tar member #{i+1}: {m.name} ({m.size:,} bytes)", flush=True)

    print("SUCCESS: ResilientGzipStream successfully read tar headers!", flush=True)
