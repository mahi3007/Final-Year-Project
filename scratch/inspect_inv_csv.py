import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/venka\Downloads/final year project main")
INV_CSV = PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv"

df_inv = pd.read_csv(INV_CSV)
print("Frozen external_speaker_inventory.csv counts:")
print(df_inv["group_code"].value_counts())
print("Total:", len(df_inv))

# Check columns in df_inv
print("\nColumns:", df_inv.columns.tolist())
print(df_inv.head(5))
