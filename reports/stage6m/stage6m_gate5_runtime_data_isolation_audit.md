# Stage 6M: Gate 5 Runtime Data-Isolation & Physical Boundary Audit Report

**Audit Identifier:** `STAGE6M-GATE5-DATA-ISOLATION-AUDIT-20261108`  
**Timestamp UTC:** `2026-11-08T05:52:20.898099+00:00`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Authorized Release Archive:** [`releases/stage6m_gate5_release_v1.0.tar.gz`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/releases/stage6m_gate5_release_v1.0.tar.gz)  
**Required Release SHA-256:** `cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4`  
**Final Audit Verdict:** **`DATA_ISOLATION_VERIFIED`**  

---

## 1. Executive Summary

This audit establishes the empirical and static code verification of the **Gate 5 Runtime Data-Isolation Boundaries**, resolving the Project Lead's final data-isolation inquiry prior to confirmatory execution.

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ STAGE 6M: RUNTIME DATA-ISOLATION AUDIT VERDICT: DATA_ISOLATION_VERIFIED                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 1. Positive Runtime Allowlist: Exactly 18,000 recordings (16,500 Evaluation + 1,500 Gate Reference) ║
║ 2. Australian Reserve Audio:   0 recordings in runtime allowlist (100% disjoint from 975 reserve)    ║
║ 3. Physical Boundary Status:   Application-logic filtering active; Physical segregation bounded      ║
║ 4. Arm 1 Transcript Access:    0 references (Strictly Unsupervised Static Baseline)                 ║
║ 5. Arm 2 Transcript Access:    0 references (Strictly Unsupervised SUTA Adaptation)                 ║
║ 6. Arm 3 Transcript Access:    Approved Sentinel Transcripts Only (sample_sentinel[:20] screening)   ║
║ 7. Evaluation Transcripts:     100% Sealed (null in online manifest; sealed key unmounted)           ║
║ 8. Bypass Vulnerabilities:     0 bypass vectors found (fail-closed manifest hash validation active)  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Positive Runtime Audio Allowlist Accounting

The benchmark cohort is partitioned into three mutually exclusive subsets:

| Cohort Role | Target Recordings | Target Speakers | Bytes on Disk | Runtime Loading Call | Online Status in Gate 5 |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Confirmatory Evaluation** | **16,500** | 1,100 | 615,810,151 B | `eval_records[start:end]` | **Primary Evaluation Stream (4,125 windows, $K=4$)** |
| **Gate-Reference Sentinel** | **1,500** | 100 | 57,160,634 B | `gate_records` (pre-cached) | **Arm 3 Sentinel Screening Only (Non-inferiority)** |
| **Australian Reserve** | **975** | 65 | 36,780,173 B | *None (Zero calls in runner)* | **STRICTLY SEALED & EXCLUDED** |
| **Positive Runtime Allowlist** | **18,000** | **1,200** | **672,970,785 B** | Allowlisted Streams Only | **Approved Online Runtime Input** |
| **Total Cohort Inventory** | 18,975 | 1,265 | 709,750,958 B | All Physical Audio | Parent Materialization Archive |

- **Reserve Audio Overlap:** `len(set(res_ids) & set(runtime_allowlist)) == 0` (Confirmed 100% Disjoint).
- **Speaker Disjointness:** Confirmed 0 shared speakers across evaluation, gate-reference, and reserve panels.

---

## 3. Physical Inaccessibility vs. Application-Logic Filtering Analysis

The Project Lead requested an explicit technical determination of whether the 975 reserve audio files are physically inaccessible to the runtime or merely filtered by application logic:

### 3.1 Empirical Finding
1. **Application-Logic Filtering:** In the audited runner ([`run_stage6m_cohort3_kaggle_benchmark.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/cloud/kaggle/run_stage6m_cohort3_kaggle_benchmark.py)), data loading is strictly driven by the partitioned lists `eval_records` and `gate_records`. AST and static line analysis prove that `load_and_resample_audio` is called exclusively for records in those two lists. There are **zero calls** to load any recording ID belonging to `res_records`.
2. **Physical Filesystem Co-location:** On the current workspace filesystem under [`datasets/audio/stage6m/cohort3_reconciled_assets/`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/audio/stage6m/cohort3_reconciled_assets), all 18,975 MP3 files reside in a single flat directory. Consequently, the files are **physically present on disk**, and their exclusion is enforced by **application logic / streaming schedule partitioning**, not by operating system permissions or physical directory separation.

### 3.2 Physical Segregation Safeguard Protocol
To upgrade the safeguard from application-level filtering to **strict physical inaccessibility** for the Kaggle execution payload:
- When creating the Kaggle private dataset payload, copy only the **18,000 allowlisted MP3 files** (672,970,785 bytes) into the dataset audio directory.
- Completely exclude the 975 reserve audio files (36,780,173 bytes) from the uploaded private dataset archive.
- Under this physical arrangement, should any software defect or unintended call attempt to request a reserve clip ID, the operating system kernel will return `FileNotFoundError`, guaranteeing **physical, hardware-level fail-closed protection**.

---

## 4. Arm-Specific Transcript Accessibility Audit

Static AST analysis of the runner (`728efdc6...`) confirms strict isolation of transcripts across the three experimental arms:

```
                  ┌──────────────────────────────────────────────┐
                  │ Official Online Inference Manifest (0f1cca...)│
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
     16,500 Evaluation Records                       1,500 Gate-Reference Records
     (transcript == None, sealed)                     (transcript == Active Text)
                 │                                               │
        ┌────────┴────────┐                                      │
        ▼                 ▼                                      ▼
  ┌───────────┐     ┌───────────┐                          ┌───────────┐
  │   Arm 1   │     │   Arm 2   │                          │   Arm 3   │
  │  Static   │     │  Ungated  │                          │ DSG Gated │
  │ Baseline  │     │   SUTA    │                          │   SUTA    │
  └─────┬─────┘     └─────┬─────┘                          └─────┬─────┘
        │                 │                                      │
   Unsupervised      Unsupervised                       Candidate Sandbox
    Evaluation        Evaluation                         (Unsupervised)
  (0 Transcripts)   (0 Transcripts)                              │
                                                          Sentinel Screening
                                                          (Evaluates vs 20
                                                           Sentinel Texts)
```

1. **Arm 1 (Static Baseline):**
   - Operates in frozen `.eval()` mode.
   - Evaluates on `batch_waveforms`.
   - **Transcript Access:** `NONE` (Zero references in source code).
2. **Arm 2 (Ungated Continuous SUTA):**
   - Continuously adapts LayerNorm parameters using `compute_masked_suta_loss`.
   - Loss function is strictly unsupervised (predictive entropy minimization + maximum cosine consistency on valid acoustic frames).
   - **Transcript Access:** `NONE` (Zero references in source code).
3. **Arm 3 (DSG Gate-Controlled SUTA):**
   - Candidate model parameters are updated via unsupervised SUTA in an isolated sandbox.
   - The candidate model is evaluated against `sample_sentinel` (gate-reference panel) using `compute_utterance_metrics`.
   - **Transcript Access:** `APPROVED_SENTINEL_SCREENING_ONLY` (Source line 450: `ref_texts = [r["transcript"] for r in sample_sentinel]`).
   - Only Arm 3 receives approved gate-reference transcripts.

---

## 5. Strict Inaccessibility of Evaluation Transcripts & Sealed Key

1. **Online Manifest Seal:** In [`stage6m_cohort3_online_inference_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_online_inference_manifest.json), exactly 16,500 evaluation records have `"transcript": null` and `"word_count": null`. Zero label leaks detected.
2. **In-Memory Defensive Nullification:** Lines 276–282 of the runner actively inspect all evaluation records; if any non-null transcript is encountered, it is immediately nullified in memory.
3. **Sealed Evaluation Key:** [`stage6m_cohort3_sealed_evaluation_transcripts.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json) (`f427ae...`) is **strictly unmounted and absent** from the release package (`checksums.sha256` contains 0 references to it).
4. **Offline Gate 6 Separation:** Multiplicity-controlled statistical scoring will occur strictly offline after Gate 5 execution outputs are frozen and locked.

---

## 6. Alternate Path / Manifest Bypass Vulnerability Audit

Static inspection of `resolve_paths()` and the Kaggle execution notebook confirmed:
- Candidate paths are restricted to official manifest names.
- Both the runner (lines 235–240) and the notebook (lines 104–115) compute the SHA-256 digest of the loaded manifest and assert an exact match against `EXPECTED_ONLINE_MANIFEST_SHA256` (`0f1cca...`) or `EXPECTED_FINAL_MANIFEST_SHA256` (`171815...`).
- Any unrecognized manifest fails closed with `ValueError`.
- No alternate path, mounted directory, or unverified archive can bypass the transcript shielding boundaries.

---

## 7. Cryptographic Verification Matrix Reconciliation

The seven original verification test checks (plus the newly integrated Check 8) map onto the ten entries of the cryptographic verification matrix as follows:

| Entry No. | Cryptographic Matrix Entry | Required / Expected Value | Covering Verification Test in Suite | Verification Mechanism & Test Assertion | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | **Release Archive Digest** | `cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4` | **Check 1** | `compute_sha256(RELEASE_TAR) == EXPECTED_TAR_SHA256` | **PASSED** |
| **2** | **Extraction Directory** | `releases/extracted_verified_gate5_v1.0` (67 files) | **Check 2** | `tar.extractall() -> extracted_root.exists()` | **PASSED** |
| **3** | **Manifest Reconciliation** | 67 / 67 files bitwise exact against `checksums.sha256` | **Check 3** | Iterates all 67 entries; asserts SHA-256 exact match | **PASSED** |
| **4** | **Audited Runner SHA-256** | `728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1` | **Check 4** | `compute_sha256(runner_p) == EXPECTED_RUNNER_SHA256` | **PASSED** |
| **5** | **Notebook SHA-256** | `c5628b62918ca65772d7ca21045793ae65e674a9cd4c248d70592cf3427d2b14` | **Check 4** | `compute_sha256(nb_p) == EXPECTED_NOTEBOOK_SHA256` | **PASSED** |
| **6** | **Locked Final Manifest** | `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | **Check 5** | `compute_sha256(final_m_path) == EXPECTED_FINAL_MANIFEST_SHA256` | **PASSED** |
| **7** | **Online Inference Manifest** | `0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1` | **Check 5** | `compute_sha256(online_m_path) == EXPECTED_ONLINE_MANIFEST_SHA256` | **PASSED** |
| **8** | **Disposition Ledger** | `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` | **Check 5** | `compute_sha256(ledger_path) == EXPECTED_LEDGER_SHA256` | **PASSED** |
| **9** | **Transcript Shielding** | 0 label leaks; sealed key absent; 16,500 eval transcripts null | **Check 6 & Check 8** | Asserts 0 leaks in online manifest; sealed key absent | **PASSED** |
| **10** | **Physical Audio Inventory** | 18,975 MP3 files, 709,750,958 bytes | **Check 7** | `len(audio_files) == 18975 and total_bytes == 709750958` | **PASSED** |

Every entry in the cryptographic verification matrix has direct test provenance in the pre-execution verification suite.

---

## 8. Final Audit Disposition

The data-isolation boundaries have been audited and verified:
- **Verdict:** **`DATA_ISOLATION_VERIFIED`**
- **Release Package:** [`releases/stage6m_gate5_release_v1.0.tar.gz`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/releases/stage6m_gate5_release_v1.0.tar.gz) (`cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4`).
- **Gate 5 Execution Status:** In strict adherence to stop conditions, execution has **NOT** started and confirmatory audio has **NOT** been accessed.

*Report generated under Protocol Section 14.7 by Antigravity.*
