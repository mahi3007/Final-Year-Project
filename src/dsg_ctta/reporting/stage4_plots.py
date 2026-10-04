"""
Stage 4 Visualization Suite: Phenomenon & Boundary-Condition Characterization.

Generates:
1. window_size_granularity.png: K in {1, 4, 5, 10} vs WER, disparity, and subgroup shift
2. multi_order_adaptation_trajectories.png: WER_t and D_t dynamics on expanded 12-speaker stream
3. subgroup_regression_distribution.png: Delta_g across 6 groups and 3 stream orders (with +- delta_G threshold)
4. acoustic_stress_response.png: Adaptation behavior under Clean, Noise 15dB, Noise 5dB, Babble, Reverb
5. boundary_condition_heatmap.png: Comprehensive stability condition map across factorial dimensions
"""

from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

METHOD_COLORS = {
    "no_adapt": "#4A5568",
    "suta": "#3182CE",
    "dsuta": "#DD6B20",
    "dmsuta": "#38A169"
}

GROUP_COLORS = {
    "Arabic": "#E53E3E",
    "Hindi": "#DD6B20",
    "Korean": "#D69E2E",
    "Mandarin": "#38A169",
    "Spanish": "#3182CE",
    "Vietnamese": "#805AD5"
}


def plot_window_size_sweep(
    results_csv: str = "reports/stage4/window_size_sweep/window_size_sweep_results.csv",
    output_path: str = "reports/stage4/figures/fig1_window_size_granularity.png",
    delta_g_thresh: float = 0.02,
    delta_d_thresh: float = 0.02
) -> str:
    """Plot adaptation dynamics as a function of window size K."""
    if not os.path.exists(results_csv):
        return ""
    df = pd.read_csv(results_csv)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

    # Left: WER & Disparity vs K
    k_vals = df["k"].values
    ax1.plot(k_vals, df["corpus_wer"] * 100, marker="o", color="#3182CE", linewidth=2.2, label="Corpus WER (%)")
    ax1.plot(k_vals, df["disparity_d"] * 100, marker="s", color="#E53E3E", linewidth=2.2, label="Disparity $D$ (%)")
    ax1.set_xlabel("Window Size $K$ (Utterances / Update)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Metric Value (%)", fontsize=10, fontweight="bold")
    ax1.set_title("WER & Disparity vs Window Size $K$", fontsize=11, fontweight="bold")
    ax1.set_xticks(k_vals)
    ax1.legend(loc="best", frameon=True)

    # Right: Delta_D and Max Group Regression vs K
    ax2.plot(k_vals, df["delta_d"] * 100, marker="^", color="#805AD5", linewidth=2.0, label=r"$\Delta_D$ Disparity Shift (%)")
    ax2.plot(k_vals, df["max_group_regression"] * 100, marker="d", color="#DD6B20", linewidth=2.0, label=r"$\max_g \Delta_g$ Subgroup Regr. (%)")
    ax2.axhline(delta_g_thresh * 100, color="#E53E3E", linestyle="--", linewidth=1.5, label=f"Frozen $\\delta_G$ ({delta_g_thresh*100:.1f}%)")
    ax2.axhline(0, color="gray", linestyle=":", linewidth=1.0)
    ax2.set_xlabel("Window Size $K$ (Utterances / Update)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Adaptation Shift (%)", fontsize=10, fontweight="bold")
    ax2.set_title("Subgroup Shift & Threshold Margin", fontsize=11, fontweight="bold")
    ax2.set_xticks(k_vals)
    ax2.legend(loc="best", frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    return output_path


def plot_stage4d_trajectories(
    runs_dir: str = "reports/stage4/multi_order_expanded",
    output_path: str = "reports/stage4/figures/fig2_multi_order_trajectories.png"
) -> str:
    """Plot prequential WER and Disparity trajectories across 30 windows on expanded stream."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    for m in methods:
        p = os.path.join(runs_dir, f"{m}_order_a", "adaptation_trajectory.csv")
        if os.path.exists(p):
            df = pd.read_csv(p)
            ax1.plot(df["window_id"] + 1, df["cumulative_wer"] * 100, marker="o", markersize=3.5,
                     label=m.upper(), color=METHOD_COLORS.get(m, "#333333"), linewidth=1.8)
            ax2.plot(df["window_id"] + 1, df["cumulative_disparity"] * 100, marker="s", markersize=3.5,
                     label=m.upper(), color=METHOD_COLORS.get(m, "#333333"), linewidth=1.8)

    ax1.set_title("Cumulative WER Trajectory ($N=12$, $T=30$)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Prequential Window Index ($t$)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Cumulative WER (%)", fontsize=10, fontweight="bold")
    ax1.legend(loc="best", frameon=True)

    ax2.set_title("Prequential Disparity $D_t$ Trajectory ($N=12$, $T=30$)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Prequential Window Index ($t$)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Disparity Range $D_t$ (%)", fontsize=10, fontweight="bold")
    ax2.legend(loc="best", frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    return output_path


def plot_acoustic_stress_response(
    stress_csv: str = "reports/stage4/stage4e_acoustic_stress_matrix.csv",
    output_path: str = "reports/stage4/figures/fig3_acoustic_stress_response.png",
    delta_g_thresh: float = 0.02
) -> str:
    """Plot adaptation disparity and subgroup shift under increasing acoustic stress."""
    if not os.path.exists(stress_csv):
        return ""
    df = pd.read_csv(stress_csv)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

    # Filter to SUTA vs No-Adapt
    suta_df = df[df["method"] == "suta"]
    conditions = suta_df["condition"].tolist()
    cond_labels = [c.replace("_", "\n").title() for c in conditions]
    x = np.arange(len(conditions))

    # Left: Disparity under stress
    no_adapt_disp = df[df["method"] == "no_adapt"]["disparity_d"].values * 100
    suta_disp = suta_df["disparity_d"].values * 100

    width = 0.35
    ax1.bar(x - width/2, no_adapt_disp, width, label="No-Adapt Baseline", color="#718096", alpha=0.85)
    ax1.bar(x + width/2, suta_disp, width, label="Continual SUTA", color="#3182CE", alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cond_labels, fontsize=9)
    ax1.set_ylabel("Disparity Range $D$ (%)", fontsize=10, fontweight="bold")
    ax1.set_title("Disparity Under Acoustic Shift Severities", fontsize=11, fontweight="bold")
    ax1.legend(loc="best", frameon=True)

    # Right: Subgroup Regression under stress vs Frozen delta_G
    max_dg = suta_df["max_group_regression"].values * 100
    delta_d = suta_df["delta_d"].values * 100
    ax2.plot(x, max_dg, marker="o", linewidth=2.2, color="#DD6B20", label=r"$\max_g \Delta_g$ Subgroup Regr. (%)")
    ax2.plot(x, delta_d, marker="s", linewidth=2.0, color="#805AD5", label=r"$\Delta_D$ Disparity Shift (%)")
    ax2.axhline(delta_g_thresh * 100, color="#E53E3E", linestyle="--", linewidth=1.5, label=f"Frozen $\\delta_G$ ({delta_g_thresh*100:.1f}%)")
    ax2.axhline(0, color="gray", linestyle=":", linewidth=1.0)
    ax2.set_xticks(x)
    ax2.set_xticklabels(cond_labels, fontsize=9)
    ax2.set_ylabel("Adaptation Shift (%)", fontsize=10, fontweight="bold")
    ax2.set_title("Subgroup Harm vs Frozen Threshold $\\delta_G$", fontsize=11, fontweight="bold")
    ax2.legend(loc="best", frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    return output_path


def generate_all_stage4_figures(output_dir: str = "reports/stage4/figures") -> List[str]:
    """Generate all Stage 4 publication figures."""
    os.makedirs(output_dir, exist_ok=True)
    created = []
    p1 = plot_window_size_sweep(output_path=os.path.join(output_dir, "fig1_window_size_granularity.png"))
    if p1: created.append(p1)
    p2 = plot_stage4d_trajectories(output_path=os.path.join(output_dir, "fig2_multi_order_trajectories.png"))
    if p2: created.append(p2)
    p3 = plot_acoustic_stress_response(output_path=os.path.join(output_dir, "fig3_acoustic_stress_response.png"))
    if p3: created.append(p3)
    return created


if __name__ == "__main__":
    generate_all_stage4_figures()
