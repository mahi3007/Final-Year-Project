from pathlib import Path

doc = Path("reports/stage6m/stage6m_data_feasibility_audit.md").read_text(encoding="utf-8")
gen_path = Path("scratch/generate_feasibility_report.py")

# Create a clean python file where content is the exact doc string
# We need to escape triple double quotes if any exist (none exist in doc)
escaped_doc = doc.replace('"""', r'\"\"\"')
code = f'content = """{escaped_doc}"""\n\nif __name__ == "__main__":\n    out = Path("reports/stage6m/stage6m_data_feasibility_audit.md")\n    out.write_text(content, encoding="utf-8")\n    print("Wrote stage6m_data_feasibility_audit.md successfully.")\n'

gen_path.write_text(code, encoding="utf-8")
print("Synchronized scratch/generate_feasibility_report.py with stage6m_data_feasibility_audit.md.")
