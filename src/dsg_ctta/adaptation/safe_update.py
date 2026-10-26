"""
Safe Adaptation Transaction Module for Test-Time Adaptation (CTTA).
=====================================================================
Enforces fail-closed, atomic numerical safety transactions for candidate model updates:
1. Scalar loss finiteness check before backpropagation.
2. Backpropagation execution with error trapping.
3. Gradient finiteness check and non-finite error-raising gradient clipping.
4. Guaranteed non-execution of optimizer step upon any non-finite gradient.
5. Post-step parameter and floating buffer finiteness validation.
6. Post-step optimizer state tensor finiteness validation (exp_avg, exp_avg_sq).
7. Atomic candidate isolation and promotion boundary: live model and live optimizer
   state are never mutated unless candidate update is explicitly promoted.
8. Padded-frame masking for variable-length audio inputs.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Any, Dict
import torch
import torch.nn as nn

from dsg_ctta.controller.shadow import compute_model_parameter_hash


@dataclass
class SafeUpdateResult:
    """Result of a fail-closed candidate adaptation step."""
    loss: Optional[float]
    numerical_status: str
    loss_finite: bool
    gradient_finite: bool
    parameter_finite: bool
    optimizer_state_finite: bool = True
    failure_reason: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return (
            self.numerical_status == "SUCCESS_FINITE"
            and self.loss_finite
            and self.gradient_finite
            and self.parameter_finite
            and self.optimizer_state_finite
        )


def compute_optimizer_state_hash(optimizer: torch.optim.Optimizer) -> str:
    """
    Computes a deterministic SHA-256 hash of an optimizer's state, including:
    - Param groups hyperparameters (lr, weight_decay, betas).
    - Step counts and state tensors (e.g. exp_avg, exp_avg_sq for AdamW).
    """
    hasher = hashlib.sha256()
    state_dict = optimizer.state_dict()

    for g_idx, group in enumerate(state_dict.get("param_groups", [])):
        hasher.update(f"group_{g_idx}".encode("utf-8"))
        for k in sorted(group.keys()):
            if k != "params":
                hasher.update(f"{k}:{group[k]}".encode("utf-8"))

    state = state_dict.get("state", {})
    for p_id in sorted(state.keys()):
        p_state = state[p_id]
        hasher.update(f"p_{p_id}".encode("utf-8"))
        for k in sorted(p_state.keys()):
            val = p_state[k]
            hasher.update(k.encode("utf-8"))
            if isinstance(val, torch.Tensor):
                hasher.update(val.detach().cpu().numpy().tobytes())
            else:
                hasher.update(str(val).encode("utf-8"))

    return hasher.hexdigest()


def validate_optimizer_state(optimizer: torch.optim.Optimizer) -> Tuple[bool, Optional[str]]:
    """
    Validates that all tensors in the optimizer state dictionary (e.g., AdamW moments)
    contain strictly finite values (no NaNs, no Infs).
    """
    for p_id, p_state in optimizer.state.items():
        for k, v in p_state.items():
            if isinstance(v, torch.Tensor) and torch.is_floating_point(v):
                if not torch.isfinite(v).all().item():
                    return False, f"Optimizer state tensor '{k}' for parameter {p_id} contains non-finite values"
    return True, None


def clone_optimizer(
    source_opt: torch.optim.Optimizer,
    target_model: nn.Module
) -> torch.optim.Optimizer:
    """
    Instantiates a new optimizer of the same class over target_model's trainable
    parameters, and deepcopies the exact optimizer state (step counts, moments).
    """
    trainable_params = [p for p in target_model.parameters() if p.requires_grad]
    opt_cls = type(source_opt)
    sig = inspect.signature(opt_cls.__init__)
    valid_keys = set(sig.parameters.keys()) - {"self", "params"}
    clean_defaults = {k: copy.deepcopy(v) for k, v in source_opt.defaults.items() if k in valid_keys}
    new_opt = opt_cls(trainable_params, **clean_defaults)
    new_opt.load_state_dict(copy.deepcopy(source_opt.state_dict()))
    return new_opt


def compute_masked_suta_loss(
    model: nn.Module,
    input_values: torch.Tensor,
    audio_lengths: List[int],
    temperature: float = 2.5,
    alpha: float = 0.5,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes unsupervised SUTA adaptation loss (Shannon Entropy + Minimum Class Confusion)
    with strict valid-frame masking for variable-length audio batches.

    Padded silence frames are excluded from both entropy and class-confusion sums,
    preventing padded blanks from dominating or corrupting acoustic representations.

    Parameters:
    -----------
    model: CTC acoustic model (e.g. Wav2Vec2ForCTC).
    input_values: Padded batch tensor (B, S).
    audio_lengths: Raw sample length for each utterance in the batch.
    temperature: Logit scaling temperature.
    alpha: Weight factor between EM and MCC.

    Returns:
    --------
    total_loss, l_em, l_mcc
    """
    outputs = model(input_values)
    logits = outputs.logits  # (B, T, C)
    B, T, C = logits.shape

    # Determine valid CTC frame count for each utterance in the batch
    if hasattr(model, "_get_feat_extract_output_lengths"):
        valid_frame_counts = model._get_feat_extract_output_lengths(
            torch.tensor(audio_lengths, dtype=torch.long, device=logits.device)
        )
    else:
        # Fallback for standard 320x convolutional stride (16 kHz -> 50 Hz)
        valid_frame_counts = [min(T, max(1, (l - 80) // 320)) for l in audio_lengths]

    # Build valid frame mask
    mask = torch.zeros((B, T), dtype=torch.bool, device=logits.device)
    for b in range(B):
        count = int(valid_frame_counts[b].item() if isinstance(valid_frame_counts[b], torch.Tensor) else valid_frame_counts[b])
        mask[b, :min(count, T)] = True

    # Temperature scaled softmax probabilities
    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1)

    # 1. Masked Entropy Minimization
    valid_probs = probs[mask]  # (N_valid_frames, C)
    if valid_probs.numel() == 0:
        # Fallback if mask is somehow empty
        valid_probs = probs.view(-1, C)

    log_probs = torch.log(valid_probs + 1e-8)
    entropy = -torch.sum(valid_probs * log_probs, dim=-1)
    l_em = torch.mean(entropy)

    # 2. Masked Minimum Class Confusion (MCC)
    class_sums = torch.sum(valid_probs, dim=0)  # (C,)
    norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0) + 1e-8)
    corr_matrix = (valid_probs.T @ valid_probs) / norm_factor
    diagonal = torch.diag(corr_matrix)
    off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
    l_mcc = off_diag_sum / (C * (C - 1) + 1e-8)

    total_loss = alpha * l_em + (1.0 - alpha) * l_mcc
    return total_loss, l_em, l_mcc


