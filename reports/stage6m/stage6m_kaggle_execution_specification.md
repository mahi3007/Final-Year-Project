# Stage 6M: Kaggle Cloud GPU Execution Specification (Updated)

**Specification ID:** `STAGE6M-KAGGLE-EXEC-SPEC-20261107-V2`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Target Environment:** Kaggle Cloud Virtual GPU (**NVIDIA Tesla T4 × 2**)  
**Parent Locked Manifest SHA-256:** `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0`  

---

## 1. Hardware Architecture & Platform Updates

### Primary Hardware: NVIDIA Tesla T4 × 2
Following Kaggle's official retirement of the NVIDIA Tesla P100 on **September 15, 2026**, the primary supported hardware accelerator for Kaggle Notebook workloads is **NVIDIA Tesla T4 × 2**.

| Hardware Dimension | Specification | Notes & Governance Controls |
| :--- | :--- | :--- |
| **Primary Accelerator** | **NVIDIA Tesla T4 × 2** | Two discrete GPUs, each with 2,560 CUDA Cores and 320 Tensor Cores. |
| **Historical Accelerator** | NVIDIA Tesla P100 | **Formally Retired on Sept 15, 2026.** Preserved only as a historical reference. |
| **VRAM Architecture** | 15.78 GB GDDR6 per GPU | **Discrete Memory Spaces:** Two 16 GB GPUs do NOT automatically form a unified 32 GB address space. |
| **Streaming Device Policy** | Dedicated to `cuda:0` | Sequential test-time adaptation is temporally dependent (Markovian). Streaming audio must NOT be arbitrarily parallelized or split across devices. Device 1 (`cuda:1`) is reserved for auxiliary sentinel evaluation offload if configured. |
| **Host System** | 4 vCPUs, 30 GB RAM | Intel Xeon @ 2.20 GHz container environment. |
| **Scratch Space** | `/kaggle/working` (~20 GB) | Ephemeral NVMe scratch disk space. |
| **Session Bounds** | 12.0 hours max | Quota: ~30 hours GPU per week. |

---

## 2. Preliminary Runtime Estimates vs. Empirical Measurement Protocol

> [!IMPORTANT]
> **Runtime Estimates Are Preliminary:** The previously reported throughput figures (~30–40 ms/clip and 2.8–4.2 hours total runtime) are theoretical analytical estimates. They have **not yet been empirically measured on Kaggle's T4 GPU hardware**.

### Empirical Benchmarking Protocol (Mandatory in Gate 4)
Before proceeding to Gate 5 confirmatory execution, the Gate 4 smoke test must measure actual runtime metrics on Kaggle using synthetic and development audio:
1. **Audio Decoding Latency:** Milliseconds per clip across MP3 decoders (`soundfile`, `pyav`, `miniaudio`).
2. **ASR Forward Pass Latency:** Milliseconds per forward pass on batch size $K=4$.
3. **SUTA Gradient Step Latency:** Milliseconds per LayerNorm backpropagation and AdamW update.
4. **Sentinel Safety Gate Evaluation Time:** Milliseconds per candidate transaction.
5. **Checkpoint Serialization Overhead:** I/O time to write `.pt` state vectors to disk.
6. **Peak VRAM & Host Memory:** Measured dynamically via `torch.cuda.max_memory_allocated()`.

---

## 3. Cryptographic Transcript Isolation Architecture

To prevent data leakage and guarantee strict scientific blinding of the confirmatory cohort, the Kaggle execution package decouples evaluation reference labels from the streaming runner:

```
Official Locked Manifest (Parent)
SHA-256: 171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0
├── 1. Restricted Online Manifest (Consumed by Online Streaming Runner)
│   Path: datasets/splits/stage6m_cohort3_online_inference_manifest.json
│   SHA-256: 0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1
│   ├── 16,500 Evaluation Clips: transcript = null (Strictly Shielded)
│   ├──  1,500 Gate-Reference Clips: transcript = Active (Required by DSG Sentinel Gate)
│   └──    975 Australian Reserve Clips: transcript = null (Sealed)
│
└── 2. Sealed Evaluation Transcripts Key (Reserved for Gate 6 Offline Scoring)
    Path: datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json
    SHA-256: f427ae7fbf386f77b0795cc1fa33b2f7831c89f89ecfce7fa30036cde5c5223e
    └── 17,475 Reference Transcripts strictly locked until post-inference scoring
```

---

## 4. Exact Dependency Freeze Directive

Kaggle containers provide a pre-installed PyTorch build compiled against CUDA.
- **Rule:** Do NOT execute unpinned upgrades (`pip install --upgrade torch` or `transformers`).
- **File:** Adhere strictly to [`requirements-kaggle-lock.txt`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/requirements-kaggle-lock.txt).
- **Installed Baseline:**
  - `torch==2.1.2+cu121`
  - `transformers==4.40.2`
  - `soundfile==0.12.1`
  - `av==12.0.0`
  - `miniaudio==1.59`
  - `numpy==1.26.4`
  - `scipy==1.13.0`
  - `pandas==2.2.2`
  - `statsmodels==0.14.2`
  - `editdistance==0.8.1`
