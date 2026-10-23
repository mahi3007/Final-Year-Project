import math
import numpy as np
import time

def run_dgp_sensitivity(n_simulations=1000, bootstrap_b=300, seed=42):
    t0 = time.time()
    ng = 60
    total_spk = ng * 6
    n_strata = 6
    np.random.seed(seed)

    scenarios = [
        ("Baseline (sigma=3.8, rho=0.88, canon)", 3.80, 0.88, False, 5, "canon", 1.40),
        ("Low Speaker Var (sigma=2.50)", 2.50, 0.88, False, 5, "canon", 1.40),
        ("High Speaker Var (sigma=5.00)", 5.00, 0.88, False, 5, "canon", 1.40),
        ("Low Correlation (rho=0.75)", 3.80, 0.75, False, 5, "canon", 1.40),
        ("High Correlation (rho=0.95)", 3.80, 0.95, False, 5, "canon", 1.40),
        ("Heteroscedastic Strata Noise", 3.80, 0.88, True, 5, "canon", 1.40),
        ("Shift on Lowest Stratum", 3.80, 0.88, False, 0, "canon", 1.40),
        ("Shift on Intermediate Stratum", 3.80, 0.88, False, 2, "canon", 1.40),
        ("Narrow Baseline Disparity (3.0 pp)", 3.80, 0.88, False, 5, "narrow", 1.40),
        ("Wide Baseline Disparity (20.0 pp)", 3.80, 0.88, False, 5, "wide", 1.40),
        ("Near-Boundary (Delta_D = +1.30 pp)", 3.80, 0.88, False, 5, "canon", 1.30),
        ("Above-Boundary (Delta_D = +1.50 pp)", 3.80, 0.88, False, 5, "canon", 1.50),
    ]

    print(f"Running DGP Sensitivity Battery (N={total_spk}, Ng={ng}, S={n_simulations}, B={bootstrap_b})...")
    for name, sig_spk, rho, heterosc, shift_idx, base_mode, true_disp in scenarios:
        sig_diff = math.sqrt(2.0 * (sig_spk ** 2) * (1.0 - rho))
        base_noise = sig_spk * math.sqrt(1.0 - rho)

        if base_mode == "narrow":
            mu_g = np.array([30.0, 30.6, 31.2, 31.8, 32.4, 33.0])
        elif base_mode == "wide":
            mu_g = np.array([20.0, 24.0, 28.0, 32.0, 36.0, 40.0])
        else:
            mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])

        spk_eff = np.random.normal(0, sig_spk, (n_simulations, n_strata, ng))

        if heterosc:
            scales = np.array([0.6, 0.8, 1.0, 1.2, 1.4, 1.6])[:, None]
            noise_u = np.random.normal(0, base_noise * scales, (n_simulations, n_strata, ng))
            noise_g = np.random.normal(0, base_noise * scales, (n_simulations, n_strata, ng))
        else:
            noise_u = np.random.normal(0, base_noise, (n_simulations, n_strata, ng))
            noise_g = np.random.normal(0, base_noise, (n_simulations, n_strata, ng))

        shift_vec = np.zeros(n_strata)
        if shift_idx == 0:
            shift_vec[0] = -true_disp  # lower minimum
        else:
            shift_vec[shift_idx] = true_disp

        err_u = mu_g[None, :, None] + spk_eff + noise_u
        err_g = (mu_g + shift_vec)[None, :, None] + spk_eff + noise_g

        # Point estimates
        pt_u = err_u.mean(axis=2).max(axis=1) - err_u.mean(axis=2).min(axis=1)
        pt_g = err_g.mean(axis=2).max(axis=1) - err_g.mean(axis=2).min(axis=1)
        mean_pt = float(np.mean(pt_g - pt_u))
        bias = mean_pt - true_disp

        idx = np.random.randint(0, ng, size=(bootstrap_b, ng))
        means_u = np.zeros((n_simulations, n_strata, bootstrap_b))
        means_g = np.zeros((n_simulations, n_strata, bootstrap_b))
        for b in range(bootstrap_b):
            means_u[:, :, b] = err_u[:, :, idx[b]].mean(axis=2)
            means_g[:, :, b] = err_g[:, :, idx[b]].mean(axis=2)

        boot_deltas = (means_g.max(axis=1) - means_g.min(axis=1)) - (means_u.max(axis=1) - means_u.min(axis=1))
        u95 = np.percentile(boot_deltas, 95.0, axis=1)
        u975 = np.percentile(boot_deltas, 97.5, axis=1)

        # Non-coverage at boundary 1.40: declares safe (UCB <= 1.40) despite true_disp >= 1.40
        # If true_disp == 1.40: boundary false safety pass
        noncov_95 = float(np.mean(u95 <= 1.40))
        noncov_975 = float(np.mean(u975 <= 1.40))
        se_975 = math.sqrt(noncov_975 * (1 - noncov_975) / n_simulations)

        print(f"  {name:38s} | Bias={bias:+.3f} pp | UCB95 NonCov={noncov_95*100:4.1f}% | Adj UCB97.5 NonCov={noncov_975*100:4.1f}% +/- {se_975*100:4.2f}%")

    print(f"Done in {time.time()-t0:.2f}s")

if __name__ == "__main__":
    run_dgp_sensitivity()
