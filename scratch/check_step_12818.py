import json

with open(r'C:\Users\venka\.gemini\antigravity-ide\brain\2eca9caf-ca8e-4172-b145-bf1506190850\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            idx = data.get('step_index', 0)
            if 12810 <= idx <= 12822:
                print(f"Step {idx} [{data.get('source')} - {data.get('type')}]:")
                print(data.get('content'))
                print("---")
        except:
            pass