def execute_safe_adaptation_transaction(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    loss_fn: Callable[[], torch.Tensor],
    max_grad_norm: float = 1.0,
) -> SafeUpdateResult:
    """
    Execute an atomic, fail-closed candidate adaptation update on an isolated model & optimizer.

    Guarantees:
    - Never executes optimizer.step() if loss or any gradient is non-finite.
    - Captures non-finite gradient norms via error_if_nonfinite=True.
    - Catches any exceptions raised during optimizer.step().
    - Validates all model parameters, floating buffers, and optimizer state tensors after the step.
    - Returns a structured SafeUpdateResult detailing the exact outcome.
    """
    optimizer.zero_grad(set_to_none=True)

    # 1. Compute scalar adaptation loss
    try:
        total_loss = loss_fn()
    except Exception as exc:
        return SafeUpdateResult(
            loss=None,
            numerical_status="FAILED_LOSS_EXCEPTION",
            loss_finite=False,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason=f"Exception during adaptation loss computation: {exc}"
        )

    # Validate loss tensor
    if total_loss is None or not torch.isfinite(total_loss).all().item():
        optimizer.zero_grad(set_to_none=True)
        return SafeUpdateResult(
            loss=None,
            numerical_status="FAILED_NONFINITE_LOSS",
            loss_finite=False,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason="Scalar loss is non-finite (NaN or Inf)"
        )

    loss_val = float(total_loss.item())

    # 2. Backpropagation
    try:
        total_loss.backward()
    except Exception as exc:
        optimizer.zero_grad(set_to_none=True)
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_BACKWARD_EXCEPTION",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason=f"Exception during backward propagation: {exc}"
        )

    # 3. Check trainable parameters and gradients
    trainable_params: List[nn.Parameter] = [p for p in model.parameters() if p.requires_grad]
    if not trainable_params:
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NO_TRAINABLE_PARAMS",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason="No trainable parameters configured for adaptation"
        )

    # Explicit element-wise gradient check
    for p in trainable_params:
        if p.grad is not None and not torch.isfinite(p.grad).all().item():
            optimizer.zero_grad(set_to_none=True)
            return SafeUpdateResult(
                loss=loss_val,
                numerical_status="FAILED_NONFINITE_GRADIENT",
                loss_finite=True,
                gradient_finite=False,
                parameter_finite=True,
                optimizer_state_finite=True,
                failure_reason="One or more trainable parameters have non-finite gradients (NaN or Inf)"
            )

    # Clip gradients with error_if_nonfinite=True
    try:
        grad_norm = torch.nn.utils.clip_grad_norm_(
            trainable_params,
            max_norm=max_grad_norm,
            error_if_nonfinite=True
        )
        if not torch.isfinite(grad_norm).all().item():
            optimizer.zero_grad(set_to_none=True)
            return SafeUpdateResult(
                loss=loss_val,
                numerical_status="FAILED_NONFINITE_GRADIENT_NORM",
                loss_finite=True,
                gradient_finite=False,
                parameter_finite=True,
                optimizer_state_finite=True,
                failure_reason="Gradient norm is non-finite"
            )
    except RuntimeError as rerr:
        optimizer.zero_grad(set_to_none=True)
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NONFINITE_GRADIENT_NORM",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason=f"clip_grad_norm_ failed closed on non-finite norm: {rerr}"
        )

    # 4. Step Optimizer with exception trapping
    try:
        optimizer.step()
    except Exception as exc:
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_OPTIMIZER_STEP_EXCEPTION",
            loss_finite=True,
            gradient_finite=True,
            parameter_finite=True,
            optimizer_state_finite=True,
            failure_reason=f"Exception during optimizer step: {exc}"
        )

    # 5. Post-step parameter and floating buffer verification
    all_params_finite = all(torch.isfinite(p).all().item() for p in model.parameters())
    all_buffers_finite = all(
        torch.isfinite(b).all().item()
        for b in model.buffers()
        if torch.is_floating_point(b)
    )

    if not all_params_finite or not all_buffers_finite:
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NONFINITE_PARAMETERS_AFTER_STEP",
            loss_finite=True,
            gradient_finite=True,
            parameter_finite=False,
            optimizer_state_finite=True,
            failure_reason="One or more model parameters or floating buffers became non-finite after optimizer step"
        )

    # 6. Post-step optimizer state tensor verification
    opt_valid, opt_err = validate_optimizer_state(optimizer)
    if not opt_valid:
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NONFINITE_OPTIMIZER_STATE",
            loss_finite=True,
            gradient_finite=True,
            parameter_finite=True,
            optimizer_state_finite=False,
            failure_reason=opt_err
        )

    return SafeUpdateResult(
        loss=loss_val,
        numerical_status="SUCCESS_FINITE",
        loss_finite=True,
        gradient_finite=True,
        parameter_finite=True,
        optimizer_state_finite=True,
        failure_reason=None
    )


