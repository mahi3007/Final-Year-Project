#!/usr/bin/env python3
"""
scripts/materialize_stage6m_cohort3_audio.py

Stage 6M v1.5 Milestone 7.4 — Controlled Cohort 3 Audio Materialization & Integrity Validation
=============================================================================================
Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)
Protocol: v1.5-five-stratum-parity
Governance Status: AUTHORIZED FOR DATA PREPARATION (GPU Adaptation Separately Gated)

Materialization Pipeline Architecture:
--------------------------------------
1. Approved Provisional Manifest Sourcing:
   - Reads strictly from datasets/splits/stage6m_cohort3_provisional_manifest.json / .csv.
   - Target Population: 1,265 unique speakers (1,100 eval + 100 gate + 65 Australian reserve).
   - Target Scale: Exactly 18,975 clips (15 clips/speaker), zero substitution.
   - Target Output Directory: datasets/external/common_voice_27/cohort3_audio/{recording_id}.mp3

2. Dual Extraction Modes:
   - Local Source Mode (--source-dir <path>):
     Copies and validates recordings from a local directory containing Common Voice MP3s.
   - Streaming Mode (--stream, default if MDC_API_KEY present and no source-dir):
     High-throughput resilient gzip stream over HTTP Range requests from Mozilla
     Data Collective (MDC ID: cmu5jplf300nwmh07iqvk9leo) with threaded prefetch.
   - Validate-Only / Dry-Run Mode (--validate-only):
     Scans and audits already-materialized local audio files against the provisional manifest.

3. Strict Quality & Physical Integrity Invariants:
   - Non-zero file size, valid MP3 bitstream.
   - Audio decoding via soundfile (valid sample rate > 0, duration > 0.0 s, channels >= 1).
   - Bitwise SHA-256 cryptographic digest computed for every clip.
   - Transcript association and speaker assignment integrity check.
   - Resumable: automatically verifies and skips already-materialized valid clips.
   - Zero substitution: never replaces a missing or failed clip with an unapproved candidate.

4. Auditable Output Deliverables:
   - reports/stage6m/stage6m_cohort3_audio_materialization.json
   - reports/stage6m/stage6m_cohort3_audio_materialization.md
   - datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv
   - datasets/splits/stage6m_cohort3_failed_clips_report.json
   - datasets/splits/stage6m_cohort3_speaker_completeness_report.json
   - Manifest remains explicitly UNLOCKED / PROVISIONAL.
   - Confirmatory GPU adaptation and model inference remain STRICTLY BLOCKED.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import queue
import shutil
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
import zlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import soundfile as sf
from dotenv import load_dotenv

# Unbuffered stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cohort3_materialize")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
PROVISIONAL_MANIFEST_JSON = SPLITS_DIR / "stage6m_cohort3_provisional_manifest.json"
PROVISIONAL_MANIFEST_CSV = SPLITS_DIR / "stage6m_cohort3_provisional_manifest.csv"

CV27_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27"
COHORT3_AUDIO_DIR = CV27_DIR / "cohort3_audio"

REPORTS_DIR = PROJECT_ROOT / "reports" / "stage6m"
MATERIALIZATION_JSON = REPORTS_DIR / "stage6m_cohort3_audio_materialization.json"
MATERIALIZATION_MD = REPORTS_DIR / "stage6m_cohort3_audio_materialization.md"

LEDGER_CSV = SPLITS_DIR / "stage6m_cohort3_clip_sha256_ledger.csv"
FAILED_REPORT_JSON = SPLITS_DIR / "stage6m_cohort3_failed_clips_report.json"
SPEAKER_REPORT_JSON = SPLITS_DIR / "stage6m_cohort3_speaker_completeness_report.json"

DATASET_ID = "cmu5jplf300nwmh07iqvk9leo"  # Mozilla Common Voice 27.0 - English
TOTAL_EXPECTED_CLIPS = 18975
TOTAL_EXPECTED_SPEAKERS = 1265
CLIPS_PER_SPEAKER = 15

# Pilot Materialization Constants & Paths (Task 7.4.2)
PILOT_EXPECTED_SPEAKERS = 5
PILOT_EXPECTED_CLIPS_PER_SPEAKER = 15
PILOT_TOTAL_EXPECTED_CLIPS = 75
PILOT_CONFIRMATORY_STRATA = [
    "Australian English",
    "Canadian English",
    "England English",
    "South Asian English",
    "US English",
]
COHORT3_PILOT_AUDIO_DIR = CV27_DIR / "cohort3_pilot_audio"
PILOT_MATERIALIZATION_JSON = REPORTS_DIR / "stage6m_cohort3_pilot_materialization.json"
PILOT_MATERIALIZATION_MD = REPORTS_DIR / "stage6m_cohort3_pilot_materialization.md"
PILOT_LEDGER_CSV = SPLITS_DIR / "stage6m_cohort3_pilot_clip_sha256_ledger.csv"
PILOT_FAILED_REPORT_JSON = SPLITS_DIR / "stage6m_cohort3_pilot_failed_clips_report.json"
PILOT_SPEAKER_REPORT_JSON = SPLITS_DIR / "stage6m_cohort3_pilot_speaker_completeness_report.json"

HARDENING_AUDIT_JSON = REPORTS_DIR / "stage6m_cohort3_materializer_hardening_audit.json"
HARDENING_AUDIT_MD = REPORTS_DIR / "stage6m_cohort3_materializer_hardening_audit.md"


def verify_pilot_materialization_authorization(audit_json_path: Path = HARDENING_AUDIT_JSON) -> None:
    """
    Verifies that physical pilot audio acquisition is authorized under Protocol Section 14.7.
    Fails closed if the governance audit artifact is missing or if the decision is not
    'AUTHORIZED_BY_PROJECT_LEAD'.
    """
    if not audit_json_path.exists():
        raise PermissionError(
            f"Physical pilot audio acquisition blocked: governance audit artifact not found at {audit_json_path}. "
            "Explicit Project-Lead authorization under Protocol Section 14.7 is required before downloading."
        )
    try:
        with open(audit_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise PermissionError(
            f"Physical pilot audio acquisition blocked: could not parse governance audit artifact {audit_json_path}: {e}"
        )

    gating = data.get("execution_gating", {})
    pilot_auth = gating.get("controlled_pilot_download")
    if pilot_auth not in ("AUTHORIZED_BY_PROJECT_LEAD", "PILOT_COMPLETE_AND_VERIFIED"):
        raise PermissionError(
            f"Physical pilot audio acquisition blocked: controlled_pilot_download is '{pilot_auth}' "
            f"(expected 'AUTHORIZED_BY_PROJECT_LEAD' or 'PILOT_COMPLETE_AND_VERIFIED' in {audit_json_path}). "
            "Controlled physical retrieval requires explicit Project-Lead authorization under Protocol Section 14.7."
        )


def verify_full_cohort_materialization_authorization(audit_json_path: Path = HARDENING_AUDIT_JSON) -> None:
    """
    Verifies that full cohort audio materialization is authorized under Protocol Section 14.7.
    Fails closed if the governance audit artifact is missing or if full_audio_materialization
    is not 'AUTHORIZED_BY_PROJECT_LEAD'.
    """
    if not audit_json_path.exists():
        raise PermissionError(
            f"Full cohort audio acquisition blocked: governance audit artifact not found at {audit_json_path}."
        )
    try:
        with open(audit_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise PermissionError(
            f"Full cohort audio acquisition blocked: could not parse governance audit artifact {audit_json_path}: {e}"
        )

    gating = data.get("execution_gating", {})
    full_auth = gating.get("full_audio_materialization")
    if full_auth != "AUTHORIZED_BY_PROJECT_LEAD":
        raise PermissionError(
            f"Full cohort audio acquisition blocked: full_audio_materialization is '{full_auth}'. "
            "Full 18,975-clip acquisition remains BLOCKED pending physical pilot validation and Project-Lead authorization."
        )


def compute_sha256(path: Path) -> str:
    """Compute lowercase SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel_path(p: Path, base: Path = PROJECT_ROOT) -> str:
    """Safely return path relative to base or POSIX string if outside base."""
    try:
        return str(p.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(p.as_posix())


def validate_audio_file(
    path: Path,
    expected_format: str = "MP3",
    allowed_sample_rates: Optional[Set[int]] = None,
) -> Tuple[bool, float, int, int, str, str]:
    """
    Validates physical audio file decodability and container integrity using soundfile.

    Audio Ingest & Downstream Resampling Contract:
    ----------------------------------------------
    1. Container & Codec: Strictly validates genuine MP3 bitstreams (info.format.upper() == 'MP3').
       Non-MP3 formats (e.g., WAV or OGG containers masquerading under a .mp3 filename)
       are strictly rejected as format mismatches.
    2. Decodability & Content: Verifies that audio frames can be successfully decoded and
       are non-empty. Truncated or bitstream-corrupted MP3 files are rejected.
    3. Sample Rate Policy: Mozilla Common Voice 27.0 recordings natively feature varied sample
       rates (typically 32,000 Hz, 44,100 Hz, or 48,000 Hz). The materialization validator
       verifies that the sample rate is positive and belongs to standard audio rates
       (default: {16000, 22050, 24000, 32000, 44100, 48000}).
       Downstream CTTA adaptation and inference models require 16,000 Hz mono audio, which is
       performed deterministically on-the-fly by src/dsg_ctta/data/acoustic.py::load_and_resample_audio
       (converting multi-channel to mono via channel averaging and resample to 16 kHz).
    4. Channels: Validates mono (1) or stereo (2) audio channels.
    5. Cryptographic Provenance: Computes SHA-256 digest of the raw on-disk audio bytes.

    Returns: (is_valid, duration_sec, sample_rate, channels, sha256_hash, error_msg)
    """
    if allowed_sample_rates is None:
        allowed_sample_rates = {16000, 22050, 24000, 32000, 44100, 48000}

    if not path.exists():
        return False, 0.0, 0, 0, "", "File does not exist"
    if path.stat().st_size == 0:
        return False, 0.0, 0, 0, "", "File is 0 bytes (empty)"
    try:
        info = sf.info(str(path))
        detected_fmt = (info.format or "").upper()
        if detected_fmt != expected_format.upper():
            return False, 0.0, 0, 0, "", f"Invalid audio format: expected {expected_format.upper()} container, got {detected_fmt}"
        if info.duration <= 0.0:
            return False, 0.0, 0, 0, "", f"Invalid non-positive duration: {info.duration}"
        if info.samplerate <= 0:
            return False, 0.0, 0, 0, "", f"Invalid non-positive sample rate: {info.samplerate}"
        if info.samplerate not in allowed_sample_rates:
            return False, 0.0, 0, 0, "", f"Unsupported sample rate: {info.samplerate} Hz (allowed: {sorted(allowed_sample_rates)})"
        if info.channels not in (1, 2):
            return False, 0.0, 0, 0, "", f"Invalid channel count: {info.channels} (expected 1 or 2)"

        # Full-file stream decoding check: decode entire file in bounded-memory chunks (4,096 frames/chunk)
        total_decoded_frames = 0
        with sf.SoundFile(str(path), "r") as reader:
            declared_frames = reader.frames
            while True:
                chunk = reader.read(4096)
                if len(chunk) == 0:
                    break
                total_decoded_frames += len(chunk)

        if total_decoded_frames == 0:
            return False, 0.0, 0, 0, "", "Audio file contains zero decoded frames"

        # MPEG Audio Layer III Frame Boundary Invariant:
        # Standard MP3 bitstreams (e.g., LAME encoding in Mozilla Common Voice) include
        # encoder delay (typically 528 samples) and container padding to round out the final
        # 1,152-sample MPEG frame. libsndfile's mpg123 backend strips encoder padding upon decoding,
        # causing total_decoded_frames to be slightly below declared_frames by at most one
        # MPEG audio frame (1,152 samples, or ~24ms at 48 kHz).
        # Any shortfall exceeding 1,152 samples (declared_frames - total_decoded_frames > 1152)
        # indicates true bitstream truncation or premature stream termination, failing closed.
        MAX_MP3_PADDING_FRAMES = 1152
        if declared_frames > 0 and (declared_frames - total_decoded_frames) > MAX_MP3_PADDING_FRAMES:
            return (
                False,
                0.0,
                0,
                0,
                "",
                f"Truncated audio stream: decoded {total_decoded_frames} frames but header declares {declared_frames} "
                f"(shortfall of {declared_frames - total_decoded_frames} frames exceeds MPEG frame padding tolerance of {MAX_MP3_PADDING_FRAMES})",
            )

        h = compute_sha256(path)
        return True, float(info.duration), int(info.samplerate), int(info.channels), h, ""
    except Exception as exc:
        return False, 0.0, 0, 0, "", f"Decode failure: {str(exc)}"



class ThreadedResilientGzipStream(io.RawIOBase):
    """
    High-throughput resilient gzip stream over HTTP.
    Uses a background producer thread with 2MB chunk prefetching to saturate
    the network pipe while decompressing synchronously into tarfile.
    Auto-reconnects at exact byte offset when Cloudflare drops TCP session,
    strictly validating HTTP 206 Partial Content status and Content-Range alignment.
    """

    def __init__(
        self,
        dataset_id: str,
        plan_getter: Any,
        queue_size: int = 32,
        url_opener: Optional[Any] = None,
    ):
        super().__init__()
        self._dataset_id = dataset_id
        self._plan_getter = plan_getter
        self._url_opener = url_opener or urllib.request.urlopen
        self.compressed_bytes_read = 0
        self._producer_bytes_read = 0
        self._expected_total_bytes: Optional[int] = None
        self._decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self._url = None
        self._url_ts = 0.0
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._stop_event = threading.Event()
        self._producer_thread: Optional[threading.Thread] = None
        self._producer_error: Optional[Exception] = None
        self._uc_buf = bytearray()
        self._offset = 0

        self._refresh_url()
        self._start_producer()

    def _refresh_url(self):
        for attempt in range(1, 10):
            try:
                plan = self._plan_getter()
                self._url = plan.download_url
                self._url_ts = time.time()
                logger.info(f"[MDC] Fresh presigned URL obtained (attempt {attempt}).")
                return
            except Exception as e:
                wait = attempt * 3
                logger.warning(f"[MDC] plan attempt {attempt} failed: {e}. Retry in {wait}s...")
                time.sleep(wait)
        raise RuntimeError("Could not obtain presigned download URL after 9 attempts.")

    def _producer_loop(self):
        consecutive_zero_reads = 0
        consecutive_errors = 0
        while not self._stop_event.is_set():
            if time.time() - self._url_ts > 36000:
                logger.info("[MDC] Presigned URL nearing expiry -- refreshing...")
                self._refresh_url()

            resp = None
            try:
                headers = {"User-Agent": "datacollective-python/0.1.0"}
                is_resuming = self._producer_bytes_read > 0
                if is_resuming:
                    headers["Range"] = f"bytes={self._producer_bytes_read}-"
                    logger.info(f"[RESUME] Reconnecting at compressed offset {self._producer_bytes_read:,} B...")
                else:
                    logger.info("[RESUME] Opening initial stream from byte 0...")

                req = urllib.request.Request(self._url, headers=headers)
                resp = self._url_opener(req, timeout=120)

                # HTTP Range and Status Code Validation
                status_code = getattr(resp, "status", None)
                if status_code is None and hasattr(resp, "getcode"):
                    status_code = resp.getcode()
                if status_code is None and hasattr(resp, "code"):
                    status_code = resp.code

                content_range = None
                content_length_hdr = None
                if hasattr(resp, "headers") and resp.headers:
                    content_range = resp.headers.get("Content-Range")
                    content_length_hdr = resp.headers.get("Content-Length")
                elif hasattr(resp, "getheader"):
                    content_range = resp.getheader("Content-Range")
                    content_length_hdr = resp.getheader("Content-Length")

                parsed_cr_start: Optional[int] = None
                parsed_cr_end: Optional[int] = None
                parsed_cr_total: Optional[int] = None

                if content_range:
                    cr_str = content_range.strip()
                    if not cr_str.lower().startswith("bytes "):
                        raise IOError(f"Malformed Content-Range header: '{content_range}'")
                    range_and_total = cr_str[6:].strip()
                    if "/" not in range_and_total:
                        raise IOError(f"Malformed Content-Range header missing '/': '{content_range}'")
                    range_part, total_part = range_and_total.split("/", 1)
                    range_part = range_part.strip()
                    total_part = total_part.strip()

                    if "-" not in range_part:
                        raise IOError(f"Malformed Content-Range byte interval: '{content_range}'")
                    start_str, end_str = range_part.split("-", 1)
                    try:
                        parsed_cr_start = int(start_str.strip())
                        parsed_cr_end = int(end_str.strip())
                    except ValueError:
                        raise IOError(f"Malformed non-integer byte range in Content-Range: '{content_range}'")

                    if parsed_cr_start < 0:
                        raise IOError(f"Invalid negative start in Content-Range: {parsed_cr_start}")
                    if parsed_cr_end < parsed_cr_start:
                        raise IOError(
                            f"Invalid inverted range in Content-Range: end {parsed_cr_end} < start {parsed_cr_start} ('{content_range}')"
                        )

                    if total_part != "*":
                        try:
                            parsed_cr_total = int(total_part)
                        except ValueError:
                            raise IOError(f"Malformed non-integer total in Content-Range: '{content_range}'")
                        if parsed_cr_total <= parsed_cr_end:
                            raise IOError(
                                f"Invalid total in Content-Range: total {parsed_cr_total} <= end {parsed_cr_end} ('{content_range}')"
                            )

                        # Validate consistency of total resource length across connections
                        if self._expected_total_bytes is None:
                            self._expected_total_bytes = parsed_cr_total
                            logger.info(f"[STREAM] Total archive size recorded: {self._expected_total_bytes:,} B")
                        elif parsed_cr_total != self._expected_total_bytes:
                            raise IOError(
                                f"Inconsistent resource total across reconnects: received {parsed_cr_total} "
                                f"but previously recorded {self._expected_total_bytes} ('{content_range}')"
                            )

                if is_resuming:
                    if status_code != 206:
                        raise IOError(
                            f"HTTP resume failed: server returned status {status_code} "
                            f"(expected 206 Partial Content) when requesting range bytes={self._producer_bytes_read}-"
                        )
                    if not content_range:
                        raise IOError(
                            f"HTTP resume failed: missing Content-Range header in 206 response at offset {self._producer_bytes_read}"
                        )
                    if parsed_cr_start != self._producer_bytes_read:
                        raise IOError(
                            f"HTTP resume failed: Content-Range start {parsed_cr_start} does not match "
                            f"requested offset {self._producer_bytes_read} ('{content_range}')"
                        )
                else:
                    # Initial connection (no Range header sent)
                    if status_code == 200:
                        if content_length_hdr and self._expected_total_bytes is None:
                            try:
                                self._expected_total_bytes = int(content_length_hdr.strip())
                                logger.info(f"[STREAM] Total archive size recorded from Content-Length: {self._expected_total_bytes:,} B")
                            except ValueError:
                                pass
                    elif status_code == 206:
                        if not content_range:
                            raise IOError("HTTP initial connect failed: server returned 206 Partial Content without Content-Range header")
                        if parsed_cr_start != 0:
                            raise IOError(
                                f"HTTP initial connect failed: server returned 206 Partial Content with non-zero start offset "
                                f"{parsed_cr_start} ('{content_range}')"
                            )
                    else:
                        raise IOError(f"HTTP initial connect failed: unexpected status {status_code} (expected 200 or 206)")

                consecutive_errors = 0
                bytes_this_conn = 0
                while not self._stop_event.is_set():
                    chunk = resp.read(2 * 1024 * 1024)
                    if not chunk:
                        logger.info(f"[RESUME] Socket closed by server at byte {self._producer_bytes_read:,}.")
                        if self._expected_total_bytes is not None and self._producer_bytes_read >= self._expected_total_bytes:
                            logger.info(f"[STREAM] Reached expected archive size ({self._producer_bytes_read:,} B). Entire archive received.")
                            self._stop_event.set()
                            break
                        if bytes_this_conn == 0:
                            consecutive_zero_reads += 1
                            if consecutive_zero_reads >= 3:
                                logger.info("[STREAM] Multiple zero-byte reads at offset. Entire archive consumed.")
                                self._stop_event.set()
                        else:
                            consecutive_zero_reads = 0
                        break

                    consecutive_zero_reads = 0
                    consecutive_errors = 0
                    bytes_this_conn += len(chunk)
                    self._producer_bytes_read += len(chunk)
                    if self._expected_total_bytes is not None and self._producer_bytes_read > self._expected_total_bytes:
                        err = IOError(
                            f"Excess compressed bytes received: stream delivered {self._producer_bytes_read:,} bytes, "
                            f"exceeding expected total of {self._expected_total_bytes:,} bytes."
                        )
                        logger.error(f"[STREAM] {err}")
                        self._producer_error = err
                        self._stop_event.set()
                        break
                    while not self._stop_event.is_set():
                        try:
                            self._queue.put(chunk, timeout=1.0)
                            break
                        except queue.Full:
                            continue

            except urllib.error.HTTPError as he:
                consecutive_errors += 1
                if he.code == 403 or consecutive_errors % 2 == 0:
                    logger.warning(f"[MDC] HTTP {he.code} / connection issue (attempt {consecutive_errors}) -- refreshing presigned URL...")
                    self._refresh_url()
                elif he.code == 416:
                    if self._expected_total_bytes is not None and self._producer_bytes_read < self._expected_total_bytes:
                        err = IOError(
                            f"HTTP 416 Range Not Satisfiable received prematurely at byte "
                            f"{self._producer_bytes_read:,} before archive fully received (expected {self._expected_total_bytes:,} B)."
                        )
                        logger.error(f"[STREAM] {err}")
                        self._producer_error = err
                        self._stop_event.set()
                        break
                    else:
                        logger.info(f"[STREAM] HTTP 416 at byte {self._producer_bytes_read:,}. Reached declared archive length.")
                        break
                if consecutive_errors >= 30:
                    self._producer_error = he
                    self._stop_event.set()
                    break
                wait_sec = min(2 ** min(consecutive_errors, 5), 30)
                time.sleep(wait_sec)
            except Exception as e:
                consecutive_errors += 1
                logger.warning(f"[STREAM] Connection/Stream error ({e}). Consecutive errors: {consecutive_errors}")
                if isinstance(e, IOError) and ("HTTP resume failed" in str(e) or "HTTP initial connect failed" in str(e) or "Inconsistent resource total" in str(e) or "Content-Range" in str(e)):
                    # Fatal range/resume contract violation
                    self._producer_error = e
                    self._stop_event.set()
                    break
                if consecutive_errors % 3 == 0:
                    logger.info(f"[STREAM] Refreshing presigned URL after {consecutive_errors} consecutive errors...")
                    try:
                        self._refresh_url()
                    except Exception as refresh_err:
                        logger.warning(f"[MDC] URL refresh attempt failed: {refresh_err}")
                if consecutive_errors >= 30:
                    self._producer_error = e
                    self._stop_event.set()
                    break
                if not self._stop_event.is_set():
                    wait_sec = min(2 ** min(consecutive_errors, 5), 30)
                    time.sleep(wait_sec)
            finally:
                if resp is not None:
                    try:
                        resp.close()
                    except Exception:
                        pass

        # Signal EOF or error to consumer
        self._queue.put(None)

    def _start_producer(self):
        self._producer_thread = threading.Thread(target=self._producer_loop, daemon=True)
        self._producer_thread.start()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def writable(self) -> bool:
        return False

    def readinto(self, b: bytearray | memoryview) -> int:
        if self._producer_error is not None:
            raise self._producer_error

        while len(self._uc_buf) == self._offset:
            if self._producer_error is not None:
                raise self._producer_error

            try:
                chunk = self._queue.get(timeout=60)
            except queue.Empty:
                if self._producer_error is not None:
                    raise self._producer_error
                if self._stop_event.is_set() or (self._producer_thread and not self._producer_thread.is_alive()):
                    flushed = self._decompressor.flush()
                    if flushed:
                        self._uc_buf = bytearray(flushed)
                        self._offset = 0
                        avail = len(self._uc_buf) - self._offset
                        n = min(len(b), avail)
                        b[:n] = self._uc_buf[self._offset : self._offset + n]
                        self._offset += n
                        return n
                    # Check EOF integrity
                    if not self._decompressor.eof:
                        raise IOError(
                            f"Incomplete gzip stream: reached end of stream without valid gzip EOF marker "
                            f"(compressed bytes read: {self.compressed_bytes_read:,}"
                            + (f" of expected {self._expected_total_bytes:,}" if self._expected_total_bytes else "")
                            + ")"
                        )
                    # Exact-length completion condition
                    if self._expected_total_bytes is not None:
                        if self._producer_bytes_read < self._expected_total_bytes:
                            raise IOError(
                                f"Incomplete download: stream ended at byte {self._producer_bytes_read:,} "
                                f"before reaching expected total of {self._expected_total_bytes:,} bytes."
                            )
                        elif self._producer_bytes_read > self._expected_total_bytes:
                            raise IOError(
                                f"Excess compressed bytes received: stream delivered {self._producer_bytes_read:,} bytes, "
                                f"exceeding expected total of {self._expected_total_bytes:,} bytes."
                            )
                    # Check for unexpected trailing data after gzip member
                    if self._decompressor.unused_data:
                        raise IOError(
                            f"Unexpected trailing compressed data: found {len(self._decompressor.unused_data):,} unexpected bytes "
                            f"after gzip EOF marker."
                        )
                    return 0
                logger.info("[STREAM] Waiting for chunks from network producer...")
                continue

            if chunk is None:
                if self._producer_error is not None:
                    raise self._producer_error
                self._queue.put(None)
                flushed = self._decompressor.flush()
                if flushed:
                    self._uc_buf = bytearray(flushed)
                    self._offset = 0
                    avail = len(self._uc_buf) - self._offset
                    n = min(len(b), avail)
                    b[:n] = self._uc_buf[self._offset : self._offset + n]
                    self._offset += n
                    return n
                # Check EOF integrity
                if not self._decompressor.eof:
                    raise IOError(
                        f"Incomplete gzip stream: reached end of stream without valid gzip EOF marker "
                        f"(compressed bytes read: {self.compressed_bytes_read:,}"
                        + (f" of expected {self._expected_total_bytes:,}" if self._expected_total_bytes else "")
                        + ")"
                    )
                # Exact-length completion condition
                if self._expected_total_bytes is not None:
                    if self._producer_bytes_read < self._expected_total_bytes:
                        raise IOError(
                            f"Incomplete download: stream ended at byte {self._producer_bytes_read:,} "
                            f"before reaching expected total of {self._expected_total_bytes:,} bytes."
                        )
                    elif self._producer_bytes_read > self._expected_total_bytes:
                        raise IOError(
                            f"Excess compressed bytes received: stream delivered {self._producer_bytes_read:,} bytes, "
                            f"exceeding expected total of {self._expected_total_bytes:,} bytes."
                        )
                # Check for unexpected trailing data after gzip member
                if self._decompressor.unused_data:
                    raise IOError(
                        f"Unexpected trailing compressed data: found {len(self._decompressor.unused_data):,} unexpected bytes "
                        f"after gzip EOF marker."
                    )
                return 0

            if self._decompressor.eof:
                raise IOError(
                    f"Unexpected trailing compressed data: received extra chunk of {len(chunk)} bytes "
                    f"after gzip EOF marker."
                )

            self.compressed_bytes_read += len(chunk)
            decomp = self._decompressor.decompress(chunk)
            if self._decompressor.eof and self._decompressor.unused_data:
                raise IOError(
                    f"Unexpected trailing compressed data: found {len(self._decompressor.unused_data):,} unexpected bytes "
                    f"after gzip EOF marker."
                )
            if decomp:
                self._uc_buf = bytearray(decomp)
                self._offset = 0

        avail = len(self._uc_buf) - self._offset
        n = min(len(b), avail)
        b[:n] = self._uc_buf[self._offset : self._offset + n]
        self._offset += n
        return n

    def close(self):
        self._stop_event.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        super().close()


def load_provisional_manifest(manifest_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Loads approved provisional manifest JSON.
    Returns: (metadata, records, target_map) where target_map maps clip_filename -> row dict.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Provisional manifest missing: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    records = data.get("records", [])

    if len(records) != TOTAL_EXPECTED_CLIPS:
        raise ValueError(
            f"Provisional manifest row count mismatch: expected {TOTAL_EXPECTED_CLIPS}, found {len(records)}"
        )

    target_map: Dict[str, Dict[str, Any]] = {}
    for r in records:
        clip_fname = r["clip_filename"]
        if clip_fname in target_map:
            raise ValueError(f"Duplicate clip filename in manifest: {clip_fname}")
        target_map[clip_fname] = r

    logger.info(f"Loaded provisional manifest: {len(records):,} records across {len(target_map):,} unique clips.")
    return meta, records, target_map


def scan_local_inventory(target_map: Dict[str, Dict[str, Any]], audio_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Scans destination audio_dir for clips referenced by target_map.
    Returns: (valid_inventory, failed_inventory)
    """
    audio_dir.mkdir(parents=True, exist_ok=True)
    valid_inv: Dict[str, Dict[str, Any]] = {}
    failed_inv: Dict[str, Dict[str, Any]] = {}

    for clip_fname, r in target_map.items():
        rec_id = r["recording_id"]
        local_path = audio_dir / f"{rec_id}.mp3"
        if local_path.exists():
            is_valid, dur, sr, ch, h, err = validate_audio_file(local_path)
            item = {
                "recording_id": rec_id,
                "clip_filename": clip_fname,
                "speaker_id": r["speaker_id"],
                "accent_group": r["accent_group"],
                "stratum_code": r["stratum_code"],
                "panel_role": r["panel_role"],
                "source_path": r["source_path"],
                "local_path": safe_rel_path(local_path),
                "file_size": local_path.stat().st_size,
                "duration_sec": dur,
                "sample_rate": sr,
                "channels": ch,
                "sha256": h,
                "transcript": r["transcript"],
                "word_count": r["word_count"],
                "validation_status": "PASS" if is_valid else "FAIL",
                "error_message": err,
            }
            if is_valid:
                valid_inv[clip_fname] = item
            else:
                failed_inv[clip_fname] = item

    return valid_inv, failed_inv


def materialize_from_local_source(
    source_dir: Path,
    target_map: Dict[str, Dict[str, Any]],
    valid_inv: Dict[str, Dict[str, Any]],
    failed_inv: Dict[str, Dict[str, Any]],
    audio_dir: Path,
) -> int:
    """Copies and validates target clips from a local source directory."""
    remaining = {k: v for k, v in target_map.items() if k not in valid_inv}
    logger.info(f"[LOCAL] Sourcing from: {source_dir}")
    logger.info(f"[LOCAL] Remaining clips to materialize: {len(remaining):,}")

    copied_count = 0
    for clip_fname, row in list(remaining.items()):
        cand_path = source_dir / clip_fname
        if not cand_path.exists():
            # Try recursive or alternative path
            cand_path = source_dir / row["source_path"]
            if not cand_path.exists():
                continue

        rec_id = row["recording_id"]
        dest_file = audio_dir / f"{rec_id}.mp3"
        shutil.copy2(cand_path, dest_file)

        is_valid, dur, sr, ch, h, err = validate_audio_file(dest_file)
        item = {
            "recording_id": rec_id,
            "clip_filename": clip_fname,
            "speaker_id": row["speaker_id"],
            "accent_group": row["accent_group"],
            "stratum_code": row["stratum_code"],
            "panel_role": row["panel_role"],
            "source_path": row["source_path"],
            "local_path": safe_rel_path(dest_file),
            "file_size": dest_file.stat().st_size,
            "duration_sec": dur,
            "sample_rate": sr,
            "channels": ch,
            "sha256": h,
            "transcript": row["transcript"],
            "word_count": row["word_count"],
            "validation_status": "PASS" if is_valid else "FAIL",
            "error_message": err,
        }
        if is_valid:
            valid_inv[clip_fname] = item
            if clip_fname in failed_inv:
                del failed_inv[clip_fname]
            del remaining[clip_fname]
            copied_count += 1
        else:
            failed_inv[clip_fname] = item

    logger.info(f"[LOCAL] Materialized and validated {copied_count:,} clips from local source.")
    return copied_count


def materialize_from_stream(
    target_map: Dict[str, Dict[str, Any]],
    valid_inv: Dict[str, Dict[str, Any]],
    failed_inv: Dict[str, Dict[str, Any]],
    audio_dir: Path,
    max_duration_seconds: Optional[float] = None,
):
    """Streams and extracts target clips from Mozilla Data Collective over HTTP."""
    remaining = {k: v for k, v in target_map.items() if k not in valid_inv}
    if not remaining:
        logger.info("[STREAM] All target clips already materialized -- skipping stream.")
        return

    load_dotenv()
    from datacollective.download import _get_download_plan, DOWNLOAD_SOURCE_SAVE

    def plan_getter():
        return _get_download_plan(DATASET_ID, CV27_DIR / "temp.tar.gz", DOWNLOAD_SOURCE_SAVE)

    t_start = time.time()
    t_last_hb = t_start
    member_no = 0

    resilient = ThreadedResilientGzipStream(DATASET_ID, plan_getter)
    buffered = io.BufferedReader(resilient, buffer_size=16 * 1024 * 1024)

    try:
        with tarfile.open(fileobj=buffered, mode="r|") as tar:
            for member in tar:
                member_no += 1
                name = member.name

                now = time.time()
                if now - t_last_hb >= 30.0:
                    t_last_hb = now
                    elapsed = now - t_start
                    base_curr = name.rsplit("/", 1)[-1]
                    logger.info(
                        f"[HB] elapsed={elapsed:.0f}s | members={member_no:,} | "
                        f"materialized={len(valid_inv):,}/{len(target_map):,} | "
                        f"remaining={len(remaining):,} | current={base_curr}"
                    )

                if max_duration_seconds and (now - t_start) > max_duration_seconds:
                    logger.info(f"[STREAM] Max execution duration {max_duration_seconds}s reached. Pausing stream.")
                    break

                if "clips/" not in name or not member.isfile():
                    continue

                base_name = name.rsplit("/", 1)[-1]
                if base_name not in remaining:
                    continue

                target_row = remaining[base_name]
                rec_id = target_row["recording_id"]
                dest_file = audio_dir / f"{rec_id}.mp3"

                extracted_f = tar.extractfile(member)
                if extracted_f is None:
                    continue

                with open(dest_file, "wb") as out_f:
                    while True:
                        data = extracted_f.read(65536)
                        if not data:
                            break
                        out_f.write(data)

                is_valid, dur, sr, ch, h, err = validate_audio_file(dest_file)
                item = {
                    "recording_id": rec_id,
                    "clip_filename": base_name,
                    "speaker_id": target_row["speaker_id"],
                    "accent_group": target_row["accent_group"],
                    "stratum_code": target_row["stratum_code"],
                    "panel_role": target_row["panel_role"],
                    "source_path": target_row["source_path"],
                    "local_path": safe_rel_path(dest_file),
                    "file_size": dest_file.stat().st_size,
                    "duration_sec": dur,
                    "sample_rate": sr,
                    "channels": ch,
                    "sha256": h,
                    "transcript": target_row["transcript"],
                    "word_count": target_row["word_count"],
                    "validation_status": "PASS" if is_valid else "FAIL",
                    "error_message": err,
                }
                if is_valid:
                    valid_inv[base_name] = item
                    if base_name in failed_inv:
                        del failed_inv[base_name]
                    del remaining[base_name]
                    logger.info(
                        f"[PASS] Materialized {rec_id} ({base_name}) [{len(valid_inv)}/{len(target_map)}] "
                        f"({dur:.2f}s, {sr}Hz, {ch}ch, sha256={h[:12]}...)"
                    )
                else:
                    failed_inv[base_name] = item
                    dest_file.unlink(missing_ok=True)
                    logger.warning(
                        f"[FAIL] Clip {base_name} ({rec_id}) failed validation: {err}"
                    )

                if not remaining:
                    logger.info(f"\n[STREAM] 100% TARGETS MATERIALIZED! ({len(valid_inv):,}/{len(target_map):,})")
                    break
    finally:
        resilient.close()


def generate_materialization_artifacts(
    manifest_meta: Dict[str, Any],
    records: List[Dict[str, Any]],
    target_map: Dict[str, Dict[str, Any]],
    valid_inv: Dict[str, Dict[str, Any]],
    failed_inv: Dict[str, Dict[str, Any]],
    audio_dir: Path,
    report_json_path: Optional[Path] = None,
    report_md_path: Optional[Path] = None,
    ledger_csv_path: Optional[Path] = None,
    speaker_report_path: Optional[Path] = None,
    failed_report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Computes per-speaker completeness, writes SHA-256 ledger, failed clips ledger,
    and produces machine-readable JSON and Markdown audit reports.
    Accepts explicit output paths for test and run isolation.
    """
    logger.info("Computing materialization completeness ledgers...")

    target_report_json = report_json_path or MATERIALIZATION_JSON
    target_report_md = report_md_path or MATERIALIZATION_MD
    target_ledger_csv = ledger_csv_path or LEDGER_CSV
    target_speaker_report = speaker_report_path or SPEAKER_REPORT_JSON
    target_failed_report = failed_report_path or FAILED_REPORT_JSON

    target_report_json.parent.mkdir(parents=True, exist_ok=True)
    target_report_md.parent.mkdir(parents=True, exist_ok=True)
    target_ledger_csv.parent.mkdir(parents=True, exist_ok=True)
    target_speaker_report.parent.mkdir(parents=True, exist_ok=True)
    target_failed_report.parent.mkdir(parents=True, exist_ok=True)

    # Speaker-level completeness: Initialize EVERY target speaker from the provisional manifest
    speaker_clips: Dict[str, List[Dict[str, Any]]] = {}
    speaker_strata: Dict[str, str] = {}
    speaker_roles: Dict[str, str] = {}
    for r in records:
        sid = r["speaker_id"]
        if sid not in speaker_clips:
            speaker_clips[sid] = []
            speaker_strata[sid] = r["accent_group"]
            speaker_roles[sid] = r["panel_role"]
        c_fname = r["clip_filename"]
        if c_fname in valid_inv:
            speaker_clips[sid].append(valid_inv[c_fname])

    speaker_completeness = {}
    complete_speakers_count = 0
    incomplete_speakers_count = 0
    for sid in sorted(speaker_clips.keys()):
        clips = speaker_clips[sid]
        is_comp = len(clips) == CLIPS_PER_SPEAKER
        if is_comp:
            complete_speakers_count += 1
        else:
            incomplete_speakers_count += 1
        speaker_completeness[sid] = {
            "speaker_id": sid,
            "accent_group": speaker_strata[sid],
            "panel_role": speaker_roles[sid],
            "materialized_clips_count": len(clips),
            "required_clips_count": CLIPS_PER_SPEAKER,
            "is_complete": is_comp,
        }

    # Write speaker completeness report
    with open(target_speaker_report, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_target_speakers": len(speaker_completeness),
                "complete_speakers": complete_speakers_count,
                "incomplete_speakers": incomplete_speakers_count,
                "speakers": speaker_completeness,
            },
            f,
            indent=2,
        )

    # Write failed clips report
    with open(target_failed_report, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_failed_count": len(failed_inv),
                "failed_clips": list(failed_inv.values()),
            },
            f,
            indent=2,
        )

    # Write per-clip SHA-256 ledger CSV
    inv_list = sorted(valid_inv.values(), key=lambda x: (x["stratum_code"], x["speaker_id"], x["recording_id"]))
    ledger_fieldnames = [
        "recording_id",
        "clip_filename",
        "speaker_id",
        "accent_group",
        "stratum_code",
        "panel_role",
        "local_path",
        "file_size",
        "duration_sec",
        "sample_rate",
        "channels",
        "sha256",
        "word_count",
        "transcript",
    ]
    with open(target_ledger_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        writer.writeheader()
        for item in inv_list:
            row_dict = {k: item.get(k, "") for k in ledger_fieldnames}
            writer.writerow(row_dict)

    ledger_sha256 = compute_sha256(target_ledger_csv)
    logger.info(f"Wrote SHA-256 ledger CSV: {target_ledger_csv} (SHA-256: {ledger_sha256})")

    # Aggregate metrics
    total_valid_clips = len(valid_inv)
    total_duration_sec = sum(x["duration_sec"] for x in valid_inv.values())
    total_bytes = sum(x["file_size"] for x in valid_inv.values())
    completion_rate_pct = (total_valid_clips / TOTAL_EXPECTED_CLIPS) * 100.0

    materialization_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": "v1.5-five-stratum-parity",
        "governing_standard": "Protocol Section 14.7 (Project-Lead Academic Authorization)",
        "governance_status": "AUTHORIZED_FOR_DATA_PREPARATION",
        "materialization_disposition": "COMPLETE_AND_VERIFIED"
        if total_valid_clips == TOTAL_EXPECTED_CLIPS
        else "IN_PROGRESS_CONTROLLED_PIPELINE",
        "manifest_status": "UNLOCKED (PROVISIONAL)",
        "target_scale": {
            "total_target_clips": TOTAL_EXPECTED_CLIPS,
            "total_target_speakers": TOTAL_EXPECTED_SPEAKERS,
            "clips_per_speaker": CLIPS_PER_SPEAKER,
            "evaluation_speakers": 1100,
            "gate_reference_speakers": 100,
            "australian_replacement_reserve_speakers": 65,
        },
        "materialized_scale": {
            "valid_clips_count": total_valid_clips,
            "remaining_clips_count": TOTAL_EXPECTED_CLIPS - total_valid_clips,
            "failed_clips_count": len(failed_inv),
            "total_target_speakers": len(speaker_completeness),
            "complete_speakers_count": complete_speakers_count,
            "incomplete_speakers_count": incomplete_speakers_count,
            "completion_rate_pct": round(completion_rate_pct, 4),
            "total_duration_seconds": round(total_duration_sec, 2),
            "total_duration_hours": round(total_duration_sec / 3600.0, 3),
            "total_bytes": total_bytes,
        },
        "ledger": {
            "ledger_csv": safe_rel_path(target_ledger_csv),
            "ledger_sha256": ledger_sha256,
        },
        "execution_gating": {
            "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
            "confirmatory_inference": "STRICTLY_BLOCKED",
            "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
        },
    }

    # Write JSON report
    with open(target_report_json, "w", encoding="utf-8") as f:
        json.dump(materialization_data, f, indent=2)

    # Write Markdown report
    ledger_url = f"file:///{target_ledger_csv.resolve().as_posix().lstrip('/')}"
    failed_url = f"file:///{target_failed_report.resolve().as_posix().lstrip('/')}"
    speaker_url = f"file:///{target_speaker_report.resolve().as_posix().lstrip('/')}"

    md_content = f"""# Stage 6M v1.5 — Cohort 3 Audio Materialization & Integrity Validation Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_AUDIO_MATERIALIZATION`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Project-Lead Academic Authorization)  
> **GOVERNANCE DISPOSITION:** **{materialization_data['materialization_disposition']}**  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** {materialization_data['timestamp_utc']}  

---

## 1. Executive Summary

This report documents the physical audio materialization and cryptographic integrity validation for **Cohort 3**:
- **Target Specification:** Exactly $18,975$ clips across $1,265$ unique speakers ($15$ clips/speaker) selected from Mozilla Common Voice 27.0.
- **Materialization Pipeline:** Controlled, deterministic pipeline with soundfile decodability verification, non-zero duration checks, and bitwise SHA-256 cryptographic hashing.
- **Current Progress:** **{total_valid_clips:,} / {TOTAL_EXPECTED_CLIPS:,}** clips verified ({completion_rate_pct:.2f}%).
- **Execution Gating:** Model adaptation and confirmatory inference remain **STRICTLY BLOCKED** under a separate execution-readiness decision.

---

## 2. Quantitative Materialization Inventory

| Metric | Target Requirement | Current Materialized | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Clips** | 16,500 ($1,100 \\times 15$) | {sum(1 for x in valid_inv.values() if x['panel_role'] == 'evaluation'):,} | **TRACKED** |
| **Gate-Reference Clips** | 1,500 ($100 \\times 15$) | {sum(1 for x in valid_inv.values() if x['panel_role'] == 'gate_reference'):,} | **TRACKED** |
| **Australian Reserve Clips** | 975 ($65 \\times 15$) | {sum(1 for x in valid_inv.values() if x['panel_role'] == 'australian_reserve'):,} | **TRACKED** |
| **Grand Total Audio Clips** | **18,975** | **{total_valid_clips:,}** | **{completion_rate_pct:.2f}%** |
| **Complete Speakers ($\\\\ge 15$ valid clips)** | 1,265 | {complete_speakers_count:,} / {len(speaker_completeness):,} (Incomplete: {incomplete_speakers_count:,}) | **{('PASS' if complete_speakers_count == len(speaker_completeness) and len(speaker_completeness) > 0 else 'IN_PROGRESS')}** |
| **Failed / Corrupt Clips** | 0 allowed | {len(failed_inv)} | **{('PASS' if len(failed_inv) == 0 else 'INVESTIGATE')}** |
| **Total Physical Audio Duration** | — | {total_duration_sec:.2f} s ({total_duration_sec/3600.0:.2f} h) | **NOMINAL** |
| **Total Physical Audio Bytes** | — | {total_bytes:,} bytes ({total_bytes / (1024*1024):.2f} MB) | **NOMINAL** |

---

## 3. Cryptographic Provenance & Ledgers

- **Per-Clip SHA-256 Ledger:** [`{safe_rel_path(target_ledger_csv)}`]({ledger_url})  
  - Ledger File SHA-256: `{ledger_sha256}`
- **Failed Clips Ledger:** [`{safe_rel_path(target_failed_report)}`]({failed_url})
- **Speaker Completeness Report:** [`{safe_rel_path(target_speaker_report)}`]({speaker_url})

---

## 4. Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: AUTHORIZED (DATA PREPARATION)                   ║
║                                                                                      ║
║  1. Materialization pipeline and integrity validator are fully operational.          ║
║  2. Manifest remains explicitly UNLOCKED / PROVISIONAL.                              ║
║  3. Final manifest locking is CONDITIONAL upon 100% verified materialization.        ║
║  4. Confirmatory GPU adaptation & model inference remain STRICTLY BLOCKED.           ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
"""

    with open(target_report_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Wrote materialization report MD: {target_report_md}")
    logger.info(f"Wrote materialization report JSON: {target_report_json}")
    return materialization_data


def select_pilot_speakers_and_clips(
    records: List[Dict[str, Any]],
    parent_manifest_sha256: str,
) -> Tuple[List[str], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Deterministically selects exactly 5 speakers (1 from each confirmatory evaluation stratum)
    and their corresponding 15 clips each (75 clips total) from the provisional manifest.
    Verifies zero substitution, exact clip counts, and records parent manifest traceability.
    """
    eval_records = [r for r in records if r.get("panel_role") == "evaluation"]
    strata_speakers: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in eval_records:
        strata_speakers[r["accent_group"]][r["speaker_id"]].append(r)

    pilot_speaker_ids: List[str] = []
    pilot_records: List[Dict[str, Any]] = []
    pilot_target_map: Dict[str, Dict[str, Any]] = {}

    for stratum in sorted(PILOT_CONFIRMATORY_STRATA):
        if stratum not in strata_speakers:
            raise ValueError(f"Pilot selection error: missing confirmatory stratum '{stratum}' in manifest")
        available_speakers = sorted(strata_speakers[stratum].keys())
        if not available_speakers:
            raise ValueError(f"Pilot selection error: zero evaluation speakers found for stratum '{stratum}'")

        # Deterministic selection: first speaker sorted by speaker_id in each stratum
        selected_spk = available_speakers[0]
        spk_clips = strata_speakers[stratum][selected_spk]
        if len(spk_clips) != PILOT_EXPECTED_CLIPS_PER_SPEAKER:
            raise ValueError(
                f"Pilot speaker {selected_spk} in {stratum} has {len(spk_clips)} clips "
                f"(expected exactly {PILOT_EXPECTED_CLIPS_PER_SPEAKER})"
            )
        pilot_speaker_ids.append(selected_spk)
        for c in spk_clips:
            clip_fname = c["clip_filename"]
            if clip_fname in pilot_target_map:
                raise ValueError(f"Duplicate clip filename in pilot: {clip_fname}")
            pilot_target_map[clip_fname] = c
            pilot_records.append(c)

    if len(pilot_speaker_ids) != PILOT_EXPECTED_SPEAKERS:
        raise ValueError(f"Pilot speaker count mismatch: {len(pilot_speaker_ids)} != {PILOT_EXPECTED_SPEAKERS}")
    if len(pilot_target_map) != PILOT_TOTAL_EXPECTED_CLIPS:
        raise ValueError(f"Pilot clip count mismatch: {len(pilot_target_map)} != {PILOT_TOTAL_EXPECTED_CLIPS}")

    logger.info(
        f"[PILOT] Selected {len(pilot_speaker_ids)} speakers across {len(PILOT_CONFIRMATORY_STRATA)} strata: "
        f"{len(pilot_target_map)} clips total."
    )
    return pilot_speaker_ids, pilot_target_map, pilot_records


def generate_pilot_materialization_artifacts(
    parent_meta: Dict[str, Any],
    parent_manifest_sha256: str,
    pilot_speaker_ids: List[str],
    pilot_records: List[Dict[str, Any]],
    pilot_target_map: Dict[str, Dict[str, Any]],
    valid_inv: Dict[str, Dict[str, Any]],
    failed_inv: Dict[str, Dict[str, Any]],
    audio_dir: Path,
    report_json_path: Optional[Path] = None,
    report_md_path: Optional[Path] = None,
    ledger_csv_path: Optional[Path] = None,
    speaker_report_path: Optional[Path] = None,
    failed_report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generates isolated pilot materialization artifacts, reports, and ledgers
    without overwriting full-cohort reports.
    Records parent provisional manifest SHA-256 for cryptographic traceability.
    Accepts explicit output paths for test and run isolation.
    """
    logger.info("Computing pilot materialization completeness ledgers...")

    target_report_json = report_json_path or PILOT_MATERIALIZATION_JSON
    target_report_md = report_md_path or PILOT_MATERIALIZATION_MD
    target_ledger_csv = ledger_csv_path or PILOT_LEDGER_CSV
    target_speaker_report = speaker_report_path or PILOT_SPEAKER_REPORT_JSON
    target_failed_report = failed_report_path or PILOT_FAILED_REPORT_JSON

    target_report_json.parent.mkdir(parents=True, exist_ok=True)
    target_report_md.parent.mkdir(parents=True, exist_ok=True)
    target_ledger_csv.parent.mkdir(parents=True, exist_ok=True)
    target_speaker_report.parent.mkdir(parents=True, exist_ok=True)
    target_failed_report.parent.mkdir(parents=True, exist_ok=True)

    speaker_clips: Dict[str, List[Dict[str, Any]]] = {sid: [] for sid in pilot_speaker_ids}
    speaker_strata: Dict[str, str] = {}
    speaker_roles: Dict[str, str] = {}
    for r in pilot_records:
        sid = r["speaker_id"]
        speaker_strata[sid] = r["accent_group"]
        speaker_roles[sid] = r["panel_role"]
        c_fname = r["clip_filename"]
        if c_fname in valid_inv:
            speaker_clips[sid].append(valid_inv[c_fname])

    speaker_completeness = {}
    complete_speakers_count = 0
    incomplete_speakers_count = 0
    for sid in sorted(speaker_clips.keys()):
        clips = speaker_clips[sid]
        is_comp = len(clips) == PILOT_EXPECTED_CLIPS_PER_SPEAKER
        if is_comp:
            complete_speakers_count += 1
        else:
            incomplete_speakers_count += 1
        speaker_completeness[sid] = {
            "speaker_id": sid,
            "accent_group": speaker_strata[sid],
            "panel_role": speaker_roles[sid],
            "materialized_clips_count": len(clips),
            "required_clips_count": PILOT_EXPECTED_CLIPS_PER_SPEAKER,
            "is_complete": is_comp,
        }

    # 1. Write pilot speaker completeness report
    with open(target_speaker_report, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "parent_provisional_manifest_sha256": parent_manifest_sha256,
                "total_target_speakers": len(speaker_completeness),
                "complete_speakers": complete_speakers_count,
                "incomplete_speakers": incomplete_speakers_count,
                "speakers": speaker_completeness,
            },
            f,
            indent=2,
        )

    # 2. Write pilot failed clips report
    with open(target_failed_report, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "parent_provisional_manifest_sha256": parent_manifest_sha256,
                "total_failed_count": len(failed_inv),
                "failed_clips": list(failed_inv.values()),
            },
            f,
            indent=2,
        )

    # 3. Write pilot per-clip SHA-256 ledger CSV
    inv_list = sorted(valid_inv.values(), key=lambda x: (x["stratum_code"], x["speaker_id"], x["recording_id"]))
    ledger_fieldnames = [
        "recording_id",
        "clip_filename",
        "speaker_id",
        "accent_group",
        "stratum_code",
        "panel_role",
        "local_path",
        "file_size",
        "duration_sec",
        "sample_rate",
        "channels",
        "sha256",
        "word_count",
        "transcript",
    ]
    with open(target_ledger_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ledger_fieldnames)
        writer.writeheader()
        for item in inv_list:
            row_dict = {k: item.get(k, "") for k in ledger_fieldnames}
            writer.writerow(row_dict)

    pilot_ledger_sha256 = compute_sha256(target_ledger_csv)
    logger.info(f"Wrote Pilot SHA-256 ledger CSV: {target_ledger_csv} (SHA-256: {pilot_ledger_sha256})")

    # Aggregate metrics
    total_valid_clips = len(valid_inv)
    total_duration_sec = sum(x["duration_sec"] for x in valid_inv.values())
    total_bytes = sum(x["file_size"] for x in valid_inv.values())
    completion_rate_pct = (total_valid_clips / PILOT_TOTAL_EXPECTED_CLIPS) * 100.0

    pilot_disposition = (
        "PILOT_COMPLETE_AND_VERIFIED"
        if total_valid_clips == PILOT_TOTAL_EXPECTED_CLIPS and len(failed_inv) == 0
        else ("PILOT_ZERO_AUDIO_DRY_RUN" if total_valid_clips == 0 else "PILOT_IN_PROGRESS")
    )

    pilot_data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": "v1.5-five-stratum-parity",
        "governing_standard": "Protocol Section 14.7 (Controlled Materialization Pilot)",
        "governance_status": "PILOT_AUTHORIZED_BY_PROJECT_LEAD",
        "materialization_disposition": pilot_disposition,
        "manifest_status": "UNLOCKED (PROVISIONAL)",
        "parent_provisional_manifest": {
            "path": safe_rel_path(PROVISIONAL_MANIFEST_JSON),
            "sha256": parent_manifest_sha256,
            "total_parent_clips": len(parent_meta.get("records", [])) if "records" in parent_meta else TOTAL_EXPECTED_CLIPS,
        },
        "target_scale": {
            "total_target_clips": PILOT_TOTAL_EXPECTED_CLIPS,
            "total_target_speakers": PILOT_EXPECTED_SPEAKERS,
            "clips_per_speaker": PILOT_EXPECTED_CLIPS_PER_SPEAKER,
            "confirmatory_strata_count": len(PILOT_CONFIRMATORY_STRATA),
            "confirmatory_strata": PILOT_CONFIRMATORY_STRATA,
            "panel_role": "evaluation",
        },
        "materialized_scale": {
            "valid_clips_count": total_valid_clips,
            "remaining_clips_count": PILOT_TOTAL_EXPECTED_CLIPS - total_valid_clips,
            "failed_clips_count": len(failed_inv),
            "total_target_speakers": len(speaker_completeness),
            "complete_speakers_count": complete_speakers_count,
            "incomplete_speakers_count": incomplete_speakers_count,
            "completion_rate_pct": round(completion_rate_pct, 4),
            "total_duration_seconds": round(total_duration_sec, 2),
            "total_duration_hours": round(total_duration_sec / 3600.0, 4),
            "total_bytes": total_bytes,
        },
        "pilot_speakers": {
            sid: {
                "accent_group": speaker_strata[sid],
                "panel_role": speaker_roles[sid],
                "materialized_clips": len(speaker_clips[sid]),
                "required_clips": PILOT_EXPECTED_CLIPS_PER_SPEAKER,
                "is_complete": len(speaker_clips[sid]) == PILOT_EXPECTED_CLIPS_PER_SPEAKER,
            }
            for sid in sorted(speaker_clips.keys())
        },
        "ledger": {
            "ledger_csv": safe_rel_path(target_ledger_csv),
            "ledger_sha256": pilot_ledger_sha256,
        },
        "execution_gating": {
            "controlled_pilot_download": "AUTHORIZED_BY_PROJECT_LEAD",
            "gpu_ctta_adaptation": "STRICTLY_BLOCKED",
            "confirmatory_inference": "STRICTLY_BLOCKED",
            "full_cohort_materialization": "HELD_PENDING_PILOT_VERIFICATION",
            "final_manifest_lock": "BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION",
        },
    }

    # 4. Write pilot JSON report
    with open(target_report_json, "w", encoding="utf-8") as f:
        json.dump(pilot_data, f, indent=2)

    # 5. Write pilot Markdown report
    speaker_table_rows = []
    for sid in sorted(speaker_clips.keys()):
        strat = speaker_strata[sid]
        n_mat = len(speaker_clips[sid])
        is_c = "PASS" if n_mat == PILOT_EXPECTED_CLIPS_PER_SPEAKER else "INCOMPLETE"
        speaker_table_rows.append(
            f"| **{strat}** | `{sid[:16]}...` | {PILOT_EXPECTED_CLIPS_PER_SPEAKER} | {n_mat} | **{is_c}** |"
        )
    speaker_table_str = "\n".join(speaker_table_rows)

    ledger_url = f"file:///{target_ledger_csv.resolve().as_posix().lstrip('/')}"
    failed_url = f"file:///{target_failed_report.resolve().as_posix().lstrip('/')}"
    speaker_url = f"file:///{target_speaker_report.resolve().as_posix().lstrip('/')}"

    md_content = f"""# Stage 6M v1.5 — Cohort 3 Controlled Audio Materialization Pilot Report

> **DOCUMENT ID:** `STAGE6M_COHORT3_PILOT_MATERIALIZATION`  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol  
> **GOVERNING STANDARD:** Protocol Section 14.7 (Controlled Materialization Pilot)  
> **GOVERNANCE DISPOSITION:** **{pilot_data['materialization_disposition']}**  
> **PARENT PROVISIONAL MANIFEST:** [`{pilot_data['parent_provisional_manifest']['path']}`](file:///{PROJECT_ROOT.as_posix()}/{pilot_data['parent_provisional_manifest']['path']}) (SHA-256: `{parent_manifest_sha256}`)  
> **PROVISIONAL MANIFEST STATUS:** **UNLOCKED (PROVISIONAL)**  
> **EXECUTION GATING:** **GPU CTTA Adaptation & Confirmatory Inference STRICTLY BLOCKED**  
> **TIMESTAMP (UTC):** {pilot_data['timestamp_utc']}  

---

## 1. Executive Summary

This report documents the preparation and execution of the **Controlled Audio Materialization Pilot** for **Cohort 3**:
- **Target Specification:** Exactly $75$ clips across $5$ unique speakers ($1$ speaker per confirmatory evaluation stratum $\\times 15$ clips/speaker).
- **Stratum Representation:** Australian English, Canadian English, England English, South Asian English, US English.
- **Parent Manifest Traceability:** Deterministically derived from provisional manifest (SHA-256 `{parent_manifest_sha256}`).
- **Current Progress:** **{total_valid_clips:,} / {PILOT_TOTAL_EXPECTED_CLIPS:,}** clips verified ({completion_rate_pct:.2f}%).
- **Execution Gating:** Confirmatory GPU CTTA adaptation and model inference remain **STRICTLY BLOCKED**.

---

## 2. Quantitative Pilot Inventory

| Stratum | Speaker ID | Target Clips | Materialized | Status |
| :--- | :--- | :---: | :---: | :---: |
{speaker_table_str}
| **Grand Total** | **5 Speakers** | **{PILOT_TOTAL_EXPECTED_CLIPS}** | **{total_valid_clips}** | **{('PASS' if complete_speakers_count == PILOT_EXPECTED_SPEAKERS else 'IN_PROGRESS')}** |

---

## 3. Cryptographic Provenance & Ledgers

- **Pilot SHA-256 Ledger:** [`{safe_rel_path(target_ledger_csv)}`]({ledger_url})  
  - Ledger File SHA-256: `{pilot_ledger_sha256}`
- **Pilot Speaker Completeness Report:** [`{safe_rel_path(target_speaker_report)}`]({speaker_url})
- **Pilot Failed Clips Report:** [`{safe_rel_path(target_failed_report)}`]({failed_url})
- **Parent Provisional Manifest:** [`{pilot_data['parent_provisional_manifest']['path']}`](file:///{PROJECT_ROOT.as_posix()}/{pilot_data['parent_provisional_manifest']['path']}) (SHA-256: `{parent_manifest_sha256}`)

---

## 4. Execution Gating & Next Operational Milestones

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                   GOVERNANCE STATUS: CONTROLLED PILOT AUTHORIZED                     ║
║                                                                                      ║
║  1. 75-clip pilot execution harness is authorized by Project-Lead (Sec 14.7).        ║
║  2. Pilot manifests and ledgers are distinct; full-cohort reports are untouched.     ║
║  3. Physical acquisition strictly confined to 5 speakers x 15 clips = 75 clips.      ║
║  4. Confirmatory GPU adaptation & model inference remain STRICTLY BLOCKED.           ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
"""

    with open(target_report_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Wrote pilot materialization report MD: {target_report_md}")
    logger.info(f"Wrote pilot materialization report JSON: {target_report_json}")
    return pilot_data


def main():
    parser = argparse.ArgumentParser(
        description="Stage 6M v1.5 Cohort 3 Controlled Audio Materialization Pipeline"
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=PROVISIONAL_MANIFEST_JSON,
        help="Path to provisional manifest JSON",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=COHORT3_AUDIO_DIR,
        help="Destination directory for materialized audio",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional destination directory for reports and ledgers (defaults to repository paths)",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run controlled 75-clip pilot materialization (5 speakers, 1 per stratum x 15 clips)",
    )
    parser.add_argument(
        "--pilot-audio-dir",
        type=Path,
        default=COHORT3_PILOT_AUDIO_DIR,
        help="Destination directory for pilot audio clips (default: datasets/external/common_voice_27/cohort3_pilot_audio)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional local source directory containing Common Voice MP3s",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream from Mozilla Data Collective over HTTP",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate already-materialized clips on disk without streaming",
    )
    parser.add_argument(
        "--max-stream-seconds",
        type=float,
        default=None,
        help="Optional maximum streaming runtime in seconds (for batch/testing)",
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        default=HARDENING_AUDIT_JSON,
        help="Path to materializer hardening audit JSON (for governance authorization checks)",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Stage 6M v1.5 — Cohort 3 Audio Materialization & Integrity Validation")
    logger.info("Governing Standard: Protocol Section 14.7 (Project-Lead Academic Authorization)")
    logger.info("=" * 80)

    # 1. Load provisional manifest
    meta, records, full_target_map = load_provisional_manifest(args.manifest_json)

    # 2. Pilot mode vs Full Cohort mode
    if args.pilot:
        logger.info("[PILOT] Running in Controlled Pilot Mode (75 clips across 5 confirmatory evaluation strata)...")
        parent_manifest_sha256 = compute_sha256(args.manifest_json)
        pilot_spk_ids, pilot_target_map, pilot_records = select_pilot_speakers_and_clips(
            records, parent_manifest_sha256
        )

        pilot_dest_dir = args.pilot_audio_dir if args.audio_dir == COHORT3_AUDIO_DIR else args.audio_dir
        logger.info(f"[PILOT] Destination directory: {pilot_dest_dir}")

        valid_inv, failed_inv = scan_local_inventory(pilot_target_map, pilot_dest_dir)
        logger.info(f"[PILOT] Initial scan: {len(valid_inv)} / {len(pilot_target_map)} pilot clips validated on disk.")

        if args.source_dir and args.source_dir.exists():
            materialize_from_local_source(args.source_dir, pilot_target_map, valid_inv, failed_inv, pilot_dest_dir)

        if args.stream and not args.validate_only:
            verify_pilot_materialization_authorization(args.audit_json)
            materialize_from_stream(
                pilot_target_map, valid_inv, failed_inv, pilot_dest_dir, max_duration_seconds=args.max_stream_seconds
            )

        output_kwargs = {}
        if args.output_dir:
            out = args.output_dir
            out.mkdir(parents=True, exist_ok=True)
            output_kwargs = {
                "report_json_path": out / "stage6m_cohort3_pilot_materialization.json",
                "report_md_path": out / "stage6m_cohort3_pilot_materialization.md",
                "ledger_csv_path": out / "stage6m_cohort3_pilot_clip_sha256_ledger.csv",
                "speaker_report_path": out / "stage6m_cohort3_pilot_speaker_completeness_report.json",
                "failed_report_path": out / "stage6m_cohort3_pilot_failed_clips_report.json",
            }

        generate_pilot_materialization_artifacts(
            meta,
            parent_manifest_sha256,
            pilot_spk_ids,
            pilot_records,
            pilot_target_map,
            valid_inv,
            failed_inv,
            pilot_dest_dir,
            **output_kwargs,
        )
        return

    # Full Cohort Mode:
    valid_inv, failed_inv = scan_local_inventory(full_target_map, args.audio_dir)
    logger.info(f"Initial scan: {len(valid_inv):,} / {len(full_target_map):,} clips already validated on disk.")

    if args.source_dir and args.source_dir.exists():
        materialize_from_local_source(args.source_dir, full_target_map, valid_inv, failed_inv, args.audio_dir)

    if args.stream and not args.validate_only:
        verify_full_cohort_materialization_authorization(args.audit_json)
        materialize_from_stream(
            full_target_map, valid_inv, failed_inv, args.audio_dir, max_duration_seconds=args.max_stream_seconds
        )

    output_kwargs = {}
    if args.output_dir:
        out = args.output_dir
        out.mkdir(parents=True, exist_ok=True)
        output_kwargs = {
            "report_json_path": out / "stage6m_cohort3_audio_materialization.json",
            "report_md_path": out / "stage6m_cohort3_audio_materialization.md",
            "ledger_csv_path": out / "stage6m_cohort3_clip_sha256_ledger.csv",
            "speaker_report_path": out / "stage6m_cohort3_speaker_completeness_report.json",
            "failed_report_path": out / "stage6m_cohort3_failed_clips_report.json",
        }

    generate_materialization_artifacts(
        meta,
        records,
        full_target_map,
        valid_inv,
        failed_inv,
        args.audio_dir,
        **output_kwargs,
    )


if __name__ == "__main__":
    main()
