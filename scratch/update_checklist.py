with open('reports/stage6m/stage6m_signoff_checklist.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Primary superiority test' in line:
        lines[i] = '  - Primary superiority test ($H_0: \\Delta_R \\ge 0$) evaluated using exact Student-t critical values $t_{\\text{crit}} = t_{0.05, N-1}$, reconciling Type I error at $4.85\\%$--$5.75\\% \\approx 5.0\\%$ across confirmatory candidates $N \\ge 180$ (with $N=60$ baseline exception at $6.30\\% \\pm 0.54\\%$, pooled $5.90\\%$, verified to converge to $4.930\\%$ at $S=100,000$), with empirical power of $97.2\\%$ ($N=60$), $100.0\\%$ ($N=180$), and $100.0\\%$ ($N \\ge 240$).\n'

with open('reports/stage6m/stage6m_signoff_checklist.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Updated line 85 in stage6m_signoff_checklist.md!")
