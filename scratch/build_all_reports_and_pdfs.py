import os
import re
import json
import shutil
import subprocess
from pathlib import Path
import markdown

KATEX_MODULE_PATH = Path("C:/Users/venka/AppData/Local/npm-cache/_npx/8c2cfac42696c54b/node_modules/katex")
PROJECT_REPORT_DIR = Path("reports/project_report")

def ensure_katex_assets():
    """Ensure fonts and CSS from KaTeX are copied to reports/project_report/."""
    dst_fonts = PROJECT_REPORT_DIR / "fonts"
    dst_fonts.mkdir(parents=True, exist_ok=True)
    
    src_fonts = KATEX_MODULE_PATH / "dist/fonts"
    for f in src_fonts.glob("*.*"):
        shutil.copy2(f, dst_fonts / f.name)
        
    src_css = KATEX_MODULE_PATH / "dist/katex.min.css"
    dst_css = PROJECT_REPORT_DIR / "katex.min.css"
    shutil.copy2(src_css, dst_css)
    print("KaTeX fonts and CSS successfully verified in reports/project_report/.")

def render_markdown_math_katex(md_text):
    """
    Parse display math ($$...$$) and inline math ($...$) from markdown,
    pre-render using KaTeX via Node.js into clean static HTML with zero client-side JS.
    """
    display_blocks = []
    
    def repl_display(match):
        idx = len(display_blocks)
        eq = match.group(1).strip()
        display_blocks.append(eq)
        return f"___KATEX_DISPLAY_BLOCK_{idx}___"
    
    text_no_display = re.sub(r"\$\$(.*?)\$\$", repl_display, md_text, flags=re.DOTALL)
    
    inline_blocks = []
    
    def repl_inline(match):
        idx = len(inline_blocks)
        eq = match.group(1).strip()
        inline_blocks.append(eq)
        return f"___KATEX_INLINE_BLOCK_{idx}___"
    
    text_tokens = re.sub(r"\$([^\$\n]+)\$", repl_inline, text_no_display)
    
    print(f"Extracted {len(display_blocks)} display equations and {len(inline_blocks)} inline equations.")
    
    scratch_dir = Path("scratch")
    scratch_dir.mkdir(exist_ok=True)
    
    payload = {
        "display": display_blocks,
        "inline": inline_blocks
    }
    in_json = scratch_dir / "katex_batch_in.json"
    out_json = scratch_dir / "katex_batch_out.json"
    in_json.write_text(json.dumps(payload), encoding="utf-8")
    
    node_script = f"""
    const katex = require('{KATEX_MODULE_PATH.as_posix()}');
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('{in_json.as_posix()}', 'utf8'));
    
    const renderedDisplay = data.display.map(eq => {{
        try {{
            return katex.renderToString(eq, {{displayMode: true, throwOnError: false, output: 'html'}});
        }} catch(e) {{
            return `<div class="katex-error">${{e.message}}</div>`;
        }}
    }});
    
    const renderedInline = data.inline.map(eq => {{
        try {{
            return katex.renderToString(eq, {{displayMode: false, throwOnError: false, output: 'html'}});
        }} catch(e) {{
            return `<span class="katex-error">${{e.message}}</span>`;
        }}
    }});
    
    fs.writeFileSync('{out_json.as_posix()}', JSON.stringify({{
        display: renderedDisplay,
        inline: renderedInline
    }}), 'utf8');
    """
    
    res = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Node KaTeX error: {res.stderr}")
        
    results = json.loads(out_json.read_text(encoding="utf-8"))
    
    out_text = text_tokens
    for idx, rendered in enumerate(results["inline"]):
        token = f"___KATEX_INLINE_BLOCK_{idx}___"
        out_text = out_text.replace(token, rendered)
        
    for idx, rendered in enumerate(results["display"]):
        token = f"___KATEX_DISPLAY_BLOCK_{idx}___"
        card_html = f'\n<div class="math-card"><div class="math-display">{rendered}</div></div>\n'
        out_text = out_text.replace(token, card_html)
        
    return out_text

def build_pdf_from_html(html_file, pdf_file):
    edge_exe = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge_exe.exists():
        print("Microsoft Edge not found!")
        return False
        
    cmd = [
        str(edge_exe),
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_file.resolve()}",
        str(html_file.resolve()),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if pdf_file.exists():
        print(f"Generated PDF: {pdf_file} ({pdf_file.stat().st_size:,} bytes)")
        return True
    else:
        print("Failed to generate PDF. Error:", res.stderr)
        return False

