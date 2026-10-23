import glob
import re

print("Scanning reports/stage6m/*.md for LaTeX math and set-builder notation...")
for f in sorted(glob.glob('reports/stage6m/*.md')):
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    
    # Check for \left{ or \right}
    for line_no, line in enumerate(content.splitlines(), start=1):
        if r'\left{' in line or r'\right}' in line:
            print(f"ERROR: Unescaped \\left{{ or \\right}} in {f}:{line_no}: {line}")
        
        # Check for set constructs like { s \in or {s \in without backslash \{
        matches = re.findall(r'(?<!\\)\{\s*[a-zA-Z]\s*\\in', line)
        if matches:
            print(f"WARNING: Potential unescaped set in {f}:{line_no}: {line}")

print("Scan complete.")
