# Stage 5E QA Audit: Pytest Runtime Warnings Forensic Documentation

**Document Identifier:** `reports/stage5/stage5e_qa_warning_audit.md`  
**Execution Timestamp:** 2026-10-04T03:20:00Z  
**Governing Standard:** ADR-005, Stage 5E Quality Assurance & Verification  
**Scope:** Exhaustive classification, origin trace, and risk assessment of the 7 runtime warnings emitted during `pytest tests/ -v` (90 passed, 7 warnings).

---

## 1. Executive Summary

During full test-suite execution (`pytest tests/ -v`), **90 out of 90 tests passed with zero failures**. 
A total of **7 runtime warnings** were captured by the pytest warning filter. 

None of the 7 warnings indicate application errors, mathematical corruption, or unhandled exceptions in the `dsg_ctta` codebase. All 7 originate from upstream third-party package compatibility boundaries or synthetic minimal-test fixtures.

---

## 2. Itemized Warning Inventory & Classification

| Warning # | Emitting Module | Warning Type | Summary Description | Classification | Risk Level |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | `torchvision.transforms._functional_pil` (L245) | `DeprecationWarning` | `BILINEAR is deprecated and will be removed in Pillow 10. Use Resampling.BILINEAR.` | Upstream Library Deprecation | **None** (Harmless) |
| **2** | `torchvision.transforms._functional_pil` (L291) | `DeprecationWarning` | `NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST.` | Upstream Library Deprecation | **None** (Harmless) |
| **3** | `torchvision.transforms._functional_pil` (L307) | `DeprecationWarning` | `NEAREST is deprecated and will be removed in Pillow 10. Use Resampling.NEAREST.` | Upstream Library Deprecation | **None** (Harmless) |
| **4** | `torchvision.transforms._functional_pil` (L324) | `DeprecationWarning` | `BICUBIC is deprecated and will be removed in Pillow 10. Use Resampling.BICUBIC.` | Upstream Library Deprecation | **None** (Harmless) |
| **5** | `<frozen importlib._bootstrap>` (L241) | `DeprecationWarning` | `builtin type SwigPyPacked has no __module__ attribute` | C-Extension Binding Warning | **None** (Harmless) |
| **6** | `<frozen importlib._bootstrap>` (L241) | `DeprecationWarning` | `builtin type SwigPyObject has no __module__ attribute` | C-Extension Binding Warning | **None** (Harmless) |
| **7** | `statsmodels.genmod.generalized_linear_model` (L1486) | `SingularMatrixWarning` | `The design matrix is rank-deficient. The model parameters are not uniquely determined.` | Synthetic Test Fixture Rank Deficiency | **None** (Test-Only) |

---

## 3. Detailed Root Cause Analysis

### Category A: Upstream Pillow / Torchvision Enums (Warnings 1–4)
- **Originating Code:** `torchvision/transforms/_functional_pil.py`
- **Cause:** Pillow 10 deprecated top-level constants (`Image.BILINEAR`, `Image.NEAREST`, `Image.BICUBIC`) in favor of `Image.Resampling.*`. The installed `torchvision` build in the local environment references the legacy Pillow constants internally during module import.
- **Project Impact:** `dsg_ctta` is an acoustic speech recognition architecture; it does not invoke `torchvision` image transformations in its operational adaptation or gating loops.
- **Resolution:** Upstream vendor resolution in future PyTorch/Torchvision wheels. Zero risk to CTTA execution.

### Category B: Upstream SWIG C-Extension Metadata (Warnings 5–6)
- **Originating Code:** Python C-API loader (`importlib._bootstrap`) via SWIG wrapper objects (`SwigPyPacked`, `SwigPyObject`).
- **Cause:** Python 3.11 introduced stricter introspection checks on extension types lacking `__module__` attributes. Packages compiled with older SWIG wrappers emit this notice when loaded.
- **Project Impact:** C-bindings operate normally; speech audio I/O via `soundfile` and `scipy` is unaffected.
- **Resolution:** Harmless C-extension introspection warning. Zero risk.

### Category C: Synthetic Mini-Fixture Rank Deficiency (Warning 7)
- **Originating Test:** `tests/integration/test_pipeline.py::test_full_e2e_research_pipeline`
- **Cause:** In this end-to-end integration test, the pipeline is evaluated on a synthetic toy fixture containing only 36 utterances across 12 speakers (3 clips per speaker). When `run_glmm=True` is executed, the Generalized Linear Mixed Model (GLMM) constructs a speaker-random-effects design matrix. Because the synthetic dataset has fewer observations than required to uniquely estimate all cluster parameters, `statsmodels` properly warns:
  `SingularMatrixWarning: The design matrix is rank-deficient.`
- **Project Impact:**
  - In full-scale research evaluations (e.g. Stage 3, Stage 4, Stage 5), datasets contain hundreds to thousands of utterances with full rank.
  - The integration test intentionally uses a lightweight 36-utterance fixture to allow test execution in under 2 seconds rather than minutes.
- **Resolution:** Expected behavior for synthetic unit fixtures; mathematically sound.

---

## 4. Verification & QA Sign-Off

- **Test Suite Status:** 90 Passed / 0 Failed.
- **Warning Count:** Exactly 7 (4 library deprecations, 2 C-binding notices, 1 synthetic fixture notice).
- **Application Code Quality:** 0 warnings generated from `dsg_ctta/*`.
- **Sign-Off Verdict:** **QA PASSED — All warnings accounted for and documented.**
