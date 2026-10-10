import sys
import torch
import numpy as np
import random
from pathlib import Path

# Let's inspect the exact environment, torch version, transformers version
print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
import transformers
print(f"Transformers version: {transformers.__version__}")

# Check if model checkpoints are identical
from dsg_ctta.models.registry import MODEL_CATALOG, create_asr_model
m_info = MODEL_CATALOG["wav2vec2_base"]
print(f"Model ID: {m_info['model_id']}")

model = create_asr_model("wav2vec2_base", device="cpu")
model.load_model()
init_hash = model.get_parameter_hash()
print(f"Loaded wav2vec2_base initial parameter hash: {init_hash}")

# Check historical hash on Window 0 before
# In reports/ctta/suta/window_metrics.csv: theta_before_hash is e28c2c6b4f74d0e2
# In results/stage3_multimodel/wav2vec2_base_suta_order_a/window_metrics.csv: theta_before_hash is e28c2c6b4f74d0e2
print(f"Matches historical Window 0 before hash: {init_hash == 'e28c2c6b4f74d0e2'}")
