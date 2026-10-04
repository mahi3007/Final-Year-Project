"""
DSUTA: Dynamic SUTA for Continual Test-Time Adaptation.
Reference: Lin et al., "Continual Test-time Adaptation for End-to-end Speech
Recognition on Noisy Speech" (EMNLP 2024).

Implements continual adaptation with an adaptive dynamic reset mechanism based on
output entropy monitoring to prevent error accumulation and representational collapse.
"""

from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn

from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch


class DsutaAdapter(BaseTestTimeAdapter):
    """
    DSUTA research adapter for Continual TTA.
    Monitors online prediction entropy and triggers dynamic parameter resets
    to initial weights theta_0 when severe domain shift or collapse is detected.
    """

    def __init__(
        self,
        asr_model: BaseASRModel,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(asr_model=asr_model, method_id="dsuta", config=config)
        self.lr = float(self.config.get("lr", 1e-4))
        self.temperature = float(self.config.get("temperature", 2.5))
        self.alpha = float(self.config.get("alpha", 0.5))
        self.steps = int(self.config.get("steps", 1))

        # Dynamic Reset Hyperparameters
        self.reset_threshold_ratio = float(self.config.get("reset_threshold_ratio", 1.25))
        self.momentum = float(self.config.get("momentum", 0.2))
        self.running_entropy: Optional[float] = None
        self.total_resets = 0

        self.optimizer: Optional[torch.optim.Optimizer] = None
        self._setup_adaptation_parameters()

    def _setup_adaptation_parameters(self) -> None:
        """Freeze non-LayerNorm parameters and configure optimizer."""
        if self.asr_model.model is None:
            self.asr_model.load_model()

        model = self.asr_model.model
        trainable_params: List[torch.nn.Parameter] = []

        for param in model.parameters():
            param.requires_grad = False

        for name, module in model.named_modules():
            if isinstance(module, (nn.LayerNorm,)):
                for p_name, param in module.named_parameters():
                    param.requires_grad = True
                    trainable_params.append(param)
            elif "layer_norm" in name.lower() or "layernorm" in name.lower():
                for p_name, param in module.named_parameters(recurse=False):
                    param.requires_grad = True
                    trainable_params.append(param)

        unique_params = list({id(p): p for p in trainable_params}.values())
        if unique_params:
            self.optimizer = torch.optim.AdamW(unique_params, lr=self.lr, weight_decay=0.0)

    def _compute_entropy(self, probs: torch.Tensor) -> torch.Tensor:
        """Compute mean frame entropy."""
        log_probs = torch.log(probs + 1e-8)
        return - torch.mean(torch.sum(probs * log_probs, dim=-1))

    def _compute_mcc_loss(self, probs: torch.Tensor) -> torch.Tensor:
        """Compute MCC loss."""
        B, T, C = probs.shape
        flat_probs = probs.view(-1, C)
        class_sums = torch.sum(flat_probs, dim=0)
        norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0)) + 1e-8
        corr_matrix = (flat_probs.T @ flat_probs) / norm_factor
        diagonal = torch.diag(corr_matrix)
        off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
        return off_diag_sum / (C * (C - 1) + 1e-8)

    def adapt(self, batch: UnlabeledAudioBatch) -> AdaptationStepResult:
        """
        Execute DSUTA adaptation step with dynamic reset detection.
        """
        start_time = time.time()
        theta_before_hash = self.compute_model_hash()

        if self.asr_model.model is None or self.optimizer is None:
            self._setup_adaptation_parameters()

        waveforms = batch.load_waveforms()
        if not waveforms:
            return AdaptationStepResult(
                batch_idx=batch.batch_idx,
                method_id="dsuta",
                theta_before_hash=theta_before_hash,
                theta_after_hash=theta_before_hash,
                updated=False,
                adaptation_time_seconds=0.0
            )

        model = self.asr_model.model
        processor = self.asr_model.processor
        device = self.asr_model.device

        inputs = processor(
            waveforms,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        input_values = inputs.input_values.to(device)

        # 1. Forward pass to evaluate batch entropy before update
        with torch.no_grad():
            eval_outputs = model(input_values)
            eval_probs = torch.softmax(eval_outputs.logits / self.temperature, dim=-1)
            batch_entropy = float(self._compute_entropy(eval_probs).item())

        # 2. Dynamic Reset Check
        reset_triggered = False
        if self.running_entropy is not None:
            threshold = self.reset_threshold_ratio * self.running_entropy
            if batch_entropy > threshold:
                reset_triggered = True
                self.reset_to_initial()
                self._setup_adaptation_parameters()
                self.total_resets += 1
                self.running_entropy = batch_entropy

        if not reset_triggered:
            if self.running_entropy is None:
                self.running_entropy = batch_entropy
            else:
                self.running_entropy = (1.0 - self.momentum) * self.running_entropy + self.momentum * batch_entropy

        # 3. Adaptation Update
        model.train()
        loss_history: List[float] = []

        for _ in range(self.steps):
            self.optimizer.zero_grad()
            outputs = model(input_values)
            probs = torch.softmax(outputs.logits / self.temperature, dim=-1)

            l_em = self._compute_entropy(probs)
            l_mcc = self._compute_mcc_loss(probs)
            total_loss = self.alpha * l_em + (1.0 - self.alpha) * l_mcc

            total_loss.backward()
            self.optimizer.step()
            loss_history.append(float(total_loss.item()))

        model.eval()
        self.step_count += 1
        elapsed = time.time() - start_time
        self.total_adaptation_time += elapsed

        theta_after_hash = self.compute_model_hash()

        return AdaptationStepResult(
            batch_idx=batch.batch_idx,
            method_id="dsuta",
            theta_before_hash=theta_before_hash,
            theta_after_hash=theta_after_hash,
            updated=True,
            reset_occurred=reset_triggered,
            adaptation_time_seconds=elapsed,
            loss_history=loss_history,
            details={
                "batch_entropy": batch_entropy,
                "running_entropy": self.running_entropy,
                "reset_triggered": reset_triggered,
                "total_resets": self.total_resets
            }
        )
