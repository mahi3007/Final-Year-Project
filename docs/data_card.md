# Dataset Data Card & Provenance Specification

## 1. Metadata Schema Definition

Each utterance/recording processed in the pipeline carries a strictly structured metadata record:

```json
{
  "utterance_id": "spk01_utt0012",
  "speaker_id": "spk01",
  "group_id": "Hindi",
  "group_type": "native_language", 
  "audio_filepath": "datasets/primary/audio/spk01_utt0012.wav",
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "sampling_rate_hz": 16000,
  "duration_seconds": 3.42,
  "snr_db": 24.5,
  "speech_rate_wpm": 142.1,
  "device_id": "studio_mic_01",
  "reference_raw": "AUTHOR OF THE DANGER TRAIL, PHILIP STEEL, ETC.",
  "reference_normalized": "AUTHOR OF THE DANGER TRAIL PHILIP STEEL ETC",
  "reference_word_count": 8,
  "reference_char_count": 43,
  "partition": "final_test",
  "provenance": {
    "source_dataset": "L2-ARCTIC",
    "dataset_release": "v2.0",
    "ingestion_timestamp": "2026-09-28T14:00:00Z",
    "normalization_version": "v1.0.0-canonical"
  }
}
```

---

## 2. Text Normalization Invariants

To ensure fair and rigorous ASR scoring across models:
1. **Case Invariant:** Transcripts are converted to uppercase (or lowercase, standardized consistently across reference and hypothesis).
2. **Punctuation Filtering:** All punctuation (periods, commas, quotes, hyphens, colons, semicolons, exclamation marks, question marks) are removed.
3. **Whitespace Standardization:** Multiple consecutive whitespace characters are collapsed into a single space, and leading/trailing whitespace is trimmed.
4. **Number / Contraction Handling:** Numbers are spoken words or standardized via consistent rule mappings.
5. **No Model-Specific Cheating:** The same normalization pipeline is applied identically to reference text and model hypothesis text before computing Levenshtein alignment.

---

## 3. Strict Speaker-Disjoint Split Generator Requirements

The split generator partitions a dataset into:
1. `development.csv` (Development / prototyping)
2. `calibration.csv` (Calibrating $\epsilon$ safety bounds, window sizes $K$)
3. `sentinel_candidates.csv` (Frozen sentinel pool)
4. `final_test.csv` (Single-pass prequential test stream)
5. `external_validation.csv` (Independent corpus)

### Mathematical Invariants Checked by Blocking Tests:
$$\text{UniqueSpeakers}(\text{Full}) = \bigcup_{p \in \mathcal{P}} \text{UniqueSpeakers}(p)$$
$$\forall p_i, p_j \in \mathcal{P}, i \ne j \implies \text{UniqueSpeakers}(p_i) \cap \text{UniqueSpeakers}(p_j) = \emptyset$$
$$\text{SentinelSpeakers} \cap \text{AdaptationSpeakers} = \emptyset$$
