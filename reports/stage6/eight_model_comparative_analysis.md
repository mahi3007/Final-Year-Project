# Stage 6 & 6.1: Eight-Model Cross-Architecture Benchmark & Generalization Analysis
## Empirical Evaluation of Continual Test-Time Adaptation and Disparity Safety Gating Across Six CTC Backbones and Two Autoregressive Baselines

- **Protocol Version:** `v1.0-cv27-amended`
- **Execution Date:** October 2026
- **Reference Standards:** ADR-005, Stage 5E Locked Baseline, Stage 6 Protocol
- **Holdout Evaluation Stream:** Frozen Common Voice 27.0 ($N = 900$ clips, 60 speakers, 6 strata, 15 clips/speaker, $K = 4$, 225 windows)
- **Sentinel Safety Panel:** Frozen External Sentinel ($M = 300$ clips, 30 speakers, 5 clips/speaker, 100% disjoint speakers)
- **Gate Hyperparameters:** $\epsilon_R = 0.0000$ (zero overall regression), $\epsilon_G = 0.0200$ (2% subgroup slack), $\epsilon_D = 0.0200$ (2% disparity slack), $B = 1,000$ paired speaker-cluster bootstrap, $\alpha = 0.05$, Seed `20261002`

---

### Executive Summary & Calibrated Scientific Claims

Stage 6.1 expands the cross-architecture evaluation suite to a finalized, frozen **8-model benchmark suite**:
- **6 CTTA-Compatible CTC Models:** `wav2vec2_base`, `hubert_large`, `data2vec_base`, `xlsr_english`, `wav2vec2_large_lv60`, `wav2vec2_large_robust`
- **2 Static Autoregressive Portability Baselines:** `whisper_base`, `distil_whisper_small`

> **Frozen Final Core Claim:**  
> *We show that continual test-time entropy minimization can produce overall and subgroup-specific ASR regression under accent-related distribution shift. We then evaluate a disparity-aware candidate-update safety controller using an independent speaker-stratified sentinel panel and paired speaker-cluster bootstrap bounds. Across six CTC ASR backbones spanning two parameter scales (94M to 316M parameters) and four pretraining paradigms, DSG consistently reduced or prevented the degradation observed under unconstrained SUTA, while remaining conservative and imperfect as a predictor of external harm.*

#### Key Scientific Findings

1. **Consistent Directional SUTA Regression Across All Six CTC Backbones:**  
   Positive aggregate word error rate (WER) regression was observed under unconstrained SUTA for all six evaluated CTC backbones under real-world accent shift. The severity of regression ranged from modest inflation ($+0.22$ pp on Data2Vec-base) to severe catastrophic collapse ($+2.73$ pp on XLSR-53). This confirms that continual adaptation vulnerability is not an idiosyncrasy of Wav2Vec2-base, but an inherent hazard of unregularized frame-entropy minimization across diverse SSL representations and parameter scales.
2. **Consistent DSG Risk Screening Across All Six Evaluated CTC Backbones:**  
   Across all six CTC backbones, DSG reduced the observed SUTA regression across all six evaluated CTC backbones under the frozen external-stream protocol. On three models (`data2vec_base`, `wav2vec2_large_lv60`, and `wav2vec2_large_robust`), DSG finished slightly better than the unadapted baseline ($-0.12$ pp, $-0.02$ pp, and $-0.02$ pp, respectively), proving that DSG is not merely a static "never-adapt" gate.
3. **The Dual Interpretation of XLSR-53 (Strongest Stress Case):**  
   Under SUTA, XLSR-53 suffered the most severe divergence in the benchmark ($11.81\% \to 14.54\%$, $+2.73$ pp). DSG rejected all 225 candidate updates under the frozen sentinel criteria and therefore preserved the No-Adapt state ($11.81\%$), completely avoiding the external degradation. This result simultaneously demonstrates **excellent safety screening** and **zero adaptation utilization** ($0/225$ accepted).
4. **Model-Dependent Adaptation Utilization:**  
   Under identical frozen risk thresholds ($\epsilon_R = 0.0000, \epsilon_G = 0.0200, \epsilon_D = 0.0200$), the controller produced substantially different adaptation acceptance rates across backbones:
   $$ 4.0\%,\quad 2.7\%,\quad 0.4\%,\quad 0.0\%,\quad 0.9\%,\quad 2.2\% $$
   *Safety screening behavior is consistent across backbones, but adaptation acceptance rate is model-dependent.*
