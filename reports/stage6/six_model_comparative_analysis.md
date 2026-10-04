# Stage 6: Multi-Backbone Generalization of Disparity Safety Gating
## Empirical Evaluation Across Four CTC Backbones and Architectural Demarcation of Autoregressive Models

- **Protocol Version:** `v1.0-cv27-amended`
- **Execution Date:** October 2026
- **Reference Standards:** ADR-005, Stage 5E Locked Benchmark
- **Holdout Stream:** Frozen Common Voice 27.0 ($N = 900$ clips, 60 speakers, 6 strata, 15 clips/speaker)
- **Sentinel Panel:** Frozen External Sentinel ($M = 300$ clips, 30 speakers, 5 clips/speaker)
- **Gate Hyperparameters:** $\epsilon_R = 0.0000$, $\epsilon_G = 0.0200$, $\epsilon_D = 0.0200$, $B = 1,000$ paired speaker-cluster bootstrap, $\alpha = 0.05$, Seed `20261002`

---

### Executive Summary & Calibrated Scientific Claims

Stage 6 evaluates whether the risk-screening behavior of the **Disparity Safety Gate (DSG)** observed on the primary baseline (`facebook/wav2vec2-base-960h` in Stage 5E) generalizes across diverse acoustic architectures, or whether it was an artifact of a single model backbone. 

Based on rigorous empirical execution across six representative ASR architectures on an identical, frozen prequential stream, we establish the following calibrated scientific findings:

> **Recommended Final Core Claim:**  
> *We show that continual test-time entropy minimization can produce overall and subgroup-specific ASR regression under accent-related distribution shift. We then evaluate a disparity-aware candidate-update safety controller using an independent speaker-stratified sentinel panel and paired speaker-cluster bootstrap bounds. Across four CTC ASR backbones, DSG substantially reduced the regression observed under unconstrained SUTA, while remaining conservative and imperfect as a predictor of external harm.*

1. **Cross-Backbone Risk-Screening Consistency:**  
   The DSG risk-screening mechanism demonstrated cross-backbone consistency across all four evaluated Connectionist Temporal Classification (CTC) ASR models. Across all four backbones, DSG consistently reduced or prevented observed SUTA regression under the frozen external-stream protocol.
2. **Universal SUTA Instability on CTC Models:**  
   Unconstrained continual test-time adaptation (SUTA) degraded word error rates across **100% of tested CTC models** (Wav2Vec2-base $+1.10$ pp, HuBERT-large $+0.40$ pp, Data2Vec-base $+0.22$ pp, XLSR-53 $+2.73$ pp). This confirms that continual adaptation vulnerability is not an idiosyncrasy of Wav2Vec2-base, but an inherent hazard of unregularized frame-entropy minimization under domain shift.
3. **Conservative Screening vs. Adaptation Utilization:**  
   Under the strict zero-tolerance regression threshold ($\epsilon_R = 0.0000$), the gate admitted between $0.0\%$ and $4.0\%$ of candidate updates (Wav2Vec2: $9/225$, HuBERT: $6/225$, Data2Vec: $1/225$, XLSR: $0/225$). DSG functions as a highly conservative filter: it strongly shields models against degradation, but limits adaptation throughput.
4. **Architectural Frontier (CTC vs. Seq2Seq):**  
   Autoregressive sequence-to-sequence models (`openai/whisper-base` and `distil-whisper/distil-small.en`) produce token sequences via conditional beam/greedy search without frame-level categorical emissions ($\hat{y}_t \in \Delta^{|V|}$). Frame-entropy SUTA is mathematically undefined on these models. Rather than substituting an ad-hoc pseudo-labeling algorithm, they are transparently evaluated as static zero-shot baselines, formally establishing the algorithmic boundary of frame-entropy CTTA.
5. **Calibrated Scope:**  
   DSG consistently reduced or prevented observed SUTA regression across the four evaluated CTC ASR backbones under the frozen external-stream protocol. The gate is conservative and does not guarantee elimination of all external harm or preservation of adaptation gains.

