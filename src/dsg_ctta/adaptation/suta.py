"""
SUTA: Single-Utterance Test-Time Adaptation for ASR.
Reference: Lin et al., "Listen, Adapt, Better WER: Source-free Single-utterance
Test-time Adaptation for Automatic Speech Recognition" (arXiv:2203.14222).

Adapts only LayerNorm affine parameters via Entropy Minimization and Minimum Class Confusion.
"""

from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
import numpy as np

from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch


class SutaAdapter(BaseTestTimeAdapter):
    """
    SUTA research adapter for CTC-based speech models (wav2vec 2.0).
    Updates only LayerNorm affine parameters using unsupervised EM + MCC loss.
    """

    def __init__(
        self,
        asr_model: BaseASRModel,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(asr_model=asr_model, method_id="suta", config=config)
        self.lr = float(self.config.get("lr", 1e-4))
        self.temperature = float(self.config.get("temperature", 2.5))
        self.alpha = float(self.config.get("alpha", 0.5))  # Weight for EM vs MCC
        self.steps = int(self.config.get("steps", 1))

        self.optimizer: Optional[torch.optim.Optimizer] = None
        self._setup_adaptation_parameters()

    def _setup_adaptation_parameters(self) -> None:
        """
        Freeze all parameters except LayerNorm weights and biases.
        Configures the AdamW optimizer over trainable LayerNorm parameters.
        """
        if self.asr_model.model is None:
            self.asr_model.load_model()

        model = self.asr_model.model
        trainable_params: List[torch.nn.Parameter] = []

        # Freeze everything first
        for param in model.parameters():
            param.requires_grad = False

        # Unfreeze only LayerNorm modules
        for name, module in model.named_modules():
            if isinstance(module, (nn.LayerNorm,)):
                for p_name, param in module.named_parameters():
                    param.requires_grad = True
                    trainable_params.append(param)
            elif "layer_norm" in name.lower() or "layernorm" in name.lower():
                for p_name, param in module.named_parameters(recurse=False):
                    param.requires_grad = True
                    trainable_params.append(param)

        # Deduplicate parameters
        unique_params = list({id(p): p for p in trainable_params}.values())
        if unique_params:
            self.optimizer = torch.optim.AdamW(unique_params, lr=self.lr, weight_decay=0.0)

    def _compute_entropy_loss(self, probs: torch.Tensor) -> torch.Tensor:
        """Compute frame-level Shannon entropy loss: - sum(p * log(p))."""
        log_probs = torch.log(probs + 1e-8)
        entropy = - torch.sum(probs * log_probs, dim=-1)  # (B, T)
        return torch.mean(entropy)

    def _compute_mcc_loss(self, probs: torch.Tensor) -> torch.Tensor:
        """
        Compute Minimum Class Confusion (MCC) loss.
        Penalizes off-diagonal cross-class correlations across frames.
        """
        # Flatten batch and time: (B*T, C)
        B, T, C = probs.shape
        flat_probs = probs.view(-1, C)

        # Class correlation matrix C_tilde
        # Correlation between class j and class k: sum_t(p_j * p_k) / (sqrt(sum p_j) * sqrt(sum p_k))
        class_sums = torch.sum(flat_probs, dim=0)  # (C,)
        norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0)) + 1e-8
        corr_matrix = (flat_probs.T @ flat_probs) / norm_factor

        # Penalize off-diagonal elements
        diagonal = torch.diag(corr_matrix)
        off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
        mcc_loss = off_diag_sum / (C * (C - 1) + 1e-8)
        return mcc_loss

    def adapt(self, batch: UnlabeledAudioBatch) -> AdaptationStepResult:
        """
        Execute unsupervised SUTA adaptation step using unlabeled audio.
        """
        start_time = time.time()
        theta_before_hash = self.compute_model_hash()

        if self.asr_model.model is None or self.optimizer is None:
            self._setup_adaptation_parameters()

        waveforms = batch.load_waveforms()
        if not waveforms:
            return AdaptationStepResult(
                batch_idx=batch.batch_idx,
                method_id="suta",
                theta_before_hash=theta_before_hash,
                theta_after_hash=theta_before_hash,
                updated=False,
                adaptation_time_seconds=0.0
            )

        model = self.asr_model.model
        processor = self.asr_model.processor
        device = self.asr_model.device

        # Process inputs
        inputs = processor(
            waveforms,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        input_values = inputs.input_values.to(device)

        model.train()  # Enable grad computation
        loss_history: List[float] = []

        for _ in range(self.steps):
            self.optimizer.zero_grad()
            outputs = model(input_values)
            logits = outputs.logits  # (B, T, C)

            # Temperature-scaled probabilities
            scaled_logits = logits / self.temperature
            probs = torch.softmax(scaled_logits, dim=-1)

            # Compute SUTA loss
            l_em = self._compute_entropy_loss(probs)
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
            method_id="suta",
            theta_before_hash=theta_before_hash,
            theta_after_hash=theta_after_hash,
            updated=True,
            reset_occurred=False,
            adaptation_time_seconds=elapsed,
            loss_history=loss_history,
            details={
                "steps": self.steps,
                "final_loss": loss_history[-1] if loss_history else 0.0,
                "alpha": self.alpha,
                "temperature": self.temperature
            }
        )
