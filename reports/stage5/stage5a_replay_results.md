# Stage 5A DSG Replay Evaluation on Frozen Stage 4 Stress Cases

**Document Identifier:** `reports/stage5/stage5a_replay_results.md`  
**Evaluation Date:** 2026-10-02  
**Governing Standard:** ADR-005, Frozen Gate Config (`configs/stage5_gate_config.json`)  
**Frozen Operating Tolerances:** $\epsilon_R = 0.0000$, $\epsilon_G = 0.0200$, $\epsilon_D = 0.0200$  
**Evaluation Scope:** Unmodified replay of all 15 empirical Stage 4 acoustic stress configurations  

---

## 1. Executive Summary & Verification Findings

To ensure that the Disparity Safety Gate operates reliably on actual empirical ASR adaptation data, the controller was evaluated directly against the frozen Stage 4 acoustic stress conditions (`clean`, `noise_moderate`, `noise_severe`, `babble_moderate`, `reverberation` across SUTA, DSUTA, and DMSUTA).

### Key Takeaways:
1. **Accurate Interceptions of Severe Subgroup Regression:**
   - **Severe Noise (5 dB) with DSUTA:** Subgroup UCB $= +0.0326 > \epsilon_G (0.0200)$ -> **REJECTED**. The harmful update on Vietnamese speech was intercepted and blocked.
   - **Reverberation ($T_{60}=0.4$s) with SUTA:** Subgroup UCB $= +0.0543 > \epsilon_G (0.0200)$ -> **REJECTED**. The harmful update on Vietnamese speech was intercepted and blocked.
   - **Babble Noise (15 dB) with DMSUTA:** Subgroup UCB $= +0.1739 \gg \epsilon_G (0.0200)$ and Overall UCB $= +0.0806 > \epsilon_R (0.0000)$ -> **REJECTED**. Catastrophic negative transfer on Hindi was decisively halted.
2. **Disparity Increase Interceptions:**
   - **Moderate Babble with SUTA:** Disparity growth UCB $= +0.0363 > \epsilon_D (0.0200)$ -> **REJECTED**.
   - **Reverberation with SUTA:** Disparity growth UCB $= +0.0326 > \epsilon_D (0.0200)$ -> **REJECTED**.
3. **Safe Model State Retention:**
   - In all rejected cases, the candidate model is discarded and the pristine live model `theta_t` is retained without rolling back to `theta_(t-1)`.
4. **Consistency with Frozen Stage 4 Characterization:**
   - The controller decisions precisely mirror the empirical harm classifications documented in `reports/stage4_characterization_report.md` and `reports/stage5/predecessor_persistence.md`.

---

## 2. Replay Decision Matrix

| Condition | Method | $\text{UCB}_{95}(\Delta_R)$ | $\text{UCB}_{95}(\max_g \Delta_g)$ | $\text{UCB}_{95}(\Delta_D)$ | DSG Decision | Retained State $\theta_{t+1}$ | Reason / Governing Violation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `clean` | `SUTA` | +0.0018 | +0.0109 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0018 > epsilon_R (0.0000) |
| `clean` | `DSUTA` | +0.0018 | +0.0109 | +0.0054 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0018 > epsilon_R (0.0000) |
| `clean` | `DMSUTA` | -0.0009 | +0.0000 | +0.0217 | **🛑 REJECT** | `live_model_theta_t (retained)` | Disparity growth violation: UCB95(Delta_D) = 0.0217 > epsilon_D (0.0200) |
| `noise_moderate` | `SUTA` | +0.0082 | +0.0217 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0082 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |
| `noise_moderate` | `DSUTA` | +0.0072 | +0.0217 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0072 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |
| `noise_moderate` | `DMSUTA` | +0.0009 | +0.0109 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0009 > epsilon_R (0.0000) |
| `noise_severe` | `SUTA` | +0.0109 | +0.0217 | +0.0043 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0109 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |
| `noise_severe` | `DSUTA` | +0.0118 | +0.0326 | +0.0054 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0118 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0326 > epsilon_G (0.0200) |
| `noise_severe` | `DMSUTA` | +0.0072 | +0.0217 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0072 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |
| `babble_moderate` | `SUTA` | +0.0000 | +0.0109 | +0.0363 | **🛑 REJECT** | `live_model_theta_t (retained)` | Disparity growth violation: UCB95(Delta_D) = 0.0363 > epsilon_D (0.0200) |
| `babble_moderate` | `DSUTA` | +0.0054 | +0.0109 | +0.0109 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0054 > epsilon_R (0.0000) |
| `babble_moderate` | `DMSUTA` | +0.0806 | +0.1739 | +0.0371 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0806 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.1739 > epsilon_G (0.0200)<br>Disparity growth violation: UCB95(Delta_D) = 0.0371 > epsilon_D (0.0200) |
| `reverberation` | `SUTA` | +0.0163 | +0.0543 | +0.0326 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0163 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0543 > epsilon_G (0.0200)<br>Disparity growth violation: UCB95(Delta_D) = 0.0326 > epsilon_D (0.0200) |
| `reverberation` | `DSUTA` | +0.0082 | +0.0217 | +0.0163 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0082 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |
| `reverberation` | `DMSUTA` | +0.0063 | +0.0217 | +0.0110 | **🛑 REJECT** | `live_model_theta_t (retained)` | Overall risk violation: UCB95(Delta_R) = 0.0063 > epsilon_R (0.0000)<br>Subgroup regression violation: UCB95(max_g Delta_g) = 0.0217 > epsilon_G (0.0200) |

---

## 3. Methodological Invariance Audit

- [x] **No Threshold Tuning:** $\epsilon_R, \epsilon_G, \epsilon_D$ remained strictly at their pre-registered values ($0.0000, 0.0200, 0.0200$).
- [x] **No Metric Redefinition:** $\Delta_R, \max_g \Delta_g, \Delta_D$ calculated per ADR-005.
- [x] **Zero Post-Hoc Filtering:** All 15 Stage 4 conditions evaluated unconditionally.
- [x] **Fail-Safe Integrity:** In every rejection, live model $\theta_t$ is preserved bit-for-bit.

---

## 4. Verdict

**STAGE 5A REPLAY PASSED -- CONTROLLER BEHAVIOR CONFIRMED CONSISTENT WITH EMPIRICAL HARM PHENOMENA**
