"""
Command Line Interface (CLI) for DSG-CTTA Research Framework.
Enforces CLI-first development adhering to the canonical research architecture.
"""

from __future__ import annotations
import os
import json
import typer
from rich.console import Console
from rich.table import Table

from dsg_ctta.data.fixtures import generate_research_fixture_dataset
from dsg_ctta.data.splits import create_speaker_disjoint_splits, export_splits_to_csv
from dsg_ctta.experiments.runner import run_baseline_evaluation, run_multi_model_audit
from dsg_ctta.offline.glmm import fit_confound_aware_count_model
from dsg_ctta.reporting.tables import (
    generate_baseline_summary_table_md,
    generate_group_breakdown_table_md,
    generate_glmm_report_table_md
)

app = typer.Typer(help="DSG-CTTA: Disparity-Aware Continual Test-Time Adaptation Research Framework")
data_app = typer.Typer(help="Dataset generation, validation, and speaker-disjoint splitting")
baseline_app = typer.Typer(help="Baseline model inference and static evaluation")
audit_app = typer.Typer(help="Cross-model disparity audit")
glmm_app = typer.Typer(help="Confound-aware GLMM analysis")
report_app = typer.Typer(help="Report generation")

app.add_typer(data_app, name="data")
app.add_typer(baseline_app, name="baseline")
app.add_typer(audit_app, name="audit")
app.add_typer(glmm_app, name="glmm")
app.add_typer(report_app, name="report")

console = Console()


