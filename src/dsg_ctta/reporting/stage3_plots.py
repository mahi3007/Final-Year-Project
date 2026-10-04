"""
Stage 3 CTTA Discovery Plotting Utilities.
Generates:
1. Overall WER vs Window Trajectory
2. Group WER vs Window Trajectory
3. Disparity D_t vs Window Trajectory
4. Delta_D and Delta_R Dynamics
5. Subgroup Regression Delta_g Distribution across Methods
"""

from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
PALETTE = {
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


def plot_overall_wer_trajectory(
    reports_base_dir: str = "reports/ctta",
    output_path: str = "reports/ctta/figures/overall_wer_trajectory.png"
) -> str:
    """Plot cumulative WER across windows for all four methods on ORDER_A."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    for m in methods:
        csv_p = os.path.join(reports_base_dir, m, "adaptation_trajectory.csv")
        if os.path.exists(csv_p):
            df = pd.read_csv(csv_p)
            ax.plot(
                df["window_id"] + 1,
                df["cumulative_wer"] * 100,
                marker="o",
                label=m.upper(),
                color=PALETTE.get(m, "#000000"),
                linewidth=2.0,
                markersize=5
            )

    ax.set_title("Prequential Overall WER Progression (Track A: wav2vec2_base, ORDER_A)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Adaptation Window $B_t$ (K=4 recordings/window)", fontsize=10)
    ax.set_ylabel("Cumulative Prequential WER (%)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return output_path


def plot_disparity_trajectory(
    reports_base_dir: str = "reports/ctta",
    output_path: str = "reports/ctta/figures/disparity_trajectory.png"
) -> str:
    """Plot cumulative Disparity D across windows for all four methods."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
    for m in methods:
        csv_p = os.path.join(reports_base_dir, m, "adaptation_trajectory.csv")
        if os.path.exists(csv_p):
            df = pd.read_csv(csv_p)
            ax.plot(
                df["window_id"] + 1,
                df["cumulative_disparity"] * 100,
                marker="s",
                label=m.upper(),
                color=PALETTE.get(m, "#000000"),
                linewidth=2.0,
                markersize=5
            )

    ax.set_title("Prequential Disparity $D_t$ Dynamics (Track A: wav2vec2_base, ORDER_A)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Adaptation Window $B_t$ (K=4 recordings/window)", fontsize=10)
    ax.set_ylabel("Prequential Disparity $D_t$ (% points)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return output_path


def plot_group_wer_trajectory_suta(
    reports_base_dir: str = "reports/ctta",
    output_path: str = "reports/ctta/figures/group_wer_trajectory_suta.png"
) -> str:
    """Plot group-level WER trajectory for SUTA."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    csv_p = os.path.join(reports_base_dir, "suta", "adaptation_trajectory.csv")
    if not os.path.exists(csv_p):
        return ""

    df = pd.read_csv(csv_p)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    for g, col in GROUP_COLORS.items():
        col_name = f"wer_group_{g}"
        if col_name in df.columns:
            # Drop NaN or forward fill
            sub_df = df.dropna(subset=[col_name])
            if not sub_df.empty:
                ax.plot(
                    sub_df["window_id"] + 1,
                    sub_df[col_name] * 100,
                    marker="^",
                    label=g,
                    color=col,
                    linewidth=1.8,
                    markersize=5
                )

    ax.set_title("Group-Level WER Trajectories under Continual SUTA (ORDER_A)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Adaptation Window $B_t$", fontsize=10)
    ax.set_ylabel("Group Cumulative WER (%)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0", loc="center left", bbox_to_anchor=(1, 0.5))
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def plot_cross_method_comparison_bar(
    comp_csv_path: str = "reports/ctta/cross_method_comparison.csv",
    output_path: str = "reports/ctta/figures/cross_method_comparison.png"
) -> str:
    """Bar chart comparing overall WER, Disparity, and Max Group Regression across methods."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not os.path.exists(comp_csv_path):
        return ""

    df = pd.read_csv(comp_csv_path)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    x = np.arange(len(df))
    width = 0.25

    ax.bar(x - width, df["corpus_wer"] * 100, width, label="Corpus WER (%)", color="#3182CE")
    ax.bar(x, df["disparity_d"] * 100, width, label="Disparity $D$ (% pts)", color="#DD6B20")
    ax.bar(x + width, df["max_group_regression"] * 100, width, label=r"Max Regr $\max_g \Delta_g$ (%)", color="#E53E3E")

    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in df["method"]], fontweight="bold")
    ax.set_title("Cross-Method Performance & Disparity Summary (ORDER_A)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Percentage / Percentage Points (%)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#E2E8F0")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    return output_path


def generate_all_stage3_figures(reports_base_dir: str = "reports/ctta") -> Dict[str, str]:
    """Generate the full figure suite for Stage 3 report."""
    fig_dir = os.path.join(reports_base_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    paths = {
        "overall_wer": plot_overall_wer_trajectory(reports_base_dir, os.path.join(fig_dir, "overall_wer_trajectory.png")),
        "disparity": plot_disparity_trajectory(reports_base_dir, os.path.join(fig_dir, "disparity_trajectory.png")),
        "group_suta": plot_group_wer_trajectory_suta(reports_base_dir, os.path.join(fig_dir, "group_wer_trajectory_suta.png")),
        "cross_bar": plot_cross_method_comparison_bar(os.path.join(reports_base_dir, "cross_method_comparison.csv"), os.path.join(fig_dir, "cross_method_comparison.png"))
    }
    return paths


if __name__ == "__main__":
    generate_all_stage3_figures()
