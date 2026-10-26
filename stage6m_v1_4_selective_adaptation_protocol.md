# Stage 6M v1.4.0 — Selective Adaptation Protocol and Implementation Plan

**Status:** Draft proposal; not yet frozen or authorized for confirmatory execution  
**Proposed protocol ID:** `v1.4.0-stage6m-selective-adaptation-draft`  
**Repository baseline inspected:** `300a676598eb44f30afb8eeb6bb122842aa2b68a`  
**Historical Cohort 2 execution source recorded in report:** `8324f38e09f9fac5362b36a010cc76cd35bfef20`  
**Historical execution artifact commit:** `c3305d6d6f6547118b216cb99c599af9402679c3`  
**Purpose:** Move Stage 6M from demonstrated harm interception toward scientifically defensible, positive selective adaptation.

> This document is a proposed protocol. It must not be represented as already implemented, run, statistically validated, or approved. All thresholds, dataset feasibility, power, and gate calibration requirements below must be addressed before the confirmatory protocol is frozen.

---

## 1. Executive decision

Stage 6M v1.4.0 should answer one narrow question:

> On a fresh, speaker-disjoint confirmatory cohort, does a frozen DSG controller that selectively promotes adaptation candidates improve overall ASR accuracy over both a static baseline and a correctly implemented ungated SUTA arm, while keeping every accent within a prespecified regression margin and preventing an increase in cross-accent disparity?

The study is successful only if **all** of the following hold:

1. DSG is statistically superior in overall WER to the static baseline.
2. DSG is statistically superior in overall WER to corrected ungated SUTA.
3. Every accent passes the prespecified non-inferiority / unacceptable-regression rule relative to static.
4. The upper confidence bound for the change in max-minus-min accent WER disparity is at or below zero.
5. The run passes provenance, numerical-integrity, paired-evaluation, and frozen-protocol checks.

Candidate acceptance rate is descriptive only. There is no minimum acceptance rate, no requirement to force acceptance, and no threshold adjustment to achieve a preferred result.

If DSG accepts no updates, it will generally reproduce the static baseline. That may demonstrate safe rejection, but it will not establish the stated primary accuracy objective. Report that outcome honestly.

## 2. What the historical Cohort 2 run means

The reconciled Cohort 2 report records approximately:

| Arm | Reported overall WER | Interpretation |
|---|---:|---|
| Static baseline | 22.28% | Reference performance for the historical cohort |
| Ungated SUTA | 99.95% | Catastrophic failure; most hypotheses were empty |
| DSG | 22.28% | No candidate update was accepted; baseline was preserved |

The report attributes the SUTA collapse primarily to non-finite gradient/parameter propagation associated with the MCC loss stabilizer, leading to degenerate CTC outputs. The reconciliation commit documents a correction to the stabilizer placement and adds gradient clipping and a non-finite scalar-loss guard. The current function still needs explicit finite-gradient and post-step parameter checks, and gradient clipping by itself is not a complete non-finite guard.

The previous result supports this qualified statement:

> In the reported Cohort 2 run, DSG rejected the observed candidate updates and preserved the live model while the ungated arm collapsed. This is evidence of protective harm interception in that run, not evidence that DSG improved WER through beneficial selective adaptation.

Do not use Cohort 2 results to select v1.4 loss functions, learning rates, window sizes, gate thresholds, confidence cut-offs, or acceptance rules and then call a second evaluation on the same material a fresh confirmatory study. Cohort 2 is outcome-exposed and should be designated **historical / retrospective development evidence** for v1.4.

## 3. Design principles

1. **No history rewriting.** Preserve all commits, artifacts, CSVs, execution logs, and reports as they are. Corrections are new commits and append-only reconciliation notes.
2. **Separate development from confirmation.** Tune on development speakers only. Use a fresh confirmatory stream and a locked evaluation manifest that has not been used to choose the algorithm or gate.
3. **Make the arms comparable.** The ungated and DSG arms must use the same candidate-generation code, model checkpoint, update schedule, optimizer configuration, loss, preprocessing and decoding. The principal difference must be candidate promotion versus unconditional promotion of valid updates.
4. **Separate numerical interlocks from DSG's statistical utility gate.** Numerical safety checks prevent invalid tensors or parameters from reaching live inference. The DSG gate then judges candidate utility and fairness. Both are mandatory in the DSG arm.
5. **Freeze before confirmatory execution.** The commit, configuration, manifest, metric definitions, analysis code, stopping rules, and decision thresholds must be locked before outcomes from the fresh confirmatory cohort are examined.
6. **No minimum acceptance rate.** Acceptance rate is a secondary diagnostic, not a target for tuning.
7. **No post-result success redefinition.** A failed or inconclusive objective is reported as such; it cannot be replaced post hoc by an easier metric.

