import json
import re
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")
S6_DIR = PROJECT_ROOT / "reports" / "stage6m"

# 1. Update stage6m_protocol_proposal.md to fix the "73" references and string escaping bugs in lines 261, 274, 281
proto_path = S6_DIR / "stage6m_protocol_proposal.md"
proto_text = proto_path.read_text(encoding="utf-8")

# Fix line 261
old_p261 = "$N = 180$ ($30 \\le 73$, 41.1% capacity) and $N = 240$ ($40 \\le 73$, 54.8% capacity)"
new_p261 = "$N = 180$ ($30 \\le 78$, 38.5% capacity) and $N = 240$ ($40 \\le 78$, 51.3% capacity)"
if old_p261 in proto_text:
    proto_text = proto_text.replace(old_p261, new_p261)
    print("Fixed line 261 in stage6m_protocol_proposal.md")
else:
    print("Warning: old_p261 not found in stage6m_protocol_proposal.md")

# Fix lines 274 and 281 literal \n and missing $N
proto_text = proto_text.replace(
    r"*  = 60$ (=59$, {\text{crit}} = -1.6711$): $\text{Type I Error} = \mathbf{6.30\% \pm 0.54\%}$ (95% CI: $[5.24\%, 7.36\%]$) — *Replication Baseline Exception: This interval excludes 5.00%. Under validation seed 20261012, $\hat{\alpha} = 5.50\% \pm 0.51\%$ (95% CI $[4.50\%, 6.50\%]$); pooled across both identical runs (=4,000$ trials), $\hat{\alpha}_{\text{pooled}} = 5.90\% \pm 0.37\%$ (95% CI $[5.17\%, 6.63\%]$). High-precision simulation at =100,000$ trials converges to .930\% \pm 0.068\%$, mathematically proving that the theoretical Student-t test is exact under normal differences and that the =60$ elevation at =2,000$ represents Monte Carlo finite-sample variation. Crucially, =60$ is the historical Cohort 1 replication baseline, not an active confirmatory candidate cohort.*\n     * $N = 180$ ($df=179$, $t_{\text{crit}} = -1.6534$): $\text{Type I Error} = \mathbf{5.40\% \pm 0.51\%}$ (95% CI: $[4.41\%, 6.39\%]$)",
    "* $N = 60$ ($df=59$, $t_{\\text{crit}} = -1.6711$): $\\text{Type I Error} = \\mathbf{6.30\\% \\pm 0.54\\%}$ (95% CI: $[5.24\\%, 7.36\\%]$) — *Replication Baseline Exception: This interval excludes 5.00%. Under validation seed 20261012, $\\hat{\\alpha} = 5.50\\% \\pm 0.51\\%$ (95% CI $[4.50\\%, 6.50\\%]$); pooled across both identical runs ($S=4,000$ trials), $\\hat{\\alpha}_{\\text{pooled}} = 5.90\\% \\pm 0.37\\%$ (95% CI $[5.17\\%, 6.63\\%]$). High-precision simulation at $S=100,000$ trials converges to $4.930\\% \\pm 0.068\\%$, mathematically proving that the theoretical Student-t test is exact under normal differences and that the $N=60$ elevation at $S=2,000$ represents Monte Carlo finite-sample variation. Crucially, $N=60$ is the historical Cohort 1 replication baseline, not an active confirmatory candidate cohort.*\n     * $N = 180$ ($df=179$, $t_{\\text{crit}} = -1.6534$): $\\text{Type I Error} = \\mathbf{5.40\\% \\pm 0.51\\%}$ (95% CI: $[4.41\\%, 6.39\\%]$)"
)

proto_text = proto_text.replace(
    r"*(For all prospective confirmatory candidate cohorts  \in \{180, 240, 300, 360, 420, 450, 468\}$, 95% Monte Carlo confidence intervals cleanly encompass nominal .0\%$, confirming calibrated error control across the confirmatory design space. The exception at replication size =60$ reflects finite Monte Carlo variation at =2,000$, and =60$ is not a candidate for confirmatory execution).*\n   - **Empirical Superiority Power ($\Delta = -0.85\text{ pp}$, $S = 2,000$ trials):**",
    "*(For all prospective confirmatory candidate cohorts $N \\in \\{180, 240, 300, 360, 420, 450, 468\\}$, 95% Monte Carlo confidence intervals cleanly encompass nominal $5.0\\%$, confirming calibrated error control across the confirmatory design space. The exception at replication size $N=60$ reflects finite Monte Carlo variation at $S=2,000$, and $N=60$ is not a candidate for confirmatory execution).*\n   - **Empirical Superiority Power ($\\Delta = -0.85\\text{ pp}$, $S = 2,000$ trials):**"
)

proto_path.write_text(proto_text, encoding="utf-8")
print("Updated stage6m_protocol_proposal.md successfully.")
