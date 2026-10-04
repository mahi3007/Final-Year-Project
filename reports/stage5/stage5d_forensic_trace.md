# Stage 5D Forensic Trace: Root Cause Analysis of DSG Evaluator Failure

**Execution Date:** 2026-10-03  
**Protocol Version:** v1.0-cv27-amended  
**Target:** Investigating the root cause of `FAIL-CLOSED: Evaluator exception occurred: Audio file not found: common_voice_en_33001339.mp3` across all 225 DSG decision windows.

---

## 1. Executive Summary

In Stage 5B and Stage 5C, all 225 DSG prequential candidate decisions were logged as `REJECT`. A forensic audit revealed that **none** of the 225 rejections were triggered by statistical threshold violations ($\text{UCB}_{95}(\Delta_R) > \epsilon_R$, $\text{UCB}_{95}(\max_g \Delta_g) > \epsilon_G$, or $\text{UCB}_{95}(\Delta_D) > \epsilon_D$). 

Instead, every single rejection was caused by an unhandled `FileNotFoundError` during audio loading inside the sentinel evaluator:
```
FAIL-CLOSED: Evaluator exception occurred: Audio file not found: common_voice_en_33001339.mp3
```

This report documents the forensic trace of the execution path, identifies why the sentinel audio files were absent from local storage, explains the breakdown in path resolution, and defines the canonical resolution contract required for Stage 5D.

---

## 2. End-to-End Failure Chain Trace

The failure was traced across 7 distinct software and data stages:

```
datasets/splits/stage5_sentinel_panel.csv
        │  (Column 'audio_path' contains raw Common Voice filename: common_voice_en_33001339.mp3)
        ▼
scripts/run_stage5b_external_eval.py (Line 255, 352)
        │  (sentinel_df.to_dict(orient="records") passed directly to evaluator)
        ▼
src/dsg_ctta/controller/evaluator.py (Line 104)
        │  (Extracts audio_path = str(utt.get("audio_filepath") or utt.get("audio_path", "")))
        │  (audio_path evaluates to bare string "common_voice_en_33001339.mp3")
        ▼
src/dsg_ctta/models/wav2vec2_base.py (Line 31)
        │  (Calls load_and_resample_audio("common_voice_en_33001339.mp3", target_sr=16000))
        ▼
src/dsg_ctta/data/acoustic.py (Line 30-31)
        │  (Checks os.path.exists("common_voice_en_33001339.mp3") in project root)
        │  (File does NOT exist on disk -> raises FileNotFoundError)
        ▼
src/dsg_ctta/controller/evaluator.py (Line 158-166)
        │  (Catches Exception as exc; passes exception_msg to gate)
        ▼
src/dsg_ctta/controller/gate.py (Line 52-58)
        │  (Appends "FAIL-CLOSED: Evaluator exception occurred: ..." to rejection_reasons)
        │  (Forces decision="REJECT", ucb_r=inf, ucb_max_group=inf, ucb_d=inf)
        ▼
dsg_decision_log.csv (225 / 225 rows logged as FAIL-CLOSED REJECT)
```

---

## 3. Detailed Forensic Findings

### Finding A: Materialization Asymmetry
When the audio materialization script (`scripts/materialize_stage5_audio.py`) was developed for Stage 5B, its scope was explicitly hardcoded to:
```python
CANONICAL_CSV = SPLITS_DIR / "stage5_external_eval.csv"
```
It selectively downloaded and extracted **only the 900 external evaluation clips** (`stage5ext_00001.mp3` through `stage5ext_00900.mp3`). The 300 sentinel panel clips curated in `datasets/splits/stage5_sentinel_panel.csv` were **never targeted or materialized** to disk.

### Finding B: Missing Canonical Audio Resolver
In `scripts/run_stage5b_external_eval.py`:
- External evaluation clips were mapped explicitly via `AUDIO_DIR / f"{recording_id}.mp3"`.
- In contrast, sentinel panel evaluation passed `sentinel_df.to_dict(orient="records")` directly into `evaluator.evaluate_candidate()`.
- The evaluator looked for `audio_filepath` or `audio_path`, finding `"common_voice_en_33001339.mp3"`.
- No path resolver existed to map canonical sentinel IDs (`sentinel_01_01_01`) or source filenames to a verified local directory (`datasets/external/common_voice_27/sentinel_audio/`).

