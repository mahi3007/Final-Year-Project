# Stage 6M Gate 5: Kaggle Runtime Mount & Hardware Preflight Audit Report

**Report Identifier:** `STAGE6M-GATE5-KAGGLE-MOUNT-AUDIT-20261108`  
**Timestamp UTC:** `2026-11-08T07:59:11.484901+00:00`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Authorization:** `STAGE6M-GATE5-AUTH-DECISION-20261108`  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Authoritative Release Digest:** `cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4`  
**Target Execution Environment:** Kaggle Virtual GPU Cluster (**NVIDIA Tesla T4 × 2**)  
**Mounted Private Dataset:** `venkataakhil07/stage6m-frozen-benchmark`  
**Runtime Preflight Verdict:** **`RUNTIME_PREFLIGHT_PASSED`**  

---

## 1. Executive Summary

This audit report records empirical execution evidence from the live Kaggle GPU worker node running under kernel `venkataakhil07/stage-6m-gate-5-runtime-mount-audit`. All six verification steps mandated by the Project Lead's formal authorization have been evaluated directly on the worker node prior to any model loading or confirmatory inference.

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ STAGE 6M: GATE 5 RUNTIME MOUNT AUDIT VERDICT: RUNTIME_PREFLIGHT_PASSED                       ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 1. Dataset Mount:              /kaggle/input/stage6m-frozen-benchmark (Fail-closed verified)         ║
║ 2. Archive vs Extracted State: Extracted directories detected (audio, splits, configs, src)          ║
║ 3. Physical Audio Inventory:   Exactly 18,000 MP3s, 672,970,785 bytes (0 zero-byte files)            ║
║ 4. Cryptographic Catalogue:    18,000 / 18,000 hashes bitwise exact against SHA256_CATALOGUE.json    ║
║ 5. Reserve Isolation:          0 reserve files present (975 reserve clips 100% physically excluded)  ║
║ 6. Transcript Blinding:        16,500 evaluation transcripts null; sealed transcript key unmounted   ║
║ 7. Virtual GPU Topology:       NVIDIA Tesla T4 × 2 (GPU 0: 14.56 GB, GPU 1: 14.56 GB)                ║
║ 8. Software Environment:       Python 3.13.16, PyTorch 2.11.0+cu130, CUDA 13.0                  ║
║ 9. Release Package Identity:   cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4      ║
║ 10. Audited Runner SHA-256:    728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1      ║
║ 11. Confirmatory Notebook:     c5628b62918ca65772d7ca21045793ae65e674a9cd4c248d70592cf3427d2b14      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Step 1: Kaggle Dataset Mount & Top-Level Inventory Verification

The dataset mount point was audited directly on the Kaggle container filesystem. Fail-closed assertion confirmed the dataset root is present at `/kaggle/input/stage6m-frozen-benchmark` with zero reliance on unsafe local fallbacks.

- **Mount Point:** `/kaggle/input/datasets/venkataakhil07/stage6m-frozen-benchmark`
- **Mount Verification Status:** `PASSED`
- **Extraction Disposition:** Kaggle backend automatically extracted the uploaded directory archives into native filesystem folders upon deployment completion (`is_audio_extracted: True`).
- **Top-Level Inventory (6 items):**
  - `SHA256_CATALOGUE.json`
  - `audio`
  - `configs`
  - `requirements-kaggle-lock.txt`
  - `splits`
  - `src`

---

## 3. Step 2: Audio Availability, Exactness & Reserve Isolation

The audio cohort was scanned directly from the mounted input path:

