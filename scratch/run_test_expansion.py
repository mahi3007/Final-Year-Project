import math
import numpy as np
from scipy import stats
import time

def test_speed():
    t0 = time.time()
    n_simulations = 2000
    bootstrap_b = 400
    ng = 78
    total_spk = 78 * 6
    n_strata = 6
    sigma_speaker = 3.80
    rho_paired = 0.88
    sigma_noise = sigma_speaker * math.sqrt(1.0 - rho_paired)
    mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])

    spk_eff = np.random.normal(0, sigma_speaker, (n_simulations, n_strata, ng))
    noise_u = np.random.normal(0, sigma_noise, (n_simulations, n_strata, ng))
    noise_g = np.random.normal(0, sigma_noise, (n_simulations, n_strata, ng))

    shift_vec = np.zeros(n_strata)
    shift_vec[-1] = 0.50

    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift_vec)[None, :, None] + spk_eff + noise_g - 0.85

    diffs = (err_g - err_u).reshape(n_simulations, -1)
    t_crit = stats.t.ppf(0.05, df=total_spk - 1)
    a_ok = (diffs.mean(axis=1) / (diffs.std(axis=1, ddof=1) / math.sqrt(total_spk))) < t_crit

    idx = np.random.randint(0, ng, size=(bootstrap_b, ng))
    means_u = np.zeros((n_simulations, n_strata, bootstrap_b))
    means_g = np.zeros((n_simulations, n_strata, bootstrap_b))
    for b in range(bootstrap_b):
        means_u[:, :, b] = err_u[:, :, idx[b]].mean(axis=2)
        means_g[:, :, b] = err_g[:, :, idx[b]].mean(axis=2)

    boot_deltas = (means_g.max(axis=1) - means_g.min(axis=1)) - (means_u.max(axis=1) - means_u.min(axis=1))
    u95 = np.percentile(boot_deltas, 95.0, axis=1)
    u975 = np.percentile(boot_deltas, 97.5, axis=1)

    p_joint95 = np.mean(a_ok & (u95 <= 1.40))
    p_joint975 = np.mean(a_ok & (u975 <= 1.40))
    print(f"Ng={ng} (N={total_spk}): S2 Drift Joint UCB95={p_joint95*100:.2f}%, Adj UCB97.5={p_joint975*100:.2f}%, Time={time.time()-t0:.2f}s")

if __name__ == "__main__":
    test_speed()
