import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import patsy
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.types import BootstrapMetrics

def run_multidataset_glmm_validation(n_datasets=5):
    """
    Validate primary GLMM across multiple independent synthetic datasets (N=5).
    Evaluates parameter recovery for fixed effects, variance components, and dispersion.
    """
    print(f"--- Running Multi-Dataset GLMM Validation ({n_datasets} independent datasets) ---")
    
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
    
    # 10 utterances per speaker = 120 utterances
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
    
    # True values
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
        np.random.seed(100 + d_idx)
        torch.manual_seed(100 + d_idx)
        
        # Word counts
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
        
        # GLMM Model with exact 36 fixed effects and Laplace penalty
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
            
            # Laplace / Random effect log-prior
            ll_bs = -0.5 * torch.sum(b_s**2 / (sig_s**2)) - n_spk * torch.log(sig_s)
            ll_bu = -0.5 * torch.sum(b_u**2 / (sig_u**2)) - n_utt * torch.log(sig_u)
            
            # Approximate Laplace Hessian log-determinant adjustment
            # W_k approx mu_k / (1 + mu_k / phi)
            w_diag = mu / (1.0 + mu / phi)
            # sum over speaker clusters and utterance clusters
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
        est_noise5db = beta[8].item() # C(condition)[T.noise_5db]
        
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
    print("\nSummary Statistics Across 5 Datasets:")
    print(f"Mean phi: {res_df['est_phi'].mean():.2f} (True: {true_phi})")
    print(f"Mean sigma_s: {res_df['est_sigma_s'].mean():.3f} (True: {true_sigma_s})")
    print(f"Mean sigma_u: {res_df['est_sigma_u'].mean():.3f} (True: {true_sigma_u})")
    print(f"Mean noise5db_beta: {res_df['est_noise5db_beta'].mean():.3f} (True: 0.180)")
    return res_df


