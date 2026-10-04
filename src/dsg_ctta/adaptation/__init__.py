"""
Test-Time Adaptation (TTA / CTTA) package for ASR.
Contains adapters for:
- No-Adaptation Control (no_adapt)
- SUTA (Single-Utterance Test-Time Adaptation)
- DSUTA (Dynamic Continual SUTA)
- DMSUTA (Dynamic Model-Bank SUTA)
"""

from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.adaptation.no_adapt import NoAdaptationAdapter
from dsg_ctta.adaptation.suta import SutaAdapter
from dsg_ctta.adaptation.dsuta import DsutaAdapter
from dsg_ctta.adaptation.dmsuta import DmsutaAdapter

__all__ = [
    "BaseTestTimeAdapter",
    "AdaptationStepResult",
    "NoAdaptationAdapter",
    "SutaAdapter",
    "DsutaAdapter",
    "DmsutaAdapter"
]
