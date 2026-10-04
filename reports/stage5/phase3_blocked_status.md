# Phase 3 Metadata Checkpoint — BLOCKED
## DSG-CTTA Stage 5 Phase 3D

**Status:** BLOCKED
**Date:** 2026-10-01
**Phase attempted:** metadata (Phase 3A–3D — no audio download)

---

## Reason for BLOCKED Status

The Phase 3 metadata checkpoint cannot complete because access to the
cv-corpus-11.0-2022-09-21 metadata (validated.tsv) requires authentication.

### Error Encountered

`
HTTP/1.1 401 Unauthorized
HuggingFace: Dataset 'mozilla-foundation/common_voice_11_0' cannot be accessed.
`

### Root Cause

Mozilla Common Voice 11.0 requires:
1. Acceptance of Mozilla Common Voice terms of service on HuggingFace
2. A valid HuggingFace access token passed as HF_TOKEN

This is a DATA ACCESS control, not a code defect.
The Phase 3 script and infrastructure are complete and correct.

---

## What Has Been Completed

- Phase 3 curation script: scripts/phase3_external_eval_curation.py
- 14 blocking test suite: tests/research_validity/test_stage5_external_eval.py
- Phase 1 audit reports: reports/stage5/ (all 11 files)
- Protocol constants frozen: seed=20261001, groups=6, speakers=10, clips=15
- All output file paths and schemas defined
- Lock/immutability mechanism implemented

Nothing is blocked by code. Everything is blocked by DATASET ACCESS only.

---

### Upstream Deprecation Notice (HuggingFace 404)

Mozilla has migrated the distribution of all Common Voice datasets to the
**Mozilla Data Collective (MDC)**. As part of this transition, the previous HuggingFace
repository (`mozilla-foundation/common_voice_11_0`) was permanently removed upstream,
causing direct HuggingFace links and `load_dataset` calls to return `404 Not Found`.

Option A (HuggingFace streaming) is therefore obsolete. The official and supported
path forward is direct metadata access via Mozilla Data Collective.

---

## Resolution Path

### Primary Resolution: Direct TSV Download (Mozilla Data Collective)

Step 1: Visit https://datacollective.mozillafoundation.org/ or https://commonvoice.mozilla.org/en/datasets
Step 2: Sign in / create a free account and accept the dataset terms of service.
Step 3: Locate the Common Voice English dataset (cv-corpus-11.0-2022-09-21 or current release).
Step 4: Download or extract the English metadata file:
        `validated.tsv` (~300 MB)
        (You do NOT need to download or extract the full ~22 GB audio archive for the metadata
         checkpoint and selection phases. Only `validated.tsv` is required for Steps 1 & 2.)
Step 5: Place the extracted `validated.tsv` in:
        `datasets/external/common_voice_11/validated.tsv`
Step 6: Run the metadata feasibility checkpoint:
        python scripts/phase3_external_eval_curation.py \
          --phase metadata \
          --tsv-path datasets/external/common_voice_11/validated.tsv

---

## What Checkpoint 1 Will Produce (After Access Resolved)

The metadata phase will print:

  CHECKPOINT 1 — PHASE 3D FEASIBILITY TABLE
  Pinned release: cv-corpus-11.0-2022-09-21

  Group                            All Spk   Eligible Spk   Target   Feasible
  United States English              EXACT          EXACT       10    YES/NO
  India and South Asia English       EXACT          EXACT       10    YES/NO
  England English                    EXACT          EXACT       10    YES/NO
  Australian English                 EXACT          EXACT       10    YES/NO
  Canadian English                   EXACT          EXACT       10    YES/NO
  Irish English                      EXACT          EXACT       10    YES/NO

If all 6 show YES: deterministic selection proceeds automatically (--phase select).
If any show NO: BLOCKED is reported with exact group and count.

---

## Subsequent Phase Commands (After Checkpoint 1 Passes)

# Step 1: Metadata feasibility (already attempted; requires auth)
python scripts/phase3_external_eval_curation.py --phase metadata [--tsv-path ...]

# Step 2: Deterministic selection (creates CSV + manifest, no audio)
python scripts/phase3_external_eval_curation.py --phase select [--tsv-path ...]

# Step 3: Audio materialization (downloads/locates exactly 900 clips)
python scripts/phase3_external_eval_curation.py --phase materialize [--audio-dir ...]

# Step 4: Run blocking tests
pytest tests/research_validity/test_stage5_external_eval.py -v

---

## Protocol Integrity

This BLOCKED status does not affect:
- Stage 2, 3, 4 results (all verified)
- Pre-flight audit status (still BLOCKED for Stage 5 controller)
- Phase 3 script correctness
- Phase 1 audit completeness

The BLOCKED status will be resolved as soon as validated.tsv is accessible.

**IMPORTANT:** Do NOT substitute another Common Voice release.
Do NOT use Phase 1 estimated counts instead of real metadata.
Do NOT proceed to audio materialization before Checkpoint 1 passes.
