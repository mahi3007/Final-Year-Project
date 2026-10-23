import json

with open("reports/stage6m/power_simulation_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for c in ["cohort_60", "cohort_180", "cohort_360", "cohort_450", "cohort_468", "cohort_540", "cohort_600"]:
    print("=" * 40)
    print("COHORT:", c)
    info = d["joint_safety_utility_simulation"].get(c, [])
    for sc in info:
        print(f"  Scenario {sc['scenario_id']}: {sc['scenario_name']}")
        print(f"    cohort_n: {sc['cohort_n']}, speakers_per_stratum: {sc['speakers_per_stratum']}")
        print(f"    true_wer_effect_pp: {sc['true_wer_effect_pp']}, true_disparity_shift_pp: {sc['true_disparity_shift_pp']}")
        print(f"    strict_adjusted_ucb975: {sc['joint_power_strict_adjusted_ucb975']} (successes: {sc['joint_power_strict_adjusted_ucb975_successes']})")
        print(f"    strict_ucb95: {sc.get('joint_power_strict_ucb95')}")
