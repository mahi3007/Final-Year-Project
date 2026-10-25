# Stage 6M Confirmatory Benchmark — Pytest Runtime Warnings Reconciliation Ledger

**Governing Standard:** ADR-005  
**Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
**Target Revision:** `3ddf79296c22ba9fba2c54eb1196ea1897caf57e`  
**Audit Context:** Full Repository Test Suite (291 passing tests)  
**Execution Environment:** Windows 11 (win32), Python 3.11.9, pytest 9.0.2, pluggy 1.6.0  

---

## 1. Executive Summary & Reconciliation of Warning Counts

In the repository test execution across all 291 unit, integration, and research-validity tests, the test runner passed with 100% success (`291 passed`) while emitting runtime warnings.

### Exact Resolution of the 9-vs-10 Count Discrepancy

An audit review identified an apparent numerical mismatch: an earlier narrative table listed 10 items while the pytest summary block printed `9 warnings`.

Ground-truth inspection of the raw execution logs reveals the exact root cause:
1. **Pytest Internal Warning Summary (9 warnings captured):**
   - **4 Pillow / TorchVision Deprecations:** `BILINEAR` (line 245), `NEAREST` (line 291), `NEAREST` (line 307), `BICUBIC` (line 324) in `torchvision/transforms/_functional_pil.py`.
   - **2 SWIG Python 3.11 Deprecations:** `SwigPyPacked` and `SwigPyObject` during module import in `<frozen importlib._bootstrap>:241`.
   - **2 Statsmodels Rank-Deficiency Warnings:** `SingularMatrixWarning` in `test_pipeline.py::test_full_e2e_research_pipeline` was emitted **twice** (due to two GLMM estimation stages on collinear synthetic covariates).
   - **1 GLMM Numeric Warning:** `RuntimeWarning: overflow encountered in exp` in `src/dsg_ctta/offline/glmm.py:203` during synthetic GLMM confidence interval calculation.
   - **Total Captured by Pytest:** $4 + 2 + 2 + 1 = \mathbf{9\text{ warnings}}$.

2. **Interpreter-Level Stderr Emissions Outside Pytest Capture:**
   - **Startup Stderr (1 warning):** `RequestsDependencyWarning: urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!` was emitted by Python's module loader to `sys.stderr` before pytest session collection initiated.
   - **Teardown Stderr (1 warning):** `sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute` was emitted during Python interpreter shutdown after pytest printed its summary block.

3. **How the "10" Count Arose:**
   The earlier transcription erroneously collapsed the 2 occurrences of `SingularMatrixWarning` into 1 category count of 1, grouped `swigvarlink` into the SWIG category (making SWIG count 3), and added the startup `RequestsDependencyWarning` (1):
   $$4\text{ (Pillow)} + 3\text{ (SWIG)} + 1\text{ (SingularMatrix)} + 1\text{ (GLMM)} + 1\text{ (Requests)} = 10\text{ listed items}.$$
   When matched strictly against pytest's internal capture mechanism, the true count is **9 warnings**. When including uncaptured interpreter stderr emissions, there are 11 total emission events across 6 distinct warning classes.

---

## 2. Comprehensive Warning Classification Matrix

| Warning Event | Emitting Subsystem | Warning Class | Originating Call Site | Capture Location | Detailed Message & Root Cause Analysis | Stage 6M Benchmark Impact |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: |
| **W-01** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:245` | Pytest Summary | `BILINEAR is deprecated and will be removed in Pillow 10. Use Resampling.BILINEAR instead.` Upstream library compatibility between Pillow and TorchVision image utilities. | **None** (ASR audio pipeline does not use PIL image transforms) |
| **W-02** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:291` | Pytest Summary | `NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST or Dither.NONE instead.` | **None** |
| **W-03** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:307` | Pytest Summary | `NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST or Dither.NONE instead.` | **None** |
| **W-04** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:324` | Pytest Summary | `BICUBIC is deprecated and will be removed in Pillow 10. Use Resampling.BICUBIC instead.` | **None** |
| **W-05** | Python 3.11 Runtime / SWIG | `DeprecationWarning` | `<frozen importlib._bootstrap>:241` | Pytest Summary | `builtin type SwigPyPacked has no __module__ attribute.` Emitted during C-extension module loading in Python 3.11. | **None** (Standard C-extension binding artifact) |
| **W-06** | Python 3.11 Runtime / SWIG | `DeprecationWarning` | `<frozen importlib._bootstrap>:241` | Pytest Summary | `builtin type SwigPyObject has no __module__ attribute.` Emitted during C-extension module loading in Python 3.11. | **None** |
| **W-07** | Offline Statistics (`statsmodels`) | `SingularMatrixWarning` | `tests/integration/test_pipeline.py` (call 1) via `generalized_linear_model.py:1486` | Pytest Summary | `The design matrix is rank-deficient. The model parameters are not uniquely determined.` Triggered by minimal synthetic covariates in the offline GLMM test fixture. | **None** (Test fixture artifact; does not affect real evaluation stream) |
| **W-08** | Offline Statistics (`statsmodels`) | `SingularMatrixWarning` | `tests/integration/test_pipeline.py` (call 2) via `generalized_linear_model.py:1486` | Pytest Summary | `The design matrix is rank-deficient. The model parameters are not uniquely determined.` Second occurrence in synthetic test fixture. | **None** (Test fixture artifact) |
| **W-09** | Offline Statistics (`dsg_ctta.offline.glmm`) | `RuntimeWarning` | `tests/integration/test_pipeline.py` via `src/dsg_ctta/offline/glmm.py:203` | Pytest Summary | `overflow encountered in exp: ci_u = float(np.exp(conf.loc[var_name][1]))`. Occurs when exponentiating confidence interval upper bounds under rank-deficient synthetic GLMM fits. | **None** (Test fixture artifact) |
| **E-01** | Environment Packaging (`requests`) | `RequestsDependencyWarning` | `requests/__init__.py:113` | Startup Stderr | `urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!` Emitted on stderr during Python startup prior to pytest collection. | **None** |
| **E-02** | Python 3.11 Teardown / SWIG | `DeprecationWarning` | `sys:1` | Teardown Stderr | `builtin type swigvarlink has no __module__ attribute.` Emitted on stderr during interpreter shutdown after pytest completes. | **None** |

---

## 3. Audit Verdict on Warnings

- **Captured by Pytest Capture Engine:** Exactly **9 warnings** (4 torchvision + 2 SWIG + 2 statsmodels SingularMatrixWarning + 1 GLMM RuntimeWarning).
- **Emitted to Stderr Outside Pytest:** Exactly **2 warnings** (1 startup `RequestsDependencyWarning` + 1 teardown `swigvarlink` deprecation).
- **Stage 6M Benchmark Codebase Warnings:** **0 warnings.** No warning originates from `scripts/generate_stage6m_locked_manifest.py`, `scripts/curate_stage6m_cohort2_csv.py`, `src/dsg_ctta/data/cohort2_preflight.py`, or `cloud/kaggle/run_stage6m_cohort2_benchmark.py`.
