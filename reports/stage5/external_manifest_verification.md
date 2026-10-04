# External Evaluation Manifest Verification
## DSG-CTTA Stage 5 Phase 3N

**Date:** 2026-10-01

## Frozen Hashes

| Artifact | SHA-256 |
|---|---|
| stage5_external_eval.csv | `5818255605c46db3832033bdd6c818d7606251a1c2d96d36a6383e9a30443351` |
| stage5_external_eval_manifest.json | `9c5b22fa2d37938d67f1a2f8e437817d1f38687e9109b23b9763586ab2451df3` |

## Selection Parameters

| Parameter | Value |
|---|---|
| Selection seed | 20261001 |
| Rule version | v1.0-cv27-amended |
| Dataset release | cv-corpus-27.0-2026-09-11 |
| Groups | 6 |
| Target speakers/group | 10 |
| Target clips/speaker | 15 |
| Actual speakers | 60 |
| Actual clips | 900 |
| Targets met | True |

## Immutability

The lock file `datasets/splits/stage5_external_eval.lock.json` contains
cryptographic hashes of both the CSV and manifest. Any modification to
the evaluation set will produce a hash mismatch detectable by the
blocking test `test_stage5_external_eval.py::test_eval_manifest_immutable`.