## 4. Population, cohorts, and leakage controls

### 4.1 Required partitions

Create and validate three logically separate data partitions:

- **Development data:** Used for optimizer stabilization, candidate-generator selection, window-size/loss/learning-rate comparisons, diagnostics, gate design and calibration. This data may be inspected repeatedly.
- **Gate reference panel for confirmation:** A fixed, labelled panel with no speakers in the confirmatory stream. Its references may be accessed by the gate at runtime. It must not be used to train the candidate model. The panel design and statistical rule are frozen before confirmation.
- **Fresh confirmatory stream (Cohort 3):** Speaker-disjoint from development data, Cohorts 1 and 2, Stage 5 evaluation data, and all sentinel/gate panels. Model and gate code may read its audio in stream order but must not access reference transcripts or outcome metrics before the run is complete and outputs are locked.

The fresh confirmatory *stream* and gate reference panel serve different purposes. Do not calculate final confirmatory WER on the same labelled panel used repeatedly to decide whether updates are accepted.

### 4.2 Cohort size and composition

Use the existing Cohort 2 design as the **target layout**, not as an assumption that enough new data exists:

- Six accent strata: Australian, Canadian, England, Irish, South Asian, and US English.
- Target 78 speakers per stratum (468 speakers total), 15 clips per speaker (7,020 clips total), if a new speaker-disjoint eligible population can be established.
- Preserve exact speaker-to-stratum mapping; each speaker must map to one and only one stratum.
- Verify no speaker overlap with all historical evaluation sets, development sets, sentinel panels, and Cohort 3.
- Verify no clip overlap, duplicate recording IDs, missing references, and duplicate audio hashes.

**Feasibility HOLD:** Before curation is locked, measure the eligible speaker count in every accent after applying the locked curation predicate and all overlap exclusions. If the target is infeasible, do not silently reuse Cohort 2 speakers or weaken filters after inspecting WER. Either (a) identify a valid external reserve source, or (b) design a smaller balanced cohort based on a documented power analysis and freeze that design before the confirmatory run. Label an underpowered run exploratory, not confirmatory.

### 4.3 Dataset and manifest locking

Create separate manifest and lock artifacts for development, gate-reference, and Cohort 3. Each lock should record:

- dataset/source/version and curation script commit;
- split ID and speaker-disjointness proof;
- canonical row count and counts by accent/speaker;
- transcript and audio-file availability checks;
- CSV byte-level SHA-256, canonicalized LF SHA-256 where useful, and per-audio SHA-256 or an immutable content manifest;
- all deterministic seeds and tie-breaking rules;
- an explicit `role`: `development`, `gate_reference`, or `confirmatory_evaluation`;
- a statement that Cohort 3 outcomes are sealed until all runs complete.

The runner must reject a confirmatory manifest whose role, hashes, speaker overlap, row counts, stratum balance, or audio validation fail. A successful data preflight does not, by itself, authorize expensive execution.

## 5. Arms and matched execution

Run the following three primary arms on the *same* Cohort 3 clips, in the same fixed order, with the same model initialization and decoding configuration:

### Arm A — Static baseline

- Frozen checkpoint `facebook/wav2vec2-base-960h` unless the protocol explicitly locks another model.
- No model or optimizer updates.
- Fixed audio conversion, text normalization, CTC decoding, and WER implementation.

### Arm B — Corrected ungated SUTA

- Uses the exact candidate-generation function and frozen hyperparameters chosen during development for Arm C.
- Attempts the same stream update opportunities as Arm C.
- Commits every candidate that passes the shared **numerical validity** contract; it does not consult DSG's overall-risk/accent/disparity utility rules.
- If a candidate becomes numerically invalid, do not allow NaN/Inf state to propagate. Record the numerical failure and follow the predeclared arm-failure policy. Recommended rule: mark the arm as a numerical protocol failure, retain a full diagnostic record, and report both the failure and all valid pre-failure outputs. Do not silently turn the arm into DSG or hide the failed portion of the run.