---

### 1. Benchmark Results Across ASR Architectures

#### Table 1: Continual Test-Time Adaptation Benchmark (Four CTC Backbones)
All models evaluated across 225 sequential prequential windows ($K=4$, 900 holdout clips) with live model evaluation preceding candidate update generation. Stage 5E Wav2Vec2 results are locked and reproduced verbatim.

| Model Identifier | Model Key | Pretraining Paradigm | Param Count | No-Adapt WER | SUTA WER | DSUTA WER | DMSUTA WER | DSG WER | DSG $\Delta R$ (vs Base) | DSG vs SUTA | DSG $\Delta D$ | Max $\Delta_g$ | DSG Accepted | DSG Rejected | Accept Rate |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `facebook/wav2vec2-base-960h` | `wav2vec2_base` | Contrastive Latent Quantization | 94.4 M | 22.45% | 23.55% | 22.55% | 22.56% | **22.52%** | $+0.07$ pp | **$-1.03$ pp** | $-0.75$ pp | $+0.47$ pp | 9 / 225 | 216 / 225 | 4.0% |
| `facebook/hubert-large-ls960-ft` | `hubert_large` | K-means Acoustic Cluster SSL | 316.8 M | 12.37% | 12.77% | 12.39% | 12.26% | **12.38%** | $+0.01$ pp | **$-0.39$ pp** | $+0.42$ pp | $+0.36$ pp | 6 / 225 | 219 / 225 | 2.7% |
| `facebook/data2vec-audio-base-960h` | `data2vec_base` | Multimodal Contextual Targets | 94.4 M | 20.43% | 20.65% | 19.79% | 20.26% | **20.32%** | **$-0.12$ pp** | **$-0.33$ pp** | $-0.63$ pp | $+0.07$ pp | 1 / 225 | 224 / 225 | 0.4% |
| `wav2vec2-large-xlsr-53-english` | `xlsr_english` | Multilingual Contrastive (53 langs) | 315.5 M | 11.81% | 14.54% | 11.88% | 11.81% | **11.81%** | $\pm 0.00$ pp | **$-2.73$ pp** | $\pm 0.00$ pp | $\pm 0.00$ pp | 0 / 225 | 225 / 225 | 0.0% |

> [!NOTE]
> Across all four CTC models, DSG substantially suppressed the error increases induced by SUTA:
> - **Wav2Vec2-base:** SUTA regression ($+1.10$ pp) reduced to $+0.07$ pp (93.7% error suppression).
> - **HuBERT-large:** SUTA regression ($+0.40$ pp) reduced to $+0.01$ pp (97.1% error suppression).
> - **Data2Vec-base:** SUTA regression ($+0.22$ pp) converted to net gain ($-0.12$ pp vs No-Adapt, $-0.33$ pp vs SUTA).
> - **XLSR-53 English:** SUTA degradation ($+2.73$ pp) completely neutralized ($0.00$ pp delta).

---

#### Table 2: Architectural Boundary & Static Portability Baselines (Seq2Seq Models)
Evaluated on the exact 900-clip Common Voice holdout stream under static zero-shot inference (`No-Adapt`). Frame-entropy CTTA methods are mathematically non-applicable.

| Model Identifier | Model Key | Architectural Family | Param Count | Vocabulary Representation | Holdout WER | Holdout Disparity $D$ | CTTA Status | Algorithmic Non-Applicability Rationale |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `openai/whisper-base` | `whisper_base` | Encoder-Decoder Transformer | 72.6 M | 51,865 BPE Tokens | 14.32% | 13.06 pp | `INCOMPATIBLE` | Model generates text autoregressively; no frame-synchronous categorical emissions $\hat{y}_t \in \Delta^{\|V\|}$ exist. Shannon frame entropy and cross-class correlation (MCC) are undefined. |
| `distil-whisper/distil-small.en` | `distil_whisper_small` | Distilled Enc-Dec Transformer | 166.1 M | 51,865 BPE Tokens | 9.18% | 11.51 pp | `INCOMPATIBLE` | Distilled autoregressive architecture without frame-level linear projections. Adapting decoder on generated hypotheses would constitute pseudo-label self-training, confounding architecture with adaptation loss. |

