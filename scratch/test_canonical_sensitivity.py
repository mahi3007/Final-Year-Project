import numpy as np
import pandas as pd
import patsy
import torch
import time

def compare_canonical_vs_duplicated():
    print("\n--- 2. Sensitivity Analysis: 21,600 Rows (Duplicated No-Adapt) vs 18,000 Rows (Canonical Option A) ---")
    np.random.seed(42)
    torch.manual_seed(42)
    
    # 12 speakers, 10 utterances each = 120 utterances
    speakers = [f"spk_{i:02d}" for i in range(12)]
    utterances = [f"utt_{i:03d}" for i in range(120)]
    spk_of_utt = [i // 10 for i in range(120)]
    
    models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    conditions = ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]
    orderings = ["ORDER_A", "ORDER_B", "ORDER_C"]
    
    true_phi = 8.0
    true_sigma_s = 0.15
    true_sigma_u = 0.10
    
    b_s = np.random.normal(0, true_sigma_s, 12)
    b_u = np.random.normal(0, true_sigma_u, 120)
    
    # Generate canonical No-Adapt evaluations once per (m, c, i)
    # Total unique No-Adapt events: 3 models * 5 conditions * 120 utterances = 1,800 events
    no_adapt_cache = {}
    for m in models:
        for c in conditions:
            log_rate = -0.16
            if m == "wav2vec2_100h": log_rate += 0.04
            elif m == "data2vec_base": log_rate -= 0.02
            if c == "noise_15db": log_rate += 0.05
            elif c == "noise_5db": log_rate += 0.18
            elif c == "babble_15db": log_rate += 0.08
            elif c == "reverb_t60_04": log_rate += 0.12
            
            for u_idx, u in enumerate(utterances):
                s_idx = spk_of_utt[u_idx]
                n_words = 10 # fixed reference words
                eta = np.log(n_words) + log_rate + b_s[s_idx] + b_u[u_idx]
                mu = np.exp(eta)
                err = int(np.random.negative_binomial(n=true_phi, p=true_phi/(true_phi + mu)))
                no_adapt_cache[(m, c, u)] = err
                
    # Now generate the two datasets:
    # Dataset 1: Duplicated 21,600 rows (repeats identical No-Adapt across ORDER_A, B, C)
    records_21600 = []
    # Dataset 2: Canonical 18,000 rows (No-Adapt included once as canonical reference)
    records_18000 = []
    
    # First, add the 1,800 canonical No-Adapt rows
    for m in models:
        for c in conditions:
            for u_idx, u in enumerate(utterances):
                s_idx = spk_of_utt[u_idx]
                err = no_adapt_cache[(m, c, u)]
                records_18000.append({
                    "model": m, "method": "no_adapt", "condition": c, "ordering": "ORDER_A", # reference order
                    "utterance_id": u, "speaker_idx": s_idx, "utterance_idx": u_idx,
                    "errors": err, "ref_words": 10
                })
                # In 21,600 design, duplicate across ORDER_A, ORDER_B, ORDER_C
                for o in orderings:
                    records_21600.append({
                        "model": m, "method": "no_adapt", "condition": c, "ordering": o,
                        "utterance_id": u, "speaker_idx": s_idx, "utterance_idx": u_idx,
                        "errors": err, "ref_words": 10
                    })
                    
    # Next, add the 16,200 active adaptation rows (3 methods * 3 orders * 5 conditions * 3 models * 120 utts)
    for m in models:
        for j in ["suta", "dsuta", "dmsuta"]:
            for o in orderings:
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
                    
                    for u_idx, u in enumerate(utterances):
                        s_idx = spk_of_utt[u_idx]
                        n_words = 10
                        eta = np.log(n_words) + log_rate + b_s[s_idx] + b_u[u_idx]
                        mu = np.exp(eta)
                        err = int(np.random.negative_binomial(n=true_phi, p=true_phi/(true_phi + mu)))
                        rec = {
                            "model": m, "method": j, "condition": c, "ordering": o,
                            "utterance_id": u, "speaker_idx": s_idx, "utterance_idx": u_idx,
                            "errors": err, "ref_words": 10
                        }
                        records_21600.append(rec)
                        records_18000.append(rec)
                        
    df_21600 = pd.DataFrame(records_21600)
    df_18000 = pd.DataFrame(records_18000)
    print(f"Dataset 1 (Duplicated): {len(df_21600)} rows")
    print(f"Dataset 2 (Canonical):  {len(df_18000)} rows")
    
    # Fit Laplace GLMM on both with observed curvature
    def fit_glmm(df, name):
        formula = (
            "C(model, Treatment('wav2vec2_base')) + "
            "C(method, Treatment('no_adapt')) + "
            "C(condition, Treatment('clean')) + "
            "C(ordering, Treatment('ORDER_A')) + "
            "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
            "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
            "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
        )
        dmat = patsy.dmatrix(formula, data=df, return_type="dataframe")
        X = torch.tensor(dmat.values, dtype=torch.float32)
        y = torch.tensor(df["errors"].values, dtype=torch.float32)
        offset = torch.tensor(np.log(df["ref_words"].values), dtype=torch.float32)
        spk_idx = torch.tensor(df["speaker_idx"].values, dtype=torch.long)
        utt_idx = torch.tensor(df["utterance_idx"].values, dtype=torch.long)
        
        n_spk = 12
        n_utt = 120
        n_obs = len(y)
        
        beta = torch.zeros(X.shape[1], requires_grad=True)
        log_phi = torch.tensor(np.log(8.0), requires_grad=True)
        log_sigma_s = torch.tensor(np.log(0.15), requires_grad=True)
        log_sigma_u = torch.tensor(np.log(0.10), requires_grad=True)
        
        b_s = torch.zeros(n_spk, requires_grad=True)
        b_u = torch.zeros(n_utt, requires_grad=True)
        
        optimizer = torch.optim.Adam([beta, log_phi, log_sigma_s, log_sigma_u, b_s, b_u], lr=0.015)
        
        for step in range(350):
            optimizer.zero_grad()
            phi = torch.exp(log_phi)
            sig_s = torch.exp(log_sigma_s)
            sig_u = torch.exp(log_sigma_u)
            
            eta = offset + (X @ beta) + b_s[spk_idx] + b_u[utt_idx]
            mu = torch.exp(eta)
            
            ll_data = (
                torch.lgamma(y + phi) - torch.lgamma(phi) - torch.lgamma(y + 1.0) +
                phi * torch.log(phi / (phi + mu)) + y * torch.log(mu / (phi + mu))
            ).sum()
            
            # Prior log-density with exact quadratic penalty
            ll_bs = -0.5 * torch.sum(b_s**2 / (sig_s**2)) - n_spk * torch.log(sig_s)
            ll_bu = -0.5 * torch.sum(b_u**2 / (sig_u**2)) - n_utt * torch.log(sig_u)
            
            # EXACT OBSERVED NEGATIVE CURVATURE
            # w_obs = mu * (1 + y/phi) / (1 + mu/phi)^2
            w_obs = (mu * (1.0 + y / phi)) / ((1.0 + mu / phi)**2)
            
            h_s = torch.zeros(n_spk).scatter_add_(0, spk_idx, w_obs) + (1.0 / (sig_s**2))
            h_u = torch.zeros(n_utt).scatter_add_(0, utt_idx, w_obs) + (1.0 / (sig_u**2))
            
            # Laplace Hessian log-determinant (prior constant cancels with Gaussian integral (2pi)^(K/2))
            log_det_h = 0.5 * (torch.sum(torch.log(h_s)) + torch.sum(torch.log(h_u)))
            
            loss = -(ll_data + ll_bs + ll_bu - log_det_h) / n_obs
            loss.backward()
            optimizer.step()
            
        print(f"[{name}] Results:")
        print(f"  phi:     {torch.exp(log_phi).item():.3f} (True: 8.000)")
        print(f"  sigma_s: {torch.exp(log_sigma_s).item():.3f} (True: 0.150)")
        print(f"  sigma_u: {torch.exp(log_sigma_u).item():.3f} (True: 0.100)")
        print(f"  beta[noise_5db]: {beta[8].item():.4f} (True: 0.1800)")
        return {
            "phi": torch.exp(log_phi).item(),
            "sigma_s": torch.exp(log_sigma_s).item(),
            "sigma_u": torch.exp(log_sigma_u).item(),
            "beta_noise_5db": beta[8].item()
        }
        
    res_21600 = fit_glmm(df_21600, "21,600 Rows (Duplicated)")
    res_18000 = fit_glmm(df_18000, "18,000 Rows (Canonical Option A)")
    
    print("\nComparison Summary:")
    print(f"  phi diff:            {abs(res_21600['phi'] - res_18000['phi']):.4f}")
    print(f"  sigma_s diff:        {abs(res_21600['sigma_s'] - res_18000['sigma_s']):.4f}")
    print(f"  sigma_u diff:        {abs(res_21600['sigma_u'] - res_18000['sigma_u']):.4f}")
    print(f"  beta_noise_5db diff: {abs(res_21600['beta_noise_5db'] - res_18000['beta_noise_5db']):.4f}")

if __name__ == "__main__":
    compare_canonical_vs_duplicated()
