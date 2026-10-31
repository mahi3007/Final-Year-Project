"""
tests/research_validity/test_stage6m_inference_parity.py

Stage 6M — Independent Statistical Parity Audit (Task 1)
========================================================
Compares the inferential calculations of

  (P) src/dsg_ctta/evaluation/paired_cluster_inference.py
        :: run_confirmatory_paired_cluster_inference      (frozen v1.4.0, REFERENCE)
  (A) scripts/stage6m_multi_corpus_feasibility_audit.py
        :: simulate_hierarchical_power                    (power simulator, UNDER AUDIT)

on IDENTICAL, fixed synthetic speaker records and an IDENTICAL stratified
bootstrap resampling stream.

Method (no committed file is modified)
--------------------------------------
The audit simulator embeds its inference inside a Monte Carlo trial loop, so it
cannot be called on fixed records directly. We therefore drive the *committed*
function for exactly one trial through a scripted RNG that

  * returns the fixed word counts and the fixed Binomial error counts, and
  * delegates all bootstrap index draws to a seeded numpy Generator.

Production draws bootstrap indices with ``rng.integers(0, n, size=n)`` once per
accent (sorted order) per replicate; the audit does the same per accent (list
order) per replicate. Using sorted accents and one shared seed makes the two
index streams identical. Spies on ``scipy.stats.t.ppf``, ``numpy.std`` and
``numpy.percentile`` expose the audit's internal numerics.

Governance: DRAFT_HOLD preserved. No audio, manifest or frozen code touched.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pytest
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import stage6m_multi_corpus_feasibility_audit as audit  # noqa: E402
from dsg_ctta.evaluation import paired_cluster_inference as prod  # noqa: E402

SIX: List[str] = sorted(prod.CANONICAL_PROTOCOL_ACCENTS)
FIVE: List[str] = sorted(a for a in SIX if a != "Irish English")

BASE_WER = {
    "US English": 14.2,
    "Canadian English": 16.1,
    "England English": 17.4,
    "Australian English": 19.3,
    "South Asian English": 23.5,
    "Irish English": 26.1,
}

ALPHA = 0.05
BOOT_SEED = 987654321
N_BOOT = 1500
UCB_TOL = 2.5e-4  # production rounds reported bounds to 4 dp


# ----------------------------------------------------------------------------
# Deterministic synthetic fixtures
# ----------------------------------------------------------------------------
def make_records(
    accents: Sequence[str],
    n_per_stratum: int,
    dsg_shift_pp: Dict[str, float],
    suta_shift_pp: Dict[str, float],
    seed: int,
    between_sd_pp: float = 6.5,
    pair_sd_pp: float = 1.5,
) -> List[Dict[str, Any]]:
    """Fixed integer-count speaker records (wc, err1=static, err2=SUTA, err3=DSG)."""
    rng = np.random.default_rng(seed)
    recs: List[Dict[str, Any]] = []
    for ai, acc in enumerate(accents):
        n = n_per_stratum
        wc = rng.integers(100, 181, size=n)
        p1 = np.clip((BASE_WER[acc] + rng.normal(0, between_sd_pp, size=n)) / 100.0, 0.01, 0.99)
        p3 = np.clip(p1 + (dsg_shift_pp[acc] + rng.normal(0, pair_sd_pp, size=n)) / 100.0, 0.01, 0.99)
        p2 = np.clip(p1 + (suta_shift_pp[acc] + rng.normal(0, pair_sd_pp, size=n)) / 100.0, 0.01, 0.99)
        e1, e2, e3 = rng.binomial(wc, p1), rng.binomial(wc, p2), rng.binomial(wc, p3)
        for k in range(n):
            recs.append(
                {
                    "speaker_id": f"A{ai}_{k:04d}",
                    "stratum": acc,
                    "wc": int(wc[k]),
                    "err1": int(e1[k]),
                    "err2": int(e2[k]),
                    "err3": int(e3[k]),
                }
            )
    return recs


def _uniform(accents: Sequence[str], v: float) -> Dict[str, float]:
    return {a: v for a in accents}


def scenario_panel() -> List[Dict[str, Any]]:
    """Scenarios chosen so that each of Events A-D both passes and fails somewhere."""
    s: List[Dict[str, Any]] = []
    narrowing = {a: -2.5 - 2.0 * (BASE_WER[a] - 14.2) / (26.1 - 14.2) for a in SIX}
    narrowing_strong = {a: -2.0 - 5.0 * (BASE_WER[a] - 14.2) / (26.1 - 14.2) for a in SIX}
    widening = {a: -4.5 + 2.0 * (BASE_WER[a] - 14.2) / (26.1 - 14.2) for a in SIX}
    shapes = {
        "strong_uniform": (_uniform(SIX, -5.0), _uniform(SIX, -1.0)),
        "moderate_uniform": (_uniform(SIX, -2.5), _uniform(SIX, -1.5)),
        "weak_uniform": (_uniform(SIX, -0.8), _uniform(SIX, -0.4)),
        "null": (_uniform(SIX, 0.0), _uniform(SIX, 0.0)),
        "dsg_worse_than_suta": (_uniform(SIX, -2.0), _uniform(SIX, -4.0)),
        "one_accent_regression": ({**_uniform(SIX, -3.5), "Irish English": +3.5}, _uniform(SIX, -1.0)),
        "disparity_narrowing": (narrowing, _uniform(SIX, -1.0)),
        "disparity_narrowing_strong": (narrowing_strong, _uniform(SIX, -1.0)),
        "disparity_widening": (widening, _uniform(SIX, -1.0)),
    }
    for name, (dsg, suta) in shapes.items():
        for seed in (101, 202, 303):
            for n in (18, 40):
                s.append({"name": f"{name}|seed{seed}|n{n}", "dsg": dsg, "suta": suta, "seed": seed, "n": n})
    return s


# ----------------------------------------------------------------------------
# Harness
# ----------------------------------------------------------------------------
class _ScriptedRNG:
    """Replays fixed data draws; delegates bootstrap-index draws to a seeded Generator."""

    def __init__(self, wc_per_accent, err_triples, boot_seed):
        self._wc = iter(wc_per_accent)
        flat: List[np.ndarray] = []
        for e1, e2, e3 in err_triples:  # audit draws e1, e2, e3 in this order per accent
            flat.extend([e1, e2, e3])
        self._bin = iter(flat)
        self._boot = np.random.default_rng(boot_seed)

    def normal(self, loc=0.0, scale=1.0, size=None):
        return 0.0 if size is None else np.zeros(size)

    def integers(self, low, high=None, size=None):
        if low == 100 and high == 181:  # speaker word-count draw in the audit
            return next(self._wc)
        return self._boot.integers(low, high, size=size)  # bootstrap indices

    def binomial(self, n, p):
        return next(self._bin)


def run_production(records, boot_seed=BOOT_SEED, n_boot=N_BOOT, **kw):
    # required_speakers_per_stratum is set absurdly high so the design-stage power
    # simulation is short-circuited; criteria results do not depend on it.
    spec = prod.DesignStagePowerSpec(required_speakers_per_stratum=10**6)
    return prod.run_confirmatory_paired_cluster_inference(
        records, num_bootstrap_replicates=n_boot, seed=boot_seed, alpha_family=ALPHA, design_spec=spec, **kw
    )


def run_audit(records, accents, monkeypatch, boot_seed=BOOT_SEED, n_boot=N_BOOT):
    by = {a: [r for r in records if r["stratum"] == a] for a in accents}
    wc = [np.array([r["wc"] for r in by[a]]) for a in accents]
    errs = [
        (
            np.array([r["err1"] for r in by[a]]),
            np.array([r["err2"] for r in by[a]]),
            np.array([r["err3"] for r in by[a]]),
        )
        for a in accents
    ]
    scripted = _ScriptedRNG(wc, errs, boot_seed)
    t_calls: List[tuple] = []
    std_calls: List[float] = []
    pct_calls: List[tuple] = []
    real_ppf, real_std, real_pct = stats.t.ppf, np.std, np.percentile

    def ppf_spy(q, df, *a, **k):
        v = real_ppf(q, df, *a, **k)
        t_calls.append((float(q), float(df), float(v)))
        return v

    def std_spy(a, *args, **kw):
        v = real_std(a, *args, **kw)
        std_calls.append(float(v))
        return v

    def pct_spy(a, q, *args, **kw):
        v = real_pct(a, q, *args, **kw)
        pct_calls.append((float(q), float(v)))
        return v

    alloc = {"C": {a: len(by[a]) for a in accents}}
    with monkeypatch.context() as mp:
        mp.setattr(np.random, "default_rng", lambda *a, **k: scripted)
        mp.setattr(stats.t, "ppf", ppf_spy)
        mp.setattr(np, "std", std_spy)
        mp.setattr(np, "percentile", pct_spy)
        out = audit.simulate_hierarchical_power(
            accents=list(accents), allocation_matrix=alloc, n_trials=1, n_bootstraps=n_boot, random_seed=0
        )
    pr = out["power_results"]
    return {
        "A": pr["event_a_static_superiority_power"] == 1.0,
        "B": pr["event_b_suta_superiority_power"] == 1.0,
        "C": pr["event_c_accent_regression_guard_power"] == 1.0,
        "D": pr["event_d_disparity_guard_power"] == 1.0,
        "joint": pr["joint_confirmatory_power"] == 1.0,
        "t_calls": t_calls,
        "std_calls": std_calls,
        "pct_calls": pct_calls,
        "M": out["simulation_parameters"]["m_simultaneous_hypotheses"],
    }


def prod_events(report) -> Dict[str, bool]:
    c = report.criteria
    acc_ok = all(v.is_success for k, v in c.items() if k.startswith("accent_safety_"))
    return {
        "A": c["primary_superiority_static"].is_success,
        "B": c["primary_superiority_ungated"].is_success,
        "C": acc_ok,
        "D": c["disparity_non_increase"].is_success,
    }


def _wer_pp(e, w):
    return float(np.sum(e)) / float(np.sum(w)) * 100.0


# ----------------------------------------------------------------------------
# 1. Hand-calculated toy fixture (protocol Section 13: hand-calculated fixtures)
# ----------------------------------------------------------------------------
def test_hand_calculated_point_estimates_production():
    """Two speakers per accent; every expected number below is derived by hand."""
    recs = []
    # (words, static_err, suta_err, dsg_err) per speaker; accent order = SIX (sorted)
    #   Australian  : (100,20,18,15) (100,30,27,24)  -> WER1=25.0 WER3=19.5
    #   Canadian    : (100,10,10,10) (100,10,10,10)  -> WER1=10.0 WER3=10.0
    #   England     : (200,40,36,30) (200,40,36,30)  -> WER1=20.0 WER3=15.0
    #   Irish       : (100,50,45,40) (100,30,27,24)  -> WER1=40.0 WER3=32.0
    #   South Asian : (150,45,40,36) (50,5,5,4)      -> WER1=25.0 WER3=20.0
    #   US          : (100,5,5,5)    (100,5,5,5)     -> WER1= 5.0 WER3= 5.0
    rows = {
        "Australian English": [(100, 20, 18, 15), (100, 30, 27, 24)],
        "Canadian English": [(100, 10, 10, 10), (100, 10, 10, 10)],
        "England English": [(200, 40, 36, 30), (200, 40, 36, 30)],
        "Irish English": [(100, 50, 45, 40), (100, 30, 27, 24)],
        "South Asian English": [(150, 45, 40, 36), (50, 5, 5, 4)],
        "US English": [(100, 5, 5, 5), (100, 5, 5, 5)],
    }
    for ai, (acc, spks) in enumerate(rows.items()):
        for k, (w, a, b, c) in enumerate(spks):
            recs.append({"speaker_id": f"T{ai}{k}", "stratum": acc, "wc": w, "err1": a, "err2": b, "err3": c})
    rep = run_production(recs, n_boot=50)

    # Totals: W=1500, E1=295, E2=269?  compute by hand below
    W = 100 + 100 + 100 + 100 + 200 + 200 + 100 + 100 + 150 + 50 + 100 + 100  # 1400
    E1 = (20 + 30) + (10 + 10) + (40 + 40) + (50 + 30) + (45 + 5) + (5 + 5)  # 290
    E2 = (18 + 27) + (10 + 10) + (36 + 36) + (45 + 27) + (40 + 5) + (5 + 5)  # 264
    E3 = (15 + 24) + (10 + 10) + (30 + 30) + (40 + 24) + (36 + 4) + (5 + 5)  # 233
    assert (W, E1, E2, E3) == (1400, 290, 264, 233)
    assert rep.corpus_wer_arm1_static == pytest.approx(290 / 1400 * 100, abs=1e-4)  # 20.7143
    assert rep.corpus_wer_arm2_ungated == pytest.approx(264 / 1400 * 100, abs=1e-4)  # 18.8571
    assert rep.corpus_wer_arm3_dsg == pytest.approx(233 / 1400 * 100, abs=1e-4)  # 16.6429
    assert rep.delta_static_pp == pytest.approx((233 - 290) / 1400 * 100, abs=1e-4)  # -4.0714
    assert rep.delta_ungated_pp == pytest.approx((233 - 264) / 1400 * 100, abs=1e-4)  # -2.2143
    # Word-weighted (NOT mean of speaker WERs): South Asian static = 50/200 = 25.0, not (30+10)/2 = 20
    assert rep.accent_wers_arm1["South Asian English"] == pytest.approx(25.0, abs=1e-4)
    assert rep.accent_wers_arm1["Australian English"] == pytest.approx(25.0, abs=1e-4)
    assert rep.accent_wers_arm1["Irish English"] == pytest.approx(40.0, abs=1e-4)
    assert rep.accent_wers_arm1["US English"] == pytest.approx(5.0, abs=1e-4)
    assert rep.accent_wers_arm3["Irish English"] == pytest.approx(32.0, abs=1e-4)
    # Disparity D = max-min per arm; D1 = 40-5 = 35, D3 = 32-5 = 27, Delta_D = -8
    assert rep.disparity_arm1_pp == pytest.approx(35.0, abs=1e-4)
    assert rep.disparity_arm3_pp == pytest.approx(27.0, abs=1e-4)
    assert rep.delta_disparity_pp == pytest.approx(-8.0, abs=1e-4)


# ----------------------------------------------------------------------------
# 2. Six-stratum parity: production vs audit, identical records + bootstrap stream
# ----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def panel_results():
    """Computed once; each entry holds production report and audit outputs."""
    mp = pytest.MonkeyPatch()
    results = []
    try:
        for sc in scenario_panel():
            recs = make_records(SIX, sc["n"], sc["dsg"], sc["suta"], sc["seed"])
            rep = run_production(recs)
            aud = run_audit(recs, SIX, mp)
            results.append({"sc": sc, "recs": recs, "rep": rep, "aud": aud})
    finally:
        mp.undo()
    return results


def test_panel_is_non_vacuous(panel_results):
    """Each decision event must both PASS and FAIL somewhere in the panel."""
    for ev in ("A", "B", "C", "D"):
        outcomes = {prod_events(r["rep"])[ev] for r in panel_results}
        assert outcomes == {True, False}, f"Event {ev} never varies across the panel; parity test would be vacuous."
    assert any(prod_events(r["rep"]) == {"A": True, "B": True, "C": True, "D": True} for r in panel_results)


def test_event_decisions_identical(panel_results):
    mism = []
    for r in panel_results:
        p, a = prod_events(r["rep"]), r["aud"]
        for ev in ("A", "B", "C", "D"):
            if p[ev] != a[ev]:
                mism.append((r["sc"]["name"], ev, p[ev], a[ev]))
        if all(p.values()) != a["joint"]:
            mism.append((r["sc"]["name"], "joint", all(p.values()), a["joint"]))
    assert not mism, f"Decision mismatches (scenario, event, production, audit): {mism}"


def test_multiplicity_family_and_tcrit_identical_for_six_strata(panel_results):
    for r in panel_results:
        a = r["aud"]
        assert a["M"] == 9
        n_tot = len(r["recs"])
        q = 1.0 - ALPHA / 9.0
        q_cur, df_cur, t_cur = a["t_calls"][0]
        assert q_cur == pytest.approx(q, abs=1e-15)
        assert df_cur == n_tot - 1
        assert t_cur == pytest.approx(float(stats.t.ppf(q, n_tot - 1)), abs=1e-12)


def test_ratio_ucb_numerics_identical(panel_results):
    """Audit UCB (from its own spied std and t quantile) == production adjusted UCB."""
    for r in panel_results:
        recs, rep, a = r["recs"], r["rep"], r["aud"]
        W = np.array([x["wc"] for x in recs], float)
        E1 = np.array([x["err1"] for x in recs], float)
        E2 = np.array([x["err2"] for x in recs], float)
        E3 = np.array([x["err3"] for x in recs], float)
        n = len(recs)
        t_corp = a["t_calls"][0][2]
        # Event A / B : spied std order is [A, B, C_1, C_2, ...]
        for std_idx, (E_ref, key) in enumerate(((E1, "primary_superiority_static"), (E2, "primary_superiority_ungated"))):
            delta = (E3.sum() - E_ref.sum()) / W.sum() * 100.0
            se = 100.0 * a["std_calls"][std_idx] / math.sqrt(n) / W.mean()
            ucb_audit = delta + t_corp * se
            assert ucb_audit == pytest.approx(rep.criteria[key].adjusted_ucb, abs=UCB_TOL), (r["sc"]["name"], key)
            assert delta == pytest.approx(rep.criteria[key].point_estimate, abs=1e-4)
        # Event C: per-accent (the audit stops at the first failing accent)
        for j, acc in enumerate(SIX):
            if 2 + j >= len(a["std_calls"]):
                break
            sub = [x for x in recs if x["stratum"] == acc]
            w = np.array([x["wc"] for x in sub], float)
            e1 = np.array([x["err1"] for x in sub], float)
            e3 = np.array([x["err3"] for x in sub], float)
            d_g = (e3.sum() - e1.sum()) / w.sum() * 100.0
            se_g = 100.0 * a["std_calls"][2 + j] / math.sqrt(len(sub)) / w.mean()
            t_g = a["t_calls"][1 + j][2]
            assert a["t_calls"][1 + j][1] == len(sub) - 1
            key = f"accent_safety_{acc.lower().replace(' ', '_')}"
            assert d_g + t_g * se_g == pytest.approx(rep.criteria[key].adjusted_ucb, abs=UCB_TOL), (r["sc"]["name"], key)


def test_disparity_bootstrap_ucb_identical(panel_results):
    """Identical bootstrap stream + identical statistic => identical 99.444th percentile."""
    q = 100.0 * (1.0 - ALPHA / 9.0)
    for r in panel_results:
        q_aud, v_aud = r["aud"]["pct_calls"][0]
        assert q_aud == pytest.approx(q, abs=1e-12)
        assert v_aud == pytest.approx(r["rep"].criteria["disparity_non_increase"].adjusted_ucb, abs=UCB_TOL), r["sc"]["name"]


# ----------------------------------------------------------------------------
# 3. Five-stratum: documented MISMATCHES (characterisation tests, not endorsements)
# ----------------------------------------------------------------------------
def _five_records(seed=5):
    return make_records(FIVE, 30, _uniform(FIVE, -4.0), _uniform(FIVE, -1.0), seed)


def test_production_rejects_five_accents_by_default():
    with pytest.raises(ValueError, match="Missing canonical protocol accents"):
        run_production(_five_records())


def test_KNOWN_MISMATCH_production_five_accent_override_still_uses_M9(monkeypatch):
    """With canonical_accents overridden to five strata production still applies alpha/9, the audit alpha/8."""
    recs = _five_records()
    real_ppf = stats.t.ppf
    seen: List[tuple] = []

    def spy(q, df, *a, **k):
        v = real_ppf(q, df, *a, **k)
        seen.append((round(float(q), 12), float(df)))
        return v

    with monkeypatch.context() as mp:
        mp.setattr(stats.t, "ppf", spy)
        run_production(recs, canonical_accents=frozenset(FIVE), n_boot=40)
    q9, q8 = round(1 - ALPHA / 9.0, 12), round(1 - ALPHA / 8.0, 12)
    assert any(q == q9 for q, _ in seen), "production should apply alpha/9"
    assert not any(q == q8 for q, _ in seen), "production never applies alpha/8 (M=8)"

    aud = run_audit(recs, FIVE, monkeypatch, n_boot=40)
    assert aud["M"] == 8
    assert aud["t_calls"][0][0] == pytest.approx(1 - ALPHA / 8.0, abs=1e-15)


def test_KNOWN_MISMATCH_production_power_simulator_hardcodes_six_accents_and_M9(monkeypatch):
    """The production design-stage simulator takes no accent list: always 6 accents, always M=9."""
    real_ppf = stats.t.ppf
    seen: List[tuple] = []

    def spy(q, df, *a, **k):
        v = real_ppf(q, df, *a, **k)
        seen.append((float(q), float(df)))
        return v

    spec = prod.DesignStagePowerSpec()
    with monkeypatch.context() as mp:
        mp.setattr(stats.t, "ppf", spy)
        prod.simulate_design_stage_joint_power(spec, num_simulations=1, num_speakers_per_stratum=7, seed=1, num_boot_replicates=20)
    q, df = seen[0]
    assert q == pytest.approx(1 - ALPHA / 9.0, abs=1e-15)
    assert df == 6 * 7 - 1  # six strata x 7 speakers


# ----------------------------------------------------------------------------
# 4. Multiplicity method: what is implemented vs what the governing text names
# ----------------------------------------------------------------------------
def test_implemented_multiplicity_is_plain_bonferroni_not_holm():
    """
    Behavioural proof. Craft per-hypothesis raw p-values such that Holm rejects
    all M but Bonferroni does not; production's decision uses UCB at alpha/M
    (i.e. Bonferroni), so it can never exploit Holm's step-down relaxation.
    """
    M, alpha = 9, 0.05
    # Sorted raw p-values p(j): Holm needs p(j) <= alpha/(M-j+1) for every j.
    p = [alpha / (M - j) * 0.99 for j in range(M)]  # j=0..8 -> alpha/9, alpha/8, ..., alpha/1 (x0.99)
    holm_rejects_all = all(p[j] <= alpha / (M - j) for j in range(M))
    bonf_rejects_all = all(pj <= alpha / M for pj in p)
    assert holm_rejects_all and not bonf_rejects_all  # Holm is strictly more permissive for 'reject all'
    # Production reports Bonferroni-adjusted p = min(1, M * p_raw). raw_p is rounded to 6 dp before
    # the comparison, so the exact rounding bound is M * 5e-7 = 4.5e-6.
    rep = run_production(make_records(SIX, 20, _uniform(SIX, -4.0), _uniform(SIX, -1.0), 7), n_boot=200)
    for c in rep.criteria.values():
        assert c.adjusted_p_value == pytest.approx(min(1.0, 9.0 * c.raw_p_value), abs=9 * 5e-7 + 1e-9)
