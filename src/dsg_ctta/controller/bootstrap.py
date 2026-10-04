"""
Stage 5A DSG Controller: Deterministic Paired Speaker-Cluster Bootstrap.
=======================================================================
Implements stratified, paired speaker-level resampling with simultaneous
max-group statistic calculation and strict fail-closed checks.
"""

from __future__ import annotations
import math
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from dsg_ctta.controller.types import BootstrapMetrics
from dsg_ctta.controller.exceptions import (
    InvalidMetricsError,
    InconsistentPairingError,
    EmptySentinelError,
    DegenerateBootstrapError,
)


def run_paired_speaker_bootstrap(
    records_base: List[Dict[str, Any]],
    records_candidate: List[Dict[str, Any]],
    num_replicates: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 20261002,
    min_speakers_per_group: int = 3,
) -> BootstrapMetrics:
    """
    Execute deterministic paired speaker-cluster bootstrap.

    Parameters:
    -----------
    records_base: List of dicts for base model predictions on sentinel.
        Required keys: utterance_id, speaker_id, group_id, substitutions,
                       deletions, insertions, reference_length.
    records_candidate: List of dicts for candidate model predictions on sentinel.
        Must pair 1-to-1 with records_base on utterance_id, speaker_id, group_id.
    num_replicates: Number of bootstrap resamples (default B=1000).
    confidence_level: UCB percentile level (default 0.95).
    seed: RNG seed for reproducible sampling.
    min_speakers_per_group: Minimum independent speaker clusters per stratum (fail-closed if < min).

    Returns:
    --------
    BootstrapMetrics containing point estimates, per-group deltas, and 95% UCBs.
    """
    if not records_base or not records_candidate:
        raise EmptySentinelError("Sentinel evaluation records cannot be empty.")

    if len(records_base) != len(records_candidate):
        raise InconsistentPairingError(
            f"Record length mismatch: base={len(records_base)}, candidate={len(records_candidate)}"
        )

    # 1. Validation & Integrity Check
    required_keys = {"utterance_id", "speaker_id", "group_id", "substitutions", "deletions", "insertions", "reference_length"}
    for idx, (b, c) in enumerate(zip(records_base, records_candidate)):
        for k in required_keys:
            if k not in b or k not in c:
                raise InvalidMetricsError(f"Missing key '{k}' at record index {idx}")

        if b["utterance_id"] != c["utterance_id"]:
            raise InconsistentPairingError(
                f"Utterance ID mismatch at index {idx}: {b['utterance_id']} != {c['utterance_id']}"
            )
        if b["speaker_id"] != c["speaker_id"]:
            raise InconsistentPairingError(
                f"Speaker ID mismatch at index {idx}: {b['speaker_id']} != {c['speaker_id']}"
            )
        if b["group_id"] != c["group_id"]:
            raise InconsistentPairingError(
                f"Group ID mismatch at index {idx}: {b['group_id']} != {c['group_id']}"
            )

        # Check numeric types, NaNs, Infs, and negativity
        for num_key in ("substitutions", "deletions", "insertions", "reference_length"):
            vb, vc = b[num_key], c[num_key]
            if not isinstance(vb, (int, float)) or not isinstance(vc, (int, float)):
                raise InvalidMetricsError(f"Non-numeric metric '{num_key}' at index {idx}")
            if math.isnan(vb) or math.isnan(vc):
                raise InvalidMetricsError(f"NaN detected in '{num_key}' at index {idx}")
            if math.isinf(vb) or math.isinf(vc):
                raise InvalidMetricsError(f"Inf detected in '{num_key}' at index {idx}")
            if vb < 0 or vc < 0:
                raise InvalidMetricsError(f"Negative metric value in '{num_key}' at index {idx}")

        if b["reference_length"] <= 0:
            raise InvalidMetricsError(f"Reference length must be positive at index {idx}")

    df_b = pd.DataFrame(records_base)
    df_c = pd.DataFrame(records_candidate)

    # 2. Check speaker clusters and groups
    groups = sorted(df_b["group_id"].unique().tolist())
    if not groups:
        raise EmptySentinelError("Zero evaluation groups found in sentinel records.")

    spks_by_group: Dict[str, List[str]] = {}
    for g in groups:
        spks_in_g = sorted(df_b[df_b["group_id"] == g]["speaker_id"].unique().tolist())
        if len(spks_in_g) < min_speakers_per_group:
            raise DegenerateBootstrapError(
                f"Stratum '{g}' has only {len(spks_in_g)} speaker clusters; minimum required is {min_speakers_per_group}."
            )
        spks_by_group[g] = spks_in_g

    # 3. Compute empirical point estimates
    b_total_words = df_b["reference_length"].sum()
    c_total_words = df_c["reference_length"].sum()
    b_total_err = df_b["substitutions"].sum() + df_b["deletions"].sum() + df_b["insertions"].sum()
    c_total_err = df_c["substitutions"].sum() + df_c["deletions"].sum() + df_c["insertions"].sum()

    b_overall_wer = b_total_err / b_total_words
    c_overall_wer = c_total_err / c_total_words
    point_delta_r = float(c_overall_wer - b_overall_wer)

    b_group_wers: Dict[str, float] = {}
    c_group_wers: Dict[str, float] = {}
    point_delta_g: Dict[str, float] = {}

    for g in groups:
        bg = df_b[df_b["group_id"] == g]
        cg = df_c[df_c["group_id"] == g]
        bw = (bg["substitutions"].sum() + bg["deletions"].sum() + bg["insertions"].sum()) / bg["reference_length"].sum()
        cw = (cg["substitutions"].sum() + cg["deletions"].sum() + cg["insertions"].sum()) / cg["reference_length"].sum()
        b_group_wers[g] = float(bw)
        c_group_wers[g] = float(cw)
        point_delta_g[g] = float(cw - bw)

    point_max_delta_g = float(max(point_delta_g.values()))
    point_b_disp = float(max(b_group_wers.values()) - min(b_group_wers.values()))
    point_c_disp = float(max(c_group_wers.values()) - min(c_group_wers.values()))
    point_delta_d = float(point_c_disp - point_b_disp)

    # 4. Pre-index speaker records for high-speed bootstrap
    all_speakers = sorted(df_b["speaker_id"].unique().tolist())
    base_spk_data: Dict[str, Tuple[int, int]] = {}      # spk -> (err, words)
    cand_spk_data: Dict[str, Tuple[int, int]] = {}      # spk -> (err, words)
    spk_to_group: Dict[str, str] = {}

    for spk in all_speakers:
        b_sub = df_b[df_b["speaker_id"] == spk]
        c_sub = df_c[df_c["speaker_id"] == spk]
        g = b_sub["group_id"].iloc[0]
        spk_to_group[spk] = g
        b_e = int(b_sub["substitutions"].sum() + b_sub["deletions"].sum() + b_sub["insertions"].sum())
        b_w = int(b_sub["reference_length"].sum())
        c_e = int(c_sub["substitutions"].sum() + c_sub["deletions"].sum() + c_sub["insertions"].sum())
        c_w = int(c_sub["reference_length"].sum())
        base_spk_data[spk] = (b_e, b_w)
        cand_spk_data[spk] = (c_e, c_w)

    # 5. Execute Stratified Paired Speaker-Cluster Bootstrap
    rng = np.random.RandomState(seed)
    replicate_delta_r: List[float] = []
    replicate_max_delta_g: List[float] = []
    replicate_delta_d: List[float] = []
    replicate_group_deltas: Dict[str, List[float]] = {g: [] for g in groups}
    omitted_groups_count = 0

    percentile_rank = confidence_level * 100.0

    for _ in range(num_replicates):
        b_rep_err, b_rep_words = 0, 0
        c_rep_err, c_rep_words = 0, 0

        rep_b_gwers: Dict[str, float] = {}
        rep_c_gwers: Dict[str, float] = {}
        rep_deltas_g: Dict[str, float] = {}

        # Stratified sampling: sample k_g speakers with replacement within each group g
        for g in groups:
            spk_pool = spks_by_group[g]
            k_g = len(spk_pool)
            chosen_spks = rng.choice(spk_pool, size=k_g, replace=True)

            g_b_err, g_b_words = 0, 0
            g_c_err, g_c_words = 0, 0

            for spk in chosen_spks:
                be, bw = base_spk_data[spk]
                ce, cw = cand_spk_data[spk]
                g_b_err += be
                g_b_words += bw
                g_c_err += ce
                g_c_words += cw

            if g_b_words == 0 or g_c_words == 0:
                omitted_groups_count += 1
                raise DegenerateBootstrapError(f"Zero reference words sampled in group '{g}' during replicate.")

            g_b_wer = g_b_err / g_b_words
            g_c_wer = g_c_err / g_c_words
            dg = g_c_wer - g_b_wer

            rep_b_gwers[g] = g_b_wer
            rep_c_gwers[g] = g_c_wer
            rep_deltas_g[g] = dg
            replicate_group_deltas[g].append(dg)

            b_rep_err += g_b_err
            b_rep_words += g_b_words
            c_rep_err += g_c_err
            c_rep_words += g_c_words

        # Replicate overall delta R
        rep_b_wer = b_rep_err / b_rep_words
        rep_c_wer = c_rep_err / c_rep_words
        replicate_delta_r.append(rep_c_wer - rep_b_wer)

        # Simultaneous worst-case group statistic
        replicate_max_delta_g.append(max(rep_deltas_g.values()))

        # Replicate disparity delta
        rep_b_disp = max(rep_b_gwers.values()) - min(rep_b_gwers.values())
        rep_c_disp = max(rep_c_gwers.values()) - min(rep_c_gwers.values())
        replicate_delta_d.append(rep_c_disp - rep_b_disp)

    # 6. Compute Upper Confidence Bounds (UCB95)
    ucb_r = float(np.percentile(replicate_delta_r, percentile_rank))
    ucb_max_group = float(np.percentile(replicate_max_delta_g, percentile_rank))
    ucb_d = float(np.percentile(replicate_delta_d, percentile_rank))

    group_ucbs: Dict[str, float] = {}
    for g in groups:
        group_ucbs[g] = float(np.percentile(replicate_group_deltas[g], percentile_rank))

    return BootstrapMetrics(
        delta_r=point_delta_r,
        max_delta_g=point_max_delta_g,
        delta_d=point_delta_d,
        ucb_r=ucb_r,
        ucb_max_group=ucb_max_group,
        ucb_d=ucb_d,
        group_deltas=point_delta_g,
        group_ucbs=group_ucbs,
        replicates_computed=num_replicates,
        omitted_groups_count=omitted_groups_count,
    )
