---
name: research-governance
description: Protect frozen research evidence, protocol versions, authorizations, private evaluation assets, and branch boundaries; use before modifying research code, datasets, reports, or running experiments.
---

# Research Governance and Evidence Preservation

## Mission
Keep research claims aligned with authorized protocols and preserve an auditable history. This skill is a mandatory preflight for all repository-changing or experiment-running work.

## Frozen Stage 6M ground truth
Treat the following as historical facts to preserve, subject to checking the authoritative reports in the repository:
- Stage 6M used five confirmatory strata: Australian, Canadian, England, South Asian and US English.
- The confirmatory cohort comprised 1,100 speakers and 16,500 clips; 100 gate-reference speakers and 65 Australian reserve speakers were separately designated.
- The approved Stage 6M v1.5 protocol used a family of M=8 hypotheses, family-wise alpha 0.05, Bonferroni-adjusted alpha 0.00625 and one-sided simultaneous 99.375% UCBs.
- Gate 6 reconciled evidence package status: `EVIDENCE_PACKAGE_RECONCILED_AND_CLOSED`.
- Historical confirmatory verdict: `INCONCLUSIVE`; A FAIL, B PASS, C PASS, D FAIL.
- Reported pooled WERs: Static 20.8000%, Ungated SUTA 60.3536%, DSG 20.9489%.

These are not permission to overwrite the source records. Check current catalogue hashes and reports before reproducing exact claims. If sources conflict, preserve all versions and raise a discrepancy.

## Non-negotiable invariants
1. **Ground before mutating.** Inspect status, branch, HEAD, diff, file history, authorizing record and artifact catalogue before any write.
2. **Say what cannot be verified.** Separate verified evidence, operator-attested statements, inference and unknowns.
3. **Fail closed.** Missing permission, mismatched hash, missing manifest, failed test or ambiguous data role means STOP, not a best-effort promotion.
4. Never change historical predictions, transcripts, sealed key, scores, confidence bounds, p-values, sample membership, thresholds or the Stage 6M verdict to obtain a favourable outcome.
5. Never copy sealed evaluation transcripts, keys, credentials, access tokens or sensitive speaker identifiers into prompts, logs, reports, Git, cloud notebooks or model context. Refer to secret assets by approved path/digest only.
6. Treat the Gate 5 release archive and Gate 6 evidence as immutable. Corrections to explanatory documentation must be additive, traceable and must not rewrite the historical record.
7. Separate future research into a new protocol version, branch, data partitions, output directories, model checkpoints and artifact catalogue.
8. No GPU experiment, new confirmatory prediction, dataset download/upload, external network access, destructive file operation or protocol amendment without explicit project-lead authorization.
9. Do not force-push, rebase published history, amend frozen commits, push to `main`, change repository visibility or purge Git history without explicit authorization.
10. Never describe a failed confirmatory criterion as passed, nor call an inconclusive benchmark a successful validation.

## Pre-change checklist
- What exact user-approved task is being performed?
- Is it read-only, documentation-only, development, calibration or confirmatory?
- Which protocol version authorizes it?
- Which files and data partitions are in scope?
- Is the working tree clean? Are there uncommitted user changes?
- Is the target branch appropriate and protected?
- Could the operation touch frozen artifacts or secrets?
- What tests and hashes will prove the work?
- What is the rollback plan?

If any answer is unresolved, do not mutate. Ask one focused question only if required; otherwise produce a blocker report.

## New-study governance
Before a new confirmatory study, require a dated protocol with estimands, hypotheses, primary outcomes, margins, multiplicity, sample-size/power scenarios, data eligibility, group labels, exclusions, split rules, adaptation procedure, stopping rules, analysis code identity, privacy plan and sign-off. Freeze it before accessing confirmatory labels or running confirmatory inference.

## Required reporting language
Use scoped terms such as “in the evaluated configuration” and “the evidence is consistent with”. Do not claim universal safety, fairness, prevention, non-inferiority, statistical significance or generalization unless the exact estimand and analysis support that wording.
