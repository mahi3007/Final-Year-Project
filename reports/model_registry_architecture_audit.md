# Model Registry & Architecture Audit Report
**Protocol Version:** `v1.1.0-model-expansion`  
**Execution Phase:** Phase 2 (Model Registry + Architecture Audit)  
**Status:** Audit Complete  
**Date:** 2026-10-08  

---

## 1. Executive Summary & Objective

In accordance with Protocol Amendment `v1.1.0-model-expansion`, this audit establishes an exact, machine-readable, and publication-grade model role taxonomy. The core scientific requirement is **zero model role ambiguity**, strictly separating:
1. **CTC Development Suite:** Models participating in Stage 2 static baseline, Stage 3M CTTA discovery, Stage 4M stress characterization, and Stage 5M DSG qualification.
2. **Seq2Seq Static Portability Suite:** Autoregressive models evaluated exclusively in zero-shot static conditions due to mathematical incompatibility with CTC frame-entropy adaptation.
3. **Stage 6 Overlap / Control CTC Models:** Backbones tested for cross-dataset replication on Common Voice 27.
4. **Stage 6 Held-Out CTC Models:** Truly unseen backbones never touched during development, calibration, or threshold tuning, providing unbiased cross-model generalization evidence.

---

## 2. Complete Model Inventory & Role Matrix

| Model Key | Canonical Hugging Face Model ID | Architecture Class | Parameter Count | CTTA Eligibility | Development Role (Stage 2–5) | Validation Role (Stage 6) | Holdout Eligible |
|---|---|---|---|---|---|---|---|
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | CTC (`Wav2Vec2ForCTC`) | 94,396,448 | **COMPATIBLE** | `PRIMARY_CTC` | `OVERLAP_CTC_CONTROL` | ❌ `false` |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | CTC (`Data2VecAudioForCTC`) | 94,396,448 | **COMPATIBLE** | `SECONDARY_CTC` | `OVERLAP_CTC_CONTROL` | ❌ `false` |
| `wav2vec2_100h` | `facebook/wav2vec2-base-100h` | CTC (`Wav2Vec2ForCTC`) | 94,396,448 | **COMPATIBLE** | `SECONDARY_CTC` | Not in Stage 6 | ❌ `false` |
| `whisper_base` | `openai/whisper-base` | Seq2Seq (`WhisperForConditionalGeneration`) | 72,593,920 | **INCOMPATIBLE_NON_CTC** | `SEQ2SEQ_STATIC` | `SEQ2SEQ_STATIC_PORTABILITY` | ❌ `false` |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | Seq2Seq (`WhisperForConditionalGeneration`) | 166,156,288 | **INCOMPATIBLE_NON_CTC** | `SEQ2SEQ_STATIC` | `SEQ2SEQ_STATIC_PORTABILITY` | ❌ `false` |
| `whisper_tiny` | `openai/whisper-tiny` | Seq2Seq (`WhisperForConditionalGeneration`) | 37,760,640 | **INCOMPATIBLE_NON_CTC** | `SEQ2SEQ_STATIC` | Not in Stage 6 | ❌ `false` |
| `hubert_large` | `facebook/hubert-large-ls960-ft` | CTC (`HubertForCTC`) | 316,826,400 | **COMPATIBLE** | Excluded | `HELD_OUT_CTC` | ✅ `true` |
| `xlsr_english` | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | CTC (`Wav2Vec2ForCTC`) | 315,471,520 | **COMPATIBLE** | Excluded | `HELD_OUT_CTC` | ✅ `true` |
| `wav2vec2_large_lv60` | `facebook/wav2vec2-large-960h-lv60` | CTC (`Wav2Vec2ForCTC`) | 315,471,520 | **COMPATIBLE** | Excluded | `HELD_OUT_CTC` | ✅ `true` |
| `wav2vec2_large_robust` | `facebook/wav2vec2-large-robust-ft-libri-960h` | CTC (`Wav2Vec2ForCTC`) | 315,471,520 | **COMPATIBLE** | Excluded | `HELD_OUT_CTC` | ✅ `true` |

---

## 3. Mathematical Basis for Architecture-Aware CTTA Eligibility

