"""
Wav2Vec2-base CTC implementation (Primary Track A Backbone).
facebook/wav2vec2-base-960h (~95M parameters).
"""

from __future__ import annotations
import torch
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.data.acoustic import load_and_resample_audio


class Wav2Vec2BaseModel(BaseASRModel):
    """Primary Track A Backbone: facebook/wav2vec2-base-960h."""

    def __init__(self, model_id: str = "facebook/wav2vec2-base-960h", device: str = "cpu"):
        super().__init__(model_id=model_id, device=device)

    def load_model(self) -> None:
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_id)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()
        self.cache_initial_state()

    def transcribe(self, audio_filepath_or_array: str | np.ndarray) -> str:
        if self.model is None or self.processor is None:
            self.load_model()

        audio, sr = load_and_resample_audio(audio_filepath_or_array, target_sr=16000)
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            logits = self.model(input_values).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription.strip()
