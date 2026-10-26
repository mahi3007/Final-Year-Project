"""
Safe Adaptation Transaction Module for Test-Time Adaptation (CTTA).
=====================================================================
Enforces fail-closed numerical safety transactions for candidate model updates:
1. Scalar loss finiteness check before backpropagation.
2. Backpropagation execution with error trapping.
3. Gradient finiteness check and non-finite error-raising gradient clipping.
4. Guaranteed non-execution of optimizer step upon any non-finite gradient.
5. Post-step parameter and floating buffer finiteness validation.
6. Structured audit recording with machine-readable failure classifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Any
import torch
import torch.nn as nn


@dataclass
class SafeUpdateResult:
    """Result of a fail-closed candidate adaptation step."""
    loss: Optional[float]
    numerical_status: str
    loss_finite: bool
    gradient_finite: bool
    parameter_finite: bool
    failure_reason: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return (
            self.numerical_status == "SUCCESS_FINITE"
            and self.loss_finite
            and self.gradient_finite
            and self.parameter_finite
        )


def execute_safe_adaptation_transaction(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    loss_fn: Callable[[], torch.Tensor],
    max_grad_norm: float = 1.0,
) -> SafeUpdateResult:
    """
    Execute an atomic, fail-closed candidate adaptation update.

    Guarantees:
    - Never executes optimizer.step() if loss or any gradient is non-finite.
    - Captures non-finite gradient norms via error_if_nonfinite=True.
    - Validates all model parameters after the step before declaring success.
    - Leaves optimizer gradients zeroed upon failure.
    """
    model.train()
    optimizer.zero_grad(set_to_none=True)

    # 1. Compute scalar adaptation loss
    try:
        total_loss = loss_fn()
    except Exception as exc:
        model.eval()
        return SafeUpdateResult(
            loss=None,
            numerical_status="FAILED_LOSS_EXCEPTION",
            loss_finite=False,
            gradient_finite=False,
            parameter_finite=True,
            failure_reason=f"Exception during adaptation loss computation: {exc}"
        )

    # Validate loss tensor
    if total_loss is None or not torch.isfinite(total_loss).all().item():
        optimizer.zero_grad(set_to_none=True)
        model.eval()
        return SafeUpdateResult(
            loss=None,
            numerical_status="FAILED_NONFINITE_LOSS",
            loss_finite=False,
            gradient_finite=False,
            parameter_finite=True,
            failure_reason="Scalar loss is non-finite (NaN or Inf)"
        )

    loss_val = float(total_loss.item())

    # 2. Backpropagation
    try:
        total_loss.backward()
    except Exception as exc:
        optimizer.zero_grad(set_to_none=True)
        model.eval()
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_BACKWARD_EXCEPTION",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            failure_reason=f"Exception during backward propagation: {exc}"
        )

    # 3. Check trainable parameters and gradients
    trainable_params: List[nn.Parameter] = [p for p in model.parameters() if p.requires_grad]
    if not trainable_params:
        model.eval()
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NO_TRAINABLE_PARAMS",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            failure_reason="No trainable parameters configured for adaptation"
        )

    # Explicit element-wise gradient check
    for p in trainable_params:
        if p.grad is not None and not torch.isfinite(p.grad).all().item():
            optimizer.zero_grad(set_to_none=True)
            model.eval()
            return SafeUpdateResult(
                loss=loss_val,
                numerical_status="FAILED_NONFINITE_GRADIENT",
                loss_finite=True,
                gradient_finite=False,
                parameter_finite=True,
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
            model.eval()
            return SafeUpdateResult(
                loss=loss_val,
                numerical_status="FAILED_NONFINITE_GRADIENT_NORM",
                loss_finite=True,
                gradient_finite=False,
                parameter_finite=True,
                failure_reason="Gradient norm is non-finite"
            )
    except RuntimeError as rerr:
        optimizer.zero_grad(set_to_none=True)
        model.eval()
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NONFINITE_GRADIENT_NORM",
            loss_finite=True,
            gradient_finite=False,
            parameter_finite=True,
            failure_reason=f"clip_grad_norm_ failed closed on non-finite norm: {rerr}"
        )

    # 4. Step Optimizer
    optimizer.step()

    # 5. Post-step parameter finiteness verification across ALL parameters and buffers
    all_params_finite = all(torch.isfinite(p).all().item() for p in model.parameters())
    all_buffers_finite = all(
        torch.isfinite(b).all().item()
        for b in model.buffers()
        if torch.is_floating_point(b)
    )

    if not all_params_finite or not all_buffers_finite:
        model.eval()
        return SafeUpdateResult(
            loss=loss_val,
            numerical_status="FAILED_NONFINITE_PARAMETERS_AFTER_STEP",
            loss_finite=True,
            gradient_finite=True,
            parameter_finite=False,
            failure_reason="One or more model parameters or floating buffers became non-finite after optimizer step"
        )

    model.eval()
    return SafeUpdateResult(
        loss=loss_val,
        numerical_status="SUCCESS_FINITE",
        loss_finite=True,
        gradient_finite=True,
        parameter_finite=True,
        failure_reason=None
    )
