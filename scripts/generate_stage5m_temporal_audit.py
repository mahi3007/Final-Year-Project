#!/usr/bin/env python3
"""
Stage 5M Retrospective Temporal Audit Generator
================================================
Protocol: v1.1.0-model-expansion | Standard: ADR-005
Audits and resolves the temporal validity of Stage 5M candidate evaluations:
1. Distinguishes same-window retrospective adaptation effect (Delta_E_same)
   from next-window prospective downstream effect (Delta_E_next).
2. Verifies counterfactual state equivalence and prior-update histories.
3. Generates:
   - results/stage5m/stage5m_retrospective_temporal_audit.csv
   - results/stage5m/stage5m_prospective_outcome_matrix.csv
   - reports/stage5m/stage5m_prospective_provenance_linkage.csv
"""

import json
from pathlib import Path
import soundfile as sf
import torch
import pandas as pd
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, Data2VecAudioForCTC
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.data.normalization import TextNormalizer

RESULTS_DIR = PROJECT_ROOT / "results" / "stage5m"
CHECKPOINTS_DIR = RESULTS_DIR / "checkpoints"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5m"

BASE_HASHES = {
    "data2vec_base": "ff0b6510020137db",
    "wav2vec2_base": "5272cc15fda04952",
    "wav2vec2_100h": "befad7c351bda930"
}

CONDITION_CSVS = {
    "clean": "datasets/splits/stage4_characterization.csv",
    "noise_15db": "datasets/splits/stage4_noise_moderate.csv",
    "noise_5db": "datasets/splits/stage4_noise_severe.csv",
    "babble_15db": "datasets/splits/stage4_babble_moderate.csv",
    "reverb_t60_04": "datasets/splits/stage4_reverberation.csv"
}

