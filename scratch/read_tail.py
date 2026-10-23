import json

with open(r'C:\Users\venka\.gemini\antigravity-ide\brain\2eca9caf-ca8e-4172-b145-bf1506190850\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            idx = data.get('step_index', 0)
            if idx in [13180, 13181, 13182, 13183, 13184, 13185, 13186, 13187]:
                print(f"=== STEP {idx} ===")
                print("CONTENT:", data.get('content'))
                print("TOOL CALLS:", data.get('tool_calls'))
        except Exception as e:
            pass
