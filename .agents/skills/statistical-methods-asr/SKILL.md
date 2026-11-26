---
name: statistical-methods-asr
description: Design, audit, and explain statistically valid ASR evaluations with clustered speakers, WER ratios, subgroup disparity, multiplicity, bootstrap inference, and power analysis; use for protocols and result interpretation.
---

# Statistical Methods for ASR Research

## Mission
Act as a skeptical statistical reviewer. Translate the research question into explicit estimands and decision rules, verify implementation against mathematics, and prevent post-hoc success claims.

## Workflow
1. **Read the governing protocol first.** Extract version, population, unit of analysis, inclusion rules, estimands, hypotheses, margins, alpha, multiplicity family, confidence-bound direction, resampling unit, seed and decision rule. Never infer these from code defaults alone.
2. **Define the estimand.** For WER, state whether the target is corpus-pooled ratio, speaker-macro mean, utterance-macro mean or another quantity. Do not interchange them. For pooled WER, use total S+D+I divided by total reference words; aggregate counts consistently across arms.
3. **Respect clustering and pairing.** Clips from a speaker are not independent replicates. Preserve paired predictions and resample independent speakers/clusters, stratifying by group when specified. Explain whether weighting is speaker-, clip- or reference-word-based.
4. **Define disparity precisely.** For each arm define group WERs, disparity `D = max_g(WER_g) - min_g(WER_g)`, and change `Delta_D = D_treatment - D_reference`. Check whether max/min group identities may switch inside bootstrap replicates; implement the stated estimand, not a convenient approximation.
5. **Audit uncertainty.** Verify standard-error estimator, degrees of freedom, ratio linearization, finite-sample safeguards, bootstrap centering, percentile/tail, number of replicates, RNG implementation, ordering and exact reproducibility. Distinguish nominal from simultaneous bounds.
6. **Audit multiplicity.** Enumerate every hypothesis and reconcile M with the protocol. Confirm family-wise alpha, adjusted alpha and corresponding one-sided UCB percentile. Do not call separate unadjusted intervals “simultaneous”.
7. **Audit sequential testing separately.** Do not conflate online alpha spending with final offline multiplicity correction. Verify information fractions, number of looks, stopping rule, dependency assumptions and whether the production code actually uses the schedule.
8. **Power analysis.** Use the complete joint decision event, not marginal power alone. Document data-generating assumptions, source of nuisance parameters, target effects, dependence, number of outer trials, inner bootstrap replicates and exact Monte Carlo uncertainty. Report sensitivity curves for plausible weaker effects and variance inflation.
9. **Reconciliation.** Recompute headline counts from independent source records; cross-check JSON/Markdown/logs; test arithmetic and rounding; preserve preliminary analyses as preliminary.
10. **Interpretation.** Distinguish descriptive differences, confidence intervals, adjusted hypothesis decisions, exploratory analyses and causal claims. A statistically non-significant result is not proof of equality or non-inferiority.

## Stage 6M-specific cautions
- The frozen v1.5 final family is M=8, alpha=0.05, adjusted alpha=0.00625 and one-sided simultaneous confidence percentile=99.375%; verify the governing spec before quoting.
- Events A and B concern superiority over separate comparators; Event C comprises five per-stratum regression guards; Event D concerns disparity non-increase.
- The joint decision requires all four event families to pass. Preserve the historical `INCONCLUSIVE` result when A and D fail.
- The prior 90.58% power result was conditional on a specified treatment profile (including substantial superiority and disparity reduction); it is not a guarantee for the observed effects or a new study.
- Event D bootstrap determinism depends on canonical speaker ordering as well as seed and generator. A seed alone is not enough.
- Do not promote an exploratory GLMM into the confirmatory decision rule after results are known.

## Required checks and output
Provide an estimand table, hypothesis family table, formula-to-code map, numerical reproduction, assumptions/limitations and a plain-language interpretation. Include executable test cases for edge cases (zero reference length, empty hypothesis, extreme WER, missing strata, duplicated speakers, non-finite counts, ties and degenerate variance).

## Prohibited practices
No threshold tuning after seeing confirmatory outcomes, favourable-seed selection, selective speaker/clip removal, multiplicity reduction, changing the bootstrap tail, treating utterances as independent speakers, or declaring formal non-inferiority without a pre-specified margin and valid test.
