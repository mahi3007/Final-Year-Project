"""
Stage 5A DSG Controller: Disparity Safety Gate Decision Logic.
==============================================================
Enforces the canonical ADR-005 tripartite UCB safety criteria:
ACCEPT iff UCB95(Delta_R) <= epsilon_R
       and UCB95(max_g Delta_g) <= epsilon_G
       and UCB95(Delta_D) <= epsilon_D
Otherwise REJECT.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from dsg_ctta.controller.types import GateDecision, BootstrapMetrics
from dsg_ctta.controller.exceptions import FailClosedException


class DisparitySafetyGate:
    """
    Risk-controlled candidate update safety gate.
    Evaluates bootstrap upper confidence bounds against frozen operating tolerances.

    UNIT CONTRACT SPECIFICATION:
    - Canonical Internal Representation: FRACTIONAL RATE DIFFERENCES (unbounded finite scale).
      Example: epsilon_r = 0.0000 (0.00 pp), epsilon_g = 0.0200 (2.00 pp), epsilon_d = 0.0200 (2.00 pp).
    - Human-Readable Reporting Representation: PERCENTAGE POINTS (pp, unbounded finite scale).
      Exact invariant: value_pp == value_fraction * 100.0, value_fraction == value_pp / 100.0.
    - Domain: Open-ended finite real numbers. Because Word Error Rate (WER = (S + D + I) / N) includes insertions,
      WER can exceed 1.0 (100%), and differences (Delta_R, max_g Delta_g, Delta_D, and UCBs) can exceed +1.0 (+100 pp)
      or fall below -1.0 (-100 pp). The gate accepts all finite real numbers without magnitude clipping.
    """

    def __init__(
        self,
        epsilon_r: float = 0.0000,
        epsilon_g: float = 0.0200,
        epsilon_d: float = 0.0200,
    ):
        """Initialize gate with fractional rate tolerances (default: 0.0000, 0.0200, 0.0200)."""
        self.epsilon_r = float(epsilon_r)
        self.epsilon_g = float(epsilon_g)
        self.epsilon_d = float(epsilon_d)

    @classmethod
    def from_percentage_points(
        cls,
        epsilon_r_pp: float = 0.0000,
        epsilon_g_pp: float = 2.0000,
        epsilon_d_pp: float = 2.0000,
    ) -> DisparitySafetyGate:
        """
        Initialize gate from percentage-point tolerances (e.g. 2.00 pp -> 0.0200 frac).
        Ensures exact mathematical equivalence between fractional and percentage-point specifications.
        """
        return cls(
            epsilon_r=float(epsilon_r_pp) / 100.0,
            epsilon_g=float(epsilon_g_pp) / 100.0,
            epsilon_d=float(epsilon_d_pp) / 100.0,
        )

    @staticmethod
    def decision_to_percentage_points(decision: GateDecision) -> Dict[str, Any]:
        """Convert a fractional GateDecision to human-readable percentage points."""
        return {
            "decision": decision.decision,
            "accept": decision.accept,
            "delta_r_pp": decision.delta_r * 100.0 if not math.isnan(decision.delta_r) else float("nan"),
            "max_delta_g_pp": decision.max_delta_g * 100.0 if not math.isnan(decision.max_delta_g) else float("nan"),
            "delta_d_pp": decision.delta_d * 100.0 if not math.isnan(decision.delta_d) else float("nan"),
            "ucb_r_pp": decision.ucb_r * 100.0 if not math.isnan(decision.ucb_r) else float("nan"),
            "ucb_max_group_pp": decision.ucb_max_group * 100.0 if not math.isnan(decision.ucb_max_group) else float("nan"),
            "ucb_d_pp": decision.ucb_d * 100.0 if not math.isnan(decision.ucb_d) else float("nan"),
            "epsilon_r_pp": decision.epsilon_r * 100.0,
            "epsilon_g_pp": decision.epsilon_g * 100.0,
            "epsilon_d_pp": decision.epsilon_d * 100.0,
            "rejection_reasons": list(decision.rejection_reasons),
            "rejection_category": decision.rejection_category,
        }


    def evaluate_decision(
        self,
        bootstrap_metrics: Optional[BootstrapMetrics],
        candidate_identifier: str,
        current_model_identifier: str,
        bootstrap_seed: int,
        bootstrap_b: int,
        exception_msg: Optional[str] = None,
    ) -> GateDecision:
        """
        Evaluate candidate safety given bootstrap metrics.
        Strict fail-closed policy: any missing metric, NaN, Inf, or exception results in REJECT.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        rejection_reasons: List[str] = []

        if exception_msg is not None:
            rejection_reasons.append(f"FAIL-CLOSED: Evaluator exception occurred: {exception_msg}")

        if bootstrap_metrics is None:
            if not rejection_reasons:
                rejection_reasons.append("FAIL-CLOSED: Bootstrap metrics are missing (None).")
            return GateDecision(
                decision="REJECT",
                accept=False,
                delta_r=float("nan"),
                delta_g={},
                max_delta_g=float("nan"),
                delta_d=float("nan"),
                ucb_r=float("inf"),
                ucb_max_group=float("inf"),
                ucb_d=float("inf"),
                epsilon_r=self.epsilon_r,
                epsilon_g=self.epsilon_g,
                epsilon_d=self.epsilon_d,
                rejection_reasons=rejection_reasons,
                candidate_identifier=candidate_identifier,
                current_model_identifier=current_model_identifier,
                bootstrap_seed=bootstrap_seed,
                bootstrap_b=bootstrap_b,
                timestamp=now_ts,
                decision_reason="FAIL_CLOSED_EVALUATOR_ERROR",
                rejection_category="FAIL_CLOSED_EVALUATOR_ERROR",
            )

        # 1. NaN and Inf Checks (Evaluator numerical integrity)
        evaluator_error = False
        for name, val in [
            ("delta_r", bootstrap_metrics.delta_r),
            ("max_delta_g", bootstrap_metrics.max_delta_g),
            ("delta_d", bootstrap_metrics.delta_d),
            ("ucb_r", bootstrap_metrics.ucb_r),
            ("ucb_max_group", bootstrap_metrics.ucb_max_group),
            ("ucb_d", bootstrap_metrics.ucb_d),
        ]:
            if math.isnan(val):
                rejection_reasons.append(f"FAIL-CLOSED: Metric '{name}' is NaN.")
                evaluator_error = True
            elif math.isinf(val):
                rejection_reasons.append(f"FAIL-CLOSED: Metric '{name}' is infinite.")
                evaluator_error = True

        # Check group deltas
        for g, val in bootstrap_metrics.group_deltas.items():
            if math.isnan(val) or math.isinf(val):
                rejection_reasons.append(f"FAIL-CLOSED: Group metric for '{g}' is NaN/Inf.")
                evaluator_error = True

        # 2. Check tripartite bounds (only if no numerical corruption detected)
        statistical_violation = False
        if not evaluator_error:
            if bootstrap_metrics.ucb_r > self.epsilon_r:
                rejection_reasons.append(
                    f"Overall risk violation: UCB95(Delta_R) = {bootstrap_metrics.ucb_r:.4f} > epsilon_R ({self.epsilon_r:.4f})"
                )
                statistical_violation = True
            if bootstrap_metrics.ucb_max_group > self.epsilon_g:
                rejection_reasons.append(
                    f"Subgroup regression violation: UCB95(max_g Delta_g) = {bootstrap_metrics.ucb_max_group:.4f} > epsilon_G ({self.epsilon_g:.4f})"
                )
                statistical_violation = True
            if bootstrap_metrics.ucb_d > self.epsilon_d:
                rejection_reasons.append(
                    f"Disparity growth violation: UCB95(Delta_D) = {bootstrap_metrics.ucb_d:.4f} > epsilon_D ({self.epsilon_d:.4f})"
                )
                statistical_violation = True

        accept = len(rejection_reasons) == 0
        decision_str = "ACCEPT" if accept else "REJECT"

        if accept:
            decision_reason = "ACCEPTED"
            rejection_cat = None
        elif evaluator_error:
            decision_reason = "FAIL_CLOSED_EVALUATOR_ERROR"
            rejection_cat = "FAIL_CLOSED_EVALUATOR_ERROR"
        else:
            decision_reason = "STATISTICAL_GATE_REJECTION"
            rejection_cat = "STATISTICAL_GATE_REJECTION"

        return GateDecision(
            decision=decision_str,
            accept=accept,
            delta_r=bootstrap_metrics.delta_r,
            delta_g=dict(bootstrap_metrics.group_deltas),
            max_delta_g=bootstrap_metrics.max_delta_g,
            delta_d=bootstrap_metrics.delta_d,
            ucb_r=bootstrap_metrics.ucb_r,
            ucb_max_group=bootstrap_metrics.ucb_max_group,
            ucb_d=bootstrap_metrics.ucb_d,
            epsilon_r=self.epsilon_r,
            epsilon_g=self.epsilon_g,
            epsilon_d=self.epsilon_d,
            rejection_reasons=rejection_reasons,
            candidate_identifier=candidate_identifier,
            current_model_identifier=current_model_identifier,
            bootstrap_seed=bootstrap_seed,
            bootstrap_b=bootstrap_b,
            timestamp=now_ts,
            decision_reason=decision_reason,
            rejection_category=rejection_cat,
        )
