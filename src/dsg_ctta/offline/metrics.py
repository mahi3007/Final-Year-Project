"""
Exact Levenshtein distance dynamic programming calculation for ASR error counts.
Provides exact S, D, I, N, WER, and CER with zero external approximation.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel
from dsg_ctta.data.normalization import TextNormalizer


class EditCounts(BaseModel):
    """Exact alignment edit counts."""
    substitutions: int
    deletions: int
    insertions: int
    hits: int
    reference_length: int
    hypothesis_length: int
    wer: float
    cer: float = 0.0

    @property
    def total_errors(self) -> int:
        return self.substitutions + self.deletions + self.insertions


def compute_levenshtein_alignment(
    reference_tokens: List[str],
    hypothesis_tokens: List[str]
) -> Tuple[int, int, int, int]:
    """
    Compute exact Levenshtein alignment between reference and hypothesis tokens.
    
    Returns:
        (substitutions, deletions, insertions, hits)
    """
    R = len(reference_tokens)
    H = len(hypothesis_tokens)

    # DP Matrix: dp[i][j] = (cost, s, d, ins, h)
    dp = [[(0, 0, 0, 0, 0) for _ in range(H + 1)] for _ in range(R + 1)]

    # Initialize boundary conditions
    for i in range(1, R + 1):
        dp[i][0] = (i, 0, i, 0, 0)  # All deletions
    for j in range(1, H + 1):
        dp[0][j] = (j, 0, 0, j, 0)  # All insertions

    for i in range(1, R + 1):
        for j in range(1, H + 1):
            ref_tok = reference_tokens[i - 1]
            hyp_tok = hypothesis_tokens[j - 1]

            if ref_tok == hyp_tok:
                # Match / Hit
                cost_diag, s, d, ins, h = dp[i - 1][j - 1]
                dp[i][j] = (cost_diag, s, d, ins, h + 1)
            else:
                # Sub / Del / Ins choices
                sub_choice = dp[i - 1][j - 1]
                del_choice = dp[i - 1][j]
                ins_choice = dp[i][j - 1]

                c_sub = sub_choice[0] + 1
                c_del = del_choice[0] + 1
                c_ins = ins_choice[0] + 1

                min_c = min(c_sub, c_del, c_ins)

                if min_c == c_sub:
                    dp[i][j] = (c_sub, sub_choice[1] + 1, sub_choice[2], sub_choice[3], sub_choice[4])
                elif min_c == c_del:
                    dp[i][j] = (c_del, del_choice[1], del_choice[2] + 1, del_choice[3], del_choice[4])
                else:
                    dp[i][j] = (c_ins, ins_choice[1], ins_choice[2], ins_choice[3] + 1, ins_choice[4])

    _, s, d, ins, h = dp[R][H]
    return s, d, ins, h


def compute_utterance_metrics(
    reference: str,
    hypothesis: str,
    normalize: bool = True
) -> EditCounts:
    """
    Compute word-level and character-level edit counts and error rates for a single utterance.
    """
    if normalize:
        ref_norm = TextNormalizer.normalize(reference)
        hyp_norm = TextNormalizer.normalize(hypothesis)
    else:
        ref_norm = reference.strip()
        hyp_norm = hypothesis.strip()

    ref_words = ref_norm.split() if ref_norm else []
    hyp_words = hyp_norm.split() if hyp_norm else []

    N = len(ref_words)

    if N == 0:
        if len(hyp_words) == 0:
            wer = 0.0
            s, d, ins, h = 0, 0, 0, 0
        else:
            ins = len(hyp_words)
            s, d, h = 0, 0, 0
            wer = 1.0  # 100% error rate on empty reference with non-empty hypothesis
    else:
        s, d, ins, h = compute_levenshtein_alignment(ref_words, hyp_words)
        wer = (s + d + ins) / N

    # Character-level CER
    ref_chars = list(ref_norm.replace(" ", ""))
    hyp_chars = list(hyp_norm.replace(" ", ""))
    N_c = len(ref_chars)
    if N_c == 0:
        cer = 0.0 if len(hyp_chars) == 0 else 1.0
    else:
        s_c, d_c, ins_c, _ = compute_levenshtein_alignment(ref_chars, hyp_chars)
        cer = (s_c + d_c + ins_c) / N_c

    return EditCounts(
        substitutions=s,
        deletions=d,
        insertions=ins,
        hits=h,
        reference_length=N,
        hypothesis_length=len(hyp_words),
        wer=wer,
        cer=cer
    )