---

### 2. Rigorous Model Identity & Checkpoint Audit

To maintain complete reproducibility and eliminate naming ambiguity, every evaluated model was audited for its exact Hugging Face identifier, commit hash, parameter count, and architectural class.

| Catalog Key | Full Hugging Face Model ID | Commit SHA (HF Hub) | PyTorch Architecture Class | Parameters | Precision / Layers | Fine-Tuning Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | `22aad52d435eb6dbaf354bdad9b0da84ce7d6156` | `Wav2Vec2ForCTC` | 94,395,552 | FP32 / 12 layers | LibriSpeech 960h CTC |
| `whisper_base` | `openai/whisper-base` | `e37978b90ca9030d5170a5c07aadb050351a65bb` | `WhisperForConditionalGeneration` | 72,593,920 | FP32 / 6 enc + 6 dec | Multitask Supervised |
| `hubert_large` | `facebook/hubert-large-ls960-ft` | `ece5fabbf034c1073acae96d5401b25be96709d8` | `HubertForCTC` | 316,846,080 | FP32 / 24 layers | LibriSpeech 960h CTC |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | `32331f3123e703528918aa688a9a38232d58c872` | `Data2VecAudioForCTC` | 94,395,552 | FP32 / 12 layers | LibriSpeech 960h CTC |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | `9e4a67ca4569c30be43a3fe7fba1621e504f0093` | `WhisperForConditionalGeneration` | 166,132,224 | FP32 / 12 enc + 4 dec | Knowledge Distilled |
| `xlsr_english` | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | `569a6236e92bd5f7652a0420bfe9bb94c5664080` | `Wav2Vec2ForCTC` | 315,472,545 | FP32 / 24 layers | Common Voice + LibriSpeech |

#### HuBERT Model Identity Verification Note
In preliminary catalog definitions, the model key was informally labeled `hubert_base`. However, Meta's `facebook/hubert-base-ls960` checkpoint is an acoustic representation pretraining model (`HubertModel`) that possesses **no ASR prediction head**. Instantiating `facebook/hubert-base-ls960` with `AutoModelForCTC` creates a randomly initialized, untrained linear classification layer that outputs arbitrary character predictions (~100% WER). 

The official, fine-tuned CTC speech recognition model released by Meta and Fairseq is `facebook/hubert-large-ls960-ft` (`HubertForCTC`, 316.8M parameters, 24 transformer layers, hidden dimension 1024). All Stage 6 experiments and checkpoints were conducted exclusively with `facebook/hubert-large-ls960-ft`. In this final report, the catalog key has been standardized to `hubert_large` across all manifests, codebases, CSVs, and checkpoint summaries to ensure total clarity.

---

### 3. Forensic Accepted-Update Trace Across All Four CTC Backbones

Just as discovered in Stage 5E, the immediate decision on a sentinel window and the cumulative downstream effect on an evolving external stream are distinct estimands. Below is the forensic trace of admitted updates and state transitions across the four CTC models:

```
Stream Window Index (t = 0 ... 224)
────────────────────────────────────────────────────────────────────────────
Wav2Vec2-base:  [S0]──w2──[S1]──w7──[S2]──w24,25,27──[S5]──w43──[S6]──w85──[S7]──w114──[S8]──w187──[S9]
HuBERT-large:   [S0]──w1──[S1]──w6──[S2]──w7──[S3]──w19──[S4]──w40──[S5]──w103──[S6] (persists to w224)
Data2Vec-base:  [S0]───────────────────────────w33──[S1] (persists to w224)
XLSR-53:        [S0]────────────────────────────────────────────────────────────────── (persists to w224)
```

