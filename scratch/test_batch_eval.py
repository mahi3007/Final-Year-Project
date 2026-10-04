import time
import torch
import numpy as np
from pathlib import Path
import pandas as pd
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from dsg_ctta.controller.resolver import SentinelAudioResolver
from dsg_ctta.data.acoustic import load_and_resample_audio

PROJECT_ROOT = Path(".").resolve()
SENTINEL_CSV = PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv"
SENTINEL_INVENTORY = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "sentinel_audio_inventory.json"

resolver = SentinelAudioResolver(inventory_path=SENTINEL_INVENTORY, project_root=PROJECT_ROOT)
df = pd.read_csv(SENTINEL_CSV)

print("Loading 32 sample waveforms...")
records = df.head(32).to_dict(orient="records")
waveforms = []
for r in records:
    p = resolver.resolve(r)
    w, _ = load_and_resample_audio(str(p), 16000)
    waveforms.append(w)

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
model.eval()

# Benchmark 1: Sequential batch_size = 1
t0 = time.time()
for w in waveforms:
    inputs = processor(w, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    pred_ids = torch.argmax(logits, dim=-1)
    _ = processor.batch_decode(pred_ids)[0].strip()
t_seq = time.time() - t0
print(f"Sequential 32 clips: {t_seq:.2f}s ({t_seq/32:.3f}s/clip -> 300 clips = {t_seq/32*300:.1f}s)")

# Benchmark 2: Batched batch_size = 16
t0 = time.time()
for b_start in range(0, 32, 16):
    b_waves = waveforms[b_start:b_start+16]
    inputs = processor(b_waves, sampling_rate=16000, return_tensors="pt", padding=True, return_attention_mask=True)
    with torch.no_grad():
        logits = model(inputs.input_values, attention_mask=inputs.attention_mask).logits
    pred_ids = torch.argmax(logits, dim=-1)
    _ = processor.batch_decode(pred_ids)
t_batch = time.time() - t0
print(f"Batched (size 16) 32 clips: {t_batch:.2f}s ({t_batch/32:.3f}s/clip -> 300 clips = {t_batch/32*300:.1f}s)")
