"""
Deterministic Mock ASR model for unit tests, offline validity verification, and rapid CI/CD runs.
Generates controlled predictions with configurable synthetic group error rates.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Optional
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.data.normalization import TextNormalizer


class MockASRModel(BaseASRModel):
    """
    Mock ASR model that produces controlled hypotheses from audio or references
    for deterministic pipeline validation.
    """

    def __init__(
        self,
        model_id: str = "mock-asr-v1",
        base_error_rate: float = 0.15,
        group_error_offsets: Optional[Dict[str, float]] = None,
        seed: int = 42
    ):
        super().__init__(model_id=model_id, device="cpu")
        self.base_error_rate = base_error_rate
        self.group_error_offsets = group_error_offsets or {
            "Region_North": -0.05,
            "Region_South": +0.10,
            "Region_East": 0.00,
            "Region_West": +0.05
        }
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.known_references: Dict[str, str] = {}

    def load_model(self) -> None:
        self.cache_initial_state()

    def register_reference(self, audio_filepath: str, reference: str) -> None:
        """Register reference text for simulated transcription."""
        self.known_references[audio_filepath] = reference

    def transcribe(self, audio_filepath_or_array: str | np.ndarray) -> str:
        """Generate simulated hypothesis with controlled errors."""
        ref = ""
        if isinstance(audio_filepath_or_array, str) and audio_filepath_or_array in self.known_references:
            ref = self.known_references[audio_filepath_or_array]
        else:
            # Fallback default prompt
            ref = "AUTHOR OF THE DANGER TRAIL PHILIP STEEL ETC"

        norm_ref = TextNormalizer.normalize(ref)
        words = norm_ref.split()
        if not words:
            return ""

        # Introduce deterministic substitutions based on hash of audio/filepath
        simulated_hyp_words = []
        for i, w in enumerate(words):
            val = (hash(w) + i + self.seed) % 100
            if val < 15:
                # Substitute word
                simulated_hyp_words.append(w + "ED" if len(w) > 3 else "THE")
            elif val > 95:
                # Omit word (deletion)
                continue
            else:
                simulated_hyp_words.append(w)

        return " ".join(simulated_hyp_words)