#### 3.1 Data2Vec Audio: The Net-Positive Single Update Trace
Data2Vec Audio is the only evaluated model where DSG achieved **better accuracy than the static baseline** ($20.32\%$ vs. $20.43\%$ No-Adapt, $-0.12$ pp; and $-0.33$ pp vs. SUTA).
- **Accepted Window:** Exactly 1 window accepted out of 225: **Window 33** (clips 132–135).
- **Sentinel Decision Statistics at Window 33:**
  - $\Delta R = -0.00205$ ($-0.205$ pp error reduction on sentinel panel).
  - $\text{UCB}_R = -0.00012 \le 0.0000$ (statistically significant non-inferiority).
  - $\text{UCB}_{\max g} = +0.00748 \le 0.0200$ (subgroup safety bound satisfied).
  - $\text{UCB}_D = +0.00762 \le 0.0200$ (disparity bound satisfied).
  - Reason: `ACCEPTED`.
- **State Progression:** Base parameters $\theta_0$ (`ff0b6510...`) governed windows 0 to 33. The candidate generated at window 33 was committed to live state $\theta_1$ (`f8020c55...`). All subsequent 191 candidate updates (windows 34 to 224) were statistically rejected, meaning state $\theta_1$ persisted through the end of the stream.
- **External Holdout Effect:**
  - 146 out of 900 hypotheses ($16.2\%$) differed between No-Adapt and DSG.
  - Total holdout errors decreased by 10 (from 1,771 in No-Adapt to 1,761 in DSG).
  - Subgroup breakdown: South Asian English errors dropped from 550 to 542 ($-8$ errors, $38.46\% \to 37.90\%$), Australian English dropped from 303 to 300 ($-3$ errors), and England English dropped from 282 to 281 ($-1$ error).
  - Holdout disparity $D$ dropped from $27.13$ pp to $26.50$ pp ($-0.63$ pp reduction).
  - Under SUTA, Data2Vec degraded to 1,790 errors ($20.65\%$). DSG eliminated this $+0.22$ pp regression and gained an additional $-0.12$ pp over No-Adapt.

#### 3.2 HuBERT Large: Neutralizing Degradation on High-Accuracy Backbones
HuBERT-large is a high-capacity model (316.8M parameters) with a strong static baseline ($12.37\%$ WER).
- **Accepted Windows:** 6 updates accepted out of 225: **Windows 1, 6, 7, 19, 40, and 103**.
- **Sentinel Decision Statistics:** All 6 accepted windows demonstrated empirical improvements on the sentinel panel ($\Delta R < 0$) with tight bootstrap confidence bounds:
  - Window 1: $\Delta R = -0.034\%$, $\text{UCB}_{\max g} = 0.00\%$, $\text{UCB}_D = 0.00\%$.
  - Window 6: $\Delta R = -0.068\%$, $\text{UCB}_{\max g} = 0.00\%$, $\text{UCB}_D = 0.00\%$.
  - Window 7: $\Delta R = -0.103\%$, $\text{UCB}_{\max g} = 0.00\%$, $\text{UCB}_D = 0.00\%$.
  - Window 19: $\Delta R = -0.103\%$, $\text{UCB}_{\max g} = +0.399\%$, $\text{UCB}_D = +0.234\%$.
  - Window 40: $\Delta R = -0.034\%$, $\text{UCB}_{\max g} = 0.00\%$, $\text{UCB}_D = 0.00\%$.
  - Window 103: $\Delta R = -0.034\%$, $\text{UCB}_{\max g} = 0.00\%$, $\text{UCB}_D = +0.356\%$.
- **State Progression:** Model transitioned through 7 live states ($\theta_0 \to \theta_6$). State $\theta_6$ persisted from window 104 through window 224.
- **External Holdout Effect:**
  - 142 out of 900 hypotheses ($15.8\%$) differed between No-Adapt and DSG, whereas SUTA altered 308 hypotheses ($34.2\%$).
  - SUTA induced $+35$ additional errors across the stream ($1,072 \to 1,107$, $+0.40$ pp).
  - DSG finished with 1,073 errors ($12.38\%$), neutralizing 34 of the 35 added SUTA errors (**97.1% error suppression**, $+0.01$ pp delta).

