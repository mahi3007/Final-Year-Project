"""
DMSUTA: Dynamic Model-bank Single-Utterance Test-Time Adaptation.
Reference: Wang et al., "Dynamic Model-bank Test-time Adaptation for Automatic
Speech Recognition" (EMNLP 2025).

Maintains a dynamic model bank of diverse model checkpoints.
Selects the most confident checkpoint for incoming test speech, adapts it,
and manages the bank via selection, appending, and pruning.
"""

from __future__ import annotations
import copy
import time
from typing import Dict, Any, List, Optional, Tuple
import torch
import torch.nn as nn

from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch


class DmsutaAdapter(BaseTestTimeAdapter):
    """
    DMSUTA research adapter for Continual TTA with Dynamic Model Bank.
    """

    def __init__(
        self,
        asr_model: BaseASRModel,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(asr_model=asr_model, method_id="dmsuta", config=config)
        self.lr = float(self.config.get("lr", 1e-4))
        self.temperature = float(self.config.get("temperature", 2.5))
        self.alpha = float(self.config.get("alpha", 0.5))
        self.steps = int(self.config.get("steps", 1))
        self.max_bank_size = int(self.config.get("max_bank_size", 3))

        self.optimizer: Optional[torch.optim.Optimizer] = None
        self._setup_adaptation_parameters()

        # Dynamic Model Bank: list of (checkpoint_id, state_dict, historical_entropy)
        self.model_bank: List[Dict[str, Any]] = []
        self._initialize_model_bank()

    def _setup_adaptation_parameters(self) -> None:
        """Freeze non-LayerNorm parameters and setup optimizer."""
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

    def _initialize_model_bank(self) -> None:
        """Initialize the model bank with the pristine source anchor model theta_0."""
        if self.asr_model.model is None:
            self.asr_model.load_model()

        anchor_state = {k: v.clone().cpu() for k, v in self.asr_model.model.state_dict().items()}
        self.model_bank = [{
            "id": "theta_0_anchor",
            "state_dict": anchor_state,
            "entropy": 1.0,
            "is_anchor": True
        }]

    def _compute_entropy(self, probs: torch.Tensor) -> torch.Tensor:
        """Frame entropy."""
        log_probs = torch.log(probs + 1e-8)
        return - torch.mean(torch.sum(probs * log_probs, dim=-1))

    def _compute_mcc_loss(self, probs: torch.Tensor) -> torch.Tensor:
        """MCC loss."""
        B, T, C = probs.shape
        flat_probs = probs.view(-1, C)
        class_sums = torch.sum(flat_probs, dim=0)
        norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0)) + 1e-8
        corr_matrix = (flat_probs.T @ flat_probs) / norm_factor
        diagonal = torch.diag(corr_matrix)
        off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
        return off_diag_sum / (C * (C - 1) + 1e-8)

    def select_best_checkpoint(self, input_values: torch.Tensor) -> Tuple[str, float]:
        """
        Evaluate all checkpoints in the model bank on input audio and select the one
        with minimum predictive entropy (maximum confidence).
        """
        model = self.asr_model.model
        best_id = self.model_bank[0]["id"]
        lowest_entropy = float("inf")
        curr_state = {k: v.clone().cpu() for k, v in model.state_dict().items()}

        with torch.no_grad():
            for item in self.model_bank:
                # Load candidate checkpoint
                model.load_state_dict(item["state_dict"])
                outputs = model(input_values)
                probs = torch.softmax(outputs.logits / self.temperature, dim=-1)
                ent = float(self._compute_entropy(probs).item())
                if ent < lowest_entropy:
                    lowest_entropy = ent
                    best_id = item["id"]

        # Restore the best checkpoint
        best_item = next(it for it in self.model_bank if it["id"] == best_id)
        model.load_state_dict(best_item["state_dict"])
        self._setup_adaptation_parameters()

        return best_id, lowest_entropy

    def adapt(self, batch: UnlabeledAudioBatch) -> AdaptationStepResult:
        """
        Execute DMSUTA adaptation: select best checkpoint from bank, adapt, and update bank.
        """
        start_time = time.time()
        theta_before_hash = self.compute_model_hash()

        if self.asr_model.model is None or self.optimizer is None:
            self._setup_adaptation_parameters()

        waveforms = batch.load_waveforms()
        if not waveforms:
            return AdaptationStepResult(
                batch_idx=batch.batch_idx,
                method_id="dmsuta",
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

        # 1. Model Bank Selection: select most confident checkpoint
        best_checkpoint_id, min_entropy = self.select_best_checkpoint(input_values)

        # 2. Local Adaptation on chosen checkpoint
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

        # 3. Model Bank Update (Append & Prune)
        with torch.no_grad():
            post_outputs = model(input_values)
            post_probs = torch.softmax(post_outputs.logits / self.temperature, dim=-1)
            adapted_entropy = float(self._compute_entropy(post_probs).item())

        new_ckpt_id = f"theta_w{batch.batch_idx}"
        new_state = {k: v.clone().cpu() for k, v in model.state_dict().items()}
        self.model_bank.append({
            "id": new_ckpt_id,
            "state_dict": new_state,
            "entropy": adapted_entropy,
            "is_anchor": False
        })

        # Prune if bank size exceeds max capacity (never prune anchor)
        if len(self.model_bank) > self.max_bank_size:
            non_anchors = [it for it in self.model_bank if not it.get("is_anchor", False)]
            if non_anchors:
                # Prune checkpoint with highest entropy
                worst_non_anchor = max(non_anchors, key=lambda it: it["entropy"])
                self.model_bank.remove(worst_non_anchor)

        elapsed = time.time() - start_time
        self.total_adaptation_time += elapsed
        theta_after_hash = self.compute_model_hash()

        return AdaptationStepResult(
            batch_idx=batch.batch_idx,
            method_id="dmsuta",
            theta_before_hash=theta_before_hash,
            theta_after_hash=theta_after_hash,
            updated=True,
            reset_occurred=False,
            adaptation_time_seconds=elapsed,
            loss_history=loss_history,
            details={
                "selected_checkpoint": best_checkpoint_id,
                "selected_entropy": min_entropy,
                "adapted_entropy": adapted_entropy,
                "bank_size": len(self.model_bank)
            }
        )
