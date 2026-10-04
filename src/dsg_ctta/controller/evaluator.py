"""
Stage 5A DSG Controller: Sentinel Panel Safety Evaluator.
========================================================
Coordinates evaluation of candidate model versus live model on the frozen sentinel panel.
Executes paired speaker-cluster bootstrap and delivers formal GateDecision with fail-closed safety.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional

from dsg_ctta.controller.types import GateDecision, BootstrapMetrics
from dsg_ctta.controller.exceptions import FailClosedException
from dsg_ctta.controller.bootstrap import run_paired_speaker_bootstrap
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.shadow import compute_model_parameter_hash


class SentinelSafetyEvaluator:
    """
    Evaluates candidate model safety against current live model on a frozen sentinel panel.
    Guarantees strict fail-closed safety semantics.
    """

    def __init__(
        self,
        gate: DisparitySafetyGate,
        num_bootstrap: int = 1000,
        confidence_level: float = 0.95,
        bootstrap_seed: int = 20261002,
        min_speakers_per_group: int = 3,
        resolver: Optional[Any] = None,
    ):
        self.gate = gate
        self.num_bootstrap = int(num_bootstrap)
        self.confidence_level = float(confidence_level)
        self.bootstrap_seed = int(bootstrap_seed)
        self.min_speakers_per_group = int(min_speakers_per_group)
        self.resolver = resolver

    def evaluate_records(
        self,
        records_live: List[Dict[str, Any]],
        records_candidate: List[Dict[str, Any]],
        candidate_identifier: str = "candidate_theta_prime",
        live_identifier: str = "live_theta_t",
    ) -> GateDecision:
        """
        Evaluate candidate safety directly from pre-computed utterance prediction records.
        Useful for unit tests, synthetic contract verification, and offline replays.
        """
        try:
            bootstrap_metrics = run_paired_speaker_bootstrap(
                records_base=records_live,
                records_candidate=records_candidate,
                num_replicates=self.num_bootstrap,
                confidence_level=self.confidence_level,
                seed=self.bootstrap_seed,
                min_speakers_per_group=self.min_speakers_per_group,
            )
            return self.gate.evaluate_decision(
                bootstrap_metrics=bootstrap_metrics,
                candidate_identifier=candidate_identifier,
                current_model_identifier=live_identifier,
                bootstrap_seed=self.bootstrap_seed,
                bootstrap_b=self.num_bootstrap,
            )
        except Exception as exc:
            # Strict fail-closed policy: any error forces REJECT
            return self.gate.evaluate_decision(
                bootstrap_metrics=None,
                candidate_identifier=candidate_identifier,
                current_model_identifier=live_identifier,
                bootstrap_seed=self.bootstrap_seed,
                bootstrap_b=self.num_bootstrap,
                exception_msg=str(exc),
            )

    def evaluate_candidate(
        self,
        live_model: Any,
        candidate_model: Any,
        sentinel_utterances: List[Any],
        transcribe_fn: Optional[Any] = None,
        metric_fn: Optional[Any] = None,
    ) -> GateDecision:
        """
        Transcribe sentinel utterances with live model and candidate model,
        compute word error counts, and evaluate safety.
        Guarantees that neither live_model nor candidate_model is mutated during evaluation.
        """
        live_hash_pre = compute_model_parameter_hash(live_model)
        cand_hash_pre = compute_model_parameter_hash(candidate_model)

        records_live: List[Dict[str, Any]] = []
        records_cand: List[Dict[str, Any]] = []

        try:
            if not sentinel_utterances:
                raise ValueError("Sentinel utterances collection is empty.")

            for utt in sentinel_utterances:
                if isinstance(utt, dict):
                    utt_id = str(utt.get("utterance_id") or utt.get("sentinel_id") or "sentinel_utt")
                    spk_id = str(utt.get("speaker_id", "unknown_spk"))
                    grp_id = str(utt.get("group_id") or utt.get("stage5_accent_group", "unknown_grp"))
                    audio_path = str(utt.get("audio_filepath") or utt.get("audio_path", ""))
                    ref_norm = str(utt.get("reference_normalized") or utt.get("transcript", ""))
                else:
                    utt_id = getattr(utt, "utterance_id", str(utt))
                    spk_id = getattr(utt, "speaker_id", "unknown_spk")
                    grp_id = getattr(utt, "group_id", getattr(utt, "stage5_accent_group", "unknown_grp"))
                    audio_path = getattr(utt, "audio_filepath", getattr(utt, "audio_path", ""))
                    ref_norm = getattr(utt, "reference_normalized", getattr(utt, "transcript", ""))

                # Resolve audio path canonically
                if self.resolver is not None:
                    target_audio = str(self.resolver.resolve(utt))
                else:
                    target_audio = audio_path

                # Transcribe
                if transcribe_fn is not None:
                    hyp_live = transcribe_fn(live_model, target_audio)
                    hyp_cand = transcribe_fn(candidate_model, target_audio)
                elif hasattr(live_model, "transcribe") and hasattr(candidate_model, "transcribe"):
                    hyp_live = live_model.transcribe(target_audio)
                    hyp_cand = candidate_model.transcribe(target_audio)
                else:
                    raise AttributeError("Models must implement .transcribe(path) or transcribe_fn provided.")

                # Compute word error counts
                if metric_fn is not None:
                    m_live = metric_fn(ref_norm, hyp_live)
                    m_cand = metric_fn(ref_norm, hyp_cand)
                else:
                    # Fallback word-level edit distance
                    from dsg_ctta.offline.metrics import compute_utterance_metrics
                    m_live = compute_utterance_metrics(ref_norm, hyp_live)
                    m_cand = compute_utterance_metrics(ref_norm, hyp_cand)

                records_live.append({
                    "utterance_id": utt_id,
                    "speaker_id": spk_id,
                    "group_id": grp_id,
                    "substitutions": m_live.substitutions,
                    "deletions": m_live.deletions,
                    "insertions": m_live.insertions,
                    "reference_length": m_live.reference_length,
                })
                records_cand.append({
                    "utterance_id": utt_id,
                    "speaker_id": spk_id,
                    "group_id": grp_id,
                    "substitutions": m_cand.substitutions,
                    "deletions": m_cand.deletions,
                    "insertions": m_cand.insertions,
                    "reference_length": m_cand.reference_length,
                })

            decision = self.evaluate_records(
                records_live=records_live,
                records_candidate=records_cand,
                candidate_identifier=cand_hash_pre[:16],
                live_identifier=live_hash_pre[:16],
            )
        except Exception as exc:
            decision = self.gate.evaluate_decision(
                bootstrap_metrics=None,
                candidate_identifier=cand_hash_pre[:16],
                current_model_identifier=live_hash_pre[:16],
                bootstrap_seed=self.bootstrap_seed,
                bootstrap_b=self.num_bootstrap,
                exception_msg=str(exc),
            )

        # Invariant check: Models must be bit-for-bit unchanged after evaluation
        live_hash_post = compute_model_parameter_hash(live_model)
        cand_hash_post = compute_model_parameter_hash(candidate_model)
        assert live_hash_pre == live_hash_post, "CRITICAL: Live model mutated during sentinel evaluation!"
        assert cand_hash_pre == cand_hash_post, "CRITICAL: Candidate model mutated during sentinel evaluation!"

        return decision