#### 3.3 Wav2Vec2 Base (Primary Frozen Benchmark)
- **Accepted Windows:** 9 updates accepted out of 225: Windows 2, 7, 24, 25, 27, 43, 85, 114, 187.
- **External Holdout Effect:** SUTA added $+95$ errors ($1,946 \to 2,041$, $+1.10$ pp). DSG held errors to 1,952 ($22.52\%$, $+0.07$ pp), arresting 89 of 95 errors (**93.7% error suppression**).
- Disparity $D$ fell by $-0.75$ pp ($30.25\% \to 29.50\%$). Under SUTA, Irish English degraded from $15.62\%$ to $18.00\%$ ($+2.38$ pp spike); DSG preserved Irish English at $15.33\%$ ($-0.29$ pp improvement).

#### 3.4 XLSR-53 English: Clean Safety Screening Under Substantial SUTA Degradation
XLSR-53 English was fine-tuned on a 53-language multilingual foundation model. While its zero-shot English performance is strong ($11.81\%$ WER), continual adaptation was severely destabilizing.
- **SUTA Behavior:** Unconstrained SUTA exhibited substantial degradation, deteriorating from $11.81\%$ to $14.54\%$ (**$+2.73$ pp**, $+236$ additional errors: $1,024 \to 1,260$). This was the largest observed SUTA regression in the entire benchmark.
- **Sentinel Decision Statistics:** Under the strict $\epsilon_R = 0.0000$ bound, every single candidate update ($225 / 225$) either directly worsened sentinel word error rate or failed the upper confidence bound $\text{UCB}_R \le 0.0000$.
- **DSG Intervention:** The gate rejected **100% of candidate updates** ($0$ accepted, $225$ rejected). The live model remained in base state $\theta_0$ throughout the entire 225 windows.
- **External Holdout Effect:** DSG WER remained identically $11.81\%$, completely shielding the system from SUTA's $+2.73$ pp degradation.

---

### 4. Safety Screening vs. Adaptation Utilization Analysis

The empirical acceptance rates across the four CTC models reveal a fundamental property of statistical risk screening:

$$\text{Wav2Vec2: } 4.0\% \quad\mid\quad \text{HuBERT: } 2.7\% \quad\mid\quad \text{Data2Vec: } 0.4\% \quad\mid\quad \text{XLSR: } 0.0\%$$

```
Model Acceptance Rate vs. Safety Screening
┌────────────────────────────────────────────────────────────────────────┐
│ XLSR-53       [0.0%]  Total Adaptation Suppression (Shields +2.73 pp)  │
│ Data2Vec-base [0.4%]  Single Safe Update Admitted (Improves -0.12 pp)  │
│ HuBERT-large  [2.7%]  Rare Updates Admitted (Arrests 97.1% of Regress) │
│ Wav2Vec2-base [4.0%]  Selective Updates Admitted (Arrests 93.7% Regres)│
└────────────────────────────────────────────────────────────────────────┘
 0.0%                  1.0%                  2.0%                 4.0%
```

#### Dual Reality: Safety and Utilization
1. **Safety Screening:**  
   The gate acts as an empirical risk screen. Across 900 candidate updates, there were 0 fail-closed software errors, and every rejection was produced by the configured statistical gate.
2. **Adaptation Utilization:**  
   Because $\epsilon_R = 0.0000$ strictly enforces the configured empirical non-regression criterion on the sentinel panel, candidate updates generated by unsupervised entropy minimization are overwhelmingly rejected. For XLSR-53, this resulted in complete suppression of adaptation ($0/225$). While this fully protected the model against degradation, it achieved zero adaptation throughput.
   - **Empirical Boundary & Limitations:** DSG generalizes as a screening mechanism, but its acceptance rate is highly model-dependent, ranging from 0% to 4% under the frozen risk budget.
