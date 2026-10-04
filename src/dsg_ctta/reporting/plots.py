"""
Publication-Quality Visualization Generator for DSG-CTTA Stage 2 Audit.
Produces high-resolution figures for group WERs, disparity metrics, error composition,
and confound-aware GLMM rate ratios.
"""

from __future__ import annotations
import os
from typing import List, Dict, Any
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dsg_ctta.offline.aggregation import GlobalEvaluationSummary
from dsg_ctta.offline.glmm import GLMMModelReport


# Modern publication style palette
ACCENT_COLORS = {
    "Arabic": "#E76F51",
    "Hindi": "#F4A261",
    "Mandarin": "#E9C46A",
    "Korean": "#2A9D8F",
    "Spanish": "#264653",
    "Vietnamese": "#457B9D"
}
MODEL_PALETTE = ["#2B2D42", "#8D99AE", "#D90429", "#EF233C", "#3A86FF", "#8338EC"]


def plot_group_wer_comparison(
    summaries: List[GlobalEvaluationSummary],
    output_path: str = "reports/audit/figures/group_wer_comparison.png"
) -> str:
    """Generate grouped bar plot comparing Group WERs across evaluated ASR models."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    model_names = [s.model_name for s in summaries]
    # Collect all unique groups
    all_groups = sorted(list(set(g for s in summaries for g in s.group_summaries.keys())))
    
    n_groups = len(all_groups)
    n_models = len(model_names)
    
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    x = np.arange(n_groups)
    width = 0.8 / n_models
    
    for i, s in enumerate(summaries):
        wers = [s.group_summaries[g].corpus_wer * 100 if g in s.group_summaries else 0.0 for g in all_groups]
        offset = (i - n_models / 2 + 0.5) * width
        color = MODEL_PALETTE[i % len(MODEL_PALETTE)]
        bars = ax.bar(x + offset, wers, width, label=s.model_name, color=color, alpha=0.9, edgecolor="black", linewidth=0.5)
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.1f}%",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 2),
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=7, rotation=45)

    ax.set_title("Static Cross-Model Accent Group Word Error Rates (Stage 2 Audit)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("L1 Background Accent Group", fontsize=11, fontweight="bold")
    ax.set_ylabel("Corpus WER (%)", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(all_groups, fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="ASR Architecture", title_fontsize=10, fontsize=9, loc="upper right")
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_disparity_comparison(
    summaries: List[GlobalEvaluationSummary],
    output_path: str = "reports/audit/figures/disparity_comparison.png"
) -> str:
    """Generate bar chart of Disparity D (max_g - min_g) across models."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    model_names = [s.model_name for s in summaries]
    disparities = [s.disparity_d * 100 for s in summaries]
    ratios = [(s.max_group_wer / s.min_group_wer) if s.min_group_wer > 0 else 1.0 for s in summaries]
    
    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=300)
    x = np.arange(len(model_names))
    width = 0.4
    
    bars1 = ax1.bar(x - width/2, disparities, width, label="Disparity Range D (max - min %)", color="#D90429", edgecolor="black", linewidth=0.6)
    ax1.set_ylabel("Disparity Range D (% points)", fontsize=11, fontweight="bold", color="#D90429")
    ax1.tick_params(axis="y", labelcolor="#D90429")
    ax1.set_xticks(x)
    ax1.set_xticklabels(model_names, rotation=20, ha="right", fontsize=9, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.3)
    
    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f"{h:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")
                    
    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, ratios, width, label="Disparity Ratio R (max/min)", color="#2B2D42", edgecolor="black", linewidth=0.6)
    ax2.set_ylabel("Disparity Ratio R (max / min)", fontsize=11, fontweight="bold", color="#2B2D42")
    ax2.tick_params(axis="y", labelcolor="#2B2D42")
    
    for bar in bars2:
        h = bar.get_height()
        ax2.annotate(f"{h:.2f}x",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")
                    
    plt.title("Cross-Model Baseline Performance Disparity Audit (Stage 2)", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_error_decomposition(
    summary: GlobalEvaluationSummary,
    output_path: str = "reports/audit/figures/error_composition.png"
) -> str:
    """Generate stacked bar chart of edit distance decomposition (Substitutions, Deletions, Insertions)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    groups = sorted(summary.group_summaries.keys())
    subs = [summary.group_summaries[g].total_substitutions for g in groups]
    dels = [summary.group_summaries[g].total_deletions for g in groups]
    inss = [summary.group_summaries[g].total_insertions for g in groups]
    
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    x = np.arange(len(groups))
    width = 0.55
    
    p1 = ax.bar(x, subs, width, label="Substitutions (S)", color="#E76F51", edgecolor="black", linewidth=0.5)
    p2 = ax.bar(x, dels, width, bottom=subs, label="Deletions (D)", color="#E9C46A", edgecolor="black", linewidth=0.5)
    p3 = ax.bar(x, inss, width, bottom=np.array(subs) + np.array(dels), label="Insertions (I)", color="#2A9D8F", edgecolor="black", linewidth=0.5)
    
    ax.set_title(f"Error Type Decomposition across Global Accents: {summary.model_name}", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Accent Group", fontsize=11, fontweight="bold")
    ax.set_ylabel("Total Edit Operations", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10)
    ax.legend(title="Edit Operation", loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path


def plot_glmm_rate_ratios(
    glmm_report: GLMMModelReport,
    model_name: str,
    output_path: str = "reports/audit/figures/confound_rate_ratios.png"
) -> str:
    """Generate Forest plot showing Rate Ratios and 95% CIs from Poisson/Negative Binomial GLMM."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    coeffs = [c for c in glmm_report.coefficients if "Intercept" not in c.variable]
    if not coeffs:
        return output_path
        
    labels = [c.variable.replace("C(group_id, Treatment(reference='", "").replace("'))[T.", " vs ").replace("]", "") for c in coeffs]
    rrs = [c.rate_ratio for c in coeffs]
    ci_lower = [c.rr_ci_lower_95 for c in coeffs]
    ci_upper = [c.rr_ci_upper_95 for c in coeffs]
    err_low = [rr - l for rr, l in zip(rrs, ci_lower)]
    err_high = [u - rr for rr, u in zip(rrs, ci_upper)]
    
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    y = np.arange(len(labels))
    
    ax.errorbar(rrs, y, xerr=[err_low, err_high], fmt='o', color="#1D3557", ecolor="#E63946", elinewidth=2, capsize=4, capthick=1.5, markersize=7)
    ax.axvline(1.0, color="gray", linestyle="--", alpha=0.7, label="Null Effect (RR = 1.0)")
    
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, fontweight="bold")
    ax.set_xlabel("Rate Ratio (RR) with 95% Wald Confidence Intervals", fontsize=11, fontweight="bold")
    ax.set_title(f"Confound-Aware Poisson GLMM Rate Ratios: {model_name}\n(Controlled for SNR, Speech Rate & Speaker Cluster)", fontsize=11, fontweight="bold", pad=12)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right")
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return output_path
