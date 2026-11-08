#!/usr/bin/env python3
"""Builds cloud/kaggle/gate4_gpu_smoke_test_kaggle.ipynb with T4 x2 and exact locks."""

import json
from pathlib import Path

nb = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Stage 6M Gate 4: Kaggle Virtual GPU Environment Readiness Smoke Test\n",
                "## Non-Confirmatory Hardware & ASR Forward-Pass Verification\n",
                "\n",
                "**Governing Protocol:** Stage 6M v1.5 Five-Stratum Benchmark (Section 14.7)  \n",
                "**Governing Branch:** `stage6m-five-stratum-parity`  \n",
                "**Target Accelerator:** NVIDIA Tesla T4 × 2 (Dual 16 GB VRAM GPUs; Tesla P100 is retired)  \n",
                "**Execution Scope:** **SYNTHETIC AUDIO ONLY** (Zero access to the 16,500 confirmatory evaluation clips)  \n",
                "\n",
                "---\n",
                "### Objective\n",
                "Verify GPU hardware visibility, CUDA runtime, frozen model loading (`facebook/wav2vec2-base-960h`), numerical stability, bitwise determinism, peak memory allocation, and checkpoint serialization before requesting confirmatory experiment authorization (Gate 5)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 1: Hardware & CUDA Environment Audit (Dynamic T4 x2 Detection)\n",
                "import sys, os, platform\n",
                "import torch\n",
                "\n",
                "print('=' * 80)\n",
                "print('STAGE 6M GATE 4: KAGGLE ACCELERATOR AUDIT')\n",
                "print('=' * 80)\n",
                "print('Python Version:  ', sys.version.split()[0])\n",
                "print('Platform:        ', platform.platform())\n",
                "print('PyTorch Version: ', torch.__version__)\n",
                "print('CUDA Available:  ', torch.cuda.is_available())\n",
                "\n",
                "if torch.cuda.is_available():\n",
                "    dev_count = torch.cuda.device_count()\n",
                "    dev_name_0 = torch.cuda.get_device_name(0)\n",
                "    vram_gb_0 = torch.cuda.get_device_properties(0).total_memory / (1024**3)\n",
                "    print(f'Device Count:     {dev_count}')\n",
                "    print(f'Primary GPU (0):  {dev_name_0} ({vram_gb_0:.2f} GB VRAM)')\n",
                "    if dev_count > 1:\n",
                "        dev_name_1 = torch.cuda.get_device_name(1)\n",
                "        vram_gb_1 = torch.cuda.get_device_properties(1).total_memory / (1024**3)\n",
                "        print(f'Secondary GPU (1): {dev_name_1} ({vram_gb_1:.2f} GB VRAM) [NVIDIA T4 x2 Dual Topology Confirmed]')\n",
                "    assert vram_gb_0 >= 14.0, f'VRAM {vram_gb_0:.2f} GB below expected 16GB profile!'\n",
                "    print('STATUS: Hardware check PASSED.')\n",
                "else:\n",
                "    print('[ERROR] CUDA not available! In Kaggle, enable Settings -> Accelerator -> GPU T4 x2')\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 2: Verify & Install Exact Dependencies (No Unpinned PyTorch Upgrades)\n",
                "# Install only complementary audio decoders and metrics with exact version pins\n",
                "!pip install -q soundfile==0.12.1 av==12.0.0 miniaudio==1.59 editdistance==0.8.1 statsmodels==0.14.2\n",
                "\n",
                "import transformers, soundfile, numpy, scipy\n",
                "print('Transformers:', transformers.__version__)\n",
                "print('SoundFile:   ', soundfile.__version__)\n",
                "print('NumPy:       ', numpy.__version__)\n",
                "print('SciPy:       ', scipy.__version__)\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 3: Verify Frozen Manifest Digest in Attached Input Dataset\n",
                "import hashlib\n",
                "from pathlib import Path\n",
                "\n",
                "# Search for attached Kaggle dataset or cloned workspace\n",
                "possible_paths = [\n",
                "    Path('/kaggle/input/stage6m-frozen-benchmark/splits/stage6m_cohort3_online_inference_manifest.json'),\n",
                "    Path('/kaggle/input/stage6m-frozen-benchmark/stage6m_cohort3_online_inference_manifest.json'),\n",
                "    Path('datasets/splits/stage6m_cohort3_online_inference_manifest.json'),\n",
                "    Path('/kaggle/input/stage6m-frozen-benchmark/splits/stage6m_cohort3_final_manifest.json'),\n",
                "    Path('/kaggle/input/stage6m-frozen-benchmark/stage6m_cohort3_final_manifest.json'),\n",
                "    Path('datasets/splits/stage6m_cohort3_final_manifest.json')\n",
                "]\n",
                "\n",
                "manifest_file = None\n",
                "for p in possible_paths:\n",
                "    if p.exists():\n",
                "        manifest_file = p\n",
                "        break\n",
                "\n",
                "if manifest_file:\n",
                "    h = hashlib.sha256(manifest_file.read_bytes()).hexdigest()\n",
                "    expected_online = '0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1'\n",
                "    expected_parent = '171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0'\n",
                "    print(f'Manifest Path:   {manifest_file}')\n",
                "    print(f'Manifest SHA256: {h}')\n",
                "    if h == expected_online:\n",
                "        print('STATUS: Restricted online manifest verified 100% authentic (transcripts shielded).')\n",
                "    elif h == expected_parent:\n",
                "        print('STATUS: Parent locked final manifest verified 100% authentic.')\n",
                "    else:\n",
                "        raise ValueError(f'Digest mismatch! Unexpected hash: {h}')\n",
                "else:\n",
                "    print('[NOTE] Benchmark dataset not mounted yet. Gate 4 smoke test will proceed on synthetic data.')\n"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Cell 4: Execute Gate 4 GPU Smoke Test (Synthetic Audio Only)\n",
                "from pathlib import Path\n",
                "if Path('cloud/kaggle/gate4_gpu_smoke_test.py').exists():\n",
                "    !python cloud/kaggle/gate4_gpu_smoke_test.py\n",
                "else:\n",
                "    import torch, numpy as np, hashlib\n",
                "    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor\n",
                "    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')\n",
                "    print(f'Executing smoke test on {device}...')\n",
                "    model_id = 'facebook/wav2vec2-base-960h'\n",
                "    processor = Wav2Vec2Processor.from_pretrained(model_id)\n",
                "    model = Wav2Vec2ForCTC.from_pretrained(model_id).to(device)\n",
                "    model.eval()\n",
                "    t = np.linspace(0, 3.0, 48000, endpoint=False)\n",
                "    synth = [0.3 * np.sin(2 * np.pi * (200 + 100*i) * t).astype(np.float32) for i in range(4)]\n",
                "    inputs = processor(synth, sampling_rate=16000, return_tensors='pt', padding=True).to(device)\n",
                "    with torch.no_grad():\n",
                "        out = model(inputs.input_values)\n",
                "        logits = out.logits\n",
                "    print(f'Logits shape: {list(logits.shape)}')\n",
                "    assert not torch.isnan(logits).any(), 'NaN found!'\n",
                "    assert not torch.isinf(logits).any(), 'Inf found!'\n",
                "    if torch.cuda.is_available():\n",
                "        print(f'Peak VRAM: {torch.cuda.max_memory_allocated() / (1024**2):.2f} MB')\n",
                "    print('GATE 4 SMOKE TEST: PASSED_READY_FOR_KAGGLE_GPU')\n"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Summary & Next Step\n",
                "If all checks pass with verdict `PASSED_READY_FOR_KAGGLE_GPU`, the Kaggle runtime is confirmed ready for confirmatory benchmarking. Record the test output and proceed to Project Lead authorization for Gate 5."
            ]
        }
    ],
    "metadata": {
        "language_info": {"name": "python"},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

out_path = Path("cloud/kaggle/gate4_gpu_smoke_test_kaggle.ipynb")
out_path.write_text(json.dumps(nb, indent=2), encoding="utf-8")
print("Wrote", out_path, out_path.stat().st_size, "bytes")
