import json

path = r'C:\Users\venka\.gemini\antigravity-ide\brain\2eca9caf-ca8e-4172-b145-bf1506190850\.system_generated\logs\transcript.jsonl'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '"step_index":6254' in line or '"step_index":6550' in line:
            obj = json.loads(line)
            print(f"=== Step {obj.get('step_index')} ===")
            print(obj.get('content'))
