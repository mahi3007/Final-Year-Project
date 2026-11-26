---
name: research-validity-tdd
description: Build and audit scientific Python software with test-driven development and adversarial research-validity tests; use when changing data pipelines, adaptation logic, inference, privacy boundaries, or experiment runners.
---

# Research Validity and Test-Driven Development

## Mission
Tests must protect the scientific meaning of the system, not merely check that code runs. Use small deterministic fixtures to make invalid states difficult to represent.

## Development loop
1. Read the governing protocol, target code and existing tests. Record expected behavior before editing.
2. Create the smallest test that demonstrates the required behavior or current defect (RED).
3. Implement the smallest safe change (GREEN).
4. Refactor without changing behavior; rerun focused tests and the full relevant suite.
5. Inspect coverage of failure paths. A passing happy-path test is insufficient.
6. Record exact commands, environment, test counts, skips, xfails and failures. Never claim tests passed if they were not run.

## Required test families
- **Unit:** mathematical helpers, normalization, schema validation, WER/S-D-I alignment, RNG wrappers and state transitions.
- **Integration:** entry-point-to-decision execution; verify that the configured gate is genuinely called and its decision is consumed.
- **Research validity:** speaker leakage, repeated speaker/clip detection, sentinel contamination, transcript/label isolation, group mapping invariants and cohort counts.
- **Statistical:** ratio calculations, cluster-resampling unit, paired resampling, group preservation, multiplicity family size, confidence-bound tails and seed/order determinism.
- **Model state:** frozen parameters unchanged, only declared parameters trainable, optimizer-state recovery, exact rollback and checkpoint-resume equivalence.
- **Adversarial/failure injection:** empty input, missing stratum, duplicate IDs, malformed manifest, hash mismatch, NaN/Inf, zero words, decoder failure, interrupted write, corrupt checkpoint, absent GPU, unavailable dependency and candidate update exception.
- **Security/privacy:** no transcript values in logs, no secrets in tracked files, no label-bearing object reaching online adaptation, no unsafe path traversal and no unexpected network dependency.

## Property-based and metamorphic checks
Where appropriate, test invariants such as:
- Adding a perfect-match utterance should change pooled WER according to its reference-word weight, not an arbitrary clip weight.
- Reordering rows must not change order-invariant point estimates; if deterministic bootstrap output is order-sensitive, canonical ordering must be specified and hashed.
- Duplicating a speaker cluster must trigger duplicate/weighting policy rather than silently treating it as a new independent speaker.
- Any missing required stratum or invalid count must fail closed.
- Rejected candidate update leaves model and optimizer state byte/value-identical to pre-update state.
- A manifest hash mismatch prevents execution before model loading.

## Git and artifact discipline
- Never remove or weaken a failing test just to get a green suite.
- Do not change a frozen test to accommodate an unauthorized implementation change. Propose a versioned test and protocol change instead.
- Preserve the user's working-tree edits. Inspect `git status` and diffs before and after.
- Keep tests isolated from real sealed data and external services.

## Outputs
Report test command, environment, count passed/failed/skipped, coverage of important branches, remaining untested cases and whether any test is synthetic. Label synthetic validation as synthetic; do not imply it is empirical confirmation.