5. **Architectural Frontier & Boundary of Applicability:**  
   Autoregressive sequence-to-sequence models (`whisper_base` and `distil_whisper_small`) lack frame-synchronous categorical emissions ($\hat{y}_t \in \Delta^{|V|}$). Frame-level Shannon entropy and cross-class correlation (MCC) losses are mathematically non-applicable. Rather than substituting an ad-hoc pseudo-labeling algorithm, they are transparently evaluated as static zero-shot baselines, formally establishing the boundary of frame-entropy CTTA.

---

### 1. Master Benchmark Suite: Two-Table Architectural Demarcation

The evaluation suite is organized into two distinct methodological tiers based on architectural compatibility with frame-level unsupervised entropy adaptation.

#### Table 1A: Continual Test-Time Adaptation Benchmark (Six CTC Backbones)
All models evaluated across 225 sequential prequential stream windows ($K=4$, 900 clips) on the frozen Common Voice 27.0 evaluation stream. Stage 5E Wav2Vec2 results are locked and reproduced verbatim.

| Model Key | Model Architecture & Catalog ID | Pretraining Objective & Scope | Param Scale | No-Adapt WER | SUTA WER | DSUTA WER | DMSUTA WER | DSG WER | DSG vs Base ($\Delta R$) | DSG vs SUTA | DSG $\Delta D$ | Max Subgroup $\Delta_g$ | DSG Accepted / Total |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | Contrastive Latent Quantization (LibriSpeech 960h) | 94.4 M | 22.45% | 23.55% | 22.55% | 22.56% | **22.52%** | $+0.07$ pp | **$-1.03$ pp** | $-0.75$ pp | $+0.47$ pp | 9 / 225 (4.0%) |
| `hubert_large` | `facebook/hubert-large-ls960-ft` | K-means Acoustic Cluster SSL (LibriSpeech 960h) | 316.8 M | 12.37% | 12.77% | 12.39% | 12.26% | **12.38%** | $+0.01$ pp | **$-0.39$ pp** | $+0.42$ pp | $+0.36$ pp | 6 / 225 (2.7%) |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | Multimodal Contextual Prediction (LibriSpeech 960h) | 94.4 M | 20.43% | 20.65% | 19.79% | 20.26% | **20.32%** | **$-0.12$ pp** | **$-0.33$ pp** | $-0.63$ pp | $+0.07$ pp | 1 / 225 (0.4%) |
| `xlsr_english` | `wav2vec2-large-xlsr-53-english` | Multilingual Contrastive SSL (53 Languages, 56k hrs) | 315.5 M | 11.81% | 14.54% | 11.88% | 11.81% | **11.81%** | $\pm 0.00$ pp | **$-2.73$ pp** | $\pm 0.00$ pp | $\pm 0.00$ pp | 0 / 225 (0.0%) |
| `wav2vec2_large_lv60` | `facebook/wav2vec2-large-960h-lv60` | Large-Scale Pretraining (Libri-Light 60k hrs + 960h FT) | 315.5 M | 12.93% | 13.97% | 13.00% | 13.06% | **12.91%** | **$-0.02$ pp** | **$-1.06$ pp** | $\pm 0.00$ pp | $\pm 0.00$ pp | 2 / 225 (0.9%) |
| `wav2vec2_large_robust` | `wav2vec2-large-robust-ft-libri-960h` | Multi-Domain Pretraining (CV, SWBD, Fisher + 960h FT) | 315.5 M | 12.91% | 13.28% | 12.86% | 12.92% | **12.89%** | **$-0.02$ pp** | **$-0.39$ pp** | **$-0.14$ pp** | $+0.14$ pp | 5 / 225 (2.2%) |

#### Table 1B: Static Portability Baselines (Two Autoregressive Seq2Seq Models)
Evaluated on the exact 900-clip holdout stream under static zero-shot inference (`No-Adapt`). Frame-entropy CTTA methods are mathematically non-applicable.

| Model Key | Model Identifier | Architectural Family | Param Scale | Vocabulary Representation | Holdout WER | Holdout Disparity $D$ | CTTA Compatibility Status | Non-Applicability Rationale |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `whisper_base` | `openai/whisper-base` | Encoder-Decoder Transformer | 72.6 M | 51,865 BPE Tokens | 14.32% | 13.06 pp | `INCOMPATIBLE` | Model generates text autoregressively via cross-attention; no frame-synchronous categorical emissions $\hat{y}_t \in \Delta^{\|V\|}$ exist. Frame-entropy SUTA is mathematically undefined. |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | Distilled Enc-Dec Transformer | 166.1 M | 51,865 BPE Tokens | 9.18% | 11.51 pp | `INCOMPATIBLE` | Distilled autoregressive architecture without frame-level linear projections. Adapting decoder on generated hypotheses would constitute pseudo-label self-training, confounding architecture with adaptation loss. |

