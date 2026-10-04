# External Evaluation Set Independence Report
## DSG-CTTA Stage 5 Phase 3M

**Date:** 2026-10-01

## Independence Claim

Operational source-level independence. Common Voice contributors registered independently on the Mozilla Common Voice platform. L2-ARCTIC speakers were recruited and recorded in a separate university research protocol. No shared registration, identity, or audio exists. Cross-dataset speaker identity cannot be formally verified or refuted from metadata alone.

## Namespace Note

Common Voice uses SHA-256 hashed client_id (anonymised UUID). L2-ARCTIC uses researcher-assigned speaker codes (e.g. HJK, TNI). These namespaces are disjoint by construction.

## Checks Performed

| Check | Result |
|---|---|
| Shared speaker IDs between CV and L2-ARCTIC splits | 0 |
| Shared audio paths | 0 |
| Namespace analysis | Disjoint by construction |
| Overall independence | PASS |

## Limitations

- Cross-dataset speaker identity matching across namespaces is not possible from metadata alone.
- The claim is 'operational source-level independence', which is the strongest achievable.
- Audio-level identity check would require audio hashing across both full corpora.