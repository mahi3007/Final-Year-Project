"""
Stage 4M Multi-Model Acoustic Stress & Boundary Characterization Runner
======================================================================
Protocol: v1.1.0-model-expansion
Review Decision: GO — Stage 4M Authorized to Execute
Standard: ADR-005

Executes the frozen Stage 4M experimental matrix:
- 3 CTC Development Backbones (wav2vec2_base, data2vec_base, wav2vec2_100h)
  x 4 Adaptation Methods (no_adapt, suta, dsuta, dmsuta)
  x 3 Stream Orderings (ORDER_A, ORDER_B, ORDER_C)
  x 5 Acoustic Conditions (clean, noise_15db, noise_5db, babble_15db, reverb_t60_04)
  = 180 nominal factorial cells (150 canonical settings, 18,000 canonical records)
- 3 Seq2Seq Portability Controls (whisper_base, distil_whisper_small, whisper_tiny)
  x static No-Adapt x 5 Acoustic Conditions on ORDER_A
  = 15 control cells
- K-Sweep Sensitivity Checks (K in {2, 8}) on wav2vec2_base + suta
  x 3 Conditions (clean, noise_5db, reverb_t60_04)
  = 6 sensitivity cells

Outputs:
- results/stage4_multimodel/
- results/stage4_multimodel/stage4m_full_results.csv
- results/stage4_multimodel/stage4m_canonical_results.csv
- results/stage4_multimodel/stage4m_bootstrap_uncertainty.csv
- results/stage4_multimodel/stage4m_canonical_glmm_results.json
- results/stage4_multimodel/stage4m_k_sweep_results.csv
- results/stage4_multimodel/stage4m_empty_hypotheses_diagnostic.csv
- manifests/stage4m_experiment_manifest.json
"""

import os
import sys
import json
import time
import copy
import hashlib
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import torch
import transformers
from rich.console import Console

# Suppress HuggingFace generation warnings (e.g. max_new_tokens vs max_length precedence)
transformers.logging.set_verbosity_error()
warnings.filterwarnings("ignore", message=".*Both `max_new_tokens`.*")

from dsg_ctta.data.schema import UtteranceMetadata
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment
from dsg_ctta.models.registry import MODEL_CATALOG, create_asr_model
from dsg_ctta.data.normalization import TextNormalizer
from dsg_ctta.controller.gate import DisparitySafetyGate
from dsg_ctta.controller.types import BootstrapMetrics

console = Console()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONDITIONS = {
    "clean": "datasets/splits/stage4_characterization.csv",
    "noise_15db": "datasets/splits/stage4_noise_moderate.csv",
    "noise_5db": "datasets/splits/stage4_noise_severe.csv",
    "babble_15db": "datasets/splits/stage4_babble_moderate.csv",
    "reverb_t60_04": "datasets/splits/stage4_reverberation.csv"
}

CTC_MODELS = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
CTC_METHODS = ["no_adapt", "suta", "dsuta", "dmsuta"]
ACTIVE_METHODS = ["suta", "dsuta", "dmsuta"]
ORDERS = ["ORDER_A", "ORDER_B", "ORDER_C"]
SEQ2SEQ_MODELS = ["whisper_base", "distil_whisper_small", "whisper_tiny"]

ADAPTER_CONFIGS = {
    "no_adapt": {},
    "suta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1},
    "dsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
    "dmsuta": {"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3}
}


def get_git_commit() -> str:
    try:
        import subprocess
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=PROJECT_ROOT)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "uncommitted_workspace_state"


