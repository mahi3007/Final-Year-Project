# Stage 6M Confirmatory Cohort 2: Curation & Strict Integrity Audit Report

> **Audit Verdict:** `PASS`  
> **Timestamp:** 2026-10-25T14:25:42.899767+00:00  
> **Protocol:** `v1.3.4-stage6m-self-authorization-amendment` (ADR-005)  
> **Predicate Level:** `STRICT QUALITY PREDICATE V (locale=='en', up_votes>=2, down_votes<2)`  
> **Deterministic Seed:** `20261020`  
> **Execution Mode:** `AUDIT-ONLY (FAIL-CLOSED)`

---

## 1. Summary Matrix

| Audit Check | Scope | Verdict | Details |
| :--- | :--- | :---: | :--- |
| **1. Prefix Resolution** | 468 Manifest Active Prefixes | `PASS` | Resolved 468/468 prefixes bijectively (1:1). |
| **1B. Accent Homogeneity** | Speaker-Level Homogeneity (B0) | `PASS` | Found 0 heterogeneous speakers. |
| **2. Strict Clip Eligibility** | Strict Quality Predicate V (B0 + V) | `PASS` | 468/468 speakers meet strict quota (0 shortfall). |
| **3. Speaker Disjointness** | Cross-Cohort Isolation | `PASS` | 0 overlap with Cohort 1 (60 spks) and Sentinel Panel (30 spks). Zero leakage. |
| **4. Stratum Preservation** | 6 Pre-specified Strata | `PASS` | Exactly 78 speakers per stratum across all 6 strata. |
| **5. Stream Geometry** | 15 Clips/Speaker Stream | `PASS` | Selected 7020/7020 strict clips across 6 strata. |
| **6. Schema & Naming** | Runner Filename Compatibility | `PASS` | Filename stem convention verified (`cohort2_audio/{recording_id}.mp3`), zero duplicate stems. |

---

## 2. Six-Strata Strict Eligibility Breakdown

| Stratum Name | Total Active Speakers | Strict-Eligible Speakers ($C_{\text{strict}} \ge 15$) | Shortfall Speakers ($C_{\text{strict}} < 15$) | Feasibility Status |
| :--- | :---: | :---: | :---: | :---: |
| **Irish English** | 78 | 78 | 0 | **PASS** |
| **England English** | 78 | 78 | 0 | **PASS** |
| **Canadian English** | 78 | 78 | 0 | **PASS** |
| **Australian English** | 78 | 78 | 0 | **PASS** |
| **South Asian English** | 78 | 78 | 0 | **PASS** |
| **US English** | 78 | 78 | 0 | **PASS** |
| **Total All 6 Strata** | **468** | **468** | **0** | **PASS** |

---

## 3. Strict Audit Verdict & Data Integrity Status

- **Strict Quality Invariant Satisfied:**
  All 468 active candidate speakers across all 6 strata possess at least 15 valid audio clips strictly satisfying both baseline predicate $B_0$ and strict quality predicate $V$ (`locale == "en"`, `up_votes >= 2`, `down_votes < 2`).
- **Cryptographic & Geometry Verification:**
  Full 7,020 clips (1,170 per stratum) selected deterministically via `SHA256(seed:client_id:clip_path)`. Zero cross-cohort exposure with Replication Cohort 1 and Sentinel Panel. Zero duplicate stems or audio paths.
- **Readiness Protocol Posture:**
  Curation audit is **PASS**. The candidate manifest is fully qualified under Option A. In accordance with ADR-005 protocol safeguards, confirmatory evaluation CSV and clip lock generation remains under controlled supervisory gate until authorized.

