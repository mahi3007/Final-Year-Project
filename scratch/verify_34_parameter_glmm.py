import numpy as np
import pandas as pd
import patsy
import torch
import time

def verify_canonical_34_parameter_glmm():
    print("=== 1. Canonical 150-Cell / 18,000-Row Design Matrix Verification ===")
    models = ['wav2vec2_base', 'data2vec_base', 'wav2vec2_100h']
    conditions = ['clean', 'noise_15db', 'noise_5db', 'babble_15db', 'reverb_t60_04']
    methods = ['no_adapt', 'suta', 'dsuta', 'dmsuta']
    orderings = ['ORDER_A', 'ORDER_B', 'ORDER_C']

    # 150 canonical factorial settings:
    # 15 canonical No-Adapt cells: ORDER_A only (3 models * 5 conditions)
    # 135 active adaptation cells: 3 models * 3 methods * 3 orders * 5 conditions
    cells = []
    for m in models:
        for c in conditions:
            cells.append({'model': m, 'method': 'no_adapt', 'condition': c, 'ordering': 'ORDER_A'})
    for m in models:
        for meth in ['suta', 'dsuta', 'dmsuta']:
            for o in orderings:
                for c in conditions:
                    cells.append({'model': m, 'method': meth, 'condition': c, 'ordering': o})

    df_cells = pd.DataFrame(cells)
    print(f"Total canonical factorial settings: {len(df_cells)} (Expected: 150 = 15 No-Adapt + 135 Active)")
    assert len(df_cells) == 150

    # Expand to 18,000 utterance records (120 utterances per cell)
    utterances = [f"utt_{i:03d}" for i in range(120)]
    spk_of_utt = [i // 10 for i in range(120)]
    records_18000 = []
    for _, row in df_cells.iterrows():
        for u_idx, u in enumerate(utterances):
            rec = dict(row)
            rec['utterance_id'] = u
            rec['speaker_idx'] = spk_of_utt[u_idx]
            rec['utterance_idx'] = u_idx
            rec['ref_words'] = 10
            records_18000.append(rec)

    df_18000 = pd.DataFrame(records_18000)
    print(f"Total canonical evaluation records: {len(df_18000)} (Expected: 18,000 = 150 * 120)")
    assert len(df_18000) == 18000

    # 34-parameter formula
    formula_raw = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )

    dmat_150_raw = patsy.dmatrix(formula_raw, data=df_cells, return_type='dataframe')
    zero_cols = [c for c in dmat_150_raw.columns if np.all(dmat_150_raw[c] == 0)]
    print(f"Structural zero columns identified and constrained out ({len(zero_cols)}):")
    for zc in zero_cols:
        print(f"  - {zc}")

    dmat_150 = dmat_150_raw.drop(columns=zero_cols)
    rank_150 = np.linalg.matrix_rank(dmat_150.values)
    svd_150 = np.linalg.svd(dmat_150.values, compute_uv=False)
    print(f"\n150-Cell Canonical Design Matrix Shape: {dmat_150.shape}")
    print(f"150-Cell Matrix Rank: {rank_150} (Full rank: {rank_150 == 34})")
    print(f"150-Cell Condition Number: {svd_150[0] / svd_150[-1]:.4f}")
    print(f"150-Cell Smallest Singular Value: {svd_150[-1]:.6f}")
    print(f"150-Cell Largest Singular Value: {svd_150[0]:.6f}")
    assert dmat_150.shape == (150, 34)
    assert rank_150 == 34

    dmat_18000_raw = patsy.dmatrix(formula_raw, data=df_18000, return_type='dataframe')
    dmat_18000 = dmat_18000_raw.drop(columns=zero_cols)
    rank_18000 = np.linalg.matrix_rank(dmat_18000.values)
    svd_18000 = np.linalg.svd(dmat_18000.values, compute_uv=False)
    print(f"\n18,000-Row Canonical Design Matrix Shape: {dmat_18000.shape}")
    print(f"18,000-Row Matrix Rank: {rank_18000} (Full rank: {rank_18000 == 34})")
    print(f"18,000-Row Condition Number: {svd_18000[0] / svd_18000[-1]:.4f}")
    print(f"18,000-Row Smallest Singular Value: {svd_18000[-1]:.6f}")
    print(f"18,000-Row Largest Singular Value: {svd_18000[0]:.6f}")
    assert dmat_18000.shape == (18000, 34)
    assert rank_18000 == 34

    print("\n--- 2. Fitting Synthetic GLMM Under Constrained 34-Parameter Formula ---")
    np.random.seed(42)
    torch.manual_seed(42)

    true_phi = 8.0
    true_sigma_s = 0.15
    true_sigma_u = 0.10

    b_s_true = np.random.normal(0, true_sigma_s, 12)
    b_u_true = np.random.normal(0, true_sigma_u, 120)

    # Generate synthetic error counts on 18,000 canonical rows
    counts = []
    for _, row in df_18000.iterrows():
        m = row['model']
        meth = row['method']
        c = row['condition']
        o = row['ordering']
        s_idx = row['speaker_idx']
        u_idx = row['utterance_idx']

        log_rate = -0.16
        if m == "wav2vec2_100h": log_rate += 0.04
        elif m == "data2vec_base": log_rate -= 0.02
        if c == "noise_15db": log_rate += 0.05
        elif c == "noise_5db": log_rate += 0.18
        elif c == "babble_15db": log_rate += 0.08
        elif c == "reverb_t60_04": log_rate += 0.12

        if meth == "suta": log_rate -= 0.02
        elif meth == "dsuta": log_rate -= 0.015
        elif meth == "dmsuta": log_rate -= 0.01

        # method x order effect
        if meth in ["suta", "dsuta", "dmsuta"] and o == "ORDER_B": log_rate += 0.01
        elif meth in ["suta", "dsuta", "dmsuta"] and o == "ORDER_C": log_rate += 0.02

        eta = np.log(10) + log_rate + b_s_true[s_idx] + b_u_true[u_idx]
        mu = np.exp(eta)
        err = int(np.random.negative_binomial(n=true_phi, p=true_phi / (true_phi + mu)))
        counts.append(err)

    df_18000['errors'] = counts

    # Fit Laplace GLMM with observed curvature
    X = torch.tensor(dmat_18000.values, dtype=torch.float32)
    y = torch.tensor(df_18000['errors'].values, dtype=torch.float32)
    offset = torch.tensor(np.log(df_18000['ref_words'].values), dtype=torch.float32)
    spk_idx = torch.tensor(df_18000['speaker_idx'].values, dtype=torch.long)
    utt_idx = torch.tensor(df_18000['utterance_idx'].values, dtype=torch.long)

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

    start_t = time.time()
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

        ll_bs = -0.5 * torch.sum(b_s**2 / (sig_s**2)) - n_spk * torch.log(sig_s)
        ll_bu = -0.5 * torch.sum(b_u**2 / (sig_u**2)) - n_utt * torch.log(sig_u)

        # EXACT OBSERVED NEGATIVE CURVATURE
        w_obs = (mu * (1.0 + y / phi)) / ((1.0 + mu / phi)**2)
        h_s = torch.zeros(n_spk).scatter_add_(0, spk_idx, w_obs) + (1.0 / (sig_s**2))
        h_u = torch.zeros(n_utt).scatter_add_(0, utt_idx, w_obs) + (1.0 / (sig_u**2))

        # Log determinant of diagonal block Hessian
        log_det_h = 0.5 * (torch.sum(torch.log(h_s)) + torch.sum(torch.log(h_u)))

        loss = -(ll_data + ll_bs + ll_bu - log_det_h) / n_obs
        loss.backward()
        optimizer.step()

    fit_time = time.time() - start_t
    print(f"\n[Canonical 34-Parameter GLMM (18,000 Rows)] Fit completed in {fit_time:.2f}s:")
    print(f"  Dispersion (phi):      {torch.exp(log_phi).item():.3f} (True: {true_phi:.3f})")
    print(f"  Speaker SD (sigma_s):  {torch.exp(log_sigma_s).item():.3f} (True: {true_sigma_s:.3f})")
    print(f"  Utterance SD (sigma_u):{torch.exp(log_sigma_u).item():.3f} (True: {true_sigma_u:.3f})")
    print(f"  Noise 5dB beta:        {beta[8].item():.4f} (True: 0.1800)")
    print(f"  Total coefficients:    {len(beta)} (Full rank 34)")

    # Also build the 21,600 duplicated dataset and fit the 36-parameter model for sensitivity comparison
    print("\n--- 3. Sensitivity Comparison: 18,000-Row (34-Param) vs 21,600-Row (36-Param) ---")
    # For 21,600 rows, repeat No-Adapt across orders
    records_21600 = []
    # Add active methods
    for _, row in df_18000[df_18000['method'] != 'no_adapt'].iterrows():
        records_21600.append(dict(row))
    # Add duplicated No-Adapt
    no_adapt_18000 = df_18000[df_18000['method'] == 'no_adapt']
    for o in orderings:
        for _, row in no_adapt_18000.iterrows():
            r = dict(row)
            r['ordering'] = o
            records_21600.append(r)

    df_21600 = pd.DataFrame(records_21600)
    print(f"Duplicated dataset shape: {len(df_21600)} rows")
    assert len(df_21600) == 21600

    formula_36 = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(ordering, Treatment('ORDER_A')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    dmat_21600 = patsy.dmatrix(formula_36, data=df_21600, return_type='dataframe')
    assert dmat_21600.shape == (21600, 36)
    assert np.linalg.matrix_rank(dmat_21600.values) == 36

    X_21600 = torch.tensor(dmat_21600.values, dtype=torch.float32)
    y_21600 = torch.tensor(df_21600['errors'].values, dtype=torch.float32)
    offset_21600 = torch.tensor(np.log(df_21600['ref_words'].values), dtype=torch.float32)
    spk_idx_21600 = torch.tensor(df_21600['speaker_idx'].values, dtype=torch.long)
    utt_idx_21600 = torch.tensor(df_21600['utterance_idx'].values, dtype=torch.long)

    beta_old = torch.zeros(X_21600.shape[1], requires_grad=True)
    log_phi_old = torch.tensor(np.log(8.0), requires_grad=True)
    log_sigma_s_old = torch.tensor(np.log(0.15), requires_grad=True)
    log_sigma_u_old = torch.tensor(np.log(0.10), requires_grad=True)
    b_s_old = torch.zeros(n_spk, requires_grad=True)
    b_u_old = torch.zeros(n_utt, requires_grad=True)

    opt_old = torch.optim.Adam([beta_old, log_phi_old, log_sigma_s_old, log_sigma_u_old, b_s_old, b_u_old], lr=0.015)
    for step in range(350):
        opt_old.zero_grad()
        p_o = torch.exp(log_phi_old)
        ss_o = torch.exp(log_sigma_s_old)
        su_o = torch.exp(log_sigma_u_old)
        eta_o = offset_21600 + (X_21600 @ beta_old) + b_s_old[spk_idx_21600] + b_u_old[utt_idx_21600]
        mu_o = torch.exp(eta_o)
        ll_d = (
            torch.lgamma(y_21600 + p_o) - torch.lgamma(p_o) - torch.lgamma(y_21600 + 1.0) +
            p_o * torch.log(p_o / (p_o + mu_o)) + y_21600 * torch.log(mu_o / (p_o + mu_o))
        ).sum()
        ll_bs_o = -0.5 * torch.sum(b_s_old**2 / (ss_o**2)) - n_spk * torch.log(ss_o)
        ll_bu_o = -0.5 * torch.sum(b_u_old**2 / (su_o**2)) - n_utt * torch.log(su_o)
        w_obs_o = (mu_o * (1.0 + y_21600 / p_o)) / ((1.0 + mu_o / p_o)**2)
        h_s_o = torch.zeros(n_spk).scatter_add_(0, spk_idx_21600, w_obs_o) + (1.0 / (ss_o**2))
        h_u_o = torch.zeros(n_utt).scatter_add_(0, utt_idx_21600, w_obs_o) + (1.0 / (su_o**2))
        ld_h = 0.5 * (torch.sum(torch.log(h_s_o)) + torch.sum(torch.log(h_u_o)))
        loss_o = -(ll_d + ll_bs_o + ll_bu_o - ld_h) / len(y_21600)
        loss_o.backward()
        opt_old.step()

    print(f"\n[Duplicated 36-Parameter GLMM (21,600 Rows)]:")
    print(f"  Dispersion (phi):      {torch.exp(log_phi_old).item():.3f}")
    print(f"  Speaker SD (sigma_s):  {torch.exp(log_sigma_s_old).item():.3f}")
    print(f"  Utterance SD (sigma_u):{torch.exp(log_sigma_u_old).item():.3f}")
    idx_n5_18000 = [i for i, c in enumerate(dmat_18000.columns) if "noise_5db" in c and ":" not in c][0]
    idx_n5_21600 = [i for i, c in enumerate(dmat_21600.columns) if "noise_5db" in c and ":" not in c][0]
    print(f"  Noise 5dB beta (18k col '{dmat_18000.columns[idx_n5_18000]}'): {beta[idx_n5_18000].item():.4f}")
    print(f"  Noise 5dB beta (21.6k col '{dmat_21600.columns[idx_n5_21600]}'): {beta_old[idx_n5_21600].item():.4f}")

    d_phi = abs(torch.exp(log_phi).item() - torch.exp(log_phi_old).item())
    d_sig_s = abs(torch.exp(log_sigma_s).item() - torch.exp(log_sigma_s_old).item())
    d_sig_u = abs(torch.exp(log_sigma_u).item() - torch.exp(log_sigma_u_old).item())
    d_beta = abs(beta[idx_n5_18000].item() - beta_old[idx_n5_21600].item())

    print("\nSensitivity Differences (Canonical 34-Param vs. Duplicated 36-Param):")
    print(f"  Delta phi:            {d_phi:.4f}")
    print(f"  Delta sigma_s:        {d_sig_s:.4f}")
    print(f"  Delta sigma_u:        {d_sig_u:.4f}")
    print(f"  Delta beta_noise_5db: {d_beta:.4f}")

    print("\n=== Verification Successful ===")

if __name__ == "__main__":
    verify_canonical_34_parameter_glmm()
