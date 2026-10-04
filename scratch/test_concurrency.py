import time
import torch
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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

records = df.head(32).to_dict(orient="records")
waveforms = []
for r in records:
    p = resolver.resolve(r)
    w, _ = load_and_resample_audio(str(p), 16000)
    waveforms.append(w)

processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
model.eval()

# Test with torch.inference_mode()
t0 = time.time()
with torch.inference_mode():
    for w in waveforms:
        inputs = processor(w, sampling_rate=16000, return_tensors="pt")
        logits = model(inputs.input_values).logits
        pred_ids = torch.argmax(logits, dim=-1)
        _ = processor.batch_decode(pred_ids)[0].strip()
t_inf = time.time() - t0
print(f"torch.inference_mode(): {t_inf:.2f}s ({t_inf/32:.3f}s/clip -> 300 clips = {t_inf/32*300:.1f}s)")

# Test with thread pool (2 threads)
def transcribe_one(w):
    with torch.inference_mode():
        inputs = processor(w, sampling_rate=16000, return_tensors="pt")
        logits = model(inputs.input_values).logits
        pred_ids = torch.argmax(logits, dim=-1)
        return processor.batch_decode(pred_ids)[0].strip()

t0 = time.time()
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(transcribe_one, waveforms))
t_pool = time.time() - t0
print(f"ThreadPool (2 workers): {t_pool:.2f}s ({t_pool/32:.3f}s/clip -> 300 clips = {t_pool/32*300:.1f}s)")
