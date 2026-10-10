# Stage 5M & Stage 6: Cloud Virtual GPU Execution Guide
## Running Closed-Loop Online Control & Multi-Model Benchmarks on Free Cloud GPUs (Kaggle & Colab)

This directory contains the complete execution package for running **Stage 5M (Closed-Loop Online Control)** and **Stage 6 (Multi-Model Generalization Benchmark)** on free virtual GPUs (NVIDIA Tesla P100 / T4).

---

### Executive Summary: What These Stages Evaluate

| Stage | Objective | Benchmark Dataset | Evaluated Models | Online Adaptation & Gate |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 5M** | **Closed-Loop Online Control** under acoustic stress | L2-ARCTIC (5 acoustic stress conditions, 12 speakers, 6 accents) | 3 CTC Backbones + 3 Seq2Seq Controls | Live Disparity Safety Gate on **Sentinel Panel ($N=30$)**; candidate updates accepted/rejected prequentially. |
| **Stage 5D** | Single-Model DSG Re-execution | Common Voice 27.0 (900 clips, 225 windows, $K=4$) | `wav2vec2_base` | Live DSG Controller on 300-clip Sentinel Panel ($N=30$). |
| **Stage 6** | **Cross-Architecture Generalization Benchmark** | Common Voice 27.0 (900 clips, 60 speakers, 6 strata) | 6 Diverse Architectures (CTC & Seq2Seq) | No-Adapt, SUTA, DSUTA, DMSUTA, and DSG across 225 prequential windows. |
| **Stage 6.1** | Two-Model Large CTC Extension | Common Voice 27.0 (900 clips, 60 speakers, 6 strata) | `wav2vec2_large_lv60`, `wav2vec2_large_robust` | Parameter scale (315.5M) and acoustic pretraining robustness. |

---

### Why Use a Free Cloud GPU (NVIDIA Tesla P100)?

Evaluating sequential prequential windows with batched sentinel panel verification requires significant neural forward passes:

| Environment | Accelerator | VRAM | Typical Speed | Total Runtime | Cost |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Local Laptop CPU** | CPU (Intel/AMD) | System RAM | 1x | 12 – 18 hours | Free |
| **Kaggle Notebooks (Recommended)** | **NVIDIA Tesla P100** | **16 GB** | **15x – 25x faster** | **~1.5 – 2.5 hours** | **Free (Zero cost)** |
| **Google Colab Free Tier** | **NVIDIA T4** | **16 GB** | **10x – 15x faster** | **~2.0 – 3.0 hours** | **Free (Zero cost)** |

---

### Quickstart Guide: Running Stage 5M on Kaggle (Step-by-Step)

#### Step 1: Open Kaggle Notebooks
1. Go to [https://www.kaggle.com/code](https://www.kaggle.com/code) and sign in (or create a free account).
2. Click **New Notebook** (top right).

#### Step 2: Enable Free Tesla P100 GPU
1. In the right-hand panel under **Notebook options**:
   - Click **Accelerator** $\to$ Select **GPU P100**.
   - Ensure **Internet** is toggled **ON**.

#### Step 3: Clone or Upload the Code
In the first notebook cell:
```bash
# Clone the repository
!git clone <YOUR_GITHUB_REPO_URL> project
%cd project
```
*(Alternatively, you can upload `cloud/kaggle/run_stage5m_kaggle.ipynb` directly via **File $\to$ Upload Notebook**).*

#### Step 4: Run the Environment & Audio Setup
In the next cell:
```python
!python cloud/kaggle/setup_kaggle.py
```
This automatically installs dependencies, checks the Tesla P100 GPU, extracts audio assets (`stage5m_audio_bundle.tar.gz`), and verifies Stage 5M research validity invariants.

#### Step 5: Fast Smoke Test (Optional, ~30s)
In the next cell:
```python
!python cloud/kaggle/run_stage5m_online_control.py --smoke-test
```
Verifies the Sentinel Safety Gate, paired bootstrap ($B=1000$), and label isolation firewall in ~30 seconds.

#### Step 6: Execute the Full Stage 5M Suite
In the next cell:
```python
!python cloud/kaggle/run_stage5m_online_control.py
```
This executes the preregistered matrix:
- 3 CTC Development Backbones (`wav2vec2_base`, `data2vec_base`, `wav2vec2_100h`)
- 5 Acoustic Stress Conditions (`clean`, `noise_15db`, `noise_5db`, `babble_15db`, `reverb_t60_04`)
- 3 Active Adaptation Methods (`suta`, `dsuta`, `dmsuta`)
- 3 Stream Arrival Orderings (`ORDER_A`, `ORDER_B`, `ORDER_C`)
- 3 Seq2Seq Static Portability Controls (`whisper_base`, `distil_whisper_small`, `whisper_tiny`)

#### Step 7: Download the Stage 5M Results Bundle
Once execution completes, all CSVs, Markdown reports, agreement matrices, and checkpoints are packaged into:
`/kaggle/working/stage5m_results_bundle.zip`

1. Look in the right-hand panel under **Output**.
2. Click the three dots next to `stage5m_results_bundle.zip` $\to$ **Download**.
3. Extract directly into your local project root:
   ```bash
   unzip -o ~/Downloads/stage5m_results_bundle.zip -d .
   ```

---

### Methodological & Scientific Invariants Enforced

1. **Frozen Safety Policy**:
   $$\epsilon_R = 0.00\text{ pp} \ (0.0000), \quad \epsilon_G = +2.00\text{ pp} \ (0.0200), \quad \epsilon_D = +2.00\text{ pp} \ (0.0200)$$
   $$B = 1,000 \text{ resamples}, \quad \alpha = 0.05 \ (95\% \text{ confidence})$$
2. **Strict Online Label Isolation**:
   - Candidate-update acceptance decisions are made exclusively on the **Sentinel Panel ($N=30$ independent speakers)**.
   - Reference transcripts of the incoming evaluation stream are strictly quarantined via `LabelIsolationSanitizer` during adaptation.
3. **Primary Diagnostic Result — Operational vs. Retrospective Agreement**:
   - The runner logs both the operational gate decision (ACCEPT/REJECT) and the retrospective ground-truth outcome on the stream.
   - Specifically records **False Approvals** (cases where the operational gate accepted a candidate that was retrospectively harmful on the test stream) as a critical diagnostic of controller limitations.
4. **Seq2Seq Static-Only Boundary**:
   - `whisper_base`, `distil_whisper_small`, and `whisper_tiny` are evaluated strictly as static No-Adapt portability controls, preserving architectural honesty.
5. **GPU VRAM Safety**:
   - Between models and stages, explicit `del model`, `torch.cuda.empty_cache()`, and `gc.collect()` prevent out-of-memory errors on 16GB VRAM.
6. **Automatic Resumption & Checkpointing**:
   - If a cloud session disconnects or times out, re-running automatically resumes from the last completed checkpoint without re-running finished streams.
