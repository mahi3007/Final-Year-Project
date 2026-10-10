"""
Prequential CTTA Experiment Runner (Stage 3 Discovery).
Executes strictly prequential online adaptation:
  For each window B_t:
    1. theta_t predicts B_t
    2. predictions recorded
    3. offline evaluation scores B_t against hidden reference
    4. unlabeled B_t passed to adapter -> produces theta_(t+1)
    5. advance to B_(t+1)
Exports canonical Stage 3 artifacts:
  predictions.csv, window_metrics.csv, group_metrics.csv,
  adaptation_trajectory.csv, experiment_manifest.json, summary.json
"""

from __future__ import annotations
import os
import gc
import json
import time
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import torch
from rich.console import Console
from rich.progress import track

from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.models.base_adapter import BaseASRModel
from dsg_ctta.online.stream import PrequentialStream, PrequentialPredictionRecord
from dsg_ctta.online.label_isolation import LabelIsolationSanitizer
from dsg_ctta.offline.metrics import compute_utterance_metrics, EditCounts
from dsg_ctta.adaptation.base import BaseTestTimeAdapter, AdaptationStepResult
from dsg_ctta.adaptation.no_adapt import NoAdaptationAdapter

console = Console()


def create_ctta_adapter(
    method_name: str,
    asr_model: BaseASRModel,
    adapter_config: Optional[Dict[str, Any]] = None
) -> BaseTestTimeAdapter:
    """Factory to instantiate the appropriate CTTA adapter."""
    config = adapter_config or {}
    method_lower = method_name.lower()

    if method_lower == "no_adapt":
        return NoAdaptationAdapter(asr_model=asr_model, config=config)
    elif method_lower == "suta":
        from dsg_ctta.adaptation.suta import SutaAdapter
        return SutaAdapter(asr_model=asr_model, config=config)
    elif method_lower == "dsuta":
        from dsg_ctta.adaptation.dsuta import DsutaAdapter
        return DsutaAdapter(asr_model=asr_model, config=config)
    elif method_lower == "dmsuta":
        from dsg_ctta.adaptation.dmsuta import DmsutaAdapter
        return DmsutaAdapter(asr_model=asr_model, config=config)
    else:
        raise ValueError(
            f"Unsupported CTTA method: '{method_name}'. "
            f"Supported methods: ['no_adapt', 'suta', 'dsuta', 'dmsuta']"
        )


