"""
Prequential evaluation stream generator for Stage 3 CTTA Discovery.
Enforces the strict temporal order:
  B_t -> Predict(theta_t) -> Record predictions -> Offline eval (hidden labels) -> Adapt(unlabeled B_t) -> theta_(t+1)
Supports deterministic pre-registered stream orderings:
  ORDER_A: Arabic -> Hindi -> Korean -> Mandarin -> Spanish -> Vietnamese
  ORDER_B: Vietnamese -> Spanish -> Mandarin -> Korean -> Hindi -> Arabic
  ORDER_C: Hindi -> Mandarin -> Arabic -> Vietnamese -> Korean -> Spanish
  NATURAL: Original file sequence in split
"""

from __future__ import annotations
import hashlib
from typing import List, Tuple, Generator, Dict, Any, Optional
from pydantic import BaseModel, Field
from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.online.label_isolation import UnlabeledAudioBatch, LabelIsolationSanitizer


# Canonical Pre-Registered Accent Group Orderings
ORDER_A_GROUPS = ["Arabic", "Hindi", "Korean", "Mandarin", "Spanish", "Vietnamese"]
ORDER_B_GROUPS = ["Vietnamese", "Spanish", "Mandarin", "Korean", "Hindi", "Arabic"]
ORDER_C_GROUPS = ["Hindi", "Mandarin", "Arabic", "Vietnamese", "Korean", "Spanish"]


def order_utterances(
    utterances: List[UtteranceMetadata],
    ordering_id: str = "ORDER_A"
) -> List[UtteranceMetadata]:
    """
    Sort utterances according to a deterministic, pre-registered ordering protocol.
    Within each accent group, recordings are sorted deterministically by utterance_id.
    """
    ordering_id_upper = ordering_id.upper()
    if ordering_id_upper == "NATURAL":
        return list(utterances)

    if ordering_id_upper == "ORDER_A":
        group_priority = {g: i for i, g in enumerate(ORDER_A_GROUPS)}
    elif ordering_id_upper == "ORDER_B":
        group_priority = {g: i for i, g in enumerate(ORDER_B_GROUPS)}
    elif ordering_id_upper == "ORDER_C":
        group_priority = {g: i for i, g in enumerate(ORDER_C_GROUPS)}
    else:
        raise ValueError(
            f"Unsupported ordering_id '{ordering_id}'. "
            f"Supported orderings are: ['ORDER_A', 'ORDER_B', 'ORDER_C', 'NATURAL']"
        )

    # Sort primarily by group order, then deterministically by utterance_id
    sorted_utts = sorted(
        utterances,
        key=lambda u: (group_priority.get(u.group_id, 999), u.utterance_id)
    )
    return sorted_utts


class PrequentialPredictionRecord(BaseModel):
    """
    Prequential prediction produced by live model theta_t before any adaptation on B_t.
    Does NOT contain ground truth or evaluation metrics.
    """
    batch_idx: int
    utterance_id: str
    hypothesis_raw: str
    model_version_at_prediction: str
    inference_time_seconds: float = 0.0


class PrequentialStream:
    """
    Manages prequential data windows with strict label isolation and stream provenance.
    Guarantees deterministic stream sequence and reproducible stream hash.
    """

    def __init__(
        self,
        utterances: List[UtteranceMetadata],
        window_size_k: int = 4,
        ordering_id: str = "ORDER_A",
        stream_id: Optional[str] = None,
        seed: int = 42
    ):
        self.ordering_id = ordering_id
        self.seed = seed
        self.window_size_k = window_size_k
        self.ordered_utterances = order_utterances(utterances, ordering_id=ordering_id)
        self.total_utterances = len(self.ordered_utterances)
        self.total_batches = (self.total_utterances + window_size_k - 1) // window_size_k

        if stream_id is None:
            self.stream_id = f"stream_{self.ordering_id.lower()}_k{window_size_k}_s{seed}"
        else:
            self.stream_id = stream_id

        self.stream_hash = self._compute_stream_hash()

    def _compute_stream_hash(self) -> str:
        """Compute deterministic SHA-256 hash across the ordered sequence of utterance IDs."""
        utt_ids = [u.utterance_id for u in self.ordered_utterances]
        content = f"{self.stream_id}:{self.ordering_id}:{self.window_size_k}:{self.seed}:{','.join(utt_ids)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def generate_windows(
        self
    ) -> Generator[Tuple[int, List[UtteranceMetadata], UnlabeledAudioBatch], None, None]:
        """
        Yields (batch_idx, ground_truth_utterances_for_offline_eval, isolated_unlabeled_batch).
        The ground_truth_utterances are retained offline and NEVER passed to online adaptation.
        """
        for i in range(0, self.total_utterances, self.window_size_k):
            batch_idx = i // self.window_size_k
            batch_utts = self.ordered_utterances[i : i + self.window_size_k]
            unlabeled_batch = LabelIsolationSanitizer.sanitize_batch(batch_utts, batch_idx)
            yield batch_idx, batch_utts, unlabeled_batch
