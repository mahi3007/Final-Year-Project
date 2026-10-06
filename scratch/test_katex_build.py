import os
import re
import json
import subprocess
from pathlib import Path
import markdown

KATEX_PATH = Path("C:/Users/venka/AppData/Local/npm-cache/_npx/8c2cfac42696c54b/node_modules/katex")

def render_markdown_math_katex(md_text):
    """
    Parse display math ($$...$$) and inline math ($...$) from markdown,
    pre-render using KaTeX via Node.js, and replace with HTML.
    """
    # 1. First, identify and extract all display math blocks ($$ ... $$)
    # Use placeholder tokens to prevent inline regex from touching block math
    display_blocks = []
    
    def repl_display(match):
        idx = len(display_blocks)
        eq = match.group(1).strip()
        display_blocks.append(eq)
        return f"___KATEX_DISPLAY_BLOCK_{idx}___"
    
    # Match $$...$$ across multiple lines
    text_no_display = re.sub(r"\$\$(.*?)\$\$", repl_display, md_text, flags=re.DOTALL)
    
    # 2. Identify and extract all inline math ($...$)
    inline_blocks = []
    
    def repl_inline(match):
        idx = len(inline_blocks)
        eq = match.group(1).strip()
        inline_blocks.append(eq)
        return f"___KATEX_INLINE_BLOCK_{idx}___"
    
    # Match $...$ on a single line (avoid matching across lines or empty $$)
    text_tokens = re.sub(r"\$([^\$\n]+)\$", repl_inline, text_no_display)
    
    print(f"Extracted {len(display_blocks)} display equations and {len(inline_blocks)} inline equations.")
    
    # 3. Batch render with Node.js KaTeX
    payload = {
        "display": display_blocks,
        "inline": inline_blocks
    }
    Path("scratch/katex_batch_in.json").write_text(json.dumps(payload), encoding="utf-8")
    
    node_script = f"""
    const katex = require('{KATEX_PATH.as_posix()}');
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('scratch/katex_batch_in.json', 'utf8'));
    
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
    
    fs.writeFileSync('scratch/katex_batch_out.json', JSON.stringify({{
        display: renderedDisplay,
        inline: renderedInline
    }}), 'utf8');
    """
    
    res = subprocess.run(["node", "-e", node_script], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Node KaTeX error: {res.stderr}")
        
    results = json.loads(Path("scratch/katex_batch_out.json").read_text(encoding="utf-8"))
    
    # 4. Substitute rendered KaTeX back into text
    # First substitute inline tokens
    out_text = text_tokens
    for idx, rendered in enumerate(results["inline"]):
        token = f"___KATEX_INLINE_BLOCK_{idx}___"
        out_text = out_text.replace(token, rendered)
        
    # Then substitute display tokens wrapped in math card container
    for idx, rendered in enumerate(results["display"]):
        token = f"___KATEX_DISPLAY_BLOCK_{idx}___"
        card_html = f'\n<div class="math-card"><div class="math-display">{rendered}</div></div>\n'
        out_text = out_text.replace(token, card_html)
        
    return out_text

def test_build():
    f_md = Path("reports/project_report/formula_reference.md")
    f_text = f_md.read_text(encoding="utf-8")
    
    rendered_text = render_markdown_math_katex(f_text)
    f_body = markdown.markdown(rendered_text, extensions=["tables", "fenced_code", "toc"])
    
    # Check for any remaining raw LaTeX or dollar signs
    rem_dollars = re.findall(r"\$+", f_body)
    rem_backslashes = set(re.findall(r"\\[a-zA-Z%]+", f_body))
    print(f"Audit results: Remaining dollar signs={len(rem_dollars)}, Remaining backslashes={len(rem_backslashes)}")
    if rem_backslashes:
        print("Backslashes found:", rem_backslashes)
        
    # Read katex.min.css
    katex_css = (KATEX_PATH / "dist/katex.min.css").read_text(encoding="utf-8")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Formula Handbook & Mathematical Reference Guide</title>
<style>
{katex_css}

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
@media print {{
    body {{ background: #ffffff; padding: 0; }}
    article {{ box-shadow: none; padding: 0; }}
    .math-card {{ page-break-inside: avoid; overflow: visible !important; }}
    table {{ page-break-inside: avoid; }}
    h2, h3 {{ page-break-after: avoid; }}
    * {{ scrollbar-width: none !important; }}
    ::-webkit-scrollbar {{ display: none !important; }}
}}
</style>
</head>
<body>
<article>
{f_body}
</article>
</body>
</html>"""
    
    out_html = Path("reports/project_report/formula_reference.html")
    out_html.write_text(html, encoding="utf-8")
    print(f"Generated {out_html} ({out_html.stat().st_size:,} bytes)")
    
    # Test PDF generation
    edge_exe = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    out_pdf = Path("reports/project_report/formula_reference.pdf")
    cmd = [
        str(edge_exe),
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf.resolve()}",
        str(out_html.resolve()),
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated PDF: {out_pdf} ({out_pdf.stat().st_size:,} bytes)")

if __name__ == "__main__":
    test_build()
