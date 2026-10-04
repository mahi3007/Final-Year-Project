"""
Abstract base class for all ASR models in the research framework.
Provides standard interfaces for transcription, parameter inspection, and checkpointing.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import os
import torch
import numpy as np
from typing import Dict, Any, List, Optional
from dsg_ctta.data.acoustic import load_and_resample_audio


class BaseASRModel(ABC):
    """Unified abstract interface for ASR backbones (CTC and Seq2Seq)."""

    def __init__(self, model_id: str, device: str = "cpu"):
        self.model_id = model_id
        self.device = torch.device(device)
        self.model: Optional[torch.nn.Module] = None
        self.processor: Any = None
        self._initial_state_dict: Optional[Dict[str, torch.Tensor]] = None

    @abstractmethod
    def load_model(self) -> None:
        """Load weights and processor from HuggingFace / disk."""
        pass

    @abstractmethod
    def transcribe(self, audio_filepath_or_array: str | np.ndarray) -> str:
        """
        Transcribe single audio file or numpy array.
        Returns raw string hypothesis.
        """
        pass

    def transcribe_batch(self, audio_inputs: List[str | np.ndarray]) -> List[str]:
        """Transcribe batch of audio inputs."""
        return [self.transcribe(inp) for inp in audio_inputs]

    def save_checkpoint(self, checkpoint_path: str) -> None:
        """Save current model state dict to disk."""
        if self.model is None:
            raise RuntimeError("Cannot save uninitialized model.")
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        torch.save(self.model.state_dict(), checkpoint_path)

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Load state dict from checkpoint path."""
        if self.model is None:
            self.load_model()
        state = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(state)

    def rollback_to_initial(self) -> None:
        """Reset model parameters to pristine pre-adaptation state."""
        if self._initial_state_dict is not None and self.model is not None:
            self.model.load_state_dict(self._initial_state_dict)

    def cache_initial_state(self) -> None:
        """Cache initial weights for rapid rollback."""
        if self.model is not None:
            self._initial_state_dict = {
                k: v.clone().detach() for k, v in self.model.state_dict().items()
            }
