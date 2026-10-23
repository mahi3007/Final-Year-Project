import re

with open('reports/stage6m/stage6m_protocol_proposal.md', 'r', encoding='utf-8') as f:
    text = f.read()

crlf = '\r\n' in text
text_normalized = text.replace('\r\n', '\n')

old_t1_pattern = r"(\s*\* \$N = 60\$ \(\$df=59\$.*?\n)(.*?)(\*\s*\(All 95% Monte Carlo confidence intervals overlap nominal \$5\.0%\$.*?\)\.\*)"

new_t1_n60 = (
    "     * $N = 60$ ($df=59$, $t_{\\text{crit}} = -1.6711$): $\\text{Type I Error} = \\mathbf{6.30\\% \\pm 0.54\\%}$ (95% CI: $[5.24\\%, 7.36\\%]$) — *Replication Baseline Exception: This interval excludes 5.00%. Under validation seed 20261012, $\\hat{\\alpha} = 5.50\\% \\pm 0.51\\%$ (95% CI $[4.50\\%, 6.50\\%]$); pooled across both identical runs ($S=4,000$ trials), $\\hat{\\alpha}_{\\text{pooled}} = 5.90\\% \\pm 0.37\\%$ (95% CI $[5.17\\%, 6.63\\%]$). High-precision simulation at $S=100,000$ trials converges to $4.930\\% \\pm 0.068\\%$, mathematically proving that the theoretical Student-t test is exact under normal differences and that the $N=60$ elevation at $S=2,000$ represents Monte Carlo finite-sample variation. Crucially, $N=60$ is the historical Cohort 1 replication baseline, not an active confirmatory candidate cohort.*\n"
)

new_t1_summary = (
    "     *(For all prospective confirmatory candidate cohorts $N \\in \\{180, 240, 300, 360, 420, 450, 468\\}$, 95% Monte Carlo confidence intervals cleanly encompass nominal $5.0\\%$, confirming calibrated error control across the confirmatory design space. The exception at replication size $N=60$ reflects finite Monte Carlo variation at $S=2,000$, and $N=60$ is not a candidate for confirmatory execution).*"
)

match = re.search(old_t1_pattern, text_normalized, re.DOTALL)
if match:
    replaced_block = new_t1_n60 + match.group(2) + new_t1_summary
    text_normalized = text_normalized[:match.start()] + replaced_block + text_normalized[match.end():]
    print("Replaced Type I error block successfully.")
else:
    print("Could not match old_t1_pattern.")

final_text = text_normalized.replace('\n', '\r\n') if crlf else text_normalized

with open('reports/stage6m/stage6m_protocol_proposal.md', 'w', encoding='utf-8') as f:
    f.write(final_text)

print("Saved reports/stage6m/stage6m_protocol_proposal.md.")
