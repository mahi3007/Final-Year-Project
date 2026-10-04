"""
Abstract Base Adapter for Test-Time Adaptation (CTTA).
Enforces the online/offline boundary: adaptation methods may only consume UnlabeledAudioBatch.
"""

from __future__ import annotations
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import torch

from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch


class AdaptationStepResult(BaseModel):
    """Result of an online adaptation step on a single window B_t."""
    batch_idx: int
    method_id: str
    theta_before_hash: str
    theta_after_hash: str
    updated: bool
    reset_occurred: bool = False
    adaptation_time_seconds: float = 0.0
    loss_history: List[float] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class BaseTestTimeAdapter(ABC):
    """
    Abstract contract for all CTTA adaptation algorithms.
    Guarantees strict label isolation: adapt() accepts ONLY UnlabeledAudioBatch.
    """

    def __init__(
        self,
        asr_model: BaseASRModel,
        method_id: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.asr_model = asr_model
        self.method_id = method_id
        self.config = config or {}
        self.step_count = 0
        self.total_adaptation_time = 0.0

    def compute_model_hash(self) -> str:
        """
        Compute deterministic SHA-256 hash of current trainable / active model parameters.
        Used to verify exact model state transitions (theta_t -> theta_(t+1)).
        """
        if self.asr_model.model is None:
            return "uninitialized"
        hasher = hashlib.sha256()
        with torch.no_grad():
            for name, param in sorted(self.asr_model.model.named_parameters()):
                if param.requires_grad:
                    hasher.update(name.encode("utf-8"))
                    hasher.update(param.data.cpu().numpy().tobytes())
        return hasher.hexdigest()[:16]

    @abstractmethod
    def adapt(self, batch: UnlabeledAudioBatch) -> AdaptationStepResult:
        """
        Perform unsupervised adaptation using only the unlabeled audio of window B_t.
        Returns AdaptationStepResult with provenance hashes and timing.
        """
        pass

    def reset_to_initial(self) -> None:
        """Reset the underlying ASR model to pristine pre-adaptation state theta_0."""
        self.asr_model.rollback_to_initial()
        self.step_count = 0
