import torch
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.online.stream import PrequentialStream
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.adaptation.dmsuta import DmsutaAdapter
from dsg_ctta.offline.metrics import compute_utterance_metrics

utts = load_partition_from_csv("datasets/splits/final_test.csv")
stream = PrequentialStream(utterances=utts, window_size_k=4, ordering_id="ORDER_C", seed=42)
gen = stream.generate_windows()

# Window 0
w0_idx, w0_utts, w0_unlabeled = next(gen)

asr = create_asr_model("wav2vec2_100h", device="cpu")
asr.load_model()
adapter = DmsutaAdapter(asr_model=asr, config={"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3})

print("Transcribing Window 0:")
for u in w0_utts:
    h = asr.transcribe(u.audio_filepath)
    print(f"  {u.utterance_id}: '{h}'")

print(f"\nModel hash before W0 adapt: {adapter.compute_model_hash()}")
res = adapter.adapt(w0_unlabeled)
print(f"Model hash after W0 adapt:  {adapter.compute_model_hash()} (expected 1eb574dc9b29d31f)")

# Window 1
w1_idx, w1_utts, w1_unlabeled = next(gen)
print("\nTranscribing Window 1 with adapted model:")
for u in w1_utts:
    h = asr.transcribe(u.audio_filepath)
    print(f"  {u.utterance_id}: '{h}'")
