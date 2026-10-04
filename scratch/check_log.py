import json

log_file = r'C:/Users/venka/.gemini/antigravity-ide/brain/2eca9caf-ca8e-4172-b145-bf1506190850/.system_generated/logs/transcript_full.jsonl'
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '"step_index":4238' in line:
            obj = json.loads(line)
            print(obj.get('content'))
