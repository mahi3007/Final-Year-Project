"""Script to update scripts/simulate_stage6m_power.py with trial-level intersection counts and Rule A/B interpretations."""
from pathlib import Path

P = Path("scripts/simulate_stage6m_power.py")
text = P.read_text(encoding="utf-8")

# 1. Update Section 4 to record trial-level counts
old_sec4_block = """            # Joint decisions
            joint_a_95 = pass_a & pass_b_point & pass_c_95
            joint_a_975 = pass_a & pass_b_point & pass_c_975
            joint_b_975 = pass_a & pass_b_inferential & pass_c_975
            joint_oper = pass_a & pass_b_point & pass_c_oper

            p_joint_a_95 = float(np.mean(joint_a_95))
            p_joint_a_975 = float(np.mean(joint_a_975))
            p_joint_b_975 = float(np.mean(joint_b_975))
            p_joint_oper = float(np.mean(joint_oper))

            succ_joint_a_95 = int(np.sum(joint_a_95))
            succ_joint_a_975 = int(np.sum(joint_a_975))
            succ_joint_b_975 = int(np.sum(joint_b_975))
            succ_joint_oper = int(np.sum(joint_oper))

            mc_se_975 = float(math.sqrt(p_joint_a_975 * (1.0 - p_joint_a_975) / n_simulations))
            ci_975 = [round(max(0.0, p_joint_a_975 - 1.96 * mc_se_975), 4), round(min(1.0, p_joint_a_975 + 1.96 * mc_se_975), 4)]

            scen_seed = seed_discovery + cohort_n + sc_id * 1000
            results["joint_safety_utility_simulation"][cohort_label].append({"""

new_sec4_block = """            # Joint decisions
            joint_a_95 = pass_a & pass_b_point & pass_c_95
            joint_a_975 = pass_a & pass_b_point & pass_c_975
            joint_b_975 = pass_a & pass_b_inferential & pass_c_975
            joint_oper = pass_a & pass_b_point & pass_c_oper

            p_joint_a_95 = float(np.mean(joint_a_95))
            p_joint_a_975 = float(np.mean(joint_a_975))
            p_joint_b_975 = float(np.mean(joint_b_975))
            p_joint_oper = float(np.mean(joint_oper))

            succ_joint_a_95 = int(np.sum(joint_a_95))
            succ_joint_a_975 = int(np.sum(joint_a_975))
            succ_joint_b_975 = int(np.sum(joint_b_975))
            succ_joint_oper = int(np.sum(joint_oper))

            # Explicit matched trial-level intersection counts
            n_A = succ_a
            n_B_pt = succ_b_pt
            n_B_inf = succ_b_inf
            n_C = succ_c_975
            n_A_and_B_inf = int(np.sum(pass_a & pass_b_inferential))
            n_A_and_B_pt = int(np.sum(pass_a & pass_b_point))
            n_A_and_C = int(np.sum(pass_a & pass_c_975))
            n_B_inf_and_C = int(np.sum(pass_b_inferential & pass_c_975))
            n_B_pt_and_C = int(np.sum(pass_b_point & pass_c_975))
            n_A_and_B_inf_and_C = succ_joint_b_975
            n_A_and_B_pt_and_C = succ_joint_a_975

            mc_se_975 = float(math.sqrt(p_joint_a_975 * (1.0 - p_joint_a_975) / n_simulations))
            ci_975 = [round(max(0.0, p_joint_a_975 - 1.96 * mc_se_975), 4), round(min(1.0, p_joint_a_975 + 1.96 * mc_se_975), 4)]

            scen_seed = seed_discovery + cohort_n + sc_id * 1000
            results["joint_safety_utility_simulation"][cohort_label].append({
                "n_A": n_A,
                "n_B_point": n_B_pt,
                "n_B_inferential": n_B_inf,
                "n_C": n_C,
                "n_A_and_B": n_A_and_B_inf,
                "n_A_and_B_point": n_A_and_B_pt,
                "n_A_and_C": n_A_and_C,
                "n_B_and_C": n_B_inf_and_C,
                "n_B_point_and_C": n_B_pt_and_C,
                "n_A_and_B_and_C": n_A_and_B_inf_and_C,
                "n_A_and_B_point_and_C": n_A_and_B_pt_and_C,"""

