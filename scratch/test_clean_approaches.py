import numpy as np, math, time
from scipy import stats

s = 4000
b = 1000
strata = 6
candidates = [(360, 60), (420, 70), (450, 75), (468, 78)]
sigma_speaker = 3.80
rho_paired = 0.88
sigma_diff = math.sqrt(2.0 * (sigma_speaker ** 2) * (1.0 - rho_paired)) # 1.862
sigma_noise = sigma_speaker * math.sqrt(1.0 - rho_paired) # 1.316
mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])

print("Testing Approach A (Point Guardrail) vs Approach B (Inferential UCB95) at S=4000, B=1000 under Modest Drift (+0.50 pp)")

for total_n, ng in candidates:
    t0 = time.time()
    t_crit = stats.t.ppf(0.05, df=total_n - 1)
    
    # Event A: Accented WER Superiority (Delta_R = -0.85 pp)
    np.random.seed(42 + total_n)
    diffs_acc = np.random.normal(-0.85, sigma_diff, (s, total_n))
    mean_acc = diffs_acc.mean(axis=1)
    se_acc = diffs_acc.std(axis=1, ddof=1) / math.sqrt(total_n)
    t_acc = mean_acc / se_acc
    pass_a = (t_acc < t_crit)
    
    # Event B (Approach A: Point guardrail hat{Delta R_clean} <= +0.50 pp)
    # Event B (Approach B: Inferential UCB95(Delta R_clean) <= +0.50 pp)
    # Clean WER contrast: true shift = -0.30 pp (or 0.00 pp)
    diffs_clean = np.random.normal(-0.30, sigma_diff, (s, total_n))
    mean_clean = diffs_clean.mean(axis=1)
    se_clean = diffs_clean.std(axis=1, ddof=1) / math.sqrt(total_n)
    pass_b_point = (mean_clean <= 0.50)
    
    ucb95_clean = mean_clean + (-t_crit) * se_clean  # one-sided 95% UCB
    pass_b_inferential = (ucb95_clean <= 0.50)
    
    # Event C: Disparity Safety (Adj UCB97.5 <= 1.40 pp)
    spk_eff = np.random.normal(0, sigma_speaker, (s, strata, ng))
    noise_u = np.random.normal(0, sigma_noise, (s, strata, ng))
    noise_g = np.random.normal(0, sigma_noise, (s, strata, ng))
    shift_vec = np.zeros(strata)
    shift_vec[-1] = 0.50 # modest drift
    
    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift_vec)[None, :, None] + spk_eff + noise_g - 0.85
    
    idx = np.random.randint(0, ng, size=(b, ng))
    means_u = np.zeros((s, strata, b))
    means_g = np.zeros((s, strata, b))
    for bi in range(b):
        means_u[:, :, bi] = err_u[:, :, idx[bi]].mean(axis=2)
        means_g[:, :, bi] = err_g[:, :, idx[bi]].mean(axis=2)
        
    boot_deltas = (means_g.max(axis=1) - means_g.min(axis=1)) - (means_u.max(axis=1) - means_u.min(axis=1))
    u975 = np.percentile(boot_deltas, 97.5, axis=1)
    pass_c = (u975 <= 1.40)
    
    # Joint Success
    joint_app_a = pass_a & pass_b_point & pass_c
    joint_app_b = pass_a & pass_b_inferential & pass_c
    
    pow_a = np.mean(joint_app_a)
    se_a = math.sqrt(pow_a * (1 - pow_a) / s)
    pow_b = np.mean(joint_app_b)
    se_b = math.sqrt(pow_b * (1 - pow_b) / s)
    
    print(f"N={total_n:3d} (Ng={ng:2d}) | App A (Point): {pow_a*100:5.2f}% +/- {se_a*100:.2f}% [{pow_a*100-1.96*se_a*100:.2f}%, {pow_a*100+1.96*se_a*100:.2f}%] | App B (Inferential): {pow_b*100:5.2f}% +/- {se_b*100:.2f}% [{pow_b*100-1.96*se_b*100:.2f}%, {pow_b*100+1.96*se_b*100:.2f}%] | Clean pass: pt={np.mean(pass_b_point)*100:.2f}%, inf={np.mean(pass_b_inferential)*100:.2f}% | Elapsed: {time.time()-t0:.1f}s")