The numerical contract is a process-integrity guard, not an accuracy/fairness gate. The protocol must explicitly state this distinction when interpreting Arm B.

### Arm C — Frozen DSG

- Same candidate-generation method, loss, learning rate, optimizer design, batch/window schedule, preprocessing, and decoder as Arm B.
- Builds a candidate on an isolated copy of the current live model **and optimizer state**.
- Runs the numerical validity contract. Invalid candidates are rejected before gate evaluation.
- Evaluates valid candidates against the separate locked gate-reference panel.
- Promotes both candidate model state and matching optimizer state only when every frozen gate criterion passes. Otherwise discards the complete candidate and optimizer copy.
- At every rejected candidate, asserts bitwise live-model parameter/buffer hash invariance and verifies that live optimizer state is unchanged.

Optional ablations (for example, legacy MCC, no numerical guard, or alternate loss) belong in development only unless separately preregistered. They are not replacements for the three primary arms.

## 6. Primary endpoint and confirmatory hypotheses

### 6.1 Primary metric

Use corpus WER computed from total substitutions, deletions, insertions and reference words under one frozen normalizer and decoder. Report WER as a percentage. Do not compare rounded display values; decisions use full-precision counts and estimates.

Define:

- `Delta_static = WER_DSG - WER_static` in percentage points;
- `Delta_ungated = WER_DSG - WER_ungated` in percentage points;
- negative values favor DSG.

### 6.2 Required primary conclusion

The primary accuracy objective passes only when both paired comparisons establish superiority:

1. `Delta_static < 0`, with the adjusted one-sided upper confidence bound below zero.
2. `Delta_ungated < 0`, with the adjusted one-sided upper confidence bound below zero.

A point estimate below zero without the required uncertainty evidence is **not** a pass. A superiority claim against only one comparator is a partial result, not success under this protocol.

### 6.3 Paired, speaker-clustered inference

- Each speaker is the independent resampling unit; utterances from the same speaker must not be treated as independent observations.
- Resample speakers within accent strata, keeping the three arms paired within each selected speaker.
- Recalculate corpus WER and both paired differences in every bootstrap replicate.
- Prespecify the bootstrap algorithm, seed, number of replicates (recommended minimum 20,000 for final analysis), interval construction, treatment of duplicate resampled speakers, and multiplicity correction.
- Use a one-sided family-wise error procedure across the two superiority comparisons and all prespecified fairness checks. Holm adjustment is an acceptable transparent default; a validated simultaneous max-statistic procedure is also acceptable if frozen before the study.
- Also report unadjusted estimates and confidence intervals for interpretation, clearly labelled as unadjusted.

Before freezing, run a speaker-cluster simulation-based power analysis using development estimates. Target at least 90% power for the *joint* primary requirement at the frozen error rate, or state the achieved power and downgrade the study to exploratory if it is inadequate. Do not infer adequate power from a large number of utterances alone.

## 7. Accent fairness and disparity estimands

### 7.1 Per-accent non-inferiority / unacceptable-regression rule

For each of the six accents `g`, define:

`Delta_g = WER_DSG,g - WER_static,g`.

Operational recommendation for the draft: use **+2.0 WER percentage points** as the provisional maximum unacceptable regression margin for each accent, matching the order of magnitude of the existing engineering gate tolerance. This value is not automatically scientifically justified merely because it exists in code. Before freeze, document why +2.0 pp is acceptable for this study; if the research owner cannot justify it, use a stricter margin (including 0 pp) and recalibrate on development data. Never choose the margin by looking at Cohort 3 outcomes.

Each accent passes only if its multiplicity-adjusted one-sided upper confidence bound for `Delta_g` is at or below the frozen margin. A point estimate within the margin is insufficient if uncertainty crosses it.

### 7.2 Disparity must not increase

For each arm, define accent disparity `D = max_g(WER_g) - min_g(WER_g)`, in percentage points. Define `Delta_D = D_DSG - D_static`.

