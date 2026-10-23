import json, math

with open('reports/stage6m/power_simulation_results.json') as f:
    d = json.load(f)

print('=== Discovery Seed 42 (from hypothesis_1_superiority_against_zero) ===')
h1 = d['hypothesis_1_superiority_against_zero']
disc_t1 = {}
for cohort_key, entries in h1.items():
    null_entry = [e for e in entries if e.get('status') == 'NULL_CALIBRATION' or e.get('true_effect_delta_pp') == 0.0][0]
    N = null_entry['cohort_n']
    df = N - 1
    t_crit = null_entry['t_crit_one_sided_alpha_005']
    rate = null_entry['option_a_one_sided_power']
    trials = 2000
    rej = int(round(rate * trials))
    se = null_entry['option_a_mc_se']
    ci_l, ci_u = null_entry['option_a_ci95']
    covers_5 = (ci_l <= 0.05 <= ci_u)
    disc_t1[N] = {'rate': rate, 'se': se, 'ci_l': ci_l, 'ci_u': ci_u, 'rej': rej, 'trials': trials}
    print(f"N={N:3d} | df={df:3d} | t_crit={t_crit:7.4f} | rej={rej:4d}/{trials} | rate={rate*100:5.2f}% | SE={se*100:4.2f}% | CI=[{ci_l*100:5.2f}%, {ci_u*100:5.2f}%] | Covers 5%: {covers_5}")

print('\n=== Disparity Calibration Investigation (Where did 3.70% and 4.85% come from?) ===')
disp_cal = d.get('disparity_calibration_investigation', {})
for k, v in disp_cal.items():
    print(f"\n--- Key: {k} ---")
    if isinstance(v, list):
        for item in v:
            print(item)
    elif isinstance(v, dict):
        for subk, subv in v.items():
            print(f"  {subk}: {subv}")

print('\n=== DGP Sensitivity Investigation ===')
dgp = d.get('dgp_sensitivity_investigation', {})
for k, v in dgp.items():
    print(f"\n--- DGP Key: {k} ---")
    if isinstance(v, list):
        for item in v:
            print(item)
    elif isinstance(v, dict):
        for subk, subv in v.items():
            print(f"  {subk}: {subv}")