@data_app.command("fixture")
def create_fixture(
    output_dir: str = typer.Option("datasets/fixture", help="Output directory for fixture dataset"),
    utts_per_speaker: int = typer.Option(3, help="Number of utterances per speaker")
):
    """Generate multi-group synthetic/curated audio fixture dataset for immediate testing."""
    console.print(f"[bold cyan]Generating E2E research fixture dataset[/bold cyan] in: {output_dir}")
    primary_utts, ext_utts = generate_research_fixture_dataset(
        output_dir=output_dir,
        utterances_per_speaker=utts_per_speaker
    )
    console.print(f"[green]Successfully generated:[/green] {len(primary_utts)} primary utterances and {len(ext_utts)} external validation utterances.")

    # Save raw metadata manifest
    manifest_path = os.path.join(output_dir, "raw_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump([u.model_dump() for u in primary_utts + ext_utts], f, indent=2)
    console.print(f"[green]Saved raw manifest to:[/green] {manifest_path}")


@data_app.command("split")
def split_dataset(
    manifest_path: str = typer.Option("datasets/fixture/raw_manifest.json", help="Path to raw metadata manifest"),
    output_dir: str = typer.Option("datasets/splits", help="Output directory for speaker-disjoint split CSVs"),
    seed: int = typer.Option(42, help="Random seed for splitting")
):
    """Create strictly speaker-disjoint 5-partition splits with zero leakage."""
    from dsg_ctta.data.schema import UtteranceMetadata
    if not os.path.exists(manifest_path):
        console.print(f"[bold red]Manifest file not found:[/bold red] {manifest_path}")
        raise typer.Exit(code=1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    all_utts = [UtteranceMetadata(**item) for item in raw_list]
    primary_utts = [u for u in all_utts if u.provenance.source_dataset != "Synthetic-External-Corpus"]
    ext_utts = [u for u in all_utts if u.provenance.source_dataset == "Synthetic-External-Corpus"]

    manifest = create_speaker_disjoint_splits(
        utterances=primary_utts,
        seed=seed,
        external_utterances=ext_utts
    )

    exported = export_splits_to_csv(manifest, output_dir=output_dir)
    console.print("[bold green]Speaker-disjoint partitions successfully created with ZERO leakage:[/bold green]")
    for p_name, csv_path in exported.items():
        part = manifest.partitions[p_name]
        console.print(f" - [cyan]{p_name}[/cyan]: {part.num_speakers} speakers, {part.num_utterances} utterances -> {csv_path}")


@baseline_app.command("run")
def run_baseline(
    split_csv: str = typer.Option("datasets/splits/final_test.csv", help="Path to partition CSV"),
    model_name: str = typer.Option("mock_asr", help="Model name (e.g. wav2vec2_base, whisper_base, mock_asr)"),
    output_dir: str = typer.Option("reports/baseline", help="Directory for evaluation results"),
    device: str = typer.Option("cpu", help="Device (cpu or cuda)")
):
    """Run baseline ASR inference and compute error rates, group metrics, and GLMM."""
    import pandas as pd
    from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo

    if not os.path.exists(split_csv):
        console.print(f"[bold red]Split CSV not found:[/bold red] {split_csv}")
        raise typer.Exit(code=1)

    df = pd.read_csv(split_csv)
    utts = []
    for _, row in df.iterrows():
        meta = UtteranceMetadata(
            utterance_id=str(row["utterance_id"]),
            speaker_id=str(row["speaker_id"]),
            group_id=str(row["group_id"]),
            group_type=str(row["group_type"]),
            audio_filepath=str(row["audio_filepath"]),
            audio_sha256=str(row.get("audio_sha256", "")),
            duration_seconds=float(row["duration_seconds"]),
            snr_db=float(row["snr_db"]) if pd.notnull(row.get("snr_db")) else 20.0,
            speech_rate_wpm=float(row["speech_rate_wpm"]) if pd.notnull(row.get("speech_rate_wpm")) else 140.0,
            device_id=str(row.get("device_id", "unknown")),
            reference_raw=str(row["reference_raw"]),
            reference_normalized=str(row["reference_normalized"]),
            reference_word_count=int(row["reference_word_count"]),
            partition=str(row.get("partition", "final_test")),
            provenance=ProvenanceInfo(source_dataset=str(row.get("source_dataset", "unknown")))
        )
        utts.append(meta)

    partition_name = os.path.splitext(os.path.basename(split_csv))[0]
    res = run_baseline_evaluation(
        utterances=utts,
        model_name=model_name,
        partition_name=partition_name,
        output_dir=output_dir,
        device=device,
        run_glmm=True
    )

    summary = res["summary"]
    console.print(f"[bold green]Baseline Evaluation Completed:[/bold green]")
    console.print(f" - Corpus WER: [bold yellow]{summary.corpus_wer * 100:.2f}%[/bold yellow]")
    console.print(f" - Speaker-Macro WER: [bold yellow]{summary.speaker_macro_wer * 100:.2f}%[/bold yellow]")
    console.print(f" - Disparity D (max - min): [bold red]{summary.disparity_d * 100:.2f}%[/bold red]")
    console.print(f" - Best Group: [cyan]{summary.best_group_id}[/cyan] ({summary.min_group_wer * 100:.2f}%)")
    console.print(f" - Worst Group: [cyan]{summary.worst_group_id}[/cyan] ({summary.max_group_wer * 100:.2f}%)")


@audit_app.command("run")
def run_audit(
    split_csv: str = typer.Option("datasets/splits/final_test.csv", help="Path to partition CSV"),
    models: str = typer.Option("mock_asr", help="Comma-separated model names or '6-models'"),
    output_dir: str = typer.Option("reports/audit", help="Directory for audit reports"),
    device: str = typer.Option("cpu", help="Device (cpu or cuda)")
):
    """Run cross-model static disparity audit."""
    import pandas as pd
    from dsg_ctta.data.schema import UtteranceMetadata, ProvenanceInfo

    if not os.path.exists(split_csv):
        console.print(f"[bold red]Split CSV not found:[/bold red] {split_csv}")
        raise typer.Exit(code=1)

    df = pd.read_csv(split_csv)
    utts = []
    for _, row in df.iterrows():
        meta = UtteranceMetadata(
            utterance_id=str(row["utterance_id"]),
            speaker_id=str(row["speaker_id"]),
            group_id=str(row["group_id"]),
            group_type=str(row["group_type"]),
            audio_filepath=str(row["audio_filepath"]),
            audio_sha256=str(row.get("audio_sha256", "")),
            duration_seconds=float(row["duration_seconds"]),
            snr_db=float(row["snr_db"]) if pd.notnull(row.get("snr_db")) else 20.0,
            speech_rate_wpm=float(row["speech_rate_wpm"]) if pd.notnull(row.get("speech_rate_wpm")) else 140.0,
            device_id=str(row.get("device_id", "unknown")),
            reference_raw=str(row["reference_raw"]),
            reference_normalized=str(row["reference_normalized"]),
            reference_word_count=int(row["reference_word_count"]),
            partition=str(row.get("partition", "final_test")),
            provenance=ProvenanceInfo(source_dataset=str(row.get("source_dataset", "unknown")))
        )
        utts.append(meta)

    if models == "6-models":
        model_list = ["wav2vec2_base", "whisper_base", "hubert_base", "data2vec_base", "distil_whisper_small", "xlsr_english"]
    else:
        model_list = [m.strip() for m in models.split(",")]

    partition_name = os.path.splitext(os.path.basename(split_csv))[0]
    audit_res = run_multi_model_audit(
        utterances=utts,
        model_names=model_list,
        partition_name=partition_name,
        output_dir=output_dir,
        device=device
    )

    console.print(f"[bold green]Audit complete! Report generated at:[/bold green] {audit_res['report_md_path']}")


if __name__ == "__main__":
    app()
