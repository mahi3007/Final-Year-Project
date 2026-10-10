import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import time

def test_nb_glmm_fit():
    # 1. Simulate data with known variance components:
    # sigma_s = 0.15, sigma_u = 0.10, dispersion phi = 8.0, base_rate = -0.16
    np.random.seed(42)
    torch.manual_seed(42)
    
    n_spk = 12
    n_utt = 120
    # 180 settings x 120 utterances = 21,600
    n_obs = 21600
    
    # Generate simple test data
    spk_ids = np.repeat(np.arange(n_spk), n_obs // n_spk)
    utt_ids = np.tile(np.arange(n_utt), n_obs // n_utt)
    
    true_sigma_s = 0.15
    true_sigma_u = 0.10
    true_b_s = np.random.normal(0, true_sigma_s, n_spk)
    true_b_u = np.random.normal(0, true_sigma_u, n_utt)
    
    ref_words = np.random.randint(8, 14, n_obs)
    x1 = np.random.binomial(1, 0.5, n_obs) # e.g. noise
    x2 = np.random.binomial(1, 0.5, n_obs) # e.g. adapt
    
    beta_0 = -0.16
    beta_1 = 0.15
    beta_2 = -0.05
    
    linpred = np.log(ref_words) + beta_0 + beta_1 * x1 + beta_2 * x2 + true_b_s[spk_ids] + true_b_u[utt_ids]
    mu = np.exp(linpred)
    phi = 8.0
    # NB draw: r=phi, p=phi/(phi+mu)
    y = np.random.negative_binomial(phi, phi / (phi + mu))
    
    print(f"Data generated: N={n_obs}, mean(y)={np.mean(y):.2f}, var(y)={np.var(y):.2f}")
    
    # Convert to PyTorch tensors
    y_t = torch.tensor(y, dtype=torch.float32)
    offset_t = torch.tensor(np.log(ref_words), dtype=torch.float32)
    x_t = torch.tensor(np.column_stack([np.ones(n_obs), x1, x2]), dtype=torch.float32)
    spk_idx = torch.tensor(spk_ids, dtype=torch.long)
    utt_idx = torch.tensor(utt_ids, dtype=torch.long)
    
    # Model parameters: beta (3), log_phi (1), log_sigma_s (1), log_sigma_u (1), b_s (12), b_u (120)
    beta = nn.Parameter(torch.tensor([-0.1, 0.1, 0.0], dtype=torch.float32))
    log_phi = nn.Parameter(torch.tensor([np.log(5.0)], dtype=torch.float32))
    log_sigma_s = nn.Parameter(torch.tensor([np.log(0.2)], dtype=torch.float32))
    log_sigma_u = nn.Parameter(torch.tensor([np.log(0.2)], dtype=torch.float32))
    b_s = nn.Parameter(torch.zeros(n_spk, dtype=torch.float32))
    b_u = nn.Parameter(torch.zeros(n_utt, dtype=torch.float32))
    
    optimizer = optim.Adam([beta, log_phi, log_sigma_s, log_sigma_u, b_s, b_u], lr=0.02)
    
    def nb_log_likelihood(y, mu, phi):
        # Negative binomial log-likelihood (gamma / lgamma parameterization)
        # log Gamma(y + phi) - log Gamma(phi) - log Gamma(y + 1) + phi * log(phi / (phi + mu)) + y * log(mu / (phi + mu))
        return (torch.lgamma(y + phi) - torch.lgamma(phi) - torch.lgamma(y + 1) +
                phi * torch.log(phi / (phi + mu)) + y * torch.log(mu / (phi + mu)))
    
    t0 = time.time()
    for step in range(300):
        optimizer.zero_grad()
        
        sigma_s = torch.exp(log_sigma_s)
        sigma_u = torch.exp(log_sigma_u)
        phi_val = torch.exp(log_phi)
        
        eta = offset_t + (x_t @ beta) + b_s[spk_idx] + b_u[utt_idx]
        mu_pred = torch.exp(eta)
        
        ll_data = nb_log_likelihood(y_t, mu_pred, phi_val).sum()
        
        # Log prior / penalty on random effects
        ll_bs = -0.5 * torch.sum(b_s**2 / (sigma_s**2)) - n_spk * torch.log(sigma_s)
        ll_bu = -0.5 * torch.sum(b_u**2 / (sigma_u**2)) - n_utt * torch.log(sigma_u)
        
        loss = -(ll_data + ll_bs + ll_bu) / n_obs
        loss.backward()
        optimizer.step()
        
        if step % 50 == 0 or step == 299:
            print(f"Step {step:3d} | Loss: {loss.item():.4f} | beta: {[round(b.item(), 3) for b in beta]} | phi: {phi_val.item():.2f} | sigma_s: {sigma_s.item():.3f} | sigma_u: {sigma_u.item():.3f}")
            
    print(f"Fit completed in {time.time()-t0:.2f}s")
    print(f"True vs Estimated:")
    print(f"beta: [{beta_0}, {beta_1}, {beta_2}] vs {[round(b.item(), 3) for b in beta]}")
    print(f"sigma_s: {true_sigma_s} vs {torch.exp(log_sigma_s).item():.3f}")
    print(f"sigma_u: {true_sigma_u} vs {torch.exp(log_sigma_u).item():.3f}")
    print(f"phi: {phi} vs {torch.exp(log_phi).item():.3f}")

if __name__ == "__main__":
    test_nb_glmm_fit()
