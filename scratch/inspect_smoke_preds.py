import json
from pathlib import Path

p = Path("results/stage5m/checkpoints/STAGE5M_wav2vec2_base_clean_no_adapt_order_a_k4.json")
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

preds = d.get("predictions", [])
print(f"Total prediction records in checkpoint: {len(preds)}")
for i, pred in enumerate(preds):
    print(f"[{i}] id={pred.get('utterance_id')} spk={pred.get('speaker_id')} accent={pred.get('accent')} ref_words={pred.get('word_count')} errors={pred.get('word_errors')} hyp='{pred.get('hypothesis')}'")

words = sum(p.get('word_count', 0) for p in preds)
errs = sum(p.get('word_errors', 0) for p in preds)
print(f"\nTotal Words: {words}")
print(f"Total Errors: {errs}")
print(f"WER: {errs/words*100:.2f}% (63/74 = {63/74*100:.4f}%)")
