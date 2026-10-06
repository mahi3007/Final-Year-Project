import markdown
from pathlib import Path

def build_html():
    md_path = Path("reports/project_report/master_research_report.md")
    html_path = Path("reports/project_report/master_research_report.html")

    md_text = md_path.read_text(encoding="utf-8")
    
    # Preprocess mermaid blocks for html
    lines = md_text.splitlines()
    processed_lines = []
    in_mermaid = False
    mermaid_block = []
    
    for line in lines:
        if line.strip() == "```mermaid":
            in_mermaid = True
            mermaid_block = []
            continue
        elif in_mermaid and line.strip() == "```":
            in_mermaid = False
            mermaid_code = "\n".join(mermaid_block)
            processed_lines.append(f'<div class="mermaid">\n{mermaid_code}\n</div>')
            continue
        
        if in_mermaid:
            mermaid_block.append(line)
        else:
            processed_lines.append(line)
            
    processed_md = "\n".join(processed_lines)
    html_body = markdown.markdown(processed_md, extensions=["tables", "fenced_code", "toc"])

    header = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DSG-CTTA Master Research Dossier</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'neutral'});</script>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #1f2937;
    max-width: 1050px;
    margin: 0 auto;
    padding: 40px 20px;
    background-color: #f9fafb;
}
article {
    background: #ffffff;
    padding: 50px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
h1, h2, h3, h4 {
    color: #111827;
    font-weight: 700;
    margin-top: 1.5em;
}
h1 {
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.3em;
    font-size: 2.2em;
}
h2 {
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 0.2em;
    font-size: 1.6em;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    font-size: 0.9em;
}
th, td {
    border: 1px solid #d1d5db;
    padding: 8px 12px;
    text-align: left;
}
th {
    background-color: #f3f4f6;
    font-weight: 600;
}
tr:nth-child(even) {
    background-color: #f9fafb;
}
pre {
    background-color: #1f2937;
    color: #f9fafb;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
}
code {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.9em;
}
p > code, li > code {
    background-color: #f3f4f6;
    color: #ef4444;
    padding: 2px 4px;
    border-radius: 4px;
}
blockquote {
    border-left: 4px solid #3b82f6;
    margin: 1.5em 0;
    padding: 0.5em 1em;
    color: #4b5563;
    background-color: #eff6ff;
}
.mermaid {
    text-align: center;
    margin: 2em 0;
    background: #ffffff;
    padding: 1em;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
}
@media print {
    body { background: #fff; padding: 0; }
    article { box-shadow: none; padding: 0; }
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

if __name__ == "__main__":
    build_html()
