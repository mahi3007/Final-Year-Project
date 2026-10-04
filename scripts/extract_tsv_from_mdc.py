#!/usr/bin/env python3
"""
Stream-extract validated.tsv from Mozilla Data Collective Common Voice 27.0
without downloading the full 88 GB archive.
"""
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TARGET_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_11"
TARGET_FILE = TARGET_DIR / "validated.tsv"

DATASET_ID = "cmu5jplf300nwmh07iqvk9leo"  # Common Voice Scripted Speech 27.0 - English

def extract_tsv(api_key: str | None = None) -> bool:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if api_key:
        os.environ["MDC_API_KEY"] = api_key
    elif not os.environ.get("MDC_API_KEY"):
        print("ERROR: MDC_API_KEY is not set.")
        print("Please generate an API key at https://mozilladatacollective.com/profile/api")
        print("Then run: $env:MDC_API_KEY='<key>'; python scripts/extract_tsv_from_mdc.py")
        return False

    import datacollective
    from datacollective import get_dataset_details
    from datacollective.download import _get_download_plan

    print(f"Fetching download session for dataset: {DATASET_ID}...")
    details = get_dataset_details(DATASET_ID)
    temp_target = TARGET_DIR / "temp_archive.tar.gz"
    
    plan = _get_download_plan(dataset_id=details.id, target_filepath=temp_target)
    download_url = plan.download_url
    sys.stdout.reconfigure(line_buffering=True)
    print(f"Obtained secure download URL from MDC. Connecting to stream...", flush=True)

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"datacollective-python/{datacollective.__version__}"}
    )

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print("Streaming archive to locate validated.tsv (this avoids downloading 88 GB)...", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            with tarfile.open(fileobj=response, mode="r|gz") as tar:
                count = 0
                for member in tar:
                    count += 1
                    filename = Path(member.name).name
                    if count <= 20 or member.name.endswith(".tsv"):
                        print(f"  [archive index {count}] {member.name} ({member.size / (1024*1024):.2f} MB)", flush=True)
                    
                    if filename == "validated.tsv" and member.isfile():
                        print(f"\nTarget found: {member.name} ({member.size / (1024*1024):.2f} MB)! Extracting...", flush=True)
                        extracted_f = tar.extractfile(member)
                        if extracted_f:
                            with open(TARGET_FILE, "wb") as out_f:
                                chunk_size = 1024 * 1024
                                total = 0
                                while chunk := extracted_f.read(chunk_size):
                                    out_f.write(chunk)
                                    total += len(chunk)
                                    print(f"  Extracted {total / (1024*1024):.1f} MB...", end="\r", flush=True)
                            print(f"\nSuccessfully extracted validated.tsv ({total / (1024*1024):.2f} MB) to:\n  {TARGET_FILE}", flush=True)
                            return True
                    
                    if count > 200 and "clips/" in member.name:
                        print(f"Reached clips directory after {count} files. Stopping scan.", flush=True)
                        break
    except Exception as e:
        print(f"\nStream extraction encountered an error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

    print("Could not locate validated.tsv in the archive stream.", flush=True)
    return False

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else None
    success = extract_tsv(key)
    sys.exit(0 if success else 1)
