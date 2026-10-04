import io
import time
import urllib.request
import zlib
import tarfile
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

class ResilientGzipStream(io.RawIOBase):
    """
    A readable stream that pulls gzip-compressed bytes from an HTTP Range source,
    transparently reconnecting with 'Range: bytes={compressed_offset}-' whenever
    the socket drops or times out, and yields uncompressed bytes via zlib.decompressobj.
    """
    def __init__(self, dataset_id: str, buffer_size: int = 16 * 1024 * 1024):
        self.dataset_id = dataset_id
        self.buffer_size = buffer_size
        self.compressed_bytes_read = 0
        self.decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self.resp = None
        self.uncompressed_buffer = bytearray()
        self._open_connection()

    def _open_connection(self):
        plan = _get_download_plan(self.dataset_id, Path("temp.tar.gz"), DOWNLOAD_SOURCE_SAVE)
        headers = {"User-Agent": "datacollective-python/0.1.0"}
        if self.compressed_bytes_read > 0:
            headers["Range"] = f"bytes={self.compressed_bytes_read}-"
            print(f"\n[AUTO-RESUME] Reconnecting at compressed byte offset {self.compressed_bytes_read:,}...", flush=True)
        else:
            print("\n[AUTO-RESUME] Opening initial connection from byte 0...", flush=True)

        req = urllib.request.Request(plan.download_url, headers=headers)
        self.resp = urllib.request.urlopen(req, timeout=120)

    def readable(self):
        return True

    def readinto(self, b):
        # Fill buffer if empty
        while len(self.uncompressed_buffer) == 0:
            try:
                chunk = self.resp.read(65536)
                if not chunk:
                    # Connection closed or EOF
                    # If decompressor still has unconsumed tail, flush it
                    flushed = self.decompressor.flush()
                    if flushed:
                        self.uncompressed_buffer.extend(flushed)
                        break
                    # If server returned empty chunk unexpectedly before archive end, reconnect:
                    print(f"\n[AUTO-RESUME] Socket closed at compressed byte {self.compressed_bytes_read:,}. Reconnecting...", flush=True)
                    time.sleep(2)
                    self._open_connection()
                    continue
                
                self.compressed_bytes_read += len(chunk)
                decomp = self.decompressor.decompress(chunk)
                if decomp:
                    self.uncompressed_buffer.extend(decomp)
            except Exception as e:
                print(f"\n[AUTO-RESUME] Socket exception ({e}) at byte {self.compressed_bytes_read:,}. Reconnecting in 5s...", flush=True)
                time.sleep(5)
                self._open_connection()

        n = min(len(b), len(self.uncompressed_buffer))
        b[:n] = self.uncompressed_buffer[:n]
        del self.uncompressed_buffer[:n]
        return n

print("Testing ResilientGzipStream with tarfile...")
stream = ResilientGzipStream("cmu5jplf300nwmh07iqvk9leo")
buffered = io.BufferedReader(stream, buffer_size=4 * 1024 * 1024)

# Open tar in stream mode (r|) on uncompressed stream
with tarfile.open(fileobj=buffered, mode="r|") as tar:
    count = 0
    for m in tar:
        count += 1
        if count <= 15:
            print(f"  [{count}] {m.name} ({m.size} B)")
        elif count == 16:
            print(f"  [{count}] {m.name} ({m.size} B) -- clips started!")
            break

print("SUCCESS: Resilient stream successfully parsed tar stream!")
