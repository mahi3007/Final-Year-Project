"""
Full End-to-End Integration Test: Fixture -> Splits -> Baseline -> GLMM -> Sentinel.
"""

import os
from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits, export_splits_to_csv
from dsg_ctta.experiments.runner import run_baseline_evaluation
from dsg_ctta.online.sentinel import FrozenSentinelPanel
from dsg_ctta.models.mock_model import MockASRModel


def test_full_e2e_research_pipeline(tmp_path):
    # Step 1: Generate synthetic research fixture
    fixture_dir = str(tmp_path / "fixture")
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=fixture_dir,
        utterances_per_speaker=3
    )
    assert len(primary_utts) == 36
    assert len(ext_utts) == 12

    # Step 2: Create speaker-disjoint splits
    manifest = create_speaker_disjoint_splits(
        utterances=primary_utts,
        seed=42,
        external_utterances=ext_utts
    )
    splits_dir = str(tmp_path / "splits")
    exported = export_splits_to_csv(manifest, output_dir=splits_dir)
    assert os.path.exists(exported["final_test"])

    # Step 3: Run baseline evaluation with MockASR model
    reports_dir = str(tmp_path / "reports")
    res = run_baseline_evaluation(
        utterances=manifest.partitions["final_test"].utterances,
        model_name="mock_asr",
        partition_name="final_test",
        output_dir=reports_dir,
        device="cpu",
        run_glmm=True
    )

    summary = res["summary"]
    assert summary.total_utterances > 0
    assert summary.corpus_wer >= 0.0
    assert summary.disparity_d >= 0.0
    assert res["glmm_report"] is not None
    assert len(res["glmm_report"].coefficients) > 0

    # Step 4: Sentinel Panel Safety Evaluation
    sentinel_utts = manifest.partitions["sentinel_candidates"].utterances
    panel = FrozenSentinelPanel(panel_id="panel_e2e_v1", sentinel_utterances=sentinel_utts)

    base_model = MockASRModel(seed=42)
    cand_model = MockASRModel(seed=43)

    sentinel_res = panel.evaluate_candidate_safety(
        base_model=base_model,
        candidate_model=cand_model,
        num_bootstrap=100
    )

    assert sentinel_res.decision in ["ACCEPT", "REJECT"]
    assert isinstance(sentinel_res.delta_r_ucb, float)
    assert isinstance(sentinel_res.max_delta_g_ucb, float)
    assert isinstance(sentinel_res.delta_d_ucb, float)
