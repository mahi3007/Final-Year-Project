"""
Paired speaker-cluster bootstrap confidence interval and UCB module.
Implements non-parametric cluster resampling at the speaker level for robust statistical inference.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel


class BootstrapResult(BaseModel):
    """Container for bootstrap estimate and confidence intervals."""
    metric_name: str
    point_estimate: float
    bootstrap_mean: float
    bootstrap_std: float
    ci_lower_95: float
    ci_upper_95: float
    ucb_95: float  # 95th percentile Upper Confidence Bound


def paired_speaker_cluster_bootstrap(
    records_base: List[Dict[str, Any]],
    records_adapted: Optional[List[Dict[str, Any]]] = None,
    num_replicates: int = 1000,
    seed: int = 42,
    alpha: float = 0.05
) -> Dict[str, BootstrapResult]:
    """
    Perform paired speaker-cluster bootstrap.
    
    If records_adapted is provided, computes bootstrap distributions for:
    - Delta_R (overall WER change)
    - Delta_g (per-group WER change)
    - max_g Delta_g (maximum group regression computed within each replicate)
    - Delta_D (disparity change)
    
    If records_adapted is None, computes bootstrap distributions for baseline:
    - Overall corpus WER
    - Per-group WER
    - Disparity D
    """
    rng = np.random.RandomState(seed)

    df_base = pd.DataFrame(records_base)
    is_paired = records_adapted is not None
    if is_paired:
        df_adapt = pd.DataFrame(records_adapted)
        assert len(df_base) == len(df_adapt), "Base and adapted records must have identical lengths."
        assert (df_base["utterance_id"] == df_adapt["utterance_id"]).all(), "Utterance IDs must match exactly."

    unique_speakers = sorted(df_base["speaker_id"].unique().tolist())
    n_speakers = len(unique_speakers)

    # Pre-index speaker sub-dataframes for fast resampling
    base_spk_map = {spk: df_base[df_base["speaker_id"] == spk] for spk in unique_speakers}
    if is_paired:
        adapt_spk_map = {spk: df_adapt[df_adapt["speaker_id"] == spk] for spk in unique_speakers}

    all_groups = sorted(df_base["group_id"].unique().tolist())

    # Accumulator lists
    replicate_corpus_wers = []
    replicate_group_wers = {g: [] for g in all_groups}
    replicate_disparities = []

    # Paired accumulator lists
    replicate_delta_r = []
    replicate_delta_g = {g: [] for g in all_groups}
    replicate_max_delta_g = []
    replicate_delta_d = []

    for _ in range(num_replicates):
        # Resample speaker IDs with replacement
        resampled_spks = rng.choice(unique_speakers, size=n_speakers, replace=True)

        resampled_base_dfs = [base_spk_map[s] for s in resampled_spks]
        b_df = pd.concat(resampled_base_dfs, ignore_index=True)

        # Baseline metrics
        b_n = b_df["reference_length"].sum()
        b_err = b_df["substitutions"].sum() + b_df["deletions"].sum() + b_df["insertions"].sum()
        b_wer = b_err / b_n if b_n > 0 else 0.0
        replicate_corpus_wers.append(b_wer)

        b_gwers = {}
        for g in all_groups:
            g_df = b_df[b_df["group_id"] == g]
            gn = g_df["reference_length"].sum()
            gerr = g_df["substitutions"].sum() + g_df["deletions"].sum() + g_df["insertions"].sum()
            gwer = gerr / gn if gn > 0 else 0.0
            replicate_group_wers[g].append(gwer)
            b_gwers[g] = gwer

        b_disp = max(b_gwers.values()) - min(b_gwers.values()) if b_gwers else 0.0
        replicate_disparities.append(b_disp)

        if is_paired:
            resampled_adapt_dfs = [adapt_spk_map[s] for s in resampled_spks]
            a_df = pd.concat(resampled_adapt_dfs, ignore_index=True)

            a_n = a_df["reference_length"].sum()
            a_err = a_df["substitutions"].sum() + a_df["deletions"].sum() + a_df["insertions"].sum()
            a_wer = a_err / a_n if a_n > 0 else 0.0

            d_r = a_wer - b_wer
            replicate_delta_r.append(d_r)

            a_gwers = {}
            current_rep_deltas = {}
            for g in all_groups:
                g_a_df = a_df[a_df["group_id"] == g]
                g_an = g_a_df["reference_length"].sum()
                g_aerr = g_a_df["substitutions"].sum() + g_a_df["deletions"].sum() + g_a_df["insertions"].sum()
                g_awer = g_aerr / g_an if g_an > 0 else 0.0
                a_gwers[g] = g_awer

                dg = g_awer - b_gwers[g]
                replicate_delta_g[g].append(dg)
                current_rep_deltas[g] = dg

            max_dg = max(current_rep_deltas.values()) if current_rep_deltas else 0.0
            replicate_max_delta_g.append(max_dg)

            a_disp = max(a_gwers.values()) - min(a_gwers.values()) if a_gwers else 0.0
            d_d = a_disp - b_disp
            replicate_delta_d.append(d_d)

    # Compute summary statistics
    results: Dict[str, BootstrapResult] = {}

    def _summarize(name: str, values: List[float]) -> BootstrapResult:
        arr = np.array(values)
        pt = float(np.mean(arr))
        return BootstrapResult(
            metric_name=name,
            point_estimate=pt,
            bootstrap_mean=float(np.mean(arr)),
            bootstrap_std=float(np.std(arr, ddof=1)),
            ci_lower_95=float(np.percentile(arr, (alpha / 2.0) * 100)),
            ci_upper_95=float(np.percentile(arr, (1.0 - alpha / 2.0) * 100)),
            ucb_95=float(np.percentile(arr, (1.0 - alpha) * 100))
        )

    results["corpus_wer"] = _summarize("corpus_wer", replicate_corpus_wers)
    for g in all_groups:
        results[f"group_wer_{g}"] = _summarize(f"group_wer_{g}", replicate_group_wers[g])
    results["disparity_d"] = _summarize("disparity_d", replicate_disparities)

    if is_paired:
        results["delta_r"] = _summarize("delta_r", replicate_delta_r)
        for g in all_groups:
            results[f"delta_g_{g}"] = _summarize(f"delta_g_{g}", replicate_delta_g[g])
        results["max_delta_g"] = _summarize("max_delta_g", replicate_max_delta_g)
        results["delta_d"] = _summarize("delta_d", replicate_delta_d)

    return results
