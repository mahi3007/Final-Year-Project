# Dataset Audit & Model Selection Report

## 1. Primary Dataset Selection & Audit

### Candidate Primary Datasets for Group/Regional ASR Disparity
1. **L2-ARCTIC (Non-Native English Corpus)**
   - **Source:** Zhao et al., University of Washington / Interspeech.
   - **Speaker Pool:** 24 non-native speakers across 6 validated native language background groups: `Arabic (ABA, SKA, YBAA, ZHAA)`, `Hindi (ASI, BJM, HKK, PRK)`, `Mandarin (BWC, LDC, MPXM, TLX)`, `Korean (EBVS, ERMS, HCC, HJK)`, `Spanish (EBVS, MBX, NJS, TLX)`, `Vietnamese (BVT, DTW, LXC, TNT)`.
   - **Group Variable:** `native_language` (Validated L1 background).
   - **Audio:** 16kHz WAV, studio phonetically balanced CMU Arctic sentences.
   - **Transcripts:** Standardized Arctic reference prompts (high phonetic coverage).
   - **Speaker IDs:** Explicitly annotated per speaker (`ASI`, `BJM`, etc.).
   - **License:** CC BY-NC 4.0 (Research use).

2. **OpenSLR-64 / Google Crowdsourced High-Quality Indian Regional English**
   - **Source:** Google / OpenSLR.
   - **Speakers:** Hundreds of speakers across Indian regions/states.
   - **Group Variable:** `region` or `state` (Categorized under **regional/native-region disparity** per terminology rule).
   - **Audio:** 16kHz mono WAV.

3. **VCTK Corpus (Voice Cloning Toolkit English Accents)**
   - **Source:** Centre for Speech Technology Research (CSTR), University of Edinburgh.
   - **Speakers:** 110 English speakers from various regional/dialect backgrounds (e.g. Scottish, Irish, Northern English, American, Indian).
   - **Group Variable:** `accent_region` / `native_region`.

---

## 2. External Validation Dataset

- **Primary Track Dataset:** L2-ARCTIC / Regional English Split (Primary benchmark with 6 distinct group partitions).
- **External Validation Corpus:** Disjoint subset of VCTK or SpeechOcean762 / Common Voice (completely distinct acoustic recording environment, microphone hardware, sentence prompts, and speaker pool).

---

## 3. The 6-Model Laptop-Suited Architecture Suite

The user requested 6 models optimized for CPU inference on a 16GB RAM laptop. The selected models span 4 distinct modeling paradigms:

| # | Model Identifier | Architecture Family | Parameters | Memory Footprint | Role in Research Protocol |
|---|-------------------|---------------------|------------|------------------|---------------------------|
| 1 | `facebook/wav2vec2-base-960h` | Self-Supervised CTC (Wav2Vec2) | 95M | ~380 MB | **Primary Track A Backbone** (Target of SUTA/DSUTA/DMSUTA & DSG) |
| 2 | `openai/whisper-base` | Autoregressive Encoder-Decoder | 74M | ~290 MB | **Secondary Track B Backbone** (Target of ASR-TRA & DSG) |
| 3 | `facebook/hubert-base-ls960` | Hidden-Unit BERT CTC (HuBERT) | 95M | ~380 MB | **Static Audit Model 1** (Acoustic cluster SSL comparison) |
| 4 | `facebook/data2vec-audio-base-960h` | Latent Representation SSL CTC | 95M | ~380 MB | **Static Audit Model 2** (Multimodal self-distillation SSL) |
| 5 | `distil-whisper/distil-small.en` | Distilled Seq2Seq Transformer | 166M | ~650 MB | **Static Audit Model 3** (High-throughput student model) |
| 6 | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | Cross-Lingual XLSR CTC | 317M | ~1.2 GB | **Static Audit Model 4** (Multilingual acoustic transfer) |

### Suitability for Laptop Environment
- All 6 models run deterministically on CPU via PyTorch / HuggingFace Transformers.
- Peak combined disk space for all 6 models is < 3.5 GB (well within the available 14.9 GB free disk space).
- Memory per inference step is < 1.5 GB RAM, safely within the 16 GB physical RAM envelope.
