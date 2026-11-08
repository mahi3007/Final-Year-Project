# Stage 6M: Private Kaggle Dataset Preparation Checklist

**Document ID:** `STAGE6M-KAGGLE-DATASET-CHECKLIST-20261107`  
**Governing Protocol:** Stage 6M v1.5 Five-Stratum Research Benchmark (Section 14.7)  
**Governing Branch:** `stage6m-five-stratum-parity` @ `baee3b8381389ffde38e907dc137623748c254a8`  
**Dataset Target:** Private Kaggle Dataset (`stage6m-frozen-benchmark`)  

---

## 1. Overview & Privacy Requirements

To execute the Stage 6M confirmatory benchmark on Kaggle's virtual GPUs, the frozen research benchmark must be uploaded as a **Private Kaggle Dataset**.

> [!CAUTION]
> **Strict Privacy Obligation:** The dataset MUST be created with visibility set to **Private**. Do NOT create a public dataset, as this would breach the blind evaluation shielding of the confirmatory cohort.

---

## 2. Dataset Payload Checklist

The private Kaggle dataset package consists of the following validated components:

| Item | Source Path in Workspace | Target Path in Kaggle Dataset | Size | Verification Rule |
| :---: | :--- | :--- | :---: | :--- |
| **1A** | `datasets/splits/stage6m_cohort3_online_inference_manifest.json` | `splits/stage6m_cohort3_online_inference_manifest.json` | 27.73 MB | **Primary Online Manifest:** SHA-256 == `0f1cca979a0b7c9872ce576df97a3db48c84358db3b4f287aa77d76a779751a1` (Evaluation labels shielded) |
| **1B** | `datasets/splits/stage6m_cohort3_sealed_evaluation_transcripts.json` | **EXCLUDED FROM PAYLOAD** | N/A | **Offline Scoring Key:** Reserved exclusively for offline Gate 6 scoring. **MUST NOT BE MOUNTED IN KAGGLE.** |
| **1C** | `datasets/splits/stage6m_cohort3_final_manifest.json` | `splits/stage6m_cohort3_final_manifest.json` | 26.68 MB | **Parent Locked Manifest:** SHA-256 == `171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0` |
| **2** | `datasets/splits/stage6m_cohort3_materialization_disposition_ledger.csv` | `splits/stage6m_cohort3_materialization_disposition_ledger.csv` | 8.64 MB | SHA-256 == `b242282ef1586219885f475fba0d1de117e7b68289ca9a42e36378cac638a0c5` |
| **3** | `dist/kaggle_dataset/audio/cohort3_reconciled_assets/` | `audio/cohort3_reconciled_assets/` | 672.97 MB | **Positive Runtime Allowlist:** Exactly 18,000 MP3 files (16,500 evaluation + 1,500 gate-reference). 0 reserve recordings. |
| **4** | `configs/*.json` | `configs/` | ~30 KB | All 5 protocol configurations |
| **5** | `src/dsg_ctta/` | `src/dsg_ctta/` | ~350 KB | Frozen inference engine source code |
| **6** | `requirements-kaggle-lock.txt` | `requirements-kaggle-lock.txt` | < 1 KB | Exact Python dependency freeze specification |
| **7** | `reports/stage6m/stage6m_kaggle_artifact_hash_verification.json` | `SHA256_CATALOGUE.json` | ~4 KB | Cryptographic verification catalogue |
| **8** | `reports/stage6m/stage6m_transcript_isolation_audit.md` | `TRANSCRIPT_ISOLATION_AUDIT.md` | ~5 KB | Audit report proving zero label leakage |

---

## 3. Preparation Instructions (Local Machine)

### Option A: Using Kaggle CLI (Recommended for Automation)
1. Ensure the Kaggle CLI is authenticated:
   ```bash
   kaggle datasets init -p dist/kaggle_dataset
   ```
2. Run the packaging tool:
   ```bash
   python scripts/package_stage6m_kaggle_benchmark.py
   ```
3. Push to Kaggle as a private dataset:
   ```bash
   kaggle datasets create -p dist/kaggle_dataset -r zip
   ```

### Option B: Web UI Drag-and-Drop
1. Navigate to [https://www.kaggle.com/datasets](https://www.kaggle.com/datasets).
2. Click **"+ New Dataset"** in the top-right corner.
3. Enter Title: `stage6m-frozen-benchmark` (URL slug: `stage6m-frozen-benchmark`).
4. Select **Private** under privacy settings.
5. Create a ZIP archive of `datasets/splits/`, `datasets/audio/stage6m/cohort3_reconciled_assets/`, `configs/`, and `src/`.
6. Drag and drop the archive into the upload modal.
7. Click **"Create"**.

---

## 4. Post-Upload Verification in Kaggle Notebook

Once the private dataset is attached to your Kaggle Notebook (it mounts at `/kaggle/input/stage6m-frozen-benchmark/`), run the following verification cell to guarantee byte-exact replication before running Gate 4 smoke tests:

```python
import hashlib, json
from pathlib import Path

manifest_path = Path("/kaggle/input/stage6m-frozen-benchmark/splits/stage6m_cohort3_final_manifest.json")
if not manifest_path.exists():
    manifest_path = Path("/kaggle/input/stage6m-frozen-benchmark/stage6m_cohort3_final_manifest.json")

h = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
expected = "171815faab962073b7d446bc6d755602c948386f62437876b5fe54fb82b4f3d0"
print(f"Manifest SHA-256: {h}")
assert h == expected, f"Manifest digest mismatch! Found {h}"
print("VERIFICATION SUCCESSFUL: Frozen benchmark mounted byte-identically.")
```