The confirmatory fairness requirement is strict: the multiplicity-adjusted one-sided upper confidence bound for `Delta_D` must be **at or below 0 pp**. A lower disparity caused by all accents becoming similarly inaccurate is not a fairness success because the primary accuracy criteria must also pass.

Estimate uncertainty by resampling speakers within accents and recalculating the full max-minus-min disparity on every replicate. Do not infer uncertainty for `Delta_D` from the difference between two point estimates alone.

### 7.3 Gate-level fairness thresholds

The per-candidate gate should enforce:

- all accent-specific regression UCBs `UCB(Delta_g_candidate_vs_live) <= +2.0 pp`, after the frozen correction/alpha-spending method;
- `UCB(Delta_D_candidate_vs_live) <= 0 pp`;
- these checks must use a statistically validated repeated-look procedure. The final evaluation analysis still compares DSG with static on the fresh confirmatory stream.

The gate-level criterion controls each candidate transition; the final confirmatory criterion evaluates the end-to-end deployed policy. One does not substitute for the other.

## 8. Frozen candidate acceptance rule

No minimum acceptance rate is allowed. A candidate is accepted only if **all** conditions below hold:

1. **Numerical integrity:** finite scalar loss, finite gradients and gradient norm, finite post-step parameters/buffers, finite logits and valid decoder outputs; all checks pass.
2. **Overall candidate utility:** the paired candidate-versus-current-live point estimate has `Delta_R < 0` and the calibrated upper confidence bound satisfies `UCB(Delta_R) <= 0 pp`.
3. **Every accent:** for each `g`, the frozen upper bound satisfies `UCB(Delta_g) <= +2.0 pp` (or the finalized prespecified margin).
4. **Disparity:** `UCB(Delta_D) <= 0 pp`.
5. **Evidence validity:** sufficient nonempty paired gate data, valid speaker/stratum mapping, supported statistic regime, and no missing metric or degenerate computation that would invalidate the bound.

Ties, missing metrics, empty or malformed gate inputs, non-finite statistics, unsupported sample sizes, and any numerical error are fail-closed rejections. A candidate rejected for numerical reasons must be distinguished in the logs from a numerically valid candidate rejected for utility/fairness reasons.

### Important sequential-statistics warning

Do not automatically carry forward the current O'Brien–Fleming schedule as if its false-acceptance guarantee were proved for this deployment. Repeatedly testing many candidate models on the same fixed gate panel creates dependence and adaptive-selection risk. The mathematical validity of a standard boundary under a simple Brownian/Gaussian score model does not, on its own, prove family-wise error control for this candidate-generation process.

Before freezing the v1.4 gate:

- define the exact estimand, score process, information fraction, repeated-look error allocation, and dependence assumptions;
- simulate the **complete** stream process, not just isolated statistics, on development-derived paired error profiles;
- test null/equivalent candidates, neutral ties, modest improvement, worsening candidates, a regression isolated to one accent, disparity increase, candidate collapse, and numerical failure;
- report false acceptance / false rejection rates with uncertainty, scenario coverage, and limitations;
- fail the calibration phase if the desired error control is not supported. Do not label the boundary “validated” based only on the existing Gaussian random-walk simulation.

## 9. Candidate generator: development plan

Development must establish that the candidate generator can produce stable candidates that can genuinely improve ASR, before DSG is evaluated as a selector. Select the generator on development speakers, never by maximizing acceptance rate.

### 9.1 Required numerical repair

Implement an atomic update transaction. A candidate must be isolated from the live model until validation and promotion are complete.

Recommended sequence:

1. Clone the live model and optimizer state.
2. Zero candidate gradients with `set_to_none=True`.
3. Compute the adaptation loss using valid-frame masks and the frozen loss definition.
4. Reject if the scalar loss is non-finite.
5. Backpropagate.
6. Verify every gradient is finite; compute a finite global gradient norm; call gradient clipping with `error_if_nonfinite=True`.
7. Apply the optimizer step only to the candidate copy.
8. Verify every floating model parameter and relevant buffer is finite after the step.
9. Run candidate inference on the gate panel and verify all logits/decoded outputs are valid.
10. Run the frozen gate. Promote both candidate model and optimizer state atomically only if all conditions pass; otherwise discard both copies.

Sketch (adapt names and error handling to the actual implementation):

