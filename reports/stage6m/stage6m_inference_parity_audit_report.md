# Stage 6M — Independent Statistical Parity Audit (Task 1)

| Field | Value |
|---|---|
| Base commit | `8b993162f62ddc0fc9a436f84a830aec14e3df52` (verified `HEAD` on `main`) |
| Branch | `stage6m-five-stratum-parity` (local; **not pushed**) |
| Governance | `DRAFT_HOLD` preserved. No audio, manifest, adaptation, or frozen-code change. |
| Audit script SHA-256 | `19fa03b10e1e04c6…` (unmodified) |
| Production inference SHA-256 | `a699ca84fbdadf68…` (unmodified) |
| Files changed | **1 added**: `tests/research_validity/test_stage6m_inference_parity.py`. No tracked file modified. |

## Verdict: PARTIAL PASS

* **PASS** — six-stratum inference parity. For identical records and an identical bootstrap stream, the audit
  simulator and the frozen production inference agree on every decision and on every numeric quantity that could
  be observed (t quantiles, SEs, UCBs, disparity bootstrap percentile).
* **Not supported** — the simulator's "protocol-exact" label. The five-stratum (M=8) procedure does not exist in
  production, the multiplicity method named in governing artifacts (Holm) is not what is implemented (Bonferroni),
  and the data-generating model departs from `DesignStagePowerSpec` (Task 3 scope; flagged, not resolved here).

## 1. Formulas compared

| # | Quantity | Production (`paired_cluster_inference.py`) | Audit (`stage6m_multi_corpus_feasibility_audit.py`) | Result |
|---|---|---|---|---|
| 1 | Word-weighted WER | L583-592 `Σerr/Σwc·100` | L1030-1034 same | MATCH (hand-calc fixture + mutation M4) |
| 2 | Static / SUTA contrasts | `wer3-wer1`, `wer3-wer2` | `(E3-E1)/W·100`, `(E3-E2)/W·100` | MATCH |
| 3 | Linearised ratio SE | L786 `100·sd(u,ddof=1)/√n/mean(w)`, u at point est. | L1044/1049/1069 same | MATCH (numeric, tol 2.5e-4) |
| 4 | df and one-sided t quantile | L788 `t.ppf(1-α/M, n-1)` | L1033, 1042, 1063 same form | MATCH for M=9 |
| 5 | Static/SUTA decision | L813 `pt<0 and UCB<0` | L1045/1050 same | MATCH |
| 6 | Per-accent guard | L815 `UCB ≤ 2.0` | L1071 `UCB > 2.0` ⇒ fail | MATCH |
| 7 | Stratified paired bootstrap | L643 per-accent `integers(0,n,size=n)`, arms paired | L1088-1100 same call order | MATCH (identical stream ⇒ identical percentile) |
| 8 | Disparity UCB | L805 `percentile(Δ_D, 100(1-α/M))` ≤ 0 | L1104 same | MATCH (numeric) |
| 9 | Multiplicity family size M | L675 hard-coded **9** | L919 `2+K+1` (9 or 8) | **MISMATCH for K=5** |
| 10 | Accent set | L26, L551 six canonical, rejects 5 | caller-supplied | **MISMATCH for K=5** |

## 2. Mismatches and findings (file:line)

1. **Production cannot run five strata as M=8.** L551 rejects a five-accent cohort. With `canonical_accents`
   overridden it still applies α/9 (L675). `simulate_design_stage_joint_power` (L241-243) hard-codes six accents and
   M=9 with no parameter to change either. Pathway 1 is a protocol *amendment*, not an executable v1.4.0 variant.
