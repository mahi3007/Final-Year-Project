# Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR (DSG-CTTA)

**Extended Title:** Disparity-Aware Continual Test-Time Adaptation for Accent-Robust ASR: Characterizing and Controlling Adaptation-Induced Performance Disparities  
**Protocol Version:** `v1.0.0-canonical`  
**Current Stage:** Stage 0 (Protocol Freeze) $\to$ Stage 1 (Data Pipeline & Baseline Evaluation)

---

## 1. Core Research Problem & Questions

Under distribution shift, Continual Test-Time Adaptation (CTTA) updates deployed Automatic Speech Recognition (ASR) models using incoming unlabeled audio streams. While average Word Error Rate (WER) may improve globally, adaptation can induce **subgroup regression** and **disparity amplification** across speech varieties.

- **RQ-S (Scientific Question):** How does continual test-time adaptation change group-level ASR performance and disparity after accounting for measurable confounders?
- **RQ-I (Intervention Question):** Can a risk-controlled update policy limit group regression and disparity growth while retaining useful adaptation gain?
- **RQ1:** How much raw group disparity remains after controlling for measurable factors (SNR, speech rate, device)?
- **RQ2:** Can a small frozen labeled sentinel panel predict whether an unlabeled adaptation update will be harmful on unseen future data?
- **RQ3:** What is the trade-off between adaptation gain, subgroup regression, disparity growth, rejection rate, and compute?

---

## 2. Terminology & Label Invariant Rule

> **MANDATORY SCIENTIFIC RULE:** All analyses must use the exact group variable provided by the dataset metadata. If the dataset provides `state`, `district`, or `native_region` without validated dialectal annotations, the analysis is strictly designated as **regional/native-region disparity**. Accent labels are never inferred from geography.

---

## 3. The 6-Model Laptop-Suited Architecture Suite

To perform extensive cross-model static audits and comparative evaluations within the CPU and 16GB RAM envelope:

| # | Model Identifier | Architecture Family | Parameters | Role |
|---|-------------------|---------------------|------------|------|
| 1 | `facebook/wav2vec2-base-960h` | Self-Supervised CTC | 95M | **Primary Track A Backbone** |
| 2 | `openai/whisper-base` | Seq2Seq Encoder-Decoder | 74M | **Secondary Track B Backbone** |
| 3 | `facebook/hubert-base-ls960` | Hidden-Unit BERT CTC | 95M | **Static Audit Model 1** |
| 4 | `facebook/data2vec-audio-base-960h` | Multimodal SSL CTC | 95M | **Static Audit Model 2** |
| 5 | `distil-whisper/distil-small.en` | Distilled Seq2Seq | 166M | **Static Audit Model 3** |
| 6 | `jonatasgrosman/wav2vec2-large-xlsr-53-english` | Cross-Lingual XLS-R CTC | 317M | **Static Audit Model 4** |

---

## 4. Repository Structure

```
final year project main/
├── configs/
│   └── default_config.yaml
├── docs/
│   ├── protocol_freeze.md
│   ├── dataset_report.md
│   └── data_card.md
├── datasets/
│   ├── fixture/
│   └── splits/
├── reports/
│   ├── baseline/
│   └── audit/
├── src/
│   └── dsg_ctta/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── data/
│       │   ├── schema.py
│       │   ├── normalization.py
│       │   ├── acoustic.py
│       │   ├── splits.py
│       │   └── fixtures.py
│       ├── models/
│       │   ├── base_adapter.py
│       │   ├── wav2vec2_base.py
│       │   ├── whisper_models.py
│       │   ├── ctc_models.py
│       │   ├── mock_model.py
│       │   └── registry.py
│       ├── offline/
│       │   ├── metrics.py
│       │   ├── aggregation.py
│       │   ├── bootstrap.py
│       │   └── glmm.py
│       ├── online/
│       │   ├── label_isolation.py
│       │   ├── stream.py
│       │   └── sentinel.py
│       ├── experiments/
│       │   └── runner.py
│       └── reporting/
│           └── tables.py
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_normalization.py
│   ├── research_validity/
│   │   ├── test_speaker_leakage.py
│   │   ├── test_sentinel_contamination.py
│   │   ├── test_label_isolation.py
│   │   └── test_seed_reproducibility.py
│   └── integration/
│       └── test_pipeline.py
├── pyproject.toml
└── README.md
```

---

## 5. CLI Commands

```powershell
# 1. Generate multi-group synthetic research fixture
python -m dsg_ctta data fixture --output-dir datasets/fixture

# 2. Generate 5-way speaker-disjoint partitions with zero leakage
python -m dsg_ctta data split --manifest-path datasets/fixture/raw_manifest.json --output-dir datasets/splits

# 3. Run baseline evaluation
python -m dsg_ctta baseline run --split-csv datasets/splits/final_test.csv --model-name mock_asr

# 4. Run cross-model disparity audit
python -m dsg_ctta audit run --split-csv datasets/splits/final_test.csv --models mock_asr

# 5. Run all unit and research-validity tests
python -m pytest tests/ -v
```
