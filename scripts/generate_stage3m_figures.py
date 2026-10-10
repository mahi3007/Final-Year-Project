"""
Generate Publication-Quality Figures for Stage 3M Multi-Model Extension
Standard: ADR-005 / Protocol v1.1.0-model-expansion
Outputs: reports/stage3m/figures/
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_CSV = PROJECT_ROOT / "results" / "stage3_multimodel" / "stage3m_full_results.csv"
FIG_DIR = PROJECT_ROOT / "reports" / "stage3m" / "figures"


def setup_style():
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight"
    })


def plot_stage3m_figures():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    assert RESULTS_CSV.exists(), f"Results CSV not found: {RESULTS_CSV}"
    df = pd.read_csv(RESULTS_CSV)
    setup_style()
    
    # -------------------------------------------------------------
    # Figure 1: Static Baseline Comparison (All 6 Models)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Filter static / no-adapt (ORDER_A)
    static_df = df[(df["method"] == "no_adapt") & (df["ordering_id"].str.startswith("ORDER_A"))].copy()
    static_df = static_df.sort_values(by="corpus_wer", ascending=True)
    
    colors = ["#2b5c8f" if arch == "CTC" else "#2e7d32" for arch in static_df["architecture"]]
    
    bars1 = ax1.barh(static_df["model_key"], static_df["corpus_wer"] * 100, color=colors, alpha=0.85, edgecolor="black")
    ax1.set_xlabel("Word Error Rate (WER %)")
    ax1.set_title("Zero-Shot Baseline WER across 6 Models")
    ax1.set_xlim(0, 100)
    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 1.5, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va="center", fontsize=9, fontweight="bold")
        
    bars2 = ax2.barh(static_df["model_key"], static_df["disparity_d"] * 100, color=colors, alpha=0.85, edgecolor="black")
    ax2.set_xlabel("Accent Disparity D (% points)")
    ax2.set_title("Initial Subgroup Disparity D (Max - Min WER)")
    ax2.set_xlim(0, 45)
    for bar in bars2:
        w = bar.get_width()
        ax2.text(w + 0.8, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va="center", fontsize=9, fontweight="bold")
        
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2b5c8f", edgecolor="black", label="CTC Development Models (Adapted in CTTA)"),
        Patch(facecolor="#2e7d32", edgecolor="black", label="Seq2Seq Controls (Static Portability Only)")
    ]
    fig.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=True)
    
    plt.tight_layout()
    fig1_path = FIG_DIR / "fig3m_1_static_baseline_comparison.png"
    plt.savefig(fig1_path)
    plt.close()
    print(f"Generated: {fig1_path}")
    
    # -------------------------------------------------------------
    # Figure 2: Model x Method Overall Delta_R vs Max Subgroup Delta_g
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    
    # Filter CTC adaptation methods (suta, dsuta, dmsuta) averaged across orders
    ctc_adapt = df[df["method"].isin(["suta", "dsuta", "dmsuta"])].copy()
    
    agg_df = ctc_adapt.groupby(["model_key", "method"])[["delta_r", "max_delta_g", "delta_d"]].mean().reset_index()
    
    models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
    methods = ["suta", "dsuta", "dmsuta"]
    x = np.arange(len(models))
    width = 0.25
    
    method_colors = {
        "suta": "#d32f2f",     # Red (Unchecked SUTA)
        "dsuta": "#f57c00",    # Orange (Restorative DSUTA)
        "dmsuta": "#1976d2"   # Blue (Mean-anchored DMSUTA)
    }
    
    for i, m in enumerate(methods):
        sub = agg_df[agg_df["method"] == m].set_index("model_key").reindex(models)
        offset = (i - 1) * width
        rects1 = ax1.bar(x + offset, sub["delta_r"] * 100, width, label=m.upper(), color=method_colors[m], alpha=0.85, edgecolor="black")
        rects2 = ax2.bar(x + offset, sub["max_delta_g"] * 100, width, label=m.upper(), color=method_colors[m], alpha=0.85, edgecolor="black")
        
        # Labels
        for rect in rects1:
            h = rect.get_height()
            ax1.text(rect.get_x() + rect.get_width()/2., h + (0.5 if h >= 0 else -1.5), f"{h:+.1f}%", ha="center", va="bottom" if h < 0 else "top", fontsize=8, fontweight="bold")
        for rect in rects2:
            h = rect.get_height()
            ax2.text(rect.get_x() + rect.get_width()/2., h + 0.5, f"{h:+.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")
            
    ax1.set_ylabel("Mean Overall WER Change ΔR (% points)")
    ax1.set_title("Overall Adaptation Impact (ΔR)\n(Negative = Improvement)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax1.legend(loc="upper left")
    
    ax2.set_ylabel("Mean Max Subgroup Regression max_g Δg (% points)")
    ax2.set_title("Subgroup Degradation Risk (max_g Δg)\n(Positive = Disproportionate Harm)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(models)
    ax2.axhline(2.0, color="crimson", linestyle=":", linewidth=1.2, label="Harm Threshold δ_G (+2.0%)")
    ax2.legend(loc="upper right")
    
    plt.tight_layout()
    fig2_path = FIG_DIR / "fig3m_2_model_method_deltas.png"
    plt.savefig(fig2_path)
    plt.close()
    print(f"Generated: {fig2_path}")
    
    # -------------------------------------------------------------
    # Figure 3: Stream Order Trajectory & Stability Analysis
    # -------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    
    order_markers = {"ORDER_A": "o", "ORDER_B": "s", "ORDER_C": "^"}
    
    for idx, model_name in enumerate(models):
        ax = axes[idx]
        m_df = df[df["model_key"] == model_name].copy()
        
        for ord_id in ["ORDER_A", "ORDER_B", "ORDER_C"]:
            sub_ord = m_df[m_df["ordering_id"] == ord_id].set_index("method").reindex(["no_adapt", "suta", "dsuta", "dmsuta"])
            ax.plot(["No-Adapt", "SUTA", "DSUTA", "DMSUTA"], sub_ord["corpus_wer"] * 100, 
                    marker=order_markers[ord_id], linewidth=2, markersize=7, label=ord_id, alpha=0.85)
            
        ax.set_title(f"{model_name}")
        ax.set_xlabel("Adaptation Method")
        if idx == 0:
            ax.set_ylabel("Stream Final WER (%)")
        ax.legend(loc="upper left")
        
    plt.suptitle("Stream-Order Sensitivity across CTTA Methods (ORDER_A vs ORDER_B vs ORDER_C)", fontsize=13, y=1.02)
    plt.tight_layout()
    fig3_path = FIG_DIR / "fig3m_3_stream_order_sensitivity.png"
    plt.savefig(fig3_path)
    plt.close()
    print(f"Generated: {fig3_path}")
    
    print("All Stage 3M figures generated successfully.")


if __name__ == "__main__":
    plot_stage3m_figures()
