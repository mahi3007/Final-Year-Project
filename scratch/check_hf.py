from huggingface_hub import HfApi

api = HfApi()

print("--- Searching for common_voice on Hugging Face ---")
try:
    results = list(api.list_datasets(search="common_voice", limit=30))
    for r in results:
        if "11" in r.id:
            print("Match 11:", r.id, "downloads:", r.downloads)
except Exception as e:
    print("Error:", e)

print("\n--- Checking mozilla-foundation datasets ---")
try:
    results = list(api.list_datasets(author="mozilla-foundation", limit=50))
    for r in results:
        print("MF:", r.id)
except Exception as e:
    print("Error:", e)
