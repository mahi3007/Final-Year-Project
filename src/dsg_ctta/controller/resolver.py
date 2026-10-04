"""
Stage 5D DSG Controller: Canonical Sentinel Audio Resolver.
===========================================================
Strict, cryptographic audio path resolution for the frozen Sentinel Panel.

Contract Requirements:
1. Resolve audio strictly through the frozen sentinel audio manifest/inventory.
2. Prefer cryptographic/audio inventory identifiers (sentinel_id) over ad-hoc filenames.
3. Verify the resolved physical audio file exists on disk and is non-empty.
4. Verify SHA-256 checksum matches the manifest before permitting evaluation.
5. Never silently substitute another recording.
6. Never perform fuzzy or glob searches in arbitrary directories.
7. Fail closed immediately if manifest, file path, or hash disagree.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from dsg_ctta.controller.exceptions import FailClosedException


class SentinelAudioResolutionError(FailClosedException):
    """Raised when sentinel audio fails canonical manifest or hash verification."""
    pass


class SentinelAudioResolver:
    """
    Canonical resolver ensuring audio loaded during sentinel evaluation strictly
    originates from the frozen sentinel panel manifest and matches cryptographic digests.
    """

    def __init__(
        self,
        manifest_path: Optional[Union[str, Path]] = None,
        inventory_path: Optional[Union[str, Path]] = None,
        project_root: Optional[Union[str, Path]] = None,
    ):
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parent.parent.parent.parent
        )

        # Default paths if not provided
        self.manifest_path = (
            Path(manifest_path).resolve()
            if manifest_path is not None
            else self.project_root / "datasets" / "splits" / "stage5_sentinel_audio_manifest.json"
        )
        self.inventory_path = (
            Path(inventory_path).resolve()
            if inventory_path is not None
            else self.project_root / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"
        )

        self._registry_by_id: Dict[str, Dict[str, Any]] = {}
        self._registry_by_src: Dict[str, Dict[str, Any]] = {}
        self._verified_hash_cache: Dict[str, str] = {}  # local_path -> sha256

        self._load_registry()

    def _load_registry(self):
        """Loads canonical mapping from manifest or inventory JSON."""
        loaded = False

        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                clips = data.get("clips", {})
                for sentinel_id, entry in clips.items():
                    entry_record = dict(entry)
                    entry_record["sentinel_id"] = sentinel_id
                    self._registry_by_id[sentinel_id] = entry_record
                    src = entry.get("source_path")
                    if src:
                        self._registry_by_src[Path(src).name] = entry_record
                loaded = True
            except Exception as exc:
                raise SentinelAudioResolutionError(
                    f"Corrupted or unreadable sentinel manifest: {self.manifest_path} ({exc})"
                ) from exc

        if not loaded and self.inventory_path.exists():
            try:
                with open(self.inventory_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                for item in items:
                    sentinel_id = item.get("sentinel_id")
                    if sentinel_id:
                        self._registry_by_id[sentinel_id] = dict(item)
                    src = item.get("source_path")
                    if src:
                        self._registry_by_src[Path(src).name] = dict(item)
                loaded = True
            except Exception as exc:
                raise SentinelAudioResolutionError(
                    f"Corrupted or unreadable sentinel inventory: {self.inventory_path} ({exc})"
                ) from exc

        if not loaded:
            # Manifest not yet generated
            pass

    @property
    def is_loaded(self) -> bool:
        return len(self._registry_by_id) > 0

    @property
    def total_clips(self) -> int:
        return len(self._registry_by_id)

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def resolve(
        self,
        clip_or_record: Union[str, Dict[str, Any], Any],
        verify_hash: bool = True,
    ) -> Path:
        """
        Resolves an utterance identifier or metadata record to a cryptographically
        verified local audio file.

        Args:
            clip_or_record: sentinel_id string, source filename string, or dict/object.
            verify_hash: If True, validates SHA-256 against manifest.

        Returns:
            Resolved absolute Path to audio file.

        Raises:
            SentinelAudioResolutionError: If file is missing, empty, or hash mismatches.
        """
        if not self.is_loaded:
            # Re-attempt loading in case it was written asynchronously
            self._load_registry()
            if not self.is_loaded:
                raise SentinelAudioResolutionError(
                    f"Sentinel audio registry empty: neither {self.manifest_path.name} nor "
                    f"{self.inventory_path.name} could be loaded."
                )

        # 1. Identify canonical key
        canonical_key = None
        source_key = None

        if isinstance(clip_or_record, str):
            clean_str = clip_or_record.strip()
            if clean_str in self._registry_by_id:
                canonical_key = clean_str
            elif Path(clean_str).name in self._registry_by_src:
                source_key = Path(clean_str).name
            else:
                canonical_key = clean_str
        elif isinstance(clip_or_record, dict):
            canonical_key = clip_or_record.get("sentinel_id") or clip_or_record.get("utterance_id")
            raw_audio = clip_or_record.get("audio_filepath") or clip_or_record.get("audio_path")
            if raw_audio:
                source_key = Path(str(raw_audio)).name
        else:
            canonical_key = getattr(clip_or_record, "sentinel_id", getattr(clip_or_record, "utterance_id", None))
            raw_audio = getattr(clip_or_record, "audio_filepath", getattr(clip_or_record, "audio_path", None))
            if raw_audio:
                source_key = Path(str(raw_audio)).name

        # 2. Lookup in registry (strictly no directory scanning or fuzzy matching)
        entry = None
        if canonical_key and canonical_key in self._registry_by_id:
            entry = self._registry_by_id[canonical_key]
        elif source_key and source_key in self._registry_by_src:
            entry = self._registry_by_src[source_key]

        if entry is None:
            raise SentinelAudioResolutionError(
                f"FAIL-CLOSED: Unregistered sentinel clip identifier: '{canonical_key or source_key}'. "
                "Ad-hoc file substitution and arbitrary directory search are strictly forbidden."
            )

        # 3. Resolve local path
        local_rel = entry.get("local_path")
        if not local_rel:
            raise SentinelAudioResolutionError(
                f"FAIL-CLOSED: Manifest entry for '{entry.get('sentinel_id')}' lacks 'local_path'."
            )

        local_path = (self.project_root / local_rel).resolve()

        # 4. Verify file exists and is non-empty
        if not local_path.exists():
            raise SentinelAudioResolutionError(
                f"FAIL-CLOSED: Sentinel audio file missing on disk: {local_path} "
                f"(expected for sentinel_id '{entry.get('sentinel_id')}')."
            )

        if local_path.stat().st_size == 0:
            raise SentinelAudioResolutionError(
                f"FAIL-CLOSED: Sentinel audio file is 0 bytes: {local_path}."
            )

        # 5. Cryptographic hash verification
        if verify_hash:
            expected_hash = entry.get("audio_hash")
            if not expected_hash:
                raise SentinelAudioResolutionError(
                    f"FAIL-CLOSED: Manifest entry for '{entry.get('sentinel_id')}' missing 'audio_hash'."
                )

            # Check cached verification (keyed by path + mtime + size)
            stat = local_path.stat()
            cache_key = f"{str(local_path)}:{stat.st_mtime_ns}:{stat.st_size}"

            if cache_key in self._verified_hash_cache:
                computed_hash = self._verified_hash_cache[cache_key]
            else:
                computed_hash = self.compute_sha256(local_path)
                self._verified_hash_cache[cache_key] = computed_hash

            if computed_hash.lower() != expected_hash.lower():
                raise SentinelAudioResolutionError(
                    f"FAIL-CLOSED: Cryptographic integrity failure for sentinel clip '{entry.get('sentinel_id')}': "
                    f"Expected SHA-256 {expected_hash}, computed {computed_hash}. File may be corrupted or tampered."
                )

        return local_path