```python
optimizer.zero_grad(set_to_none=True)
loss = compute_adaptation_loss(candidate_model, batch)

if not torch.isfinite(loss).all():
    return reject("nonfinite_loss")

loss.backward()
params = [p for p in candidate_model.parameters() if p.requires_grad]
if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in params):
    optimizer.zero_grad(set_to_none=True)
    return reject("nonfinite_gradient")

try:
    grad_norm = torch.nn.utils.clip_grad_norm_(
        params, max_norm=1.0, error_if_nonfinite=True
    )
except RuntimeError:
    optimizer.zero_grad(set_to_none=True)
    return reject("nonfinite_gradient_norm")

if not torch.isfinite(grad_norm).all():
    optimizer.zero_grad(set_to_none=True)
    return reject("nonfinite_gradient_norm")

optimizer.step()  # candidate copy only
if any(not torch.isfinite(p).all() for p in candidate_model.parameters()):
    return reject("nonfinite_parameter_after_step")

if not all_floating_buffers_are_finite(candidate_model):
    return reject("nonfinite_buffer_after_step")
```

This is design pseudocode, not a drop-in patch. The actual helper must handle optimizer state, model buffers, mixed precision if ever enabled, candidate disposal, and detailed audit logging.

### 9.2 Loss and tensor correctness

- Keep the MCC normalization stabilizer inside the square root, as in the reconciled code, and add unit tests with zero-probability / absent-token classes to check finite loss and finite gradients.
- Make padding treatment explicit. Entropy/MCC terms must not give padded frames unintended weight. Compute each utterance's valid output-frame length using the model's feature-length mapping and mask the loss accordingly.
- Confirm the correct attention-mask policy for the chosen Wav2Vec2 checkpoint and processor; do not pass a mask blindly without checking checkpoint/config requirements.
- Make train/eval mode and dropout behavior explicit. Record all RNG seeds and test deterministic repeatability under the frozen environment.
- Keep the decoder and text normalizer identical across arms.
- Log pre-update and post-update output diagnostics: blank-token fraction, nonblank-token rate, decoded transcript length, empty-hypothesis count, repeated-token rate, logit finiteness, loss terms and gradient norm. Any hard collapse threshold must be derived on development data and frozen before confirmation.

### 9.3 Bounded development grid

Use a small, recorded grid rather than open-ended tuning. Recommended first pass:

- window size `K in {4, 8, 16}`;
- learning rate `lr in {1e-5, 3e-5, 1e-4}`;
- trainable parameters: LayerNorm only as the initial conservative configuration;
- candidate loss variants: (A) numerically corrected entropy + MCC; (B) confidence-filtered CTC pseudo-label update with a fixed confidence/blank-collapse rule; (C) augmentation-consistency update if the first two are unstable or ineffective.

Run the full grid only on development data. Store all trials, including bad runs; do not delete failed combinations from the audit trail. Use development WER by accent, numerical failure, blank-collapse diagnostics, runtime, and candidate paired improvement to choose a single frozen method. Do not choose by acceptance percentage alone. The exact grid may be reduced for compute reasons, but any reduction must be documented before outcomes are reviewed.

### 9.4 Optimizer-state parity

Arm B and Arm C must use the same optimizer-state semantics. Recommended implementation: clone the current live optimizer state along with the candidate model; update the candidate copy; if accepted, atomically promote both. If rejected, discard both, leaving live model and live optimizer unchanged. In Arm B, valid candidate updates are promoted on every update opportunity. Never compare persistent optimizer state in one arm with an inadvertently reset state in the other.

## 10. Gate reference panel and repeated-look calibration

The existing Stage 5 sentinel panel has only 30 core speakers and about 281 reference words according to the prior project audit. That is a weak basis for fine-grained per-accent and disparity decisions, especially under many repeated candidate evaluations. The uncertainty floor previously used was described as an engineering safeguard rather than a formally calibrated standard error.

For v1.4:

1. Audit feasibility of a larger speaker-disjoint gate panel. Suggested target: at least 120 speakers, 20 per accent, with 2 or more usable clips per speaker if the corpus permits. The final size must follow a development-based precision/power analysis, not convenience.
2. Aggregate inference at speaker level. Extra utterances help estimate each speaker's error but do not increase the independent-speaker count.
3. Keep gate-reference speakers separate from development tuning speakers and final Cohort 3 evaluation speakers. Do not reuse Cohort 3 references for online gating.
4. Specify how many sequential update opportunities occur and the exact stopping rule. Freeze any seed, resampling count, and fallback for zero-variance cases.
5. Calibrate the end-to-end process on development-derived trajectories, including adaptation-induced correlations and all gate criteria. Include positive and negative alternatives, not only the null.
6. Report calibration uncertainty and failures. If the planned gate does not meet the prespecified false-acceptance/safety criteria, stop and redesign on development data before freezing.

The target panel size is a proposal contingent on feasibility. Do not claim the existing 30-speaker panel is statistically adequate without supporting analysis.

## 11. Confirmatory power and lock procedure

Before locking Cohort 3:

- estimate speaker-level paired differences and variance from development data;
- simulate the actual six-stratum, paired, sequential three-arm design;
- estimate joint power for DSG superiority over both comparators and power for all accent non-inferiority requirements;
- examine how often a 2 pp regression margin or zero-disparity-growth requirement is inconclusive under realistic variance;
- determine the required speaker counts; if target power cannot be achieved with available eligible data, call the study exploratory or obtain more eligible data rather than making a weak confirmatory claim.

Then freeze these items together:

- protocol file and protocol hash;
- exact implementation commit SHA and clean-tree status;
- environment lock (Python, PyTorch, Transformers, CUDA/driver, processor/model revisions);
- candidate-generation config and all random seeds;
- gate thresholds, alpha/error-control rule, confidence procedure and bootstrap seeds;
- development winner and reason for selection;
- Cohort 3 and gate-panel manifests, row/clip/audio hashes and disjointness report;
- endpoint definitions, multiplicity correction, exclusion policy, run-failure policy and final success decision rules;
- compute-budget authorization / project governance artifact consistent with university requirements.

No threshold, loss, candidate generator, cohort filter, margin, decoder, or metric may be changed after the confirmation freeze without declaring the run amended/exploratory and creating a new versioned protocol.

## 12. Final analysis and metrics

### Confirmatory outcomes

- Corpus WER per arm.
- Substitutions, deletions, insertions, reference words, hypotheses count and empty-hypothesis count.
- WER and paired change per accent.
- Max-minus-min disparity per arm and `Delta_D`.
- Paired speaker-level distributions and adjusted confidence intervals/p-values for both primary comparisons and all fairness criteria.
- Final gate acceptance count and rate (descriptive only), with acceptance/rejection reasons.
- Numerical-failure count, non-finite loss/gradient/parameter counts, blank-collapse indicators, model/optimizer hash transitions and rollback invariance checks.
- Runtime, GPU/CPU, memory, inference/update time and environment metadata.

### Required interpretation rules

- If DSG improves over static but not corrected ungated SUTA: primary objective fails.
- If DSG improves over both but any accent's regression bound exceeds the margin: fairness objective fails or remains unproven, depending on estimate and uncertainty.
- If disparity's upper confidence bound is positive: the no-increase requirement is not demonstrated.
- If zero candidates are accepted: report protection/invariance honestly; do not claim selective-accuracy improvement.
- If the ungated arm fails numerically: report that protocol failure, do not use the failed arm as sole evidence of DSG superiority. The primary comparison requires a valid corrected ungated baseline; rerun only under the predeclared restart rule and preserve the failed output.
- If inference is too imprecise: call the result inconclusive, not “almost passed.”

## 13. Implementation map

Use new versioned modules/configs so the v1.3.4/historical implementation remains inspectable. Proposed repository paths (confirm naming against current conventions before creating):

