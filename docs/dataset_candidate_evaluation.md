# Candidate Dataset Evaluation for Global English Accents (Stage 2)

**Project:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR (DSG-CTTA)  
**Protocol Version:** `v1.0.0-canonical`  
**Scope Directive:** Focus on **Global English Accents** (cross-linguistic L1 native background varieties) rather than sub-national regional varieties.

---

## 1. Candidate Dataset Comparison Matrix

| Evaluation Criterion | Candidate 1: **L2-ARCTIC** | Candidate 2: **VCTK Corpus** | Candidate 3: **Mozilla Common Voice (en)** | Candidate 4: **SpeechOcean762** |
|:---|:---|:---|:---|:---|
| **Source & Citations** | Zhao et al., Univ. of Washington (Interspeech) | Yamagishi et al., CSTR Edinburgh | Mozilla Foundation | Zhang et al., OpenSLR-101 |
| **Release / Version** | v2.0 (Official Release) | v0.92 | v13.0+ English Subset | v1.0 |
| **Primary Scope** | Global Non-Native English Varieties | Global Native/L2 English Dialects | Global Self-Reported Accents | Non-Native English Assessment |
| **Validated Group Variable** | `native_language` (L1 Background) | `accent_region` / `accent` | `accent` (Self-Reported) | `l1_language` / `proficiency` |
| **Accent / L1 Groups** | **6 Global Groups:**<br>• Arabic (`ARA`)<br>• Hindi (`HIN`)<br>• Mandarin (`CHI`)<br>• Korean (`KOR`)<br>• Spanish (`SPA`)<br>• Vietnamese (`VIE`) | **7+ Regional/Global Groups:**<br>• Scottish (`Scottish`)<br>• Irish (`Irish`)<br>• English (`English`)<br>• American (`American`)<br>• Canadian (`Canadian`)<br>• Australian (`Australian`)<br>• Indian (`Indian`) | **10+ Uncontrolled Groups:**<br>• US, UK, Canada, Australia, Ireland, South Africa, New Zealand, etc. | 2 Broad Groups (Chinese L1 vs Others) |
| **Speaker Count** | 24 speakers (4 per group: 2M/2F) | 110 speakers (uneven per group) | 1,000+ speakers (sparse per spk) | 250 speakers |
| **Recordings per Speaker** | ~1,132 phonetically balanced sentences | ~400 sentences | 5–50 sentences (highly variable) | 20 sentences |
| **Total Utterances** | ~26,867 recordings | ~44,000 recordings | ~1,000,000+ recordings | 5,000 recordings |
| **Audio Format & Quality** | 16kHz mono WAV, studio clean | 48kHz WAV (resampled to 16kHz) | Mixed MP3/WAV, unverified SNR | 16kHz WAV |
| **Speaker ID Reliability** | **100% Deterministic** (`spk_id` code) | **100% Deterministic** (`pXXX` code) | `client_id` (high noise/anonymized) | Deterministic ID |
| **Speaker-Disjoint Balance** | **Exact:** Exactly 1 spk/group across all 4 partitions | **Imbalanced:** Heavy bias towards Scottish/English | **Sparsely clustered** | Imbalanced |
| **Measurable Confounders** | Word count, SNR, duration, speech rate | Microphone channels (mic1/mic2), SNR | Extreme crowd SNR/device noise | Duration, score |
| **Licensing** | CC BY-NC 4.0 (Non-Commercial Research) | CC BY 4.0 (Open Research) | CC0 / Public Domain | CC BY 4.0 |
| **Download Footprint** | ~3.2 GB (compressed) / ~7 GB raw | ~11 GB | ~80+ GB | ~1.5 GB |
| **CTTA Suitability** | **Highest:** Fixed text prompts enable controlled acoustic shift analysis without lexical confounding | **High:** Multiple prompts, good acoustic diversity | **Low:** Heavy lexical variation confounds acoustic CTTA | **Moderate:** Short assessment clips |

---

## 2. In-Depth Evaluation & Selection

### 2.1 Selected Primary Corpus: **L2-ARCTIC (v2.0)**
- **Why L2-ARCTIC is optimal for Primary Track:**
  1. **Validated Global L1 Backgrounds:** Provides 6 distinct, well-documented global native language backgrounds (`Arabic`, `Hindi`, `Mandarin`, `Korean`, `Spanish`, `Vietnamese`).
  2. **Lexically Balanced Arctic Sentences:** All speakers read phonetically rich CMU Arctic prompt sentences. This decouples acoustic accent shift from vocabulary/lexicon shift, ensuring that WER disparities reflect acoustic-phonetic distribution shift rather than out-of-vocabulary artifacts.
  3. **Perfect 4-Way Speaker Disjointness:** With exactly 4 speakers (2 male, 2 female) per group across 6 groups, the dataset maps with mathematical precision to the 4 canonical primary partitions:
     - `Development`: 6 speakers (1 per group)
     - `Calibration`: 6 speakers (1 per group)
     - `Sentinel Panel`: 6 speakers (1 per group, frozen labeled safety gate)
     - `Final Test Stream`: 6 speakers (1 per group, prequential evaluation)
  4. **Strict Confounder Control:** Standard studio recording setup with high SNR allows testing baseline acoustic robustness and evaluating the impact of controlled SNR and speech rate variations via GLMM.

### 2.2 Selected External Validation Corpus: **VCTK Global Subsets / SpeechOcean762**
- Independent recording environment, distinct sentence prompts, and independent speaker pool to serve as the Stage 9 external validation set.

---

## 3. Metadata & Group Definition Audit

- **Group Variable Name in Ingestion Pipeline:** `native_language`
- **Group Categorization Scope:** `l1_accent` (validated non-native global English variety)
- **Documented Groups:**
  1. `Arabic` (`ARA`): Native Arabic speakers speaking English.
  2. `Hindi` (`HIN`): Native Hindi speakers speaking English.
  3. `Mandarin` (`CHI`): Native Mandarin Chinese speakers speaking English.
  4. `Korean` (`KOR`): Native Korean speakers speaking English.
  5. `Spanish` (`SPA`): Native Spanish speakers speaking English.
  6. `Vietnamese` (`VIE`): Native Vietnamese speakers speaking English.

---

## 4. Invariant Compliance Confirmation
- The group label is explicitly taken from the dataset's validated demographic metadata (`native_language`).
- No geographical inferences (such as country $\to$ accent) are made.
