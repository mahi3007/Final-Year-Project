import time
import torch
import pandas as pd
from pathlib import Path
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.data.acoustic import load_and_resample_audio

audio_dir = Path("datasets/external/common_voice_27/audio")
sentinel_df = pd.read_csv("datasets/splits/stage5_sentinel_panel.csv")
print(f"Loaded sentinel panel: {len(sentinel_df)} clips")

# Preload audio waveforms
t0 = time.time()
waveforms = []
for _, row in sentinel_df.iterrows():
    p = audio_dir / row["audio_path"]
    w, _ = load_and_resample_audio(str(p), 16000)
    waveforms.append(w)
print(f"Preloaded 300 audio files in {time.time()-t0:.2f}s")

# Load model
model = create_asr_model("wav2vec2_base", device="cpu")
model.load_model()

# Benchmark single vs batched transcription
t1 = time.time()
with torch.no_grad():
    inputs = model.processor(waveforms[:16], sampling_rate=16000, return_tensors="pt", padding=True)
    input_values = inputs.input_values.to("cpu")
    logits = model.model(input_values).logits
    pred_ids = torch.argmax(logits, dim=-1)
    trans = model.processor.batch_decode(pred_ids)
elapsed_batch = time.time() - t1
print(f"Batched 16 clips in {elapsed_batch:.2f}s ({elapsed_batch/16:.3f}s/clip)")
