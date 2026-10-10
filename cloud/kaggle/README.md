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

### Quickstart Guide: Running on Kaggle (Step-by-Step)

#### Step 1: Open Kaggle Notebooks
1. Go to [https://www.kaggle.com/code](https://www.kaggle.com/code) and sign in.
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
*(Alternatively, you can upload `cloud/kaggle/run_stage5_and_stage6_kaggle.ipynb` directly via File $\to$ Upload Notebook).*

#### Step 4: Run the Environment & Audio Setup
In the next cell:
```python
!python cloud/kaggle/setup_kaggle.py
```
This automatically installs dependencies, checks the Tesla P100 GPU, validates audio assets, and executes preflight integrity checks.

#### Step 5: Execute the Benchmarks

You have several flexible execution options:

##### Option A: Run Everything (Stage 5M + Stage 6 + Stage 6.1)
```python
!python cloud/kaggle/run_stage5_and_stage6.py --stage all
```

##### Option B: Run Stage 5M Only (Closed-Loop Online Control Suite)
```python
!python cloud/kaggle/run_stage5_and_stage6.py --stage 5m
```

##### Option C: Run Stage 6 Only (Six-Model Benchmark)
```python
!python cloud/kaggle/run_stage5_and_stage6.py --stage 6
```

##### Option D: Fast Smoke Test (Validates Stage 5M Sentinel Gate in ~30s)
```python
!python cloud/kaggle/run_stage5m_online_control.py --smoke-test
```

#### Step 6: Download the Results Bundle
Once execution completes, all CSVs, Markdown reports, and checkpoint records are automatically packaged into:
`/kaggle/working/stage5_stage6_results_bundle.zip`

1. Look at the right-hand sidebar under **Output**.
2. Click the three dots next to `stage5_stage6_results_bundle.zip` $\to$ **Download**.
3. Extract directly into your local repository:
   ```bash
   unzip -o ~/Downloads/stage5_stage6_results_bundle.zip -d .
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