### 3.1 CTC Models (Eligible for SUTA / DSUTA / DMSUTA)
CTC models produce frame-synchronous categorical emissions:
$$ p(y_t \mid X) = \text{Softmax}\left(\frac{\mathbf{z}_t}{T}\right) \in \Delta^{|\mathcal{V}|}, \quad t = 1, \dots, T $$
The adaptation objective directly minimizes frame-level Shannon entropy and cross-class correlation (Minimum Class Confusion):
$$ \mathcal{L}_{\text{EM}} = -\frac{1}{T}\sum_{t=1}^T \sum_{k=1}^{|\mathcal{V}|} p_{t,k} \log p_{t,k} $$
Because $\mathbf{z}_t$ is computed in parallel across frames and conditioned purely on acoustic representations, gradient updates with respect to LayerNorm affine parameters ($\gamma, \beta$) are mathematically well-defined and computationally sound.

### 3.2 Autoregressive Seq2Seq Models (Mathematically Incompatible)
In encoder-decoder architectures (`whisper_base`, `distil_whisper_small`, `whisper_tiny`), token emissions are non-frame-synchronous and conditionally dependent on previously generated tokens:
$$ p(y_u \mid y_{<u}, X) = \text{Softmax}\left(\mathbf{W}_{\text{dec}} \mathbf{h}_u^{\text{dec}}\right) $$
There is no frame-level categorical distribution $\mathbf{p}_t$ over time. Applying frame-entropy minimization or CTC class confusion loss to an autoregressive model without ground truth tokens triggers degenerate loop repetitions or silence emission collapses.
- **Protocol Decision:** All Seq2Seq models participate strictly as **static zero-shot portability controls**. No pseudo-adaptation numbers are ever fabricated.

---

## 4. Rigorous Holdout Separation

### 4.1 Genuinely Held-Out CTC Models (`holdout_eligible: true`)
The following four backbones were **never** used in:
- Stage 2 baseline calibration
- Stage 3M CTTA dynamics discovery
- Stage 4M acoustic stress calibration or $\delta_G / \delta_D$ threshold calculation
- Stage 5M DSG gate tuning or sentinel panel qualification

1. `facebook/hubert-large-ls960-ft` (316.8M params, acoustic cluster SSL)
2. `jonatasgrosman/wav2vec2-large-xlsr-53-english` (315.5M params, multilingual cross-lingual SSL)
3. `facebook/wav2vec2-large-960h-lv60` (315.5M params, Libri-Light 60k pretraining, commit `8e7d14742e8f98c6bbb24e5231406af321a8f9ce`)
4. `facebook/wav2vec2-large-robust-ft-libri-960h` (315.5M params, multi-domain robust pretraining, commit `5d28473cc25ef7b338c9f731fe55626c4b082f58`)

### 4.2 Overlap / Replication Controls (`holdout_eligible: false`)
The backbones `wav2vec2_base` and `data2vec_base` participated in development (Stages 2–5). When evaluated on Common Voice 27 in Stage 6, they evaluate **cross-dataset replication** (testing whether the DSG gate functions when the domain shifts from L2-ARCTIC to Common Voice 27 on known architectures). They do **not** claim to test unseen-model generalization.

---

## 5. Checkpoint Identifiers and Aliases

- **HuBERT Checkpoint Audit:** The repository uses `facebook/hubert-large-ls960-ft` (the fine-tuned CTC ASR checkpoint). The alias `hubert_base` in `MODEL_CATALOG` maps directly to this checkpoint to preserve historical backward compatibility.
- **Stage 2 Low-Resource Checkpoint:** `facebook/wav2vec2-base-100h` is preserved verbatim as recorded in Stage 2 historical files.
- **Commit Lineage:** Large models specify verified Hugging Face revision commit SHAs for bit-exact reproducibility.

---

## 6. Audit Verdict

- **Total Models Registered:** 10
- **CTC Development Suite:** 3 models (`wav2vec2_base`, `data2vec_base`, `wav2vec2_100h`)
- **Seq2Seq Static Suite:** 3 models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`)
- **Held-Out CTC Suite:** 4 models (`hubert_large`, `xlsr_english`, `wav2vec2_large_lv60`, `wav2vec2_large_robust`)
- **Overlap CTC Controls:** 2 models (`wav2vec2_base`, `data2vec_base`)
- **Ambiguous or Unknown Models:** 0

**STATUS: PHASE_2_VERIFIED**
