import json

with open('reports/stage6m/power_simulation_results.json', 'r') as f:
    data = json.load(f)

print("=== 1. HYPOTHESIS 1 NULL REJECTION (TYPE I ERROR) ===")
h1 = data['hypothesis_1_superiority_against_zero']
for cohort, items in h1.items():
    for it in items:
        if it['true_effect_delta_pp'] == 0.0:
            n = it['cohort_n']
            tcrit = it['t_crit_one_sided_alpha_005']
            p1s = it['option_a_one_sided_power'] * 100
            se1s = it['option_a_mc_se'] * 100
            ci1s = [x * 100 for x in it['option_a_ci95']]
            p2s = it['option_b_two_sided_directional_power'] * 100
            se2s = it['option_b_mc_se'] * 100
            print(f"N={n:3d} (tcrit={tcrit:.4f}): Option A Type I = {p1s:5.2f}% +/- {se1s:4.2f}% (95% CI: [{ci1s[0]:.2f}%, {ci1s[1]:.2f}%]) | Option B = {p2s:5.2f}% +/- {se2s:4.2f}%")

print("\n=== 2. JOINT SAFETY-UTILITY CORE SCENARIO 1 & 2 ===")
js = data['joint_safety_utility_simulation']
for cohort, items in js.items():
    s1 = items[0]
    s2 = items[1]
    n = int(cohort.replace('cohort_', ''))
    print(f"N={n:3d} | S1: UCB95={s1['joint_power_strict_ucb95']*100:5.1f}%, Adj UCB97.5={s1['joint_power_strict_adjusted_ucb975']*100:5.1f}% +/- {s1['mc_se_joint_strict_adjusted_ucb975']*100:.2f}% | S2: UCB95={s2['joint_power_strict_ucb95']*100:5.1f}%, Adj UCB97.5={s2['joint_power_strict_adjusted_ucb975']*100:5.1f}% +/- {s2['mc_se_joint_strict_adjusted_ucb975']*100:.2f}%, Oper={s2['joint_power_operational_rule']*100:5.1f}%")

print("\n=== 3. DGP SENSITIVITY INVESTIGATION (N=360, Discovery Seed 42) ===")
dgp360 = data['dgp_sensitivity_investigation']['discovery_n360_seed42']
for sc in dgp360:
    name = sc['scenario_name']
    t_disp = sc['true_disparity_contrast_pp']
    noncov = sc['confidence_bound_noncoverage_adjusted_ucb975'] * 100
    noncov_se = sc['noncoverage_adjusted_ucb975_mc_se'] * 100
    noncov_ci = [x * 100 for x in sc['noncoverage_adjusted_ucb975_ci95']]
    pass_prob = sc['safety_pass_probability_adjusted_ucb975'] * 100
    false_safe = sc['false_safety_declaration_probability_adjusted_ucb975'] * 100
    print(f"{name[:35]:35s} | True={t_disp:+.2f} | NonCov={noncov:4.2f}% +/- {noncov_se:4.2f}% [{noncov_ci[0]:.2f}%, {noncov_ci[1]:.2f}%] | Pass={pass_prob:4.2f}% | FalseSafe={false_safe:4.2f}%")

print("\n=== 4. DGP SENSITIVITY INVESTIGATION (N=180, Discovery Seed 42) ===")
dgp180 = data['dgp_sensitivity_investigation']['discovery_n180_seed42']
for sc in dgp180:
    name = sc['scenario_name']
    t_disp = sc['true_disparity_contrast_pp']
    noncov = sc['confidence_bound_noncoverage_adjusted_ucb975'] * 100
    noncov_se = sc['noncoverage_adjusted_ucb975_mc_se'] * 100
    noncov_ci = [x * 100 for x in sc['noncoverage_adjusted_ucb975_ci95']]
    pass_prob = sc['safety_pass_probability_adjusted_ucb975'] * 100
    false_safe = sc['false_safety_declaration_probability_adjusted_ucb975'] * 100
    print(f"{name[:35]:35s} | True={t_disp:+.2f} | NonCov={noncov:4.2f}% +/- {noncov_se:4.2f}% [{noncov_ci[0]:.2f}%, {noncov_ci[1]:.2f}%] | Pass={pass_prob:4.2f}% | FalseSafe={false_safe:4.2f}%")
