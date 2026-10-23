import json
from pathlib import Path

names = [
    'STAGE5M_wav2vec2_base_clean_no_adapt_order_a_k4.json',
    'STAGE5M_wav2vec2_base_clean_suta_order_a_k4.json',
    'STAGE5M_wav2vec2_base_clean_suta_order_b_k4.json',
    'STAGE5M_data2vec_base_clean_no_adapt_order_a_k4.json',
    'STAGE5M_wav2vec2_100h_clean_no_adapt_order_a_k4.json',
    'STAGE5M_wav2vec2_base_noise_15db_no_adapt_order_a_k4.json'
]

for name in names:
    p = Path('results/stage5m/checkpoints') / name
    if p.exists():
        with open(p, 'r') as f:
            d = json.load(f)
        s = d.get('summary', {})
        preds = d.get('predictions', [])
        ops = d.get('operational_decisions', [])
        print(f"=== {name} ===")
        print(f"  summary: WER={s.get('final_wer')}, D={s.get('final_disparity')}, words={s.get('total_words')}, errors={s.get('total_errors')}, elapsed={s.get('elapsed_seconds')}")
        print(f"  total candidates: {s.get('total_candidates')}, accepted: {s.get('accepted_candidates')}")
        print(f"  predictions count: {len(preds)}")
        print(f"  operational decisions count: {len(ops)}")
        print(f"  group_wers: {s.get('group_wers')}")
