import os
import time
import math
import hashlib
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.online.stream import PrequentialStream
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.offline.metrics import compute_utterance_metrics
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.adaptation.dmsuta import DmsutaAdapter

def run_dmsuta_collapse_diagnostics():
    print("=== Replaying wav2vec2_100h / DMSUTA / ORDER_C for Collapse Diagnostics ===")
    split_csv = "datasets/splits/final_test.csv"
    utts = load_partition_from_csv(split_csv)
    
    stream = PrequentialStream(
        utterances=utts,
        window_size_k=4,
        ordering_id="ORDER_C",
        seed=42
    )
    
    asr_model = create_asr_model("wav2vec2_100h", device="cpu")
    asr_model.load_model()
    model = asr_model.model
    processor = asr_model.processor
    
    # Cache initial anchor parameters theta_0 for drift computation
    anchor_params = {k: v.clone().detach().cpu() for k, v in model.named_parameters()}
    
    adapter = DmsutaAdapter(
        asr_model=asr_model,
        config={"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
    )
    
    diagnostic_rows = []
    
    for batch_idx, batch_utts, unlabeled_batch in stream.generate_windows():
        print(f"\n--- Window {batch_idx:02d} --- ({[u.utterance_id for u in batch_utts]})")
        
        # 1. Prequential inference under current active model theta_t
        model.eval()
        total_frames = 0
        blank_frames = 0
        blank_probs_sum = 0.0
        nonblank_token_count = 0
        total_hyp_chars = 0
        total_hyp_words = 0
        total_ref_words = 0
        window_errors = 0
        
        window_hyps = []
        for u in batch_utts:
            audio_path = u.audio_filepath
            from dsg_ctta.data.acoustic import load_and_resample_audio
            wav, sr = load_and_resample_audio(audio_path, target_sr=16000)
            inp = processor(wav, sampling_rate=16000, return_tensors="pt", padding=True)
            inp_vals = inp.input_values.to("cpu")
            
            with torch.no_grad():
                logits = model(inp_vals).logits # (1, T, V)
                probs = torch.softmax(logits, dim=-1) # (1, T, V)
            
            # CTC Blank token is index 0
            blank_idx = 0
            pred_tokens = torch.argmax(logits, dim=-1)[0] # (T,)
            
            T = logits.shape[1]
            total_frames += T
            b_cnt = int((pred_tokens == blank_idx).sum().item())
            blank_frames += b_cnt
            nonblank_token_count += (T - b_cnt)
            blank_probs_sum += float(probs[0, :, blank_idx].sum().item())
            
            # Greedy decode
            decoded_str = processor.batch_decode(pred_tokens.unsqueeze(0))[0].strip()
            window_hyps.append(decoded_str)
            
            norm_hyp = TextNormalizer.normalize(decoded_str)
            total_hyp_chars += len(norm_hyp.replace(" ", ""))
            total_hyp_words += len(norm_hyp.split()) if norm_hyp else 0
            
            met = compute_utterance_metrics(u.reference_normalized, decoded_str)
            total_ref_words += met.reference_length
            window_errors += (met.substitutions + met.deletions + met.insertions)
            
        blank_fraction = (blank_frames / total_frames) if total_frames > 0 else 0.0
        mean_blank_prob = (blank_probs_sum / total_frames) if total_frames > 0 else 0.0
        win_wer = (window_errors / total_ref_words) if total_ref_words > 0 else 0.0
        
        # Compute Parameter Drift from theta_0: L2 norm of parameter differences
        param_drift_sq = 0.0
        for name, param in model.named_parameters():
            if name in anchor_params:
                diff = param.detach().cpu() - anchor_params[name]
                param_drift_sq += float(torch.sum(diff ** 2).item())
        param_drift_l2 = math.sqrt(param_drift_sq)
        
        # Check active model bank candidates and their entropy
        waveforms = unlabeled_batch.load_waveforms()
        inputs = processor(waveforms, sampling_rate=16000, return_tensors="pt", padding=True)
        input_values = inputs.input_values.to("cpu")
        
        bank_entropies = {}
        with torch.no_grad():
            for item in adapter.model_bank:
                model.load_state_dict(item["state_dict"])
                out = model(input_values)
                p = torch.softmax(out.logits / adapter.temperature, dim=-1)
                bank_entropies[item["id"]] = float(adapter._compute_entropy(p).item())
        
        # Restore active model before adapt
        # 2. Adaptation step
        # Track gradient norm during adapt
        best_ckpt_id, selected_ent = adapter.select_best_checkpoint(input_values)
        
        # Local adaptation step
        model.train()
        adapter.optimizer.zero_grad()
        out = model(input_values)
        p = torch.softmax(out.logits / adapter.temperature, dim=-1)
        
        # Check for NaN / Inf in logits
        has_nan_logits = bool(torch.isnan(out.logits).any().item())
        has_inf_logits = bool(torch.isinf(out.logits).any().item())
        
        l_em = adapter._compute_entropy(p)
        l_mcc = adapter._compute_mcc_loss(p)
        total_loss = adapter.alpha * l_em + (1.0 - adapter.alpha) * l_mcc
        
        total_loss.backward()
        
        # Compute gradient norm across trainable parameters
        grad_norm_sq = 0.0
        has_nan_grad = False
        for param in model.parameters():
            if param.requires_grad and param.grad is not None:
                if torch.isnan(param.grad).any():
                    has_nan_grad = True
                grad_norm_sq += float(torch.sum(param.grad ** 2).item())
        grad_norm = math.sqrt(grad_norm_sq)
        
        adapter.optimizer.step()
        model.eval()
        
        # Post-adapt entropy
        with torch.no_grad():
            post_out = model(input_values)
            post_p = torch.softmax(post_out.logits / adapter.temperature, dim=-1)
            post_ent = float(adapter._compute_entropy(post_p).item())
            
        new_ckpt_id = f"theta_w{batch_idx}"
        new_state = {k: v.clone().cpu() for k, v in model.state_dict().items()}
        adapter.model_bank.append({
            "id": new_ckpt_id,
            "state_dict": new_state,
            "entropy": post_ent,
            "is_anchor": False
        })
        
        pruned_id = "none"
        if len(adapter.model_bank) > adapter.max_bank_size:
            non_anchors = [it for it in adapter.model_bank if not it.get("is_anchor", False)]
            if non_anchors:
                worst_non_anchor = max(non_anchors, key=lambda it: it["entropy"])
                pruned_id = worst_non_anchor["id"]
                adapter.model_bank.remove(worst_non_anchor)
                
        primary_group = list(set(u.group_id for u in batch_utts))[0]
        sample_transcript = window_hyps[0][:50] if window_hyps else ""
        
        row = {
            "window_id": batch_idx,
            "primary_group": primary_group,
            "total_frames": total_frames,
            "blank_frames": blank_frames,
            "blank_frame_fraction": round(blank_fraction, 4),
            "mean_blank_probability": round(mean_blank_prob, 4),
            "nonblank_token_count": nonblank_token_count,
            "total_hyp_words": total_hyp_words,
            "total_ref_words": total_ref_words,
            "window_wer": round(win_wer, 4),
            "sample_hypothesis": sample_transcript,
            "bank_size_before": len(bank_entropies),
            "selected_checkpoint": best_ckpt_id,
            "selected_entropy": round(selected_ent, 4),
            "adapted_entropy": round(post_ent, 4),
            "pruned_checkpoint": pruned_id,
            "loss_em": round(float(l_em.item()), 4),
            "loss_mcc": round(float(l_mcc.item()), 4),
            "loss_total": round(float(total_loss.item()), 4),
            "grad_norm": round(grad_norm, 4),
            "param_drift_l2": round(param_drift_l2, 4),
            "has_nan_inf": bool(has_nan_logits or has_inf_logits or has_nan_grad)
        }
        diagnostic_rows.append(row)
        print(f"Win {batch_idx:02d}: group={primary_group} | WER={win_wer:.4f} | BlankFrac={blank_fraction*100:.2f}% | MeanBlankProb={mean_blank_prob:.4f} | NonBlankTokens={nonblank_token_count} | HypWords={total_hyp_words}/{total_ref_words} | CkptSelected={best_ckpt_id} | SelEnt={selected_ent:.4f} -> PostEnt={post_ent:.4f} | DriftL2={param_drift_l2:.4f}")
        
    df = pd.DataFrame(diagnostic_rows)
    os.makedirs("reports/stage3m", exist_ok=True)
    out_path = "reports/stage3m/stage3m_collapse_diagnostics.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved diagnostics to {out_path}")
    print(df.to_string())

if __name__ == "__main__":
    run_dmsuta_collapse_diagnostics()
