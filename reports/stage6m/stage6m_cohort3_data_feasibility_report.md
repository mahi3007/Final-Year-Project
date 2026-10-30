# Stage 6M Confirmatory Cohort 3 — Data Feasibility & Speaker Capacity Audit Report

- **Standard:** ADR-005
- **Protocol Version:** v1.4.0
- **Decision Rule:** Decision Rule B
- **Target Specification:** 6 Strata x 220 Speakers x 15 Clips = 19,800 Cohort 3 Clips + 120-Speaker Dedicated Gate-Reference Panel
- **Audit Timestamp (UTC):** 2026-10-30T10:35:14.326869+00:00
- **Overall Feasibility Disposition:** **FAIL-CLOSED CAPACITY BOTTLENECK (MATERIALIZATION FORBIDDEN)**

---

## 1. Executive Summary & Core Feasibility Finding

This audit evaluates the empirical capacity of **Mozilla Common Voice 27.0** (`validated.tsv`) to satisfy the statistical sample size requirements of **Decision Rule B** (1,320 independent speakers, 19,800 clips) and a separate 120-speaker Gate Reference Panel, while strictly enforcing **zero speaker leakage** against all prior developmental and confirmatory partitions.

### Key Finding:
1. **Five Strata Have Ample Capacity:** Australian English, Canadian English, England English, South Asian English, and US English all have surplus strictly qualified, unexposed speakers ($\ge 305$ available vs. $240$ required).
2. **Irish English Represents an Absolute Empirical Bottleneck:**
   - In the **entirety** of Common Voice 27 worldwide, there are only **220 raw speakers** with declared Irish English accent.
   - Only **92 unique Irish speakers** meet strict quality filtering ($\ge 15$ qualified clips with `locale == 'en'`, `up_votes >= 2`, `down_votes < 2`, `words >= 2`).
   - All **92** strictly eligible Irish speakers have already been exposed across historical partitions (10 in Cohort 1, 5 in Stage 5 Sentinel, 78 in Cohort 2).
   - Consequently, the number of unexposed, strictly qualified Irish English speakers available in Common Voice 27 is **EXACTLY ZERO (0)**.
   - The stratum shortfall for Irish English is **240 speakers** (or **148 speakers** even if all historical data were disregarded).

---

## 2. Empirical Speaker Capacity Ledger

| Stratum | Raw Declared | Strict ($\ge 15$ clips) | Prior Exposed | Unexposed Available | Req C3 | Req Gate | Total Req | Shortfall | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Australian English** | 804 | 398 | 93 | **305** | 220 | 20 | 240 | 0 | **PASS** |
| **Canadian English** | 1,031 | 511 | 93 | **418** | 220 | 20 | 240 | 0 | **PASS** |
| **England English** | 2,733 | 1,213 | 93 | **1,120** | 220 | 20 | 240 | 0 | **PASS** |
| **Irish English** | 220 | 92 | 92 | **0** | 220 | 20 | 240 | 240 | **CRITICAL SHORTFALL** |
| **South Asian English** | 2,459 | 746 | 93 | **653** | 220 | 20 | 240 | 0 | **PASS** |
| **US English** | 9,085 | 3,884 | 93 | **3,791** | 220 | 20 | 240 | 0 | **PASS** |

---

## 3. Prior Exposure & Partition Tracking

- **Cohort 1 (Stage 5 External Eval):** 60 speakers (10 per stratum)
- **Stage 5 Sentinel Panel:** 30 speakers (5 per stratum)
- **Cohort 2 Audio:** 468 speakers (78 per stratum)
- **Total Unique Prior Exposed Speakers:** 558 speakers

Under the governing scientific protocol, confirmatory evaluation requires genuine partition disjointness:
- No Cohort 3 speaker may appear in Cohort 1, Cohort 2, or Stage 5 Sentinel.
- No Dedicated Gate-Reference speaker may appear in Cohort 3 or any historical partition.

---

## 4. Methodological Invariants & Enforcement

1. **No Silent Downsampling:**
   The protocol forbids silently reducing Irish English from 220 speakers to 92, 78, or 0. Such an ungrounded modification would violate the prespecified balance required for the disparity estimand $\Delta_D = \max WER - \min WER$.
2. **No Corpus Confounding:**
   Supplementing only Irish English from an external corpus (e.g. EdAcc or VoxCeleb) while sourcing the other five strata from Common Voice 27 would introduce a fatal corpus-versus-accent confound, making it impossible to disentangle adaptation efficacy from acoustic recording conditions.
3. **Fail-Closed Governance Invariant:**
   Because Common Voice 27 cannot physically materialize 220 independent Irish English speakers under Decision Rule B, **Cohort 3 materialization cannot proceed to completion from Common Voice 27 alone**.
   The project remains strictly locked at **`DRAFT_HOLD`**, and no confirmatory inference may be executed.

---

## 5. Next Steps for Academic Supervisor Alignment

To resolve this empirical data constraint without invalidating confirmatory rigor, the project lead and research supervisor must formally evaluate one of two scientifically sound options:

1. **Option 1: Harmonized Multi-Corpus Sampling Protocol**
   Formally amend the data sourcing protocol to draw balanced, acoustically normalized subsets across **all six strata** from a multi-corpus registry, preventing corpus confounding.
2. **Option 2: Statistically Re-Powered Balanced Sample Size Protocol**
   Re-calibrate Decision Rule B sample sizes to the empirical ceiling of the rarest stratum (e.g. $N_g = 78$ or an alternative balanced specification) with updated power curves.
