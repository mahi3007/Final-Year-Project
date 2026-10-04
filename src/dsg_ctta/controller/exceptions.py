"""
Stage 5A DSG Controller: Exception Hierarchy.
============================================
Fail-closed domain exceptions for gate, bootstrap, and shadow candidate operations.
"""

from __future__ import annotations


class DSGException(Exception):
    """Base exception for all Disparity Safety Gate operations."""
    pass


class FailClosedException(DSGException):
    """Base exception indicating an operational defect that forces an automatic REJECT."""
    pass


class InvalidMetricsError(FailClosedException):
    """Raised when evaluation records contain NaN, Inf, missing fields, or malformed counts."""
    pass


class SpeakerLeakageError(FailClosedException):
    """Raised when an adaptation or calibration speaker contaminates the sentinel panel."""
    pass


class EmptySentinelError(FailClosedException):
    """Raised when the sentinel panel contains zero recordings or zero speakers."""
    pass


class DegenerateBootstrapError(FailClosedException):
    """Raised when bootstrap cannot form valid clusters or encounters degenerate degrees of freedom."""
    pass


class InconsistentPairingError(FailClosedException):
    """Raised when base and candidate evaluation records do not match 1-to-1 in order or identity."""
    pass


class ModelMismatchError(FailClosedException):
    """Raised when candidate model architecture or parameter dictionary mismatches base model."""
    pass
