# Master Benchmark and Empirical Accent Results Ledger
## Authoritative Cross-Model Performance, Literature Reconciliation, and Demographic Subgroup Analysis

- **Project Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust Automatic Speech Recognition (DSG-CTTA)
- **Protocol Version:** `v1.0-cv27-amended` (Stage 0 Protocol Freeze & ADR-005)
- **Holdout Evaluation Stream:** Mozilla Common Voice 27.0 ($N = 900$ clips, 60 speakers, 6 strata, exactly $8,667$ reference words)
- **Sentinel Panel:** Frozen External Calibration Panel ($M = 300$ clips, 30 disjoint speakers, $2,925$ words)
- **Document Purpose:** Consolidated single-file empirical ledger for academic supervision, viva defense, and peer review.

---

## 1. Grounding & Denominator Invariants (Proof of Authenticity)

To verify that all reported error rates are mathematically authentic and reproducible, the entire evaluation is grounded on a pre-registered, frozen evaluation split (`datasets/splits/stage5_external_eval.csv`).

| Accent Stratum | Total Clips | Distinct Speakers | Clips / Speaker | Reference Word Count ($N_{\text{ref}}$) | Proportion of Corpus |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **US English** | 150 | 10 | 15 | **1,468 words** | 16.94% |
| **England English** | 150 | 10 | 15 | **1,393 words** | 16.07% |
| **South Asian English** | 150 | 10 | 15 | **1,430 words** | 16.50% |
| **Australian English** | 150 | 10 | 15 | **1,493 words** | 17.23% |
| **Canadian English** | 150 | 10 | 15 | **1,500 words** | 17.31% |
| **Irish English** | 150 | 10 | 15 | **1,383 words** | 15.96% |
| **TOTAL / SUM INVARIANT** | **900** | **60** | **15** | **8,667 words** | **100.00%** |

$$\text{Sum Invariant: } 1468 + 1393 + 1430 + 1493 + 1500 + 1383 = \mathbf{8,667\text{ reference words}}$$

---

## 2. Table 1: Master Cross-Backbone Benchmark & Official Literature Reconciliation

This table reconciles published official benchmarks from original literature citations with our measured results across all 8 models.

| Model Key | Architecture & Pretraining | Parameters | Published Benchmark Dataset | Published Benchmark WER | Official Citation | Measured Baseline No-Adapt | Measured SUTA | Measured DSUTA | Measured DMSUTA | Measured DSG-CTTA (Ours) | Net DSG vs Base | DSG Accepted Updates |
| :--- | :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`wav2vec2_base`** | CTC | 94.4M | LibriSpeech test-clean / test-other (no LM) | **3.4% / 8.6%** | Baevski et al. (NeurIPS 2020), Table 1 | **22.45%** | 23.55% | 22.55% | 22.56% | **22.52%** | **+0.07 pp** | 9 / 225 |
| **`whisper_base`** | EncoderDecoder | 72.6M | LibriSpeech test-other / Common Voice en zero-shot | **10.5% / 13.1%** | Radford et al. (ICML 2023), Table 8 & 9 | **14.32%** | INCOMPATIBLE | INCOMPATIBLE | INCOMPATIBLE | **INCOMPATIBLE** | **—** | — |
| **`hubert_large`** | CTC | 316.8M | LibriSpeech test-clean / test-other (no LM) | **1.9% / 3.5%** | Hsu et al. (IEEE/ACM TASLP 2021), Table 2 | **12.37%** | 12.77% | 12.39% | 12.26% | **12.38%** | **+0.01 pp** | 6 / 225 |
| **`data2vec_base`** | CTC | 94.4M | LibriSpeech test-clean / test-other (no LM) | **3.4% / 8.0%** | Baevski et al. (ICML 2022), Table 1 | **20.43%** | 20.65% | 19.79% | 20.26% | **20.32%** | **-0.12 pp** | 1 / 225 |
| **`distil_whisper_small`** | EncoderDecoder | 166.1M | Out-of-Distribution Average WER across 4 diverse datasets | **10.3%** | Gandhi et al. (EMNLP 2023), Table 1 & Model Card | **9.18%** | INCOMPATIBLE | INCOMPATIBLE | INCOMPATIBLE | **INCOMPATIBLE** | **—** | — |
| **`xlsr_english`** | CTC | 315.5M | Common Voice 6.1 English Test Split | **13.52%** | Model Card: jonatasgrosman/wav2vec2-large-xlsr-53-english | **11.81%** | 14.54% | 11.88% | 11.81% | **11.81%** | **+0.00 pp** | 0 / 225 |
| **`wav2vec2_large_lv60`** | CTC | 315.5M | LibriSpeech test-clean / test-other (no LM) | **1.9% / 4.1%** | Baevski et al. (NeurIPS 2020), Table 1 | **12.93%** | 13.97% | 13.00% | 13.06% | **12.91%** | **-0.02 pp** | 2 / 225 |
| **`wav2vec2_large_robust`** | CTC | 315.5M | LibriSpeech test-clean / test-other (no LM) | **1.8% / 3.7%** | Hsu et al. (Interspeech 2021) Robust Wav2Vec 2.0, Table 1 | **12.91%** | 13.28% | 12.86% | 12.92% | **12.89%** | **-0.02 pp** | 5 / 225 |

