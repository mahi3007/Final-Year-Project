"""
Confound-aware Generalized Linear Mixed Model (GLMM) and Count Model module.
Fits Poisson / Negative Binomial regression on ASR edit counts E = S + D + I with log(N) offset,
controlling for SNR, speech rate, recording device, and speaker clustering.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GLMMCoefficientResult(BaseModel):
    """Regression coefficient and exponentiated Rate Ratio."""
    variable: str
    beta: float
    std_err: float
    z_stat: float
    p_value: float
    p_value_adjusted: float  # Holm-Bonferroni adjusted
    rate_ratio: float  # exp(beta)
    rr_ci_lower_95: float
    rr_ci_upper_95: float


class GLMMModelReport(BaseModel):
    """Complete GLMM confound analysis report."""
    model_family: str  # 'Poisson' or 'NegativeBinomial'
    formula: str
    num_observations: int
    num_speakers: int
    dispersion_statistic: float  # Pearson Chi2 / dof
    is_overdispersed: bool
    log_likelihood: float
    aic: float
    bic: float
    coefficients: List[GLMMCoefficientResult]
    raw_group_disparity_rr: float
    adjusted_group_disparity_rr: float
    summary_text: str


def fit_confound_aware_count_model(
    evaluation_records: List[Dict[str, Any]],
    baseline_group: Optional[str] = None
) -> GLMMModelReport:
    """
    Fit count-based Poisson / Negative Binomial GLM with cluster-robust standard errors.
    
    Formula:
    total_errors ~ C(group_id, Treatment(reference='...')) + snr_db + speech_rate_wpm + C(device_id)
    Offset: log(reference_length)
    Cluster: speaker_id
    """
    df = pd.DataFrame(evaluation_records).copy()

    # Filter out records with 0 reference words
    df = df[df["reference_length"] > 0].copy()
    if len(df) < 5:
        raise ValueError("Insufficient data to fit GLMM count model (at least 5 utterances required).")

    # Compute edit count E = S + D + I
    df["total_errors"] = df["substitutions"] + df["deletions"] + df["insertions"]
    df["log_offset"] = np.log(df["reference_length"].astype(float))

    # Standardize continuous confounders for numerical stability
    if "snr_db" not in df.columns or df["snr_db"].isnull().all():
        df["snr_db"] = 20.0
    else:
        df["snr_db"] = df["snr_db"].fillna(20.0)

    if "speech_rate_wpm" not in df.columns or df["speech_rate_wpm"].isnull().all():
        df["speech_rate_wpm"] = 140.0
    else:
        df["speech_rate_wpm"] = df["speech_rate_wpm"].fillna(140.0)

    if "device_id" not in df.columns or df["device_id"].isnull().all():
        df["device_id"] = "unknown"
    else:
        df["device_id"] = df["device_id"].fillna("unknown")

    # Standardize continuous variables
    snr_mean, snr_std = df["snr_db"].mean(), df["snr_db"].std()
    df["snr_z"] = (df["snr_db"] - snr_mean) / (snr_std if snr_std > 0 else 1.0)

    rate_mean, rate_std = df["speech_rate_wpm"].mean(), df["speech_rate_wpm"].std()
    df["rate_z"] = (df["speech_rate_wpm"] - rate_mean) / (rate_std if rate_std > 0 else 1.0)

    # Set reference group
    unique_groups = sorted(df["group_id"].unique())
    ref_grp = baseline_group if (baseline_group and baseline_group in unique_groups) else unique_groups[0]

    # Build formula dynamically based on degrees of freedom and distinct levels
    formula_terms = [f"C(group_id, Treatment(reference='{ref_grp}'))"]
    
    # Only add continuous covariates if there is variance and enough samples
    if df["snr_z"].std() > 1e-4 and len(df) > len(unique_groups) + 2:
        formula_terms.append("snr_z")
    if df["rate_z"].std() > 1e-4 and len(df) > len(unique_groups) + 3:
        formula_terms.append("rate_z")
    if len(df["device_id"].unique()) > 1 and len(df) > len(unique_groups) + len(df["device_id"].unique()) + 2:
        formula_terms.append("C(device_id)")

    formula = f"total_errors ~ {' + '.join(formula_terms)}"

    # Determine whether cluster covariance is feasible (requires > 1 speaker and enough clusters)
    num_clusters = len(df["speaker_id"].unique())
    use_cluster = num_clusters >= 3 and len(df) >= num_clusters * 2

    # Step 1: Fit Poisson model
    poisson_model = smf.glm(
        formula=formula,
        data=df,
        family=sm.families.Poisson(),
        offset=df["log_offset"]
    )
    
    try:
        if use_cluster:
            poisson_res = poisson_model.fit(
                cov_type="cluster",
                cov_kwds={"groups": df["speaker_id"]}
            )
        else:
            poisson_res = poisson_model.fit(cov_type="HC1")
    except Exception:
        # Fallback to minimal formula if singular
        minimal_formula = f"total_errors ~ C(group_id, Treatment(reference='{ref_grp}'))"
        poisson_model = smf.glm(
            formula=minimal_formula,
            data=df,
            family=sm.families.Poisson(),
            offset=df["log_offset"]
        )
        poisson_res = poisson_model.fit()
        formula = minimal_formula


    # Pearson Chi-square dispersion statistic = Chi2 / dof_residual
    pearson_chi2 = float(poisson_res.pearson_chi2)
    dof_resid = max(1, int(poisson_res.df_resid))
    dispersion_stat = pearson_chi2 / dof_resid
    is_overdispersed = (dispersion_stat > 1.5)

    # Step 2: If overdispersed, fit Negative Binomial GLM
    if is_overdispersed:
        nb_model = smf.glm(
            formula=formula,
            data=df,
            family=sm.families.NegativeBinomial(alpha=1.0),
            offset=df["log_offset"]
        )
        try:
            res = nb_model.fit(
                cov_type="cluster",
                cov_kwds={"groups": df["speaker_id"]}
            )
            family_name = "NegativeBinomial"
        except Exception:
            res = poisson_res
            family_name = "Poisson"
    else:
        res = poisson_res
        family_name = "Poisson"

    # Extract coefficients and compute Rate Ratios
    params = res.params
    conf = res.conf_int()
    pvalues = res.pvalues
    bse = res.bse

    # Compute Holm-Bonferroni correction across group comparisons
    group_var_names = [v for v in params.index if "group_id" in v]
    raw_pvals = [float(pvalues[v]) for v in group_var_names]
    
    # Sort and apply Holm correction
    sorted_indices = np.argsort(raw_pvals)
    adj_pvals = np.zeros(len(raw_pvals))
    m = len(raw_pvals)
    cum_max = 0.0
    for rank, idx in enumerate(sorted_indices):
        p_adj = raw_pvals[idx] * (m - rank)
        p_adj = min(1.0, max(cum_max, p_adj))
        cum_max = p_adj
        adj_pvals[idx] = p_adj

    group_adj_map = {group_var_names[i]: adj_pvals[i] for i in range(len(group_var_names))}

    coeff_results = []
    group_rrs = []

    for var_name in params.index:
        beta = float(params[var_name])
        se = float(bse[var_name])
        z = float(res.tvalues[var_name]) if hasattr(res, "tvalues") else beta / se if se > 0 else 0.0
        p = float(pvalues[var_name])
        p_adj = float(group_adj_map.get(var_name, p))
        rr = float(np.exp(beta))
        ci_l = float(np.exp(conf.loc[var_name][0]))
        ci_u = float(np.exp(conf.loc[var_name][1]))

        if "group_id" in var_name:
            group_rrs.append(rr)

        coeff_results.append(GLMMCoefficientResult(
            variable=var_name,
            beta=beta,
            std_err=se,
            z_stat=z,
            p_value=p,
            p_value_adjusted=p_adj,
            rate_ratio=rr,
            rr_ci_lower_95=ci_l,
            rr_ci_upper_95=ci_u
        ))

    # Disparity in Rate Ratios
    raw_group_wers = {
        gid: (gdf["total_errors"].sum() / gdf["reference_length"].sum()) if gdf["reference_length"].sum() > 0 else 0.0
        for gid, gdf in df.groupby("group_id")
    }
    min_raw_wer = min(raw_group_wers.values())
    max_raw_wer = max(raw_group_wers.values())
    raw_disp_rr = (max_raw_wer / min_raw_wer) if min_raw_wer > 0 else 1.0

    all_rrs = [1.0] + group_rrs  # Reference group has RR = 1.0
    adj_disp_rr = max(all_rrs) / min(all_rrs) if min(all_rrs) > 0 else 1.0

    return GLMMModelReport(
        model_family=family_name,
        formula=formula,
        num_observations=len(df),
        num_speakers=len(df["speaker_id"].unique()),
        dispersion_statistic=float(dispersion_stat),
        is_overdispersed=is_overdispersed,
        log_likelihood=float(res.llf),
        aic=float(res.aic),
        bic=float(res.bic) if hasattr(res, "bic") else 0.0,
        coefficients=coeff_results,
        raw_group_disparity_rr=float(raw_disp_rr),
        adjusted_group_disparity_rr=float(adj_disp_rr),
        summary_text=str(res.summary())
    )
