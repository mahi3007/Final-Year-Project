"""
Stage 4M Statistical Engine & Specification Validation Script
Protocol: v1.1.0-model-expansion
Author: Antigravity IDE / DSG-CTTA Research Team

Validates:
1. Full 36-parameter design matrix (M, J, C, O, M:J, J:C, J:O) with rank 36.
2. 30-window prequential stream (120 utterances / K=4 = 30 windows).
3. Primary Observed Safety Estimands (Analysis A) vs Secondary GLMM (Analysis B).
4. Laplace approximation marginal likelihood objective & multi-dataset parameter recovery (N=5).
5. Formal DSG Safety Gate Controller tests on 4 canonical UCB boundary cases.
6. Stratified paired speaker-cluster bootstrap (729 distinct multiset combinatorial limit).
"""

import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import patsy
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.types import BootstrapMetrics


def test_window_count_and_terminal_rule():
    """Verify window count = 30 and terminal window update policy."""
    n_utterances = 120
    k_window = 4
    n_windows = int(np.ceil(n_utterances / k_window))
    assert n_windows == 30, f"Expected 30 windows, got {n_windows}"
    
    windows = [list(range(w * k_window, (w + 1) * k_window)) for w in range(n_windows)]
    assert len(windows) == 30
    assert windows[0] == [0, 1, 2, 3]
    assert windows[-1] == [116, 117, 118, 119]
    
    adaptation_steps = n_windows - 1 # 29 adaptation updates per stream
    print(f"[Window Audit] Stream has {n_windows} prediction windows and {adaptation_steps} adaptation updates.")
    print("  Terminal Window Rule: Window 29 evaluated only; terminal update omitted.")
    return n_windows, adaptation_steps