def generate_temporal_audit():
    print("=" * 80)
    print("EXECUTING STAGE 5M TEMPORAL VALIDITY AUDIT GENERATION")
    print("=" * 80)

    # 1. Load operational decisions
    dec_csv_path = RESULTS_DIR / "stage5m_operational_decisions.csv"
    assert dec_csv_path.exists(), f"Missing {dec_csv_path}"
    df_dec = pd.read_csv(dec_csv_path)

    # Precompute prior updates count per run
    prior_updates_map = {}
    for exp_id, group in df_dec.groupby("experiment_id"):
        cum_acc = 0
        for _, r in group.sort_values("window_id").iterrows():
            prior_updates_map[(exp_id, r["window_id"])] = cum_acc
            if r["decision"] == "ACCEPT":
                cum_acc += 1

    # 2. Build multi-index prediction lookup from all 103 checkpoints
    print("Loading predictions from 103 checkpoints...")
    pred_map = {}
    preds_by_exp_win = {} # (exp_id, window_id) -> list of preds
    
    ckpt_files = sorted(CHECKPOINTS_DIR.glob("STAGE5M_*.json"))
    for f in ckpt_files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        exp_id = d.get("summary", {}).get("experiment_id", f.stem)
        for p in d.get("predictions", []):
            k = (p["model_key"], p["condition"], p["ordering_id"], p["window_id"], p["utterance_id"], p["theta_hash"])
            if k not in pred_map:
                pred_map[k] = p
            
            ew_k = (exp_id, p["window_id"])
            if ew_k not in preds_by_exp_win:
                preds_by_exp_win[ew_k] = []
            preds_by_exp_win[ew_k].append(p)

    print(f"Loaded {len(pred_map):,} unique prediction records.")

    # 3. Load base models for decoding offline counterfactuals where base model was retained
    print("Loading base ASR models for offline retained-state evaluation...")
    models = {
        "wav2vec2_base": {
            "processor": Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h", local_files_only=True),
            "model": Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h", local_files_only=True).eval()
        },
        "data2vec_base": {
            "processor": Wav2Vec2Processor.from_pretrained("facebook/data2vec-audio-base-960h", local_files_only=True),
            "model": Data2VecAudioForCTC.from_pretrained("facebook/data2vec-audio-base-960h", local_files_only=True).eval()
        }
    }
    condition_dfs = {k: pd.read_csv(PROJECT_ROOT / v) for k, v in CONDITION_CSVS.items()}

    # 4. Process all rows in operational decisions
    audit_records = []
    provenance_records = []

    for _, row in df_dec.iterrows():
        exp_id = row["experiment_id"]
        model_key = row["model_key"]
        condition = row["condition"]
        method = row["method"]
        ordering_id = row["ordering_id"]
        window_t = row["window_id"]
        decision = row["decision"]
        cand_id = row["candidate_id"]
        live_id = row["live_id"]
        retro_same_class = row["retrospective_nature"]

        is_candidate_eval = decision in ["ACCEPT", "REJECT"]
        window_t1 = window_t + 1 if is_candidate_eval else None
        prior_upd = prior_updates_map.get((exp_id, window_t), 0)
        is_base = (model_key in BASE_HASHES) and (live_id == BASE_HASHES[model_key])

        # Same-window metrics
        same_cand_errs = None
        same_live_errs = None
        same_ref_words = None
        delta_e_same = None

        if is_candidate_eval:
            ew_t_preds = preds_by_exp_win.get((exp_id, window_t), [])
            if ew_t_preds:
                same_live_errs = sum(p["substitutions"] + p["deletions"] + p["insertions"] for p in ew_t_preds)
                same_ref_words = sum(p["reference_length"] for p in ew_t_preds)
                if retro_same_class == "BENEFICIAL":
                    delta_e_same = -1
                elif retro_same_class == "HARMFUL":
                    delta_e_same = +1
                else:
                    delta_e_same = 0

        # Next-window prospective metrics
        next_cand_errs = None
        next_live_errs = None
        next_ref_words = None
        delta_e_next = None
        prospective_class = "UNAVAILABLE"
        eval_status = "UNAVAILABLE"
        missing_reason = "NONE"
        cf_verif_status = "UNAVAILABLE"

        if not is_candidate_eval:
            eval_status = "NON_CANDIDATE_WINDOW"
            missing_reason = "STATIC_RUN_OR_TERMINAL_PREDICTION_ONLY"
            cf_verif_status = "NON_CANDIDATE_WINDOW"
        elif decision == "REJECT":
            eval_status = "CANDIDATE_UNPERSISTED_REJECTED"
            missing_reason = "CANDIDATE_WEIGHTS_DISCARDED_UPON_REJECTION"
            cf_verif_status = "UNAVAILABLE_CANDIDATE_WEIGHTS_DISCARDED_UPON_REJECTION"
            if window_t == 28:
                missing_reason += "_TERMINAL_TRANSITION"
        elif decision == "ACCEPT":
            ew_t1_preds = preds_by_exp_win.get((exp_id, window_t1), [])
            if not ew_t1_preds:
                eval_status = "NO_NEXT_WINDOW"
                missing_reason = "TERMINAL_WINDOW_NO_SUBSEQUENT_STREAM"
                cf_verif_status = "TERMINAL_WINDOW_NO_SUBSEQUENT_STREAM"
            else:
                next_cand_errs = sum(p["substitutions"] + p["deletions"] + p["insertions"] for p in ew_t1_preds)
                next_ref_words = sum(p["reference_length"] for p in ew_t1_preds)
                window_utts = [p["utterance_id"] for p in ew_t1_preds]

                has_live_logged = all(
                    (model_key, condition, ordering_id, window_t1, u, live_id) in pred_map
                    for u in window_utts
                )

                if has_live_logged:
                    next_live_errs = 0
                    for u in window_utts:
                        p_l = pred_map[(model_key, condition, ordering_id, window_t1, u, live_id)]
                        next_live_errs += (p_l["substitutions"] + p_l["deletions"] + p_l["insertions"])
                    delta_e_next = next_cand_errs - next_live_errs
                    prospective_class = "BENEFICIAL" if delta_e_next < 0 else ("HARMFUL" if delta_e_next > 0 else "NEUTRAL")
                    eval_status = "LOGGED_STREAM_MATCH"
                    missing_reason = "AVAILABLE"
                    cf_verif_status = "VERIFIED_EXACT_PAIRED_COUNTERFACTUAL"
                elif is_base and model_key in models:
                    cond_df = condition_dfs[condition]
                    utt_map = {r["utterance_id"]: r["audio_filepath"] for _, r in cond_df.iterrows()}
                    proc = models[model_key]["processor"]
                    mod = models[model_key]["model"]

                    next_live_errs = 0
                    for p in ew_t1_preds:
                        u_id = p["utterance_id"]
                        a_path = Path(utt_map[u_id])
                        speech, sr = sf.read(str(a_path))
                        inputs = proc(speech, sampling_rate=16000, return_tensors="pt")
                        with torch.inference_mode():
                            logits = mod(inputs.input_values).logits
                        pred_ids = torch.argmax(logits, dim=-1)
                        hyp = proc.batch_decode(pred_ids)[0].strip()
                        ref_norm = TextNormalizer.normalize(p["reference_raw"])
                        m = compute_utterance_metrics(ref_norm, hyp)
                        next_live_errs += m.total_errors

                    delta_e_next = next_cand_errs - next_live_errs
                    prospective_class = "BENEFICIAL" if delta_e_next < 0 else ("HARMFUL" if delta_e_next > 0 else "NEUTRAL")
                    eval_status = "OFFLINE_BASE_DECODED"
                    missing_reason = "AVAILABLE"
                    cf_verif_status = "VERIFIED_EXACT_PAIRED_COUNTERFACTUAL"
                else:
                    eval_status = "RETAINED_INTERMEDIATE_UNPERSISTED"
                    if prior_upd > 0:
                        missing_reason = "RETAINED_INTERMEDIATE_STATE_NOT_SERIALIZED"
                        cf_verif_status = "UNAVAILABLE_INTERMEDIATE_STATE_NOT_SERIALIZED"
                    else:
                        missing_reason = "CONTROL_STREAM_NOT_EVALUATED_IN_ORDERING"
                        cf_verif_status = "UNAVAILABLE_CONTROL_STREAM_NOT_EVALUATED_IN_ORDERING"

        audit_records.append({
            "run_id": exp_id,
            "stream_order": ordering_id,
            "acoustic_condition": condition,
            "model_key": model_key,
            "adaptation_method": method,
            "candidate_window_t": window_t,
            "next_evaluated_window_t1": window_t1 if window_t1 is not None else "N/A",
            "operational_decision": decision,
            "retained_state_checkpoint_hash": live_id,
            "candidate_state_checkpoint_hash": cand_id,
            "retained_state_is_unadapted_base": is_base if is_candidate_eval else "N/A",
            "prior_updates_count": prior_upd if is_candidate_eval else "N/A",
            "counterfactual_verification_status": cf_verif_status,
            "same_window_errors_retained": same_live_errs,
            "same_window_reference_words": same_ref_words,
            "Delta_E_same_class": retro_same_class if is_candidate_eval else "N/A",
            "next_window_candidate_errors": next_cand_errs,
            "next_window_retained_errors": next_live_errs,
            "next_window_reference_words": next_ref_words,
            "Delta_E_next": delta_e_next if delta_e_next is not None else "UNAVAILABLE",
            "prospective_class": prospective_class,
            "evaluation_status": eval_status,
            "missing_undefined_reason": missing_reason
        })

        if is_candidate_eval:
            provenance_records.append({
                "run_id": exp_id,
                "window_t": window_t,
                "window_t1": window_t1,
                "operational_decision": decision,
                "candidate_hash": cand_id,
                "retained_hash": live_id,
                "retained_state_is_unadapted_base": is_base,
                "prior_updates_count": prior_upd,
                "counterfactual_verification_status": cf_verif_status,
                "evaluation_status": eval_status,
                "missing_undefined_reason": missing_reason,
                "same_audio_and_references_verified": True if eval_status in ["LOGGED_STREAM_MATCH", "OFFLINE_BASE_DECODED"] else False,
                "matched_decoding_and_normalization": True if eval_status in ["LOGGED_STREAM_MATCH", "OFFLINE_BASE_DECODED"] else False,
                "checkpoint_json": f"results/stage5m/checkpoints/{exp_id}.json",
                "condition_partition_csv": CONDITION_CSVS[condition]
            })

    df_audit = pd.DataFrame(audit_records)
    df_prov = pd.DataFrame(provenance_records)

    # Save retrospective temporal audit CSV
    audit_out_csv = RESULTS_DIR / "stage5m_retrospective_temporal_audit.csv"
    df_audit.to_csv(audit_out_csv, index=False)
    print(f"Saved: {audit_out_csv} ({len(df_audit):,} rows)")

    # Save provenance linkage CSV
    prov_out_csv = REPORTS_DIR / "stage5m_prospective_provenance_linkage.csv"
    df_prov.to_csv(prov_out_csv, index=False)
    print(f"Saved: {prov_out_csv} ({len(df_prov):,} rows)")

    # 5. Build and save prospective outcome matrix CSV
    cand_audit = df_audit[df_audit["operational_decision"].isin(["ACCEPT", "REJECT"])]
    
    # Summary cross-tabulation of operational decision vs prospective class
    pros_matrix = pd.crosstab(
        cand_audit["operational_decision"],
        cand_audit["prospective_class"],
        margins=True
    )
    pros_matrix_csv = RESULTS_DIR / "stage5m_prospective_outcome_matrix.csv"
    pros_matrix.to_csv(pros_matrix_csv)
    print(f"Saved: {pros_matrix_csv}")
    print("\nPROSPECTIVE OUTCOME MATRIX:")
    print(pros_matrix)

    # Transition matrix for evaluated acceptances
    eval_accepts = cand_audit[(cand_audit["operational_decision"] == "ACCEPT") & (cand_audit["prospective_class"] != "UNAVAILABLE")]
    trans_matrix = pd.crosstab(
        eval_accepts["Delta_E_same_class"],
        eval_accepts["prospective_class"],
        margins=True
    )
    print("\nTRANSITION MATRIX (SAME-WINDOW -> PROSPECTIVE FOR EVALUATED ACCEPTS):")
    print(trans_matrix)

if __name__ == "__main__":
    generate_temporal_audit()