2. **Multiplicity method: spec says Holm, code is Bonferroni.**
   *Implemented:* plain Bonferroni, M=9, decisions from simultaneous UCBs at α/9; adjusted p = min(1, 9·p_raw) is
   reported but never used for decisions.
   *Named in governing artifacts:* module docstring L13, `evaluation/__init__.py`, `reports/stage6m/
   stage6m_rule_b_power_simulation_spec.json` ("Holm-Bonferroni across all 9 hypotheses"; success = "all 9 rejected
   … under Holm-Bonferroni"), and the independent remediation audit.
   *Protocol §6.3:* Holm is "an acceptable transparent default"; a validated simultaneous max-statistic procedure is
   also acceptable **if frozen before the study**. The protocol text does not mandate either, and never names
   Bonferroni.
   *Consequence:* for the event "reject all M", Holm's rejection set strictly contains Bonferroni's (shown
   behaviourally in `test_implemented_multiplicity_is_plain_bonferroni_not_holm`). Implemented behaviour is therefore
   **conservative** (Type I preserved) and Bonferroni-based power is a **lower bound** relative to Holm. But the audit
   cannot be called "protocol-exact" while the spec JSON says Holm. This is a human governance decision: freeze
   Bonferroni explicitly (fix docstring + spec JSON) **or** implement Holm. Neither was changed here.
3. **Reported p-values are not decision-consistent.** Production p uses a score statistic with SE at the null
   threshold (L772); the decision uses a Wald UCB with SE at the point estimate (L786). In a deliberately
   boundary-focused scan, 11 of 1,760 ratio-criterion evaluations had `adj_p<0.05` and the decision disagree
   (e.g. UCB=+1.9756 passes, adj_p=0.063). Verdicts are unaffected (UCB is authoritative); the printed p-values are not.
4. **Dead code.** L740 `for spec in test_specs:` has an empty-effect body; `criteria_results` and
   `simultaneous_percentile` are defined twice. Harmless, should be cleaned in a *new* versioned path, not in frozen v1.4.0.
5. **Two copies of the protocol differ.** Root `stage6m_v1_4_selective_adaptation_protocol.md` (458 lines, older draft)
   vs `reports/stage6m/…` (473 lines, Decision Rule B + §14.7). Both carry the same §6.3 multiplicity wording.
   Decide which is the frozen artifact before hashing it as `approved_protocol_sha256`.

## 3. Tests added and results

`tests/research_validity/test_stage6m_inference_parity.py` — 10 tests, **10 passed**.

* Hand-calculated fixture (12 speakers, expected totals derived in the docstring).
* 54-scenario panel (9 effect shapes × 3 seeds × N∈{18,40}), B=1,500, shared bootstrap seed. A non-vacuity guard
  asserts each of Events A–D both passes and fails somewhere (it caught a first panel where D never passed).
* Decisions, t quantiles, SEs/UCBs, disparity percentile: all identical.
* Characterisation tests that *document* the K=5 / M=9 mismatches and Bonferroni-vs-Holm.

**Mutation check (parity tests can fail):** five deliberate errors injected into the audit script — df=n, ddof=0,
disparity percentile 97.5, per-speaker-mean WER, margin 2.5 — were each caught; script restored byte-identical.

## 4. Remaining limitations

* **Full suite NOT run.** Sandbox lacks `torch`/`patsy` and the raw Common Voice TSV. Run here:
  `12 failed, 156 passed, 2 skipped, 10 collection errors` (156 includes the 10 new tests). Failure causes: 5 need
  `torch`, 1 needs `patsy`, 4 need the raw CV27 TSV (not in repo), 2 are **CRLF-vs-LF hash locks**
  (`stage5_external_eval.csv`, `reports/stage5/external_speaker_inventory.csv`: lock hashes equal the CRLF form of
  the files exactly, while `.gitattributes` forces LF). The CRLF pair means those two locks fail on any fresh
  checkout; run the suite on your machine for the real 344-test result.
* Parity covers the audit's *decision* path. The audit's data-generating model was not compared to
  `DesignStagePowerSpec` (Task 3).
* Tested at B=1,500 (parity, not precision). Bootstrap precision is Task 4.

## 5. Flag for Task 3 (diagnostic, not a verified power result)

The audit draws per-trial accent effects with σ = 5 pp (L965), which reorders accents. For its five-stratum model the
nominal true Δ_D is −2.00 pp, but over 200,000 simulated draws (accent term only) the true Δ_D has mean −1.03 pp, is
≥ 0 in ~19.9% of studies, and is ≤ −2.0 in only ~30.3%. Joint power may therefore be capped near ~80% regardless of
N. **Verify before running any sample-size sweep.** The simulated DSG-vs-SUTA gap is 1.0–2.0 pp (spec: 3.5) and
clip noise is divided by √15 (L987).
