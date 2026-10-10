import torch
import numpy as np
import pandas as pd
import json
import patsy
from pathlib import Path
from dsg_ctta.models.registry import MODEL_CATALOG

# Verify Hessian eigenvalues at (phi, sigma_s, sigma_u)
# Let's inspect the Laplace log-likelihood around (sigma_s, sigma_u)
results_base = Path("results/stage4_multimodel")
with open(results_base / "stage4m_canonical_glmm_results.json", "r") as f:
    glmm_res = json.load(f)

canon = glmm_res["canonical_specification"]
print("Canonical specification results:")
print(f"phi: {canon['dispersion_phi']}")
print(f"sigma_s: {canon['speaker_sd_sigma_s']}")
print(f"sigma_u: {canon['utterance_sd_sigma_u']}")
print(f"Optimization duration: {canon['fit_duration_seconds']}s")
