# Protocol Amendment v1.1: Multi-Model Scientific Expansion

**Governing Standard:** ADR-005  
**Protocol Version:** `v1.1.0-model-expansion`  
**Supersedes:** `v1.0.0-canonical` (Stages 0–4), `v1.0-cv27-amended` (Stages 5–6.1) for extension stages  
**Historical Invariant:** All `v1.0.0-canonical` artifacts and stage reports remain **IMMUTABLE**  

---

## 1. Executive Summary & Rationale for Protocol Extension

In the canonical `v1.0.0-canonical` protocol, test-time adaptation discovery (Stage 3), acoustic boundary characterization (Stage 4), and Disparity Safety Gate qualification (Stage 5) were conducted exclusively on a single backbone architecture: `facebook/wav2vec2-base-960h`. While Stage 6 subsequently evaluated six CTC backbones and two Seq2Seq models on Common Voice 27.0, an important scientific critique can be raised:

> *"Did the DSG controller succeed because of universal statistical risk-screening properties, or was it co-adapted to the dynamics of the single development backbone family on which it was qualified?"*

To address this critique and elevate the dissertation to the highest standard of publication rigor (targeting top-tier speech conferences and dissertations), **Protocol Amendment v1.1** establishes an architecture-aware multi-model extension:

$$\boxed{\text{Multiple CTC models participate in every adaptation stage, while Seq2Seq models serve as static portability controls.}}$$

This amendment explicitly formalizes the separation between **development/qualification models** and **held-out validation models**:

$$\boxed{\text{Stage 3M–5M Development Backbones} \neq \text{Stage 6M Held-Out Validation Backbones}}$$

---

## 2. Historical Integrity Mandate (`v1.0.0-canonical` is Frozen)

The existing historical experiments represent genuine scientific milestones and must **NEVER** be overwritten or retroactively altered:

```
Protocol v1.0.0-canonical (Historical Record - IMMUTABLE)
  ├── Stage 0: Protocol Freeze & Rules of Engagement
  ├── Stage 1: Data Ingestion & Schema Verification
  ├── Stage 2: 6-Model Static Audit on L2-ARCTIC (552 words)
  ├── Stage 3: CTTA Discovery on Wav2Vec2-base only
  ├── Stage 4: Acoustic Stress Characterization on Wav2Vec2-base only
  ├── Stage 5: Primary DSG Qualification on Wav2Vec2-base only
  └── Stage 6: External Cross-Architecture Benchmark on Common Voice 27.0
```

Under this amendment, new extension stages are explicitly designated with the **"M" suffix** (Multi-Model):

```
Protocol v1.1.0-model-expansion (Amended Multi-Model Pipeline)
  ├── Stage 2:  Historical 6-Model Static Disparity Map (Inherited)
  ├── Stage 3M: Multi-Model CTTA Discovery across 3 CTC models + 3 static Seq2Seq controls
  ├── Stage 4M: Multi-Model Stress & Boundary Characterization (5 acoustic conditions, K sweep)
  ├── Stage 5M: Multi-Model DSG Qualification across 3 CTC development backbones
  │             └── FREEZE BARRIER: Thresholds, Gate Logic, Bootstrap, Rollback Locked
  └── Stage 6M: Final Cross-Dataset Validation on Common Voice 27.0
                ├── 4 Genuinely Held-Out CTC Backbones (Zero Development Exposure)
                ├── 2 Overlap CTC Controls (Cross-Dataset Replication)
                └── 2 Seq2Seq Static Portability Controls
```

---

## 3. Authoritative Model Role Registry (`configs/model_role_registry.json`)

The eight models in the repository are strictly partitioned into architecture-aware scientific roles:

