import json

with open(r'C:\Users\venka\.gemini\antigravity-ide\brain\2eca9caf-ca8e-4172-b145-bf1506190850\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('source') == 'USER_EXPLICIT' or data.get('type') == 'USER_INPUT':
                print(f"Step {data.get('step_index')}: {data.get('content')}")
        except:
            pass
