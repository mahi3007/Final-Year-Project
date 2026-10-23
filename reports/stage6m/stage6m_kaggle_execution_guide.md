# Stage 6M: Kaggle Virtual GPU Execution Guide (Path B)

**Document Identifier:** `reports/stage6m/stage6m_kaggle_execution_guide.md`  
**Governing Standard:** ADR-005  
**Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
**Target Hardware:** Kaggle Free Virtual GPU (NVIDIA Tesla P100 / T4, 16 GB VRAM)  
**Target Workload:** Confirmatory Cohort 2 (468 speakers, 7,020 audio clips, 1,755 streaming windows, 1,754 candidate updates)  

---

## 1. Why Execute Path B on Kaggle?

The complete confirmatory benchmark evaluates 1,755 sequential streaming windows with continuous test-time adaptation and sequential sentinel panel screening ($K=4$, $U=1,754$ candidate evaluations).
- **Host Laptop (CPU-only):** At ~220 ms per audio forward pass and ~450 ms per SUTA adaptation step, the 533,220 total clip decodings across the 3 arms require **~32.8 CPU hours**.
- **Kaggle Cloud Virtual GPU (Tesla P100):** With high parallel throughput (45 ms per clip decoding, batched inference over 16-32 clips), the entire workload finishes in **~1.5 to 2.5 hours**, utilizing Kaggle's free 30 hours/week GPU quota at zero cost.

---

## 2. Step-by-Step Instructions to Run on Kaggle

### Step 1: Open Kaggle & Create New Notebook
1. Navigate to [https://www.kaggle.com/code](https://www.kaggle.com/code).
2. Sign in to your Kaggle account (free).
3. Click **"New Notebook"** in the top right.

### Step 2: Configure Free GPU Accelerator
1. In the right-hand panel under **Notebook options**:
   - Click **Accelerator** $\rightarrow$ Select **GPU P100** (or **GPU T4 x2**).
   - Scroll down to **Internet** $\rightarrow$ Toggle **ON** (required to load Hugging Face models and packages).

### Step 3: Upload or Clone the Notebook
You have two easy options:

#### Option A: Direct Notebook Upload (Recommended)
1. In the Kaggle notebook top menu, click **File $\rightarrow$ Upload Notebook**.
2. Select [`cloud/kaggle/run_stage6m_cohort2_kaggle.ipynb`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/cloud/kaggle/run_stage6m_cohort2_kaggle.ipynb) from your local computer.

#### Option B: Clone via Git
In the first code cell:
```bash
!git clone https://github.com/mahi3007/Final-Year-Project.git project
%cd project
```

### Step 4: Execute the Confirmatory Benchmark
Run the notebook cells sequentially:
1. **Cell 1:** Hardware verification (`torch.cuda.is_available()` returns `True`, displaying Tesla P100 16 GB VRAM).
2. **Cell 2:** Dependency installation (`transformers`, `soundfile`, `editdistance`, `statsmodels`).
3. **Cell 3:** Cryptographic lock check (verifies SHA-256 hash `610649e8f634e21c0236f18e9461f865721c7864703fb87d597df7968f912895`).
4. **Cell 4:** Launch the confirmatory runner:
   ```bash
   !python cloud/kaggle/run_stage6m_cohort2_benchmark.py
   ```
5. **Cell 5:** Compress output artifacts into `stage6m_confirmatory_results.tar.gz`.

### Step 5: Download Confirmatory Results
1. In the right-hand panel under **Output** (`/kaggle/working/`), find `stage6m_confirmatory_results.tar.gz`.
2. Click the three dots $\rightarrow$ **Download**.
3. Unpack into your local project directory:
   ```powershell
   tar -xzvf stage6m_confirmatory_results.tar.gz
   ```

---

## 3. Comparison of Path A vs. Path B

| Feature | Path A (Local Host Execution) | Path B (Kaggle Cloud GPU Execution) |
| :--- | :--- | :--- |
| **Cohort** | Cohort 1 (`stage5_external_eval.csv`) | Cohort 2 (`stage6m_locked_candidate_manifest.json`) |
| **Speakers** | 60 independent speakers (10/stratum) | 468 independent speakers (78/stratum) |
| **Audio Clips** | 900 physical clips | 7,020 physical clips |
| **Streaming Windows** | 225 windows ($K=4$) | 1,755 windows ($K=4$) |
| **Hardware** | Host Local CPU | NVIDIA Tesla P100 (16 GB VRAM) |
| **Execution Command** | `python scripts/run_stage6m_physical_cohort1.py` | `python cloud/kaggle/run_stage6m_cohort2_benchmark.py` |
| **Scientific Role** | Immediate physical replication & multi-step trajectory verification | Full confirmatory blind sample size expansion (Option A) |
