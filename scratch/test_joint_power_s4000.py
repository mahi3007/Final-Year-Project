import numpy as np, math, time

# Evaluate joint power with S = 4,000 trials to narrow MC uncertainty around the 85% design target
# Target candidates: N in [360, 420, 450, 468] under Modest Disparity Drift (Delta_D = +0.50 pp)
# Combined with WER Superiority: Delta_R = -0.85 pp, sigma_diff = 1.862 pp
# Clean WER non-degradation: Delta_R_clean = -0.30 pp (tested <= +0.50 pp)

np.random.seed(42)
s = 4000
strata = 6
mu_g = np.array([12.0, 14.5, 17.0, 19.5, 22.0, 26.0])
shift_drift = np.zeros(strata)
shift_drift[-1] = 0.50  # +0.50 pp disparity drift
delta_wer = -0.85
sigma_diff = 1.862

candidates = [
    (360, 60),
    (420, 70),
    (450, 75),
    (468, 78)
]

b = 400

print(f"=== Joint Power Simulation with S = {s} Trials (Modest Drift +0.50 pp) ===")

for total_n, ng in candidates:
    t0 = time.time()
    t_crit = -1.6481 if total_n == 468 else (-1.6483 if total_n == 450 else (-1.6485 if total_n == 420 else -1.6491))
    
    # Event A: Paired Student-t superiority against zero
    np.random.seed(42 + total_n)
    diffs = np.random.normal(loc=delta_wer, scale=sigma_diff, size=(s, total_n))
    means_diff = np.mean(diffs, axis=1)
    se_diff = np.std(diffs, axis=1, ddof=1) / math.sqrt(total_n)
    t_stats = means_diff / se_diff
    pass_a = (t_stats < t_crit)
    
    # Event B: Clean WER non-degradation (Delta_R_clean <= +0.50 pp)
    diffs_clean = np.random.normal(loc=-0.30, scale=sigma_diff, size=(s, total_n))
    means_clean = np.mean(diffs_clean, axis=1)
    pass_b = (means_clean <= 0.50)
    
    # Event C: Disparity safety
    spk_eff = np.random.normal(0, 3.80, (s, strata, ng))
    noise_u = np.random.normal(0, 1.316, (s, strata, ng))
    noise_g = np.random.normal(0, 1.316, (s, strata, ng))
    
    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift_drift)[None, :, None] + spk_eff + noise_g
    
    idx = np.random.randint(0, ng, size=(b, ng))
    means_u = np.zeros((s, strata, b))
    means_g = np.zeros((s, strata, b))
    for bi in range(b):
        means_u[:, :, bi] = err_u[:, :, idx[bi]].mean(axis=2)
        means_g[:, :, bi] = err_g[:, :, idx[bi]].mean(axis=2)
        
    disp_u = means_u.max(axis=1) - means_u.min(axis=1)
    disp_g = means_g.max(axis=1) - means_g.min(axis=1)
    delta_d = disp_g - disp_u
    
    ucb95 = np.percentile(delta_d, 95.0, axis=1)
    ucb975 = np.percentile(delta_d, 97.5, axis=1)
    delta_d_hat = (err_g.mean(axis=2).max(axis=1) - err_g.mean(axis=2).min(axis=1)) - (err_u.mean(axis=2).max(axis=1) - err_u.mean(axis=2).min(axis=1))
    
    # Disparity criteria
    pass_c_strict975 = (ucb975 <= 1.40)
    pass_c_strict95 = (ucb95 <= 1.40)
    pass_c_oper = (delta_d_hat <= 1.40) & (ucb95 <= 2.00)
    
    # Joint events
    joint_strict975 = pass_a & pass_b & pass_c_strict975
    joint_strict95 = pass_a & pass_b & pass_c_strict95
    joint_oper = pass_a & pass_b & pass_c_oper
    
    pow_975 = np.mean(joint_strict975)
    se_975 = math.sqrt(pow_975 * (1 - pow_975) / s)
    ci_975 = [pow_975 - 1.96 * se_975, pow_975 + 1.96 * se_975]
    
    pow_95 = np.mean(joint_strict95)
    se_95 = math.sqrt(pow_95 * (1 - pow_95) / s)
    
    pow_op = np.mean(joint_oper)
    se_op = math.sqrt(pow_op * (1 - pow_op) / s)
    
    elapsed = time.time() - t0
    print(f"N={total_n:3d} (Ng={ng:2d}) | Strict Adj UCB97.5 Joint Power = {pow_975*100:5.2f}% +/- {se_975*100:.2f}% | 95% MC CI = [{ci_975[0]*100:.2f}%, {ci_975[1]*100:.2f}%] | UCB95 = {pow_95*100:5.2f}% | Oper = {pow_op*100:5.2f}% | Elapsed = {elapsed:.2f}s")