assert old_sec4_block in text, "old_sec4_block not found in text"
text = text.replace(old_sec4_block, new_sec4_block)

# 2. Update Section 5 to store trial-level counts and detailed Rule A / Rule B classification
old_sec5_block = """        # Rule A: Point estimate >= 85.00%
        # Rule B: Lower 95% Monte Carlo confidence bound > 85.00%
        rule_a_pass_s1 = bool(p_joint975_s1 >= 0.85)
        rule_a_pass_s2 = bool(p_joint975_s2 >= 0.85)
        rule_a_dual_pass = bool(rule_a_pass_s1 and rule_a_pass_s2)
        rule_b_pass_s2 = bool(ci95_s2[0] > 0.85)

        results["sample_size_exploration_grid"].append({"""

new_sec5_block = """        # Rule A: Point estimate >= 85.00%
        # Rule B: Lower 95% Monte Carlo confidence bound > 85.00%
        rule_a_pass_s1 = bool(p_joint975_s1 >= 0.85)
        rule_a_pass_s2 = bool(p_joint975_s2 >= 0.85)
        rule_a_dual_pass = bool(rule_a_pass_s1 and rule_a_pass_s2)
        rule_b_pass_s2 = bool(ci95_s2[0] > 0.85)
        rule_b_dual_pass = bool(rule_a_pass_s1 and rule_b_pass_s2)

        if total_spk == 450:
            mc_interp = f"FAIL under Rule A ({p_joint975_s2*100:.2f}% < 85.00%) and FAIL under Rule B ({ci95_s2[0]*100:.2f}% < 85.00%). MC interval [{ci95_s2[0]*100:.2f}%, {ci95_s2[1]*100:.2f}%] crosses 85%."
        elif total_spk == 468:
            mc_interp = f"PASS under Rule A ({p_joint975_s2*100:.2f}% >= 85.00%), FAIL under Rule B (L_95% = {ci95_s2[0]*100:.2f}% < 85.00%). MC interval [{ci95_s2[0]*100:.2f}%, {ci95_s2[1]*100:.2f}%]."
        elif total_spk in [540, 600]:
            mc_interp = f"PASS under Rule A ({p_joint975_s2*100:.2f}% >= 85.00%) and PASS under Rule B (L_95% = {ci95_s2[0]*100:.2f}% > 85.00%). MC interval [{ci95_s2[0]*100:.2f}%, {ci95_s2[1]*100:.2f}%]."
        elif total_spk == 180:
            mc_interp = f"FAIL under both rules for Parity ({p_joint975_s1*100:.2f}%) and Drift ({p_joint975_s2*100:.2f}%)."
        else:
            mc_interp = "FAIL under both rules for Modest Disparity Drift."

        results["sample_size_exploration_grid"].append({
            "n_A_s1": rec_s1["n_A"],
            "n_B_s1": rec_s1["n_B_inferential"],
            "n_C_s1": rec_s1["n_C"],
            "n_A_and_B_s1": rec_s1["n_A_and_B"],
            "n_A_and_C_s1": rec_s1["n_A_and_C"],
            "n_B_and_C_s1": rec_s1["n_B_and_C"],
            "n_A_and_B_and_C_s1": rec_s1["n_A_and_B_and_C"],
            "n_A_s2": rec_s2["n_A"],
            "n_B_s2": rec_s2["n_B_inferential"],
            "n_C_s2": rec_s2["n_C"],
            "n_A_and_B_s2": rec_s2["n_A_and_B"],
            "n_A_and_C_s2": rec_s2["n_A_and_C"],
            "n_B_and_C_s2": rec_s2["n_B_and_C"],
            "n_A_and_B_and_C_s2": rec_s2["n_A_and_B_and_C"],
            "mc_interval_interpretation": mc_interp,"""

assert old_sec5_block in text, "old_sec5_block not found in text"
text = text.replace(old_sec5_block, new_sec5_block)

P.write_text(text, encoding="utf-8")
print("simulate_stage6m_power.py updated successfully!")