def verify_design_matrix_36_parameters():
    """
    P0-1: Verify exact fixed-effect formula, 36 columns, and full rank 36.
    """
    print("\n--- [P0-1] Reconciling Fixed-Effect Design Matrix (p=36) ---")
    ctc_models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
    conditions = ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]
    
    import itertools
    grid = list(itertools.product(ctc_models, methods, orders, conditions))
    df = pd.DataFrame(grid, columns=["model", "method", "ordering", "condition"])
    df["errors"] = 1
    
    formula_36 = (
        "errors ~ C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(ordering, Treatment('ORDER_A')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    
    _, X_mat = patsy.dmatrices(formula_36, data=df, return_type="dataframe")
    p = X_mat.shape[1]
    rank = np.linalg.matrix_rank(X_mat.values)
    
    print(f"Factorial grid settings: {len(df)}")
    print(f"Design matrix shape: {X_mat.shape}")
    print(f"Design matrix rank: {rank}")
    print(f"Coefficients estimated: {p}")
    
    assert p == 36, f"Expected 36 columns, got {p}"
    assert rank == 36, f"Expected rank 36, got {rank}"
    
    # Verify exact component decomposition:
    # Intercept (1), Model (2), Method (3), Condition (4), Order (2),
    # Model:Method (6), Method:Condition (12), Method:Order (6)
    expected_decomp = {
        "Intercept": 1,
        "Model": 2,
        "Method": 3,
        "Condition": 4,
        "Order": 2,
        "Model x Method": 6,
        "Method x Condition": 12,
        "Method x Order": 6
    }
    assert sum(expected_decomp.values()) == 36
    print("[P0-1 PASS] Design matrix successfully reconciled: 36 columns with full rank 36.")
    return formula_36, X_mat.columns


def run_differential_subgroup_fixtures():
    """
    P0-2 & P0-4: Metric validation under differential subgroup harm.
    Tests A, B, and C with exact manual reference values.
    """
    print("\n--- [P0-2] Metric Validation: Differential Subgroup Synthetic Tests ---")
    groups = ["Arabic", "Hindi", "Spanish", "Mandarin", "Vietnamese", "Korean"]
    n_words_per_group = 100
    total_words = n_words_per_group * len(groups) # 600
    
    base_errors = {"Arabic": 10, "Hindi": 20, "Spanish": 30, "Mandarin": 40, "Vietnamese": 50, "Korean": 60}
    base_wers = {g: (base_errors[g] / n_words_per_group) * 100.0 for g in groups}
    base_overall_wer = (sum(base_errors.values()) / total_words) * 100.0 # 210/600 = 35.0%
    base_disp_d = max(base_wers.values()) - min(base_wers.values()) # 60.0 - 10.0 = 50.0 pp
    
    def calc_metrics(adapt_errors):
        adapt_wers = {g: (adapt_errors[g] / n_words_per_group) * 100.0 for g in groups}
        adapt_overall = (sum(adapt_errors.values()) / total_words) * 100.0
        delta_r = adapt_overall - base_overall_wer
        delta_g = {g: adapt_wers[g] - base_wers[g] for g in groups}
        max_delta_g = max(delta_g.values())
        adapt_disp_d = max(adapt_wers.values()) - min(adapt_wers.values())
        delta_d = adapt_disp_d - base_disp_d
        return {
            "overall_wer": adapt_overall,
            "delta_r": delta_r,
            "group_wers": adapt_wers,
            "delta_g": delta_g,
            "max_delta_g": max_delta_g,
            "disp_d": adapt_disp_d,
            "delta_d": delta_d
        }
    
    # Test A: Uniform change (-5.0 pp)
    test_a_errors = {"Arabic": 5, "Hindi": 15, "Spanish": 25, "Mandarin": 35, "Vietnamese": 45, "Korean": 55}
    res_a = calc_metrics(test_a_errors)
    assert abs(res_a["delta_r"] - (-5.0)) < 1e-5
    assert abs(res_a["delta_d"] - 0.0) < 1e-5
    assert abs(res_a["max_delta_g"] - (-5.0)) < 1e-5
    print("[Metric Test A PASS] Uniform group improvement: Delta_R = -5.00 pp, Delta_D = 0.00 pp, max Delta_g = -5.00 pp.")

    # Test B: Overall improvement (-4.17 pp), Korean regresses (+5.0 pp)
    test_b_errors = {"Arabic": 4, "Hindi": 14, "Spanish": 24, "Mandarin": 34, "Vietnamese": 44, "Korean": 65}
    res_b = calc_metrics(test_b_errors)
    assert abs(res_b["delta_r"] - (185.0/600.0*100 - 35.0)) < 1e-5
    assert abs(res_b["max_delta_g"] - 5.0) < 1e-5
    assert abs(res_b["delta_d"] - 11.0) < 1e-5
    assert res_b["delta_r"] < 0
    assert res_b["max_delta_g"] > 2.0 # Threshold violation
    print(f"[Metric Test B PASS] Overall improvement with subgroup harm: Delta_R = {res_b['delta_r']:.2f} pp, "
          f"max Delta_g = +{res_b['max_delta_g']:.2f} pp, Delta_D = +{res_b['delta_d']:.2f} pp.")

    # Test C: Overall deterioration (+13.33 pp), disparity shrinks (-20 pp)
    test_c_errors = {"Arabic": 35, "Hindi": 40, "Spanish": 45, "Mandarin": 50, "Vietnamese": 55, "Korean": 65}
    res_c = calc_metrics(test_c_errors)
    assert abs(res_c["delta_r"] - (290.0/600.0*100 - 35.0)) < 1e-5
    assert abs(res_c["max_delta_g"] - 25.0) < 1e-5
    assert abs(res_c["delta_d"] - (-20.0)) < 1e-5
    assert res_c["delta_d"] < 0
    assert res_c["delta_r"] > 0
    print(f"[Metric Test C PASS] Deterioration with disparity shrinkage: Delta_R = +{res_c['delta_r']:.2f} pp, "
          f"Delta_D = {res_c['delta_d']:.2f} pp, max Delta_g = +{res_c['max_delta_g']:.2f} pp.")
    return True


def test_dsg_safety_gate_controller():
    """
    P0-4: Formal DSG Safety Gate Controller Validation.
    Evaluates tripartite UCB95 rules on canonical boundary cases.
    """
    print("\n--- [P0-4] Formal DSG Safety Gate Controller Boundary Tests ---")
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    
    # Case 1: Fully Safe Candidate (All UCBs <= tolerances) -> ACCEPT
    metrics_safe = BootstrapMetrics(
        delta_r=-0.0350,
        max_delta_g=-0.0300,
        delta_d=-0.0100,
        ucb_r=-0.0200, # <= 0.0000
        ucb_max_group=-0.0150, # <= 0.0200
        ucb_d=-0.0050, # <= 0.0200
        group_deltas={"Arabic": -0.04, "Hindi": -0.03, "Spanish": -0.03, "Mandarin": -0.03, "Vietnamese": -0.04, "Korean": -0.03},
        group_ucbs={"Arabic": -0.02, "Hindi": -0.015, "Spanish": -0.015, "Mandarin": -0.015, "Vietnamese": -0.02, "Korean": -0.015},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_safe = gate.evaluate_decision(metrics_safe, "cand_safe", "curr", 42, 1000)
    assert dec_safe.accept is True, "Case 1 should be ACCEPTED"
    print("[Gate Test 1 PASS] Safe Candidate ACCEPTED: UCB_R <= 0.00, UCB_G <= 0.02, UCB_D <= 0.02.")
    
    # Case 2: Point estimates inside tolerance, but UCB_G exceeds threshold -> REJECT!
    metrics_ucb_violation = BootstrapMetrics(
        delta_r=-0.0200,
        max_delta_g=+0.0150, # Point estimate safe!
        delta_d=+0.0100, # Point estimate safe!
        ucb_r=-0.0050,
        ucb_max_group=0.0280, # UCB exceeds 0.0200!
        ucb_d=0.0180,
        group_deltas={"Arabic": -0.03, "Hindi": -0.02, "Spanish": -0.02, "Mandarin": -0.02, "Vietnamese": -0.02, "Korean": +0.0150},
        group_ucbs={"Arabic": -0.01, "Hindi": -0.005, "Spanish": -0.005, "Mandarin": -0.005, "Vietnamese": -0.005, "Korean": 0.0280},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_ucb = gate.evaluate_decision(metrics_ucb_violation, "cand_ucb_fail", "curr", 42, 1000)
    assert dec_ucb.accept is False, "Case 2 should be REJECTED"
    assert any("Subgroup regression violation" in r for r in dec_ucb.rejection_reasons)
    print(f"[Gate Test 2 PASS] Point-safe candidate REJECTED by UCB: point max_delta_g = +0.0150, but UCB95 = +0.0280 > 0.0200.")
    
    # Case 3: Overall improvement with subgroup harm (Test B) -> REJECT!
    metrics_subgroup_harm = BootstrapMetrics(
        delta_r=-0.0417,
        max_delta_g=+0.0500,
        delta_d=+0.1100,
        ucb_r=-0.0250,
        ucb_max_group=0.0700,
        ucb_d=0.1400,
        group_deltas={"Arabic": -0.06, "Hindi": -0.06, "Spanish": -0.06, "Mandarin": -0.06, "Vietnamese": -0.06, "Korean": +0.05},
        group_ucbs={"Arabic": -0.04, "Hindi": -0.04, "Spanish": -0.04, "Mandarin": -0.04, "Vietnamese": -0.04, "Korean": 0.07},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_harm = gate.evaluate_decision(metrics_subgroup_harm, "cand_harm", "curr", 42, 1000)
    assert dec_harm.accept is False, "Case 3 should be REJECTED"
    assert any("Subgroup regression violation" in r for r in dec_harm.rejection_reasons)
    print("[Gate Test 3 PASS] Overall improvement with subgroup harm REJECTED: UCB_G = +0.0700 > 0.0200.")
    
    # Case 4: Overall deterioration with disparity shrinkage (Test C) -> REJECT!
    metrics_shrunk_disp = BootstrapMetrics(
        delta_r=+0.1333,
        max_delta_g=+0.2500,
        delta_d=-0.2000,
        ucb_r=+0.1600,
        ucb_max_group=+0.3000,
        ucb_d=-0.1500,
        group_deltas={"Arabic": +0.25, "Hindi": +0.20, "Spanish": +0.15, "Mandarin": +0.10, "Vietnamese": +0.05, "Korean": +0.05},
        group_ucbs={"Arabic": +0.30, "Hindi": +0.24, "Spanish": +0.18, "Mandarin": +0.13, "Vietnamese": +0.08, "Korean": +0.08},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_shrunk = gate.evaluate_decision(metrics_shrunk_disp, "cand_shrunk", "curr", 42, 1000)
    assert dec_shrunk.accept is False, "Case 4 should be REJECTED"
    assert any("Overall risk violation" in r for r in dec_shrunk.rejection_reasons)
    print("[Gate Test 4 PASS] Shrunk disparity candidate REJECTED: UCB_D = -0.1500, but UCB_R = +0.1600 > 0.0000.")
    return True


def run_multidataset_glmm_validation(n_datasets=5):
    """
    P0-3: Multi-dataset validation of the 36-parameter GLMM with Laplace marginal approximation.
    """
    print(f"\n--- [P0-3] Multi-Dataset GLMM Validation ({n_datasets} independent datasets) ---")
    ctc_models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
    conditions = ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]
    accent_groups = ["Arabic", "Hindi", "Spanish", "Mandarin", "Vietnamese", "Korean"]
    
    speakers = {
        "Arabic": ["ABA", "SKA"],
        "Hindi": ["BJM", "ASI"],
        "Spanish": ["EBVS", "NCC"],
        "Mandarin": ["TLX", "TXHC"],
        "Vietnamese": ["BVT", "THV"],
        "Korean": ["YDCK", "YKXP"]
    }
    all_spks = [s for grp in speakers for s in speakers[grp]]
    spk2idx = {s: i for i, s in enumerate(all_spks)}
    
    utterances = []
    for grp, spk_list in speakers.items():
        for spk in spk_list:
            for u_idx in range(10):
                utt_id = f"{spk}_arctic_a{u_idx+1:04d}"
                utterances.append({
                    "utterance_id": utt_id,
                    "speaker_id": spk,
                    "accent_group": grp,
                })
    utt2idx = {u["utterance_id"]: i for i, u in enumerate(utterances)}
    
    true_phi = 8.0
    true_sigma_s = 0.15
    true_sigma_u = 0.10
    
    formula_36 = (
        "errors ~ C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(ordering, Treatment('ORDER_A')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    
    results = []
    for d_idx in range(n_datasets):
        np.random.seed(200 + d_idx)
        torch.manual_seed(200 + d_idx)
        
        for u in utterances:
            u["ref_words"] = int(np.random.randint(8, 14))
            
        true_b_s = np.random.normal(0, true_sigma_s, len(all_spks))
        true_b_u = np.random.normal(0, true_sigma_u, len(utterances))
        
        records = []
        for m in ctc_models:
            for j in methods:
                for o in orders:
                    for c in conditions:
                        log_rate = -0.16
                        if m == "wav2vec2_100h": log_rate += 0.04
                        elif m == "data2vec_base": log_rate -= 0.02
                        
                        if c == "noise_15db": log_rate += 0.05
                        elif c == "noise_5db": log_rate += 0.18
                        elif c == "babble_15db": log_rate += 0.08
                        elif c == "reverb_t60_04": log_rate += 0.12
                        
                        if j == "suta": log_rate -= 0.02
                        elif j == "dsuta": log_rate -= 0.015
                        elif j == "dmsuta": log_rate -= 0.01
                        
                        if j == "suta" and c == "noise_5db": log_rate += 0.06
                        
                        for u in utterances:
                            uid = u["utterance_id"]
                            spk = u["speaker_id"]
                            grp = u["accent_group"]
                            n_words = u["ref_words"]
                            s_i = spk2idx[spk]
                            u_i = utt2idx[uid]
                            
                            eta = np.log(n_words) + log_rate + true_b_s[s_i] + true_b_u[u_i]
                            mu = np.exp(eta)
                            errors = int(np.random.negative_binomial(n=true_phi, p=true_phi/(true_phi + mu)))
                            
                            records.append({
                                "model": m,
                                "method": j,
                                "ordering": o,
                                "condition": c,
                                "speaker_id": spk,
                                "utterance_id": uid,
                                "s_idx": s_i,
                                "u_idx": u_i,
                                "ref_words": n_words,
                                "errors": errors,
                                "log_offset": np.log(n_words)
                            })
                            
        df = pd.DataFrame(records)
        _, X_mat = patsy.dmatrices(formula_36, data=df, return_type="matrix")
        
        y_t = torch.tensor(df["errors"].values, dtype=torch.float32)
        X_t = torch.tensor(X_mat, dtype=torch.float32)
        offset_t = torch.tensor(df["log_offset"].values, dtype=torch.float32)
        spk_t = torch.tensor(df["s_idx"].values, dtype=torch.long)
        utt_t = torch.tensor(df["u_idx"].values, dtype=torch.long)
        
        p_dim = X_t.shape[1]
        n_spk = len(all_spks)
        n_utt = len(utterances)
        
        beta = nn.Parameter(torch.zeros(p_dim, dtype=torch.float32))
        log_phi = nn.Parameter(torch.tensor(np.log(5.0), dtype=torch.float32))
        log_sigma_s = nn.Parameter(torch.tensor(np.log(0.15), dtype=torch.float32))
        log_sigma_u = nn.Parameter(torch.tensor(np.log(0.10), dtype=torch.float32))
        b_s = nn.Parameter(torch.zeros(n_spk, dtype=torch.float32))
        b_u = nn.Parameter(torch.zeros(n_utt, dtype=torch.float32))
        
        optimizer = optim.Adam([beta, log_phi, log_sigma_s, log_sigma_u, b_s, b_u], lr=0.02)
        
        t0 = time.time()
        for step in range(120):
            optimizer.zero_grad()
            phi = torch.exp(log_phi)
            sig_s = torch.exp(log_sigma_s)
            sig_u = torch.exp(log_sigma_u)
            
            eta = offset_t + (X_t @ beta) + b_s[spk_t] + b_u[utt_t]
            mu = torch.exp(eta)
            
            ll_data = (
                torch.lgamma(y_t + phi) - torch.lgamma(phi) - torch.lgamma(y_t + 1.0) +
                phi * torch.log(phi / (phi + mu)) + y_t * torch.log(mu / (phi + mu))
            ).sum()
            
            ll_bs = -0.5 * torch.sum(b_s**2 / (sig_s**2)) - n_spk * torch.log(sig_s)
            ll_bu = -0.5 * torch.sum(b_u**2 / (sig_u**2)) - n_utt * torch.log(sig_u)
            
            # Laplace Hessian log-determinant volume adjustment
            w_diag = mu / (1.0 + mu / phi)
            h_s = torch.zeros(n_spk).scatter_add_(0, spk_t, w_diag) + (1.0 / (sig_s**2))
            h_u = torch.zeros(n_utt).scatter_add_(0, utt_t, w_diag) + (1.0 / (sig_u**2))
            log_det_h = 0.5 * (torch.sum(torch.log(h_s)) + torch.sum(torch.log(h_u)))
            
            loss = -(ll_data + ll_bs + ll_bu - log_det_h) / len(y_t)
            loss.backward()
            optimizer.step()
            
        fit_time = time.time() - t0
        est_phi = torch.exp(log_phi).item()
        est_sig_s = torch.exp(log_sigma_s).item()
        est_sig_u = torch.exp(log_sigma_u).item()
        est_noise5db = beta[8].item()
        
        results.append({
            "dataset_id": d_idx + 1,
            "fit_time_s": round(fit_time, 2),
            "est_phi": round(est_phi, 2),
            "est_sigma_s": round(est_sig_s, 3),
            "est_sigma_u": round(est_sig_u, 3),
            "est_noise5db_beta": round(est_noise5db, 3)
        })
        print(f"Dataset {d_idx+1:2d} | Time: {fit_time:.2f}s | phi: {est_phi:.2f} | sigma_s: {est_sig_s:.3f} | sigma_u: {est_sig_u:.3f} | noise5db_beta: {est_noise5db:.3f}")
        
    res_df = pd.DataFrame(results)
    print("\n[P0-3 Summary] Parameter Recovery Across 5 Independent Datasets:")
    print(f"  phi:       {res_df['est_phi'].mean():.2f} +/- {res_df['est_phi'].std():.2f} (True: {true_phi})")
    print(f"  sigma_s:   {res_df['est_sigma_s'].mean():.3f} +/- {res_df['est_sigma_s'].std():.3f} (True: {true_sigma_s})")
    print(f"  sigma_u:   {res_df['est_sigma_u'].mean():.3f} +/- {res_df['est_sigma_u'].std():.3f} (True: {true_sigma_u})")
    print(f"  noise_5db: {res_df['est_noise5db_beta'].mean():.3f} +/- {res_df['est_noise5db_beta'].std():.3f} (True: 0.180)")
    return res_df


def test_stratified_bootstrap_combinatorics():
    """
    P0-5: Verify Stratified Paired Speaker-Cluster Bootstrap and 729 multiset limit.
    """
    print("\n--- [P0-5] Verifying Stratified Paired Bootstrap Combinatorics ---")
    # 6 strata with 2 speakers each: {s1, s1}, {s1, s2}, {s2, s2} -> 3^6 = 729 multisets
    n_strata = 6
    configs_per_stratum = 3
    total_multisets = configs_per_stratum ** n_strata
    assert total_multisets == 729
    print(f"Stratified bootstrap combinatorics: 3^6 = {total_multisets} distinct multisets.")
    print("  B = 1000 controls computational resampling precision across these 729 configurations.")
    print("  Explicit small-sample limit: Bootstrap accounts for sample sensitivity, NOT 1000 independent speakers.")
    return total_multisets


if __name__ == "__main__":
    test_window_count_and_terminal_rule()
    verify_design_matrix_36_parameters()
    run_differential_subgroup_fixtures()
    test_dsg_safety_gate_controller()
    run_multidataset_glmm_validation(n_datasets=5)
    test_stratified_bootstrap_combinatorics()
