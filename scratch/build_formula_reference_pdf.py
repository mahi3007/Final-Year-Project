import subprocess
from pathlib import Path
import markdown
import re

def convert_markdown_math_to_html(md_text):
    """
    Convert markdown with math into clean, elegant HTML math elements.
    Ensures that no raw dollar signs appear in the output.
    """
    lines = md_text.splitlines()
    processed_lines = []
    in_block_math = False
    block_math_lines = []

    for line in lines:
        stripped = line.strip()
        
        # Display math $$ ... $$ on separate lines
        if stripped == "$$":
            if in_block_math:
                in_block_math = False
                eq_content = "\n".join(block_math_lines)
                html_eq = format_math_expression(eq_content)
                processed_lines.append(f'<div class="math-card"><div class="math-display">{html_eq}</div></div>')
                block_math_lines = []
            else:
                in_block_math = True
                block_math_lines = []
            continue
        elif stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 2:
            eq_content = stripped[2:-2].strip()
            html_eq = format_math_expression(eq_content)
            processed_lines.append(f'<div class="math-card"><div class="math-display">{html_eq}</div></div>')
            continue
        
        if in_block_math:
            block_math_lines.append(line)
        else:
            # Replace inline math $...$
            line_processed = process_inline_math(line)
            processed_lines.append(line_processed)

    return "\n".join(processed_lines)

