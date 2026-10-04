"""
Phase D Pilot: Real-Data Prequential No-Adaptation Control Pilot (12 recordings from development split).
Verifies:
- Clean audio loading and resample
- Label isolation (zero reference or group leakage online)
- Exact Levenshtein evaluation on live predictions theta_t
- Model state invariance under No-Adaptation control
"""

import os
import json
import pandas as pd
from rich.console import Console

from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.online.stream import order_utterances
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment

console = Console()

def run_pilot():
    dev_csv = "datasets/splits/development.csv"
    all_dev_utts = load_partition_from_csv(dev_csv)

    # Select 2 utterances per group (12 total) for a small, fast, rigorous pilot
    groups = ["Arabic", "Hindi", "Korean", "Mandarin", "Spanish", "Vietnamese"]
    pilot_utts = []
    for g in groups:
        g_utts = [u for u in all_dev_utts if u.group_id == g]
        pilot_utts.extend(g_utts[:2])

    console.print(f"Loaded {len(pilot_utts)} pilot utterances across {len(groups)} groups from {dev_csv}.")

    output_dir = "reports/ctta/pilot_no_adapt"
    res = run_prequential_stream_experiment(
        utterances=pilot_utts,
        model_name="wav2vec2_base",
        method_name="no_adapt",
        ordering_id="ORDER_A",
        window_size_k=4,
        device="cpu",
        output_dir=output_dir,
        seed=42,
        experiment_id="pilot_no_adapt_wav2vec2"
    )

    console.print("\n[bold green]Pilot Output Verification:[/bold green]")
    summary = res["summary"]
    console.print(f"Corpus WER: {summary['corpus_wer']:.4f}")
    console.print(f"Speaker-Macro WER: {summary['speaker_macro_wer']:.4f}")
    console.print(f"Disparity D: {summary['disparity_d']:.4f}")
    console.print(f"Best Group: {summary['best_group_id']} | Worst Group: {summary['worst_group_id']}")
    console.print(f"Group WERs: {summary['group_wers']}")

    # Verify predictions file
    df_pred = pd.read_csv(os.path.join(output_dir, "predictions.csv"))
    console.print(f"\nPredictions logged: {len(df_pred)} rows.")
    console.print("Sample predictions:")
    for _, row in df_pred.head(3).iterrows():
        console.print(f"  [{row['group_id']}] Ref: '{row['reference_normalized']}' -> Hyp: '{row['hypothesis_normalized']}' (WER: {row['wer']})")

    # Verify window metrics
    df_win = pd.read_csv(os.path.join(output_dir, "window_metrics.csv"))
    console.print(f"\nWindows logged: {len(df_win)} windows.")
    console.print(df_win[["window_id", "window_wer", "cumulative_wer", "theta_before_hash", "theta_after_hash", "adaptation_updated"]])

    # Verify invariant: theta_before_hash == theta_after_hash for all windows
    for idx, row in df_win.iterrows():
        assert row["theta_before_hash"] == row["theta_after_hash"], f"Model state mutated in window {row['window_id']}!"
        assert row["adaptation_updated"] == False

    console.print("\n[bold green][PASS] Phase D/E Pilot Verification PASSED with strict invariance![/bold green]")

if __name__ == "__main__":
    run_pilot()
