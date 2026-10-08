# Protocol Amendment v1.1 – Multi‑Model Expansion

## 1. Historical (v1.0.0‑canonical) Protocol

- **Stage 2** – Static six‑model audit on L2‑ARCTIC (CTC + Seq2Seq models).  
- **Stage 3** – CTTA discovery **only on `facebook/wav2vec2-base-960h`**.  
- **Stage 4** – Stress/boundary characterization **only on `wav2vec2_base`**.  
- **Stage 5** – DSG qualification **only on `wav2vec2_base`**.  
- **Stage 6** – External validation on a mixture of CTC and Seq2Seq models (4 held‑out CTC back‑bones, 2 overlap CTC controls, 2 Seq2Seq baselines).

All results from Stages 3‑5 are **immutable** – they must remain part of the archival record and cannot be overwritten or re‑interpreted as if six models had been run.

---

## 2. New (v1.1.0‑model‑expansion) Protocol

### 2.1. Design Principles

- **Architecture‑aware CTTA** – only CTC models participate in the frame‑entropy CTTA methods (SUTA, DSUTA, DMSUTA).  
- **Seq2Seq models** are kept as **static‑only portability baselines** (no adaptation).  
- **Historical integrity** – Stage 3‑5 artifacts are **preserved unchanged** and referenced as *canonical* results.
- **Explicit model role registry** – a single source‑of‑truth JSON that classifies every model used in the project (development, overlap‑control, held‑out, Seq2Seq).
- **Clear separation** between development/qualification (Stages 3‑5) and final external validation (Stage 6).

### 2.2. Model Registry (`configs/model_role_registry.json`)

```json
{
  "stage2_development_models": {
    "ctc": [
      "wav2vec2_base",
      "data2vec_base",
      "wav2vec2_100h"
    ],
    "seq2seq": [
      "whisper_base",
      "distil_whisper_small",
      "whisper_tiny"
    ]
  },
  "stage6_validation_models": {
    "held_out_ctc": [
      "hubert_large",
      "xlsr_english",
      "wav2vec2_large_lv60",
      "wav2vec2_large_robust"
    ],
    "overlap_ctc_controls": [
      "wav2vec2_base",
      "data2vec_base"
    ],
    "seq2seq_static": [
      "whisper_base",
      "distil_whisper_small"
    ]
  }
}
```

*The keys are intentionally verbose to avoid any future ambiguity.*

### 2.3. Stage 3M – Multi‑Model CTTA Discovery

| Model (CTC) | Methods | Orders | Primary Metrics |
|---|---|---|---|
| `wav2vec2_base` | No‑Adapt, SUTA, DSUTA, DMSUTA | A, B, C | WER, Δ_R, Δ_D, max Δ_g |
| `data2vec_base` | Same as above | Same | Same |
| `wav2vec2_100h` | Same as above | Same | Same |

*Seq2Seq models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) are run **static‑only** on the same L2‑ARCTIC benchmark for architectural comparison.*

### 2.4. Stage 4M – Multi‑Model Stress Characterisation

- **Acoustic conditions** (identical to original Stage 4): Clean, Moderate Noise (15 dB SNR), Severe Noise (5 dB SNR), Moderate Babble (15 dB SNR), Reverberation (T₆₀ = 0.4 s).
- **CTC models**: the three from Stage 3M, each with No‑Adapt, SUTA, DSUTA, DMSUTA across the three stream orders.
- **Seq2Seq models**: static evaluation under the five acoustic conditions (no adaptation).
- **K‑sweep**: Full sweep `{1,4,5,10}` for Clean, Severe Noise, Reverberation; `K = 4` for the remaining conditions.

### 2.5. Stage 5M – Multi‑Model DSG Qualification

- **CTC models**: run the frozen DSG controller (ε_R = 0.01, ε_G = 0.02, ε_D = 0.02, B = 500) on the three development back‑bones.
- **Seq2Seq models**: static‑only portability analysis (no DSG candidate updates).
- **Outputs**: per‑model acceptance/rejection tables, UCB statistics, and a **DSG freeze certificate**.

### 2.6. Stage 6M – Final Cross‑Dataset Validation

- **Dataset**: Common Voice 27 (external held‑out dataset).
- **CTC models**: the four held‑out back‑bones **plus** the two overlap controls.
- **Seq2Seq models**: static baselines (`whisper_base`, `distil_whisper_small`).
- **No further tuning** – all thresholds, bootstraps, and controller logic are frozen from Stage 5M.
- **Reports**: final benchmark tables, subgroup‑harm heat‑maps, and a **held‑out‑model certificate**.

---

## 3. Leakage & Reproducibility Rules (Non‑Negotiable)

1. **No modification** of any artifact under `reports/stage3_*/`, `reports/stage4_*/`, `reports/stage5_*/`, or `reports/stage6_*/` that were generated with the original protocol.
2. **Never claim** that Whisper/Distil‑Whisper participated in SUTA/DSUTA/DMSUTA – the code enforces architecture checks and will error if attempted.
3. **All random seeds** (global seed = 42, bootstrap seed = 1234) are logged in each new report.
4. **Model identifiers** must match exactly the strings listed in the registry JSON; any deviation aborts the pipeline.
5. **Speaker‑cluster bootstrap** implementation (`src/dsg_ctta/online/sentinel.py`) is reused unchanged for all new stages.
6. **Threshold files** (`safety_gate_tolerances` in `configs/default_config.yaml`) remain frozen; new stages read them but never rewrite.

---

## 4. New Artifacts & Directory Structure

```
configs/
    model_role_registry.json   # <-- newly added
reports/
    protocol_amendment_v1.1.md # <-- this document
    stage3_multimodel_extension.md  (placeholder – to be filled after experiments)
    stage4_multimodel_extension.md
    stage5_multimodel_qualification.md
    stage6_multimodel_final_validation.md
    dsg_freeze_certificate.md
    heldout_model_certificate.md
```

All placeholder markdown files are created empty for now; the research team will populate them after running the new experiments.

---

## 5. Next Steps (Phase 0 – Audit Completed)

1. Commit the new `model_role_registry.json` and this amendment markdown to the repository.  
2. Verify that the existing CI pipeline does **not** attempt to re‑run any historical Stage 3‑5 code.
3. Create empty placeholder reports (see Section 4) so that downstream scripts can locate them.
4. When ready, proceed to **Phase 1** – generate the Stage 3M experimental design scripts.

---

*All changes respect the immutable historical record while establishing a clear, reproducible, and architecture‑aware extension of the DSG‑CTTA research workflow.*

---

**References**
- Original protocol version: `v1.0.0-canonical` (see `docs/protocol_freeze.md`).
- Code locations: 
  - CTTC adapters – `src/dsg_ctta/models/ctc_models.py`.
  - Seq2Seq adapters – `src/dsg_ctta/models/whisper_models.py`.
  - Safety gate tolerances – `configs/default_config.yaml`.
  - Sentinel implementation – `src/dsg_ctta/online/sentinel.py`.

---
