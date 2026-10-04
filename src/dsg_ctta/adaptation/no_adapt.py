"""
No-Adaptation Control Adapter for CTTA.
In this control condition, theta_(t+1) = theta_t = theta_0 for all t.
Used to separate stream composition dynamics from adaptation effects.
"""

from __future__ import annotations
import time
from typing import Dict, Any, Optional

from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch


class NoAdaptationAdapter(BaseTestTimeAdapter):
    """
    Control baseline where no model updates are performed.
    theta_(t+1) == theta_t == theta_0.
    """

    def __init__(
        self,
        asr_model: BaseASRModel,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(asr_model=asr_model, method_id="no_adapt", config=config)

    def adapt(self, batch: UnlabeledAudioBatch) -> AdaptationStepResult:
        """
        No-op adaptation step: parameters remain strictly identical.
        """
        start_time = time.time()
        curr_hash = self.compute_model_hash()
        self.step_count += 1
        elapsed = time.time() - start_time
        self.total_adaptation_time += elapsed

        return AdaptationStepResult(
            batch_idx=batch.batch_idx,
            method_id="no_adapt",
            theta_before_hash=curr_hash,
            theta_after_hash=curr_hash,
            updated=False,
            reset_occurred=False,
            adaptation_time_seconds=elapsed,
            loss_history=[],
            details={"description": "Identity control - no parameter updates"}
        )
