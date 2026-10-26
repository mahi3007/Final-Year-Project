"""
Stage 6M Statistical Evaluation and Inferential Analysis Package.
Implements speaker-clustered paired bootstrap inference, Holm multiplicity adjustments,
and frozen protocol decision rules under Protocol v1.4.0.
"""

from dsg_ctta.evaluation.paired_cluster_inference import (
    ConfirmatoryAnalysisReport,
    CriterionResult,
    run_confirmatory_paired_cluster_inference,
)

__all__ = [
    "ConfirmatoryAnalysisReport",
    "CriterionResult",
    "run_confirmatory_paired_cluster_inference",
]
