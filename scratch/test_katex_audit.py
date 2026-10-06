import re
from pathlib import Path
import subprocess
import json

def check_file(path_str):
    path = Path(path_str)
    print(f"\n=======================================================")
    print(f"Checking {path}...")
    print(f"=======================================================")
    text = path.read_text(encoding='utf-8')
    
    # Extract blocks ($$ ... $$)
    blocks = re.findall(r'\$\$(.*?)\$\$', text, re.DOTALL)
    # Extract inlines ($ ... $)
    no_blocks = re.sub(r'\$\$.*?\$\$', '', text, flags=re.DOTALL)
    inlines = re.findall(r'\$([^\$\n]+)\$', no_blocks)
    
    print(f"Found {len(blocks)} display equations and {len(inlines)} inline equations.")
    
    data = {'blocks': [b.strip() for b in blocks], 'inlines': [i.strip() for i in inlines]}
    json_path = Path("scratch/test_math.json")
    json_path.write_text(json.dumps(data), encoding='utf-8')
    
    node_script = """
    const katex = require('C:/Users/venka/AppData/Local/npm-cache/_npx/8c2cfac42696c54b/node_modules/katex');
    const fs = require('fs');
    const data = JSON.parse(fs.readFileSync('scratch/test_math.json', 'utf8'));
    
    let blockErrors = 0;
    data.blocks.forEach((eq, idx) => {
        try {
            katex.renderToString(eq, {displayMode: true, throwOnError: true});
        } catch(e) {
            console.log(`[Block #${idx}] ERROR: ${e.message}`);
            console.log(`   Eq: ${eq}`);
            blockErrors++;
        }
    });
    
    let inlineErrors = 0;
    data.inlines.forEach((eq, idx) => {
        try {
            katex.renderToString(eq, {displayMode: false, throwOnError: true});
        } catch(e) {
            console.log(`[Inline #${idx}] ERROR: ${e.message}`);
            console.log(`   Eq: ${eq}`);
            inlineErrors++;
        }
    });
    console.log(`Summary: Blocks=${data.blocks.length} (Errors: ${blockErrors}), Inlines=${data.inlines.length} (Errors: ${inlineErrors})`);
    """
    
    res = subprocess.run(['node', '-e', node_script], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

if __name__ == '__main__':
    check_file('reports/project_report/formula_reference.md')
    check_file('reports/project_report/master_research_report.md')
