"""
Stage 5A Disparity Safety Gate (DSG) Controller Package.
========================================================
Implements risk-controlled candidate update safety monitoring for continual test-time adaptation.
"""

from dsg_ctta.controller.types import (
    GateDecision,
    BootstrapMetrics,
    GroupRegressionMetrics,
)
from dsg_ctta.controller.exceptions import (
    DSGException,
    FailClosedException,
    InvalidMetricsError,
    SpeakerLeakageError,
    EmptySentinelError,
    DegenerateBootstrapError,
    InconsistentPairingError,
    ModelMismatchError,
)
from dsg_ctta.controller.bootstrap import run_paired_speaker_bootstrap
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.shadow import (
    ShadowCandidateManager,
    compute_model_parameter_hash,
)
from dsg_ctta.controller.evaluator import SentinelSafetyEvaluator
from dsg_ctta.controller.resolver import (
    SentinelAudioResolver,
    SentinelAudioResolutionError,
)

__all__ = [
    "GateDecision",
    "BootstrapMetrics",
    "GroupRegressionMetrics",
    "DSGException",
    "FailClosedException",
    "InvalidMetricsError",
    "SpeakerLeakageError",
    "EmptySentinelError",
    "DegenerateBootstrapError",
    "InconsistentPairingError",
    "ModelMismatchError",
    "run_paired_speaker_bootstrap",
    "DisparitySafetyGate",
    "ShadowCandidateManager",
    "compute_model_parameter_hash",
    "SentinelSafetyEvaluator",
    "SentinelAudioResolver",
    "SentinelAudioResolutionError",
]

