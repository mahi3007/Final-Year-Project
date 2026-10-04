from __future__ import annotations
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class ProvenanceInfo(BaseModel):
    """Tracks full origin and processing history for research reproducibility."""
    source_dataset: str
    dataset_release: str = "v1.0"
    ingestion_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    normalization_version: str = "v1.0.0-canonical"
    protocol_version: str = "v1.0.0-canonical"
    extra: Dict[str, Any] = Field(default_factory=dict)


class UtteranceMetadata(BaseModel):
    """Canonical schema for a single speech recording in the research pipeline."""
    utterance_id: str
    speaker_id: str
    group_id: str
    group_type: str = Field(
        ...,
        description="Type of group variable: 'native_language', 'regional_accent', 'native_region', 'dialect', or 'geographic_state'."
    )
    audio_filepath: str
    audio_sha256: str = ""
    sampling_rate_hz: int = 16000
    duration_seconds: float
    snr_db: Optional[float] = None
    speech_rate_wpm: Optional[float] = None
    device_id: Optional[str] = "unknown_device"
    reference_raw: str
    reference_normalized: str = ""
    reference_word_count: int = 0
    reference_char_count: int = 0
    partition: Optional[str] = None  # 'development', 'calibration', 'sentinel_candidates', 'final_test', 'external_validation'
    provenance: ProvenanceInfo

    @field_validator("group_type")
    @classmethod
    def validate_group_type(cls, v: str) -> str:
        valid_types = {
            "native_language",
            "regional_accent",
            "native_region",
            "dialect",
            "geographic_state",
            "accent"
        }
        if v.lower() not in valid_types:
            raise ValueError(f"group_type '{v}' must be one of {valid_types}")
        return v.lower()


class PartitionManifest(BaseModel):
    """A collection of utterances belonging to a single partition."""
    partition_name: str
    num_utterances: int
    num_speakers: int
    speaker_ids: List[str]
    group_ids: List[str]
    utterances: List[UtteranceMetadata]
    manifest_sha256: str = ""


class DatasetManifest(BaseModel):
    """Full dataset manifest containing all partitions and metadata."""
    dataset_name: str
    protocol_version: str = "v1.0.0-canonical"
    creation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    partitions: Dict[str, PartitionManifest]
    total_utterances: int = 0
    total_speakers: int = 0
    total_duration_hours: float = 0.0
    group_distribution: Dict[str, int] = Field(default_factory=dict)
    speaker_group_mapping: Dict[str, str] = Field(default_factory=dict)
    manifest_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.dataset_name}:{self.total_utterances}:{sorted(self.partitions.keys())}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
