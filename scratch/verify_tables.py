import re
from pathlib import Path

def check_tables_in_md(file_path: Path):
    lines = file_path.read_text(encoding="utf-8").splitlines()
    in_table = False
    header_cols = None
    table_start_line = 0
    mismatches = []
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                in_table = True
                header_cols = len(cells)
                table_start_line = i
            else:
                if len(cells) != header_cols:
                    mismatches.append((i, len(cells), header_cols, line))
        else:
            in_table = False
            header_cols = None
            
    return mismatches

for md in (Path("reports/stage6m")).glob("*.md"):
    m = check_tables_in_md(md)
    if m:
        print(f"FAILED: {md.name} has {len(m)} table column mismatches:")
        for line_no, got, exp, line in m:
            print(f"  Line {line_no}: got {got} cols, expected {exp}: {line[:60]}")
    else:
        print(f"PASSED: {md.name} table columns 100% consistent.")
