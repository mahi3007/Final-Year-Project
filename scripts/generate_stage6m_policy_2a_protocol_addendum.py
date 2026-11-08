#!/usr/bin/env python3
"""
Generator script for Document A: Stage 6M Policy 2A Protocol Addendum (DRAFT).
Protocol: Stage 6M v1.5 Five-Stratum Research Benchmark
Governing Branch: stage6m-five-stratum-parity
Reference Commit: baee3b8381389ffde38e907dc137623748c254a8

Emits:
- reports/stage6m/stage6m_policy_2a_protocol_addendum.json
- reports/stage6m/stage6m_policy_2a_protocol_addendum.md
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("policy_2a_addendum")

ROOT_DIR = Path.cwd()
REPORTS_DIR = ROOT_DIR / "reports" / "stage6m"
DATASETS_DIR = ROOT_DIR / "datasets"
SPLITS_DIR = DATASETS_DIR / "splits"

JSON_OUTPUT_PATH = REPORTS_DIR / "stage6m_policy_2a_protocol_addendum.json"
MD_OUTPUT_PATH = REPORTS_DIR / "stage6m_policy_2a_protocol_addendum.md"

def build_protocol_addendum_data() -> Dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "metadata": {
            "document_id": "STAGE6M_PROTOCOL_ADDENDUM_POLICY_2A",
            "document_title": "Stage 6M Protocol Addendum: Policy 2A Physical Integrity & Decodability Benchmark Specification",
            "governing_protocol": "Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)",
            "governing_branch": "stage6m-five-stratum-parity",
            "reference_commit": "baee3b8381389ffde38e907dc137623748c254a8",
            "timestamp_utc": timestamp,
            "document_status": "APPROVED_PROTOCOL_ADDENDUM (Executed under Gate 1 by Project Lead)",
            "governance_classification": "Academic Honours / Thesis Protocol Addendum (Officially Adopted)",
            "project_lead": "Venkata Akhil Kumar",
            "authoritative_notice": (
                "This document is an APPROVED protocol addendum formally executed by the Project Lead (Venkata Akhil Kumar) "
                "on 2026-11-07 under Gate 1 (Scientific Admission Decision Record). Policy 2A is formally adopted as the "
                "governing scientific admission policy for the Stage 6M v1.5 benchmark. Crucially, Gate 1 authorizes solely "
                "the formal scientific admission criteria and target dataset definition; it does NOT authorize Task 7.7.4 "
                "implementation, audio mutations, manifest locking, or GPU CTTA execution. Task 7.7.4 requires a separate, "
                "explicit Gate 2 authorization."
            )
        },
        "section_1_target_population_and_research_scope": {
            "target_population_definition": (
                "The target speech audio population for the Stage 6M confirmatory benchmark is defined strictly as the "
                "speech recordings of Mozilla Common Voice 27.0 (en) as distributed, packaged, and accessible to the "
                "scientific community, possessing valid MPEG bitstream synchronization and clean PCM decodability."
            ),
            "scientific_objective": (
                "To evaluate whether Dynamic Spectral Guidance (DSG) provides statistically significant Word Error Rate (WER) "
                "reductions and cross-accent disparity safety during Continuous Test-Time Adaptation (CTTA) on real-world, "
                "community-contributed natural speech audio without incurring catastrophic accent-specific regression."
            ),
            "four_level_audio_integrity_distinction": {
                "level_1_current_file_structural_integrity": {
                    "dimension": "Current-File Structural Validity Through Observed EOF",
                    "technical_definition": "All available recording files passed the documented MPEG structural checks through their observed file boundaries (valid frame sync headers 0xFFE/0xFFF to EOF, uncorrupted frame synchronization, and complete physical container structure). This does not establish completeness relative to an original recording session or master recording.",
                    "empirical_status": "VERIFIED (18,975 of 18,975 recordings, 100.0%)"
                },
                "level_2_full_file_decoder_pcm_success": {
                    "dimension": "Full-File Decoder / PCM Success",
                    "technical_definition": "Clean, finite floating-point PCM decompression without decoding errors or aborts. Verified file-by-file via SoundFile (libmpg123) for all 18,845 accepted recordings in reports/stage6m/stage6m_cohort3_task772b_validator_impact_assessment.json, and verified file-by-file across three independent decoders (SoundFile, PyAV, miniaudio) with sample-exact agreement for all 130 discrepancy-screened recordings in reports/stage6m/stage6m_cohort3_task771_mp3_forensic_triage.json. Full 3-decoder verification across all 18,845 recordings is scheduled under Task 7.7.4 materialization.",
                    "empirical_status": "VERIFIED (18,975 of 18,975 recordings: 18,845 via SoundFile/libmpg123; 130 via 3-way multi-decoder exact match)"
                },
                "level_3_completeness_relative_to_original_masters": {
                    "dimension": "Completeness Relative to Original Masters (Claim B)",
                    "technical_definition": "Absence of upstream audio shortening or client-side truncation relative to the uncompressed original microphone capture prior to MP3 compression.",
                    "empirical_status": "UNVERIFIED FOR ALL 18,975 RECORDINGS (Authoritative original masters are unavailable in Common Voice 27.0)"
                },
                "level_4_recording_stage_acoustic_clipping": {
                    "dimension": "Recording-Stage Acoustic Clipping",
                    "technical_definition": "Saturation or non-linear distortion occurring at the contributor's physical microphone diaphragm or ADC during the physical recording event.",
                    "empirical_status": "PHYSICALLY IRRECOVERABLE (Cannot be disproven even if an uncompressed master were available)"
                }
            },
            "evidentiary_status_statement": (
                "Current-file structural integrity and PCM decoding have been evaluated using the documented validation "
                "procedures. Original-source completeness relative to the uncompressed master recordings remains unverified "
                "for all 18,975 recordings because authoritative master references are unavailable. The 130 quarantined "
                "recordings additionally have documented duration-estimation discrepancies, which are not, by themselves, "
                "proof of physical truncation."
            ),
            "negative_evidentiary_boundary": (
                "Clean decoding and current-file integrity do NOT prove complete original recording capture or zero recording "
                "truncation. An audio file can decode cleanly to PCM even if audio was previously shortened at a valid MPEG "
                "frame boundary prior to distribution. Under Policy 2A, the dissertation explicitly discloses that Claim B "
                "remains unverified across all 18,975 recordings."
            )
        },
        "section_2_preservation_of_registered_balanced_design": {
            "design_principle": "Strict adherence to the registered balanced five-stratum experimental design authorized under Section 14.7.",
            "confirmatory_strata_count": 5,
            "strata_names": [
                "Australian English",
                "Canadian English",
                "England English",
                "South Asian English",
                "United States English"
            ],
            "evaluation_speakers_per_stratum": 220,
            "total_evaluation_speakers": 1100,
            "clips_per_evaluation_speaker": 15,
            "total_evaluation_clips": 16500,
            "gate_reference_panel": {
                "total_speakers": 100,
                "speakers_per_stratum": 20,
                "clips_per_speaker": 15,
                "total_clips": 1500,
                "role": "Exclusively calibrate adaptation gating and candidate model acceptance; strictly isolated from evaluation estimands."
            },
            "reserve_replacement_pool": {
                "total_speakers": 65,
                "stratum": "Australian English",
                "clips_per_speaker": 15,
                "total_clips": 975,
                "role": "Dedicated Australian English replacement pool; strictly preserved and isolated."
            },
            "total_cohort3_audio_assets": 18975,
            "cohort_balance_table": [
                {"stratum": "Australian English", "eval_speakers": 220, "eval_clips": 3300, "gate_speakers": 20, "gate_clips": 300, "reserve_speakers": 65, "reserve_clips": 975, "total_clips": 4575},
                {"stratum": "Canadian English", "eval_speakers": 220, "eval_clips": 3300, "gate_speakers": 20, "gate_clips": 300, "reserve_speakers": 0, "reserve_clips": 0, "total_clips": 3600},
                {"stratum": "England English", "eval_speakers": 220, "eval_clips": 3300, "gate_speakers": 20, "gate_clips": 300, "reserve_speakers": 0, "reserve_clips": 0, "total_clips": 3600},
                {"stratum": "South Asian English", "eval_speakers": 220, "eval_clips": 3300, "gate_speakers": 20, "gate_clips": 300, "reserve_speakers": 0, "reserve_clips": 0, "total_clips": 3600},
                {"stratum": "United States English", "eval_speakers": 220, "eval_clips": 3300, "gate_speakers": 20, "gate_clips": 300, "reserve_speakers": 0, "reserve_clips": 0, "total_clips": 3600},
                {"stratum": "Total Confirmatory Cohort", "eval_speakers": 1100, "eval_clips": 16500, "gate_speakers": 100, "gate_clips": 1500, "reserve_speakers": 65, "reserve_clips": 975, "total_clips": 18975}
            ],
            "admission_vs_physical_storage_disposition": {
                "logically_admitted_dataset_assets": 18975,
                "assets_under_admission_hold": 0,
                "files_in_accepted_directory": 18845,
                "files_retained_in_quarantine": 130,
                "original_source_completeness_verified": 0,
                "discrepancy_screened_disposition": "ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY",
                "accepted_files_disposition": "ADMITTED_CLAIM_A_VALID_ORIGIN_UNVERIFIED",
                "physical_isolation_note": (
                    "Under Policy 2A, all 18,975 recordings are logically admitted as Common Voice assets, while the 130 "
                    "discrepancy-screened recordings remain physically in the quarantine directory (cohort3_rejected_quarantine). "
                    "Those are two different concepts. The 130 files carry the explicit admission disposition "
                    "ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY, retaining their original physical location until a separate "
                    "Gate 2 authorization permits any materialization operation. This avoids accidentally suggesting that the 130 "
                    "recordings are excluded from the research population merely because they remain in quarantine."
                )
            }
        },
        "section_3_exact_primary_estimand_and_mathematical_specifications": {
            "registered_estimand_standard": "Protocol Section 14.7 / ADR-005 Pre-Registered Primary Inferential Estimand",
            "speaker_level_wer_calculation": {
                "formal_definition": "Approach 2: Pooled Speaker Errors Divided by Pooled Reference Words",
                "formula": "WER_{a, s} = \\frac{\\sum_{c=1}^{C_s} (S_{a, sc} + D_{a, sc} + I_{a, sc})}{\\sum_{c=1}^{C_s} N_{sc}^{\\text{ref}}} \\times 100\\%",
                "variables": {
                    "a": "Experimental arm (Arm 1 = Static, Arm 2 = Ungated CTTA, Arm 3 = DSG-Gated CTTA)",
                    "s": "Speaker identifier (s in {1, ..., S}, where S = 1,100)",
                    "c": "Clip index within speaker cluster (c in {1, ..., C_s}, where C_s = 15 for all s under Policy 2A)",
                    "S_{a, sc}": "Levensthein substitutions for clip c under arm a",
                    "D_{a, sc}": "Levensthein deletions for clip c under arm a",
                    "I_{a, sc}": "Levensthein insertions for clip c under arm a",
                    "N_{sc}^{\\text{ref}}": "Total reference words in ground-truth transcript for clip c"
                },
                "protocol_alignment": (
                    "This pooled-speaker formula matches the production implementation in src/dsg_ctta/offline/aggregation.py "
                    "(spk_wer = (s_s + s_d + s_i) / s_n) and tests/research_validity/test_stage6m_reproducibility_and_gate_validity.py. "
                    "It prevents small-denominator distortion from single-word clips and avoids changing the pre-registered estimand."
                )
            },
            "paired_speaker_difference": {
                "formula": "\\Delta_s = \\text{WER}_{3, s} - \\text{WER}_{1, s} = \\frac{\\sum_{c=1}^{15} (E_{3, sc} - E_{1, sc})}{\\sum_{c=1}^{15} N_{sc}^{\\text{ref}}} \\times 100\\%",
                "interpretation": "Negative values (\\Delta_s < 0) represent improvement (error reduction) under DSG-gated adaptation relative to static baseline."
            },
            "stratum_aggregation": {
                "formula": "\\Delta_g = \\frac{1}{N_g} \\sum_{s \\in \\text{Stratum } g} \\Delta_s",
                "sample_size": "N_g = 220 speakers per stratum (strictly equal across all 5 strata under Policy 2A)."
            },
            "primary_confirmatory_contrasts": [
                {
                    "contrast_id": "CRITERION_1_EVENT_A",
                    "name": "DSG-Gated vs Static Baseline (Primary Utility)",
                    "formula": "\\Delta_{\\text{static}} = \\text{WER}_{3} - \\text{WER}_{1} = \\frac{\\sum_{s,c} (E_{3,sc} - E_{1,sc})}{\\sum_{s,c} N_{sc}^{\\text{ref}}} \\times 100\\%",
                    "null_hypothesis": "H_{0, A}: \\Delta_{\\text{static}} \\ge 0.00\\text{ pp}",
                    "alternative_hypothesis": "H_{1, A}: \\Delta_{\\text{static}} < 0.00\\text{ pp}",
                    "test_statistic": "Linearized cluster-robust ratio estimator with t(S-1) critical value at alpha_adj = 0.00625",
                    "acceptance_criterion": "\\text{UCB}_{99.375\\%}(\\Delta_{\\text{static}}) < 0.00\\text{ pp}"
                },
                {
                    "contrast_id": "CRITERION_2_EVENT_B",
                    "name": "DSG-Gated vs Ungated SUTA (Primary Utility)",
                    "formula": "\\Delta_{\\text{ungated}} = \\text{WER}_{3} - \\text{WER}_{2} = \\frac{\\sum_{s,c} (E_{3,sc} - E_{2,sc})}{\\sum_{s,c} N_{sc}^{\\text{ref}}} \\times 100\\%",
                    "null_hypothesis": "H_{0, B}: \\Delta_{\\text{ungated}} \\ge 0.00\\text{ pp}",
                    "alternative_hypothesis": "H_{1, B}: \\Delta_{\\text{ungated}} < 0.00\\text{ pp}",
                    "test_statistic": "Linearized cluster-robust ratio estimator with t(S-1) critical value at alpha_adj = 0.00625",
                    "acceptance_criterion": "\\text{UCB}_{99.375\\%}(\\Delta_{\\text{ungated}}) < 0.00\\text{ pp}"
                },
                {
                    "contrast_id": "CRITERION_3_EVENT_C",
                    "name": "Per-Accent Non-Inferiority across All 5 Strata (Fairness Guards)",
                    "formula": "\\Delta_g = \\text{WER}_{3, g} - \\text{WER}_{1, g} \\quad \\forall g \\in \\{1, 2, 3, 4, 5\\}",
                    "null_hypothesis": "H_{0, C, g}: \\Delta_g > +2.00\\text{ pp}",
                    "alternative_hypothesis": "H_{1, C, g}: \\Delta_g \\le +2.00\\text{ pp}",
                    "test_statistic": "Stratum-specific linearized cluster-robust ratio estimator with t(N_g-1) critical value at alpha_adj = 0.00625",
                    "acceptance_criterion": "\\text{UCB}_{99.375\\%}(\\Delta_g) \\le +2.00\\text{ pp} \\quad \\forall g \\in \\{1, 2, 3, 4, 5\\}"
                },
                {
                    "contrast_id": "CRITERION_4_EVENT_D",
                    "name": "Cross-Accent Disparity Non-Increase (Fairness Safety)",
                    "formula": "D = \\max_{g \\in \\mathcal{G}} \\text{WER}_g - \\min_{g \\in \\mathcal{G}} \\text{WER}_g, \\quad \\Delta D = D_{\\text{Arm 3}} - D_{\\text{Arm 1}}",
                    "null_hypothesis": "H_{0, D}: \\Delta D > 0.00\\text{ pp}",
                    "alternative_hypothesis": "H_{1, D}: \\Delta D \\le 0.00\\text{ pp}",
                    "test_statistic": "Stratified paired-cluster bootstrap across B = 20,000 replicates evaluated at 99.375th percentile",
                    "acceptance_criterion": "\\text{UCB}_{99.375\\%}(\\Delta D) \\le 0.00\\text{ pp} \\quad (\\text{with diagnostic monitoring boundary } \\le +1.40\\text{ pp})"
                }
            ],
            "composite_joint_success_rule": {
                "rule_statement": "Stage 6M confirmatory CTTA success is declared IF AND ONLY IF all 8 hypotheses pass simultaneously:",
                "formula": "\\text{SUCCESS} \\iff \\text{Event A} \\land \\text{Event B} \\land \\text{Event C} \\land \\text{Event D}",
                "multiplicity_framework": "Fixed Single-Step Simultaneous Bonferroni (M = 8, alpha_family = 0.05, alpha_adj = 0.00625, UCB percentile = 99.375%)"
            },
            "mathematical_relationship_between_estimands": {
                "derivation": (
                    "In speech recognition evaluation with cluster sampling, three aggregation levels exist:\\n"
                    "1. Clip-Macro WER: WER_clip = (1/(S*C)) * sum_s sum_c (E_sc / N_sc). Weights every clip equally.\\n"
                    "2. Pooled Speaker WER (Approach 2): WER_s = sum_c E_sc / sum_c N_sc = sum_c (N_sc / W_s) * WER_sc. "
                    "This is a word-count-weighted average of that speaker's clips.\\n"
                    "3. Speaker-Macro WER: WER_speaker = (1/S) * sum_s WER_s. Weights every speaker equally (1/S).\\n"
                    "4. Word-Micro WER: WER_word = sum_s sum_c E_sc / sum_s sum_c N_sc. Weights every word equally."
                ),
                "non_identity_proof": (
                    "Comparing Speaker-Macro and Clip-Macro under constant C = 15 clips per speaker:\\n"
                    "WER_speaker = (1/S) * sum_s sum_c (N_sc / W_s) * WER_sc\\n"
                    "WER_clip    = (1/S) * sum_s sum_c (1 / C)      * WER_sc\\n"
                    "The difference between these two aggregation operations is:\\n"
                    "WER_speaker - WER_clip = (1/S) * sum_s sum_c (N_sc / W_s - 1/C) * WER_sc\\n"
                    "As mathematical aggregation operators (functions over all possible clip WER vectors in [0, inf)^{S x C}), "
                    "these two estimands are identical functions IF AND ONLY IF N_sc / W_s = 1/C for all clips c, "
                    "meaning every clip of speaker s has identical reference word count N_sc = W_s / C. "
                    "While accidental numerical equality can theoretically occur on a single realized dataset through fortuitous cancellation "
                    "(sum_c (N_sc / W_s - 1/C) * WER_sc = 0), they are fundamentally distinct mathematical estimands that assign different weights "
                    "to speech samples. In natural speech corpora like Common Voice, utterance lengths vary naturally (e.g. 3 to 15+ words). "
                    "Therefore, equal clip counts per speaker do NOT make pooled speaker-macro functionally identical to clip-macro."
                ),
                "concrete_numerical_counterexample": {
                    "scenario": "Consider a minimal cohort with S = 1 speaker and C = 2 clips (balanced clip count):",
                    "clip_1": "N_11 = 2 reference words, E_11 = 2 errors -> WER_11 = 2/2 = 100.0%",
                    "clip_2": "N_12 = 10 reference words, E_12 = 0 errors -> WER_12 = 0/10 = 0.0%",
                    "clip_macro_result": "WER_clip = (1/2) * (100.0% + 0.0%) = 50.0%",
                    "pooled_speaker_macro_result": "WER_s = (2 + 0) / (2 + 10) = 2/12 = 16.67%",
                    "discrepancy": "WER_speaker (16.67%) != WER_clip (50.0%) by 33.33 percentage points despite balanced C=2.",
                    "conclusion": (
                        "The registered Section 14.7 protocol specifies Speaker-Macro over Pooled Speaker WERs (Approach 2). "
                        "This preserves equal speaker weighting (1/S) across the evaluation cohort without distorting estimates "
                        "by single short utterances, but must NOT be described as mathematically identical to clip-macro."
                    )
                }
            }
        },
        "section_4_statistical_power_and_decision_rules": {
            "approved_power_result": {
                "source": "Task 6.3 Calibrated 5-Stratum Power Simulation (Git Commit 06cf833)",
                "sample_size": "N_g = 220 speakers per stratum (N = 1,100, C = 15, M = 16,500 clips)",
                "multiplicity_family": "M = 8 One-Sided Hypotheses, Fixed Bonferroni alpha_adj = 0.00625, Percentile = 99.375%",
                "simulation_depth": "10,000 Monte Carlo trajectories, B = 20,000 bootstrap resamples per trajectory",
                "calibrated_disparity_reduction": "-2.0 percentage points",
                "observed_joint_power": "90.58%",
                "clopper_pearson_exact_bounds": {
                    "one_sided_lcb_95": "90.085739%",
                    "two_sided_ci_95": "[89.990601%, 91.145641%]",
                    "acceptance_criterion": "LCB_95 >= 90.000000% (Passed by +0.0857 pp / +8 trajectories)"
                }
            },
            "conditional_validity_statement": (
                "The calibrated 90.58% joint power result was calculated under the exact M = 8 simultaneous Bonferroni "
                "decision architecture with simultaneous one-sided 99.375% bounds. It is strictly conditional on its "
                "pre-registered simulation assumptions: between-speaker standard deviation sigma_between = 6.50 pp, "
                "within-speaker paired difference standard deviation sigma_paired = 3.20 pp, and target disparity effect "
                "Delta D = -2.00 pp. This result demonstrates that the registered balanced sample size (N_g=220) is statistically "
                "adequate to detect the targeted effect sizes under Monte Carlo simulation; it does NOT constitute proof of "
                "observed DSG efficacy or guarantee real-world adaptation success on the physical confirmatory run."
            ),
            "reconciliation_of_nominal_vs_simultaneous_confidence_levels": {
                "reported_nominal_levels": [
                    {
                        "dimension": "Accent Non-Inferiority",
                        "reported_level": "97.5% UCB <= +2.00 pp",
                        "context": "Nominal single-comparison rate (alpha = 0.025 one-sided / 0.05 two-sided) from exploratory Task 5 design screening."
                    },
                    {
                        "dimension": "Disparity Safety",
                        "reported_level": "95.0% UCB <= +1.40 pp",
                        "context": "Unadjusted nominal bootstrap percentile used as an auxiliary diagnostic monitoring boundary in exploratory studies."
                    }
                ],
                "confirmatory_bonferroni_architecture": (
                    "In the authoritative Stage 6M v1.5 confirmatory benchmark (src/dsg_ctta/evaluation/paired_cluster_inference_v15.py), "
                    "multiplicity across all M = 8 confirmatory hypotheses is controlled via a single-step simultaneous Bonferroni procedure: "
                    "alpha_family = 0.05, alpha_adjusted = 0.05 / 8 = 0.00625, simultaneous one-sided UCB percentile = 99.375%. "
                    "All confirmatory decisions are governed by simultaneous 99.375% bounds (Event A: static UCB < 0.00 pp; "
                    "Event B: ungated UCB < 0.00 pp; Event C: 5 accent regression UCBs <= +2.00 pp; Event D: disparity bootstrap UCB <= 0.00 pp). "
                    "Crucially, the Task 6.3 calibrated power result of 90.58% (Clopper-Pearson 95% LCB = 90.085739%) evaluated this exact "
                    "simultaneous M = 8, 99.375% Bonferroni criterion. The nominal 97.5% and 95.0% levels are exploratory only and do NOT govern confirmatory gate decisions."
                )
            },
            "preservation_of_all_decision_thresholds": [
                {"rule": "Multiplicity Family", "threshold": "M = 8 Hypotheses, alpha_family = 0.05, alpha_adj = 0.00625"},
                {"rule": "Simultaneous UCB Percentile", "threshold": "99.375% (1 - 0.00625)"},
                {"rule": "Event A (Superiority vs Static)", "threshold": "UCB_99.375%(Delta_static) < 0.00 pp"},
                {"rule": "Event B (Superiority vs Ungated SUTA)", "threshold": "UCB_99.375%(Delta_ungated) < 0.00 pp"},
                {"rule": "Event C (Accent Regression Guards)", "threshold": "UCB_99.375%(Delta_g) <= +2.00 pp for all 5 strata"},
                {"rule": "Event D (Disparity Safety)", "threshold": "UCB_99.375%(Delta_D) <= 0.00 pp (nominal) / <= +1.40 pp (diagnostic)"},
                {"rule": "Candidate Loss Sanity", "threshold": "Scalar loss is finite; grad_norm < 100.0; non-zero update norm"}
            ]
        },
        "section_5_governance_and_preconditions": {
            "operative_status": "ACTIVE / APPROVED UNDER GATE 1 (Executed 2026-11-07)",
            "governance_roadmap": {
                "gate_1": "Policy 2A Scientific Admission — Formally APPROVED on 2026-11-07 by Project Lead. Authorizes formal scientific admission criteria and target dataset definition ONLY. Stated evidentiary limitations apply (Claim B unverified across all 18,975 recordings). Does NOT authorize Task 7.7.4 implementation or production dataset operations.",
                "gate_2": "Task 7.7.4 Authorization — Authorizes implementation and execution of non-destructive materializer workflow under exclusive OS-level ownership locking (STATUS: NOT AUTHORIZED / PENDING INDEPENDENT DETERMINATION).",
                "gate_3": "Manifest Approval & Locking — Final dataset verification, hash reconciliation, and manifest locking (STATUS: LOCKED).",
                "gates_4_to_6": "Environment readiness, confirmatory GPU CTTA experiments, and simultaneous statistical analysis."
            },
            "preconditions_to_activation": [
                "1. Project Lead formally executes Gate 1 (Scientific Admission Decision Record for Policy 2A) — COMPLETE (2026-11-07).",
                "2. Project Lead independently executes Gate 2 (Task 7.7.4 Non-Destructive Materialization Authorization) — PENDING.",
                "3. Reconciled dataset assets are validated without destructive deletion or file mutation.",
                "4. Final execution manifest is generated, verified, and locked under Gate 3 (STATUS: LOCKED).",
                "5. Software environment, models, and configuration are verified via non-confirmatory smoke tests (Gate 4)."
            ],
            "prohibited_actions": [
                "No automatic authorization of Task 7.7.4 upon Gate 1 approval.",
                "No GPU CTTA execution on confirmatory audio.",
                "No unsealing of evaluation transcripts.",
                "No promotion or mutation of audio assets prior to independent Gate 2 authorization.",
                "No git commit or push without explicit instruction."
            ]
        }
    }


def generate_markdown(data: Dict[str, Any]) -> str:
    meta = data["metadata"]
    s1 = data["section_1_target_population_and_research_scope"]
    s2 = data["section_2_preservation_of_registered_balanced_design"]
    s3 = data["section_3_exact_primary_estimand_and_mathematical_specifications"]
    s4 = data["section_4_statistical_power_and_decision_rules"]
    s5 = data["section_5_governance_and_preconditions"]

    lines: List[str] = [
        f"# {meta['document_title']}",
        "",
        f"**Document ID:** `{meta['document_id']}`<br>",
        f"**Governing Protocol:** {meta['governing_protocol']}<br>",
        f"**Governing Branch / Base Commit:** `{meta['governing_branch']}` @ [`{meta['reference_commit'][:7]}`](https://github.com/mahi3007/Final-Year-Project/commit/{meta['reference_commit']})<br>",
        f"**Document Status:** **{meta['document_status']}**<br>",
        f"**Project Lead:** {meta['project_lead']}<br>",
        f"**Timestamp (UTC):** {meta['timestamp_utc']}<br>",
        "",
        "> [!IMPORTANT]",
        f"> **Authoritative Notice:** {meta['authoritative_notice']}",
        "",
        "---",
        "",
        "## 1. Target Population Definition and Research Scope",
        "",
        f"**Target Population:** {s1['target_population_definition']}",
        "",
        f"**Scientific Research Objective:** {s1['scientific_objective']}",
        "",
        "### Four-Level Audio Integrity & Completeness Hierarchy",
        "",
        "To prevent conflation of distinct technical, decoding, container, and acoustic phenomena, the protocol enforces a strict four-level forensic taxonomy:",
        "",
        "| Hierarchy Level | Forensic Dimension | Technical Definition | Empirical Status Across 18,975 Recordings |",
        "| :---: | :--- | :--- | :--- |",
    ]

    for idx, (lvl_key, lvl) in enumerate(s1["four_level_audio_integrity_distinction"].items(), 1):
        lines.append(
            f"| **Level {idx}** | **{lvl['dimension']}** | {lvl['technical_definition']} | **{lvl['empirical_status']}** |"
        )

    lines.extend([
        "",
        "> [!IMPORTANT]",
        f"> **Evidentiary Status:** {s1['evidentiary_status_statement']}",
        "",
        "> [!WARNING]",
        f"> **Epistemic Boundary:** {s1['negative_evidentiary_boundary']}",
        "",
        "---",
        "",
        "## 2. Preservation of Registered Balanced Experimental Design",
        "",
        f"This protocol addendum preserves in full the registered balanced sampling design authorized under Section 14.7. Admitting all 18,975 recordings under Policy 2A maintains the exact sample and cluster counts:",
        "",
        f"- **Confirmatory Strata:** Exactly {s2['confirmatory_strata_count']} distinct accent groups ({', '.join(s2['strata_names'])}).",
        f"- **Evaluation Speakers:** Exactly **{s2['evaluation_speakers_per_stratum']} speakers per stratum** across all 5 strata = **{s2['total_evaluation_speakers']:,} total evaluation speakers**.",
        f"- **Clips per Evaluation Speaker:** Exactly **{s2['clips_per_evaluation_speaker']} recordings per speaker** ($C = 15$) = **{s2['total_evaluation_clips']:,} evaluation clips**.",
        f"- **Sentinel Gate-Reference Panel:** Exactly **{s2['gate_reference_panel']['total_speakers']} speakers** ({s2['gate_reference_panel']['speakers_per_stratum']} per stratum $\\times$ 15 clips = {s2['gate_reference_panel']['total_clips']:,} clips). {s2['gate_reference_panel']['role']}",
        f"- **Australian Reserve Pool:** Exactly **{s2['reserve_replacement_pool']['total_speakers']} speakers** ({s2['reserve_replacement_pool']['total_clips']} clips). {s2['reserve_replacement_pool']['role']}",
        f"- **Total Dataset Assets:** Exactly **{s2['total_cohort3_audio_assets']:,} audio recordings**.",
        "",
        "### Cohort Structure & Balance Matrix",
        "",
        "| Accent Stratum | Evaluation Speakers | Evaluation Clips | Gate Speakers | Gate Clips | Reserve Speakers | Reserve Clips | Total Audio Clips |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for row in s2["cohort_balance_table"]:
        lines.append(
            f"| **{row['stratum']}** | {row['eval_speakers']:,} | {row['eval_clips']:,} | "
            f"{row['gate_speakers']} | {row['gate_clips']} | {row['reserve_speakers']} | {row['reserve_clips']} | **{row['total_clips']:,}** |"
        )

    adm_disp = s2["admission_vs_physical_storage_disposition"]
    lines.extend([
        "",
        "### Separation of Logical Admission Status and Physical Storage Location",
        "",
        "Under Policy 2A, all 18,975 recordings are logically admitted as Common Voice assets, while the 130 discrepancy-screened recordings remain physically in the quarantine directory. Those are two different concepts:",
        "",
        "| Measure | Policy 2A Disposition |",
        "| :--- | :---: |",
        f"| **Logically admitted dataset assets** | **{adm_disp['logically_admitted_dataset_assets']:,}** |",
        f"| **Assets under admission hold** | **{adm_disp['assets_under_admission_hold']}** |",
        f"| **Files in the ordinary accepted directory** | **{adm_disp['files_in_accepted_directory']:,}** |",
        f"| **Files physically retained in quarantine** | **{adm_disp['files_retained_in_quarantine']}** |",
        f"| **Original-source completeness verified** | **{adm_disp['original_source_completeness_verified']}** |",
        "",
        f"- **130 Discrepancy-Screened Recordings Disposition:** `{adm_disp['discrepancy_screened_disposition']}`",
        f"- **18,845 Accepted Recordings Disposition:** `{adm_disp['accepted_files_disposition']}`",
        "",
        "> [!NOTE]",
        f"> **Physical Isolation Rationale:** {adm_disp['physical_isolation_note']}",
    ])

    lines.extend([
        "",
        "---",
        "",
        "## 3. Exact Primary Estimand and Mathematical Specifications",
        "",
        f"The primary inferential estimand follows the pre-registered specification under **{s3['registered_estimand_standard']}**.",
        "",
        "### 3.1 Speaker-Level Word Error Rate (WER) Calculation",
        "",
        f"**Registered Definition:** {s3['speaker_level_wer_calculation']['formal_definition']}",
        "",
        f"$${s3['speaker_level_wer_calculation']['formula']}$$",
        "",
        f"> **Protocol Alignment:** {s3['speaker_level_wer_calculation']['protocol_alignment']}",
        "",
        "### 3.2 Paired Differences and Stratum Aggregation",
        "",
        "For each speaker $s$, the paired adaptation impact is:",
        f"$${s3['paired_speaker_difference']['formula']}$$",
        "",
        "The stratum-level contrast is the unweighted average across all $N_g = 220$ speakers in stratum $g$:",
        f"$${s3['stratum_aggregation']['formula']}$$",
        "",
        "### 3.3 Primary Confirmatory Contrasts & Bonferroni Decision Rules",
        "",
        "The confirmatory benchmark enforces a **Fixed Single-Step Simultaneous Bonferroni Procedure** across $M = 8$ one-sided hypotheses ($\alpha_{\text{family}} = 0.05, \alpha_{\text{adj}} = 0.00625$, simultaneous confidence percentile = $99.375\%$):",
        "",
        "| Event / Hypothesis | Target Comparison | Mathematical Estimand | Null & Alternative | Confirmatory Acceptance Rule ($99.375\%$ UCB) |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])

    for c in s3["primary_confirmatory_contrasts"]:
        lines.append(
            f"| **{c['contrast_id']}** | {c['name']} | $${c['formula']}$$ | $${c['null_hypothesis']}$$ vs $${c['alternative_hypothesis']}$$ | `{c['acceptance_criterion']}` |"
        )

    cj = s3["composite_joint_success_rule"]
    rel = s3["mathematical_relationship_between_estimands"]
    cex = rel["concrete_numerical_counterexample"]

    lines.extend([
        "",
        "### Composite Joint Success Rule",
        f"> **{cj['rule_statement']}**",
        f"> $${cj['formula']}$$",
        f"> **Multiplicity Framework:** `{cj['multiplicity_framework']}`",
        "",
        "### 3.4 Relationship Between Estimands & Proof of Non-Identity under Variable Word Counts",
        "",
        "In speech recognition evaluation, three distinct aggregation levels exist:",
        "- **Clip-Macro WER:** $$\\text{WER}_{\\text{clip}} = \\frac{1}{S \\cdot C} \\sum_{s=1}^S \\sum_{c=1}^C \\frac{E_{sc}}{N_{sc}}$$. Weights every audio clip equally ($1 / (S \\cdot C)$).",
        "- **Pooled Speaker WER (Approach 2):** $$\\text{WER}_s = \\frac{\\sum_{c=1}^C E_{sc}}{\\sum_{c=1}^C N_{sc}} = \\sum_{c=1}^C \\left( \\frac{N_{sc}}{W_s} \\right) \\text{WER}_{sc}$$. Weights clips within a speaker by their reference-word counts.",
        "- **Speaker-Macro WER:** $$\\text{WER}_{\\text{speaker}} = \\frac{1}{S} \\sum_{s=1}^S \\text{WER}_s$$. Weights each speaker equally ($1/S$).",
        "- **Corpus Word-Micro WER:** $$\\text{WER}_{\\text{word}} = \\frac{\\sum_{s,c} E_{sc}}{\\sum_{s,c} N_{sc}}$$. Weights each word equally; speakers weighted by total words.",
        "",
        "> [!IMPORTANT]",
        "> **Proof of Non-Identity:** Under constant $C = 15$ clips per speaker, speaker-macro and clip-macro are identical **as mathematical aggregation functions** if and only if every clip of speaker $s$ contains the exact same number of reference words ($N_{sc} = W_s / C$). While accidental numerical equality can theoretically occur on a single realized dataset through fortuitous cancellation, they are fundamentally distinct estimands with different weighting structures. In natural speech corpora like Common Voice, sentence lengths vary naturally. Therefore, equal clip counts per speaker do **NOT** make pooled speaker-macro functionally identical to clip-macro.",
        "",
        "#### Concrete Numerical Counterexample",
        f"- **Scenario:** {cex['scenario']}",
        f"  - Clip 1: `{cex['clip_1']}`",
        f"  - Clip 2: `{cex['clip_2']}`",
        f"- **Clip-Macro Outcome:** `{cex['clip_macro_result']}`",
        f"- **Pooled Speaker-Macro Outcome:** `{cex['pooled_speaker_macro_result']}`",
        f"- **Observed Discrepancy:** **{cex['discrepancy']}**",
        "",
        f"> **Protocol Specification:** {cex['conclusion']}",
        "",
        "---",
        "",
        "## 4. Statistical Power Status and Decision Boundaries",
        "",
        "### 4.1 Calibrated Statistical Power",
        f"- **Registered Sample Size:** {s4['approved_power_result']['sample_size']}",
        f"- **Multiplicity Architecture:** `{s4['approved_power_result']['multiplicity_family']}`",
        f"- **Simulation Depth:** {s4['approved_power_result']['simulation_depth']}",
        f"- **Calibrated Disparity Effect:** {s4['approved_power_result']['calibrated_disparity_reduction']}",
        f"- **Observed Joint Empirical Power:** **{s4['approved_power_result']['observed_joint_power']}**",
        f"- **Exact Clopper-Pearson Bounds:** One-sided 95% LCB = **{s4['approved_power_result']['clopper_pearson_exact_bounds']['one_sided_lcb_95']}** ({s4['approved_power_result']['clopper_pearson_exact_bounds']['acceptance_criterion']}). Two-sided 95% CI: `{s4['approved_power_result']['clopper_pearson_exact_bounds']['two_sided_ci_95']}`.",
        "",
        "> [!WARNING]",
        f"> **Conditional Simulation Boundary:** {s4['conditional_validity_statement']}",
        "",
        "### 4.2 Reconciliation of Nominal vs. Authoritative Simultaneous Confidence Levels",
        "",
        "The project reports have previously referenced both nominal unadjusted bounds (e.g. 97.5% for accent non-inferiority, 95% for disparity safety) and simultaneous Bonferroni bounds ($99.375\\%$). The table below reconciles these quantities against the authoritative frozen five-stratum protocol (`src/dsg_ctta/evaluation/paired_cluster_inference_v15.py`):",
        "",
        "| Evaluation Metric | Nominal / Exploratory Level | Confirmatory Bonferroni Architecture ($M = 8$) | Operative Status |",
        "| :--- | :--- | :--- | :--- |",
        "| **Event A (Superiority vs. Static)** | $\\Delta_{\\text{static}} < 0.00\\text{ pp}$ (nominal) | $\\text{UCB}_{99.375\\%}(\\Delta_{\\text{static}}) < 0.00\\text{ pp}$ | Confirmatory Gate |",
        "| **Event B (Superiority vs. Ungated SUTA)** | $\\Delta_{\\text{ungated}} < 0.00\\text{ pp}$ (nominal) | $\\text{UCB}_{99.375\\%}(\\Delta_{\\text{ungated}}) < 0.00\\text{ pp}$ | Confirmatory Gate |",
        "| **Event C (Accent Regression Guards)** | $97.5\\%\\text{ UCB} \\le +2.00\\text{ pp}$ (per-comparison) | $\\text{UCB}_{99.375\\%}(\\Delta_g) \\le +2.00\\text{ pp} \\quad \\forall g \\in \\{1..5\\}$ | Confirmatory Gate (5 Strata) |",
        "| **Event D (Disparity Safety)** | $95.0\\%\\text{ UCB} \\le +1.40\\text{ pp}$ (diagnostic) | $\\text{UCB}_{99.375\\%}(\\Delta D) \\le 0.00\\text{ pp}$ | Confirmatory Gate |",
        "",
        "> [!IMPORTANT]",
        f"> **Power Alignment:** {s4['reconciliation_of_nominal_vs_simultaneous_confidence_levels']['confirmatory_bonferroni_architecture']}",
        "",
        "### 4.3 Preserved Decision Thresholds",
        "",
        "| Gate / Confirmatory Dimension | Pre-Registered Threshold Invariant |",
        "| :--- | :--- |",
    ])

    for th in s4["preservation_of_all_decision_thresholds"]:
        lines.append(f"| **{th['rule']}** | `{th['threshold']}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Governance Status & Execution Preconditions",
        "",
        f"**Operative Status:** `{s5['operative_status']}`",
        "",
        "### Mandatory Preconditions Before Activation:",
    ])

    for pre in s5["preconditions_to_activation"]:
        lines.append(f"- {pre}")

    lines.extend([
        "",
        "### Strictly Prohibited Operations:",
    ])

    for pro in s5["prohibited_actions"]:
        lines.append(f"- {pro}")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Project Lead Gate 1 Decision Record",
        "",
        "```markdown",
        "# GATE 1: SCIENTIFIC ADMISSION POLICY (POLICY 2A) — DECISION RECORD",
        "",
        "Decision Authority: Project Lead (Venkata Akhil Kumar)",
        "Governing Scope:    Authorizes formal scientific admission criteria and target dataset definition only.",
        "                    Implementation and execution of Task 7.7.4 require separate Gate 2 authorization.",
        "",
        "Decision Status:    [X] APPROVED AS ACTIVE PROTOCOL ADDENDUM (Gate 1 Passed)",
        "                    [ ] REJECTED / RETURNED FOR REVISION",
        "                    [ ] AWAITING DETERMINATION",
        "",
        "Selected Policy:    [X] Policy 2A (Physical Integrity & Decodability Benchmark)",
        "                    [ ] Policy 1  (Claim B Prerequisite)",
        "                    [ ] Policy 2B (Estimation Discrepancy Screen)",
        "",
        "Decision Rationale: Evaluates Mozilla Common Voice 27.0 (en) as distributed to the speech recognition",
        "                    research community across five balanced accent strata (Australian, Canadian,",
        "                    England, South Asian, US English) without asserting unverified claims regarding",
        "                    original recording capture or master completeness.",
        "Research Scope:     Mozilla Common Voice 27.0 (en) as distributed across five balanced accent strata",
        "Claim Limitations:  Claim A: Current-file structural validity through observed EOF (Verified 18,975/18,975)",
        "                    Claim B: Original-source completeness relative to uncompressed masters (Unverified for all 18,975)",
        "",
        "Dataset Admission & Physical Storage Disposition (Policy 2A):",
        "| Measure                                  | Policy 2A disposition |",
        "| Logically admitted dataset assets        | 18,975                |",
        "| Assets under admission hold              | 0                     |",
        "| Files in the ordinary accepted directory | 18,845                |",
        "| Files physically retained in quarantine  | 130                   |",
        "| Original-source completeness verified    | 0                     |",
        "",
        "130 Discrepancy-Screened Files Disposition: ADMITTED_ORIGIN_UNVERIFIED_WITH_DURATION_DISCREPANCY",
        "(Physically retained in quarantine directory until separate Gate 2 materializer authorization)",
        "",
        "Decision Date:      2026-11-07",
        "```",
        ""
    ])

    return "\n".join(lines) + "\n"


def main():
    logger.info("Generating Stage 6M Policy 2A Protocol Addendum deliverables...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = build_protocol_addendum_data()

    logger.info(f"Writing JSON output to {JSON_OUTPUT_PATH}...")
    JSON_OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    logger.info(f"Generating Markdown output to {MD_OUTPUT_PATH}...")
    md_content = generate_markdown(data)
    MD_OUTPUT_PATH.write_text(md_content, encoding="utf-8")

    logger.info("Policy 2A Protocol Addendum generated successfully.")
    logger.info(f"  JSON size: {JSON_OUTPUT_PATH.stat().st_size:,} bytes")
    logger.info(f"  MD size:   {MD_OUTPUT_PATH.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
