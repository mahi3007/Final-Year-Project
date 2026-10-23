import json

with open('reports/stage6m/power_simulation_results.json', 'r') as f:
    data = json.load(f)

print("\n=== 5. DGP SENSITIVITY INVESTIGATION (N=360, Validation Seed 20261012) ===")
dgp_val = data['dgp_sensitivity_investigation']['validation_n360_seed20261012']
for sc in dgp_val:
    name = sc['scenario_name']
    t_disp = sc['true_disparity_contrast_pp']
    noncov = sc['confidence_bound_noncoverage_adjusted_ucb975'] * 100
    noncov_se = sc['noncoverage_adjusted_ucb975_mc_se'] * 100
    noncov_ci = [x * 100 for x in sc['noncoverage_adjusted_ucb975_ci95']]
    pass_prob = sc['safety_pass_probability_adjusted_ucb975'] * 100
    false_safe = sc['false_safety_declaration_probability_adjusted_ucb975'] * 100
    print(f"{name[:35]:35s} | True={t_disp:+.2f} | NonCov={noncov:4.2f}% +/- {noncov_se:4.2f}% [{noncov_ci[0]:.2f}%, {noncov_ci[1]:.2f}%] | Pass={pass_prob:4.2f}% | FalseSafe={false_safe:4.2f}%")
