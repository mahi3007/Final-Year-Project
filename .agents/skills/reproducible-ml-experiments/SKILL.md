---
name: reproducible-ml-experiments
description: Make ASR/ML runs traceable and repeatable through pinned software/model revisions, deterministic RNG, hardware records, checkpoints, logs and hash catalogues; use before and after any authorized experiment.
---

# Reproducible ML Experiment Engineering

## Mission
Create an evidence chain from protocol and code identity to the exact input data, environment, execution and outputs. A seed alone does not establish reproducibility.

## Pre-run workflow
1. Verify written authorization and protocol status. Classify the run as unit test, synthetic test, development, calibration or confirmatory.
2. Record Git commit, branch, dirty status, release/archive digest, script/notebook digest, configuration digest and all relevant source-module digests.
3. Pin Python, OS, PyTorch, CUDA, cuDNN, Transformers, tokenizer/processor, NumPy, SciPy, Pandas, Numba and other material package versions. Capture GPU model, driver, VRAM and device count.
4. Pin model and processor revisions by immutable commit/revision or checksummed local snapshot. A moving model name/tag is not sufficient.
5. Specify all RNGs: Python, NumPy Generator/legacy RNG, PyTorch CPU and CUDA, dataloader workers, bootstrap RNG and any third-party kernels. Document deterministic-algorithm flags and known nondeterministic operations.
6. Hash all inputs and verify expected counts, schema, manifest, audio inventory and split disjointness before loading model weights.
7. Define output directories and log policies. Never overwrite frozen outputs. Keep raw logs, structured JSON, human-readable reports and artifact catalogues distinct.

## During execution
- Record exact command, start/end timestamps with timezone, host/kernel ID, hardware, dependency versions, exit code, warnings and progress checkpoints.
- Record inference and adaptation configuration, stream order, batch/window size, optimizer, learning rate, parameter mask, decoding settings and rollback decisions.
- Make resume behavior explicit. Store model, optimizer, scheduler, RNG, data cursor and output-record count. Verify resume against an uninterrupted miniature fixture.
- Do not suppress errors or continue after input/hash mismatch. Use atomic writes where possible.

## Post-run workflow
1. Recompute output hashes and sizes independently.
2. Verify expected row counts, unique speakers/recordings, no missing/duplicate output records and finite values.
3. Re-run deterministic offline analysis on the same canonical input when authorized; hash the canonical input serialization and full resampling distribution where applicable.
4. Compare logs, JSON, Markdown and catalogue values. Preserve preliminary runs and label their status accurately.
5. Produce a manifest linking protocol, code, data, environment, outputs, run command and limitations.
6. Have an independent reproduction procedure that does not depend on undocumented local state.

## Stage 6M cautions
- Stage 6M Event D required canonical speaker ordering as well as fixed RNG settings. Its final evidence report records canonical speaker-input and bootstrap-distribution digests; check the actual final catalogue.
- The original preliminary Numba scoring log and authoritative deterministic NumPy scoring log have different roles and must remain distinct.
- Kaggle execution claims must be tied to the exact notebook version, release archive, kernel version, mounted dataset identities and downloaded output hashes.

## Stop conditions
Do not run if authorization, code identity, data identity, environment or output destination is ambiguous. Do not upload private/sealed assets to cloud runtimes. Report operator-attested claims as such unless independently verified.
