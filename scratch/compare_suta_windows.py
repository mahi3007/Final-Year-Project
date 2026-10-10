import pandas as pd

wm_h = pd.read_csv('reports/ctta/suta/window_metrics.csv')
wm_n = pd.read_csv('results/stage3_multimodel/wav2vec2_base_suta_order_a/window_metrics.csv')

print("Window metrics comparison:")
for i in range(min(len(wm_h), len(wm_n))):
    row_h = wm_h.iloc[i]
    row_n = wm_n.iloc[i]
    print(f"Win {i:02d}: H_wer={row_h['window_wer']:.4f} N_wer={row_n['window_wer']:.4f} | "
          f"H_cum_wer={row_h['cumulative_wer']:.4f} N_cum_wer={row_n['cumulative_wer']:.4f} | "
          f"H_before={row_h['theta_before_hash'][:8]} N_before={row_n['theta_before_hash'][:8]} | "
          f"H_after={row_h['theta_after_hash'][:8]} N_after={row_n['theta_after_hash'][:8]}")

traj_h = pd.read_csv('reports/ctta/suta/adaptation_trajectory.csv')
traj_n = pd.read_csv('results/stage3_multimodel/wav2vec2_base_suta_order_a/adaptation_trajectory.csv')
print("\nTrajectory cols:", list(traj_h.columns))

print("\nTrajectory comparison:")
for i in range(min(len(traj_h), len(traj_n))):
    th = traj_h.iloc[i]
    tn = traj_n.iloc[i]
    print(f"Traj {i:02d}: H_loss={th['loss']:.6f} N_loss={tn['loss']:.6f} | "
          f"H_ent={th['entropy']:.6f} N_ent={tn['entropy']:.6f} | "
          f"H_div={th['em_divergence']:.6f} N_div={tn['em_divergence']:.6f}")
