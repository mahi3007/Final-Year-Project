import os
import requests
from kaggle import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

api = KaggleApi()
api.authenticate()

owner_slug = "venkataakhil07"
kernel_slug = "notebook840244cb83"

dest_dir = "scratch/all_kaggle_research_outputs"
os.makedirs(dest_dir, exist_ok=True)

all_research_files = []
page = 1
next_token = None

print("Fetching all output file pages from Kaggle...")
with api.build_kaggle_client() as client:
    while True:
        req = ApiListKernelSessionOutputRequest()
        req.user_name = owner_slug
        req.kernel_slug = kernel_slug
        if next_token:
            req.page_token = next_token
            
        res = client.kernels.kernels_api_client.list_kernel_session_output(req)
        print(f"Page {page}: received {len(res.files)} files.")
        
        for item in res.files:
            fname = item.file_name
            # Exclude audio and git objects
            if not fname.endswith(".wav") and not fname.endswith(".mp3") and not "/.git/" in fname and not fname.endswith(".pack"):
                all_research_files.append((fname, item.url))
                
        next_token = res.next_page_token
        if not next_token:
            break
        page += 1

print(f"\nTotal research files found across all pages: {len(all_research_files)}")

# Download each file
for i, (fname, url) in enumerate(all_research_files, 1):
    target_path = os.path.join(dest_dir, fname)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    print(f"[{i}/{len(all_research_files)}] Downloading {fname} ...", end="", flush=True)
    r = requests.get(url)
    with open(target_path, "wb") as f:
        f.write(r.content)
    print(f" Done ({len(r.content)/1024:.1f} KB)")

print("\nAll research artifacts successfully downloaded!")
