import os
import requests
from kaggle import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

api = KaggleApi()
api.authenticate()

owner_slug = "venkataakhil07"
kernel_slug = "notebook840244cb83"

print("Contacting Kaggle API...")
with api.build_kaggle_client() as client:
    req = ApiListKernelSessionOutputRequest()
    req.user_name = owner_slug
    req.kernel_slug = kernel_slug
    res = client.kernels.kernels_api_client.list_kernel_session_output(req)

print(f"Log received? {'Yes' if res.log else 'No'} (length: {len(res.log) if res.log else 0})")
if res.log:
    with open("scratch/kaggle_kernel_session.log", "w", encoding="utf-8") as f:
        f.write(res.log)
    print("Saved scratch/kaggle_kernel_session.log")

print(f"Total files in output: {len(res.files)}")

# Filter and print all non-wav and non-pack files
dest_dir = "scratch/selective_download"
os.makedirs(dest_dir, exist_ok=True)

downloaded_count = 0
for item in res.files:
    fname = item.file_name
    # We want results, reports, checkpoints, logs, csv, json, md, txt, zip
    if (fname.endswith(".csv") or fname.endswith(".json") or fname.endswith(".md") 
        or fname.endswith(".zip") or fname.endswith(".txt") or fname.endswith(".log")
        or "stage5" in fname or "checkpoint" in fname):
        
        target_path = os.path.join(dest_dir, fname)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        print(f"Downloading: {fname} ...", end="", flush=True)
        r = requests.get(item.url)
        with open(target_path, "wb") as f:
            f.write(r.content)
        print(f" Done ({len(r.content)/1024:.1f} KB)")
        downloaded_count += 1

print(f"\nFinished selective download: {downloaded_count} research files saved to {dest_dir}.")
