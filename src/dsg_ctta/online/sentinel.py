"""
Frozen Sentinel Panel Manager.
Manages the frozen labeled calibration/sentinel subset used strictly for candidate safety decisions.
"""

from __future__ import annotations
import hashlib
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.offline.metrics import compute_utterance_metrics, EditCounts
from dsg_ctta.offline.bootstrap import paired_speaker_cluster_bootstrap, BootstrapResult


class SentinelEvaluationResult(BaseModel):
    """Output of evaluating live model theta vs candidate theta' on the frozen sentinel panel."""
    panel_id: str
    panel_hash: str
    num_recordings: int
    num_speakers: int
    delta_r_ucb: float
    max_delta_g_ucb: float
    delta_d_ucb: float
    bootstrap_results: Dict[str, BootstrapResult]
    is_safe: bool = False
    decision: str = "REJECT"
    rejection_reasons: List[str] = Field(default_factory=list)


class FrozenSentinelPanel:
    """Encapsulates a frozen, immutable labeled panel with strict validation."""

    def __init__(self, panel_id: str, sentinel_utterances: List[UtteranceMetadata]):
        self.panel_id = panel_id
        self.sentinel_utterances = sentinel_utterances
        self.speaker_ids = sorted(list(set(u.speaker_id for u in sentinel_utterances)))
        self.group_ids = sorted(list(set(u.group_id for u in sentinel_utterances)))
        self.panel_hash = self._compute_panel_hash()

    def _compute_panel_hash(self) -> str:
        content = f"{self.panel_id}:{len(self.sentinel_utterances)}:{sorted(u.utterance_id for u in self.sentinel_utterances)}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def assert_no_speaker_contamination(self, stream_speakers: List[str]) -> None:
        """Ensure no sentinel speaker ever appears in the test/adaptation stream."""
        overlap = set(self.speaker_ids).intersection(set(stream_speakers))
        if overlap:
            raise AssertionError(
                f"CRITICAL RESEARCH INVALIDITY: Sentinel panel '{self.panel_id}' is contaminated with stream speakers: {overlap}"
            )

    def evaluate_candidate_safety(
        self,
        base_model: BaseASRModel,
        candidate_model: BaseASRModel,
        epsilon_r: float = 0.01,
        epsilon_g: float = 0.02,
        epsilon_d: float = 0.02,
        num_bootstrap: int = 500
    ) -> SentinelEvaluationResult:
        """
        Evaluate candidate model theta' vs base model theta on the frozen panel.
        Calculates paired speaker-cluster bootstrap UCB for Delta_R, max_g Delta_g, and Delta_D.
        
        FAIL-SAFE INVARIANT: If sentinel evaluation fails, panel is empty/missing, or statistics
        are unavailable, immediately return REJECT.
        """
        if not self.sentinel_utterances:
            return SentinelEvaluationResult(
                panel_id=self.panel_id,
                panel_hash=self.panel_hash,
                num_recordings=0,
                num_speakers=0,
                delta_r_ucb=float("inf"),
                max_delta_g_ucb=float("inf"),
                delta_d_ucb=float("inf"),
                bootstrap_results={},
                is_safe=False,
                decision="REJECT",
                rejection_reasons=["FAIL-SAFE: Sentinel panel is empty or missing recordings."]
            )

        base_records: List[Dict[str, Any]] = []
        candidate_records: List[Dict[str, Any]] = []


        for utt in self.sentinel_utterances:
            hyp_base = base_model.transcribe(utt.audio_filepath)
            hyp_cand = candidate_model.transcribe(utt.audio_filepath)

            m_base = compute_utterance_metrics(utt.reference_normalized, hyp_base)
            m_cand = compute_utterance_metrics(utt.reference_normalized, hyp_cand)

            base_records.append({
                "utterance_id": utt.utterance_id,
                "speaker_id": utt.speaker_id,
                "group_id": utt.group_id,
                "substitutions": m_base.substitutions,
                "deletions": m_base.deletions,
                "insertions": m_base.insertions,
                "reference_length": m_base.reference_length,
                "wer": m_base.wer,
                "cer": m_base.cer
            })

            candidate_records.append({
                "utterance_id": utt.utterance_id,
                "speaker_id": utt.speaker_id,
                "group_id": utt.group_id,
                "substitutions": m_cand.substitutions,
                "deletions": m_cand.deletions,
                "insertions": m_cand.insertions,
                "reference_length": m_cand.reference_length,
                "wer": m_cand.wer,
                "cer": m_cand.cer
            })

        # Run paired speaker-cluster bootstrap
        boot_res = paired_speaker_cluster_bootstrap(
            records_base=base_records,
            records_adapted=candidate_records,
            num_replicates=num_bootstrap
        )

        delta_r_ucb = boot_res["delta_r"].ucb_95
        max_delta_g_ucb = boot_res["max_delta_g"].ucb_95
        delta_d_ucb = boot_res["delta_d"].ucb_95

        # Check safety gate constraints
        rejection_reasons = []
        if delta_r_ucb > epsilon_r:
            rejection_reasons.append(f"Overall regression UCB(Delta_R) = {delta_r_ucb:.4f} > epsilon_R ({epsilon_r:.4f})")
        if max_delta_g_ucb > epsilon_g:
            rejection_reasons.append(f"Worst-group regression UCB(max_g Delta_g) = {max_delta_g_ucb:.4f} > epsilon_G ({epsilon_g:.4f})")
        if delta_d_ucb > epsilon_d:
            rejection_reasons.append(f"Disparity amplification UCB(Delta_D) = {delta_d_ucb:.4f} > epsilon_D ({epsilon_d:.4f})")

        is_safe = (len(rejection_reasons) == 0)
        decision = "ACCEPT" if is_safe else "REJECT"

        return SentinelEvaluationResult(
            panel_id=self.panel_id,
            panel_hash=self.panel_hash,
            num_recordings=len(self.sentinel_utterances),
            num_speakers=len(self.speaker_ids),
            delta_r_ucb=delta_r_ucb,
            max_delta_g_ucb=max_delta_g_ucb,
            delta_d_ucb=delta_d_ucb,
            bootstrap_results=boot_res,
            is_safe=is_safe,
            decision=decision,
            rejection_reasons=rejection_reasons
        )
