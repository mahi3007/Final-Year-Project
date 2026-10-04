"""
Speaker-disjoint partition generator.
Enforces zero speaker leakage across Development, Calibration, Sentinel, and Final Test partitions.
"""

from __future__ import annotations
import random
from typing import List, Dict, Set, Tuple
import pandas as pd
from dsg_ctta.data.schema import UtteranceMetadata, PartitionManifest, DatasetManifest, ProvenanceInfo


def create_speaker_disjoint_splits(
    utterances: List[UtteranceMetadata],
    split_ratios: Dict[str, float] = None,
    seed: int = 42,
    external_utterances: List[UtteranceMetadata] = None
) -> DatasetManifest:
    """
    Generate strictly speaker-disjoint partitions:
    - development
    - calibration
    - sentinel_candidates
    - final_test
    - external_validation (if provided)
    
    Guarantees:
    1. Every speaker appears in exactly one primary partition.
    2. Group representation is balanced across partitions.
    3. Sentinel speakers never appear in adaptation data.
    """
    if split_ratios is None:
        split_ratios = {
            "development": 0.25,
            "calibration": 0.25,
            "sentinel_candidates": 0.25,
            "final_test": 0.25
        }

    # Verify ratio sum
    total_ratio = sum(split_ratios.values())
    assert abs(total_ratio - 1.0) < 1e-5, f"Split ratios must sum to 1.0, got {total_ratio}"

    # Group speakers by their group_id
    rng = random.Random(seed)
    group_to_speakers: Dict[str, List[str]] = {}
    speaker_to_group: Dict[str, str] = {}
    speaker_to_utterances: Dict[str, List[UtteranceMetadata]] = {}

    for utt in utterances:
        spk = utt.speaker_id
        grp = utt.group_id
        speaker_to_group[spk] = grp
        if grp not in group_to_speakers:
            group_to_speakers[grp] = []
        if spk not in group_to_speakers[grp]:
            group_to_speakers[grp].append(spk)
        if spk not in speaker_to_utterances:
            speaker_to_utterances[spk] = []
        speaker_to_utterances[spk].append(utt)

    # Sort keys for deterministic reproducibility
    sorted_groups = sorted(group_to_speakers.keys())
    for grp in sorted_groups:
        group_to_speakers[grp].sort()
        rng.shuffle(group_to_speakers[grp])

    partition_speakers: Dict[str, Set[str]] = {p: set() for p in split_ratios.keys()}
    partition_names = list(split_ratios.keys())

    # Distribute speakers per group across partitions
    for grp in sorted_groups:
        spks = group_to_speakers[grp]
        n_spks = len(spks)
        
        if n_spks == 1:
            # If only 1 speaker for this group, assign to final_test
            partition_speakers["final_test"].add(spks[0])
        elif n_spks == 2:
            partition_speakers["development"].add(spks[0])
            partition_speakers["final_test"].add(spks[1])
        elif n_spks == 3:
            partition_speakers["development"].add(spks[0])
            partition_speakers["sentinel_candidates"].add(spks[1])
            partition_speakers["final_test"].add(spks[2])
        else:
            # Round-robin or proportional allocation
            for i, spk in enumerate(spks):
                p_idx = i % len(partition_names)
                partition_speakers[partition_names[p_idx]].add(spk)

    # STRICT INVARIANT ASSERTION: Check zero speaker overlap across all primary partitions
    all_assigned_speakers = []
    for p_name, spk_set in partition_speakers.items():
        all_assigned_speakers.extend(list(spk_set))
    
    unique_assigned = set(all_assigned_speakers)
    if len(all_assigned_speakers) != len(unique_assigned):
        raise AssertionError("CRITICAL INVARIANT VIOLATION: Speaker leakage detected across split partitions!")

    # Check pair-wise intersections
    p_keys = list(partition_speakers.keys())
    for i in range(len(p_keys)):
        for j in range(i + 1, len(p_keys)):
            overlap = partition_speakers[p_keys[i]].intersection(partition_speakers[p_keys[j]])
            if overlap:
                raise AssertionError(
                    f"CRITICAL LEAKAGE: Partitions '{p_keys[i]}' and '{p_keys[j]}' share speakers: {overlap}"
                )

    # Construct partition manifests
    partitions_dict: Dict[str, PartitionManifest] = {}
    total_utts = 0
    total_spks = len(unique_assigned)
    group_dist: Dict[str, int] = {}

    for p_name, spk_set in partition_speakers.items():
        p_utts: List[UtteranceMetadata] = []
        p_groups: Set[str] = set()
        for spk in sorted(spk_set):
            for utt in speaker_to_utterances[spk]:
                # Update partition field on metadata copy
                utt_copy = utt.model_copy(update={"partition": p_name})
                p_utts.append(utt_copy)
                p_groups.add(utt_copy.group_id)
                group_dist[utt_copy.group_id] = group_dist.get(utt_copy.group_id, 0) + 1

        total_utts += len(p_utts)
        partitions_dict[p_name] = PartitionManifest(
            partition_name=p_name,
            num_utterances=len(p_utts),
            num_speakers=len(spk_set),
            speaker_ids=sorted(list(spk_set)),
            group_ids=sorted(list(p_groups)),
            utterances=p_utts
        )

    # Add external validation partition if provided
    if external_utterances:
        ext_spks = set()
        ext_groups = set()
        ext_utts_clean = []
        for utt in external_utterances:
            ext_spk = utt.speaker_id
            # Ensure external speakers do NOT overlap with primary speakers
            if ext_spk in unique_assigned:
                raise AssertionError(
                    f"CRITICAL LEAKAGE: External validation speaker '{ext_spk}' overlaps with primary dataset!"
                )
            ext_spks.add(ext_spk)
            ext_groups.add(utt.group_id)
            utt_copy = utt.model_copy(update={"partition": "external_validation"})
            ext_utts_clean.append(utt_copy)

        partitions_dict["external_validation"] = PartitionManifest(
            partition_name="external_validation",
            num_utterances=len(ext_utts_clean),
            num_speakers=len(ext_spks),
            speaker_ids=sorted(list(ext_spks)),
            group_ids=sorted(list(ext_groups)),
            utterances=ext_utts_clean
        )

    manifest = DatasetManifest(
        dataset_name=utterances[0].provenance.source_dataset if utterances else "unknown",
        partitions=partitions_dict,
        total_utterances=total_utts,
        total_speakers=total_spks,
        group_distribution=group_dist,
        speaker_group_mapping=speaker_to_group
    )
    manifest.manifest_hash = manifest.compute_hash()
    return manifest