def get_shared_css():
    katex_css = (KATEX_MODULE_PATH / "dist/katex.min.css").read_text(encoding="utf-8")
    return f"""{katex_css}

@page {{
    size: letter;
    margin: 1.8cm 1.5cm 1.8cm 1.5cm;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #1e293b;
    max-width: 950px;
    margin: 0 auto;
    padding: 30px 20px;
    background-color: #f8fafc;
}}
article {{
    background: #ffffff;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}}
h1 {{
    color: #0f172a;
    font-size: 2.1em;
    font-weight: 800;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 0.3em;
    margin-bottom: 0.5em;
}}
h2 {{
    color: #1e3a8a;
    font-size: 1.45em;
    font-weight: 700;
    margin-top: 2.2em;
    padding-bottom: 0.3em;
    border-bottom: 1.5px solid #e2e8f0;
}}
h3 {{
    color: #334155;
    font-size: 1.15em;
    font-weight: 600;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    font-size: 0.9em;
}}
th, td {{
    border: 1px solid #cbd5e1;
    padding: 8px 12px;
    text-align: left;
}}
th {{
    background-color: #f1f5f9;
    font-weight: 600;
    color: #0f172a;
}}
tr:nth-child(even) {{
    background-color: #f8fafc;
}}
.math-card {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-left: 6px solid #2563eb;
    border-radius: 6px;
    padding: 14px 20px;
    margin: 1.1em 0;
    overflow: visible;
}}
.math-display {{
    font-size: 1.08em;
    text-align: center;
    color: #0f172a;
    overflow: visible;
}}
.katex {{
    font-size: 1.05em;
}}
.katex-display {{
    margin: 0.3em 0 !important;
    overflow: visible !important;
}}
blockquote {{
    border-left: 4px solid #3b82f6;
    margin: 1.2em 0;
    padding: 0.6em 1.2em;
    color: #334155;
    background-color: #eff6ff;
    border-radius: 0 4px 4px 0;
}}
code {{
    font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
    font-size: 0.88em;
    background-color: #f1f5f9;
    color: #b91c1c;
    padding: 2px 4px;
    border-radius: 4px;
}}
pre {{
    background-color: #1e293b;
    color: #f8fafc;
    padding: 14px;
    border-radius: 6px;
    overflow-x: auto;
}}
.mermaid {{
    text-align: center;
    margin: 1.5em 0;
    background: #ffffff;
    padding: 15px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}}
@media print {{
    body {{ background: #ffffff; padding: 0; }}
    article {{ box-shadow: none; padding: 0; }}
    .math-card {{ page-break-inside: avoid; overflow: visible !important; }}
    table {{ page-break-inside: avoid; }}
    h2, h3 {{ page-break-after: avoid; }}
    * {{ scrollbar-width: none !important; }}
    ::-webkit-scrollbar {{ display: none !important; }}
}}"""

def main():
    print(">>> 0. Verifying KaTeX assets...")
    ensure_katex_assets()
    css_content = get_shared_css()
    
    print("\n>>> 1. Processing Formula Reference...")
    f_md = PROJECT_REPORT_DIR / "formula_reference.md"
    f_html = PROJECT_REPORT_DIR / "formula_reference.html"
    f_pdf = PROJECT_REPORT_DIR / "formula_reference.pdf"
    
    f_text = f_md.read_text(encoding="utf-8")
    f_rendered = render_markdown_math_katex(f_text)
    f_body = markdown.markdown(f_rendered, extensions=["tables", "fenced_code", "toc"])
    
    f_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Formula Handbook & Mathematical Reference Guide</title>
<style>
{css_content}
</style>
</head>
<body>
<article>
{f_body}
</article>
</body>
</html>"""
    f_html.write_text(f_template, encoding="utf-8")
    print(f"Generated {f_html} ({f_html.stat().st_size:,} bytes)")
    build_pdf_from_html(f_html, f_pdf)
    
    print("\n>>> 2. Processing Master Research Report...")
    m_md = PROJECT_REPORT_DIR / "master_research_report.md"
    m_html = PROJECT_REPORT_DIR / "master_research_report.html"
    m_pdf = PROJECT_REPORT_DIR / "master_research_report.pdf"
    
    m_text = m_md.read_text(encoding="utf-8")
    
    # Preprocess mermaid diagrams
    m_lines = m_text.splitlines()
    processed_m_lines = []
    in_mermaid = False
    mermaid_block = []
    for line in m_lines:
        if line.strip() == "```mermaid":
            in_mermaid = True
            mermaid_block = []
            continue
        elif in_mermaid and line.strip() == "```":
            in_mermaid = False
            mermaid_code = "\n".join(mermaid_block)
            processed_m_lines.append(f'<div class="mermaid">\n{mermaid_code}\n</div>')
            continue
        
        if in_mermaid:
            mermaid_block.append(line)
        else:
            processed_m_lines.append(line)
            
    m_intermediate = "\n".join(processed_m_lines)
    m_rendered = render_markdown_math_katex(m_intermediate)
    m_body = markdown.markdown(m_rendered, extensions=["tables", "fenced_code", "toc"])
    
    m_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Master Research Dossier</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
<style>
{css_content}
</style>
</head>
<body>
<article>
{m_body}
</article>
</body>
</html>"""
    m_html.write_text(m_template, encoding="utf-8")
    print(f"Generated {m_html} ({m_html.stat().st_size:,} bytes)")
    build_pdf_from_html(m_html, m_pdf)
    
    print("\n>>> 3. Processing Master Model Benchmarks and Accent Metrics...")
    b_md = PROJECT_REPORT_DIR / "master_model_benchmarks_and_accent_metrics.md"
    b_html = PROJECT_REPORT_DIR / "master_model_benchmarks_and_accent_metrics.html"
    b_pdf = PROJECT_REPORT_DIR / "master_model_benchmarks_and_accent_metrics.pdf"
    
    b_text = b_md.read_text(encoding="utf-8")
    b_rendered = render_markdown_math_katex(b_text)
    b_body = markdown.markdown(b_rendered, extensions=["tables", "fenced_code", "toc"])
    
    b_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Master Model Benchmark & Accent Performance Ledger</title>
<style>
{css_content}
</style>
</head>
<body>
<article>
{b_body}
</article>
</body>
</html>"""
    b_html.write_text(b_template, encoding="utf-8")
    print(f"Generated {b_html} ({b_html.stat().st_size:,} bytes)")
    build_pdf_from_html(b_html, b_pdf)
    
    print("\n=======================================================")
    print("ALL REPORTS AND PDFS SUCCESSFULLY REBUILT WITH KATEX!")
    print("=======================================================")

if __name__ == "__main__":
    main()

