# External Evaluation Quality Report
## DSG-CTTA Stage 5 Phase 3
**Date:** 2026-10-01
**Dataset:** cv-corpus-27.0-2026-09-11

## Transcript Quality

| Metric | Count |
|---|---|
| Total clips audited | 900 |
| Empty transcripts | 0 |
| Too-short transcripts (<2 words) | 0 |
| Duplicate sentence+path pairs | 0 |
| Suspicious characters | 0 |
| **Transcript audit result** | PASS |

## Cross-Source Independence

| Check | Result |
|---|---|
| CV speakers | 60 |
| L2-ARCTIC speakers in splits | 28 |
| Shared speaker IDs | 0 |
| Shared audio paths | 0 |
| Independence audit | PASS |

## Independence Claim

> Operational source-level independence. Common Voice contributors registered independently on the Mozilla Common Voice platform. L2-ARCTIC speakers were recruited and recorded in a separate university research protocol. No shared registration, identity, or audio exists. Cross-dataset speaker identity cannot be formally verified or refuted from metadata alone.

## Namespace Note

> Common Voice uses SHA-256 hashed client_id (anonymised UUID). L2-ARCTIC uses researcher-assigned speaker codes (e.g. HJK, TNI). These namespaces are disjoint by construction.

## Prohibited Operations

The following operations are prohibited during and after Phase 3:
- ASR inference
- WER computation for selection
- DSG implementation
- CTTA execution
- Modification of stage5_external_eval.csv after freeze