def format_math_expression(eq):
    """Format LaTeX display equations into clean HTML/Unicode typography."""
    res = eq
    # Handle fraction \frac{num}{den}
    while r"\frac{" in res:
        res = re.sub(
            r"\\frac\{([^{}]+)\}\{([^{}]+)\}",
            r'<span class="fraction"><span class="numerator">\1</span><span class="denominator">\2</span></span>',
            res
        )
    
    # Common mathematical symbols
    replacements = [
        (r"\\text\{WER\}", "<strong>WER</strong>"),
        (r"\\text\{CER\}", "<strong>CER</strong>"),
        (r"\\text\{UCB\}_\{95\}", "<strong>UCB</strong><sub>95</sub>"),
        (r"\\text\{UCB\}", "<strong>UCB</strong>"),
        (r"\\text\{ACCEPT\}", "<strong>ACCEPT</strong>"),
        (r"\\text\{REJECT\}", "<strong>REJECT</strong>"),
        (r"\\text\{Reduction\}_\{errors\}", "<strong>Reduction</strong><sub>errors</sub>"),
        (r"\\text\{Rate Ratio \(RR\)\}_g", "<strong>Rate Ratio (RR)</strong><sub>g</sub>"),
        (r"\\text\{RR\}", "<strong>RR</strong>"),
        (r"\\text\{ref\}", "ref"),
        (r"\\text\{cand\}", "cand"),
        (r"\\text\{SUTA\}", "SUTA"),
        (r"\\text\{DSG\}", "DSG"),
        (r"\\text\{No-Adapt\}", "No-Adapt"),
        (r"\\text\{char\}", "char"),
        (r"\\text\{errors\}", "errors"),
        (r"\\text\{words\}", "words"),
        (r"\\text\{spk\}", "spk"),
        (r"\\text\{speaker\}", "speaker"),
        (r"\\text\{group\}", "group"),
        (r"\\text\{SNR\}", "SNR"),
        (r"\\text\{rate\}", "rate"),
        (r"\\text\{ent\}", "ent"),
        (r"\\text\{mcc\}", "mcc"),
        (r"\\text\{sentinel\}", "sentinel"),
        (r"\\text\{max\}", "max"),
        (r"\\text\{min\}", "min"),
        (r"\\text\{Quantile\}_\{0\.95\}", "Quantile<sub>0.95</sub>"),
        (r"\\text\{In Clear Text: \}", "<em>In Clear Text: </em>"),
        (r"\\mathcal\{G\}", "<strong>G</strong>"),
        (r"\\mathcal\{S\}_\{sentinel\}", "<strong>S</strong><sub>sentinel</sub>"),
        (r"\\mathcal\{S\}", "<strong>S</strong>"),
        (r"\\mathcal\{C\}", "<strong>C</strong>"),
        (r"\\mathcal\{V\}", "<strong>V</strong>"),
        (r"\\mathcal\{L\}_\{SUTA\}", "<strong>L</strong><sub>SUTA</sub>"),
        (r"\\mathcal\{L\}_\{ent\}", "<strong>L</strong><sub>ent</sub>"),
        (r"\\mathcal\{L\}_\{mcc\}", "<strong>L</strong><sub>mcc</sub>"),
        (r"\\Delta_R", "Δ<sub>R</sub>"),
        (r"\\Delta_D", "Δ<sub>D</sub>"),
        (r"\\Delta_g", "Δ<sub>g</sub>"),
        (r"\\Delta", "Δ"),
        (r"\\max_\{g \\in \\mathcal\{G\}\}", "max<sub>g ∈ G</sub>"),
        (r"\\min_\{g \\in \\mathcal\{G\}\}", "min<sub>g ∈ G</sub>"),
        (r"\\max_g", "max<sub>g</sub>"),
        (r"\\min_g", "min<sub>g</sub>"),
        (r"\\theta_t", "θ<sub>t</sub>"),
        (r"\\theta_\{t\+1\}", "θ<sub>t+1</sub>"),
        (r"\\theta\'_t", "θ'<sub>t</sub>"),
        (r"\\theta\'", "θ'"),
        (r"\\theta_0", "θ<sub>0</sub>"),
        (r"\\theta_\{ref\}", "θ<sub>ref</sub>"),
        (r"\\theta", "θ"),
        (r"\\epsilon_R", "ε<sub>R</sub>"),
        (r"\\epsilon_G", "ε<sub>G</sub>"),
        (r"\\epsilon_D", "ε<sub>D</sub>"),
        (r"\\epsilon", "ε"),
        (r"\\delta_G", "δ<sub>G</sub>"),
        (r"\\delta_D", "δ<sub>D</sub>"),
        (r"\\delta", "δ"),
        (r"\\lambda_\{mcc\}", "λ<sub>mcc</sub>"),
        (r"\\lambda", "λ"),
        (r"\\mu_\{ij\}", "μ<sub>ij</sub>"),
        (r"\\mu", "μ"),
        (r"\\sigma", "σ"),
        (r"\\beta_0", "β<sub>0</sub>"),
        (r"\\beta_g", "β<sub>g</sub>"),
        (r"\\beta_\{SNR\}", "β<sub>SNR</sub>"),
        (r"\\beta_\{rate\}", "β<sub>rate</sub>"),
        (r"\\beta", "β"),
        (r"\\mathbf\{x\}_t", "<strong>x</strong><sub>t</sub>"),
        (r"\\mathbf\{x\}", "<strong>x</strong>"),
        (r"\\mathbf\{y\}", "<strong>y</strong>"),
        (r"\\hat\{\\mathbf\{y\}\}", "<strong>ŷ</strong>"),
        (r"\\mathbb\{I\}", "<strong>1</strong>"),
        (r"\\mathbb\{E\}", "<strong>E</strong>"),
        (r"\\mathbb\{N\}_0", "<strong>N</strong><sub>0</sub>"),
        (r"\\mathbb\{N\}_\{>0\}", "<strong>N</strong><sub>>0</sub>"),
        (r"\\mathbb\{R\}_\{>0\}", "<strong>R</strong><sub>>0</sub>"),
        (r"\\mathbb\{R\}", "<strong>R</strong>"),
        (r"\\mathcal\{N\}", "<strong>N</strong>"),
        (r"\\le", "≤"),
        (r"\\ge", "≥"),
        (r"\\land", " ∧ "),
        (r"\\lor", " ∨ "),
        (r"\\iff", " ⟺ "),
        (r"\\implies", " ⟹ "),
        (r"\\neq", "≠"),
        (r"\\pm", "±"),
        (r"\\approx", "≈"),
        (r"\\equiv", "≡"),
        (r"\\times", " × "),
        (r"\\cdot", " · "),
        (r"\\to", " → "),
        (r"\\in", " ∈ "),
        (r"\\notin", " ∉ "),
        (r"\\emptyset", "∅"),
        (r"\\cap", " ∩ "),
        (r"\\cup", " ∪ "),
        (r"\\sum_\{t=1\}\^\{T\'\}", "Σ<sub>t=1..T'</sub>"),
        (r"\\sum_\{v \\in \\mathcal\{V\}\}", "Σ<sub>v ∈ V</sub>"),
        (r"\\sum_\{g=2\}\^G", "Σ<sub>g=2..G</sub>"),
        (r"\\sum", "Σ"),
        (r"\\infty", "∞"),
        (r"\\quad", " &nbsp;&nbsp; "),
        (r"\\left\(", "("),
        (r"\\right\)", ")"),
        (r"\\{", "{"),
        (r"\\}", "}"),
        (r"\\dots", "…"),
        (r"\\log", "log"),
        (r"\\exp", "exp"),
    ]
    for p, r in replacements:
        res = re.sub(p, r, res)
    return res

