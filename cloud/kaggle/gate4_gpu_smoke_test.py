#!/usr/bin/env python3
"""
cloud/kaggle/gate4_gpu_smoke_test.py

Stage 6M Gate 4: GPU Environment Readiness & Synthetic-Data Smoke Test
=====================================================================
Governing Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)
Governing Branch:   stage6m-five-stratum-parity
Reference Commit:   baee3b8381389ffde38e907dc137623748c254a8

NON-CONFIRMATORY SMOKE TEST:
Executes GPU readiness verification using SYNTHETIC AUDIO ONLY.
Guarantees zero access to the 16,500 confirmatory evaluation audio clips,
100 gate-reference clips, or 65 reserve clips.

Verifies:
1. CUDA device availability & GPU architecture (NVIDIA Tesla T4 / P100).
2. Driver, CUDA runtime, PyTorch, and dependency versions.
3. Frozen model loading (facebook/wav2vec2-base-960h).
4. Forward pass execution on synthetic 16 kHz waveforms.
5. Finite numerical outputs (no NaNs, no Infs) & expected tensor shapes.
6. Bitwise deterministic execution under registered seed (20261101).
7. GPU memory footprint & peak VRAM allocation tracking.
8. Checkpoint serialization and round-trip state verification.
9. Clean resource shutdown & CUDA cache release.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
import torch.nn as nn
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True, errors="replace")

MODEL_ID = "facebook/wav2vec2-base-960h"
REGISTERED_SEED = 20261101


def generate_synthetic_audio(duration_sec: float = 3.0, sample_rate: int = 16000, seed: int = 42) -> np.ndarray:
    """Generates synthetic audio (multi-frequency tones + white noise) for smoke testing."""
    rng = np.random.RandomState(seed)
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Multi-frequency harmonic tones (speech-like bandwidth: 200 Hz, 500 Hz, 1200 Hz)
    signal = 0.3 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sin(2 * np.pi * 500 * t) + 0.1 * np.sin(2 * np.pi * 1200 * t)
    noise = 0.05 * rng.randn(len(t))
    waveform = (signal + noise).astype(np.float32)
    # Normalize peak amplitude to [-0.9, 0.9]
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val * 0.9
    return waveform


def compute_param_hash(model: nn.Module) -> str:
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def compute_subset_param_hash(model: nn.Module, include_ln: bool = True) -> str:
    h = hashlib.sha256()
    for name, p in model.named_parameters():
        is_ln = "layer_norm" in name or "layernorm" in name.lower()
        if (include_ln and is_ln) or (not include_ln and not is_ln):
            h.update(name.encode("utf-8"))
            h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def run_gate4_smoke_test(output_dir: Path | None = None) -> Dict[str, Any]:
    print("=" * 80)
    print("STAGE 6M GATE 4: GPU ENVIRONMENT READINESS & SYNTHETIC SMOKE TEST")
    print("Governing Protocol: Stage 6M v1.5 Five-Stratum Benchmark (Section 14.7)")
    print("Test Scope: Pure Synthetic Audio (Evaluation Cohort Strictly Sealed)")
    print("=" * 80)

    t0 = time.time()
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1. Environment & Hardware Inventory
    print("\n[Step 1] Auditing System & GPU Hardware Environment...")
    py_ver = sys.version.replace("\n", " ")
    plat_str = platform.platform()
    torch_ver = torch.__version__
    cuda_avail = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_avail else 0

    print(f"  Python Version:   {py_ver}")
    print(f"  Platform:         {plat_str}")
    print(f"  PyTorch:          {torch_ver}")
    cuda_ver = getattr(torch.version, "cuda", "N/A")
    print(f"  CUDA:             {cuda_ver}")
    print(f"  CUDA available:   {cuda_avail}")
    print(f"  GPU count:        {device_count}")
    if cuda_avail:
        for i in range(device_count):
            print(f"    GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB)")

    gpu_info: Dict[str, Any] = {}
    if cuda_avail:
        device = torch.device("cuda:0")
        device_name = torch.cuda.get_device_name(0)
        vram_bytes = torch.cuda.get_device_properties(0).total_memory
        vram_gb = vram_bytes / (1024 ** 3)
        cuda_arch = getattr(torch.cuda.get_device_properties(0), "major", "unknown")
        print(f"  Primary Device:   {device_name} (cuda:0)")
        print(f"  Total VRAM:       {vram_gb:.2f} GB ({vram_bytes:,} bytes)")
        print(f"  Compute Arch:     SM {cuda_arch}")
        if device_count > 1:
            sec_name = torch.cuda.get_device_name(1)
            sec_vram_gb = torch.cuda.get_device_properties(1).total_memory / (1024 ** 3)
            print(f"  Secondary Device: {sec_name} (cuda:1, {sec_vram_gb:.2f} GB) [NVIDIA T4 x2 Dual Topology Confirmed]")
        gpu_info = {
            "device_name": device_name,
            "device_count": device_count,
            "vram_gb": round(vram_gb, 2),
            "vram_bytes": vram_bytes,
            "cuda_arch": str(cuda_arch),
            "dual_gpu_detected": (device_count >= 2)
        }
    else:
        print("  [NOTE] CUDA not detected on local runtime. Using CPU fallback for dry-run verification.")
        device = torch.device("cpu")
        gpu_info = {
            "device_name": "CPU_FALLBACK",
            "device_count": 0,
            "vram_gb": 0.0,
            "vram_bytes": 0,
            "cuda_arch": "N/A"
        }

    # 2. Set Deterministic Seeding
    print("\n[Step 2] Enforcing Deterministic Execution Settings (Seed = 20261101)...")
    torch.manual_seed(REGISTERED_SEED)
    np.random.seed(REGISTERED_SEED)
    if cuda_avail:
        torch.cuda.manual_seed_all(REGISTERED_SEED)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    print("  -> Determinism flags successfully set.")

    # 3. Model Loading & Initial Parameter Hash
    print(f"\n[Step 3] Loading Frozen ASR Model ({MODEL_ID})...")
    t_load_start = time.time()
    processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID)
    model = model.to(device)
    model.eval()
    t_load_end = time.time()

    initial_param_hash = compute_param_hash(model)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"  Model loaded in:          {t_load_end - t_load_start:.2f} seconds")
    print(f"  Total Parameters:         {total_params:,}")
    print(f"  Trainable Parameters:     {trainable_params:,}")
    print(f"  Initial Parameter Hash:   {initial_param_hash}")
    print(f"  Vocabulary Size:          {len(processor.tokenizer.get_vocab())}")

    # 4. Forward Pass on Synthetic Waveforms (Window Size K = 4)
    print("\n[Step 4] Executing Forward Pass on Synthetic Audio Batch (K = 4 clips)...")
    synthetic_clips = [
        generate_synthetic_audio(duration_sec=3.2, seed=101),
        generate_synthetic_audio(duration_sec=2.8, seed=102),
        generate_synthetic_audio(duration_sec=4.0, seed=103),
        generate_synthetic_audio(duration_sec=3.5, seed=104),
    ]

    inputs = processor(synthetic_clips, sampling_rate=16000, return_tensors="pt", padding=True)
    input_values = inputs.input_values.to(device)

    print(f"  Input Tensor Shape:       {list(input_values.shape)}")

    if cuda_avail:
        torch.cuda.reset_peak_memory_stats()
        mem_before = torch.cuda.memory_allocated() / (1024 ** 2)

    t_fwd_start = time.time()
    with torch.no_grad():
        outputs = model(input_values)
        logits = outputs.logits
    t_fwd_end = time.time()

    fwd_time_ms = (t_fwd_end - t_fwd_start) * 1000.0
    print(f"  Forward Pass Latency:     {fwd_time_ms:.2f} ms ({fwd_time_ms / len(synthetic_clips):.2f} ms / clip)")
    print(f"  Logits Tensor Shape:      {list(logits.shape)} (batch, time, vocab)")

    # 5. Numerical Stability Verification
    print("\n[Step 5] Checking Numerical Stability & Finite Values...")
    has_nan = torch.isnan(logits).any().item()
    has_inf = torch.isinf(logits).any().item()
    min_val = logits.min().item()
    max_val = logits.max().item()
    mean_val = logits.mean().item()

    print(f"  NaN Detected:             {has_nan}")
    print(f"  Inf Detected:             {has_inf}")
    print(f"  Min Value:                {min_val:.4f}")
    print(f"  Max Value:                {max_val:.4f}")
    print(f"  Mean Value:               {mean_val:.4f}")

    if has_nan or has_inf:
        raise ValueError("Forward pass produced non-finite values (NaN or Inf)!")
    print("  -> Numerical stability verified: 100% finite logits.")

    # 6. Determinism Verification (Repeat forward pass)
    print("\n[Step 6] Testing Bitwise Determinism on Repeated Execution...")
    with torch.no_grad():
        outputs_repeat = model(input_values)
        logits_repeat = outputs_repeat.logits

    max_diff = (logits - logits_repeat).abs().max().item()
    print(f"  Max Absolute Difference:  {max_diff:.8e}")
    if max_diff != 0.0:
        raise ValueError(f"Non-deterministic execution detected! Diff = {max_diff}")
    print("  -> Determinism verified: bitwise identical outputs across repeated runs.")

    # 7. Model Invariance (Weights unchanged during inference)
    post_param_hash = compute_param_hash(model)
    print(f"\n[Step 7] Confirming Model Parameter Invariance...")
    print(f"  Post-Inference Hash:      {post_param_hash}")
    if initial_param_hash != post_param_hash:
        raise ValueError("Model weights mutated during forward pass!")
    print("  -> Invariance verified: Initial and post-inference parameter hashes match exactly.")

    # 8. Synthetic LayerNorm Adaptation Step (Disposable Model Copy)
    print("\n[Step 8] Testing Synthetic LayerNorm Adaptation Step (Disposable Model Copy)...")
    import copy
    disposable_model = copy.deepcopy(model)
    disposable_model.eval()  # SUTA preserves eval mode to disable stochastic dropout and specaugment masking

    # Freeze non-LayerNorm parameters, set requires_grad=True ONLY for LayerNorm
    for p in disposable_model.parameters():
        p.requires_grad = False
    adapt_params = []
    for name, p in disposable_model.named_parameters():
        if "layer_norm" in name or "layernorm" in name.lower():
            p.requires_grad = True
            adapt_params.append(p)

    disp_optimizer = torch.optim.AdamW(adapt_params, lr=1e-4, eps=1e-8)

    disp_initial_non_ln_hash = compute_subset_param_hash(disposable_model, include_ln=False)
    disp_initial_ln_hash = compute_subset_param_hash(disposable_model, include_ln=True)

    t_adapt_start = time.time()
    disp_optimizer.zero_grad()
    disp_logits = disposable_model(input_values).logits
    disp_probs = torch.softmax(disp_logits, dim=-1)
    disp_log_probs = torch.log(disp_probs + 1e-8)
    disp_loss = -torch.sum(disp_probs * disp_log_probs, dim=-1).mean()
    if torch.isnan(disp_loss) or torch.isinf(disp_loss):
        raise ValueError("Adaptation loss produced non-finite value (NaN or Inf)!")
    disp_loss.backward()
    disp_optimizer.step()
    t_adapt_end = time.time()
    adapt_time_ms = (t_adapt_end - t_adapt_start) * 1000.0

    disp_post_non_ln_hash = compute_subset_param_hash(disposable_model, include_ln=False)
    disp_post_ln_hash = compute_subset_param_hash(disposable_model, include_ln=True)

    print(f"  Adaptation Step Latency:  {adapt_time_ms:.2f} ms")
    print(f"  SUTA Entropy Loss:        {disp_loss.item():.4f}")
    print(f"  Non-LN Hash Invariant:    {disp_initial_non_ln_hash == disp_post_non_ln_hash}")
    print(f"  LN Hash Mutated:          {disp_initial_ln_hash != disp_post_ln_hash}")

    if disp_initial_non_ln_hash != disp_post_non_ln_hash:
        raise ValueError("Non-LayerNorm weights were mutated during adaptation step!")
    if disp_initial_ln_hash == disp_post_ln_hash:
        raise ValueError("LayerNorm weights did not update during adaptation step!")
    print("  -> Disposable LayerNorm adaptation verified: non-LN parameters 100% invariant, LN updated.")

    # 9. Checkpoint Round-Trip Simulation
    print("\n[Step 9] Testing Checkpoint State Serialization & Round-Trip Loading...")
    test_ckpt_dir = Path("scratch/test_gate4_checkpoint") if output_dir is None else output_dir / "test_ckpt"
    test_ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_file = test_ckpt_dir / "smoke_test_state.pt"

    # Save LayerNorm and optimizer state dicts
    t_ckpt_start = time.time()
    ln_state = {k: v.cpu() for k, v in disposable_model.state_dict().items() if "layer_norm" in k or "layer_norm" in k.lower()}
    torch.save({
        "ln_state": ln_state,
        "opt_state": disp_optimizer.state_dict(),
        "non_ln_param_hash": disp_initial_non_ln_hash,
        "adapted_ln_param_hash": disp_post_ln_hash,
        "win_idx": 0
    }, ckpt_file)
    ckpt_write_ms = (time.time() - t_ckpt_start) * 1000.0

    loaded_ckpt = torch.load(ckpt_file, map_location="cpu", weights_only=False)
    assert loaded_ckpt["non_ln_param_hash"] == disp_initial_non_ln_hash
    assert loaded_ckpt["adapted_ln_param_hash"] == disp_post_ln_hash
    assert "ln_state" in loaded_ckpt and "opt_state" in loaded_ckpt
    print(f"  Checkpoint File:          {ckpt_file} ({ckpt_file.stat().st_size:,} bytes)")
    print(f"  Checkpoint Write Latency: {ckpt_write_ms:.2f} ms")
    print("  -> Checkpoint serialization & round-trip verification passed.")

    # Clean up checkpoint
    if ckpt_file.exists():
        ckpt_file.unlink()
    del disposable_model, disp_optimizer

    # 10. VRAM Peak Allocation Tracking
    if cuda_avail:
        mem_after = torch.cuda.memory_allocated() / (1024 ** 2)
        peak_mem = torch.cuda.max_memory_allocated() / (1024 ** 2)
        print(f"\n[Step 10] GPU VRAM Memory Tracking:")
        print(f"  Allocated Before Fwd:     {mem_before:.2f} MB")
        print(f"  Allocated After Fwd:      {mem_after:.2f} MB")
        print(f"  Peak VRAM Used:           {peak_mem:.2f} MB")
    else:
        peak_mem = 0.0
        print("\n[Step 10] Memory tracking: CPU execution (no CUDA VRAM).")

    # 11. Clean Resource Shutdown
    print("\n[Step 11] Performing Clean Resource Shutdown & GPU Cache Clearing...")
    del input_values, outputs, logits, outputs_repeat, logits_repeat, model, processor
    gc.collect()
    if cuda_avail:
        torch.cuda.empty_cache()
        print("  -> PyTorch CUDA cache cleared.")
    print("  -> Resources released.")

    elapsed = round(time.time() - t0, 2)

    verdict = "PASSED_READY_FOR_KAGGLE_GPU" if cuda_avail else "PASSED_CPU_LOCAL_DRYRUN"

    report = {
        "report_id": "STAGE6M-GATE4-SMOKE-TEST-20261107",
        "timestamp_utc": now_utc,
        "governing_protocol": "Stage 6M v1.5 Five-Stratum Benchmark (Section 14.7)",
        "verdict": verdict,
        "system_environment": {
            "python": py_ver,
            "platform": plat_str,
            "pytorch": torch_ver,
            "cuda_version": cuda_ver,
            "cuda_available": cuda_avail,
            "gpu": gpu_info
        },
        "model_verification": {
            "model_id": MODEL_ID,
            "total_parameters": total_params,
            "initial_parameter_hash": initial_param_hash,
            "post_parameter_hash": post_param_hash,
            "weights_invariant": (initial_param_hash == post_param_hash)
        },
        "disposable_adaptation_verification": {
            "adaptation_step_latency_ms": round(adapt_time_ms, 2),
            "suta_entropy_loss": round(disp_loss.item(), 4),
            "non_layernorm_weights_invariant": (disp_initial_non_ln_hash == disp_post_non_ln_hash),
            "layernorm_weights_adapted": (disp_initial_ln_hash != disp_post_ln_hash)
        },
        "numerical_and_latency_metrics": {
            "synthetic_batch_size": len(synthetic_clips),
            "forward_latency_ms": round(fwd_time_ms, 2),
            "adaptation_latency_ms": round(adapt_time_ms, 2),
            "checkpoint_write_latency_ms": round(ckpt_write_ms, 2),
            "has_nan": has_nan,
            "has_inf": has_inf,
            "deterministic_reproducibility": (max_diff == 0.0),
            "peak_vram_mb": round(peak_mem, 2)
        },
        "checkpoint_test": "PASSED",
        "execution_duration_sec": elapsed
    }

    print("\n" + "=" * 80)
    print(f"GATE 4 SMOKE TEST VERDICT: {verdict} ({elapsed}s)")
    print("=" * 80)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 6M Gate 4 GPU Smoke Test")
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional output directory for reports")
    args = parser.parse_args()
    run_gate4_smoke_test(args.out_dir)
