"""
General CTC model adapter for HuBERT, Data2Vec, and XLS-R architectures.
"""

from __future__ import annotations
import gc
import torch
import numpy as np
from transformers import AutoModelForCTC, AutoProcessor, Wav2Vec2Processor, Wav2Vec2ForCTC, HubertForCTC, Data2VecAudioForCTC
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.data.acoustic import load_and_resample_audio


class GenericCTCModel(BaseASRModel):
    """Generic CTC model wrapper for HuBERT, Data2Vec, XLS-R."""

    def __init__(self, model_id: str, device: str = "cpu"):
        super().__init__(model_id=model_id, device=device)

    def load_model(self) -> None:
        if "data2vec" in self.model_id:
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_id)
            self.model = Data2VecAudioForCTC.from_pretrained(self.model_id)
        elif "hubert" in self.model_id:
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_id)
            self.model = HubertForCTC.from_pretrained(self.model_id)
        else:
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