3. **Scientific Implication:**  
   DSG should not be characterized as an "adaptation booster", but as a **robust statistical safety fuse**. When adaptation updates are noisy or degrading (as SUTA frequently is under natural accent shifts), the gate conservatively reverts to the base model. When a candidate update is unambiguously beneficial across diverse speakers (as in Data2Vec window 33), the gate safely admits it.

---

### 5. Dissertation Chapter Synthesis: Four Core Research Questions

Stage 6 completes the empirical narrative of this dissertation. The overall research contributions align with four core research questions:

#### RQ1: Does accent/group disparity exist in contemporary ASR models?
- **Finding:** Yes. Evaluated across Common Voice strata, every single tested architecture—regardless of model size, training objective, or acoustic family—exhibits pronounced disparity between accent groups.
- **Evidence:** Disparities ($D = \max_g \text{WER}_g - \min_g \text{WER}_g$) range from $11.51$ pp (Distil-Whisper) to $30.25$ pp (Wav2Vec2-base), with South Asian English consistently experiencing 2 to 3 times higher error rates than native US/Canadian strata.

#### RQ2: Can continual test-time adaptation worsen subgroup performance?
- **Finding:** Yes. Continual test-time adaptation via unsupervised entropy minimization (SUTA) introduces systematic instability and regresses accuracy.
- **Evidence:** On the primary Wav2Vec2 backbone, SUTA worsened overall WER from $22.45\%$ to $23.55\%$ ($+1.10$ pp) and induced subgroup regressions up to $+2.39$ pp. Across the remaining CTC backbones, SUTA regressed in 100% of cases, degrading XLSR-53 by $+2.73$ pp.

#### RQ3: Can a risk-controlled candidate gate prevent harmful updates?
- **Finding:** Sentinel-panel bounding with speaker-cluster bootstrapping provides conservative candidate-update screening on the primary Wav2Vec2 backbone, accepting 9/225 updates and rejecting 216/225 under the frozen risk constraints.
- **Evidence:** On the primary Stage 5 benchmark, DSG accepted $9/225$ updates ($4.0\%$), rejected $216/225$ ($96.0\%$), held WER to $22.52\%$ (mitigating $93.7\%$ of SUTA's error increase), and reduced overall disparity by $-0.75$ pp.

#### RQ4: Does the risk-screening behavior generalize across acoustic backbones?
- **Finding:** Yes, across CTC backbones. The screening behavior demonstrated consistent protection across contrastive, acoustic-cluster, multimodal, and multilingual CTC encoders. Autoregressive Seq2Seq models delineate the architectural boundary where frame-entropy CTTA is inapplicable.
- **Evidence:** DSG mitigated SUTA degradation on HuBERT-large ($+0.40 \to +0.01$ pp), produced net gains on Data2Vec-base ($-0.12$ pp vs No-Adapt, $-0.63$ pp disparity), and completely shielded XLSR-53 from a $+2.73$ pp collapse ($0/225$ accepted), while Whisper-base ($14.32\%$) and Distil-Whisper ($9.18\%$) establish strong static reference points.

---

### 6. Archival Artifact Reference

All empirical artifacts are committed, versioned, and cryptographically verified:
- Master Benchmark CSV: [`reports/stage6/six_model_benchmark.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/six_model_benchmark.csv)
- DSG Controller Audit: [`reports/stage6/six_model_dsg_summary.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/six_model_dsg_summary.csv)
- Subgroup Disparity Metrics: [`reports/stage6/six_model_group_metrics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/six_model_group_metrics.csv)
- Architectural Manifest: [`reports/stage6/model_compatibility_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/model_compatibility_manifest.json)
- Checkpoint Data & Predictions: [`reports/stage6/checkpoints/`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6/checkpoints/)
- Primary Frozen Baseline (Stage 5E): [`reports/stage5/final_external_metrics.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/final_external_metrics.csv) (SHA-256: `a76bfc4efbfaa8d9df374881e78ee55f7138f256ce488a5cb7b3a55a778738dd`)