### Finding C: Bare Filename Resolution Assumption
In `src/dsg_ctta/data/acoustic.py`:
```python
if isinstance(filepath_or_array, str):
    if not os.path.exists(filepath_or_array):
        raise FileNotFoundError(f"Audio file not found: {filepath_or_array}")
```
Passing a bare relative filename like `"common_voice_en_33001339.mp3"` assumes the working directory contains the file. Because the file was neither in the working directory nor materialized in any project subfolder, the exception was immediate and deterministic on every candidate evaluation.

### Finding D: Decision Reason Conflation
In `src/dsg_ctta/controller/gate.py`, the gate produced:
- `decision: "REJECT"`
- `rejection_reasons: ["FAIL-CLOSED: Evaluator exception occurred: ..."]`

However, the high-level decision structure did not explicitly expose a standardized classification separating:
- `STATISTICAL_GATE_REJECTION` (candidate evaluated, finite metrics produced, but $\text{UCB} > \epsilon$)
from:
- `FAIL_CLOSED_EVALUATOR_ERROR` (candidate could not be evaluated due to missing data, numerical corruption, or runtime exception).

This conflation led the Stage 5B reporting narrative to state that "DSG prevented 88 harmful updates," when in reality the statistical gate had never evaluated acoustic waveforms.

---

## 4. Integrity and Air-Gap Invariant Verification

Before proceeding with repair, the following structural invariants were verified:

1. **Air-Gap Preservation:**
   - Sentinel panel speakers ($N=30$) and external evaluation speakers ($N=60$) share **0** common speakers.
   - Sentinel panel clips ($N=300$) and external evaluation clips ($N=900$) share **0** common audio files.
2. **Cryptographic CSV Integrity:**
   - `datasets/splits/stage5_sentinel_panel.csv` SHA-256 matches `665009a00660f7e9bbdf8de8a53473fc1249362ca2a5bc0038518313d18f0543` exactly as recorded in `stage5_sentinel_panel.lock.json`.
3. **No Retrospective Leakage:**
   - Transcripts in `stage5_sentinel_panel.csv` are accessible **only** to the sentinel evaluation module for scoring hypotheses; they are never leaked to the online adaptation stream.

---

## 5. Required Remedies (Phases 2 through 5)

1. **Materialize Sentinel Audio Clips:**
   - Stream and extract the 300 sentinel audio clips from the Common Voice 27.0 archive to `datasets/external/common_voice_27/sentinel_audio/{sentinel_id}.mp3`.
   - Validate each clip with `soundfile` and compute SHA-256 cryptographic hashes.
   - Generate `datasets/external/common_voice_27/sentinel_audio_inventory.json` and `datasets/splits/stage5_sentinel_audio_manifest.json`.

2. **Implement Canonical SentinelAudioResolver:**
   - Create `src/dsg_ctta/controller/resolver.py` enforcing:
     - Strict lookup through frozen sentinel manifest/inventory by `sentinel_id` or `source_path`.
     - File existence verification.
     - SHA-256 hash verification against the manifest prior to transcription.
     - Strict fail-closed exception on mismatch, missing file, or empty payload.
     - Zero directory fuzzy search or ad-hoc substitution.

3. **Formally Disentangle Decision Reasons:**
   - Update `GateDecision` to provide `decision_reason` distinguishing `STATISTICAL_GATE_REJECTION` from `FAIL_CLOSED_EVALUATOR_ERROR`.
   - Update `DisparitySafetyGate` to tag the decision category explicitly.

4. **Sentinel Smoke Test:**
   - Execute a single-window deterministic smoke test to verify end-to-end evaluation, finite $\Delta_R, \max_g \Delta_g, \Delta_D$, and $B=1000$ bootstrap replicates with zero evaluator exceptions.

5. **225-Window Prequential Re-execution:**
   - Re-run the full 225-window stream under the frozen protocol ($\epsilon_R=0.0000, \epsilon_G=0.0200, \epsilon_D=0.0200$).
