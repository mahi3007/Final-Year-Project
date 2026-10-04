"""
Verification Pilot for DSUTA and DMSUTA on 12 real recordings from development split.
"""

from rich.console import Console
from dsg_ctta.data.splits import load_partition_from_csv
from dsg_ctta.experiments.ctta_runner import run_prequential_stream_experiment

console = Console()

def run_pilots():
    dev_csv = "datasets/splits/development.csv"
    all_dev_utts = load_partition_from_csv(dev_csv)

    groups = ["Arabic", "Hindi", "Korean", "Mandarin", "Spanish", "Vietnamese"]
    pilot_utts = []
    for g in groups:
        g_utts = [u for u in all_dev_utts if u.group_id == g]
        pilot_utts.extend(g_utts[:2])

    console.print(f"Loaded {len(pilot_utts)} pilot utterances.")

    # 1. DSUTA Pilot
    console.print("\n[bold cyan]--- Running DSUTA Pilot ---[/bold cyan]")
    res_dsuta = run_prequential_stream_experiment(
        utterances=pilot_utts,
        model_name="wav2vec2_base",
        method_name="dsuta",
        adapter_config={"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "reset_threshold_ratio": 1.25},
        ordering_id="ORDER_A",
        window_size_k=4,
        device="cpu",
        output_dir="reports/ctta/pilot_dsuta",
        seed=42,
        experiment_id="pilot_dsuta_wav2vec2"
    )
    console.print(f"DSUTA WER: {res_dsuta['summary']['corpus_wer']:.4f} | Resets: {res_dsuta['summary']['num_resets']}")

    # 2. DMSUTA Pilot
    console.print("\n[bold cyan]--- Running DMSUTA Pilot ---[/bold cyan]")
    res_dmsuta = run_prequential_stream_experiment(
        utterances=pilot_utts,
        model_name="wav2vec2_base",
        method_name="dmsuta",
        adapter_config={"lr": 1e-4, "temperature": 2.5, "alpha": 0.5, "steps": 1, "max_bank_size": 3},
        ordering_id="ORDER_A",
        window_size_k=4,
        device="cpu",
        output_dir="reports/ctta/pilot_dmsuta",
        seed=42,
        experiment_id="pilot_dmsuta_wav2vec2"
    )
    console.print(f"DMSUTA WER: {res_dmsuta['summary']['corpus_wer']:.4f} | Disparity: {res_dmsuta['summary']['disparity_d']:.4f}")

    console.print("\n[bold green][PASS] DSUTA & DMSUTA Pilots Completed Successfully![/bold green]")

if __name__ == "__main__":
    run_pilots()
