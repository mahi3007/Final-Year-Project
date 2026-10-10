import itertools
import numpy as np
import pandas as pd
import patsy

ctc_models = ["wav2vec2_base", "data2vec_base", "wav2vec2_100h"]
methods = ["no_adapt", "suta", "dsuta", "dmsuta"]
orders = ["ORDER_A", "ORDER_B", "ORDER_C"]
conditions = ["clean", "noise_15db", "noise_5db", "babble_15db", "reverb_t60_04"]

grid = list(itertools.product(ctc_models, methods, orders, conditions))
df = pd.DataFrame(grid, columns=["model", "method", "ordering", "condition"])
df["errors"] = 1

formula = (
    "errors ~ C(model, Treatment('wav2vec2_base')) + "
    "C(method, Treatment('no_adapt')) + "
    "C(condition, Treatment('clean')) + "
    "C(ordering, Treatment('ORDER_A')) + "
    "C(model, Treatment('wav2vec2_base')):C(method, Treatment('no_adapt')) + "
    "C(method, Treatment('no_adapt')):C(condition, Treatment('clean')) + "
    "C(method, Treatment('no_adapt')):C(ordering, Treatment('ORDER_A'))"
)

y, X = patsy.dmatrices(formula, data=df, return_type="dataframe")
print("Factorial grid settings:", len(df))
print("Design matrix shape:", X.shape)
print("Design matrix rank:", np.linalg.matrix_rank(X.values))
print("\nColumns (p = {}):".format(len(X.columns)))
for i, col in enumerate(X.columns):
    print(f"  {i+1:2d}. {col}")