| Artifact | Purpose |
|---|---|
| `reports/stage6m/v1.4.0_selective_adaptation_protocol.md` | This protocol, revised into the final frozen version |
| `configs/stage6m/v1.4.0_confirmatory.yaml` | Frozen config: arms, loss, LR, K, gate thresholds, seeds, inference |
| `src/dsg_ctta/adaptation/safe_update.py` | Atomic candidate update, finite checks and structured failure reasons |
| `src/dsg_ctta/controller/streaming_gate_v14.py` | Versioned gate interface and frozen decision semantics |
| `src/dsg_ctta/evaluation/paired_cluster_inference.py` | Paired speaker-stratified inference, WER, accent and disparity analysis |
| `scripts/validate_stage6m_v14_data.py` | Manifest, hashes, audio validation and partition disjointness checks |
| `scripts/run_stage6m_v14_development.py` | Development grid only; never writes confirmatory success reports |
| `scripts/run_stage6m_v14_confirmatory.py` | Frozen runner with manifest/protocol/hash checks and label separation |
| `scripts/analyze_stage6m_v14_confirmatory.py` | Offline analysis only after predictions and run manifest are locked |
| `tests/research_validity/stage6m_v14/` | Numerical, data, gate, rollback, inference and end-to-end validity tests |
| `reports/stage6m/v1.4.0/` | Separate development, calibration, preflight and confirmatory reports |
| `results/stage6m_v14/development/` | Append-only development runs and failure logs |
| `results/stage6m_v14/confirmatory/` | Immutable raw outputs keyed by frozen run ID |

### Required tests

**Numerical transaction tests**
- Non-finite loss prevents backward/step and logs `nonfinite_loss`.
- One non-finite gradient prevents optimizer promotion.
- Non-finite gradient norm fails closed.
- NaN/Inf parameter or floating buffer after optimizer step discards the candidate and optimizer copy.
- Candidate logits and decoded hypotheses are checked before gate scoring.
- Rejected candidates preserve exact live model and optimizer hashes.
- Accepted candidates promote model and matching optimizer state together.
- Zero MCC token counts yield finite loss/gradients or an explicit rejection.
- Padding masks and valid output lengths behave correctly for mixed-duration batches.

**Gate tests**
- Positive overall risk change rejects.
- Tie / zero observed improvement rejects.
- UCB_R greater than zero rejects.
- Any accent UCB above the frozen margin rejects.
- Any disparity UCB above zero rejects.
- NaNs, missing group, invalid word counts, duplicate/mismatched speaker mappings, or invalid samples reject.
- Repeated-look alpha/error-control tests exercise the whole trajectory under null, neutral, beneficial, and harmful alternatives.
- One accent-only degradation and disparity-only increase are both rejected.

**Data and analysis tests**
- No speaker or recording overlap among development, gate-reference, historical evaluation and Cohort 3.
- Exactly one stratum per speaker; prescribed number of speakers per accent.
- Lock mismatch, audio hash mismatch, missing files or transcript schema errors fail preflight.
- Same raw hypotheses produce identical WER metrics across arms and analysis runs.
- Paired bootstrap clusters by speaker rather than utterance.
- Multiplicity adjustment and pass/fail decisions have hand-calculated toy fixtures.
- Confirmatory runner cannot use evaluation transcripts at inference/gate time.
- Clean run records commit SHA, config hash, manifests and environment; a dirty or changed tree fails frozen execution checks.

## 14. Git, provenance and historical preservation

1. Keep commits `8324f38...`, `c3305d6...`, and `300a676...` and all other history untouched. The first is the execution source identified in the physical report; the second records the physical artifacts; the third reconciles report provenance and diagnostics.
2. Branch from the reconciled `300a676598eb44f30afb8eeb6bb122842aa2b68a` baseline for development. Do not force-push or rebase historical project commits. A separate branch such as `stage6m-v1.4-selective-dev` is appropriate.
3. Preserve the old Cohort 2 raw outputs/report. Add a new audit note explaining that Cohort 2 is now historical and outcome-exposed for v1.4 candidate/gate selection; do not relabel its results as v1.4.
4. Commit the protocol draft before code changes; then commit implementation in logical stages. The final freeze commit/tag must contain the final protocol, config, tests and manifest references.
5. Run development only against development IDs. The confirmatory runner should require the frozen version tag/commit, clean working tree and manifest hashes.
6. Treat raw output as append-only. A correction creates a new run ID and a reconciliation report. Never overwrite a completed raw run or make repaired post hoc metrics appear to have come from the original execution source.
7. Governance text should be internally consistent. If university rules do not require supervisor sign-off, reconcile outdated report wording and record the actual authorized project-lead/compute decision. Do not leave contradictory “HOLD” and “authorized” statements in different artifacts.

## 15. Ordered execution plan and exit criteria

