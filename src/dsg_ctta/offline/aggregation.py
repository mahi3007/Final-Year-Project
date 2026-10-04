"""
ASR metric aggregation module.
Computes corpus WER, speaker-macro WER, group WER, group regression, and disparity metrics.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from dsg_ctta.offline.metrics import EditCounts, compute_utterance_metrics


class GroupEvaluationSummary(BaseModel):
    """Evaluation summary for a single speech group."""
    group_id: str
    num_speakers: int
    num_utterances: int
    total_reference_words: int
    total_substitutions: int
    total_deletions: int
    total_insertions: int
    corpus_wer: float
    speaker_macro_wer: float
    mean_cer: float


class GlobalEvaluationSummary(BaseModel):
    """Complete evaluation report for a model checkpoint across a partition."""
    model_name: str
    partition_name: str
    total_speakers: int
    total_utterances: int
    total_reference_words: int
    total_substitutions: int
    total_deletions: int
    total_insertions: int
    corpus_wer: float
    speaker_macro_wer: float
    mean_cer: float
    group_summaries: Dict[str, GroupEvaluationSummary]
    min_group_wer: float
    max_group_wer: float
    disparity_d: float  # max_g - min_g
    best_group_id: str
    worst_group_id: str
    speaker_wers: Dict[str, float] = Field(default_factory=dict)


class AdaptationDeltaSummary(BaseModel):
    """Measures prequential adaptation changes between theta and candidate theta'."""
    base_model_name: str
    adapted_model_name: str
    delta_r_corpus_wer: float  # WER(theta') - WER(theta)
    delta_r_speaker_macro_wer: float
    group_deltas: Dict[str, float]  # Delta_g per group
    max_group_regression: float  # max_g Delta_g
    regressed_groups: List[str]
    improved_groups: List[str]
    initial_disparity_d: float
    adapted_disparity_d: float
    delta_d: float  # D(theta') - D(theta)
    is_disparity_amplified: bool


def aggregate_partition_evaluation(
    evaluation_records: List[Dict[str, Any]],
    model_name: str = "wav2vec2_base",
    partition_name: str = "final_test"
) -> GlobalEvaluationSummary:
    """
    Aggregate individual utterance evaluation records into comprehensive group and corpus summaries.
    
    Each record must have:
    - 'speaker_id'
    - 'group_id'
    - 'substitutions'
    - 'deletions'
    - 'insertions'
    - 'reference_length'
    - 'wer'
    - 'cer'
    """
    if not evaluation_records:
        raise ValueError("Cannot aggregate empty evaluation records.")

    df = pd.DataFrame(evaluation_records)

    # Global totals
    tot_s = int(df["substitutions"].sum())
    tot_d = int(df["deletions"].sum())
    tot_i = int(df["insertions"].sum())
    tot_n = int(df["reference_length"].sum())

    corpus_wer = (tot_s + tot_d + tot_i) / tot_n if tot_n > 0 else 0.0
    mean_cer = float(df["cer"].mean())

    # Speaker-level WER aggregation
    spk_groups = df.groupby("speaker_id")
    speaker_wers = {}
    for spk_id, spk_df in spk_groups:
        s_s = spk_df["substitutions"].sum()
        s_d = spk_df["deletions"].sum()
        s_i = spk_df["insertions"].sum()
        s_n = spk_df["reference_length"].sum()
        spk_wer = (s_s + s_d + s_i) / s_n if s_n > 0 else 0.0
        speaker_wers[spk_id] = float(spk_wer)

    speaker_macro_wer = float(np.mean(list(speaker_wers.values())))

    # Group-level aggregations
    group_summaries = {}
    for grp_id, grp_df in df.groupby("group_id"):
        g_s = int(grp_df["substitutions"].sum())
        g_d = int(grp_df["deletions"].sum())
        g_i = int(grp_df["insertions"].sum())
        g_n = int(grp_df["reference_length"].sum())
        g_corpus_wer = (g_s + g_d + g_i) / g_n if g_n > 0 else 0.0

        # Group speaker-macro WER
        g_spk_wers = [speaker_wers[s] for s in grp_df["speaker_id"].unique() if s in speaker_wers]
        g_spk_macro = float(np.mean(g_spk_wers)) if g_spk_wers else g_corpus_wer

        group_summaries[grp_id] = GroupEvaluationSummary(
            group_id=grp_id,
            num_speakers=len(grp_df["speaker_id"].unique()),
            num_utterances=len(grp_df),
            total_reference_words=g_n,
            total_substitutions=g_s,
            total_deletions=g_d,
            total_insertions=g_i,
            corpus_wer=g_corpus_wer,
            speaker_macro_wer=g_spk_macro,
            mean_cer=float(grp_df["cer"].mean())
        )

    # Disparity calculation D = max_g WER_g - min_g WER_g
    group_wers = {gid: summary.corpus_wer for gid, summary in group_summaries.items()}
    best_grp = min(group_wers, key=group_wers.get)
    worst_grp = max(group_wers, key=group_wers.get)
    min_wer = group_wers[best_grp]
    max_wer = group_wers[worst_grp]
    disparity_d = max_wer - min_wer

    return GlobalEvaluationSummary(
        model_name=model_name,
        partition_name=partition_name,
        total_speakers=len(speaker_wers),
        total_utterances=len(df),
        total_reference_words=tot_n,
        total_substitutions=tot_s,
        total_deletions=tot_d,
        total_insertions=tot_i,
        corpus_wer=corpus_wer,
        speaker_macro_wer=speaker_macro_wer,
        mean_cer=mean_cer,
        group_summaries=group_summaries,
        min_group_wer=min_wer,
        max_group_wer=max_wer,
        disparity_d=disparity_d,
        best_group_id=best_grp,
        worst_group_id=worst_grp,
        speaker_wers=speaker_wers
    )


def compute_adaptation_delta(
    base_summary: GlobalEvaluationSummary,
    adapted_summary: GlobalEvaluationSummary
) -> AdaptationDeltaSummary:
    """
    Compute adaptation delta statistics:
    Delta_R = WER_overall(theta') - WER_overall(theta)
    Delta_g = WER_g(theta') - WER_g(theta)
    Delta_D = D(theta') - D(theta)
    """
    delta_r_corpus = adapted_summary.corpus_wer - base_summary.corpus_wer
    delta_r_macro = adapted_summary.speaker_macro_wer - base_summary.speaker_macro_wer

    group_deltas = {}
    regressed = []
    improved = []

    for grp_id, base_g in base_summary.group_summaries.items():
        if grp_id in adapted_summary.group_summaries:
            adapt_g = adapted_summary.group_summaries[grp_id]
            d_g = adapt_g.corpus_wer - base_g.corpus_wer
            group_deltas[grp_id] = float(d_g)
            if d_g > 1e-4:
                regressed.append(grp_id)
            elif d_g < -1e-4:
                improved.append(grp_id)

    max_reg = max(group_deltas.values()) if group_deltas else 0.0
    delta_d = adapted_summary.disparity_d - base_summary.disparity_d

    return AdaptationDeltaSummary(
        base_model_name=base_summary.model_name,
        adapted_model_name=adapted_summary.model_name,
        delta_r_corpus_wer=float(delta_r_corpus),
        delta_r_speaker_macro_wer=float(delta_r_macro),
        group_deltas=group_deltas,
        max_group_regression=float(max_reg),
        regressed_groups=regressed,
        improved_groups=improved,
        initial_disparity_d=base_summary.disparity_d,
        adapted_disparity_d=adapted_summary.disparity_d,
        delta_d=float(delta_d),
        is_disparity_amplified=(delta_d > 1e-4)
    )
