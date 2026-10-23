import numpy as np, math

# Script to compute exact 2x2 Pass/Fail transitions, conditional agreements, and bound differences
# Scenarios:
# 1. Boundary State (Delta_D = +1.40 pp, where pass rate is low ~2.5-3%)
# 2. Modest Drift State (Delta_D = +0.50 pp, near-threshold operational state where pass rate is ~85-88%)
# Cohorts: N = 360 (Ng = 60) and N = 468 (Ng = 78)
# Trials: S = 2000 trials per condition to obtain high cell counts

def analyze_transitions(ng, true_disp, scenario_name, seed=42):
    total_n = 6 * ng
    s = 2000
    strata = 6
    mu_g = np.array([25.0, 27.0, 30.0, 32.0, 34.0, 36.0])
    shift = np.zeros(strata)
    shift[-1] = true_disp
    
    np.random.seed(seed + ng + int(abs(true_disp)*100))
    spk_eff = np.random.normal(0, 3.80, (s, strata, ng))
    noise_u = np.random.normal(0, 1.316, (s, strata, ng))
    noise_g = np.random.normal(0, 1.316, (s, strata, ng))
    
    err_u = mu_g[None, :, None] + spk_eff + noise_u
    err_g = (mu_g + shift)[None, :, None] + spk_eff + noise_g
    
    # Compute for B = 400, B = 1000, B = 1200
    b_dict = {}
    for b in [400, 1000, 1200]:
        np.random.seed(12345 + b)
        idx = np.random.randint(0, ng, size=(b, ng))
        means_u = np.zeros((s, strata, b))
        means_g = np.zeros((s, strata, b))
        for bi in range(b):
            means_u[:, :, bi] = err_u[:, :, idx[bi]].mean(axis=2)
            means_g[:, :, bi] = err_g[:, :, idx[bi]].mean(axis=2)
        disp_u = means_u.max(axis=1) - means_u.min(axis=1)
        disp_g = means_g.max(axis=1) - means_g.min(axis=1)
        delta_d = disp_g - disp_u
        u975 = np.percentile(delta_d, 97.5, axis=1)
        passed = (u975 <= 1.40)
        b_dict[b] = {'u975': u975, 'passed': passed}
        
    print(f"\n================================================================================")
    print(f"Cohort N = {total_n} (Ng = {ng}) | Scenario: {scenario_name} (True Delta_D = {true_disp:+.2f} pp)")
    print(f"================================================================================")
    
    for comp_b in [1000, 1200]:
        pass_400 = b_dict[400]['passed']
        pass_comp = b_dict[comp_b]['passed']
        
        # 2x2 cells
        pp = int(np.sum(pass_400 & pass_comp))
        pf = int(np.sum(pass_400 & (~pass_comp)))
        fp = int(np.sum((~pass_400) & pass_comp))
        ff = int(np.sum((~pass_400) & (~pass_comp)))
        
        total = s
        overall_agr = (pp + ff) / total
        
        # Conditional agreement among passing cases
        total_p_400 = pp + pf
        total_p_comp = pp + fp
        
        cond_agr_400 = (pp / total_p_400) if total_p_400 > 0 else 1.0
        cond_agr_comp = (pp / total_p_comp) if total_p_comp > 0 else 1.0
        jaccard_pass = pp / (pp + pf + fp) if (pp + pf + fp) > 0 else 1.0
        
        # Bound differences
        diffs = b_dict[comp_b]['u975'] - b_dict[400]['u975']
        mean_abs_diff = np.mean(np.abs(diffs))
        bias_diff = np.mean(diffs)
        corr = np.corrcoef(b_dict[400]['u975'], b_dict[comp_b]['u975'])[0, 1]
        
        print(f"\n--- B = 400 vs B = {comp_b} ---")
        print(f"  2x2 Transition Matrix (Total S = {total}):")
        print(f"    Pass(B=400) & Pass(B={comp_b}): {pp:4d} ({pp/total*100:5.2f}%)")
        print(f"    Pass(B=400) & Fail(B={comp_b}): {pf:4d} ({pf/total*100:5.2f}%)")
        print(f"    Fail(B=400) & Pass(B={comp_b}): {fp:4d} ({fp/total*100:5.2f}%)")
        print(f"    Fail(B=400) & Fail(B={comp_b}): {ff:4d} ({ff/total*100:5.2f}%)")
        print(f"  Overall Decision Agreement        : {overall_agr*100:.2f}%")
        print(f"  Pass Rate B=400                   : {total_p_400/total*100:.2f}% ({total_p_400}/{total})")
        print(f"  Pass Rate B={comp_b}                  : {total_p_comp/total*100:.2f}% ({total_p_comp}/{total})")
        print(f"  Conditional Agreement P(B={comp_b}|B=400) : {cond_agr_400*100:.2f}%")
        print(f"  Conditional Agreement P(B=400|B={comp_b}) : {cond_agr_comp*100:.2f}%")
        print(f"  Pass Event Jaccard Similarity     : {jaccard_pass*100:.2f}%")
        print(f"  Bound Correlation (r)             : {corr:.4f}")
        print(f"  Mean Absolute Difference |Diff|   : {mean_abs_diff:.4f} pp")
        print(f"  Mean Bound Shift (B={comp_b} - B=400)  : {bias_diff:+.4f} pp")

analyze_transitions(60, 1.40, "Boundary Stress State (Delta_D = +1.40 pp)")
analyze_transitions(78, 1.40, "Boundary Stress State (Delta_D = +1.40 pp)")
analyze_transitions(78, 0.50, "Modest Drift Near-Threshold State (Delta_D = +0.50 pp)")