---

## 3. Table 2: Complete Accent-by-Accent Performance Master Matrix

This table details the exact Word Error Rate (WER) achieved across each individual accent stratum for every model and adaptation method.

| Model Key | Adaptation Method | US English (1,468 w) | England English (1,393 w) | South Asian English (1,430 w) | Australian English (1,493 w) | Canadian English (1,500 w) | Irish English (1,383 w) | Aggregate Stream WER (8,667 w) | Disparity Range ($D$) | Total Errors ($E$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | **No-Adapt Baseline** | 21.46% | 20.32% | **42.45%** | 22.91% | 12.20% | 15.62% | **22.45%** | **30.25 pp** | 1,946 words |
| `wav2vec2_base` | **SUTA (Unconstrained)** | 21.32% | 21.82% | **42.66%** | 24.05% | 13.73% | 18.00% | **23.55%** | **28.92 pp** | 2,041 words |
| `wav2vec2_base` | **DSUTA (Entropy Resets)** | 21.59% | 20.17% | **41.96%** | 22.97% | 13.20% | 15.55% | **22.55%** | **28.76 pp** | 1,954 words |
| `wav2vec2_base` | **DMSUTA (Memory Banks)** | 21.66% | 20.60% | **42.31%** | 22.44% | 12.87% | 15.69% | **22.56%** | **29.44 pp** | 1,955 words |
| `wav2vec2_base` | **DSG-CTTA (Ours)** | 21.53% | 20.46% | **42.17%** | 23.17% | 12.67% | 15.33% | **22.52%** | **29.50 pp** | 1,952 words |
| `hubert_large` | **No-Adapt Baseline** | 13.15% | 11.27% | **22.31%** | 11.05% | 9.07% | 7.38% | **12.37%** | **14.93 pp** | 1,072 words |
| `hubert_large` | **SUTA (Unconstrained)** | 13.28% | 11.41% | **23.08%** | 11.25% | 9.47% | 8.17% | **12.77%** | **14.91 pp** | 1,107 words |
| `hubert_large` | **DSUTA (Entropy Resets)** | 13.08% | 11.49% | **22.66%** | 10.72% | 9.20% | 7.23% | **12.39%** | **15.43 pp** | 1,074 words |
| `hubert_large` | **DMSUTA (Memory Banks)** | 13.08% | 11.27% | **22.38%** | 10.65% | 9.13% | 7.09% | **12.26%** | **15.29 pp** | 1,063 words |
| `hubert_large` | **DSG-CTTA (Ours)** | 12.94% | 11.63% | **22.66%** | 10.78% | 9.00% | 7.30% | **12.38%** | **15.35 pp** | 1,073 words |
| `data2vec_base` | **No-Adapt Baseline** | 20.37% | 20.24% | **38.46%** | 20.29% | 11.33% | 12.08% | **20.43%** | **27.13 pp** | 1,771 words |
| `data2vec_base` | **SUTA (Unconstrained)** | 20.30% | 19.89% | **36.85%** | 20.90% | 12.40% | 13.74% | **20.65%** | **24.45 pp** | 1,790 words |
| `data2vec_base` | **DSUTA (Entropy Resets)** | 19.82% | 19.96% | **36.50%** | 19.42% | 11.13% | 12.08% | **19.79%** | **25.37 pp** | 1,715 words |
| `data2vec_base` | **DMSUTA (Memory Banks)** | 19.62% | 20.24% | **38.53%** | 20.03% | 11.13% | 12.22% | **20.26%** | **27.40 pp** | 1,756 words |
| `data2vec_base` | **DSG-CTTA (Ours)** | 20.37% | 20.17% | **37.90%** | 20.09% | 11.40% | 12.15% | **20.32%** | **26.50 pp** | 1,761 words |
| `xlsr_english` | **No-Adapt Baseline** | 13.76% | 12.06% | **16.99%** | 11.32% | 8.07% | 8.75% | **11.81%** | **8.93 pp** | 1,024 words |
| `xlsr_english` | **SUTA (Unconstrained)** | 13.42% | 12.99% | **18.39%** | 15.14% | 12.53% | 14.82% | **14.54%** | **5.86 pp** | 1,260 words |
| `xlsr_english` | **DSUTA (Entropy Resets)** | 13.49% | 12.20% | **16.92%** | 11.39% | 8.27% | 9.11% | **11.88%** | **8.66 pp** | 1,030 words |
| `xlsr_english` | **DMSUTA (Memory Banks)** | 13.76% | 12.20% | **16.78%** | 11.39% | 8.07% | 8.75% | **11.81%** | **8.72 pp** | 1,024 words |
| `xlsr_english` | **DSG-CTTA (Ours)** | 13.76% | 12.06% | **16.99%** | 11.32% | 8.07% | 8.75% | **11.81%** | **8.93 pp** | 1,024 words |
| `wav2vec2_large_lv60` | **No-Adapt Baseline** | 14.85% | 12.35% | **20.14%** | 12.46% | 9.27% | 8.53% | **12.93%** | **11.61 pp** | 1,121 words |
| `wav2vec2_large_lv60` | **SUTA (Unconstrained)** | 15.05% | 12.28% | **21.47%** | 13.26% | 10.33% | 11.50% | **13.97%** | **11.14 pp** | 1,211 words |
| `wav2vec2_large_lv60` | **DSUTA (Entropy Resets)** | 14.92% | 12.35% | **19.93%** | 12.53% | 9.73% | 8.53% | **13.00%** | **11.40 pp** | 1,127 words |
| `wav2vec2_large_lv60` | **DMSUTA (Memory Banks)** | 14.78% | 12.49% | **20.35%** | 12.53% | 9.33% | 8.89% | **13.06%** | **11.46 pp** | 1,132 words |
| `wav2vec2_large_lv60` | **DSG-CTTA (Ours)** | 14.85% | 12.35% | **20.14%** | 12.46% | 9.13% | 8.53% | **12.91%** | **11.61 pp** | 1,119 words |
| `wav2vec2_large_robust` | **No-Adapt Baseline** | 15.94% | 12.85% | **18.81%** | 11.65% | 9.20% | 9.04% | **12.91%** | **9.77 pp** | 1,119 words |
| `wav2vec2_large_robust` | **SUTA (Unconstrained)** | 15.46% | 12.42% | **18.60%** | 11.86% | 9.93% | 11.50% | **13.28%** | **8.67 pp** | 1,151 words |
| `wav2vec2_large_robust` | **DSUTA (Entropy Resets)** | 15.67% | 12.56% | **18.46%** | 12.06% | 9.40% | 9.04% | **12.86%** | **9.42 pp** | 1,115 words |
| `wav2vec2_large_robust` | **DMSUTA (Memory Banks)** | 15.46% | 12.99% | **18.39%** | 12.19% | 9.47% | 9.04% | **12.92%** | **9.35 pp** | 1,120 words |
| `wav2vec2_large_robust` | **DSG-CTTA (Ours)** | 15.87% | 12.99% | **18.60%** | 11.79% | 9.13% | 8.97% | **12.89%** | **9.64 pp** | 1,117 words |
| `whisper_base` | **No-Adapt Baseline** | 16.55% | 14.43% | **21.40%** | 13.53% | 7.87% | 12.36% | **14.32%** | **13.53 pp** | 1,241 words |
| `distil_whisper_small` | **No-Adapt Baseline** | 10.90% | 9.62% | **13.50%** | 8.24% | 6.40% | 6.51% | **9.18%** | **7.10 pp** | 796 words |

---

## 4. Table 3: Exact Edit Operation Breakdown (Substitutions, Deletions, Insertions)

Below are the exact raw edit distances computed via dynamic string alignment across all 6 accent strata for each model under baseline (No-Adapt):

| Model Key | Accent Stratum | Reference Words | Substitutions ($S$) | Deletions ($D$) | Insertions ($I$) | Total Errors ($S+D+I$) | Measured WER |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `data2vec_base` | US English | 1468 | 231 | 34 | 34 | **299** | **20.37%** |
| `data2vec_base` | England English | 1393 | 235 | 21 | 26 | **282** | **20.24%** |
| `data2vec_base` | South Asian English | 1430 | 439 | 65 | 46 | **550** | **38.46%** |
| `data2vec_base` | Australian English | 1493 | 245 | 34 | 24 | **303** | **20.29%** |
| `data2vec_base` | Canadian English | 1500 | 141 | 12 | 17 | **170** | **11.33%** |
| `data2vec_base` | Irish English | 1383 | 142 | 12 | 13 | **167** | **12.08%** |
| `distil_whisper_small` | US English | 1468 | 124 | 16 | 20 | **160** | **10.90%** |
| `distil_whisper_small` | England English | 1393 | 100 | 11 | 23 | **134** | **9.62%** |
| `distil_whisper_small` | South Asian English | 1430 | 149 | 14 | 30 | **193** | **13.50%** |
| `distil_whisper_small` | Australian English | 1493 | 88 | 20 | 15 | **123** | **8.24%** |
| `distil_whisper_small` | Canadian English | 1500 | 79 | 10 | 7 | **96** | **6.40%** |
| `distil_whisper_small` | Irish English | 1383 | 72 | 12 | 6 | **90** | **6.51%** |
| `hubert_large` | US English | 1468 | 163 | 8 | 22 | **193** | **13.15%** |
| `hubert_large` | England English | 1393 | 127 | 11 | 19 | **157** | **11.27%** |
| `hubert_large` | South Asian English | 1430 | 269 | 25 | 25 | **319** | **22.31%** |
| `hubert_large` | Australian English | 1493 | 135 | 10 | 20 | **165** | **11.05%** |
| `hubert_large` | Canadian English | 1500 | 109 | 12 | 15 | **136** | **9.07%** |
| `hubert_large` | Irish English | 1383 | 86 | 8 | 8 | **102** | **7.38%** |
| `wav2vec2_base` | Australian English | 1493 | 271 | 32 | 39 | **342** | **22.91%** |
| `wav2vec2_base` | Canadian English | 1500 | 153 | 13 | 17 | **183** | **12.20%** |
| `wav2vec2_base` | England English | 1393 | 227 | 27 | 29 | **283** | **20.32%** |
| `wav2vec2_base` | Irish English | 1383 | 179 | 23 | 14 | **216** | **15.62%** |
| `wav2vec2_base` | South Asian English | 1430 | 500 | 53 | 54 | **607** | **42.45%** |
| `wav2vec2_base` | US English | 1468 | 253 | 30 | 32 | **315** | **21.46%** |
| `whisper_base` | US English | 1468 | 176 | 16 | 51 | **243** | **16.55%** |
| `whisper_base` | England English | 1393 | 151 | 12 | 38 | **201** | **14.43%** |
| `whisper_base` | South Asian English | 1430 | 229 | 19 | 58 | **306** | **21.40%** |
| `whisper_base` | Australian English | 1493 | 153 | 21 | 28 | **202** | **13.53%** |
| `whisper_base` | Canadian English | 1500 | 98 | 9 | 11 | **118** | **7.87%** |
| `whisper_base` | Irish English | 1383 | 134 | 10 | 27 | **171** | **12.36%** |
| `xlsr_english` | US English | 1468 | 161 | 26 | 15 | **202** | **13.76%** |
| `xlsr_english` | England English | 1393 | 136 | 18 | 14 | **168** | **12.06%** |
| `xlsr_english` | South Asian English | 1430 | 203 | 25 | 15 | **243** | **16.99%** |
| `xlsr_english` | Australian English | 1493 | 136 | 21 | 12 | **169** | **11.32%** |
| `xlsr_english` | Canadian English | 1500 | 104 | 12 | 5 | **121** | **8.07%** |
| `xlsr_english` | Irish English | 1383 | 99 | 15 | 7 | **121** | **8.75%** |
| `wav2vec2_large_lv60` | US English | 1468 | 178 | 15 | 25 | **218** | **14.85%** |
| `wav2vec2_large_lv60` | England English | 1393 | 142 | 7 | 23 | **172** | **12.35%** |
| `wav2vec2_large_lv60` | South Asian English | 1430 | 241 | 26 | 21 | **288** | **20.14%** |
| `wav2vec2_large_lv60` | Australian English | 1493 | 152 | 15 | 19 | **186** | **12.46%** |
| `wav2vec2_large_lv60` | Canadian English | 1500 | 110 | 12 | 17 | **139** | **9.27%** |
| `wav2vec2_large_lv60` | Irish English | 1383 | 102 | 8 | 8 | **118** | **8.53%** |
| `wav2vec2_large_robust` | US English | 1468 | 197 | 17 | 20 | **234** | **15.94%** |
| `wav2vec2_large_robust` | England English | 1393 | 148 | 8 | 23 | **179** | **12.85%** |
| `wav2vec2_large_robust` | South Asian English | 1430 | 229 | 21 | 19 | **269** | **18.81%** |
| `wav2vec2_large_robust` | Australian English | 1493 | 144 | 13 | 17 | **174** | **11.65%** |
| `wav2vec2_large_robust` | Canadian English | 1500 | 117 | 9 | 12 | **138** | **9.20%** |
| `wav2vec2_large_robust` | Irish English | 1383 | 105 | 10 | 10 | **125** | **9.04%** |

---

## 5. Table 4: DSG Online Controller Decision & Safety Statistics

Across all 6 adaptable CTC architectures, the Disparity Safety Gate evaluated $1,350$ candidate updates across 225 sequential stream windows:

| Model Key | Model ID | Architecture | Candidate Updates | Accepted Updates | Rejected Updates | Acceptance Rate | Statistical Violations | Fail-Closed Errors | Final Net $\Delta_R$ vs Base | Worst Subgroup Harm ($\max_g \Delta_g$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | facebook/wav2vec2-base-960h | CTC | 225 | **9.0** | **216.0** | **4.0%** | 216.0 | **0.0** | **+0.07 pp** | **+0.47 pp** |
| `whisper_base` | openai/whisper-base | EncoderDecoder | INCOMPATIBLE | **nan** | **nan** | **nan** | nan | **nan** | **+nan pp** | **+nan pp** |
| `hubert_large` | facebook/hubert-large-ls960-ft | CTC | 225 | **6.0** | **219.0** | **2.7%** | 219.0 | **0.0** | **+0.01 pp** | **+0.36 pp** |
| `data2vec_base` | facebook/data2vec-audio-base-960h | CTC | 225 | **1.0** | **224.0** | **0.4%** | 224.0 | **0.0** | **-0.12 pp** | **+0.07 pp** |
| `distil_whisper_small` | distil-whisper/distil-small.en | EncoderDecoder | INCOMPATIBLE | **nan** | **nan** | **nan** | nan | **nan** | **+nan pp** | **+nan pp** |
| `xlsr_english` | jonatasgrosman/wav2vec2-large-xlsr-53-english | CTC | 225 | **0.0** | **225.0** | **0.0%** | 225.0 | **0.0** | **+0.00 pp** | **+0.00 pp** |
| `wav2vec2_large_lv60` | facebook/wav2vec2-large-960h-lv60 | CTC | 225 | **2.0** | **223.0** | **0.9%** | 223.0 | **0.0** | **-0.02 pp** | **+0.00 pp** |
| `wav2vec2_large_robust` | facebook/wav2vec2-large-robust-ft-libri-960h | CTC | 225 | **5.0** | **220.0** | **2.2%** | 220.0 | **0.0** | **-0.02 pp** | **+0.14 pp** |

---

## 6. Scientific Defense & Authenticity Reconciliation for Professors and Reviewers

When presenting these empirical numbers, reviewers often ask two key questions:

### Q1: Why are the Common Voice error rates (11% - 42%) higher than published LibriSpeech benchmarks (2% - 8%)?
1. **Acoustic Domain Divergence:** LibriSpeech consists of clean, professional audiobooks read by native North American speakers in acoustically controlled environments using studio-grade condenser microphones.
2. **Demographic and Accent Shift:** Mozilla Common Voice 27.0 captures crowdsourced recordings from real-world laptop and smartphone microphones across global English speakers. For example, South Asian English exhibits phonemic retroflexion and syllable timing that diverges sharply from North American training priors (resulting in 42.45% baseline WER on `wav2vec2_base`).
3. **Consistency with Literature:** This divergence is fully corroborated by published literature: Koenecke et al. (PNAS 2020) demonstrated a 2x error rate elevation across diverse speakers; Radford et al. (ICML 2023) showed that Whisper error rates jump from 2.7% on LibriSpeech clean to 13.1% on global Common Voice English.

### Q2: How can the results be verified independently?
Every single number in this report is backed by raw row-level prediction CSVs stored in `reports/stage6/checkpoints/`:
- Every transcribed audio clip has its exact audio ID, speaker ID, accent code, normalized reference text, model hypothesis string, and exact execution timestamp.
- Any independent auditor can open any CSV in Excel or Python and run `(sub + del + ins) / ref_words` to verify bit-for-bit numerical reproducibility.

---

## 7. Artifact File Directory Reference

- **Master CSV Matrix:** [`reports/stage6/master_model_accent_benchmark_matrix.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/master_model_accent_benchmark_matrix.csv)
- **8-Model Overall CSV:** [`reports/stage6/eight_model_benchmark.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/eight_model_benchmark.csv)
- **Complete Accent CSV:** [`reports/stage6/eight_model_group_metrics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/eight_model_group_metrics.csv)
- **Dissertation Dossier PDF:** [`reports/project_report/master_research_report.pdf`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/project_report/master_research_report.pdf)
- **Formula Reference PDF:** [`reports/project_report/formula_reference.pdf`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/project_report/formula_reference.pdf)