import json

with open('reports/stage6m/power_simulation_results.json', 'r') as f:
    data = json.load(f)

h1 = data.get('hypothesis_1_superiority_against_zero', {})
print("=== Hypothesis 1 Null Rejection (Type I Error) from power_simulation_results.json ===")
for cohort_key, items in h1.items():
    for item in items:
        if item['true_effect_delta_pp'] == 0.0:
            n = item['cohort_n']
            tcrit = item['t_crit_one_sided_alpha_005']
            opt_a = item['option_a_one_sided_power'] * 100
            opt_a_se = item['option_a_mc_se'] * 100
            opt_a_ci = [x * 100 for x in item['option_a_ci95']]
            opt_b = item['option_b_two_sided_directional_power'] * 100
            opt_b_se = item['option_b_mc_se'] * 100
            print(f"N={n:3d} (tcrit={tcrit:.4f}): Option A = {opt_a:5.2f}% +/- {opt_a_se:.2f}% (95% CI: [{opt_a_ci[0]:.2f}%, {opt_a_ci[1]:.2f}%]) | Option B = {opt_b:5.2f}% +/- {opt_b_se:.2f}%")

print("\n=== Metadata ===")
print(json.dumps(data.get('metadata', {}), indent=2))