| Model Key | HuggingFace Model Identifier | Architecture | Parameter Count | Development Role | Stage 6 Role | CTTA Eligibility Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `wav2vec2_base` | `facebook/wav2vec2-base-960h` | CTC | 94.4 M | Primary CTC Backbone | Overlap / Replication Control | **COMPATIBLE** |
| `data2vec_base` | `facebook/data2vec-audio-base-960h` | CTC | 94.4 M | Secondary CTC Backbone | Overlap / Replication Control | **COMPATIBLE** |
| `wav2vec2_100h` | `facebook/wav2vec2-base-100h` | CTC | 94.4 M | Low-Resource CTC Backbone | *Not Evaluated in Stage 6* | **COMPATIBLE** |
| `whisper_base` | `openai/whisper-base` | Seq2Seq | 72.6 M | Static Baseline | Static Portability Baseline | `INCOMPATIBLE_NON_CTC` |
| `distil_whisper_small` | `distil-whisper/distil-small.en` | Seq2Seq | 166.1 M | Static Baseline | Static Portability Baseline | `INCOMPATIBLE_NON_CTC` |
| `whisper_tiny` | `openai/whisper-tiny` | Seq2Seq | 37.8 M | Static Baseline | *Not Evaluated in Stage 6* | `INCOMPATIBLE_NON_CTC` |
| `hubert_large` | `facebook/hubert-large-ls960-ft` | CTC | 316.8 M | *Excluded from Development* | **Genuinely Held-Out CTC** | **COMPATIBLE** |
| `xlsr_english` | `wav2vec2-large-xlsr-53-english` | CTC | 315.5 M | *Excluded from Development* | **Genuinely Held-Out CTC** | **COMPATIBLE** |
| `wav2vec2_large_lv60` | `facebook/wav2vec2-large-960h-lv60` | CTC | 315.5 M | *Excluded from Development* | **Genuinely Held-Out CTC** | **COMPATIBLE** |
| `wav2vec2_large_robust` | `wav2vec2-large-robust-ft-libri-960h` | CTC | 315.5 M | *Excluded from Development* | **Genuinely Held-Out CTC** | **COMPATIBLE** |

---

## 4. Architecture-Aware Adaptation Rule (CTC vs. Seq2Seq Boundary)

### 4.1 CTC Family Eligibility
The current unsupervised adaptation objectives (SUTA, DSUTA, DMSUTA) minimize frame entropy $\mathcal{H}_{\text{frame}}$ and class confusion $\mathcal{R}_{\text{mcc}}$:

$$\mathcal{H}_{\text{frame}}(\hat{Y}) = -\frac{1}{T}\sum_{t=1}^T \sum_{c \in \mathcal{V}} P(y_t = c \mid X; \theta) \log P(y_t = c \mid X; \theta)$$

This formulation requires **frame-synchronous categorical emissions** $\hat{y}_t \in \Delta^{|\mathcal{V}|}$. CTC architectures (Wav2Vec2, Data2Vec, HuBERT, XLSR) produce these emissions directly via an acoustic encoder and linear projection head.

### 4.2 Seq2Seq Family Non-Applicability
Autoregressive Encoder-Decoder architectures (Whisper, Distil-Whisper) generate text conditionally token-by-token:

$$P(Y \mid X) = \prod_{u=1}^U P(y_u \mid y_{<u}, X)$$

They do **not** emit frame-synchronous acoustic posteriors. Applying frame-entropy minimization to autoregressive decoders is mathematically undefined. Decoded beam-search hypotheses would transform the objective into pseudo-label self-training, violating method comparability.

**Mandate:** Seq2Seq models participate exclusively in static zero-shot inference, static acoustic stress characterization, and architectural portability benchmarks. The repository strictly forbids generating synthetic or fabricated adaptation runs for Seq2Seq models.

---

## 5. Multi-Model Stage Specifications

### 5.1 Stage 3M — Multi-Model CTTA Discovery
- **Dataset:** L2-ARCTIC `final_test` ($N = 60$ utterances, 6 speakers, 6 accent groups, 552 reference words).
- **Streaming Parameters:** $K = 4$ window size, 15 sequential windows.
- **Experimental Orders:** $\text{ORDER}_A, \text{ORDER}_B, \text{ORDER}_C$ (pre-registered permutations).
- **CTC Scope:** 3 development backbones (`wav2vec2_base`, `data2vec_base`, `wav2vec2_100h`) $\times$ 4 methods (`No-Adapt`, `SUTA`, `DSUTA`, `DMSUTA`) $\times$ 3 orders $= 36$ conditions.
- **Seq2Seq Scope:** 3 models (`whisper_base`, `distil_whisper_small`, `whisper_tiny`) $\times$ `No-Adapt` static evaluation $= 3$ reference runs.
- **Core Research Question:** Are continual test-time adaptation dynamics and ordering sensitivities general across CTC backbones, or specific to `wav2vec2_base`?

### 5.2 Stage 4M — Multi-Model Stress & Boundary Characterization
- **Dataset:** L2-ARCTIC `stage4_characterization` ($N = 120$ utterances, 12 speakers, 2 speakers/group, 1,104 reference words).
- **Acoustic Stress Conditions:**
  1. Clean (unmodified speech)
  2. Moderate Noise ($\text{SNR} = 15\text{ dB}$)
  3. Severe Noise ($\text{SNR} = 5\text{ dB}$)
  4. Moderate Babble ($\text{SNR} = 15\text{ dB}$)
  5. Reverberation ($T_{60} = 0.4\text{ s}$)
