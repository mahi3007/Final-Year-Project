# Model Holdout Certificate
**Protocol:** `v1.1.0-model-expansion`  
**Certification Scope:** Stage 6 Validation Model Suite  
**Generated:** 2026-10-08  

---

## 1. Formal Certification Rule

A model is formally certified as **`HELD_OUT_CTC`** if and only if it satisfies all of the following non-negotiable criteria:
1. **Zero Development Exposure:** The model was never evaluated in Stage 2 static development, Stage 3M CTTA dynamics discovery, or Stage 4M acoustic stress characterization.
2. **Zero Calibration Exposure:** The model was never used to compute word granularity, variance metrics, or calibrate practical effect thresholds ($\delta_G = 0.02, \delta_D = 0.02$).
3. **Zero Controller Exposure:** The model was never used in Stage 5M DSG qualification, sentinel panel selection, or threshold tuning.
4. **Frozen Controller Evaluation:** The model is evaluated in Stage 6 using the pre-frozen DSG controller without post-hoc modifications.

Models violating any of conditions 1–3 are classified as **`OVERLAP_CTC_CONTROL`**.

---

## 2. Certified Model Categorization

### Category A: Genuinely Held-Out CTC Models (`holdout_eligible: true`)
These models provide unbiased scientific evidence for **unseen-backbone generalization**:

| Model Key | Canonical Hugging Face Model ID | Parameters | Architecture |
|---|---|---|---|
| `hubert_large` | `facebook/hubert-large-ls960-ft` | 316.8M | Acoustic Cluster SSL CTC |
| `xlsr_english` | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | 315.5M | Multilingual Cross-Lingual CTC |
| `wav2vec2_large_lv60` | `facebook/wav2vec2-large-960h-lv60` | 315.5M | Pretrained Libri-Light 60k CTC |
| `wav2vec2_large_robust` | `facebook/wav2vec2-large-robust-ft-libri-960h` | 315.5M | Multi-Domain Robust Pretrained CTC |

### Category B: Overlap / Control CTC Models (`holdout_eligible: false`)
These models provide scientific evidence for **cross-dataset replication** (domain shift from L2-ARCTIC to Common Voice 27 on known development architectures):

| Model Key | Canonical Hugging Face Model ID | Parameters | Development Predecessor |
|---|---|---|---|
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | 94.4M | Primary Track A Baseline |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | 94.4M | Secondary Multimodal Baseline |

### Category C: Static-Only Seq2Seq Portability Baselines
These models are mathematically incompatible with frame-entropy CTTA objectives and participate strictly as zero-shot static controls:

| Model Key | Canonical Hugging Face Model ID | Parameters | CTTA Status |
|---|---|---|---|
| `whisper_base` | `openai/whisper-base` | 72.6M | `INCOMPATIBLE_NON_CTC` |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | 166.2M | `INCOMPATIBLE_NON_CTC` |

---

## 3. Certification Attestation

The undersigned system certifies that no held-out model has been exposed to development data, calibration routines, or gate tuning. The boundary between cross-model generalization and cross-dataset replication is formally maintained across all code, configurations, and reports.

**Status:** **CERTIFIED AND LOCKED**
