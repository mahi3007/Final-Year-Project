with open('reports/stage6m/stage6m_power_analysis.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith("- $N=60$ ($df=59$):"):
        print(f"Updating line {i+1} for N=60")
        lines[i] = "- $N=60$ ($df=59$): $t_{\\text{crit}} = -1.6711$. Empirical Type I error is **$6.30\\% \\pm 0.54\\%$** (95% CI $[5.24\\%, 7.36\\%]$) — *Replication Baseline Exception (CI excludes 5.00%; validation seed gives $5.50\\% \\pm 0.51\\%$; pooled $S=4,000$ gives $5.90\\% \\pm 0.37\\%$, CI $[5.17\\%, 6.63\\%]$; high-precision $S=100,000$ converges to $4.930\\% \\pm 0.068\\%$. Note: $N=60$ is the historical Cohort 1 replication baseline, not an active confirmatory candidate).*\n"
    elif "Because all 95% confidence intervals encompass 5.0%" in line:
        print(f"Updating line {i+1} for Note")
        lines[i] = "> The observed empirical false-positive rates are close to the nominal 5% level under the specified simulation assumptions. Their Monte Carlo uncertainty ($\\pm 0.48\\%\\text{ to }\\pm 0.54\\%$) is explicitly documented. For all prospective confirmatory candidate cohorts ($N \\ge 180$, $N \\in \\{180, 240, 300, 360, 420, 450, 468\\}$), 95% confidence intervals cleanly encompass 5.0%, confirming exact error calibration across the confirmatory design space. The exception at baseline replication size $N=60$ ($[5.24\\%, 7.36\\%]$) reflects finite Monte Carlo variation at $S=2,000$, and $N=60$ is not a candidate for confirmatory execution. (All prior draft figures such as $4.70\\%$ or $4.80\\%$ are superseded).\n"
    elif "11. Sub-Boundary Drift (ΔD = +1.30 pp)*" in line:
        print(f"Updating line {i+1} for Scenario 11")
        lines[i] = line.replace("0.00%", " N/A ")
    elif "* Note: For ΔD = +1.30 pp, true drift is within tolerance" in line:
        print(f"Updating line {i+1} for Scenario 11 Note")
        lines[i] = "* Note: For ΔD = +1.30 pp, true drift is within tolerance (τ_D = +1.40 pp). Under the formal conditional definition P(U <= τ_D | ΔD > τ_D), False Safety Declaration is formally NOT APPLICABLE (N/A) because the conditioning violation event is empty (true drift does not exceed tolerance). At the exact boundary (ΔD = +1.40 pp), passing safety represents Boundary False Declaration Probability.\n"

# Deduplicate duplicated line 273 if present
dedup_lines = []
for i, line in enumerate(lines):
    if i > 0 and line == lines[i-1] and "Simulation-Calibrated Status" in line:
        print(f"Skipping duplicate line {i+1}")
        continue
    dedup_lines.append(line)

with open('reports/stage6m/stage6m_power_analysis.md', 'w', encoding='utf-8') as f:
    f.writelines(dedup_lines)

print("Saved reports/stage6m/stage6m_power_analysis.md successfully!")
