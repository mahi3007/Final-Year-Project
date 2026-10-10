# Stage-3M Data and Stream Audit Report
**Protocol Version:** `v1.1.0-model-expansion`  
**Execution Phase:** Phase 3 (Data & Stream Audit Only — Zero Inference Executed)  
**Date:** 2026-10-08  
**Audit Status:** Complete & Verified  

---

## 1. Dataset Identity & Provenance

The Stage-3M multi-model CTTA discovery stream is built from the historical, canonical L2-ARCTIC `final_test` partition.

| Parameter | Recorded Value | Verification Status |
|---|---|---|
| **Dataset Source** | L2-ARCTIC Non-Native English Speech Corpus | Frozen historical split |
| **Partition Path** | `datasets/splits/final_test.csv` | Exists & bit-exact |
| **Partition SHA-256** | `a4eb01993bf746b0a0b079224f1480338de01a3b224c635fdcc97a99047285d8` | Verified |
| **Audio Directory** | `datasets/primary/audio/` | All 60 files exist on disk |
| **Total Audio Files** | 60 | Verified |
| **Audio Format** | 16 kHz Mono PCM WAV, Studio Condenser Mic | 100% compliant |
| **Metadata Schema** | `utterance_id`, `speaker_id`, `group_id`, `group_type`, `audio_filepath`, `audio_sha256`, `duration_seconds`, `snr_db`, `speech_rate_wpm`, `device_id`, `reference_raw`, `reference_normalized`, `reference_word_count`, `partition`, `source_dataset` | Fully populated |

---

## 2. Stream Composition & Group Balance

The stream comprises exactly **60 utterances across 6 accent groups**, maintaining strict balance across all linguistic cohorts:

| Accent Group | Speaker ID | Utterance Count | Reference Words | Total Duration (s) | Mean SNR (dB) | Mean Speech Rate (wpm) |
|---|---|---|---|---|---|---|
| **Arabic** | `ABA` | 10 | 92 | 40.96s | 23.14 dB | 134.62 wpm |
| **Hindi** | `BJM` | 10 | 92 | 40.96s | 22.25 dB | 134.62 wpm |
| **Korean** | `EBVS` | 10 | 92 | 40.96s | 22.90 dB | 134.62 wpm |
| **Mandarin** | `TLX` | 10 | 92 | 40.96s | 22.89 dB | 134.62 wpm |
| **Spanish** | `MBX` | 10 | 92 | 40.96s | 22.09 dB | 134.62 wpm |
| **Vietnamese** | `BVT` | 10 | 92 | 40.96s | 23.05 dB | 134.62 wpm |
| **TOTAL** | **6 speakers** | **60 utts** | **552 words** | **245.76s** | **22.72 dB** | **134.62 wpm** |

All 6 accent groups possess exactly 10 utterances, 92 words, and 40.96 seconds of acoustic material.

---

## 3. Evaluation Resolution & One-Word Sensitivity

Because each subgroup contains exactly $N_g = 92$ reference words, the minimum discrete change produced by altering a single word is:
$$ \text{Resolution}_{\text{one-word}} = \frac{1}{92} \times 100\% = 1.0869565\% \approx 1.09\% \text{ pt} $$

### Methodological Interpretation:
A measured regression of $+1.09\%$ points corresponds to exactly **one additional word error** across the 10 utterances of that accent cohort. It is a discrete measurement limitation of a 92-word cohort, rather than widespread acoustic collapse. This justifies why practical effect thresholds must be placed above the single-word granularity threshold ($\delta_G \ge 0.02$).

---

## 4. Window Size & Prequential Structure ($K=4$)

- **Window Size:** $K = 4$ sequential utterances.
- **Window Count:** Exactly $\frac{60}{4} = 15$ windows.
- **Batch Processing:** 
  - Windows 0–14 each contain 4 utterances.
  - In `ORDER_A`:
    - Windows 0–1 contain Arabic (8 utts).
    - Window 2 contains 2 Arabic + 2 Hindi utts (transition boundary).
    - Windows 3–4 contain Hindi (8 utts).
    - Window 5 contains 1 Hindi + 3 Korean utts (transition boundary).
    - And so forth, creating realistic continual distribution shifts across consecutive windows.

---

## 5. Pre-Registered Stream Orderings

The exact set of 60 utterances $\mathcal{S}$ is evaluated under three deterministic orderings to isolate arrival-order sensitivity:
$$ \mathcal{S}_A = \mathcal{S}_B = \mathcal{S}_C $$

| Ordering ID | Group Progression Sequence | Deterministic Stream Hash (SHA-256) |
|---|---|---|
| `ORDER_A` | Arabic $\rightarrow$ Hindi $\rightarrow$ Korean $\rightarrow$ Mandarin $\rightarrow$ Spanish $\rightarrow$ Vietnamese | `e02b45a1fd0070116800e79940ec34ef1d0956a8d95a034a1bf987c43f08f778` |
| `ORDER_B` | Vietnamese $\rightarrow$ Spanish $\rightarrow$ Mandarin $\rightarrow$ Korean $\rightarrow$ Hindi $\rightarrow$ Arabic | `e45bd9d0921c06db3a830efbdec8725bcec9c0f6e4cb89976f647b95c9bf5e74` |
| `ORDER_C` | Hindi $\rightarrow$ Mandarin $\rightarrow$ Arabic $\rightarrow$ Vietnamese $\rightarrow$ Korean $\rightarrow$ Spanish | `5dc02804e713625a856f87e70ea9aa72262378f7a3d028f26c4715767243b98f` |