def run_prequential_stream_experiment(
    utterances: List[UtteranceMetadata],
    model_name: str = "wav2vec2_base",
    method_name: str = "no_adapt",
    adapter_config: Optional[Dict[str, Any]] = None,
    ordering_id: str = "ORDER_A",
    window_size_k: int = 4,
    device: str = "cpu",
    output_dir: Optional[str] = None,
    seed: int = 42,
    experiment_id: Optional[str] = None,
    stream_id: Optional[str] = None,
    skip_terminal_update: bool = False,
    asr_model: Optional[BaseASRModel] = None
) -> Dict[str, Any]:
    """
    Execute a single, strict prequential CTTA experiment across a sequential stream.
    Invariant: B_t is evaluated strictly using theta_t, never theta_(t+1).
    """
    if experiment_id is None:
        experiment_id = f"exp_{method_name}_{model_name}_{ordering_id.lower()}_k{window_size_k}_s{seed}"

    if output_dir is None:
        output_dir = os.path.join("reports", "ctta", method_name)
    os.makedirs(output_dir, exist_ok=True)

    console.print(f"[bold cyan]=====================================================[/bold cyan]")
    console.print(f"[bold cyan]Stage 3 Prequential Experiment:[/bold cyan] [yellow]{experiment_id}[/yellow]")
    console.print(f"Model: [green]{model_name}[/green] | Method: [yellow]{method_name}[/yellow] | Ordering: [magenta]{ordering_id}[/magenta] | K={window_size_k}")
    console.print(f"[bold cyan]=====================================================[/bold cyan]")

    # 1. Initialize Prequential Stream
    stream = PrequentialStream(
        utterances=utterances,
        window_size_k=window_size_k,
        ordering_id=ordering_id,
        stream_id=stream_id,
        seed=seed
    )

    console.print(f"Stream ID: [cyan]{stream.stream_id}[/cyan] | Hash: [dim]{stream.stream_hash[:16]}...[/dim]")
    console.print(f"Total Utterances: [green]{stream.total_utterances}[/green] across [yellow]{stream.total_batches}[/yellow] windows.")

    # 2. Instantiate Live ASR Model
    if asr_model is None:
        asr_model = create_asr_model(model_name, device=device)
        asr_model.load_model()

    # 3. Instantiate CTTA Adapter
    adapter = create_ctta_adapter(
        method_name=method_name,
        asr_model=asr_model,
        adapter_config=adapter_config
    )

    # 4. Containers for Prequential Logging & Metrics
    prediction_records: List[Dict[str, Any]] = []
    window_records: List[Dict[str, Any]] = []
    trajectory_records: List[Dict[str, Any]] = []

    # Running cumulative counters
    cumulative_s = 0
    cumulative_d = 0
    cumulative_i = 0
    cumulative_n = 0
    cumulative_s_c = 0
    cumulative_d_c = 0
    cumulative_i_c = 0
    cumulative_n_c = 0

    group_counts: Dict[str, Dict[str, int]] = {}
    speaker_counts: Dict[str, Dict[str, int]] = {}

    total_infer_time = 0.0
    total_adapt_time = 0.0
    num_updates = 0
    num_resets = 0

    # 5. Prequential Streaming Loop
    for batch_idx, batch_utts, unlabeled_batch in stream.generate_windows():
        theta_before_hash = adapter.compute_model_hash()

        # STEP A: Live Inference on B_t using theta_t
        window_hypotheses: List[str] = []
        window_infer_start = time.time()
        for u in batch_utts:
            hyp = asr_model.transcribe(u.audio_filepath)
            window_hypotheses.append(hyp)
        window_infer_time = time.time() - window_infer_start
        total_infer_time += window_infer_time

        # STEP B: Offline Evaluation of B_t under theta_t (Strictly Offline)
        win_s = 0
        win_d = 0
        win_i = 0
        win_n = 0
        win_s_c = 0
        win_d_c = 0
        win_i_c = 0
        win_n_c = 0
        group_dist: Dict[str, int] = {}

        for u, hyp in zip(batch_utts, window_hypotheses):
            metrics = compute_utterance_metrics(u.reference_normalized, hyp)
            win_s += metrics.substitutions
            win_d += metrics.deletions
            win_i += metrics.insertions
            win_n += metrics.reference_length

            # Character level
            ref_chars = list(u.reference_normalized.replace(" ", ""))
            hyp_chars = list(TextNormalizer.normalize(hyp).replace(" ", ""))
            win_n_c += len(ref_chars)
            # cer counts
            if metrics.reference_length > 0:
                win_s_c += int(metrics.cer * len(ref_chars))  # approximate char count or exact from metrics
            
            gid = u.group_id
            spk = u.speaker_id
            group_dist[gid] = group_dist.get(gid, 0) + 1

            if gid not in group_counts:
                group_counts[gid] = {"s": 0, "d": 0, "i": 0, "n": 0, "n_c": 0, "err_c": 0, "utts": 0, "speakers": set()}
            group_counts[gid]["s"] += metrics.substitutions
            group_counts[gid]["d"] += metrics.deletions
            group_counts[gid]["i"] += metrics.insertions
            group_counts[gid]["n"] += metrics.reference_length
            group_counts[gid]["utts"] += 1
            group_counts[gid]["speakers"].add(spk)

            if spk not in speaker_counts:
                speaker_counts[spk] = {"s": 0, "d": 0, "i": 0, "n": 0}
            speaker_counts[spk]["s"] += metrics.substitutions
            speaker_counts[spk]["d"] += metrics.deletions
            speaker_counts[spk]["i"] += metrics.insertions
            speaker_counts[spk]["n"] += metrics.reference_length

            # Record detailed prediction row
            prediction_records.append({
                "experiment_id": experiment_id,
                "stream_id": stream.stream_id,
                "ordering_id": ordering_id,
                "window_id": batch_idx,
                "utterance_id": u.utterance_id,
                "speaker_id": u.speaker_id,
                "group_id": u.group_id,
                "device_id": u.device_id,
                "snr_db": u.snr_db,
                "speech_rate_wpm": u.speech_rate_wpm,
                "reference_raw": u.reference_raw,
                "reference_normalized": u.reference_normalized,
                "hypothesis_raw": hyp,
                "hypothesis_normalized": TextNormalizer.normalize(hyp),
                "substitutions": metrics.substitutions,
                "deletions": metrics.deletions,
                "insertions": metrics.insertions,
                "hits": metrics.hits,
                "reference_length": metrics.reference_length,
                "hypothesis_length": metrics.hypothesis_length,
                "wer": round(metrics.wer, 4),
                "cer": round(metrics.cer, 4),
                "theta_version": theta_before_hash,
                "inference_time_seconds": round(window_infer_time / len(batch_utts), 4)
            })

        # Cumulative updates
        cumulative_s += win_s
        cumulative_d += win_d
        cumulative_i += win_i
        cumulative_n += win_n

        window_wer = (win_s + win_d + win_i) / win_n if win_n > 0 else 0.0
        cum_wer = (cumulative_s + cumulative_d + cumulative_i) / cumulative_n if cumulative_n > 0 else 0.0

        # STEP C: Unlabeled Adaptation on B_t -> theta_(t+1)
        if skip_terminal_update and (batch_idx == stream.total_batches - 1):
            adapt_res = AdaptationStepResult(
                batch_idx=batch_idx,
                method_id=method_name,
                theta_before_hash=theta_before_hash,
                theta_after_hash=theta_before_hash,
                updated=False,
                reset_occurred=False,
                adaptation_time_seconds=0.0,
                loss_history=[],
                details={"terminal_window_skipped": True}
            )
        else:
            adapt_res: AdaptationStepResult = adapter.adapt(unlabeled_batch)
        total_adapt_time += adapt_res.adaptation_time_seconds
        if adapt_res.updated:
            num_updates += 1
        if adapt_res.reset_occurred:
            num_resets += 1

        theta_after_hash = adapt_res.theta_after_hash

        # Compute current cumulative group WERs and disparity
        curr_group_wers: Dict[str, float] = {}
        for gid, gc_data in group_counts.items():
            tot_g_err = gc_data["s"] + gc_data["d"] + gc_data["i"]
            tot_g_n = gc_data["n"]
            curr_group_wers[gid] = (tot_g_err / tot_g_n) if tot_g_n > 0 else 0.0

        if len(curr_group_wers) > 1:
            cum_disparity = max(curr_group_wers.values()) - min(curr_group_wers.values())
        else:
            cum_disparity = 0.0

        # STEP D: Record Window Summary
        window_records.append({
            "experiment_id": experiment_id,
            "stream_id": stream.stream_id,
            "window_id": batch_idx,
            "window_size": len(batch_utts),
            "recording_ids": ",".join([u.utterance_id for u in batch_utts]),
            "group_distribution": json.dumps(group_dist),
            "substitutions": win_s,
            "deletions": win_d,
            "insertions": win_i,
            "reference_words": win_n,
            "window_wer": round(window_wer, 4),
            "cumulative_wer": round(cum_wer, 4),
            "cumulative_disparity": round(cum_disparity, 4),
            "theta_before_hash": theta_before_hash,
            "theta_after_hash": theta_after_hash,
            "adaptation_updated": adapt_res.updated,
            "adaptation_reset": adapt_res.reset_occurred,
            "adaptation_time_seconds": round(adapt_res.adaptation_time_seconds, 4),
            "inference_time_seconds": round(window_infer_time, 4)
        })

        # STEP E: Record Adaptation Trajectory Point
        traj_point = {
            "window_id": batch_idx,
            "cumulative_utterances": len(prediction_records),
            "cumulative_words": cumulative_n,
            "cumulative_wer": round(cum_wer, 4),
            "cumulative_disparity": round(cum_disparity, 4),
            "theta_after_hash": theta_after_hash,
            "adaptation_updated": adapt_res.updated,
            "adaptation_reset": adapt_res.reset_occurred,
            "adaptation_time_seconds": round(adapt_res.adaptation_time_seconds, 4),
            "inference_time_seconds": round(window_infer_time, 4)
        }
        for gid, g_wer in curr_group_wers.items():
            traj_point[f"wer_group_{gid}"] = round(g_wer, 4)
        trajectory_records.append(traj_point)

    # 6. Aggregate Final Corpus & Group Metrics
    final_corpus_wer = (cumulative_s + cumulative_d + cumulative_i) / cumulative_n if cumulative_n > 0 else 0.0
    spk_wers = [
        (data["s"] + data["d"] + data["i"]) / data["n"]
        for data in speaker_counts.values()
        if data["n"] > 0
    ]
    speaker_macro_wer = float(np.mean(spk_wers)) if spk_wers else 0.0

    final_group_metrics_rows: List[Dict[str, Any]] = []
    final_group_wers: Dict[str, float] = {}

    for gid, gc_data in sorted(group_counts.items()):
        tot_err = gc_data["s"] + gc_data["d"] + gc_data["i"]
        tot_n = gc_data["n"]
        g_wer = (tot_err / tot_n) if tot_n > 0 else 0.0
        final_group_wers[gid] = g_wer

        # Speaker macro within group
        g_spk_wers = [
            (speaker_counts[s]["s"] + speaker_counts[s]["d"] + speaker_counts[s]["i"]) / speaker_counts[s]["n"]
            for s in gc_data["speakers"]
            if speaker_counts[s]["n"] > 0
        ]
        g_spk_macro = float(np.mean(g_spk_wers)) if g_spk_wers else 0.0

        final_group_metrics_rows.append({
            "group_id": gid,
            "num_speakers": len(gc_data["speakers"]),
            "num_utterances": gc_data["utts"],
            "reference_words": tot_n,
            "substitutions": gc_data["s"],
            "deletions": gc_data["d"],
            "insertions": gc_data["i"],
            "total_errors": tot_err,
            "corpus_wer": round(g_wer, 4),
            "speaker_macro_wer": round(g_spk_macro, 4),
            "substitution_ratio": round(gc_data["s"] / tot_err, 4) if tot_err > 0 else 0.0,
            "deletion_ratio": round(gc_data["d"] / tot_err, 4) if tot_err > 0 else 0.0,
            "insertion_ratio": round(gc_data["i"] / tot_err, 4) if tot_err > 0 else 0.0
        })

    if final_group_wers:
        best_gid = min(final_group_wers, key=final_group_wers.get)
        worst_gid = max(final_group_wers, key=final_group_wers.get)
        final_disparity = final_group_wers[worst_gid] - final_group_wers[best_gid]
        final_ratio = (final_group_wers[worst_gid] / final_group_wers[best_gid]) if final_group_wers[best_gid] > 0 else 1.0
    else:
        best_gid, worst_gid = "none", "none"
        final_disparity, final_ratio = 0.0, 1.0

    # 7. Write All CSV Files
    df_pred = pd.DataFrame(prediction_records)
    pred_path = os.path.join(output_dir, "predictions.csv")
    df_pred.to_csv(pred_path, index=False)

    df_win = pd.DataFrame(window_records)
    win_path = os.path.join(output_dir, "window_metrics.csv")
    df_win.to_csv(win_path, index=False)

    df_grp = pd.DataFrame(final_group_metrics_rows)
    grp_path = os.path.join(output_dir, "group_metrics.csv")
    df_grp.to_csv(grp_path, index=False)

    df_traj = pd.DataFrame(trajectory_records)
    traj_path = os.path.join(output_dir, "adaptation_trajectory.csv")
    df_traj.to_csv(traj_path, index=False)

    # 8. Write Experiment Manifest JSON
    manifest_data = {
        "experiment_id": experiment_id,
        "protocol_version": "v1.0.0-canonical",
        "stream_id": stream.stream_id,
        "ordering_id": ordering_id,
        "seed": seed,
        "stream_hash": stream.stream_hash,
        "model_id": model_name,
        "method_id": method_name,
        "window_size_k": window_size_k,
        "total_windows": stream.total_batches,
        "total_utterances": stream.total_utterances,
        "total_reference_words": cumulative_n,
        "adapter_config": adapter_config or {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "output_files": {
            "predictions_csv": pred_path,
            "window_metrics_csv": win_path,
            "group_metrics_csv": grp_path,
            "adaptation_trajectory_csv": traj_path
        }
    }
    manifest_path = os.path.join(output_dir, "experiment_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 9. Write Summary JSON
    summary_data = {
        "experiment_id": experiment_id,
        "method_id": method_name,
        "model_id": model_name,
        "stream_id": stream.stream_id,
        "ordering_id": ordering_id,
        "window_size_k": window_size_k,
        "total_utterances": len(prediction_records),
        "total_reference_words": cumulative_n,
        "corpus_wer": round(final_corpus_wer, 4),
        "speaker_macro_wer": round(speaker_macro_wer, 4),
        "disparity_d": round(final_disparity, 4),
        "disparity_ratio_r": round(final_ratio, 3),
        "best_group_id": best_gid,
        "worst_group_id": worst_gid,
        "total_adaptation_time_seconds": round(total_adapt_time, 4),
        "total_inference_time_seconds": round(total_infer_time, 4),
        "num_updates": num_updates,
        "num_resets": num_resets,
        "group_wers": {k: round(v, 4) for k, v in final_group_wers.items()}
    }
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    console.print(f"[bold green]Experiment {experiment_id} completed successfully![/bold green]")
    console.print(f"Corpus WER: [yellow]{final_corpus_wer:.4f}[/yellow] | Disparity D: [magenta]{final_disparity:.4f}[/magenta]")

    # Memory cleanup
    del asr_model
    del adapter
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "summary": summary_data,
        "manifest": manifest_data,
        "files": {
            "predictions": pred_path,
            "window_metrics": win_path,
            "group_metrics": grp_path,
            "adaptation_trajectory": traj_path,
            "experiment_manifest": manifest_path,
            "summary": summary_path
        }
    }
