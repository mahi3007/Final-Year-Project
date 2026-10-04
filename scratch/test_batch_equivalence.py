import time
import torch
import pandas as pd
from pathlib import Path
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.data.acoustic import load_and_resample_audio

audio_dir = Path("datasets/external/common_voice_27/audio")
eval_df = pd.read_csv("datasets/splits/stage5_external_eval.csv")

# Test first 4 clips
test_rows = eval_df.iloc[:4]
waveforms = []
for _, r in test_rows.iterrows():
    p = str(audio_dir / f"{r['recording_id']}.mp3")
    w, _ = load_and_resample_audio(p, 16000)
    waveforms.append(w)

model = create_asr_model("wav2vec2_base", device="cpu")
model.load_model()

# Sequential transcription
t0 = time.time()
seq_hyps = []
for w in waveforms:
    inputs = model.processor(w, sampling_rate=16000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model.model(inputs.input_values).logits
    pred_ids = torch.argmax(logits, dim=-1)
    seq_hyps.append(model.processor.batch_decode(pred_ids)[0].strip())
t_seq = time.time() - t0

# Batched transcription
t1 = time.time()
inputs_batch = model.processor(waveforms, sampling_rate=16000, return_tensors="pt", padding=True)
with torch.no_grad():
    logits_batch = model.model(inputs_batch.input_values).logits
pred_ids_batch = torch.argmax(logits_batch, dim=-1)
batch_hyps = [h.strip() for h in model.processor.batch_decode(pred_ids_batch)]
t_batch = time.time() - t1

print(f"Sequential time: {t_seq:.3f}s")
print(f"Batched time:    {t_batch:.3f}s (Speedup: {t_seq/t_batch:.2f}x)")
print(f"Exact match:     {seq_hyps == batch_hyps}")
for i, (s, b) in enumerate(zip(seq_hyps, batch_hyps)):
    print(f"Clip {i}: match={s==b}")
    if s != b:
        print(f"  Seq:   {s}")
        print(f"  Batch: {b}")