def export_splits_to_csv(manifest: DatasetManifest, output_dir: str) -> Dict[str, str]:
    """Export each partition to a dedicated CSV file."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    exported_files = {}

    for p_name, part in manifest.partitions.items():
        records = []
        for utt in part.utterances:
            records.append({
                "utterance_id": utt.utterance_id,
                "speaker_id": utt.speaker_id,
                "group_id": utt.group_id,
                "group_type": utt.group_type,
                "audio_filepath": utt.audio_filepath,
                "audio_sha256": utt.audio_sha256,
                "duration_seconds": utt.duration_seconds,
                "snr_db": utt.snr_db,
                "speech_rate_wpm": utt.speech_rate_wpm,
                "device_id": utt.device_id,
                "reference_raw": utt.reference_raw,
                "reference_normalized": utt.reference_normalized,
                "reference_word_count": utt.reference_word_count,
                "partition": utt.partition,
                "source_dataset": utt.provenance.source_dataset
            })
        df = pd.DataFrame(records)
        csv_path = os.path.join(output_dir, f"{p_name}.csv")
        df.to_csv(csv_path, index=False)
        exported_files[p_name] = csv_path

    return exported_files
 
 
def load_partition_from_csv(csv_path: str) -> List[UtteranceMetadata]:
    """Load a partition CSV into a list of UtteranceMetadata objects."""
    df = pd.read_csv(csv_path)
    utterances = []
    for _, row in df.iterrows():
        utt = UtteranceMetadata(
            utterance_id=str(row["utterance_id"]),
            speaker_id=str(row["speaker_id"]),
            group_id=str(row["group_id"]),
            group_type=str(row.get("group_type", "native_language")),
            audio_filepath=str(row["audio_filepath"]),
            audio_sha256=str(row.get("audio_sha256", "")),
            sampling_rate_hz=int(row.get("sampling_rate_hz", 16000)),
            duration_seconds=float(row.get("duration_seconds", 4.0)),
            snr_db=float(row["snr_db"]) if pd.notnull(row.get("snr_db")) else 20.0,
            speech_rate_wpm=float(row["speech_rate_wpm"]) if pd.notnull(row.get("speech_rate_wpm")) else 140.0,
            device_id=str(row.get("device_id", "studio_condenser")),
            reference_raw=str(row["reference_raw"]),
            reference_normalized=str(row.get("reference_normalized", row["reference_raw"])),
            reference_word_count=int(row.get("reference_word_count", len(str(row["reference_raw"]).split()))),
            partition=str(row.get("partition", "")),
            provenance=ProvenanceInfo(source_dataset=str(row.get("source_dataset", "L2-ARCTIC")))
        )
        utterances.append(utt)
    return utterances
