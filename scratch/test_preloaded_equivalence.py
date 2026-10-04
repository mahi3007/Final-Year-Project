import pandas as pd
from pathlib import Path
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.data.acoustic import load_and_resample_audio

audio_dir = Path('datasets/external/common_voice_27/audio')
eval_df = pd.read_csv('datasets/splits/stage5_external_eval.csv')

model = create_asr_model('wav2vec2_base', device='cpu')
model.load_model()

matches = []
for _, r in eval_df.iloc[:5].iterrows():
    p = str(audio_dir / f"{r['recording_id']}.mp3")
    w, _ = load_and_resample_audio(p, 16000)
    hyp_path = model.transcribe(p)
    hyp_arr = model.transcribe(w)
    matches.append(hyp_path == hyp_arr)
    print(r['recording_id'], hyp_path == hyp_arr, f'"{hyp_path}"')
print('All match:', all(matches))