| Phase | Work | Exit criterion | Stop condition |
|---|---|---|---|
| 0. Preserve baseline | Tag/bookmark current history; copy no raw artifacts into mutable working files; create a development branch | Baseline SHA and artifact inventory recorded | Any history rewrite or missing raw artifact |
| 1. Protocol reconciliation | Adopt this draft, define accent margin, primary statistics, Cohort 3 plan and governance language | Versioned protocol draft committed; unresolved choices listed | Margin, estimand or data roles remain ambiguous |
| 2. Atomic numerical safety | Implement candidate/optimizer clone, finite checks, valid-frame masking, audit logs | Numerical tests all pass; rejected candidate leaves live state unchanged | Any NaN/Inf can reach live state |
| 3. Correct comparator | Match generator/hyperparameters/optimizer state between Arms B/C; set explicit numerical failure policy | Deterministic fixture proves arms differ only by update-promotion policy | Optimizer mismatch or silent arm change |
| 4. Candidate development | Bounded grid on development data; log every run; select one candidate generator | At least one stable candidate method evaluated by WER/fairness and diagnostics; winner rationale documented | Choose winner only by acceptance rate or delete negative runs |
| 5. Gate calibration | Use independent development calibration panel; test whole repeated stream under null and alternatives; revise statistic if needed | Frozen false-acceptance/safety criteria supported with uncertainty and limitations recorded | Error control unsupported or panel too weak |
| 6. Data feasibility and power | Establish fresh, speaker-disjoint Cohort 3; calculate joint power and fairness feasibility | Preflight passes; power adequacy documented; hashes locked | Any overlap or insufficient data treated as confirmatory without qualification |
| 7. Freeze | Freeze protocol/config/code/env/manifests/analysis and confirmatory permissions | Signed-off freeze record, clean tree and immutable identifiers | Any mutable decision remains after freeze |
| 8. Fresh physical confirmation | Execute all primary arms on identical Cohort 3 stream; keep labels sealed; save all outputs | Completed run with hashes, environment and no unresolved provenance issue | Failure triggers predeclared halt/restart; no selective rerun based on outcomes |
| 9. Independent reconciliation | Verify joins, words/errors, stratum labels, paired inference and gate logs from raw output | Reproducible analysis and independent audit checklist pass | Any unresolved denominator, mapping, hash or statistical discrepancy |
| 10. Report conclusion | Apply frozen composite decision rule | Success, failure or inconclusive outcome explicitly stated | No post hoc relaxation of criteria |

## 16. Frozen composite success rule

Declare **Stage 6M v1.4.0 selective-adaptation success** only if all of the following are true:

- **Accuracy:** Adjusted one-sided upper confidence bounds for both `WER_DSG - WER_static` and `WER_DSG - WER_corrected_ungated` are below zero.
- **Accent regression:** For all six accents, adjusted upper confidence bounds for `WER_DSG,g - WER_static,g` are at or below the prespecified maximum regression margin.
- **Disparity:** The adjusted one-sided upper confidence bound for `D_DSG - D_static` is at or below zero.
- **Integrity:** No unresolved numerical, data-leakage, provenance or protocol deviation invalidates the comparison.

No minimum acceptance rate appears in this rule. Acceptance rate and rejection reasons are reported to explain how DSG behaved, not as a success target.

A result can be scientifically valuable without meeting the composite objective. For example, zero acceptances can validate a protective behavior on a cohort, while still failing to establish beneficial adaptation. A mixed or inconclusive result must be reported as mixed or inconclusive.

## 17. Immediate next actions

1. Commit this as a **draft** protocol on a branch from `300a676...`; do not modify old result reports to make them look like v1.4 output.
2. Implement the atomic numerical update transaction and its unit tests before any further benchmark run.
3. Establish exact development, gate-reference and Cohort 3 speaker-disjointness; do a feasibility/power audit before promising 468 speakers.
4. Run the bounded development grid and select one stable candidate generator based on accuracy and fairness evidence, not acceptance rate.
5. Calibrate the complete repeated gate process and freeze all rules before collecting/inspecting fresh confirmatory outcomes.

**Bottom line:** The route to a positive result is not to make DSG accept more updates by force. It is to build stable candidates that improve recognition, ensure the gate can reliably distinguish those candidates from harmful ones, and test the frozen policy on data that did not influence the choices.