def test_dsg_safety_gate_controller():
    """
    P0-4: Test DisparitySafetyGate on 4 canonical boundary cases:
    1. Safe Candidate (ACCEPT)
    2. Point-Safe but UCB Exceeded (REJECT)
    3. Overall Improvement with Subgroup Harm (REJECT)
    4. Overall Deterioration with Shrunk Disparity (REJECT)
    """
    print("\n--- [P0-4] Formal DSG Safety Gate Controller Boundary Tests ---")
    gate = DisparitySafetyGate(epsilon_r=0.0000, epsilon_g=0.0200, epsilon_d=0.0200)
    
    # Case 1: Safe Candidate (All UCBs <= tolerances)
    metrics_safe = BootstrapMetrics(
        delta_r=-0.0350,
        max_delta_g=-0.0300,
        delta_d=-0.0100,
        ucb_r=-0.0200, # <= 0.0000 -> PASS
        ucb_max_group=-0.0150, # <= 0.0200 -> PASS
        ucb_d=-0.0050, # <= 0.0200 -> PASS
        group_deltas={"Arabic": -0.04, "Hindi": -0.03, "Spanish": -0.03, "Mandarin": -0.03, "Vietnamese": -0.04, "Korean": -0.03},
        group_ucbs={"Arabic": -0.02, "Hindi": -0.015, "Spanish": -0.015, "Mandarin": -0.015, "Vietnamese": -0.02, "Korean": -0.015},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_safe = gate.evaluate_decision(metrics_safe, "cand_safe", "curr", 42, 1000)
    assert dec_safe.accept is True, "Case 1 should be ACCEPTED"
    print("[Gate Test 1 PASS] Safe Candidate accepted: UCB_R <= 0, UCB_G <= 0.02, UCB_D <= 0.02.")
    
    # Case 2: Point estimates inside tolerance, but UCB_G exceeds 0.02
    metrics_ucb_violation = BootstrapMetrics(
        delta_r=-0.0200,
        max_delta_g=+0.0150, # Point estimate <= 0.0200!
        delta_d=+0.0100, # Point estimate <= 0.0200!
        ucb_r=-0.0050, # <= 0.0000 -> PASS
        ucb_max_group=0.0280, # > 0.0200 -> FAIL!
        ucb_d=0.0180, # <= 0.0200 -> PASS
        group_deltas={"Arabic": -0.03, "Hindi": -0.02, "Spanish": -0.02, "Mandarin": -0.02, "Vietnamese": -0.02, "Korean": +0.0150},
        group_ucbs={"Arabic": -0.01, "Hindi": -0.005, "Spanish": -0.005, "Mandarin": -0.005, "Vietnamese": -0.005, "Korean": 0.0280},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_ucb = gate.evaluate_decision(metrics_ucb_violation, "cand_ucb_fail", "curr", 42, 1000)
    assert dec_ucb.accept is False, "Case 2 should be REJECTED (point estimate safe, but UCB exceeded)"
    assert any("Subgroup regression violation" in r for r in dec_ucb.rejection_reasons)
    print(f"[Gate Test 2 PASS] Point-safe candidate REJECTED: point max_delta_g = +0.0150, but UCB95 = +0.0280 > 0.0200.")
    
    # Case 3: Overall improvement with subgroup harm (Test B)
    metrics_subgroup_harm = BootstrapMetrics(
        delta_r=-0.0417, # Overall improved
        max_delta_g=+0.0500, # Group harmed
        delta_d=+0.1100, # Disparity widened
        ucb_r=-0.0250,
        ucb_max_group=0.0700, # > 0.0200 -> FAIL!
        ucb_d=0.1400, # > 0.0200 -> FAIL!
        group_deltas={"Arabic": -0.06, "Hindi": -0.06, "Spanish": -0.06, "Mandarin": -0.06, "Vietnamese": -0.06, "Korean": +0.05},
        group_ucbs={"Arabic": -0.04, "Hindi": -0.04, "Spanish": -0.04, "Mandarin": -0.04, "Vietnamese": -0.04, "Korean": 0.07},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_harm = gate.evaluate_decision(metrics_subgroup_harm, "cand_harm", "curr", 42, 1000)
    assert dec_harm.accept is False, "Case 3 should be REJECTED (subgroup harm)"
    assert any("Subgroup regression violation" in r for r in dec_harm.rejection_reasons)
    assert any("Disparity growth violation" in r for r in dec_harm.rejection_reasons)
    print("[Gate Test 3 PASS] Overall improvement with subgroup harm REJECTED: UCB_G = +0.0700, UCB_D = +0.1400.")
    
    # Case 4: Overall deterioration with disparity shrinkage (Test C)
    metrics_shrunk_disp = BootstrapMetrics(
        delta_r=+0.1333, # Deterioration
        max_delta_g=+0.2500,
        delta_d=-0.2000, # Disparity shrank!
        ucb_r=+0.1600, # > 0.0000 -> FAIL!
        ucb_max_group=+0.3000, # > 0.0200 -> FAIL!
        ucb_d=-0.1500, # <= 0.0200 -> PASS
        group_deltas={"Arabic": +0.25, "Hindi": +0.20, "Spanish": +0.15, "Mandarin": +0.10, "Vietnamese": +0.05, "Korean": +0.05},
        group_ucbs={"Arabic": +0.30, "Hindi": +0.24, "Spanish": +0.18, "Mandarin": +0.13, "Vietnamese": +0.08, "Korean": +0.08},
        replicates_computed=1000,
        omitted_groups_count=0
    )
    dec_shrunk = gate.evaluate_decision(metrics_shrunk_disp, "cand_shrunk", "curr", 42, 1000)
    assert dec_shrunk.accept is False, "Case 4 should be REJECTED (overall deterioration despite shrunk disparity)"
    assert any("Overall risk violation" in r for r in dec_shrunk.rejection_reasons)
    print("[Gate Test 4 PASS] Shrunk disparity candidate REJECTED: UCB_D = -0.1500, but UCB_R = +0.1600 > 0.0000.")
    return True

if __name__ == "__main__":
    test_dsg_safety_gate_controller()
    run_multidataset_glmm_validation(n_datasets=5)
