# CTTA Methods Specification: SUTA, DSUTA, and DMSUTA
**Protocol Version:** `v1.0.0-canonical`  
**Target Backbone:** `facebook/wav2vec2-base-960h` (CTC-based SSL ASR)  
**Track:** Track A Discovery  

---

## 1. SUTA (Single-Utterance Test-Time Adaptation)
*Reference:* Lin, G. T., Li, S. W., & Lee, H. Y. (2022). *Listen, Adapt, Better WER: Source-free Single-utterance Test-time Adaptation for Automatic Speech Recognition.* Interspeech / arXiv:2203.14222.

### 1.1 Mathematical Objective
For an unlabeled input audio window $B_t = \{x_1, \dots, x_k\}$, let $z_t \in \mathbb{R}^{T \times C}$ denote the frame-level output logits across vocabulary $C$.
Softmax probabilities with temperature $T_{\text{temp}} = 2.5$:
$$\hat{p}_{t,c} = \frac{\exp(z_{t,c} / T_{\text{temp}})}{\sum_{c'=1}^C \exp(z_{t,c'} / T_{\text{temp}})}$$

The unsupervised adaptation loss combines **Entropy Minimization** ($L_{\text{em}}$) and **Minimum Class Confusion** ($L_{\text{mcc}}$):
$$L_{\text{SUTA}} = \alpha L_{\text{em}} + (1 - \alpha) L_{\text{mcc}}$$

Where:
1. **Entropy Minimization ($L_{\text{em}}$):**
   $$L_{\text{em}} = - \frac{1}{T} \sum_{t=1}^T \sum_{c=1}^C \hat{p}_{t,c} \log(\hat{p}_{t,c} + \epsilon)$$
   Encourages the model to make sharp, confident token predictions for the incoming speech.

2. **Minimum Class Confusion ($L_{\text{mcc}}$):**
   Let $\hat{Y} \in \mathbb{R}^{T \times C}$. The class correlation matrix $\tilde{C} \in \mathbb{R}^{C \times C}$ is:
   $$\tilde{C}_{j,k} = \frac{\sum_{t=1}^T \hat{p}_{t,j} \hat{p}_{t,k}}{\sqrt{\sum_{t=1}^T \hat{p}_{t,j}} \sqrt{\sum_{t=1}^T \hat{p}_{t,k}} + \epsilon}$$
   MCC penalizes pairwise ambiguity between classes:
   $$L_{\text{mcc}} = \frac{1}{C(C-1)} \sum_{j=1}^C \sum_{k \neq j}^C \tilde{C}_{j,k}$$

### 1.2 Trainable Parameters
- **Only LayerNorm affine parameters:** `weight` ($\gamma$) and `bias` ($\beta$) of all LayerNorm layers in Wav2Vec2 (`encoder.layers.*.layer_norm`, `encoder.layer_norm`, `feature_projection.layer_norm`).
- All other parameters (CNN feature encoder, attention weights, linear projections, CTC head) remain **strictly frozen**.
- Trainable parameter ratio: $\approx 0.05\%$ of total model weights.

### 1.3 Optimization & Hyperparameters
- **Optimizer:** AdamW ($\beta_1 = 0.9, \beta_2 = 0.999$, weight decay = 0.0).
- **Learning rate ($\eta$):** $1 \times 10^{-4}$.
- **Temperature ($T_{\text{temp}}$):** $2.5$.
- **Weight $\alpha$:** $0.5$ (balanced EM and MCC).
- **Adaptation steps per window:** $N_{\text{steps}} = 1$.
- **Reset behavior:** In continual SUTA, parameters accumulate across windows without periodic resets ($\theta_0 \to \theta_1 \to \dots \to \theta_T$).

---

## 2. DSUTA (Dynamic SUTA)
*Reference:* Lin, G. T., et al. (2024). *Continual Test-time Adaptation for End-to-end Speech Recognition on Noisy Speech.* EMNLP 2024.

### 2.1 Adaptation Objective & Parameter Scope
- Inherits the SUTA loss function ($L_{\text{em}} + L_{\text{mcc}}$) and LayerNorm parameter update scope.
- Operates in a **continual adaptation** mode across the sequence of windows.

### 2.2 Dynamic Reset Mechanism
- Continual adaptation under non-stationary shifts is prone to error accumulation and representational collapse.
- DSUTA maintains a running exponential moving average of normalized utterance entropy:
  $$\bar{H}_t = (1 - \rho) \bar{H}_{t-1} + \rho H(B_t)$$
  where $\rho = 0.2$ is the momentum parameter.
- **Reset Criterion:**
  If the current window entropy $H(B_t)$ exceeds an adaptive threshold relative to running history:
  $$H(B_t) > \tau_{\text{reset}} \cdot \bar{H}_{t-1}$$
  or if absolute entropy indicates severe divergence ($H(B_t) > H_{\text{max}}$), a **Dynamic Reset** is triggered:
  $$\theta_{t+1} \leftarrow \theta_0$$
  The model parameters are rolled back to the original source weights $\theta_0$, shedding accumulated drift.

---

## 3. DMSUTA (Dynamic Model-Bank SUTA)
*Reference:* Wang, Y., et al. (2025). *Dynamic Model-bank Test-time Adaptation for Automatic Speech Recognition.* EMNLP 2025.

### 3.1 Architecture: Dynamic Model Bank
Instead of relying on a single evolving model or hard reset, DMSUTA maintains a **model bank** of historical checkpoints:
$$\mathcal{M} = \{\theta_0, \theta_{(1)}, \theta_{(2)}, \dots, \theta_{(M)}\}$$
where $\theta_0$ is the permanent source anchor model, and capacity $M_{\text{bank}} = 3$.

### 3.2 Workflow per Window $B_t$
1. **Checkpoint Selection:**
   Each model $\theta_m \in \mathcal{M}$ evaluates $B_t$. The uncertainty/entropy $H(\theta_m; B_t)$ is computed.
   The model with the lowest entropy (highest confidence) is selected:
   $$\theta^*_t = \arg\min_{\theta_m \in \mathcal{M}} H(\theta_m; B_t)$$
   $\theta^*_t$ produces the live prequential hypothesis $\hat{Y}_t$ for window $B_t$.
2. **Local Adaptation:**
   $\theta^*_t$ is adapted on unlabeled $B_t$ via the SUTA loss to produce candidate $\theta'_{t+1}$.
3. **Model Bank Management (Append & Prune):**
   - If candidate $\theta'_{t+1}$ achieves low entropy ($H < \tau_{\text{accept}}$), it is appended to $\mathcal{M}$.
   - If $|\mathcal{M}| > M_{\text{bank}}$, the bank is pruned by discarding the highest-entropy checkpoint (excluding source anchor $\theta_0$, which is never pruned).

---

## 4. Invariant Prequential Workflow Across All Methods
For all three methods, the prequential evaluation rule remains absolute:
$$\boxed{B_t \xrightarrow{\theta_t} \text{Record Live Prediction } \hat{Y}_t \xrightarrow{\text{Offline Eval}} (S, D, I, N) \implies B_t \xrightarrow{\text{Unlabeled Adapt}} \theta_{t+1}}$$
Offline ground-truth labels and evaluation routines are strictly inaccessible during online inference and adaptation.
