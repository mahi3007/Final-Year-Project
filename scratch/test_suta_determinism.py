import torch
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.online.stream import PrequentialStream
from dsg_ctta.models.registry import create_asr_model
from dsg_ctta.adaptation.suta import SutaAdapter

utts = load_partition_from_csv("datasets/splits/final_test.csv")
stream = PrequentialStream(utterances=utts, window_size_k=4, ordering_id="ORDER_A", seed=42)
gen = stream.generate_windows()
batch_idx, batch_utts, unlabeled_batch = next(gen)

print(f"Batch {batch_idx}: {[u.utterance_id for u in batch_utts]}")

for run_i in range(3):
    m = create_asr_model("wav2vec2_base", device="cpu")
    m.load_model()
    adapter = SutaAdapter(asr_model=m, config={"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1})
    res = adapter.adapt(unlabeled_batch)
    print(f"Run {run_i} (sequential execution): after_hash = {res.theta_after_hash}")
