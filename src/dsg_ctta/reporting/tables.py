"""
Report generation and table formatting utilities for ASR baseline and disparity audits.
"""

from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
from dsg_ctta.offline.aggregation import GlobalEvaluationSummary
from dsg_ctta.offline.glmm import GLMMModelReport


def generate_baseline_summary_table_md(summaries: List[GlobalEvaluationSummary]) -> str:
    """Generate markdown table comparing models across global and disparity metrics."""
    headers = [
        "Model Name",
        "Corpus WER (%)",
        "Spk-Macro WER (%)",
        "Mean CER (%)",
        "Min Group WER (%)",
        "Max Group WER (%)",
        "Disparity D (%)",
        "Best Group",
        "Worst Group"
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for s in summaries:
        row = [
            f"`{s.model_name}`",
            f"{s.corpus_wer * 100:.2f}%",
            f"{s.speaker_macro_wer * 100:.2f}%",
            f"{s.mean_cer * 100:.2f}%",
            f"{s.min_group_wer * 100:.2f}%",
            f"{s.max_group_wer * 100:.2f}%",
            f"**{s.disparity_d * 100:.2f}%**",
            s.best_group_id,
            s.worst_group_id
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def generate_group_breakdown_table_md(summary: GlobalEvaluationSummary) -> str:
    """Generate detailed group-by-group markdown table for a single model."""
    headers = [
        "Group ID",
        "Speakers",
        "Utterances",
        "Ref Words",
        "Substitutions",
        "Deletions",
        "Insertions",
        "Corpus WER (%)",
        "Spk-Macro WER (%)",
        "Mean CER (%)"
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for gid, g in sorted(summary.group_summaries.items()):
        row = [
            f"**{gid}**",
            str(g.num_speakers),
            str(g.num_utterances),
            str(g.total_reference_words),
            str(g.total_substitutions),
            str(g.total_deletions),
            str(g.total_insertions),
            f"{g.corpus_wer * 100:.2f}%",
            f"{g.speaker_macro_wer * 100:.2f}%",
            f"{g.mean_cer * 100:.2f}%"
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def generate_glmm_report_table_md(glmm_report: GLMMModelReport) -> str:
    """Generate markdown table for GLMM regression coefficients and Rate Ratios."""
    headers = [
        "Variable",
        "Estimate (beta)",
        "Std. Error",
        "z-stat",
        "p-value",
        "Holm-adj p-value",
        "Rate Ratio (RR)",
        "95% CI (RR)"
    ]
    lines = [
        f"**Model Family:** {glmm_report.model_family} | **Formula:** `{glmm_report.formula}`",
        f"**Observations:** {glmm_report.num_observations} | **Speakers:** {glmm_report.num_speakers} | **Dispersion:** {glmm_report.dispersion_statistic:.3f} (Overdispersed: {glmm_report.is_overdispersed})",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]

    for c in glmm_report.coefficients:
        sig = "***" if c.p_value_adjusted < 0.001 else "**" if c.p_value_adjusted < 0.01 else "*" if c.p_value_adjusted < 0.05 else ""
        row = [
            f"`{c.variable}`",
            f"{c.beta:.4f}",
            f"{c.std_err:.4f}",
            f"{c.z_stat:.3f}",
            f"{c.p_value:.4e}",
            f"**{c.p_value_adjusted:.4e}** {sig}",
            f"**{c.rate_ratio:.3f}**",
            f"[{c.rr_ci_lower_95:.3f}, {c.rr_ci_upper_95:.3f}]"
        ]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append(f"> **Raw Group Disparity Rate Ratio:** {glmm_report.raw_group_disparity_rr:.3f}x")
    lines.append(f"> **Adjusted Group Disparity Rate Ratio (Controlled for SNR, Speech Rate, Device):** {glmm_report.adjusted_group_disparity_rr:.3f}x")

    return "\n".join(lines)
