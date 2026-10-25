# Stage 6M Confirmatory Cohort 2: Curation & Strict Integrity Audit Report

> **Audit Verdict:** `HOLD_STRICT_QUALITY_SHORTFALL`  
> **Timestamp:** 2026-10-25T12:15:12.259109+00:00  
> **Protocol:** `v1.3.4-stage6m-self-authorization-amendment` (ADR-005)  
> **Predicate Level:** `STRICT QUALITY PREDICATE V (locale=='en', up_votes>=2, down_votes<2)`  
> **Deterministic Seed:** `20261020`  
> **Execution Mode:** `AUDIT-ONLY (FAIL-CLOSED)`

---

## 1. Summary Matrix

| Audit Check | Scope | Verdict | Details |
| :--- | :--- | :---: | :--- |
| **1. Prefix Resolution** | 468 Manifest Active Prefixes | `PASS` | Resolved 468/468 prefixes bijectively (1:1). |
| **2. Strict Clip Eligibility** | Strict Quality Predicate V (B0 + V) | `FAIL` | 464/468 speakers meet strict quota (4 shortfall). |
| **3. Speaker Disjointness** | Cross-Cohort Isolation | `PASS` | 0 overlap with Cohort 1 (60 spks) and Sentinel Panel (30 spks). Zero leakage. |
| **4. Stratum Preservation** | 6 Pre-specified Strata | `PASS` | Exactly 78 speakers per stratum across all 6 strata. |
| **5. Stream Geometry** | 15 Clips/Speaker Stream | `FAIL` | Selected 7014/7020 strict clips across 6 strata. |
| **6. Schema & Naming** | Runner Filename Compatibility | `PASS` | Filename stem convention verified (`cohort2_audio/{recording_id}.mp3`). |

---

## 2. Six-Strata Strict Eligibility Breakdown

| Stratum Name | Total Active Speakers | Strict-Eligible Speakers ($C_{\text{strict}} \ge 15$) | Shortfall Speakers ($C_{\text{strict}} < 15$) | Feasibility Status |
| :--- | :---: | :---: | :---: | :---: |
| **Australian English** | 78 | 78 | 0 | **PASS** |
| **Canadian English** | 78 | 78 | 0 | **PASS** |
| **England English** | 78 | 78 | 0 | **PASS** |
| **Irish English** | 78 | 78 | 0 | **PASS** |
| **South Asian English** | 78 | 74 | 4 | **HOLD (4 Shortfall)** |
| **US English** | 78 | 78 | 0 | **PASS** |
| **Total All 6 Strata** | **468** | **464** | **4** | **HOLD_STRICT_QUALITY_SHORTFALL** |

### Strict Quality Shortfall Speakers (|Q| Violations in Manifest):

| Speaker Prefix | Stratum | Raw Clips | Baseline B0 | Strict V | Shortfall | Rejected by Votes (`down>=2` or `up<2`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `07004fed5c5e5b0eec54cada…` | South Asian English | 15 | 15 | **14** | -1 | 1 |
| `6cd7653404104d87053bcef6…` | South Asian English | 15 | 15 | **13** | -2 | 2 |
| `25949e8d7229d181418b78ad…` | South Asian English | 15 | 15 | **13** | -2 | 2 |
| `a7a33ab5ac9181d03e49a22a…` | South Asian English | 17 | 17 | **14** | -1 | 3 |

---

## 3. Methodological Audit Finding & Supervisory Decision Gate

- **Root Cause Analysis:**
  The locked candidate manifest ([`stage6m_locked_candidate_manifest.json`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_locked_candidate_manifest.json)) was constructed by [`scripts/generate_stage6m_locked_manifest.py`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/scripts/generate_stage6m_locked_manifest.py) from [`reports/stage5/external_speaker_inventory.csv`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage5/external_speaker_inventory.csv).
  `external_speaker_inventory.csv` indexed baseline qualification ($C_{\text{inventory}} \ge 15$, Predicate $B_0$) without applying strict quality predicate $V$.
  As documented in [`reports/stage6m/stage6m_data_feasibility_audit.md`](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage6m/stage6m_data_feasibility_audit.md) Section 2.2, exactly 18 South Asian speakers in the inventory belong to the quality exclusion set $Q$ ($C_{\text{strict}} < 15$ due to down-votes $\ge 2$). Four of these 18 speakers were allocated into the active manifest.
- **Fail-Closed Guarantee:**
  Because 4 active speakers have only 13 or 14 strict-eligible clips, confirmatory evaluation CSV generation is **HALTED**. `MANIFEST_LOCKED_AUDIO_DOWNLOAD_HOLD` remains strictly in effect.
