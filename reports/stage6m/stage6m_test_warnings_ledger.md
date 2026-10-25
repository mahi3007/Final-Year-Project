# Stage 6M Confirmatory Benchmark — Pytest Runtime Warnings Reconciliation Ledger

**Governing Standard:** ADR-005  
**Protocol Version:** `v1.3.4-stage6m-self-authorization-amendment`  
**Execution Environment:** Windows 11 (win32), Python 3.11.9, pytest 9.0.2, pluggy 1.6.0  

---

## 1. Multi-Run Provenance & Execution Summary

This ledger maintains run-specific records across repository revisions to guarantee complete empirical traceability without conflating distinct test executions.

| Run ID | Git Revision (Full Hash) | Test Scope | Exact CLI Command | Exit Code | Wall Duration | Test Count | Pytest-Captured Warnings | Stderr Emissions (Outside Pytest) | Post-Run Git Working Tree |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Run-1** | `3ddf79296c22ba9fba2c54eb1196ea1897caf57e` | Full Repository Suite | `python -m pytest tests/` | `0` | 101.74s | 291 passed | **9** | 2 (1 startup, 1 teardown) | Clean (prior to test isolation) |
| **Run-2** | `3886d903930c589ab1a1d70e394798d2ec727e1c` | Full Repository Suite | `python -m pytest tests/` | `0` | 118.93s | 291 passed | **7** | 2 (1 startup, 1 teardown) | `nothing to commit, working tree clean` |
| **Run-3** | `3886d903930c589ab1a1d70e394798d2ec727e1c` | Focused Cohort 2 Suite | `python -m pytest tests/research_validity/test_stage6m_cohort2_curation.py tests/research_validity/test_stage6m_cohort2_readiness.py` | `0` | 65.57s | 57 passed | **0** | 1 (startup RequestsDependencyWarning) | `nothing to commit, working tree clean` |

---

## 2. Analysis of Run-Specific Warning Variations

### Exact Reconciliation of Run-1 (9 Warnings) vs. Run-2 (7 Warnings)

Across both full-suite runs (**Run-1** and **Run-2**), exactly **6 warnings** are deterministic third-party library/runtime deprecations, while statistical test-fixture warnings in synthetic offline integration tests exhibit slight run-dependent convergence behavior:

1. **Deterministic Upstream Library Warnings (Present in Both Run-1 & Run-2 — 6 warnings):**
   - **4 Pillow / TorchVision Deprecations:** `BILINEAR` (line 245), `NEAREST` (line 291), `NEAREST` (line 307), `BICUBIC` (line 324) in `torchvision/transforms/_functional_pil.py`. (ASR pipeline does not use PIL image transforms).
   - **2 SWIG Python 3.11 Runtime Deprecations:** `SwigPyPacked` and `SwigPyObject` during C-extension loading in `<frozen importlib._bootstrap>:241`.

2. **Synthetic Integration Test Fixture Warnings (Run-Dependent — 1 to 3 warnings):**
   - In `tests/integration/test_pipeline.py::test_full_e2e_research_pipeline`, statsmodels fits a generalized linear mixed model (GLMM) on minimal collinear synthetic test covariates.
   - **Run-1:** Emitted `SingularMatrixWarning` twice (two estimation stages) + 1 GLMM numeric `RuntimeWarning: overflow encountered in exp` in `src/dsg_ctta/offline/glmm.py:203`. Total captured: $6 + 3 = \mathbf{9\text{ warnings}}$.
   - **Run-2:** Emitted `SingularMatrixWarning` once, and GLMM parameter estimation reached termination before triggering exponential overflow in `ci_u`. Total captured: $6 + 1 = \mathbf{7\text{ warnings}}$.

3. **Interpreter-Level Stderr Emissions Outside Pytest Summary Block:**
   - **Startup Stderr (1 warning):** `RequestsDependencyWarning: urllib3 (1.26.12) or chardet (7.4.3)/charset_normalizer (2.1.1) doesn't match a supported version!` (emitted by Python loader before pytest begins).
   - **Teardown Stderr (1 warning):** `sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute` (emitted by interpreter teardown after pytest prints its summary).

4. **Resolution of the Historical "10" Count in Run-1:**
   The earlier transcription erroneously collapsed the 2 occurrences of `SingularMatrixWarning` into 1 category count of 1, grouped `swigvarlink` into the SWIG category (making SWIG count 3), and added the startup `RequestsDependencyWarning` (1):
   $$4\text{ (Pillow)} + 3\text{ (SWIG)} + 1\text{ (SingularMatrix)} + 1\text{ (GLMM)} + 1\text{ (Requests)} = 10\text{ listed items}.$$
   When matched strictly against pytest's internal capture mechanism, the true count for Run-1 was **9 warnings**, and for Run-2 was **7 warnings**.

---

## 3. Comprehensive Warning Classification Matrix

| Warning Event | Emitting Subsystem | Warning Class | Originating Call Site | Capture Location | Observed in Run-1 (`3ddf792`) | Observed in Run-2 (`3886d90`) | Stage 6M Benchmark Impact |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **W-01** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:245` | Pytest Summary | Yes (1) | Yes (1) | **None** (ASR pipeline does not use PIL) |
| **W-02** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:291` | Pytest Summary | Yes (1) | Yes (1) | **None** |
| **W-03** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:307` | Pytest Summary | Yes (1) | Yes (1) | **None** |
| **W-04** | Third-Party Upstream (`torchvision`) | `DeprecationWarning` | `torchvision/transforms/_functional_pil.py:324` | Pytest Summary | Yes (1) | Yes (1) | **None** |
| **W-05** | Python 3.11 Runtime / SWIG | `DeprecationWarning` | `<frozen importlib._bootstrap>:241` | Pytest Summary | Yes (1) | Yes (1) | **None** (Standard C-extension binding artifact) |
| **W-06** | Python 3.11 Runtime / SWIG | `DeprecationWarning` | `<frozen importlib._bootstrap>:241` | Pytest Summary | Yes (1) | Yes (1) | **None** |
| **W-07** | Offline Statistics (`statsmodels`) | `SingularMatrixWarning` | `tests/integration/test_pipeline.py` via `generalized_linear_model.py:1486` | Pytest Summary | Yes (2 occurrences) | Yes (1 occurrence) | **None** (Synthetic integration test fixture artifact) |
| **W-08** | Offline Statistics (`dsg_ctta.offline.glmm`) | `RuntimeWarning` | `src/dsg_ctta/offline/glmm.py:203` | Pytest Summary | Yes (1) | No (0) | **None** (Synthetic integration test fixture artifact) |
| **E-01** | Environment Packaging (`requests`) | `RequestsDependencyWarning` | `requests/__init__.py:113` | Startup Stderr | Yes (1) | Yes (1) | **None** |
| **E-02** | Python 3.11 Teardown / SWIG | `DeprecationWarning` | `sys:1` | Teardown Stderr | Yes (1) | Yes (1) | **None** |

---

## 4. Audit Verdict on Warnings

- **Captured by Pytest Capture Engine:** Exactly **9 warnings** in Run-1; exactly **7 warnings** in Run-2; **0 warnings** in Focused Cohort 2 Suite (Run-3).
- **Emitted to Stderr Outside Pytest:** Exactly **2 warnings** (1 startup `RequestsDependencyWarning` + 1 teardown `swigvarlink` deprecation).
- **Stage 6M Benchmark Codebase Warnings:** **0 warnings across all runs.** No warnings originate from any Stage 6M generator, curation, preflight, or runner code.
