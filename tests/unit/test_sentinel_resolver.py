"""
Unit tests for SentinelAudioResolver (Stage 5D Phase 2).
========================================================
Verifies canonical resolution contract:
1. Strict manifest lookup (no fuzzy / directory scanning)
2. File existence and non-empty check
3. Cryptographic SHA-256 validation
4. Strict fail-closed semantics on any integrity failure
"""

import hashlib
import json
import pytest
from pathlib import Path

from dsg_ctta.controller.resolver import (
    SentinelAudioResolver,
    SentinelAudioResolutionError,
)
from dsg_ctta.controller.exceptions import FailClosedException


@pytest.fixture
def sentinel_fixture(tmp_path):
    """Creates a temporary isolated manifest and audio directory fixture."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)

    # Valid clip 1
    clip1_path = audio_dir / "sentinel_01_01_01.mp3"
    clip1_data = b"VALID_AUDIO_PAYLOAD_CLIP_1"
    clip1_path.write_bytes(clip1_data)
    clip1_hash = hashlib.sha256(clip1_data).hexdigest()

    # Valid clip 2
    clip2_path = audio_dir / "sentinel_01_01_02.mp3"
    clip2_data = b"VALID_AUDIO_PAYLOAD_CLIP_2"
    clip2_path.write_bytes(clip2_data)
    clip2_hash = hashlib.sha256(clip2_data).hexdigest()

    # Tampered clip 3 (hash in manifest won't match data)
    clip3_path = audio_dir / "sentinel_01_01_03.mp3"
    clip3_data = b"TAMPERED_OR_CORRUPT_DATA"
    clip3_path.write_bytes(clip3_data)

    # Empty clip 4 (0 bytes)
    clip4_path = audio_dir / "sentinel_01_01_04.mp3"
    clip4_path.write_bytes(b"")

    manifest_path = tmp_path / "manifest.json"
    manifest_data = {
        "panel_id": "test_sentinel_panel",
        "clips": {
            "sentinel_01_01_01": {
                "source_path": "common_voice_en_1001.mp3",
                "local_path": f"audio/sentinel_01_01_01.mp3",
                "audio_hash": clip1_hash,
                "duration": 2.5,
                "speaker_id": "spk_01",
                "stage5_accent_group": "US English",
            },
            "sentinel_01_01_02": {
                "source_path": "common_voice_en_1002.mp3",
                "local_path": f"audio/sentinel_01_02.mp3",  # Note: missing on disk!
                "audio_hash": clip2_hash,
                "duration": 3.0,
                "speaker_id": "spk_01",
                "stage5_accent_group": "US English",
            },
            "sentinel_01_01_03": {
                "source_path": "common_voice_en_1003.mp3",
                "local_path": f"audio/sentinel_01_01_03.mp3",
                "audio_hash": "0000000000000000000000000000000000000000000000000000000000000000",  # mismatched!
                "duration": 1.5,
                "speaker_id": "spk_01",
                "stage5_accent_group": "US English",
            },
            "sentinel_01_01_04": {
                "source_path": "common_voice_en_1004.mp3",
                "local_path": f"audio/sentinel_01_01_04.mp3",
                "audio_hash": hashlib.sha256(b"").hexdigest(),
                "duration": 0.0,
                "speaker_id": "spk_01",
                "stage5_accent_group": "US English",
            },
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    return {
        "root": tmp_path,
        "manifest_path": manifest_path,
        "clip1_path": clip1_path,
        "clip1_hash": clip1_hash,
    }


def test_resolver_success(sentinel_fixture):
    """Test successful resolution by ID, source filename, and dict record."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    assert resolver.is_loaded
    assert resolver.total_clips == 4

    # 1. Resolve by canonical ID
    res1 = resolver.resolve("sentinel_01_01_01")
    assert res1.exists()
    assert res1.samefile(sentinel_fixture["clip1_path"])

    # 2. Resolve by source filename
    res2 = resolver.resolve("common_voice_en_1001.mp3")
    assert res2.samefile(sentinel_fixture["clip1_path"])

    # 3. Resolve by dict record
    rec = {"sentinel_id": "sentinel_01_01_01", "audio_path": "common_voice_en_1001.mp3"}
    res3 = resolver.resolve(rec)
    assert res3.samefile(sentinel_fixture["clip1_path"])


def test_resolver_missing_clip_fail_closed(sentinel_fixture):
    """Unregistered clip must fail closed immediately."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    with pytest.raises(SentinelAudioResolutionError) as exc_info:
        resolver.resolve("sentinel_99_99_99")
    assert "FAIL-CLOSED" in str(exc_info.value)
    assert issubclass(SentinelAudioResolutionError, FailClosedException)


def test_resolver_missing_file_fail_closed(sentinel_fixture):
    """Registered clip whose local file does not exist must fail closed."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    with pytest.raises(SentinelAudioResolutionError) as exc_info:
        resolver.resolve("sentinel_01_01_02")
    assert "FAIL-CLOSED" in str(exc_info.value)
    assert "missing on disk" in str(exc_info.value)


def test_resolver_empty_file_fail_closed(sentinel_fixture):
    """0-byte audio file must fail closed."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    with pytest.raises(SentinelAudioResolutionError) as exc_info:
        resolver.resolve("sentinel_01_01_04")
    assert "FAIL-CLOSED" in str(exc_info.value)
    assert "0 bytes" in str(exc_info.value)


def test_resolver_hash_mismatch_fail_closed(sentinel_fixture):
    """Cryptographic hash mismatch must fail closed immediately."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    with pytest.raises(SentinelAudioResolutionError) as exc_info:
        resolver.resolve("sentinel_01_01_03", verify_hash=True)
    assert "FAIL-CLOSED" in str(exc_info.value)
    assert "Cryptographic integrity failure" in str(exc_info.value)


def test_resolver_no_fuzzy_or_dir_scan(sentinel_fixture):
    """Resolver must never search arbitrary directories or substitute similar filenames."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    # Similar name that exists in directory but is not registered
    arbitrary_file = sentinel_fixture["root"] / "audio" / "sentinel_01_01_99.mp3"
    arbitrary_file.write_bytes(b"ARBITRARY_FILE")

    with pytest.raises(SentinelAudioResolutionError):
        resolver.resolve("sentinel_01_01_99")


def test_resolver_hash_caching(sentinel_fixture):
    """Resolver caches verified hashes to avoid redundant disk I/O."""
    resolver = SentinelAudioResolver(
        manifest_path=sentinel_fixture["manifest_path"],
        project_root=sentinel_fixture["root"],
    )
    # First call computes hash
    p1 = resolver.resolve("sentinel_01_01_01", verify_hash=True)
    assert len(resolver._verified_hash_cache) == 1

    # Second call uses cache
    p2 = resolver.resolve("sentinel_01_01_01", verify_hash=True)
    assert p1 == p2
