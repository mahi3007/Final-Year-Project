import json

with open('datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('Type:', type(d).__name__)
if isinstance(d, dict):
    print('Top-level keys:', list(d.keys()))
    if 'records' in d:
        print(f"records count: {len(d['records'])}")
        print("Record keys:", list(d['records'][0].keys()))
elif isinstance(d, list):
    print(f"List length: {len(d)}")
    print("Element keys:", list(d[0].keys()))