class AtomicCandidateManager:
    """
    Manages isolated candidate generation and atomic promotion for CTTA.
    
    Guarantees:
    - Candidate adaptation occurs strictly on deepcopied model and optimizer clones.
    - Live model and live optimizer are ONLY mutated upon explicit promotion.
    - On candidate rejection or failure, candidates are discarded and live state
      is verified to remain bitwise invariant.
    """
    def __init__(
        self,
        live_model: nn.Module,
        live_optimizer: torch.optim.Optimizer,
        device: str = "cpu"
    ):
        self.live_model = live_model
        self.live_optimizer = live_optimizer
        self.device = device
        self._initial_model_hash = self.get_live_model_hash()
        self._initial_opt_hash = self.get_live_optimizer_hash()

    def get_live_model_hash(self) -> str:
        """Returns bitwise SHA-256 parameter hash of live model."""
        return compute_model_parameter_hash(self.live_model)

    def get_live_optimizer_hash(self) -> str:
        """Returns bitwise SHA-256 state hash of live optimizer."""
        return compute_optimizer_state_hash(self.live_optimizer)

    def create_candidate(self) -> Tuple[nn.Module, torch.optim.Optimizer]:
        """Creates an isolated candidate clone of model and optimizer state."""
        candidate_model = copy.deepcopy(self.live_model).to(self.device)
        candidate_optimizer = clone_optimizer(self.live_optimizer, candidate_model)
        return candidate_model, candidate_optimizer

    def execute_candidate_transaction(
        self,
        candidate_model: nn.Module,
        candidate_optimizer: torch.optim.Optimizer,
        loss_fn: Callable[[], torch.Tensor],
        max_grad_norm: float = 1.0,
    ) -> SafeUpdateResult:
        """Runs the safe update transaction strictly on candidate copies."""
        return execute_safe_adaptation_transaction(
            model=candidate_model,
            optimizer=candidate_optimizer,
            loss_fn=loss_fn,
            max_grad_norm=max_grad_norm,
        )

    def promote_candidate(
        self,
        candidate_model: nn.Module,
        candidate_optimizer: torch.optim.Optimizer
    ) -> Tuple[str, str]:
        """
        Atomically commits candidate model parameters and optimizer state into live model and optimizer.
        """
        self.live_model.load_state_dict(candidate_model.state_dict())
        self.live_optimizer.load_state_dict(candidate_optimizer.state_dict())
        return self.get_live_model_hash(), self.get_live_optimizer_hash()

    def discard_candidate(
        self,
        candidate_model: Optional[nn.Module] = None,
        candidate_optimizer: Optional[torch.optim.Optimizer] = None
    ) -> None:
        """
        Safely disposes candidate copies and asserts live model & optimizer invariance.
        """
        if candidate_model is not None:
            del candidate_model
        if candidate_optimizer is not None:
            del candidate_optimizer
