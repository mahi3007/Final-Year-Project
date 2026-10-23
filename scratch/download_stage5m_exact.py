import os
import requests
import zipfile
from kaggle import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

api = KaggleApi()
api.authenticate()

owner_slug = "venkataakhil07"
kernel_slug = "notebook840244cb83"

target_files = {}

page = 1
next_token = None

print("Querying Kaggle pages for exact Stage 5M targets...")
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
            # We want:
            # 1. Any zip bundles
            # 2. Anything in results/stage5m/
            # 3. Anything in reports/stage5m/
            if fname in ["stage5m_results_bundle.zip", "stage5_stage6_results_bundle.zip"]:
                target_files[fname] = item.url
            elif "results/stage5m" in fname or "reports/stage5m" in fname:
                target_files[fname] = item.url

        next_token = res.next_page_token
        if not next_token:
            break
        page += 1

print(f"Total target Stage 5M files found: {len(target_files)}")

# Download each file
for fname, url in target_files.items():
    if fname.startswith("project/"):
        rel_dest = fname[len("project/"):]
    else:
        rel_dest = fname
    
    # Save to local workspace or scratch
    if rel_dest.endswith(".zip"):
        local_path = os.path.join("scratch", rel_dest)
    else:
        local_path = rel_dest
        
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print(f"Downloading {fname} -> {local_path} ...", end="", flush=True)
    r = requests.get(url)
    with open(local_path, "wb") as f:
        f.write(r.content)
    print(f" Done ({len(r.content)/1024:.1f} KB)")

# If stage5m_results_bundle.zip exists in scratch, extract it
zip_path = os.path.join("scratch", "stage5m_results_bundle.zip")
if os.path.exists(zip_path):
    print(f"\nExtracting {zip_path} into workspace...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall("scratch/extracted_stage5m_bundle")
    print("Extracted archive successfully.")

print("\nStage 5M download and sync complete!")
