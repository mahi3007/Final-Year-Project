"""
Model Registry for the 6-Model Laptop-Suited Architecture Suite.
"""

from __future__ import annotations
from typing import Dict, Type, List, Optional
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.models.wav2vec2_base import Wav2Vec2BaseModel
from dsg_ctta.models.whisper_models import WhisperModel
from dsg_ctta.models.ctc_models import GenericCTCModel
from dsg_ctta.models.mock_model import MockASRModel


MODEL_CATALOG: Dict[str, Dict[str, Any]] = {
    # 1. Primary Track A Backbone
    "wav2vec2_base": {
        "model_id": "facebook/wav2vec2-base-960h",
        "family": "CTC",
        "role": "Primary Track A Backbone",
        "adapter_cls": Wav2Vec2BaseModel,
        "default_device": "cpu"
    },
    # 2. Secondary Track B Backbone
    "whisper_base": {
        "model_id": "openai/whisper-base",
        "family": "EncoderDecoder",
        "role": "Secondary Track B Backbone",
        "adapter_cls": WhisperModel,
        "default_device": "cpu"
    },
    # 3. Static Audit Model 1 (Data2Vec Multimodal SSL)
    "data2vec_base": {
        "model_id": "facebook/data2vec-audio-base-960h",
        "family": "CTC",
        "role": "Static Audit Model 1 (Multimodal SSL)",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    # 4. Static Audit Model 2 (Distilled Transformer Seq2Seq)
    "distil_whisper_small": {
        "model_id": "distil-whisper/distil-small.en",
        "family": "EncoderDecoder",
        "role": "Static Audit Model 2 (Distilled Transformer)",
        "adapter_cls": WhisperModel,
        "default_device": "cpu"
    },
    # 5. Static Audit Model 3 (Lightweight Fast Seq2Seq)
    "whisper_tiny": {
        "model_id": "openai/whisper-tiny",
        "family": "EncoderDecoder",
        "role": "Static Audit Model 3 (Lightweight Seq2Seq)",
        "adapter_cls": WhisperModel,
        "default_device": "cpu"
    },
    # 6. Static Audit Model 4 (Low-Resource Pretrained CTC)
    "wav2vec2_100h": {
        "model_id": "facebook/wav2vec2-base-100h",
        "family": "CTC",
        "role": "Static Audit Model 4 (Low-Resource CTC)",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    # Additional benchmark models
    "hubert_large": {
        "model_id": "facebook/hubert-large-ls960-ft",
        "family": "CTC",
        "role": "Self-Supervised Acoustic Cluster Encoder (CTC Fine-Tuned, 316.8M params)",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    "hubert_base": {
        "model_id": "facebook/hubert-large-ls960-ft",
        "family": "CTC",
        "role": "Self-Supervised Acoustic Cluster Encoder (CTC Fine-Tuned, 316.8M params) [Alias for hubert_large]",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    "xlsr_english": {
        "model_id": "jonatasgrosman/wav2vec2-large-xlsr-53-english",
        "family": "CTC",
        "role": "Cross-Lingual SSL CTC",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    # Stage 6.1 Expanded CTC Backbones
    "wav2vec2_large_lv60": {
        "model_id": "facebook/wav2vec2-large-960h-lv60",
        "family": "CTC",
        "role": "Larger Pretrained Wav2Vec2 (Libri-Light 60k + LibriSpeech 960h FT, 315.5M params)",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    "wav2vec2_large_robust": {
        "model_id": "facebook/wav2vec2-large-robust-ft-libri-960h",
        "family": "CTC",
        "role": "Multi-Domain Robust Pretrained Wav2Vec2 (LibriSpeech 960h FT, 315.5M params)",
        "adapter_cls": GenericCTCModel,
        "default_device": "cpu"
    },
    "mock_asr": {
        "model_id": "mock-asr-v1",
        "family": "Mock",
        "role": "Deterministic Test / CI Backbone",
        "adapter_cls": MockASRModel,
        "default_device": "cpu"
    }
}


def get_available_model_names() -> List[str]:
    """Return list of supported model keys."""
    return list(MODEL_CATALOG.keys())


def create_asr_model(name: str, device: str = "cpu") -> BaseASRModel:
    """Factory function to instantiate an ASR model by catalog key."""
    if name not in MODEL_CATALOG:
        raise KeyError(f"Unknown model name '{name}'. Available: {get_available_model_names()}")

    entry = MODEL_CATALOG[name]
    cls = entry["adapter_cls"]
    model_id = entry["model_id"]

    if cls == GenericCTCModel:
        return GenericCTCModel(model_id=model_id, device=device)
    elif cls == WhisperModel:
        return WhisperModel(model_id=model_id, device=device)
    elif cls == Wav2Vec2BaseModel:
        return Wav2Vec2BaseModel(model_id=model_id, device=device)
    elif cls == MockASRModel:
        return MockASRModel(model_id=model_id)
    else:
        return cls(model_id=model_id, device=device)