---

### 2. Six-Model DSG Outcome & Diagnostic Matrix

To rigorously determine whether DSG acts merely as a blunt rejection filter or whether it meaningfully discriminates update utility, we examine the fine-grained decision and outcome logs across all 1,350 candidate evaluations.

#### Table 2: Multi-Backbone Safety Gate Outcome & Verification Matrix
*Sentinel evaluations reflect candidate-level point estimate changes $\Delta_R$ evaluated under paired bootstrap bounds ($B=1,000$). Cumulative downstream external word differences reflect retrospective utterance-level word deltas across the 900-clip prequential stream.*

| Model Key | Candidate Updates | Accepted Updates | Rejected Updates | Acceptance Rate | Statistical Rejections | Fail-Closed Software Errors | Sentinel Lower Error ($\Delta_R < 0$) | Sentinel Neutral ($\Delta_R = 0$) | Sentinel Higher Error ($\Delta_R > 0$) | Cumulative Downstream External Word Difference | Downstream External Clips (Imp / Deg / Identical) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | 225 | 9 | 216 | 4.0% | 216 | 0 | 5 | 4 | **0** | $+6$ words ($+0.07$ pp) | 23 / 25 / 852 |
| `hubert_large` | 225 | 6 | 219 | 2.7% | 219 | 0 | 6 | 0 | **0** | $+1$ word ($+0.01$ pp) | 24 / 26 / 850 |
| `data2vec_base` | 225 | 1 | 224 | 0.4% | 224 | 0 | 1 | 0 | **0** | **$-10$ words ($-0.12$ pp)** | 26 / 18 / 856 |
| `xlsr_english` | 225 | 0 | 225 | 0.0% | 225 | 0 | 0 | 0 | **0** | **$0$ words ($\pm 0.00$ pp)** | 0 / 0 / 900 |
| `wav2vec2_large_lv60` | 225 | 2 | 223 | 0.9% | 223 | 0 | 1 | 1 | **0** | **$-2$ words ($-0.02$ pp)** | 2 / 0 / 898 |
| `wav2vec2_large_robust` | 225 | 5 | 220 | 2.2% | 220 | 0 | 4 | 1 | **0** | **$-2$ words ($-0.02$ pp)** | 9 / 7 / 884 |
| **Aggregate / Total** | **1,350** | **23** | **1,327** | **1.7%** | **1,327** | **0** | **17** | **6** | **0** | — | — |

#### Critical Diagnostic Insights from the Outcome Matrix

1. **Sentinel-Panel Risk Compliance:**  
   **No accepted update produced a positive sentinel-panel overall regression under the frozen overall-risk criterion** ($\Delta_R \le 0.0$ in 100% of accepted cases; 17 candidate states exhibited lower overall sentinel WER ($\Delta_R < 0$), and 6 exhibited identical sentinel WER ($\Delta_R = 0$)). The configured empirical gate bound ($\text{UCB}_R \le \epsilon_R = 0.0000$) functioned strictly as configured across all six backbones.
2. **Sentinel vs. Downstream Decoupling:**  
   While every accepted update was non-inferior on the sentinel panel, downstream generalization on the external stream showed subtle divergence:
   - In `data2vec_base`, `wav2vec2_large_lv60`, and `wav2vec2_large_robust`, accepted updates produced **net-positive downstream generalization** (more clips improved than degraded, reducing total corpus errors by $-10$, $-2$, and $-2$ words, respectively).
   - In `wav2vec2_base` and `hubert_large`, accepted updates were non-inferior on the sentinel panel but induced a small net increase on the evolving external stream ($+6$ words and $+1$ word, respectively). This proves empirically that **sentinel non-inferiority is a conservative empirical risk screen, not a mathematical guarantee of downstream benefit**.
3. **Flawless Software Reliability:**  
   Across all 1,350 evaluations, there were **0 fail-closed software errors**. Every single rejection was produced by the configured statistical hypothesis test.

---

### 3. Three-Axis Comparative Analysis: Scale, Pretraining, and Architecture

The expanded 6-CTC suite provides a structured, multi-dimensional testbed:

```
                              ASR Model Suite
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      │                              │                              │
Architecture Family             Model Scale                 Pretraining Regime
      │                              │                              │
 CTC vs. Seq2Seq             94M vs. 316M Parameters     Standard, Robust, Multilingual
 (Wav2Vec2, HuBERT,          (Base: 94.4M)               (Contrastive, Cluster,
  Data2Vec vs. Whisper)       (Large: 315.5M - 316.8M)    Contextual, Robust 4-Domain)
```

