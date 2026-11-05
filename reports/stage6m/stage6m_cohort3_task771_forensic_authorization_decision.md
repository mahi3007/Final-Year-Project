# Stage 6M v1.5 — Task 7.7.1 Project-Lead Authorization Decision: Diagnostic Quarantine Retrieval

> **DOCUMENT ID:** `STAGE6M_COHORT3_TASK771_FORENSIC_AUTHORIZATION_DECISION`  
> **TASK ID:** `TASK_7_7_1`  
> **TASK TITLE:** Project-Lead Academic Authorization for Diagnostic Quarantine Retrieval & MP3 Forensic Triage  
> **PROTOCOL VERSION:** v1.5 Five-Stratum Confirmatory Protocol (`v1.5-five-stratum-parity`)  
> **GOVERNING STANDARD:** Protocol Section 14.7 (*Project-Lead Academic Authorization*)  
> **DECISION STATUS:** **AUTHORIZED_FOR_DIAGNOSTIC_QUARANTINE_ONLY**  
> **AUTHORIZING ROLE:** Project Lead  
> **TIMESTAMP (UTC):** `2026-11-05T06:55:00Z`  

---

## 1. Executive Summary & Review Findings

During the full-cohort streaming execution of Task 7.7, the entire **94.95 GB** Common Voice 27.0 archive (`94,956,262,763` bytes) was traversed through gzip EOF. Out of 18,975 target recordings:
- **18,845 physical recordings** across 1,252 speakers were successfully acquired, decoded, and bitwise SHA-256 verified against the baseline ledger with **zero hash mismatches**.
- **130 recordings** across 13 speakers failed the MPEG Audio Layer III frame-boundary completeness check (`declared_frames - total_decoded_frames > 1152`), with frame shortfalls ranging from 1,296 to 2,979 frames (~27 to ~62 ms at 48 kHz).
- Because the production materializer unlinked failed files, the raw bytes of those 130 rejected clips were not retained in the physical cohort directory.
- Post-acquisition independent validation correctly failed closed (`FAIL_BASELINE_LEDGER_INVALID`), confirming that the physical cohort is short by 130 recordings.

To establish whether these 130 recordings are valid gapless MP3s rejected by an overly strict frame-shortfall threshold or genuine bitstream truncations in the Common Voice archive, this decision formally authorizes **Task 7.7.1: MP3 Forensic Triage**.

---

## 2. Authorized Scope & Governance Boundaries

In strict compliance with Protocol Section 14.7, this authorization is narrowly scoped and legally partitioned from the main Cohort 3 dataset:

| Field | Authorized Specification | Enforcement / Restriction |
| :--- | :--- | :--- |
| **Purpose** | Diagnostic MP3 forensic investigation only | Cannot be used for model adaptation or inference |
| **Source Dataset** | Mozilla Data Collective (`cmu5jplf300nwmh07iqvk9leo`) | Exact same Mozilla Common Voice 27.0 release |
| **Parent Manifest SHA-256** | `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` | Modification strictly prohibited |
| **Quarantine Targets List** | [`datasets/splits/stage6m_cohort3_task771_quarantine_targets.json`](file:///C:/Users/venka/Downloads/final%20year%20project%20main/datasets/splits/stage6m_cohort3_task771_quarantine_targets.json) | SHA-256: `a530fb8b60fc302e536ce14efb620cda936ad91783f7d1f482a430dd154696ae` |
| **Target Scale** | Exactly **130 rejected recordings** across **13 speakers** | 0 substitutions permitted |
| **Stratum Breakdown** | Canadian: 73, US: 33, Australian: 16, England: 8 | Evaluation panel role only |
| **Quarantine Destination** | `datasets/external/common_voice_27/cohort3_rejected_quarantine` | Separate physical diagnostic folder |
| **Cohort Promotion** | **STRICTLY PROHIBITED** | Must not be placed into `cohort3_audio` |
| **Extraction Policy** | Preserve raw original bytes without decoding gate | Failed files must NOT be unlinked/deleted |
| **Preservation Rule** | Original 18,845 files & acquisition ledger preserved | No alteration of partial-acquisition evidence |

---

## 3. Required Forensic Protocols (Task 7.7.1B)

Every one of the 130 quarantined recordings must undergo multi-method technical analysis:
1. **MPEG Frame-Header Bitstream Scan**: Sequential frame-by-frame traversal validating sync words, Layer III headers, sampling rates, bitrates, padding bits, and frame lengths to EOF to detect truncation or garbage bytes.
2. **Xing / Info / LAME Metadata Inspection**: Parsing ID3v2 tags, Xing/Info headers, and LAME tags to record encoder delay and encoder padding.
3. **Decoded Sample-Frame Shortfall Calculation**: Measuring decoded PCM sample frames against container declarations, accounting for MPEG Layer III frame sizes (1,152 samples for MPEG-1; 576 samples for MPEG-2/2.5).
4. **Independent Decoders**: Cross-evaluating across SoundFile (libmpg123), native Python frame parser, and Mutagen.
5. **Deterministic Dispositions**: Assigning each recording to `VALID_GAPLESS_PADDING`, `TRUNCATED_BITSTREAM`, or `INCONCLUSIVE`.

---

## 4. Execution Gating & Downstream Boundaries

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║               TASK 7.7.1 EXECUTION GATING & GOVERNANCE BOUNDARIES                    ║
║                                                                                      ║
║  1. Task 7.7.1 Quarantine Retrieval: AUTHORIZED_BY_PROJECT_LEAD                      ║
║  2. Task 7.7.1 Forensic Triage: AUTHORIZED_BY_PROJECT_LEAD                           ║
║  3. Cohort Promotion of Quarantined Audio: STRICTLY_PROHIBITED                       ║
║  4. Task 7.8 Final Manifest Lock: STRICTLY_BLOCKED (Pending 100% Valid Cohort)       ║
║  5. GPU CTTA Adaptation: STRICTLY_BLOCKED                                            ║
║  6. Confirmatory Inference: STRICTLY_BLOCKED                                         ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
