"""
Partition and Split Audit Report generator.
Computes speaker disjointness, word counts, and partition balances, generating
reports/split_report.json and reports/split_report.md.
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any, List
import pandas as pd
from pydantic import BaseModel, Field

from dsg_ctta.data.schema import DatasetManifest


class PartitionSummary(BaseModel):
    partition_name: str
    num_speakers: int
    num_utterances: int
    total_reference_words: int
    speaker_ids: List[str]
    group_distribution: Dict[str, int]


class SplitAuditReport(BaseModel):
    dataset_name: str
    protocol_version: str = "v1.0.0-canonical"
    total_primary_speakers: int
    total_primary_utterances: int
    is_strictly_speaker_disjoint: bool
    speaker_intersections: Dict[str, List[str]]
    partition_summaries: Dict[str, PartitionSummary]
    creation_timestamp: str


def generate_split_audit_report(
    splits_dir: str = "datasets/splits",
    output_dir: str = "reports"
) -> SplitAuditReport:
    """Generate split audit report across all CSVs in splits_dir."""
    os.makedirs(output_dir, exist_ok=True)
    from datetime import datetime

    partition_files = {
        "development": os.path.join(splits_dir, "development.csv"),
        "calibration": os.path.join(splits_dir, "calibration.csv"),
        "sentinel_candidates": os.path.join(splits_dir, "sentinel_candidates.csv"),
        "final_test": os.path.join(splits_dir, "final_test.csv"),
        "external_validation": os.path.join(splits_dir, "external_validation.csv")
    }

    partition_dfs = {}
    partition_speakers = {}
    partition_summaries = {}

    for p_name, csv_path in partition_files.items():
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            partition_dfs[p_name] = df
            spks = sorted(df["speaker_id"].unique().tolist())
            partition_speakers[p_name] = set(spks)
            
            grp_dist = df.groupby("group_id")["utterance_id"].count().to_dict()
            tot_words = int(df["reference_word_count"].sum())

            partition_summaries[p_name] = PartitionSummary(
                partition_name=p_name,
                num_speakers=len(spks),
                num_utterances=len(df),
                total_reference_words=tot_words,
                speaker_ids=spks,
                group_distribution=grp_dist
            )

    # Check pairwise speaker intersections
    speaker_intersections = {}
    p_names = list(partition_speakers.keys())
    has_leakage = False

    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            p1, p2 = p_names[i], p_names[j]
            overlap = sorted(list(partition_speakers[p1].intersection(partition_speakers[p2])))
            if overlap:
                has_leakage = True
                speaker_intersections[f"{p1}_x_{p2}"] = overlap

    total_primary_spks = sum(
        partition_summaries[p].num_speakers
        for p in ["development", "calibration", "sentinel_candidates", "final_test"]
        if p in partition_summaries
    )
    total_primary_utts = sum(
        partition_summaries[p].num_utterances
        for p in ["development", "calibration", "sentinel_candidates", "final_test"]
        if p in partition_summaries
    )

    report = SplitAuditReport(
        dataset_name="L2-ARCTIC",
        total_primary_speakers=total_primary_spks,
        total_primary_utterances=total_primary_utts,
        is_strictly_speaker_disjoint=(not has_leakage),
        speaker_intersections=speaker_intersections,
        partition_summaries=partition_summaries,
        creation_timestamp=datetime.utcnow().isoformat() + "Z"
    )

    # Save JSON
    json_path = os.path.join(output_dir, "split_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    # Save Markdown
    md_path = os.path.join(output_dir, "split_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Stage 2: Speaker-Disjoint Partition Audit Report\n\n")
        f.write(f"**Protocol Version:** `{report.protocol_version}` | **Timestamp:** `{report.creation_timestamp}`  \n")
        disjoint_status = "**ZERO LEAKAGE (PASSED)**" if report.is_strictly_speaker_disjoint else "**LEAKAGE DETECTED (FAILED)**"
        f.write(f"**Speaker Disjointness Verification:** {disjoint_status}  \n\n")
        f.write("## 1. Partition Overview\n\n")
        f.write("| Partition | Role in Protocol | Speakers | Utterances | Ref Words | Assigned Speaker IDs |\n")
        f.write("|---|---|---|---|---|---|\n")
        for p_name, p in report.partition_summaries.items():
            role_desc = {
                "development": "Development & baseline tuning",
                "calibration": "Controller hyperparameter calibration",
                "sentinel_candidates": "Frozen sentinel safety evaluation panel",
                "final_test": "Untouched one-shot prequential evaluation",
                "external_validation": "Independent generalization verification"
            }.get(p_name, "Research partition")
            spk_str = ", ".join(p.speaker_ids)
            f.write(f"| **{p_name}** | {role_desc} | {p.num_speakers} | {p.num_utterances} | {p.total_reference_words} | `{spk_str}` |\n")

        f.write("\n## 2. Global Accent Distribution per Partition\n\n")
        all_groups = sorted(list(set(g for p in report.partition_summaries.values() for g in p.group_distribution.keys())))
        headers = ["Partition"] + all_groups
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        for p_name, p in report.partition_summaries.items():
            row = [f"**{p_name}**"] + [str(p.group_distribution.get(g, 0)) for g in all_groups]
            f.write("| " + " | ".join(row) + " |\n")

    return report
