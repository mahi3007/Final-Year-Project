---
name: execution-path-forensics
description: Trace the exact code and artifact path that produced an experiment result; use when auditing benchmark runners, model updates, gates, inference calls, release hashes, or protocol conformance.
---

# Execution Path Forensics

## Mission
Establish what actually executed, not what comments, class names, configuration objects, reports, or intended architecture say should have executed. Produce reproducible, source-grounded findings.

## Mandatory workflow
1. **Establish the checkout.** Record repository root, branch, HEAD, working-tree status, submodules, Python environment, and relevant release/tag/commit identities. Do not switch branches or reset a worktree.
2. **Identify the execution artifact.** Find the exact command, entry point, notebook, workflow, script, archive, container or scheduler job used. Record its SHA-256 and byte size. For Stage 6M Gate 5, compare the executed runner with the frozen release identity recorded in the release reports; expected runner SHA-256: `728efdc613dcbfe639c531f9c673a4f956c9cfb74c181725b59cfce728fa0ed1`. Treat this as an expected value to verify, not proof by itself.
3. **Trace imports and calls.** Follow execution from entry point through imports, constructors, configuration, candidate generation, scoring, decision functions, state application/rollback, logging and checkpointing. Search for callers and prove whether each relevant function is invoked. An instantiated object is not evidence that it is used.
4. **Trace data flow.** Record data sources, transformations, ordering, filters, sampling, group composition, sentinel/test partition use, labels available at each stage, and whether records are reused. Quantify counts by speaker, clip and stratum where possible without exposing transcript contents or secret identifiers.
5. **Trace decision semantics.** Identify the exact condition that accepts, rejects, commits, rolls back or skips an update. Check whether uncertainty bounds, margins, multiplicity corrections, sequential schedules and subgroup checks actually participate in the executed decision.
6. **Compare implementation to protocol.** Build a requirement-to-code matrix with protocol citation, implementation location, runtime call evidence, test evidence and status: CONFORMANT / PARTIAL / NONCONFORMANT / UNVERIFIED.
7. **Reproduce safely.** Prefer static inspection and read-only tests. Do not launch GPU, network, data downloads, model inference or confirmatory jobs without explicit authorization. Never open or print sealed transcript values, keys, credentials or private audio.
8. **Report.** State confirmed facts, inferences and unknowns separately. Include repository-relative path, symbol, line range from the checked-out revision, relevant snippet or call chain, evidence command and limitation for each material claim.

## Stage 6M audit targets
- Frozen Gate 5 release archive, runner, notebook and checksum manifest.
- `cloud/kaggle/run_stage6m_cohort3_kaggle_benchmark.py` and the exact extracted release counterpart.
- `StreamingSentinelSafetyGateV14`, its constructor and `evaluate_candidate` call sites.
- Sentinel selection, speaker/stratum composition and repeated use across windows.
- `AtomicCandidateManager`, `compute_masked_suta_loss`, candidate optimizer state, update commit and rollback.
- Actual online decision rule versus the approved specification: overall utility, every stratum regression guard, disparity non-increase and any sequential alpha-spending rule.
- Gate 6 scorer, v1.5 inference function, deterministic bootstrap path and canonical speaker ordering.

## Required deliverables
- `gate5_execution_path_audit.md`
- `gate5_protocol_conformance.json`
- `active_dependency_graph.md`
- `research_risk_register.md`

For each finding report severity, evidence, confidence, affected conclusion, required remediation, test/verification command and whether new authorization is needed.

## Stop conditions
Stop and report BLOCKED if the exact executed release cannot be verified, evidence is missing, hashes mismatch, or a claim depends on inaccessible runtime logs. Do not repair the code during an audit. Do not turn an audit discrepancy into an unsupported claim that the experiment is invalid; determine scope and impact first.

## Quality bar
A reviewer must be able to independently follow the call chain and reproduce the finding from the cited revision. Never infer execution from a class being imported, instantiated, documented or tested in isolation.
