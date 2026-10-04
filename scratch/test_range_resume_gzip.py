import urllib.request
import zlib
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

plan = _get_download_plan("cmu5jplf300nwmh07iqvk9leo", Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
url = plan.download_url

# Part 1: Download bytes 0 to 5,000,000 (5 MB)
print("Downloading part 1 (bytes 0 - 4,999,999)...")
req1 = urllib.request.Request(
    url,
    headers={
        "User-Agent": "datacollective-python/0.1.0",
        "Range": "bytes=0-4999999"
    }
)
with urllib.request.urlopen(req1) as resp:
    data1 = resp.read()

# Part 2: Download bytes 5,000,000 to 10,000,000 (5 MB)
print("Downloading part 2 (bytes 5,000,000 - 9,999,999)...")
req2 = urllib.request.Request(
    url,
    headers={
        "User-Agent": "datacollective-python/0.1.0",
        "Range": "bytes=5000000-9999999"
    }
)
with urllib.request.urlopen(req2) as resp:
    data2 = resp.read()

print(f"Downloaded part 1: {len(data1)} bytes, part 2: {len(data2)} bytes")

# Decompress using zlib.decompressobj(16 + zlib.MAX_WBITS) for gzip
decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
decomp1 = decompressor.decompress(data1)
print(f"Decompressed from part 1: {len(decomp1)} bytes uncompressed")

decomp2 = decompressor.decompress(data2)
print(f"Decompressed from part 2: {len(decomp2)} bytes uncompressed")
print("SUCCESS: zlib seamlessly crossed the HTTP Range boundary!")