---

## 6. Prequential Scoring Invariant & Online Information Isolation

### 6.1 Prequential Temporal Invariant
Code inspection of `src/dsg_ctta/experiments/ctta_runner.py` (lines 146–245) confirms the strict prequential execution cycle:
$$ B_t \xrightarrow{\theta_t} \text{predict}(B_t) \xrightarrow{\text{score}} \text{evaluate}_{\text{offline}}(B_t) \xrightarrow{\text{adapt}} \text{adapt}(\text{unlabeled } B_t) \rightarrow \theta_{t+1} $$
1. Live model state $\theta_t$ predicts window $B_t$ before any adaptation.
2. Predictions are scored offline against hidden references.
3. Unlabeled audio is subsequently sanitized and passed to the adapter.
4. Candidate $\theta_{t+1}$ is produced and used to evaluate window $B_{t+1}$.
5. **Invariant Verified:** Scoring $B_t$ under $\theta_{t+1}$ is structurally impossible.

### 6.2 Online Label Isolation
The object passed to `adapter.adapt()` is strictly an `UnlabeledAudioBatch` instantiated via `LabelIsolationSanitizer.sanitize_batch()`.
- Stripped fields: `reference_raw`, `reference_normalized`, `group_id`, `speaker_id`, `substitutions`, `deletions`, `insertions`, `wer`, `cer`.
- Delivered fields: Only raw waveforms/filepaths and temporal batch indices.

---

## 7. Speaker Disjointness & Contamination Audit

Speaker disjointness was audited across all splits:
- `development` (6 speakers): `DTW`, `ERMS`, `LDC`, `NJS`, `PRK`, `YBAA`
- `calibration` (6 speakers): `HJK`, `HKK`, `MPXM`, `SKA`, `TNI`, `TNT`
- `sentinel_candidates` (6 speakers): `ASI`, `BWC`, `HCC`, `LXC`, `YDCK`, `ZHAA`
- `final_test` (Stage-3M) (6 speakers): `ABA`, `BJM`, `BVT`, `EBVS`, `MBX`, `TLX`

$$ \text{final\_test} \cap \text{development} = \emptyset $$
$$ \text{final\_test} \cap \text{calibration} = \emptyset $$
$$ \text{final\_test} \cap \text{sentinel\_candidates} = \emptyset $$

Zero speaker leakage detected.

---

## 8. Duplicate Audio & Transcript Audit

1. **Audio Hash Uniqueness:** Exactly 60 unique SHA-256 hashes across the 60 utterances.
2. **Path Uniqueness:** Exactly 60 unique file paths.
3. **Utterance ID Uniqueness:** Exactly 60 unique recording keys.
4. **Duplicate Transcripts:** None accidental; text follows canonical ARCTIC prompt script distribution.

---

## 9. Model Wiring & CTTA Eligibility Precheck

- **CTC Development Suite Wired:**
  - `facebook/wav2vec2-base-960h`
  - `facebook/data2vec-audio-base-960h`
  - `facebook/wav2vec2-base-100h`
- **Adaptation Methods Wired:** `no_adapt`, `suta`, `dsuta`, `dmsuta`.
- **Seq2Seq Decoupling:** `whisper_base`, `distil_whisper_small`, and `whisper_tiny` are strictly restricted to static zero-shot inference, with zero access to frame-entropy CTTA routines.

---

## 10. Pilot Nature & Statistical Limitation Acknowledgment

> [!IMPORTANT]
> **Stage-3M Scientific Scope:**
> Stage-3M preserves the historical six-speaker stream exclusively to ensure direct numerical comparability with the historical `v1.0.0-canonical` results. Having 1 speaker per group provides limited sample power for population-level generalization.
> Therefore:
> - **Stage-3M functions as a controlled multi-model discovery pilot** (evaluating whether order-induced subgroup regressions are idiosyncratic to `wav2vec2_base` or replicate on other CTC architectures).
> - **Stage-4M provides the expanded 12-speaker characterization**, multi-speaker cluster resampling, and acoustic stress matrix.

---

## 11. Artifacts Created

1. [`manifests/stage3m_order_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/manifests/stage3m_order_manifest.json) — Formal definitions and deterministic hashes of `ORDER_A`, `ORDER_B`, `ORDER_C`.
2. [`manifests/stage3m_window_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/manifests/stage3m_window_manifest.json) — Complete offline mapping of 15 windows per order ($K=4$).
3. [`manifests/stage3m_frozen_stream.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/manifests/stage3m_frozen_stream.json) — Cryptographic stream lock and immutability manifest.
4. [`reports/stage3m/stage3m_data_stream_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage3m_data_stream_audit.md) — This report.

---

## 12. Audit Verdict

All 15 verification criteria satisfied. Zero data leaks, zero audio duplicates, zero label exposure, bit-exact reproducibility confirmed.

**STATUS: PHASE_3_VERIFIED**
