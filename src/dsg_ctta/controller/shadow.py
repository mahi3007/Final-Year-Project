"""
Stage 5A DSG Controller: Shadow Candidate Architecture and State Transitions.
=============================================================================
Enforces live model immutability during test-time adaptation and implements
fail-safe candidate state transitions per ADR-005:
If ACCEPT: theta_(t+1) = candidate
If REJECT: theta_(t+1) = theta_t (discard candidate, preserve live model)
NEVER rolls back to theta_(t-1).
"""

from __future__ import annotations
import copy
import hashlib
from typing import Any, Dict, Optional
import torch

from dsg_ctta.controller.types import GateDecision


def compute_model_parameter_hash(model: Any) -> str:
    """
    Compute a deterministic SHA-256 hash over all trainable and non-trainable
    parameters of a PyTorch model or state dict.
    """
    hasher = hashlib.sha256()

    if isinstance(model, dict):
        state_dict = model
    elif hasattr(model, "model") and hasattr(model.model, "state_dict") and model.model is not None:
        state_dict = model.model.state_dict()
    elif hasattr(model, "state_dict"):
        state_dict = model.state_dict()
    elif hasattr(model, "parameters"):
        # Custom mock model or object
        params = list(model.parameters())
        for p in params:
            if hasattr(p, "detach"):
                hasher.update(p.detach().cpu().numpy().tobytes())
            else:
                hasher.update(str(p).encode("utf-8"))
        return hasher.hexdigest()
    else:
        # Fallback for generic object
        hasher.update(str(model).encode("utf-8"))
        return hasher.hexdigest()

    for k in sorted(state_dict.keys()):
        tensor = state_dict[k]
        hasher.update(k.encode("utf-8"))
        if hasattr(tensor, "detach"):
            hasher.update(tensor.detach().cpu().numpy().tobytes())
        else:
            hasher.update(str(tensor).encode("utf-8"))

    return hasher.hexdigest()


class ShadowCandidateManager:
    """
    Manages the lifecycle of live models theta_t and shadow candidate clones theta'.
    Guarantees that theta_t is never modified in-place by adaptation or gate evaluation.
    """

    @staticmethod
    def create_candidate_clone(live_model: Any) -> Any:
        """
        Deep-copy the live model to create an isolated shadow clone for adaptation.
        The live model remains pristine and immutable.
        """
        if hasattr(live_model, "clone"):
            return live_model.clone()
        return copy.deepcopy(live_model)

    @staticmethod
    def apply_transition(
        live_model: Any,
        candidate_model: Any,
        decision: GateDecision,
        pre_adaptation_hash: Optional[str] = None,
    ) -> Any:
        """
        Execute the ADR-005 state transition:
        - If decision.accept is True: return candidate_model (theta_{t+1} = theta')
        - If decision.accept is False: return live_model (theta_{t+1} = theta_t)

        Asserts that if REJECT, the retained model is bit-for-bit identical
        to the pre-adaptation live model.
        """
        if pre_adaptation_hash is not None:
            current_live_hash = compute_model_parameter_hash(live_model)
            assert current_live_hash == pre_adaptation_hash, (
                f"CRITICAL IMMUTABILITY BREACH: Live model was mutated during adaptation! "
                f"Expected hash {pre_adaptation_hash}, got {current_live_hash}"
            )

        if decision.accept:
            # Candidate accepted -> promotes to live model for next step
            return candidate_model
        else:
            # Candidate rejected -> discard candidate, retain current live model theta_t
            # (Note: candidate_model is unreferenced and garbage-collected; theta_t remains unchanged)
            return live_model
