# Cross-Model Baseline Disparity Audit Report (Stage 1 & 2)

**Partition:** `final_test` | **Total Recordings:** 9

## 1. Global & Disparity Comparison Table

| Model Name | Corpus WER (%) | Spk-Macro WER (%) | Mean CER (%) | Min Group WER (%) | Max Group WER (%) | Disparity D (%) | Best Group | Worst Group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mock_asr` | 80.52% | 80.10% | 64.88% | 72.00% | 96.30% | **24.30%** | Region_East | Region_North |

## 2. Detailed Per-Model Group Breakdowns

### Model: `mock_asr`

| Group ID | Speakers | Utterances | Ref Words | Substitutions | Deletions | Insertions | Corpus WER (%) | Spk-Macro WER (%) | Mean CER (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Region_East** | 1 | 3 | 25 | 14 | 4 | 0 | 72.00% | 72.00% | 56.73% |
| **Region_North** | 1 | 3 | 27 | 20 | 6 | 0 | 96.30% | 96.30% | 81.19% |
| **Region_South** | 1 | 3 | 25 | 14 | 4 | 0 | 72.00% | 72.00% | 56.73% |

