"""
Whisper and Distil-Whisper sequence-to-sequence model adapter.
Supports openai/whisper-tiny, openai/whisper-base, openai/whisper-small, distil-whisper/distil-small.en.
"""

from __future__ import annotations
import torch
import numpy as np
import warnings
import transformers

# Suppress HuggingFace generation warnings (e.g. max_new_tokens vs max_length precedence)
transformers.logging.set_verbosity_error()
warnings.filterwarnings("ignore", message=".*Both `max_new_tokens`.*")

from transformers import WhisperForConditionalGeneration, WhisperProcessor
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.data.acoustic import load_and_resample_audio


class WhisperModel(BaseASRModel):
    """Secondary Track B Backbone & Distilled Whisper architectures."""

    def __init__(self, model_id: str = "openai/whisper-base", device: str = "cpu"):
        super().__init__(model_id=model_id, device=device)

    def load_model(self) -> None:
        self.processor = WhisperProcessor.from_pretrained(self.model_id)
        target_dtype = torch.float32 if self.device == "cpu" else torch.float16
        self.model = WhisperForConditionalGeneration.from_pretrained(
            self.model_id,
            torch_dtype=target_dtype
        )
        if hasattr(self.model, "generation_config") and self.model.generation_config is not None:
            self.model.generation_config.max_length = None
        if self.device == "cpu":
            self.model = self.model.float()
        self.model.to(self.device)
        self.model.eval()
        self.cache_initial_state()


    def transcribe(self, audio_filepath_or_array: str | np.ndarray) -> str:
        if self.model is None or self.processor is None:
            self.load_model()

        audio, sr = load_and_resample_audio(audio_filepath_or_array, target_sr=16000)
        input_features = self.processor(
            audio, sampling_rate=16000, return_tensors="pt"
        ).input_features.to(device=self.device, dtype=self.model.dtype)

        with torch.no_grad():
            if hasattr(self.model, "generation_config") and self.model.generation_config is not None:
                self.model.generation_config.max_length = None
            is_multilingual = getattr(self.model.config, "is_multilingual", True)
            if is_multilingual and not self.model_id.endswith(".en"):
                predicted_ids = self.model.generate(
                    input_features,
                    language="english",
                    task="transcribe",
                    max_new_tokens=64
                )
            else:
                predicted_ids = self.model.generate(
                    input_features,
                    max_new_tokens=64
                )

        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        return transcription.strip()

