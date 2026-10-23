import os
import requests
from kaggle.api.kaggle_api_extended import KaggleApi
from kaggle.models.api_list_kernel_session_output_request import ApiListKernelSessionOutputRequest

api = KaggleApi()
api.authenticate()

owner_slug = "venkataakhil07"
kernel_slug = "notebook840244cb83"

with api.build_kaggle_client() as kaggle:
    req = ApiListKernelSessionOutputRequest()
    req.user_name = owner_slug
    req.kernel_slug = kernel_slug
    res = kaggle.kernels.kernels_api_client.list_kernel_session_output(req)

print(f"Log length: {len(res.log) if res.log else 0}")
if res.log:
    print("=== LOG HEAD ===")
    print(res.log[:500])
    print("=== LOG TAIL ===")
    print(res.log[-2000:])

print(f"\nTotal files available: {len(res.files)}")
print("\nFiles list (filtered non-wav, non-pack):")
for item in res.files:
    fname = item.file_name
    if not fname.endswith(".wav") and not fname.endswith(".pack"):
        print(f"  {fname}")
