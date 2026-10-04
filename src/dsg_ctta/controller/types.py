"""
Stage 5A DSG Controller: Core Type Definitions and Decision Containers.
======================================================================
Strict, immutable types for DSG decisions, bootstrap outcomes, and metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json


@dataclass(frozen=True)
class GroupRegressionMetrics:
    """Per-group regression metrics for a single stratum."""
    group_id: str
    baseline_wer: float
    candidate_wer: float
    delta_g: float
    ucb_g: float


@dataclass(frozen=True)
class BootstrapMetrics:
    """Statistical summary across B bootstrap replicates."""
    delta_r: float
    max_delta_g: float
    delta_d: float
    ucb_r: float
    ucb_max_group: float
    ucb_d: float
    group_deltas: Dict[str, float]
    group_ucbs: Dict[str, float]
    replicates_computed: int
    omitted_groups_count: int


@dataclass(frozen=True)
class GateDecision:
    """
    Immutable gate decision record.
    Every decision retains full provenance, bounds, tolerances, and reasons.
    """
    decision: str                         # "ACCEPT" or "REJECT"
    accept: bool                          # True iff ACCEPT
    delta_r: float                        # Empirical point estimate of overall WER change
    delta_g: Dict[str, float]             # Empirical point estimates of per-group WER change
    max_delta_g: float                    # Empirical max_g Delta_g
    delta_d: float                        # Empirical point estimate of disparity change
    ucb_r: float                          # 95% Upper Confidence Bound for Delta_R
    ucb_max_group: float                  # 95% Upper Confidence Bound for max_g Delta_g
    ucb_d: float                          # 95% Upper Confidence Bound for Delta_D
    epsilon_r: float                      # Operating tolerance for overall risk
    epsilon_g: float                      # Operating tolerance for subgroup regression
    epsilon_d: float                      # Operating tolerance for disparity growth
    rejection_reasons: List[str]          # Empty if ACCEPT, otherwise specific constraint violations
    candidate_identifier: str            # Identifier / hash of candidate model theta'
    current_model_identifier: str        # Identifier / hash of current live model theta_t
    bootstrap_seed: int                   # RNG seed used for bootstrap
    bootstrap_b: int                      # Number of bootstrap replicates (e.g. 1000)
    timestamp: str                        # ISO 8601 timestamp of evaluation
    decision_reason: str = "ACCEPTED"     # "ACCEPTED", "STATISTICAL_GATE_REJECTION", or "FAIL_CLOSED_EVALUATOR_ERROR"
    rejection_category: Optional[str] = None  # None if ACCEPT, else "STATISTICAL_GATE_REJECTION" or "FAIL_CLOSED_EVALUATOR_ERROR"

    def to_dict(self) -> Dict:
        """Deterministic dictionary serialization."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Deterministic JSON string serialization."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
