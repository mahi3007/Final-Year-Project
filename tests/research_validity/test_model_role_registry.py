"""
Blocking Research Validity Tests: Model Role Registry & Architecture Audit.
Ensures zero ambiguity in model classification, strict holdout eligibility,
and enforcement of CTTA architectural boundaries.
"""

from __future__ import annotations
import json
from pathlib import Path
import pytest
from dsg_ctta.models.registry import MODEL_CATALOG, create_asr_model
from dsg_ctta.models.whisper_models import WhisperModel
from dsg_ctta.models.ctc_models import GenericCTCModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def registry_data():
    reg_path = PROJECT_ROOT / "configs" / "model_role_registry.json"
    assert reg_path.exists(), f"Missing model role registry: {reg_path}"
    with open(reg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_stage2_models_registered(registry_data):
    """Verify all 6 historical Stage 2 models exist in the authoritative registry."""
    stage2_keys = [
        "wav2vec2_base",
        "whisper_base",
        "data2vec_base",
        "distil_whisper_small",
        "whisper_tiny",
        "wav2vec2_100h",
    ]
    models = registry_data["models"]
    for key in stage2_keys:
        assert key in models, f"Stage 2 model {key} not registered"
        assert models[key]["stage2_role"] == "STATIC_BASELINE"


def test_all_stage6_models_registered(registry_data):
    """Verify all models evaluated in Stage 6 / 6.1 exist in registry with proper roles."""
    expected_stage6_roles = {
        "wav2vec2_base": "OVERLAP_CTC_CONTROL",
        "data2vec_base": "OVERLAP_CTC_CONTROL",
        "whisper_base": "SEQ2SEQ_STATIC_PORTABILITY",
        "distil_whisper_small": "SEQ2SEQ_STATIC_PORTABILITY",
        "hubert_large": "HELD_OUT_CTC",
        "xlsr_english": "HELD_OUT_CTC",
        "wav2vec2_large_lv60": "HELD_OUT_CTC",
        "wav2vec2_large_robust": "HELD_OUT_CTC",
    }
    models = registry_data["models"]
    for key, expected_role in expected_stage6_roles.items():
        assert key in models, f"Stage 6 model {key} missing from registry"
        assert models[key]["stage6_role"] == expected_role, (
            f"Model {key} has incorrect stage6_role: {models[key]['stage6_role']} != {expected_role}"
        )


def test_ctc_models_have_ctta_eligibility(registry_data):
    """Verify all CTC models have COMPATIBLE CTTA status and frame logits."""
    models = registry_data["models"]
    for key, spec in models.items():
        if spec["architecture"] == "CTC":
            assert spec["ctta_status"] == "COMPATIBLE"
            assert spec["has_ctc_head"] is True
            assert spec["has_frame_logits"] is True


def test_seq2seq_models_marked_incompatible(registry_data):
    """Verify Seq2Seq models are marked INCOMPATIBLE_NON_CTC with mathematical rationale."""
    models = registry_data["models"]
    for key, spec in models.items():
        if spec["architecture"] == "SEQ2SEQ":
            assert spec["ctta_status"] == "INCOMPATIBLE_NON_CTC"
            assert spec["has_ctc_head"] is False
            assert spec["has_frame_logits"] is False
            assert "frame-synchronous" in spec.get("incompatibility_reason", "").lower()


def test_holdout_models_not_in_development_registry(registry_data):
    """Ensure genuinely held-out models were never flagged as development models."""
    models = registry_data["models"]
    held_out_keys = ["hubert_large", "xlsr_english", "wav2vec2_large_lv60", "wav2vec2_large_robust"]
    for key in held_out_keys:
        spec = models[key]
        assert spec["holdout_eligible"] is True
        assert spec["holdout_status"] == "GENUINE_HELD_OUT"
        assert spec["development_role"] == "EXCLUDED_FROM_DEVELOPMENT"
        assert spec["stage2_role"] == "NOT_EVALUATED_IN_STAGE2"
        assert spec["stage3m_role"] == "EXCLUDED_HELD_OUT"
        assert spec["stage4m_role"] == "EXCLUDED_HELD_OUT"
        assert spec["stage5m_role"] == "EXCLUDED_HELD_OUT"


def test_overlap_models_not_marked_holdout(registry_data):
    """Ensure development models evaluated in Stage 6 are marked OVERLAP_CONTROL, not held-out."""
    models = registry_data["models"]
    overlap_keys = ["wav2vec2_base", "data2vec_base"]
    for key in overlap_keys:
        spec = models[key]
        assert spec["holdout_eligible"] is False
        assert spec["holdout_status"] == "OVERLAP_CONTROL"
        assert spec["stage6_role"] == "OVERLAP_CTC_CONTROL"


def test_unknown_model_fails_closed():
    """Verify that attempting to instantiate an unknown model raises an error."""
    with pytest.raises(KeyError, match="Unknown model name"):
        create_asr_model("non_existent_model_xyz")


def test_model_id_immutability(registry_data):
    """Verify model IDs match exact historical registry in MODEL_CATALOG."""
    models = registry_data["models"]
    for key, spec in models.items():
        if key in MODEL_CATALOG:
            assert MODEL_CATALOG[key]["model_id"] == spec["model_id"], (
                f"ID mismatch for {key}: {MODEL_CATALOG[key]['model_id']} != {spec['model_id']}"
            )


def test_checkpoint_identity():
    """Verify specific high-stakes checkpoints are exact canonical models."""
    assert MODEL_CATALOG["hubert_large"]["model_id"] == "facebook/hubert-large-ls960-ft"
    assert MODEL_CATALOG["wav2vec2_100h"]["model_id"] == "facebook/wav2vec2-base-100h"
    assert MODEL_CATALOG["data2vec_base"]["model_id"] == "facebook/data2vec-audio-base-960h"
    assert MODEL_CATALOG["wav2vec2_base"]["model_id"] == "facebook/wav2vec2-base-960h"


def test_architecture_identity(registry_data):
    """Verify model adapter classes match their architectural family."""
    models = registry_data["models"]
    for key, spec in models.items():
        if key in MODEL_CATALOG:
            adapter_cls = MODEL_CATALOG[key]["adapter_cls"]
            if spec["architecture"] == "CTC":
                assert issubclass(adapter_cls, GenericCTCModel) or adapter_cls.__name__ == "Wav2Vec2BaseModel"
            elif spec["architecture"] == "SEQ2SEQ":
                assert issubclass(adapter_cls, WhisperModel)


def test_whisper_not_sent_to_ctc_adapter():
    """Verify that Seq2Seq models use WhisperModel adapter and not GenericCTCModel."""
    whisper_entry = MODEL_CATALOG["whisper_base"]
    assert whisper_entry["adapter_cls"] == WhisperModel
    assert whisper_entry["family"] == "EncoderDecoder"