- **K Sweep:** $K \in \{1, 4, 5, 10\}$ evaluated on Clean, Severe Noise, and Reverberation; $K = 4$ for remaining conditions.
- **Model $\times$ Method Interaction Analysis:** Evaluates whether different backbones exhibit statistically significant differences in adaptation sensitivity ($\beta_{\text{Model} \times \text{Method}}$).
- **Practical Instability Thresholds:** Frozen at $\delta_G = 0.0200$ ($2.00\text{ pp}$ subgroup regression) and $\delta_D = 0.0200$ ($2.00\text{ pp}$ disparity growth) based on `configs/stage4_thresholds.json`.

### 5.3 Stage 5M — Multi-Model DSG Qualification
- **Sentinel Panel:** `datasets/splits/stage5_sentinel_panel.csv` ($M = 300$ clips, 30 speakers, 10 clips/speaker, strictly speaker-disjoint from evaluation partitions).
- **Frozen Controller Tolerances:**
  $$\epsilon_R = 0.0000 \quad (0.00\text{ pp overall regression allowable})$$
  $$\epsilon_G = 0.0200 \quad (2.00\text{ pp subgroup regression allowable})$$
  $$\epsilon_D = 0.0200 \quad (2.00\text{ pp disparity expansion allowable})$$
  $$B = 1,000 \quad (\text{paired speaker-cluster bootstrap resamples, } \alpha = 0.05)$$
- **Tripartite Acceptance Rule:** Candidate update $\theta'$ is accepted if and only if all three Upper Confidence Bounds satisfy operating tolerances:
  $$\text{ACCEPT} \iff \begin{cases} \text{UCB}_{95}(\Delta_R) \le \epsilon_R \\ \text{UCB}_{95}(\max_g \Delta_g) \le \epsilon_G \\ \text{UCB}_{95}(\Delta_D) \le \epsilon_D \end{cases}$$
- **Fail-Safe Rollback Semantics:** If rejected, candidate $\theta'$ is discarded and live state $\theta_t$ is preserved: $\theta_{t+1} \leftarrow \theta_t$. The system never rolls back to $\theta_{t-1}$.
- **Qualification Scope:** Evaluates whether the identical, un-tuned DSG controller operates safely across all 3 Stage-2 CTC backbones.

### 5.4 The DSG Freeze Barrier
Upon completion of Stage 5M, a formal cryptographic freeze is executed:
- All tolerances ($\epsilon_R, \epsilon_G, \epsilon_D$), bootstrap seeds, gate contracts, and candidate rollback rules are permanently locked in `configs/dsg_frozen_final.json`.
- A formal `reports/dsg_freeze_certificate.md` is emitted.
- **No adaptive tuning or hyperparameter adjustments are permitted for Stage 6.**

### 5.5 Stage 6M — Final Cross-Dataset & Held-Out Validation
- **Evaluation Stream:** Untouched Common Voice 27.0 holdout (`datasets/splits/stage5_external_eval.csv`, $N = 900$ clips, 60 speakers, 6 strata, 8,667 words).
- **Held-Out CTC Backbones:** `hubert_large`, `xlsr_english`, `wav2vec2_large_lv60`, `wav2vec2_large_robust`.
- **Overlap CTC Controls:** `wav2vec2_base`, `data2vec_base` (provides cross-dataset replication).
- **Static Seq2Seq Portability:** `whisper_base`, `distil_whisper_small`.
- **Generalization Assessment:** Tests whether the frozen DSG controller generalizes to genuinely unseen model families without prior exposure.

---

## 6. Leakage Firewall and Verification Rules

1. **Speaker Disjointness Invariant:**
   $$\mathcal{S}(\text{Sentinel}) \cap \mathcal{S}(\text{Holdout}) = \emptyset \quad (30 \text{ speakers} \cap 60 \text{ speakers} = \emptyset)$$
   $$\mathcal{S}(\text{Calibration}) \cap \mathcal{S}(\text{Holdout}) = \emptyset$$
2. **Label Isolation Sanitizer:** The online adaptation process receives only `UnlabeledAudioBatch` instances (audio filepath and duration). Ground-truth text, word counts, speaker IDs, and demographic group IDs are firewalled offline.
3. **Prequential Invariant:** Every incoming window $B_t$ is transcribed with live parameters $\theta_t$ and scored offline *before* unsupervised adaptation on $B_t$ is initiated.
4. **Reproducibility Guarantee:** All stream orderings, resample indices, acoustic corruptions, and gate decisions are seeded deterministically.

---

## 7. Protocol Status & Approval Barrier

This document formally establishes the scientific and architectural requirements for Protocol `v1.1.0-model-expansion`. Execution proceeds strictly stage-by-stage with explicit review and user approval required prior to each subsequent experimental phase.
