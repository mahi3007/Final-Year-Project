import json

log_file = r'C:/Users/venka/.gemini/antigravity-ide/brain/2eca9caf-ca8e-4172-b145-bf1506190850/.system_generated/logs/transcript_full.jsonl'
targets = {4122, 4125, 4135, 4143, 4153, 4161, 4169, 4171, 4237}
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        for idx in targets:
            if f'"step_index":{idx}' in line:
                try:
                    obj = json.loads(line)
                    print(f"=== Step {idx} ===")
                    print(obj.get('content', '')[:300])
                except Exception:
                    pass
