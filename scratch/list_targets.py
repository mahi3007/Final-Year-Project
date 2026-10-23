from kaggle import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

api = KaggleApi()
api.authenticate()

owner_slug = "venkataakhil07"
kernel_slug = "notebook840244cb83"

stage5m_items = []
results_items = []
reports_items = []
zip_items = []

page = 1
next_token = None

with api.build_kaggle_client() as client:
    while True:
        req = ApiListKernelSessionOutputRequest()
        req.user_name = owner_slug
        req.kernel_slug = kernel_slug
        if next_token:
            req.page_token = next_token
        res = client.kernels.kernels_api_client.list_kernel_session_output(req)
        for item in res.files:
            fname = item.file_name
            if "stage5m" in fname.lower() or "checkpoint" in fname.lower():
                stage5m_items.append((fname, item.url))
            if "results" in fname.lower() and (fname.endswith(".csv") or fname.endswith(".json")):
                results_items.append((fname, item.url))
            if "reports" in fname.lower():
                reports_items.append((fname, item.url))
            if fname.endswith(".zip"):
                zip_items.append((fname, item.url))
        next_token = res.next_page_token
        if not next_token:
            break
        page += 1

print(f"Total Stage 5M / Checkpoint items: {len(stage5m_items)}")
print(f"Total Results items: {len(results_items)}")
print(f"Total Reports items: {len(reports_items)}")
print(f"Total Zip items: {len(zip_items)}")

print("\n--- Zip files ---")
for f, u in zip_items:
    print(" ", f)

print("\n--- First 20 Stage 5M / Checkpoint items ---")
for f, u in stage5m_items[:20]:
    print(" ", f)

print("\n--- Last 20 Stage 5M / Checkpoint items ---")
for f, u in stage5m_items[-20:]:
    print(" ", f)
