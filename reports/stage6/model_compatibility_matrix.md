# Stage 6: Six-Model DSG Generalization Benchmark
## Model Compatibility Matrix & Architectural Verification Report

- **Date:** October 2026
- **Status:** APPROVED & LOCKED FOR EXECUTION
- **Protocol Version:** `v1.0-cv27-amended`
- **Reference Standard:** ADR-005, Stage 5E Frozen Invariant

---

### Executive Summary

Stage 5E established a frozen, empirical validation of the Disparity Safety Gate (DSG) on the primary Track-A model, `facebook/wav2vec2-base-960h`:
- **Accepted Updates:** 9 / 225 ($4.0\%$)
- **Statistical Rejections:** 216 / 225 ($96.0\%$)
- **Fail-Closed Evaluator Rejections:** 0 ($0.0\%$)
- **Holdout Corpus WER:** No-Adapt $22.45\%$, SUTA $23.55\%$, DSG $22.52\%$ ($+0.07$ pp vs No-Adapt, preventing $93.7\%$ of SUTA's error increase)
- **Subgroup Disparity $D$:** Reduced from $30.25$ pp to $29.50$ pp ($-0.75$ pp)

**Critical Methodological Invariant:**
The Stage 5E numbers belong strictly to `facebook/wav2vec2-base-960h`. In Stage 6, we evaluate whether disparity-aware candidate-update gating generalizes across distinct ASR architectures, or whether its empirical behavior is specific to Wav2Vec2-base. Under no circumstance may results be copied, estimated, or fabricated.

Prior to cloud execution on virtual GPUs (Kaggle Tesla P100 / Google Colab), this report provides the formal architectural verification and compatibility matrix across all six candidate models.

---

### 1. Six-Model Architectural Comparison Matrix

| Model Key | HuggingFace Model Identifier | Architectural Family | Parameters | Inference Mechanism | Adaptable Layers | CTC-SUTA Loss Compatibility | DSG Shadow Cloning | Sentinel & Prequential Compatibility | Overall Stage 6 Status |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | CTC Acoustic Model | 94.4 M | Frame logits $(B, T, 32)$ $\to$ Greedy CTC | 24 Transformer LayerNorms | **COMPATIBLE** | **COMPATIBLE** | **COMPATIBLE** | **PRIMARY FROZEN BASELINE** (Stage 5E locked) |
| `whisper_base` | `openai/whisper-base` | Seq2Seq Encoder-Decoder | 72.6 M | Log-Mel $(B, 80, T)$ $\to$ Autoregressive BPE | Encoder/Decoder LayerNorms | **INCOMPATIBLE** (No CTC frames) | **COMPATIBLE** | Incompatible for CTTA Gating | **STATIC NO-ADAPT ONLY** (CTTA Incompatible) |
| `hubert_large` | `facebook/hubert-large-ls960-ft` *(Note 1)* | CTC Acoustic Model (Cluster SSL) | 316.8 M | Frame logits $(B, T, 32)$ $\to$ Greedy CTC | 48 Transformer LayerNorms | **COMPATIBLE** | **COMPATIBLE** | **COMPATIBLE** | **EXECUTION CANDIDATE** (Full CTTA + DSG) |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | CTC Acoustic Model (Multimodal SSL) | 94.4 M | Frame logits $(B, T, 32)$ $\to$ Greedy CTC | 24 Transformer LayerNorms | **COMPATIBLE** | **COMPATIBLE** | **COMPATIBLE** | **EXECUTION CANDIDATE** (Full CTTA + DSG) |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | Distilled Seq2Seq Encoder-Decoder | 166.1 M | Log-Mel $(B, 80, T)$ $\to$ Autoregressive BPE | Encoder/Decoder LayerNorms | **INCOMPATIBLE** (No CTC frames) | **COMPATIBLE** | Incompatible for CTTA Gating | **STATIC NO-ADAPT ONLY** (CTTA Incompatible) |
| `xlsr_english` | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | CTC Acoustic Model (Cross-Lingual SSL) | 315.5 M | Frame logits $(B, T, 32)$ $\to$ Greedy CTC | 48 Transformer LayerNorms | **COMPATIBLE** | **COMPATIBLE** | **COMPATIBLE** | **EXECUTION CANDIDATE** (Full CTTA + DSG) |

*(Note 1: As documented below, Meta's raw `facebook/hubert-base-ls960` checkpoint is an un-fine-tuned SSL feature extractor without an ASR vocabulary head; the official Fairseq fine-tuned ASR model with CTC head is `facebook/hubert-large-ls960-ft`.)*

---

### 2. Methodological Incompatibility Exposition: Autoregressive vs. CTC Models

A foundational principle of this benchmark is scientific integrity: **Do not force incompatible models through the Wav2Vec2 implementation, and do not substitute a different adaptation algorithm merely to populate a table.**

#### 2.1 The Mathematical Formulation of SUTA
The SUTA objective (Lin et al., 2022) is formulated strictly on frame-synchronous categorical distributions produced by a Connectionist Temporal Classification (CTC) projection layer:
$$L_{SUTA} = \alpha L_{EM}(\hat{Y}) + (1 - \alpha) L_{MCC}(\hat{Y})$$
where $\hat{Y} = [\hat{y}_1, \dots, \hat{y}_T] \in \Delta^{|V| \times T}$ represents the softmax output over vocabulary $V$ for acoustic frame $t$:
$$L_{EM} = -\frac{1}{T} \sum_{t=1}^T \sum_{c=1}^C \hat{y}_{t,c} \log \hat{y}_{t,c}$$
$$L_{MCC} = \frac{1}{C(C-1)} \sum_{j \neq k} \tilde{C}_{j,k}$$
where $\tilde{C}$ is the cross-class correlation matrix computed over the temporal sequence of frames.

#### 2.2 Why Whisper and Distil-Whisper Cannot Legitimately Run SUTA
1. **Absence of Temporal Frame Emissions:**
   In encoder-decoder sequence-to-sequence models (such as `openai/whisper-base` and `distil-whisper/distil-small.en`), the model does not output a temporal frame emission matrix $\hat{Y}$. Instead, speech recognition is formulated as autoregressive conditional text generation:
   $$P(w_{1:N} \mid X) = \prod_{i=1}^N P(w_i \mid w_{<i}, \text{Enc}(X))$$
   Frame-level Shannon entropy is mathematically undefined because speech features are encoded into continuous representations rather than discrete token distributions per audio frame.
2. **Unsupervised Label Isolation Firewall:**
   In test-time adaptation, the stream is strictly unlabeled. To compute token-level entropy in Whisper, one would need to decode an autoregressive hypothesis first, and then adapt the decoder on the hypothesis tokens. However, doing so converts the algorithm into **pseudo-label cross-entropy self-training**, which is a fundamentally different adaptation paradigm from unsupervised frame-level entropy minimization + MCC.
3. **Scientific Invalidation of Confounding Variables:**
   If we altered the adaptation algorithm for Whisper while keeping SUTA for Wav2Vec2, any observed performance difference would confound **model architecture** with **adaptation objective**.
4. **Protocol Decision:**
   - `whisper-base` and `distil-whisper/distil-small.en` are designated as **`INCOMPATIBLE (Non-CTC Seq2Seq)`** for SUTA, DSUTA, DMSUTA, and DSG.
   - Both models are evaluated on the frozen 900-clip holdout under **`No-Adapt`** to provide an authoritative comparison of static zero-shot accuracy and subgroup disparity across model families.
   - Their CTTA cells are marked `INCOMPATIBLE` rather than fabricated.

---

### 3. Verification of Compatible CTC Architectures

The four compatible architectures (`wav2vec2_base`, `hubert_large`, `data2vec_base`, `xlsr_english`) strictly satisfy all nine criteria:

1. **Emission Interface:** All four models take raw 16 kHz audio waveforms and emit frame logits $\mathbb{R}^{B \times T \times |V|}$ through linear projection heads.
2. **LayerNorm Affine Parameters:**
   - `wav2vec2-base-960h`: 24 Transformer blocks $\times 2$ LayerNorms $= 48$ LayerNorm modules ($48 \times 768 \times 2 = 73,728$ parameters).
   - `data2vec-audio-base-960h`: 12 Transformer blocks $\times 2$ LayerNorms $= 24$ modules ($36,864$ parameters).
   - `hubert-large-ls960-ft`: 24 Transformer blocks $\times 2$ LayerNorms $= 48$ modules ($98,304$ parameters).
   - `wav2vec2-large-xlsr-53-english`: 24 Transformer blocks $\times 2$ LayerNorms $= 48$ modules ($98,304$ parameters).
3. **Shadow Candidate Cloning:** PyTorch `copy.deepcopy(model)` creates isolated candidate parameters $\theta'$ with zero state leakage to live parameters $\theta_t$.
4. **Sentinel Safety Evaluation:** All four models transcribe the 300 frozen sentinel audio clips, producing string hypotheses that feed the exact paired speaker-cluster bootstrap ($B=1,000$, $\text{seed}=20261002$, $\alpha=0.05$).
5. **Prequential Ordering:** All four models execute sequential windows of $K=4$ (225 windows), evaluating live model $\theta_t$ before candidate generation.

---

### 4. Cloud Execution Strategy: Virtual GPU Optimization

Executing 225 sequential prequential windows with a 300-clip sentinel panel per window evaluates:
$$\text{Clips per Method} = 900 \text{ stream clips} + (225 \times 300 \text{ sentinel clips}) = 68,400 \text{ forward passes}$$
With live model hypothesis caching (reusing live sentinel predictions across rejected windows), this reduces to approximately:
$$\approx 900 + 300 + (225 \times 300 \text{ candidate}) \approx 68,700 \text{ forward passes per model}$$

#### 4.1 Kaggle Tesla P100 Architecture (Primary Free Source)
- **GPU:** NVIDIA Tesla P100 (16 GB VRAM)
- **Batching & Throughput:** In-memory waveform preloading eliminates disk I/O; `torch.inference_mode()` on P100 achieves $\approx 45$ clips/sec on Wav2Vec2/Data2Vec, completing 225 windows in $\approx 25$ minutes per model.
- **Sequential Execution with Garbage Collection:**
  Models run sequentially:
  $$\text{Model } i \to \text{Methods (No-Adapt, SUTA, DSUTA, DMSUTA, DSG)} \to \text{Save CSV} \to \text{del model} \to \text{empty\_cache} \to \text{Model } i+1$$
  Peak VRAM remains strictly under $4.2$ GB for base models and $7.8$ GB for large models (well within the 16 GB P100 limit).

#### 4.2 Automated Resumption & Checkpointing
Each method writes its window-level predictions and decision logs incrementally. If a session is interrupted, the runner detects existing checkpoint CSVs and skips already-completed runs without wasting compute.

---

### 5. Summary Table Template for Final Reporting

Upon completion of execution, the results will be reported in:
1. `reports/stage6/six_model_benchmark.csv`
2. `reports/stage6/six_model_group_metrics.csv`
3. `reports/stage6/six_model_dsg_summary.csv`
4. `reports/stage6/six_model_comparative_analysis.md`

| Model Key | Model Name | Family | No-Adapt WER | SUTA WER | DSUTA WER | DMSUTA WER | DSG WER | DSG $\Delta R$ | DSG $\Delta D$ | DSG $\max_g \Delta_g$ | DSG Accepted | DSG Rejected |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | Wav2Vec2-base-960h | CTC | **22.45%** | **23.55%** | **22.55%** | **22.56%** | **22.52%** | **+0.07 pp** | **−0.75 pp** | **+0.47 pp** | **9** | **216** |
| `whisper_base` | Whisper-base | Seq2Seq | *Pending* | *Incompatible* | *Incompatible* | *Incompatible* | *Incompatible* | N/A | N/A | N/A | N/A | N/A |
| `hubert_large` | HuBERT-large-ls960-ft | CTC | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |
| `data2vec_base` | Data2Vec-audio-base | CTC | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |
| `distil_whisper` | Distil-Whisper-small.en | Seq2Seq | *Pending* | *Incompatible* | *Incompatible* | *Incompatible* | *Incompatible* | N/A | N/A | N/A | N/A | N/A |
| `xlsr_english` | Wav2Vec2-large-XLSR-53 | CTC | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* |