def process_inline_math(text):
    """Convert $...$ inline math into styled HTML without dollar signs."""
    def repl(m):
        content = m.group(1)
        formatted = format_math_expression(content)
        return f'<span class="math-inline">{formatted}</span>'
    return re.sub(r"\$([^\$\n]+)\$", repl, text)

def build_formula_reference_pdf():
    md_path = Path("reports/project_report/formula_reference.md")
    html_path = Path("reports/project_report/formula_reference.html")
    pdf_path = Path("reports/project_report/formula_reference.pdf")

    md_text = md_path.read_text(encoding="utf-8")
    converted_md = convert_markdown_math_to_html(md_text)
    
    html_body = markdown.markdown(converted_md, extensions=["tables", "fenced_code", "toc"])

    # Enhance visual styling for formula reference handbook
    header = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Formula Handbook & Mathematical Reference Guide</title>
<style>
@page {
    size: letter;
    margin: 1.8cm 1.5cm 1.8cm 1.5cm;
    @bottom-right {
        content: "Page " counter(page);
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #1e293b;
    max-width: 950px;
    margin: 0 auto;
    padding: 30px 20px;
    background-color: #f8fafc;
}
article {
    background: #ffffff;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
h1 {
    color: #0f172a;
    font-size: 2.2em;
    font-weight: 800;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 0.3em;
    margin-bottom: 0.5em;
}
h2 {
    color: #1e3a8a;
    font-size: 1.5em;
    font-weight: 700;
    margin-top: 2.2em;
    padding-bottom: 0.3em;
    border-bottom: 1.5px solid #e2e8f0;
}
h3 {
    color: #334155;
    font-size: 1.15em;
    font-weight: 600;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    font-size: 0.9em;
}
th, td {
    border: 1px solid #cbd5e1;
    padding: 8px 12px;
    text-align: left;
}
th {
    background-color: #f1f5f9;
    font-weight: 600;
    color: #0f172a;
}
tr:nth-child(even) {
    background-color: #f8fafc;
}
.math-card {
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-left: 6px solid #2563eb;
    border-radius: 6px;
    padding: 16px 20px;
    margin: 1.2em 0;
}
.math-display {
    font-family: "Cambria Math", "STIX Two Math", "Georgia", serif;
    font-size: 1.35em;
    text-align: center;
    color: #0f172a;
    letter-spacing: 0.5px;
}
.math-inline {
    font-family: "Cambria Math", "STIX Two Math", "Georgia", serif;
    font-weight: 500;
    color: #1e3a8a;
    padding: 0 2px;
}
.fraction {
    display: inline-flex;
    flex-direction: column;
    vertical-align: middle;
    text-align: center;
    padding: 0 4px;
}
.numerator {
    border-bottom: 1.5px solid #1e293b;
    padding-bottom: 2px;
    line-height: 1.1;
}
.denominator {
    padding-top: 2px;
    line-height: 1.1;
}
blockquote {
    border-left: 4px solid #3b82f6;
    margin: 1.2em 0;
    padding: 0.6em 1.2em;
    color: #334155;
    background-color: #eff6ff;
    border-radius: 0 4px 4px 0;
}
code {
    font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
    font-size: 0.88em;
    background-color: #f1f5f9;
    color: #b91c1c;
    padding: 2px 4px;
    border-radius: 4px;
}
pre code {
    background-color: transparent;
    color: inherit;
    padding: 0;
}
pre {
    background-color: #1e293b;
    color: #f8fafc;
    padding: 14px;
    border-radius: 6px;
    overflow-x: auto;
}
ul, ol {
    padding-left: 1.6em;
}
li {
    margin-bottom: 0.4em;
}
@media print {
    body {
        background: #ffffff;
        padding: 0;
    }
    article {
        box-shadow: none;
        padding: 0;
    }
    .math-card {
        page-break-inside: avoid;
    }
    table {
        page-break-inside: avoid;
    }
}
</style>
</head>
<body>
<article>
"""
    footer = """
</article>
</body>
</html>
"""
    full_html = header + html_body + footer
    html_path.write_text(full_html, encoding="utf-8")
    print(f"Generated {html_path} ({html_path.stat().st_size:,} bytes)")

    # Print to PDF using Microsoft Edge
    edge_exe = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if edge_exe.exists():
        print(f"Printing PDF via Edge headless to {pdf_path}...")
        cmd = [
            str(edge_exe),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.resolve()}",
            str(html_path.resolve()),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if pdf_path.exists():
            print(f"PDF generated successfully: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
        else:
            print("Edge failed to write PDF. Error:", res.stderr)
    else:
        print("Microsoft Edge executable not found.")

if __name__ == "__main__":
    build_formula_reference_pdf()
