import math
import numpy as np

def test_metrics_mult(true_disp, shift_val):
    n_simulations = 2000
    bootstrap_b = 400
    n_strata = 6
    ng = 60
    np.random.seed(42)

    sig_spk = 3.8
    rho = 0.88
    base_noise = sig_spk * math.sqrt(1.0 - rho)
    mu_base = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])

    shift_vec = np.zeros(n_strata)
    shift_vec[-1] = shift_val

    spk_eff = np.random.normal(0, sig_spk, (n_simulations, n_strata, ng))
    noise_u = np.random.normal(0, base_noise, (n_simulations, n_strata, ng))
    noise_g = np.random.normal(0, base_noise, (n_simulations, n_strata, ng))

    err_u = mu_base[None, :, None] + spk_eff + noise_u
    err_g = (mu_base + shift_vec)[None, :, None] + spk_eff + noise_g

    idx = np.random.randint(0, ng, size=(bootstrap_b, ng))
    means_u = np.zeros((n_simulations, n_strata, bootstrap_b))
    means_g = np.zeros((n_simulations, n_strata, bootstrap_b))
    for b in range(bootstrap_b):
        means_u[:, :, b] = err_u[:, :, idx[b]].mean(axis=2)
        means_g[:, :, b] = err_g[:, :, idx[b]].mean(axis=2)

    boot_deltas = (means_g.max(axis=1) - means_g.min(axis=1)) - (means_u.max(axis=1) - means_u.min(axis=1))
    u95 = np.percentile(boot_deltas, 95.0, axis=1)
    u975 = np.percentile(boot_deltas, 97.5, axis=1)

    # 1. Confidence-bound noncoverage: P(U < true_disp)
    noncov_95 = float(np.mean(u95 < true_disp))
    noncov_975 = float(np.mean(u975 < true_disp))

    # 2. Confidence-bound coverage: P(U >= true_disp)
    cov_95 = 1.0 - noncov_95
    cov_975 = 1.0 - noncov_975

    # 3. Safety-pass probability: P(U <= 1.40)
    pass_95 = float(np.mean(u95 <= 1.40))
    pass_975 = float(np.mean(u975 <= 1.40))

    # 4. False safety declaration: P(U <= 1.40 | true_disp > 1.40)
    false_safe_95 = pass_95 if true_disp > 1.40 else (pass_95 if true_disp == 1.40 else 0.0)
    false_safe_975 = pass_975 if true_disp > 1.40 else (pass_975 if true_disp == 1.40 else 0.0)

    print(f"true_disp = {true_disp:+.2f} pp:")
    print(f"  Non-coverage P(U < true): UCB95 = {noncov_95*100:5.2f}%, Adj UCB97.5 = {noncov_975*100:5.2f}%")
    print(f"  Coverage P(U >= true):    UCB95 = {cov_95*100:5.2f}%, Adj UCB97.5 = {cov_975*100:5.2f}%")
    print(f"  Safety pass P(U <= 1.40): UCB95 = {pass_95*100:5.2f}%, Adj UCB97.5 = {pass_975*100:5.2f}%")
    print(f"  False safety declar.:     UCB95 = {false_safe_95*100:5.2f}%, Adj UCB97.5 = {false_safe_975*100:5.2f}%")

print("--- SUB-BOUNDARY (+1.30 pp) ---")
test_metrics_mult(1.30, 1.30)
print("\n--- EXACT BOUNDARY (+1.40 pp) ---")
test_metrics_mult(1.40, 1.40)
print("\n--- ABOVE BOUNDARY (+1.50 pp) ---")
test_metrics_mult(1.50, 1.50)