- **Audio Directory:** `/kaggle/input/stage6m-frozen-benchmark/audio/cohort3_reconciled_assets`
- **Total Physical MP3 Files:** `18,000` (Protocol requirement: exactly 18,000)
- **Total Physical Audio Bytes:** `672,970,785` bytes (Protocol requirement: exactly 672,970,785 bytes)
- **Frozen Catalogue Verification:** All 18,000 physical recordings were SHA-256 hashed on the GPU worker and compared against [`SHA256_CATALOGUE.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/dist/kaggle_dataset/SHA256_CATALOGUE.json) (`e7187136c5004623f1f3044eb60587efbd201f4c9006bb081d91a94efa8ebaf8`):
  - **Catalogue Matches:** `18,000` / 18,000 (100% bitwise exact match)
  - **Catalogue Mismatches:** `0`
  - **Missing Files:** 0
- **Cohort Role Breakdown:**
  - **Confirmatory Evaluation Clips:** `16,500` (Expected: 16,500)
  - **Gate-Reference Sentinel Clips:** `1,500` (Expected: 1,500)
  - **Australian Reserve Clips:** **`0`** (Expected: 0)
- **Reserve Disjointness Proof:** Cross-referencing all 18,000 mounted audio filenames against the 975 reserve recording IDs from the final manifest yielded **exactly 0 overlapping files**, proving complete physical isolation of the reserve pool.

---

## 4. Step 3: Transcript Isolation & Sealed Key Exclusion Audit

Transcript accessibility was verified against the online inference manifest and container filesystem:

- **Online Inference Manifest:** [`splits/stage6m_cohort3_online_inference_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_online_inference_manifest.json)
- **Evaluation Transcript Blinding:** All 16,500 evaluation records contain `transcript: null` (`eval_transcripts_shielded: True`). Zero evaluation labels are present in the online manifest.
- **Gate-Reference Transcripts:** 1,500 gate-reference records contain reference transcripts strictly for Arm 3 sentinel candidate screening against `sample_sentinel[:20]`.
- **Sealed Key Scan:** Recursive filesystem scan across `/kaggle/input` and `/kaggle/working` for `stage6m_cohort3_sealed_evaluation_transcripts.json` returned **0 occurrences** (`sealed_key_present: False`). The sealed evaluation key remains strictly unmounted and offline until Gate 6.

---

## 5. Step 4: Hardware Accelerator Environment (NVIDIA Tesla T4 × 2)

Kaggle GPU runtime specifications were measured via PyTorch and CUDA runtime calls:

- **Python Version:** `3.13.16`
- **PyTorch Build:** `2.11.0+cu130`
- **CUDA Runtime:** `13.0`
- **CUDA Available:** `True`
- **Device Count:** `2` (Approved Dual GPU Topology)
- **GPU Accelerators Inventory:**
  - **GPU 0:** `Tesla T4` — **14.56 GB GDDR6 VRAM**
  - **GPU 1:** `Tesla T4` — **14.56 GB GDDR6 VRAM**

- **Topology Compliance:** NVIDIA Tesla T4 × 2 confirmed. Both devices offer discrete memory spaces (>= 14.0 GB each), satisfying Section 14.7 compute infrastructure requirements.

---

## 6. Step 5: Cryptographic Matrix & Frozen Release Authentication

The cryptographic identities of all execution components were audited against authoritative frozen digests:

| Component / Artifact | Expected Authoritative SHA-256 | Measured Runtime SHA-256 | Status |
| :--- | :--- | :--- | :---: |
| **Release Archive** | `cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4` | `cfa471be9b2faa7a67b98826cc1b68c1d92380aecbf229d57889e17d4e47d8b4` | **MATCH** |
| **Audited Runner** | `728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1` | `728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1` | **MATCH** |
| **Confirmatory Notebook** | `c5628b62918ca65772d7ca21045793ae65e674a9cd4c248d70592cf3427d2b14` | `c5628b62918ca65772d7ca21045793ae65e674a9cd4c248d70592cf3427d2b14` | **MATCH** |
| **Online Manifest** | `0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1` | `0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1` | **MATCH** |
| **Final Manifest** | `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` | **MATCH** |
| **Disposition Ledger** | `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` | `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` | **MATCH** |
| **SHA256 Catalogue** | `e7187136c5004623f1f3044eb60587efbd201f4c9006bb081d91a94efa8ebaf8` | `e7187136c5004623f1f3044eb60587efbd201f4c9006bb081d91a94efa8ebaf8` | **MATCH** |

---

## 7. Step 6: Final Execution Readiness Determination

All six verification steps mandated under formal Project Lead decision `STAGE6M-GATE5-AUTH-DECISION-20261108` have passed with 100% compliance.

```
══════════════════════════════════════════════════════════════════════════════════════════════════════
FINAL VERDICT: RUNTIME_PREFLIGHT_PASSED
Execution Clearance: The Kaggle GPU container is cryptographically authentic, hardware-compliant,
and fully isolated. The Stage 6M confirmatory three-arm benchmark may now proceed.
══════════════════════════════════════════════════════════════════════════════════════════════════════
```

### Protocol Constraints Enforced
1. **Gate 5 Confirmatory Stream:** Exactly 16,500 evaluation clips across 4,125 streaming windows ($K=4$).
2. **Gate-Reference Stream:** Exactly 1,500 clips restricted to Arm 3 sentinel candidate screening.
3. **Australian Reserve Pool:** Exactly 0 clips in runtime environment (100% physically excluded).
4. **Gate 6 Multiplicity Analysis:** Blocked and offline until Gate 5 prediction streams are frozen.
