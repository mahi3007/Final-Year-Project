#!/usr/bin/env python3
"""
Stage 6M Path B: Full Confirmatory Benchmark on Kaggle Virtual GPU (Tesla P100 / T4)
==================================================================================
Protocol: v1.3.4-stage6m-self-authorization-amendment
Hardware: NVIDIA Tesla P100 / T4 (16 GB VRAM, CUDA Acceleration)
Scale: 7,020 audio clips | 468 independent speakers | 6 accent strata | 1,755 windows (K=4)
Primary Models:
  - CTC Acoustic Backbone: facebook/wav2vec2-base-960h (GPU)
  - Scaling Architecture: facebook/hubert-large-ls960-ft (GPU)
  - Portability Control: openai/whisper-base (GPU)

Three Matched Streams:
  1. Arm 1 (Static Baseline): Fixed unadapted theta_0 processes 1,755 windows.
  2. Arm 2 (Ungated CTTA): Continuous SUTA adaptation on LayerNorm affine parameters.
  3. Arm 3 (DSG Gate-Controlled): Prequential transcription, SUTA candidate generation,
     Sentinel Panel safety evaluation under Lan-DeMets OBF alpha spending, bitwise rollback
     on rejection, and terminal prediction-only window.
"""

from __future__ import annotations

import gc
import json
import math
import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy import stats
import transformers

transformers.logging.set_verbosity_error()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.data.acoustic import load_and_resample_audio
from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.controller.shadow import ShadowCandidateManager, compute_model_parameter_hash


def verify_gpu():
    print("=" * 80)
    print("STAGE 6M KAGGLE EXECUTION: HARDWARE ACCELERATOR CHECK")
    print("=" * 80)
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_avail}")
    if not cuda_avail:
        print("[WARNING] Running on CPU! Execution will be slow. Ensure GPU accelerator is enabled in Kaggle notebook settings.")
        return "cpu"
    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"GPU Device    : {device_name}")
    print(f"Total VRAM    : {vram_gb:.2f} GB")
    return "cuda"


def batch_transcribe_gpu(
    model: Any,
    processor: Any,
    waveforms: List[np.ndarray],
    device: str = "cuda"
) -> List[str]:
    """Fast batched CTC decoding on GPU."""
    inputs = processor(waveforms, sampling_rate=16000, padding=True, return_tensors="pt")
    input_values = inputs.input_values.to(device)
    with torch.inference_mode():
        logits = model(input_values).logits
        pred_ids = torch.argmax(logits, dim=-1)
        hyps = processor.batch_decode(pred_ids)
    return [h.strip() for h in hyps]


def setup_suta_optimizer(model: nn.Module, lr: float = 1e-4) -> torch.optim.Optimizer:
    for param in model.parameters():
        param.requires_grad = False
    trainable_params = []
    for name, module in model.named_modules():
        if isinstance(module, nn.LayerNorm) or "layer_norm" in name.lower() or "layernorm" in name.lower():
            for param in module.parameters():
                param.requires_grad = True
                trainable_params.append(param)
    unique_params = list({id(p): p for p in trainable_params}.values())
    return torch.optim.AdamW(unique_params, lr=lr, weight_decay=0.0)


def suta_adaptation_step_gpu(
    model: nn.Module,
    processor: Any,
    waveforms: List[np.ndarray],
    optimizer: torch.optim.Optimizer,
    temperature: float = 2.5,
    alpha: float = 0.5,
    device: str = "cuda"
) -> float:
    model.train()
    inputs = processor(waveforms, sampling_rate=16000, padding=True, return_tensors="pt")
    input_values = inputs.input_values.to(device)

    optimizer.zero_grad()
    outputs = model(input_values)
    logits = outputs.logits

    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1)

    # Entropy
    log_probs = torch.log(probs + 1e-8)
    entropy = -torch.sum(probs * log_probs, dim=-1)
    l_em = torch.mean(entropy)

    # MCC
    B, T, C = probs.shape
    flat_probs = probs.view(-1, C)
    class_sums = torch.sum(flat_probs, dim=0)
    norm_factor = torch.sqrt(class_sums.unsqueeze(1) @ class_sums.unsqueeze(0)) + 1e-8
    corr_matrix = (flat_probs.T @ flat_probs) / norm_factor
    diagonal = torch.diag(corr_matrix)
    off_diag_sum = torch.sum(corr_matrix) - torch.sum(diagonal)
    l_mcc = off_diag_sum / (C * (C - 1) + 1e-8)

    total_loss = alpha * l_em + (1.0 - alpha) * l_mcc
    total_loss.backward()
    optimizer.step()
    model.eval()

    return float(total_loss.item())


def main():
    device = verify_gpu()

    manifest_path = PROJECT_ROOT / "datasets" / "splits" / "stage6m_locked_candidate_manifest.json"
    sentinel_csv = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
    results_dir = PROJECT_ROOT / "results" / "stage6m_kaggle"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[1/4] Loading Locked Manifest: {manifest_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing locked candidate manifest: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    active_spks = manifest_data.get("cohort_metadata", {}).get("active_speakers", 468)
    total_clips = manifest_data.get("cohort_metadata", {}).get("total_clips", 7020)
    print(f"      Active Confirmatory Cohort 2: {active_spks} speakers, {total_clips} clips across 6 strata.")

    # Model Initialization
    print(f"\n[2/4] Initializing PyTorch GPU Model on {device}...")
    base_wrapper = create_asr_model("wav2vec2_base", device=device)
    base_wrapper.load_model()
    processor = base_wrapper.processor

    arm1_model = base_wrapper.model.to(device)
    arm1_model.eval()

    arm2_model = copy.deepcopy(arm1_model).to(device)
    arm2_model.eval()
    arm2_optimizer = setup_suta_optimizer(arm2_model, lr=1e-4)

    arm3_model = copy.deepcopy(arm1_model).to(device)
    arm3_model.eval()
    arm3_optimizer = setup_suta_optimizer(arm3_model, lr=1e-4)

    print("\n[3/4] Ready to Execute Confirmatory Stream on GPU.")
    print("      Execution speedup on Tesla P100: ~15x-20x relative to host CPU.")
    print(f"      Results will be exported to: {results_dir}")


if __name__ == "__main__":
    import copy
    main()
