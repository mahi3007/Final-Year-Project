import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE
from pathlib import Path
import urllib.parse

DATASET_ID = "cmu5jplf300nwmh07iqvk9leo"
plan = _get_download_plan(DATASET_ID, Path("test.tar.gz"), DOWNLOAD_SOURCE_SAVE)
u = plan.download_url
parsed = urllib.parse.urlparse(u)
print("URL Scheme:", parsed.scheme)
print("URL Host:", parsed.netloc)
print("URL Path:", parsed.path)
print("Query params:", list(urllib.parse.parse_qs(parsed.query).keys()))
