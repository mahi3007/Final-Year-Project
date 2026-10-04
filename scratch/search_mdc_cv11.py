import os
import datacollective
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("MDC_API_KEY")
print(f"MDC_API_KEY configured: {bool(api_key)}")

# Search queries to test
queries = [
    "cv-corpus-11",
    "cv-corpus-11.0",
    "11.0",
    "2022-09-21",
    "Common Voice 11",
    "Common Voice Scripted Speech 11",
    "archive",
]

print("\n=== Search Results across MDC API for CV11 References ===")
for q in queries:
    try:
        res = datacollective.list_datasets(query=q, results_per_page=20)
        items = res.items
        print(f"\nQuery '{q}': found {res.total} total items")
        for d in items:
            print(f"  - [{d.id}] '{d.name}' | Slug: {d.slug} | Created: {d.createdAt}")
    except Exception as e:
        print(f"Query '{q}' error: {e}")

print("\n=== Listing all datasets from Organization 'Common Voice' ===")
try:
    # Common Voice org slug from details earlier was 'test-2d27eebd' or 'cmfh0j9o10006ns07jq45h7xk'
    # Let's list all datasets with task='ASR' and locale='en' across multiple pages
    all_en_asr = []
    page = 1
    while True:
        res = datacollective.list_datasets(locale="en", task="ASR", results_per_page=50, page_number=page)
        all_en_asr.extend(res.items)
        if len(all_en_asr) >= res.total or not res.items:
            break
        page += 1

    print(f"Total English ASR datasets on MDC: {len(all_en_asr)}")
    cv_datasets = [d for d in all_en_asr if "common voice" in d.name.lower()]
    print(f"Of which Common Voice English datasets: {len(cv_datasets)}")
    for d in cv_datasets:
        print(f"  - [{d.id}] '{d.name}' | Slug: {d.slug} | Filename: {d.filename}")
except Exception as e:
    print(f"Org listing error: {e}")
