"""
Label Isolation Security Boundary.
Strictly ensures that the online adaptation process has zero access to reference transcripts,
WER/CER metrics, or offline evaluation routines.
"""

from __future__ import annotations
from typing import List, Optional
import numpy as np
from pydantic import BaseModel, Field
from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.data.acoustic import load_and_resample_audio


class UnlabeledAudioItem(BaseModel):
    """An individual unlabeled audio item passed to online adaptation."""
    utterance_id: str
    audio_filepath: str
    duration_seconds: float
    sampling_rate_hz: int = 16000
    # Note: reference_raw, reference_normalized, group_id, speaker_id are deliberately omitted!


class UnlabeledAudioBatch(BaseModel):
    """A batch/window B_t of unlabeled audio items for test-time adaptation."""
    batch_idx: int
    window_size: int
    items: List[UnlabeledAudioItem]

    def load_waveforms(self) -> List[np.ndarray]:
        """Load audio waveforms for the batch."""
        waveforms = []
        for item in self.items:
            audio, _ = load_and_resample_audio(item.audio_filepath, target_sr=16000)
            waveforms.append(audio)
        return waveforms


class LabelIsolationSanitizer:
    """Sanitizes raw metadata objects before passing them to the online adaptation runtime."""

    @staticmethod
    def sanitize_utterance(utt: UtteranceMetadata) -> UnlabeledAudioItem:
        """Strip all ground-truth labels and evaluation attributes."""
        return UnlabeledAudioItem(
            utterance_id=utt.utterance_id,
            audio_filepath=utt.audio_filepath,
            duration_seconds=utt.duration_seconds,
            sampling_rate_hz=utt.sampling_rate_hz
        )

    @staticmethod
    def sanitize_batch(utterances: List[UtteranceMetadata], batch_idx: int) -> UnlabeledAudioBatch:
        """Create a completely label-isolated batch."""
        items = [LabelIsolationSanitizer.sanitize_utterance(u) for u in utterances]
        return UnlabeledAudioBatch(
            batch_idx=batch_idx,
            window_size=len(items),
            items=items
        )


def enforce_data_access_firewall(batch: UnlabeledAudioBatch) -> None:
    """
    Automated assertion verifying that incoming batch has zero reference transcripts,
    zero group labels, zero speaker IDs, and zero offline metric fields.
    """
    for item in batch.items:
        forbidden = [
            "reference_raw", "reference_normalized", "transcript", "sentence",
            "group_id", "stage5_accent_group", "speaker_id", "client_id",
            "wer", "cer", "substitutions", "deletions", "insertions"
        ]
        for field in forbidden:
            assert not hasattr(item, field), f"FIREWALL BREACH: Online item contains forbidden field '{field}'!"