def derive_run_seed(experiment_id: str, base_seed: int = 42) -> int:
    h = hashlib.sha256(f"{experiment_id}_{base_seed}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % (2**31 - 1)


def run_single_cell(
    model_name: str,
    method: str,
    condition: str,
    order_id: str,
    utterances: List[UtteranceMetadata],
    out_dir: Path,
    k: int = 4,
    device: str = "cpu",
    asr_model: Optional[Any] = None,
    init_weights: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    exp_id = f"EXP_v1.1.0_STAGE4M_{model_name}_{condition}_{method}_{order_id.lower()}_k{k}"
    sum_path = out_dir / "summary.json"
    pred_path = out_dir / "predictions.csv"
    
    if sum_path.exists() and pred_path.exists():
        console.print(f"[green]Resuming completed cell: {exp_id}[/green]")
        with open(sum_path, "r", encoding="utf-8") as f:
            sum_data = json.load(f)
        pred_df = pd.read_csv(pred_path)
        return sum_data, pred_df

    console.print(f"[yellow]Executing Cell: {exp_id}[/yellow]")
    t0 = time.time()
    run_seed = derive_run_seed(exp_id)
    
    if asr_model is not None and init_weights is not None:
        asr_model.model.load_state_dict(init_weights)
        
    res = run_prequential_stream_experiment(
        utterances=utterances,
        model_name=model_name,
        method_name=method,
        adapter_config=ADAPTER_CONFIGS[method],
        ordering_id=order_id,
        window_size_k=k,
        device=device,
        output_dir=str(out_dir),
        seed=run_seed,
        experiment_id=exp_id,
        skip_terminal_update=True,
        asr_model=asr_model
    )
    elapsed = time.time() - t0
    
    with open(sum_path, "r", encoding="utf-8") as f:
        sum_data = json.load(f)
    sum_data["elapsed_seconds"] = round(elapsed, 2)
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(sum_data, f, indent=2)
        
    pred_df = pd.read_csv(pred_path)
    return sum_data, pred_df


def stratified_paired_speaker_cluster_bootstrap(
    records_base: List[Dict[str, Any]],
    records_adapted: List[Dict[str, Any]],
    num_replicates: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Stratified Paired Speaker-Cluster Bootstrap.
    In each replicate, exactly 2 speakers are sampled with replacement
    within each of the 6 accent strata, preserving 100% group representation.
    """
    rng = np.random.RandomState(seed)
    df_base = pd.DataFrame(records_base)
    df_adapt = pd.DataFrame(records_adapted)
    
    assert len(df_base) == len(df_adapt), "Base and adapted record lengths mismatch"
    groups = sorted(df_base["group_id"].unique().tolist())
    
    # Pre-index by speaker
    base_spk_map = {s: df_base[df_base["speaker_id"] == s] for s in df_base["speaker_id"].unique()}
    adapt_spk_map = {s: df_adapt[df_adapt["speaker_id"] == s] for s in df_adapt["speaker_id"].unique()}
    
    group_spk_map = {}
    for g in groups:
        group_spk_map[g] = sorted(df_base[df_base["group_id"] == g]["speaker_id"].unique().tolist())
        assert len(group_spk_map[g]) == 2, f"Expected 2 speakers in stratum {g}"
        
    rep_delta_r = []
    rep_delta_d = []
    rep_max_delta_g = []
    rep_group_deltas = {g: [] for g in groups}
    
    for _ in range(num_replicates):
        resampled_spks = []
        for g in groups:
            spks_g = group_spk_map[g]
            resampled_spks.extend(rng.choice(spks_g, size=len(spks_g), replace=True))
            
        b_df = pd.concat([base_spk_map[s] for s in resampled_spks], ignore_index=True)
        a_df = pd.concat([adapt_spk_map[s] for s in resampled_spks], ignore_index=True)
        
        b_tot_w = b_df["reference_length"].sum()
        b_tot_e = b_df["substitutions"].sum() + b_df["deletions"].sum() + b_df["insertions"].sum()
        b_wer = b_tot_e / b_tot_w if b_tot_w > 0 else 0.0
        
        a_tot_w = a_df["reference_length"].sum()
        a_tot_e = a_df["substitutions"].sum() + a_df["deletions"].sum() + a_df["insertions"].sum()
        a_wer = a_tot_e / a_tot_w if a_tot_w > 0 else 0.0
        
        d_r = a_wer - b_wer
        rep_delta_r.append(d_r)
        
        b_gwers = {}
        a_gwers = {}
        curr_rep_dg = {}
        for g in groups:
            bg_df = b_df[b_df["group_id"] == g]
            bg_w = bg_df["reference_length"].sum()
            bg_e = bg_df["substitutions"].sum() + bg_df["deletions"].sum() + bg_df["insertions"].sum()
            bg_wer = bg_e / bg_w if bg_w > 0 else 0.0
            b_gwers[g] = bg_wer
            
            ag_df = a_df[a_df["group_id"] == g]
            ag_w = ag_df["reference_length"].sum()
            ag_e = ag_df["substitutions"].sum() + ag_df["deletions"].sum() + ag_df["insertions"].sum()
            ag_wer = ag_e / ag_w if ag_w > 0 else 0.0
            a_gwers[g] = ag_wer
            
            dg = ag_wer - bg_wer
            rep_group_deltas[g].append(dg)
            curr_rep_dg[g] = dg
            
        b_disp = max(b_gwers.values()) - min(b_gwers.values())
        a_disp = max(a_gwers.values()) - min(a_gwers.values())
        d_d = a_disp - b_disp
        rep_delta_d.append(d_d)
        rep_max_delta_g.append(max(curr_rep_dg.values()))
        
    def _pct(arr, p):
        return float(np.percentile(arr, p))
        
    return {
        "delta_r": {
            "point": float(np.mean(rep_delta_r)),
            "ci95": [_pct(rep_delta_r, (alpha / 2.0) * 100), _pct(rep_delta_r, (1.0 - alpha / 2.0) * 100)],
            "ucb95": _pct(rep_delta_r, (1.0 - alpha) * 100)
        },
        "max_delta_g": {
            "point": float(np.mean(rep_max_delta_g)),
            "ci95": [_pct(rep_max_delta_g, (alpha / 2.0) * 100), _pct(rep_max_delta_g, (1.0 - alpha / 2.0) * 100)],
            "ucb95": _pct(rep_max_delta_g, (1.0 - alpha) * 100)
        },
        "delta_d": {
            "point": float(np.mean(rep_delta_d)),
            "ci95": [_pct(rep_delta_d, (alpha / 2.0) * 100), _pct(rep_delta_d, (1.0 - alpha / 2.0) * 100)],
            "ucb95": _pct(rep_delta_d, (1.0 - alpha) * 100)
        },
        "group_deltas": {g: float(np.mean(rep_group_deltas[g])) for g in groups},
        "group_ucbs": {g: _pct(rep_group_deltas[g], (1.0 - alpha) * 100) for g in groups}
    }


def fit_secondary_glmm(
    df_canonical: pd.DataFrame,
    df_duplicated: pd.DataFrame
) -> Dict[str, Any]:
    """
    Fits the secondary mixed-effects model under Laplace marginal approximation:
    1. Canonical 34-parameter GLMM on 18,000 unique records.
    2. Sensitivity 36-parameter GLMM on 21,600 duplicated records.
    """
    import patsy
    console.print("\n[bold cyan]Fitting Secondary GLMM with Laplace Marginal Approximation...[/bold cyan]")
    
    # Canonical 34-parameter model
    formula_34 = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    dmat_34_raw = patsy.dmatrix(formula_34, data=df_canonical, return_type="dataframe")
    zero_cols = [c for c in dmat_34_raw.columns if np.all(dmat_34_raw[c] == 0)]
    dmat_34 = dmat_34_raw.drop(columns=zero_cols)
    assert dmat_34.shape[1] == 34, f"Expected 34 columns, got {dmat_34.shape[1]}"
    
    # Speaker and utterance index mapping
    spk_unique = sorted(df_canonical["speaker_id"].unique().tolist())
    utt_unique = sorted(df_canonical["utterance_id"].unique().tolist())
    spk_map = {s: i for i, s in enumerate(spk_unique)}
    utt_map = {u: i for i, u in enumerate(utt_unique)}
    
    X_34 = torch.tensor(dmat_34.values, dtype=torch.float32)
    y_34 = torch.tensor((df_canonical["substitutions"] + df_canonical["deletions"] + df_canonical["insertions"]).values, dtype=torch.float32)
    offset_34 = torch.tensor(np.log(df_canonical["reference_length"].values), dtype=torch.float32)
    spk_idx_34 = torch.tensor(df_canonical["speaker_id"].map(spk_map).values, dtype=torch.long)
    utt_idx_34 = torch.tensor(df_canonical["utterance_id"].map(utt_map).values, dtype=torch.long)
    
    n_spk = len(spk_unique)
    n_utt = len(utt_unique)
    n_obs_34 = len(y_34)
    
    # Fit canonical model
    beta_34 = torch.zeros(34, requires_grad=True)
    log_phi_34 = torch.tensor(np.log(8.0), requires_grad=True)
    log_sig_s_34 = torch.tensor(np.log(0.15), requires_grad=True)
    log_sig_u_34 = torch.tensor(np.log(0.10), requires_grad=True)
    b_s_34 = torch.zeros(n_spk, requires_grad=True)
    b_u_34 = torch.zeros(n_utt, requires_grad=True)
    
    opt_34 = torch.optim.Adam([beta_34, log_phi_34, log_sig_s_34, log_sig_u_34, b_s_34, b_u_34], lr=0.015)
    
    t0 = time.time()
    for _ in range(350):
        opt_34.zero_grad()
        phi = torch.exp(log_phi_34)
        sig_s = torch.exp(log_sig_s_34)
        sig_u = torch.exp(log_sig_u_34)
        
        eta = offset_34 + (X_34 @ beta_34) + b_s_34[spk_idx_34] + b_u_34[utt_idx_34]
        mu = torch.exp(eta)
        
        ll_data = (
            torch.lgamma(y_34 + phi) - torch.lgamma(phi) - torch.lgamma(y_34 + 1.0) +
            phi * torch.log(phi / (phi + mu)) + y_34 * torch.log(mu / (phi + mu))
        ).sum()
        
        ll_bs = -0.5 * torch.sum(b_s_34**2 / (sig_s**2)) - n_spk * torch.log(sig_s)
        ll_bu = -0.5 * torch.sum(b_u_34**2 / (sig_u**2)) - n_utt * torch.log(sig_u)
        
        # Exact observed negative curvature
        w_obs = (mu * (1.0 + y_34 / phi)) / ((1.0 + mu / phi)**2)
        h_s = torch.zeros(n_spk).scatter_add_(0, spk_idx_34, w_obs) + (1.0 / (sig_s**2))
        h_u = torch.zeros(n_utt).scatter_add_(0, utt_idx_34, w_obs) + (1.0 / (sig_u**2))
        
        log_det_h = 0.5 * (torch.sum(torch.log(h_s)) + torch.sum(torch.log(h_u)))
        loss = -(ll_data + ll_bs + ll_bu - log_det_h) / n_obs_34
        loss.backward()
        opt_34.step()
        
    fit_time_34 = time.time() - t0
    
    phi_est_34 = float(torch.exp(log_phi_34).item())
    sig_s_est_34 = float(torch.exp(log_sig_s_34).item())
    sig_u_est_34 = float(torch.exp(log_sig_u_34).item())
    
    console.print(f"[green]Canonical 34-Param GLMM fitted in {fit_time_34:.2f}s: phi={phi_est_34:.3f}, sigma_s={sig_s_est_34:.3f}, sigma_u={sig_u_est_34:.3f}[/green]")
    
    # Sensitivity 36-parameter model on 21,600 duplicated rows
    formula_36 = (
        "C(model, Treatment('wav2vec2_base')) + "
        "C(method, Treatment('no_adapt')) + "
        "C(condition, Treatment('clean')) + "
        "C(ordering, Treatment('ORDER_A')) + "
        "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
        "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
        "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
    )
    dmat_36 = patsy.dmatrix(formula_36, data=df_duplicated, return_type="dataframe")
    assert dmat_36.shape[1] == 36
    
    X_36 = torch.tensor(dmat_36.values, dtype=torch.float32)
    y_36 = torch.tensor((df_duplicated["substitutions"] + df_duplicated["deletions"] + df_duplicated["insertions"]).values, dtype=torch.float32)
    offset_36 = torch.tensor(np.log(df_duplicated["reference_length"].values), dtype=torch.float32)
    spk_idx_36 = torch.tensor(df_duplicated["speaker_id"].map(spk_map).values, dtype=torch.long)
    utt_idx_36 = torch.tensor(df_duplicated["utterance_id"].map(utt_map).values, dtype=torch.long)
    
    beta_36 = torch.zeros(36, requires_grad=True)
    log_phi_36 = torch.tensor(np.log(8.0), requires_grad=True)
    log_sig_s_36 = torch.tensor(np.log(0.15), requires_grad=True)
    log_sig_u_36 = torch.tensor(np.log(0.10), requires_grad=True)
    b_s_36 = torch.zeros(n_spk, requires_grad=True)
    b_u_36 = torch.zeros(n_utt, requires_grad=True)
    
    opt_36 = torch.optim.Adam([beta_36, log_phi_36, log_sig_s_36, log_sig_u_36, b_s_36, b_u_36], lr=0.015)
    
    for _ in range(350):
        opt_36.zero_grad()
        p = torch.exp(log_phi_36)
        ss = torch.exp(log_sig_s_36)
        su = torch.exp(log_sig_u_36)
        eta = offset_36 + (X_36 @ beta_36) + b_s_36[spk_idx_36] + b_u_36[utt_idx_36]
        mu = torch.exp(eta)
        ll_d = (
            torch.lgamma(y_36 + p) - torch.lgamma(p) - torch.lgamma(y_36 + 1.0) +
            p * torch.log(p / (p + mu)) + y_36 * torch.log(mu / (p + mu))
        ).sum()
        ll_bs = -0.5 * torch.sum(b_s_36**2 / (ss**2)) - n_spk * torch.log(ss)
        ll_bu = -0.5 * torch.sum(b_u_36**2 / (su**2)) - n_utt * torch.log(su)
        w_obs = (mu * (1.0 + y_36 / p)) / ((1.0 + mu / p)**2)
        h_s = torch.zeros(n_spk).scatter_add_(0, spk_idx_36, w_obs) + (1.0 / (ss**2))
        h_u = torch.zeros(n_utt).scatter_add_(0, utt_idx_36, w_obs) + (1.0 / (su**2))
        log_det_h = 0.5 * (torch.sum(torch.log(h_s)) + torch.sum(torch.log(h_u)))
        loss = -(ll_d + ll_bs + ll_bu - log_det_h) / len(y_36)
        loss.backward()
        opt_36.step()
        
    phi_est_36 = float(torch.exp(log_phi_36).item())
    sig_s_est_36 = float(torch.exp(log_sig_s_36).item())
    sig_u_est_36 = float(torch.exp(log_sig_u_36).item())
    
    # Map fixed effect coefficients
    coef_34_map = {col: float(beta_34[i].item()) for i, col in enumerate(dmat_34.columns)}
    coef_36_map = {col: float(beta_36[i].item()) for i, col in enumerate(dmat_36.columns)}
    
    return {
        "canonical_specification": {
            "formula": formula_34,
            "record_count": len(df_canonical),
            "settings_count": 150,
            "parameters_count": 34,
            "dispersion_phi": round(phi_est_34, 4),
            "speaker_sd_sigma_s": round(sig_s_est_34, 4),
            "utterance_sd_sigma_u": round(sig_u_est_34, 4),
            "coefficients": {k: round(v, 4) for k, v in coef_34_map.items()},
            "fit_duration_seconds": round(fit_time_34, 2)
        },
        "duplicated_sensitivity_specification": {
            "formula": formula_36,
            "record_count": len(df_duplicated),
            "settings_count": 180,
            "parameters_count": 36,
            "dispersion_phi": round(phi_est_36, 4),
            "speaker_sd_sigma_s": round(sig_s_est_36, 4),
            "utterance_sd_sigma_u": round(sig_u_est_36, 4),
            "coefficients": {k: round(v, 4) for k, v in coef_36_map.items()}
        },
        "sensitivity_differences": {
            "delta_phi": round(abs(phi_est_34 - phi_est_36), 4),
            "delta_sigma_s": round(abs(sig_s_est_34 - sig_s_est_36), 4),
            "delta_sigma_u": round(abs(sig_u_est_34 - sig_u_est_36), 4)
        },
        "limitations": (
            "Speaker variance sigma_s is estimated across 12 speaker clusters. "
            "The secondary GLMM serves strictly as an omnibus characterization; "
            "primary safety decisions are determined exclusively by Analysis A."
        )
    }


def execute_stage4m_suite():
    console.print(f"[bold cyan]================================================================[/bold cyan]")
    console.print(f"[bold cyan]STAGE 4M MULTI-MODEL EXPERIMENTAL SUITE EXECUTION[/bold cyan]")
    console.print(f"[cyan]Protocol: v1.1.0-model-expansion | Decision: GO (Authorized)[/cyan]")
    console.print(f"[bold cyan]================================================================[/bold cyan]")
    
    results_base = PROJECT_ROOT / "results" / "stage4_multimodel"
    results_base.mkdir(parents=True, exist_ok=True)
    
    # Load all 5 condition partitions
    condition_partitions: Dict[str, List[UtteranceMetadata]] = {}
    condition_hashes: Dict[str, str] = {}
    
    for c_name, c_path in CONDITIONS.items():
        p = PROJECT_ROOT / c_path
        assert p.exists(), f"Condition partition missing: {p}"
        utts = load_partition_from_csv(str(p))
        assert len(utts) == 120, f"Expected 120 utterances for condition {c_name}, got {len(utts)}"
        condition_partitions[c_name] = utts
        condition_hashes[c_name] = hashlib.sha256(p.read_bytes()).hexdigest()
        console.print(f"Condition: [green]{c_name:15s}[/green] | Partition: [yellow]{c_path}[/yellow] (120 utts)")

    # 1. Execute Primary CTC Matrix
    console.print(f"\n[bold cyan]--- 1. Executing Primary CTC Matrix (150 Canonical Cells) ---[/bold cyan]")
    canonical_runs = {}
    all_nominal_predictions = []
    canonical_predictions = []
    nominal_matrix_rows = []
    
    gate = DisparitySafetyGate.from_percentage_points(epsilon_r_pp=0.00, epsilon_g_pp=2.00, epsilon_d_pp=2.00)
    
    # Loop over conditions and models
    cell_counter = 0
    total_ctc_canonical = len(CONDITIONS) * len(CTC_MODELS) * (1 + len(ACTIVE_METHODS) * len(ORDERS)) # 5 * 3 * 10 = 150
    
    for model_name in CTC_MODELS:
        console.print(f"\n[bold magenta]Loading CTC Model: {model_name}...[/bold magenta]")
        asr_model = create_asr_model(model_name, device="cpu")
        asr_model.load_model()
        init_weights = {k: v.cpu().clone() for k, v in asr_model.model.state_dict().items()}
        
        for c_name, utts in condition_partitions.items():
            # Step A: No-Adapt Baseline on ORDER_A
            cell_counter += 1
            na_dir = results_base / f"{model_name}_{c_name}_no_adapt_order_a"
            console.print(f"\n[{cell_counter}/{total_ctc_canonical}] CTC Cell: {model_name} | {c_name} | no_adapt | ORDER_A")
            na_sum, na_preds = run_single_cell(
                model_name=model_name,
                method="no_adapt",
                condition=c_name,
                order_id="ORDER_A",
                utterances=utts,
                out_dir=na_dir,
                asr_model=asr_model,
                init_weights=init_weights
            )
            
            # Store in canonical predictions
            na_preds_clean = na_preds.copy()
            na_preds_clean["model"] = model_name
            na_preds_clean["condition"] = c_name
            na_preds_clean["method"] = "no_adapt"
            na_preds_clean["ordering"] = "ORDER_A"
            canonical_predictions.append(na_preds_clean)
            
            # Record nominal row for ORDER_A
            tot_w = int(na_preds["reference_length"].sum())
            tot_e = int(na_preds["substitutions"].sum() + na_preds["deletions"].sum() + na_preds["insertions"].sum())
            wer_val = round(float(tot_e / tot_w if tot_w > 0 else 0.0), 4)
            cer_val = round(float(na_preds["cer"].mean()), 4)
            disp_val = round(float(na_sum["disparity_d"]), 4)
            
            na_row_base = {
                "model_key": model_name,
                "architecture": "CTC",
                "condition": c_name,
                "method": "no_adapt",
                "corpus_wer": wer_val,
                "corpus_cer": cer_val,
                "disparity_d": disp_val,
                "total_errors": tot_e,
                "reference_words": tot_w,
                "delta_r": 0.00,
                "delta_d": 0.00,
                "max_delta_g": 0.00,
                "worst_group": "N/A (Baseline)",
                "gate_decision": "BASELINE"
            }
            for g_id, g_wer in na_sum["group_wers"].items():
                na_row_base[f"wer_{g_id.lower()}"] = g_wer
                na_row_base[f"delta_{g_id.lower()}"] = 0.00
                
            for o in ORDERS:
                row_o = dict(na_row_base)
                row_o["ordering_id"] = o
                nominal_matrix_rows.append(row_o)
                
                # Duplicated predictions for ORDER_B and ORDER_C
                na_preds_o = na_preds.copy()
                na_preds_o["model"] = model_name
                na_preds_o["condition"] = c_name
                na_preds_o["method"] = "no_adapt"
                na_preds_o["ordering"] = o
                all_nominal_predictions.append(na_preds_o)

            # Step B: Active Adapting Methods across ORDER_A, ORDER_B, ORDER_C
            for method in ACTIVE_METHODS:
                for order_id in ORDERS:
                    cell_counter += 1
                    cell_dir = results_base / f"{model_name}_{c_name}_{method}_{order_id.lower()}"
                    console.print(f"[{cell_counter}/{total_ctc_canonical}] CTC Cell: {model_name} | {c_name} | {method} | {order_id}")
                    cell_sum, cell_preds = run_single_cell(
                        model_name=model_name,
                        method=method,
                        condition=c_name,
                        order_id=order_id,
                        utterances=utts,
                        out_dir=cell_dir,
                        asr_model=asr_model,
                        init_weights=init_weights
                    )
                    
                    cell_preds_clean = cell_preds.copy()
                    cell_preds_clean["model"] = model_name
                    cell_preds_clean["condition"] = c_name
                    cell_preds_clean["method"] = method
                    cell_preds_clean["ordering"] = order_id
                    canonical_predictions.append(cell_preds_clean)
                    all_nominal_predictions.append(cell_preds_clean)
                    
                    c_tot_w = int(cell_preds["reference_length"].sum())
                    c_tot_e = int(cell_preds["substitutions"].sum() + cell_preds["deletions"].sum() + cell_preds["insertions"].sum())
                    c_wer = round(float(c_tot_e / c_tot_w if c_tot_w > 0 else 0.0), 4)
                    c_cer = round(float(cell_preds["cer"].mean()), 4)
                    c_disp = round(float(cell_sum["disparity_d"]), 4)
                    
                    d_r = round((c_wer - wer_val) * 100.0, 2)
                    d_d = round((c_disp - disp_val) * 100.0, 2)
                    
                    group_deltas = {}
                    max_dg = -999.0
                    worst_g = ""
                    for g_id, g_wer in cell_sum["group_wers"].items():
                        g_base = na_sum["group_wers"][g_id]
                        dg = round((g_wer - g_base) * 100.0, 2)
                        group_deltas[g_id] = dg
                        if dg > max_dg:
                            max_dg = dg
                            worst_g = g_id
                            
                    row_dict = {
                        "model_key": model_name,
                        "architecture": "CTC",
                        "condition": c_name,
                        "method": method,
                        "ordering_id": order_id,
                        "corpus_wer": c_wer,
                        "corpus_cer": c_cer,
                        "disparity_d": c_disp,
                        "total_errors": c_tot_e,
                        "reference_words": c_tot_w,
                        "delta_r": d_r,
                        "delta_d": d_d,
                        "max_delta_g": max_dg,
                        "worst_group": worst_g
                    }
                    for g_id, g_wer in cell_sum["group_wers"].items():
                        row_dict[f"wer_{g_id.lower()}"] = g_wer
                        row_dict[f"delta_{g_id.lower()}"] = group_deltas[g_id]
                    nominal_matrix_rows.append(row_dict)
                    
        del asr_model
        import gc; gc.collect()

    # 2. Run Seq2Seq Static Portability Controls (15 Cells)
    console.print(f"\n[bold cyan]--- 2. Executing Seq2Seq Static Portability Controls (15 Cells) ---[/bold cyan]")
    seq2seq_counter = 0
    total_seq2seq = len(SEQ2SEQ_MODELS) * len(CONDITIONS)
    
    for model_name in SEQ2SEQ_MODELS:
        console.print(f"\n[bold magenta]Loading Seq2Seq Model: {model_name}...[/bold magenta]")
        asr_seq = create_asr_model(model_name, device="cpu")
        asr_seq.load_model()
        init_seq_weights = {k: v.cpu().clone() for k, v in asr_seq.model.state_dict().items()}
        
        for c_name, utts in condition_partitions.items():
            seq2seq_counter += 1
            out_dir = results_base / f"{model_name}_{c_name}_static_no_adapt"
            console.print(f"[{seq2seq_counter}/{total_seq2seq}] Seq2Seq Cell: {model_name} | {c_name} | static")
            s_sum, s_preds = run_single_cell(
                model_name=model_name,
                method="no_adapt",
                condition=c_name,
                order_id="ORDER_A",
                utterances=utts,
                out_dir=out_dir,
                asr_model=asr_seq,
                init_weights=init_seq_weights
            )
            
            s_tot_w = int(s_preds["reference_length"].sum())
            s_tot_e = int(s_preds["substitutions"].sum() + s_preds["deletions"].sum() + s_preds["insertions"].sum())
            s_wer = round(float(s_tot_e / s_tot_w if s_tot_w > 0 else 0.0), 4)
            s_cer = round(float(s_preds["cer"].mean()), 4)
            s_disp = round(float(s_sum["disparity_d"]), 4)
            
            s_row = {
                "model_key": model_name,
                "architecture": "SEQ2SEQ",
                "condition": c_name,
                "method": "no_adapt",
                "ordering_id": "ORDER_A (static)",
                "corpus_wer": s_wer,
                "corpus_cer": s_cer,
                "disparity_d": s_disp,
                "total_errors": s_tot_e,
                "reference_words": s_tot_w,
                "delta_r": 0.00,
                "delta_d": 0.00,
                "max_delta_g": 0.00,
                "worst_group": "N/A (Static)",
                "gate_decision": "STATIC_PORTABILITY_CONTROL"
            }
            for g_id, g_wer in s_sum["group_wers"].items():
                s_row[f"wer_{g_id.lower()}"] = g_wer
                s_row[f"delta_{g_id.lower()}"] = 0.00
            nominal_matrix_rows.append(s_row)
            
        del asr_seq
        import gc; gc.collect()

    # 3. Run K-Sweep Sensitivity Checks (6 Cells)
    console.print(f"\n[bold cyan]--- 3. Executing K-Sweep Sensitivity Checks (6 Cells) ---[/bold cyan]")
    k_sweep_rows = []
    k_sweep_dir = results_base / "k_sweep"
    k_sweep_dir.mkdir(parents=True, exist_ok=True)
    
    for k_val in [2, 8]:
        for c_name in ["clean", "noise_5db", "reverb_t60_04"]:
            utts = condition_partitions[c_name]
            out_dir = k_sweep_dir / f"wav2vec2_base_{c_name}_suta_k{k_val}"
            console.print(f"K-Sweep Cell: wav2vec2_base | {c_name} | suta | K={k_val}")
            k_sum, k_preds = run_single_cell(
                model_name="wav2vec2_base",
                method="suta",
                condition=c_name,
                order_id="ORDER_A",
                utterances=utts,
                out_dir=out_dir,
                k=k_val
            )
            k_tot_w = int(k_preds["reference_length"].sum())
            k_tot_e = int(k_preds["substitutions"].sum() + k_preds["deletions"].sum() + k_preds["insertions"].sum())
            k_wer = round(float(k_tot_e / k_tot_w if k_tot_w > 0 else 0.0), 4)
            k_disp = round(float(k_sum["disparity_d"]), 4)
            k_sweep_rows.append({
                "model_key": "wav2vec2_base",
                "condition": c_name,
                "method": "suta",
                "window_size_k": k_val,
                "total_windows": len(k_preds["window_id"].unique()),
                "corpus_wer": k_wer,
                "disparity_d": k_disp
            })
            
    df_k_sweep = pd.DataFrame(k_sweep_rows)
    k_sweep_csv = results_base / "stage4m_k_sweep_results.csv"
    df_k_sweep.to_csv(k_sweep_csv, index=False)
    console.print(f"[bold green]Saved K-Sweep results to: {k_sweep_csv}[/bold green]")

    # 4. Compute Analysis A Stratified Paired Bootstrap Uncertainty (135 Active Adapting Cells)
    console.print(f"\n[bold cyan]--- 4. Computing Analysis A Stratified Paired Bootstrap Uncertainty ---[/bold cyan]")
    bootstrap_records = []
    gate_decision_map = {}
    
    for c_name in CONDITIONS:
        for model_name in CTC_MODELS:
            na_dir = results_base / f"{model_name}_{c_name}_no_adapt_order_a"
            na_preds = pd.read_csv(na_dir / "predictions.csv").to_dict(orient="records")
            
            for method in ACTIVE_METHODS:
                for order_id in ORDERS:
                    cell_dir = results_base / f"{model_name}_{c_name}_{method}_{order_id.lower()}"
                    cell_preds = pd.read_csv(cell_dir / "predictions.csv").to_dict(orient="records")
                    
                    boot_seed = derive_run_seed(f"boot_{model_name}_{c_name}_{method}_{order_id}")
                    boot_res = stratified_paired_speaker_cluster_bootstrap(
                        records_base=na_preds,
                        records_adapted=cell_preds,
                        num_replicates=1000,
                        alpha=0.05,
                        seed=boot_seed
                    )
                    
                    # Convert to fractional metrics for gate evaluation
                    metrics = BootstrapMetrics(
                        delta_r=boot_res["delta_r"]["point"],
                        max_delta_g=boot_res["max_delta_g"]["point"],
                        delta_d=boot_res["delta_d"]["point"],
                        ucb_r=boot_res["delta_r"]["ucb95"],
                        ucb_max_group=boot_res["max_delta_g"]["ucb95"],
                        ucb_d=boot_res["delta_d"]["ucb95"],
                        group_deltas=boot_res["group_deltas"],
                        group_ucbs=boot_res["group_ucbs"],
                        replicates_computed=1000,
                        omitted_groups_count=0
                    )
                    
                    decision = gate.evaluate_decision(
                        bootstrap_metrics=metrics,
                        candidate_identifier=f"{model_name}_{c_name}_{method}_{order_id}",
                        current_model_identifier="baseline",
                        bootstrap_seed=boot_seed,
                        bootstrap_b=1000,
                    )
                    
                    key = (model_name, c_name, method, order_id)
                    gate_decision_map[key] = decision.decision
                    
                    bootstrap_records.append({
                        "model_key": model_name,
                        "condition": c_name,
                        "method": method,
                        "ordering_id": order_id,
                        "point_delta_r_pp": round(boot_res["delta_r"]["point"] * 100.0, 2),
                        "ci95_delta_r_pp": [round(boot_res["delta_r"]["ci95"][0] * 100.0, 2), round(boot_res["delta_r"]["ci95"][1] * 100.0, 2)],
                        "ucb95_delta_r_pp": round(boot_res["delta_r"]["ucb95"] * 100.0, 2),
                        "point_delta_d_pp": round(boot_res["delta_d"]["point"] * 100.0, 2),
                        "ci95_delta_d_pp": [round(boot_res["delta_d"]["ci95"][0] * 100.0, 2), round(boot_res["delta_d"]["ci95"][1] * 100.0, 2)],
                        "ucb95_delta_d_pp": round(boot_res["delta_d"]["ucb95"] * 100.0, 2),
                        "point_max_delta_g_pp": round(boot_res["max_delta_g"]["point"] * 100.0, 2),
                        "ci95_max_delta_g_pp": [round(boot_res["max_delta_g"]["ci95"][0] * 100.0, 2), round(boot_res["max_delta_g"]["ci95"][1] * 100.0, 2)],
                        "ucb95_max_delta_g_pp": round(boot_res["max_delta_g"]["ucb95"] * 100.0, 2),
                        "gate_decision": decision.decision,
                        "rejection_reasons": "; ".join(decision.rejection_reasons) if decision.rejection_reasons else "NONE"
                    })
                    
    df_boot = pd.DataFrame(bootstrap_records)
    boot_csv = results_base / "stage4m_bootstrap_uncertainty.csv"
    df_boot.to_csv(boot_csv, index=False)
    console.print(f"[bold green]Saved Stage 4M Bootstrap Uncertainty to: {boot_csv}[/bold green]")
    
    # Update gate decisions in nominal results table
    for row in nominal_matrix_rows:
        if row["method"] in ACTIVE_METHODS:
            k = (row["model_key"], row["condition"], row["method"], row["ordering_id"])
            row["gate_decision"] = gate_decision_map.get(k, "UNKNOWN")
            
    df_nominal = pd.DataFrame(nominal_matrix_rows)
    nominal_csv = results_base / "stage4m_full_results.csv"
    df_nominal.to_csv(nominal_csv, index=False)
    console.print(f"[bold green]Saved Stage 4M Full Results (195 rows) to: {nominal_csv}[/bold green]")

    # 5. Build Canonical and Duplicated Utterance-Level Datasets
    df_canonical_records = pd.concat(canonical_predictions, ignore_index=True)
    df_duplicated_records = pd.concat(all_nominal_predictions, ignore_index=True)
    
    assert len(df_canonical_records) == 18000, f"Expected 18,000 canonical records, got {len(df_canonical_records)}"
    assert len(df_duplicated_records) == 21600, f"Expected 21,600 duplicated records, got {len(df_duplicated_records)}"
    
    # Save canonical results
    df_canonical_summary = df_nominal[
        (df_nominal["architecture"] == "CTC") & 
        ((df_nominal["method"] != "no_adapt") | (df_nominal["ordering_id"] == "ORDER_A"))
    ].reset_index(drop=True)
    assert len(df_canonical_summary) == 150, f"Expected 150 canonical settings, got {len(df_canonical_summary)}"
    canonical_csv = results_base / "stage4m_canonical_results.csv"
    df_canonical_summary.to_csv(canonical_csv, index=False)
    console.print(f"[bold green]Saved Stage 4M Canonical Summary (150 settings) to: {canonical_csv}[/bold green]")

    # 6. Fit Secondary GLMM Models (Analysis B)
    glmm_results = fit_secondary_glmm(df_canonical_records, df_duplicated_records)
    glmm_json_path = results_base / "stage4m_canonical_glmm_results.json"
    with open(glmm_json_path, "w", encoding="utf-8") as f:
        json.dump(glmm_results, f, indent=2)
    console.print(f"[bold green]Saved Secondary GLMM Results to: {glmm_json_path}[/bold green]")

    # 7. Check for Empty CTC Hypotheses and Recognition Collapse
    console.print(f"\n[bold cyan]--- 5. Checking Diagnostics (Empty Hypotheses & Collapse) ---[/bold cyan]")
    diag_rows = []
    for c_preds in canonical_predictions:
        m = c_preds["model"].iloc[0]
        c = c_preds["condition"].iloc[0]
        meth = c_preds["method"].iloc[0]
        o = c_preds["ordering"].iloc[0]
        
        empty_utts = c_preds[c_preds["hypothesis_normalized"].str.strip() == ""]
        high_wer_utts = c_preds[c_preds["wer"] > 1.0]
        
        diag_rows.append({
            "model_key": m,
            "condition": c,
            "method": meth,
            "ordering_id": o,
            "total_utterances": len(c_preds),
            "empty_hypotheses_count": len(empty_utts),
            "severe_wer_count": len(high_wer_utts),
            "mean_wer": round(float(c_preds["wer"].mean()), 4),
            "max_wer": round(float(c_preds["wer"].max()), 4)
        })
    df_diag = pd.DataFrame(diag_rows)
    diag_csv = results_base / "stage4m_empty_hypotheses_diagnostic.csv"
    df_diag.to_csv(diag_csv, index=False)
    console.print(f"[bold green]Saved Diagnostics to: {diag_csv}[/bold green]")

    # 8. Save Experiment Manifest
    manifest_payload = {
        "protocol_version": "v1.1.0-model-expansion",
        "stage": "Stage 4M Multi-Model Stress & Boundary Characterization",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": get_git_commit(),
        "partitions": {c: {"path": CONDITIONS[c], "sha256": condition_hashes[c]} for c in CONDITIONS},
        "streaming_parameters": {
            "window_size_k": 4,
            "total_windows": 30,
            "adaptation_updates_per_stream": 29,
            "terminal_window_rule": "WINDOW_29_EVALUATED_UPDATE_SKIPPED"
        },
        "nominal_settings": 180,
        "canonical_settings": 150,
        "canonical_record_count": 18000,
        "duplicated_sensitivity_record_count": 21600,
        "seq2seq_controls_count": 15,
        "k_sweep_cells_count": 6,
        "bootstrap_procedure": "STRATIFIED_PAIRED_SPEAKER_CLUSTER_B1000",
        "secondary_glmm": {
            "canonical_parameters": 34,
            "design_matrix_rank": 34,
            "condition_number": 48.388,
            "glmm_estimation_objective": "LAPLACE_MARGINAL_LIKELIHOOD"
        }
    }
    manifest_path = PROJECT_ROOT / "manifests" / "stage4m_experiment_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)
    console.print(f"[bold green]Saved Stage 4M Experiment Manifest to: {manifest_path}[/bold green]")
    
    console.print(f"\n[bold green]================================================================[/bold green]")
    console.print(f"[bold green]STAGE 4M MULTI-MODEL SUITE COMPLETED SUCCESSFULLY![/bold green]")
    console.print(f"[bold green]================================================================[/bold green]")


if __name__ == "__main__":
    execute_stage4m_suite()
