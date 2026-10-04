# Stage 6: Cloud Virtual GPU Execution Guide
## Running the Six-Model DSG Benchmark on Free Cloud GPUs (Kaggle & Google Colab)

This directory contains the complete execution package for running **Stage 6 — Six-Model DSG Generalization Benchmark** on a free virtual GPU (NVIDIA Tesla P100 / T4).

---

### Why Use a Free Cloud GPU?

Evaluating 225 sequential prequential windows ($K=4$, 900 evaluation clips) against a 300-clip sentinel panel across multiple ASR models requires approximately **68,000 forward passes per model**.

| Environment | GPU | VRAM | Typical Speed per Model | Total 6-Model Runtime | Cost |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Local Laptop CPU** | CPU (Intel/AMD) | System RAM | $\approx 2.5 - 4.0$ hours | $\approx 12 - 18$ hours | Free |
| **Kaggle Notebooks (Recommended)** | **NVIDIA Tesla P100** | **16 GB** | **$\approx 25 - 35$ minutes** | **$\approx 2.0 - 2.5$ hours** | **Free (Zero cost)** |
| **Google Colab Free Tier** | **NVIDIA T4** | **16 GB** | **$\approx 30 - 45$ minutes** | **$\approx 2.5 - 3.0$ hours** | **Free (Zero cost)** |

---

### Architecture & Division of Responsibility

```
YOUR LOCAL PC (Antigravity IDE)
┌──────────────────────────────────────────────────┐
│ - Development, source code, configs, reports     │
│ - Stage 5E frozen baseline locks                 │
│ - Git repository & artifact analysis             │
└────────────────────────┬─────────────────────────┘
                         │ Git Push / Upload
                         ▼
FREE CLOUD VIRTUAL GPU (Kaggle / Colab)
┌──────────────────────────────────────────────────┐
│ - NVIDIA Tesla P100 GPU (16 GB VRAM)             │
│ - Fast PyTorch CUDA execution                    │
│ - High-speed model downloading (500+ Mbps)       │
│ - Automated checkpointing & memory purging       │
│ - Sequential multi-model evaluation              │
└────────────────────────┬─────────────────────────┘
                         │ Download stage6_results_bundle.zip
                         ▼
YOUR LOCAL PC (Antigravity IDE)
┌──────────────────────────────────────────────────┐
│ - Final CSVs in reports/stage6/                  │
│ - Full comparative analysis & manuscript tables  │
└──────────────────────────────────────────────────┘
```

---

### Quickstart Guide: Running on Kaggle (Step-by-Step)

#### Step 1: Open Kaggle Notebooks
1. Go to [https://www.kaggle.com/code](https://www.kaggle.com/code) and sign in (or create a free account).
2. Click **New Notebook** (top right).

#### Step 2: Enable Free Tesla P100 GPU
1. In the right-hand sidebar under **Notebook options**:
   - Click **Accelerator** $\to$ Select **GPU P100**.
   - Ensure **Internet** is toggled **ON**.

#### Step 3: Clone or Upload the Code
In the first notebook cell, clone your repository or upload the notebook:

```bash
# Clone the repository
!git clone <YOUR_GITHUB_REPO_URL> project
%cd project
```

*(Alternatively, you can upload `cloud/kaggle/run_stage6_kaggle.ipynb` directly to Kaggle via File $\to$ Upload Notebook).*

#### Step 4: Run the Environment Setup
In the next cell:
```python
!python cloud/kaggle/setup_kaggle.py
```
This automatically installs dependencies, checks the Tesla P100 GPU, validates audio paths, and verifies all 10 preflight integrity checks.

#### Step 5: Run the Benchmark
In the next cell:
```python
!python cloud/kaggle/run_six_model_benchmark.py
```

The runner executes models sequentially:
1. `wav2vec2_base`: Imports frozen Stage 5E metrics instantly.
2. `whisper_base`: Audits static No-Adapt; records CTTA as `INCOMPATIBLE`.
3. `hubert_base`: Evaluates No-Adapt, SUTA, DSUTA, DMSUTA, and DSG across 225 windows.
4. `data2vec_base`: Evaluates No-Adapt, SUTA, DSUTA, DMSUTA, and DSG across 225 windows.
5. `distil_whisper_small`: Audits static No-Adapt; records CTTA as `INCOMPATIBLE`.
6. `xlsr_english`: Evaluates No-Adapt, SUTA, DSUTA, DMSUTA, and DSG across 225 windows.

Between every model, `del model`, `torch.cuda.empty_cache()`, and `gc.collect()` purge VRAM, preventing out-of-memory errors.

#### Step 6: Download the Results
Once complete, the runner packages all results into `/kaggle/working/stage6_results_bundle.zip`.
- Look at the right-hand panel under **Output** $\to$ click the three dots on `stage6_results_bundle.zip` $\to$ **Download**.
- Extract `stage6_results_bundle.zip` directly into your local project directory:
  ```bash
  # Inside your local Antigravity terminal:
  unzip -o ~/Downloads/stage6_results_bundle.zip -d .
  ```

---

### Alternative: Running on Google Colab

1. Go to [https://colab.research.google.com](https://colab.research.google.com).
2. Click **File** $\to$ **Upload notebook** $\to$ Select `cloud/kaggle/run_stage6_kaggle.ipynb`.
3. Click **Runtime** $\to$ **Change runtime type** $\to$ Select **T4 GPU** $\to$ **Save**.
4. Clone your repository in the first cell and click **Runtime** $\to$ **Run all**.
5. When finished, Colab automatically makes `stage6_results_bundle.zip` available for download.

---

### Invariant & Scientific Guardrails Enforced

1. **Stage 5E Invariant:** `facebook/wav2vec2-base-960h` results are strictly locked and never overwritten.
2. **Seq2Seq Non-CTC Honesty:** `openai/whisper-base` and `distil-whisper/distil-small.en` are evaluated for static No-Adapt and legitimately marked `INCOMPATIBLE` for CTTA adaptation rather than fabricating numbers.
3. **Identical Datasets & Seeds:** Every model runs on the exact 900-clip external stream, 30-speaker sentinel panel, $B=1,000$ paired cluster bootstrap, $\epsilon_R=0.0000, \epsilon_G=0.0200, \epsilon_D=0.0200$, and seed $20261002$.
4. **Resumption & Checkpointing:** If a cloud session times out or disconnects, re-running the script automatically resumes from the last completed model/method without re-computing past windows.

---

### Stage 6.1: Running the Two-Model CTC Extension on Kaggle

To evaluate the two additional CTC models (`facebook/wav2vec2-large-960h-lv60` and `facebook/wav2vec2-large-robust-ft-libri-960h`):

1. In Kaggle, open a notebook with **GPU enabled (Tesla P100 or T4)** and **Internet ON**.
2. Run setup:
   ```python
   !python cloud/kaggle/setup_kaggle.py
   ```
3. Run Stage 6.1 Preflight Audit (verifies AutoModelForCTC, CTC logits, Shannon frame entropy, SUTA update, and DSG shadow isolation):
   ```python
   !python scripts/stage6/06_stage6_1_preflight_audit.py
   ```
4. Run the Stage 6.1 Extension across 225 prequential windows:
   ```python
   !python cloud/kaggle/run_stage6_1_extension.py
   ```
5. Download `stage6_1_results_bundle.zip` from `/kaggle/working/` (right panel Output).
6. In your local project, extract the bundle and merge results into the unified 8-model suite:
   ```bash
   unzip -o ~/Downloads/stage6_1_results_bundle.zip -d .
   python scripts/stage6/09_merge_stage6_1_into_stage6.py
   ```

