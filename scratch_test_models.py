import gc
import time
from dsg_ctta.models.registry import create_asr_model

models = ['wav2vec2_base', 'whisper_base', 'data2vec_base', 'distil_whisper_small', 'whisper_tiny', 'wav2vec2_100h']
wav_path = 'datasets/primary/audio/ABA_arctic_a0001.wav'

for name in models:
    t0 = time.time()
    m = create_asr_model(name, device='cpu')
    m.load_model()
    t_load = time.time() - t0
    t0 = time.time()
    hyp = m.transcribe(wav_path)
    t_inf = time.time() - t0
    print(f'SUCCESS [{name}]: load={t_load:.2f}s, inf={t_inf:.2f}s, hyp="{hyp}"')
    del m
    gc.collect()
