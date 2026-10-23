import numpy as np, math, time

# Evaluate bootstrap stability for B in [400, 800, 1000, 1200]
# Sample size N = 360 (Ng = 60) and N = 468 (Ng = 78) at boundary Delta_D = +1.40 pp
# DGP: sigma_spk = 3.80, rho = 0.88, sigma_noise = 1.316, canonical baseline disparity

np.random.seed(42)
n_sim = 1000  # 1000 trials for stability audit
strata = 6
mu_g = np.array([12.0, 14.5, 17.0, 19.5, 22.0, 26.0])
shift = np.zeros(strata)
shift[-1] = 1.40

ng_list = [60, 78]
b_counts = [400, 800, 1000, 1200]

results = {}

for ng in ng_list:
    total_n = strata * ng
    print(f"\n================ N = {total_n} (Ng = {ng}) ================")
    # Generate fixed evaluation trials so comparison across B is on identical synthetic trials
    np.random.seed(42 + ng)
    spk_eff = np.random.normal(0, 3.80, (n_sim, strata, ng))
    noise_u = np.random.normal(0, 1.316, (n_sim, strata, ng))
    noise_g = np.random.normal(0, 1.316, (n_sim, strata, ng))

    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift)[None, :, None] + spk_eff + noise_g

    b_results = {}
    
    # Store decisions for agreement analysis
    decisions_adj = {}
    decisions_95 = {}
    ucb_adj_vals = {}
    ucb_95_vals = {}

    for b in b_counts:
        t0 = time.time()
        np.random.seed(12345 + b) # seed for bootstrap resampling
        idx = np.random.randint(0, ng, size=(b, ng))
        
        means_u = np.zeros((n_sim, strata, b))
        means_g = np.zeros((n_sim, strata, b))
        for bi in range(b):
            means_u[:, :, bi] = err_u[:, :, idx[bi]].mean(axis=2)
            means_g[:, :, bi] = err_g[:, :, idx[bi]].mean(axis=2)
            
        disp_u = means_u.max(axis=1) - means_u.min(axis=1)
        disp_g = means_g.max(axis=1) - means_g.min(axis=1)
        delta_d = disp_g - disp_u  # shape (n_sim, b)
        
        ucb95 = np.percentile(delta_d, 95.0, axis=1)
        ucb975 = np.percentile(delta_d, 97.5, axis=1)
        
        # True Delta_D is 1.40 pp
        noncov_95 = np.mean(ucb95 < 1.40)
        noncov_975 = np.mean(ucb975 < 1.40)
        
        cov_95 = 1.0 - noncov_95
        cov_975 = 1.0 - noncov_975
        
        # Safety pass at tau_D = 1.40
        pass_95 = np.mean(ucb95 <= 1.40)
        pass_975 = np.mean(ucb975 <= 1.40)
        
        mean_ucb95 = np.mean(ucb95)
        std_ucb95 = np.std(ucb95)
        mean_ucb975 = np.mean(ucb975)
        std_ucb975 = np.std(ucb975)
        
        elapsed = time.time() - t0
        
        decisions_adj[b] = (ucb975 <= 1.40)
        decisions_95[b] = (ucb95 <= 1.40)
        ucb_adj_vals[b] = ucb975
        ucb_95_vals[b] = ucb95
        
        se_noncov_975 = math.sqrt(noncov_975 * (1 - noncov_975) / n_sim)
        
        b_results[b] = {
            'mean_ucb975': mean_ucb975,
            'std_ucb975': std_ucb975,
            'noncov_adj975': noncov_975,
            'se_noncov_adj975': se_noncov_975,
            'ci_noncov_adj975': [noncov_975 - 1.96*se_noncov_975, noncov_975 + 1.96*se_noncov_975],
            'cov_adj975': cov_975,
            'pass_adj975': pass_975,
            'noncov_ucb95': noncov_95,
            'pass_ucb95': pass_95,
            'elapsed_sec': elapsed
        }
        print(f"B={b:4d} | Mean Adj UCB={mean_ucb975:.3f} pp (SD={std_ucb975:.3f}) | Noncov={noncov_975*100:.2f}% +/- {se_noncov_975*100:.2f}% | Pass={pass_975*100:.2f}% | Elapsed={elapsed:.2f}s")

    # Compute decision agreement relative to B=1200
    ref_b = 1200
    print(f"\n--- Decision Agreement vs B={ref_b} (on identical {n_sim} synthetic trials) ---")
    for b in [400, 800, 1000]:
        agr_adj = np.mean(decisions_adj[b] == decisions_adj[ref_b])
        corr_adj = np.corrcoef(ucb_adj_vals[b], ucb_adj_vals[ref_b])[0, 1]
        mean_abs_diff = np.mean(np.abs(ucb_adj_vals[b] - ucb_adj_vals[ref_b]))
        print(f"B={b:4d} vs B={ref_b} | Decision Agreement = {agr_adj*100:.2f}% | UCB Correlation = {corr_adj:.4f} | Mean |Diff| = {mean_abs_diff:.4f} pp")

    results[ng] = b_results