#### Axis 1: Model Scale (94.4M vs. 315.5M Parameters)
- Comparing `facebook/wav2vec2-base-960h` (94.4M params, 12 layers) against `facebook/wav2vec2-large-960h-lv60` (315.5M params, 24 layers) isolates the effect of parameter scale within the same architectural family.
- SUTA degraded the large model by $+1.04$ pp ($12.93\% \to 13.97\%$), nearly identical to the $+1.10$ pp degradation observed on the base model ($22.45\% \to 23.55\%$).
- **Conclusion:** Continual entropy collapse is **scale-invariant**; increasing model depth and parameter capacity by over $3.3\times$ does not immunize self-supervised encoders against test-time adaptation divergence.

#### Axis 2: Pretraining Regime & Multi-Domain Robustness
- Comparing `wav2vec2_large_lv60` (pretrained solely on Libri-Light read audio) against `wav2vec2_large_robust` (pretrained on diverse multi-domain audio: LibriSpeech, Common Voice, Switchboard, and Fisher).
- The robustly fine-tuned checkpoint exhibited lower observed SUTA regression than the LV60 checkpoint ($+0.37$ pp vs. $+1.04$ pp). This pattern is consistent with greater robustness to distribution shift, but the experiment does not isolate pretraining diversity as a causal factor.
- Under DSG, `wav2vec2_large_robust` achieved the highest acceptance rate among large models ($2.2\%$, $5/225$ updates), successfully reducing WER to **12.89%** and reducing accent disparity by **$-0.14$ pp**.

#### Axis 3: Acoustic Representation Objective
- **Contrastive Quantization (`wav2vec2_base`):** SUTA degradation $+1.10$ pp; DSG accepts 9 updates, containing WER to $22.52\%$.
- **K-Means Acoustic Clustering (`hubert_large`):** SUTA degradation $+0.40$ pp; DSG accepts 6 updates, containing WER to $12.38\%$.
- **Multimodal Contextual Target Prediction (`data2vec_base`):** SUTA degradation $+0.22$ pp; DSG accepts 1 update, achieving a net gain of $-0.12$ pp ($20.43\% \to 20.32\%$).
- **Multilingual Pretraining (`xlsr_english`):** SUTA degradation $+2.73$ pp; DSG accepts 0 updates, perfectly preserving baseline $11.81\%$.

---

### 4. Final Five-Contribution Structure for Dissertation

This 8-model experimental suite establishes five cohesive scientific contributions for the thesis:

1. **Contribution 1 — CTTA Vulnerability Characterization:**  
   Empirically demonstrates positive aggregate WER regression under unconstrained SUTA across all six evaluated CTC backbones under real-world accent shift, disproving the assumption that test-time entropy adaptation is uniformly safe.
2. **Contribution 2 — Risk-Screening Controller:**  
   Formulates a tripartite candidate-update safety controller evaluating overall risk ($\Delta_R$), subgroup-specific risk ($\max_g \Delta_g$), and between-group disparity ($\Delta_D$).
3. **Contribution 3 — Independent Statistical Screening:**  
   Introduces an independent, speaker-disjoint 30-speaker sentinel panel evaluated via paired speaker-cluster bootstrap bounds ($B=1,000$).
4. **Contribution 4 — External Empirical Validation:**  
   Rigorously validates that DSG substantially reduces the WER regression observed under unconstrained SUTA on the primary external benchmark stream.
5. **Contribution 5 — Cross-Backbone Validation & Architectural Demarcation:**  
   Generalizes the risk-screening behavior across six CTC checkpoints covering different scales (94M to 316M) and representation-learning/pretraining regimes, while formally establishing Seq2Seq autoregressive models as an architectural boundary and static portability comparison.

---

### 5. Final Research Narrative

The complete, defensible narrative arc of the dissertation is summarized as follows:

```
Baseline ASR Accent Disparity
              ↓
Continual Test-Time Adaptation Vulnerability
              ↓
SUTA Regresses on All Six Evaluated CTC Backbones
              ↓
Some Regressions are Subgroup-Sensitive
              ↓
DSG Evaluates Candidate Updates on Independent Sentinel
              ↓
23 / 1,350 Updates Admitted | 1,327 / 1,350 Rejected (0 Fail-Closed Errors)
              ↓
DSG Lowers Observed SUTA Regression Across All 6 CTC Backbones
              ↓
BUT Acceptance Rate Varies Strongly by Model (0.0% to 4.0%)
              ↓
AND One Accepted Update Can Still Be Externally Harmful (Decoupling)
              ↓
Therefore:
DSG = Conservative Empirical Risk Screening ≠ Universal Safety Guarantee
```
