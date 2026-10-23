import json

path = r"C:\Users\venka\.gemini\antigravity-ide\brain\2eca9caf-ca8e-4172-b145-bf1506190850\.system_generated\logs\transcript_full.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        if '"step_index":18346' in line:
            data = json.loads(line)
            content = data.get("content")
            print(f"Total length of step 18346 content: {len(content)}")
            with open("reports/stage6m/user_review_step18346.txt", "w", encoding="utf-8") as out:
                out.write(content)
            print("Written to reports/stage6m/user_review_step18346.txt")
            break
