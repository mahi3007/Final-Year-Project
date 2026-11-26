---
name: asr-ctta-engineering
description: Design, implement, and debug PyTorch speech-recognition and continual test-time adaptation systems; use for Wav2Vec2, CTC decoding, SUTA, gating, optimizer state, model rollback, and adaptation baselines.
---

# ASR and Continual Test-Time Adaptation Engineering

## Mission
Build technically correct and testable ASR/CTTA systems. Maintain a strict distinction between a proposed architecture, a reusable library class, the active runtime path and a frozen historical experiment.

## Workflow
1. Identify the exact model family, checkpoint revision, processor/tokenizer revision, sampling rate, decoding method and inference settings. Pin them in experiment metadata.
2. Trace the current adaptation implementation and its callers before replacing or reusing it. Do not assume a class named “DSG” represents the method used in a prior run.
3. For CTC models, validate logits, attention/audio masks, output lengths, blank token, greedy or beam decoding and text normalization. Test on short, long, padded and silent/truncated fixtures.
4. For entropy-minimisation adaptation, document exactly which probabilities, frames and samples contribute to the loss. Mask padding and invalid frames. Check for blank dominance, collapsed outputs, non-finite loss and gradient explosion.
5. For Minimum Class Confusion or other auxiliary losses, verify tensor dimensions, normalization, numerical stabilizers and the mathematical objective. Add gradient-level unit tests.
6. Freeze and unfreeze parameters explicitly. For LayerNorm-only adaptation, enumerate the exact trainable parameter names and assert that all other parameter gradients are absent and weights unchanged.
7. Make candidate updates transactional: clone/functionalize candidate state, keep live model untouched during optimization, validate candidate tensors and optimizer state, then commit only on accepted decision. On rejection/error, rollback both model and optimizer state exactly.
8. Test checkpoint-resume equivalence, optimizer-state restoration, RNG state, batch/window order and duplicate/missing record protection.
9. Compare against credible baselines under the same data, stream order, update budget and compute constraints. Include static model, ungated adaptation and relevant literature baselines such as SUTA/DSUTA/DMSUTA only where methodologically compatible.
10. Measure latency, memory, update frequency, rejection rate, rollback rate and parameter drift, not only WER.

## Stage 6M constraints
- The frozen benchmark used `facebook/wav2vec2-base-960h`, three arms (static, ungated SUTA, DSG-gated SUTA), K=4 windows and a 16,500-clip evaluation stream; verify the release before asserting details.
- The generic `src/dsg_ctta/online/sentinel.py`, `src/dsg_ctta/controller/streaming_gate_v14.py`, `src/dsg_ctta/controller/streaming_gate.py` and other modules may be historical or unused in the frozen Gate 5 run. Trace imports/calls from the release entry point.
- Do not modify frozen Stage 6M source or rerun confirmatory inference while investigating it.

## Testing requirements
Add tests for parameter masks, model immutability on rejection, exact rollback, optimizer-state parity, deterministic resume, padded-frame masking, empty/NaN batches, candidate update exceptions and acoustic collapse. Use small synthetic tensors for routine tests; no external model download or GPU is needed unless separately authorized.

## Prohibited practices
Do not load evaluation references in online adaptation. Do not leak labels through logs or metadata. Do not increase adaptation steps or tune hyperparameters on confirmatory results. Do not claim a method is safer because it was named or configured as a safety gate; demonstrate the executed decision path.
