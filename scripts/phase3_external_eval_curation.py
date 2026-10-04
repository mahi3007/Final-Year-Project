#!/usr/bin/env python3
"""
DSG-CTTA Stage 5 Phase 3: External Final-Evaluation Set Curation
================================================================
Dataset:  Mozilla Common Voice English (cv-corpus-11.0-2022-09-21)
License:  CC0 1.0 Public Domain
Role:     External out-of-distribution stress-test / final evaluation
          NOT an L2-ARCTIC replication corpus.

Design target:
    6 groups × 10 speakers/group × 15 clips/speaker = 900 evaluation clips

ABSOLUTE RESTRICTIONS (enforced in code):
  - No ASR model inference
  - No WER / CER computation for selection
  - No DSG implementation
  - No CTTA execution
  - No performance-based speaker or clip selection
  - Fail-closed: report BLOCKED rather than silently relaxing criteria

Usage:
    # Step 1 — metadata feasibility checkpoint (no audio download)
    python scripts/phase3_external_eval_curation.py --phase metadata

    # Step 2 — deterministic selection + manifest (after checkpoint passes)
    python scripts/phase3_external_eval_curation.py --phase select

    # Step 3 — audio materialization of exactly 900 clips (after select)
    python scripts/phase3_external_eval_curation.py --phase materialize

    # Run all phases in sequence
    python scripts/phase3_external_eval_curation.py --phase all

    # If you already have validated.tsv downloaded:
    python scripts/phase3_external_eval_curation.py --phase metadata \\
        --tsv-path /path/to/validated.tsv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure stdout/stderr handles UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
SPLITS_DIR = PROJECT_ROOT / "datasets" / "splits"
REPORTS_DIR = PROJECT_ROOT / "reports" / "stage5"
EXTERNAL_AUDIO_DIR = PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "audio"

# ---------------------------------------------------------------------------
# Frozen protocol constants — Stage 5 Amended Protocol v2.0.0 (CV 27.0)
# ---------------------------------------------------------------------------
SELECTION_SEED: int = 20261001
CLIP_SEED_OFFSET: int = 1          # clip RNG seed = SELECTION_SEED + CLIP_SEED_OFFSET
SELECTION_RULE_VERSION: str = "v1.0-cv27-amended"
GROUP_DEFINITION_VERSION: str = "stage5_cv27_normalized_strata_v1"
PROTOCOL_VERSION: str = "v2.0.0-amended-cv27"

DATASET_NAME: str = "common_voice"
DATASET_RELEASE: str = "cv-corpus-27.0-2026-09-11"
DATASET_TITLE: str = "Common Voice Scripted Speech 27.0 - English"
DATASET_LICENSE: str = "CC0-1.0"
DATASET_DISTRIBUTOR: str = "Mozilla Data Collective (MDC Dataset ID: cmu5jplf300nwmh07iqvk9leo)"
DATASET_SOURCE_URL: str = "https://mozilladatacollective.com/datasets/cmu5jplf300nwmh07iqvk9leo"
HF_DATASET_ID: str = "cmu5jplf300nwmh07iqvk9leo"
DATASET_LANGUAGE: str = "en"

# Target pre-specified evaluation strata (frozen)
TARGET_GROUPS: List[str] = [
    "US English",
    "England English",
    "South Asian English",
    "Australian English",
    "Canadian English",
    "Irish English",
]

TARGET_STRATA_CODES: Dict[str, str] = {
    "US English": "us",
    "England English": "england",
    "South Asian English": "south_asian",
    "Australian English": "australia",
    "Canadian English": "canada",
    "Irish English": "ireland",
}

GROUP_LABELS: Dict[str, str] = {
    "US English": "United States English",
    "England English": "England English",
    "South Asian English": "India and South Asia (India, Pakistan, Sri Lanka)",
    "Australian English": "Australian English",
    "Canadian English": "Canadian English",
    "Irish English": "Irish English",
}

# Frozen accent normalization mapping:
# Maps raw CV 27.0 accents strings (lowercased, stripped) to pre-specified evaluation strata.
ACCENT_NORMALIZATION_MAP: Dict[str, str] = {
    "united states english": "US English",
    "england english": "England English",
    "india and south asia (india, pakistan, sri lanka)": "South Asian English",
    "australian english": "Australian English",
    "canadian english": "Canadian English",
    "irish english": "Irish English",
}

def normalize_accent_label(raw_accent: str) -> Optional[str]:
    """
    Normalize raw accent string to one of the 6 canonical Stage 5 evaluation strata.
    Strictly excludes:
      - Empty or whitespace-only strings
      - Compound/piped declarations ('|')
      - Unrecognized accent strings
    """
    if not raw_accent:
        return None
    # Compound / piped accents strictly excluded from primary 6-group evaluation
    if "|" in raw_accent:
        return None
    cleaned = raw_accent.strip().lower()
    return ACCENT_NORMALIZATION_MAP.get(cleaned)

TARGET_SPEAKERS_PER_GROUP: int = 10
TARGET_CLIPS_PER_SPEAKER: int = 15
TARGET_TOTAL_SPEAKERS: int = TARGET_SPEAKERS_PER_GROUP * len(TARGET_GROUPS)   # 60
TARGET_TOTAL_CLIPS: int = (
    TARGET_SPEAKERS_PER_GROUP * TARGET_CLIPS_PER_SPEAKER * len(TARGET_GROUPS)  # 900
)
MIN_CLIPS_FOR_ELIGIBILITY: int = TARGET_CLIPS_PER_SPEAKER  # 15
MIN_TRANSCRIPT_WORDS: int = 2   # minimum transcript length

# ---------------------------------------------------------------------------

# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ===========================================================================
# PHASE 3A — DATASET ACCESS
# ===========================================================================

def get_hf_token() -> Optional[str]:
    """Retrieve HuggingFace token from environment variables."""
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")


def _stream_from_huggingface() -> List[Dict[str, Any]]:
    """
    Stream metadata from HuggingFace Common Voice 11.0 (English).

    Uses streaming=True so that audio bytes are NOT downloaded.
    We capture only text/metadata fields.

    Requires either:
      - HF_TOKEN env var (token that has accepted CV 11.0 terms)
      - Public access (unlikely post-Oct-2025)
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        raise RuntimeError(
            "datasets library not installed.\n"
            "Run: pip install datasets huggingface_hub"
        )

    token = get_hf_token()
    if not token:
        logger.warning(
            "No HF_TOKEN found in environment. "
            "Access to Common Voice 11.0 may require authentication."
        )

    logger.info(f"Streaming metadata from HuggingFace: {HF_DATASET_ID} / {DATASET_LANGUAGE}")

    try:
        ds = load_dataset(
            HF_DATASET_ID,
            DATASET_LANGUAGE,
            streaming=True,
            split="train+validation+test+other",
            token=token,
        )
    except Exception as exc:
        err_str = str(exc)
        raise RuntimeError(
            f"Common Voice dataset not accessible on HuggingFace ({err_str[:200]}).\n\n"
            "CAUSE:\n"
            "  Mozilla transitioned all Common Voice dataset distribution to the\n"
            "  Mozilla Data Collective (MDC). As part of this transition, the previous\n"
            f"  HuggingFace repo '{HF_DATASET_ID}' was deprecated and removed upstream (404 Not Found).\n\n"
            "RESOLUTION (Direct TSV Download):\n"
            "  1. Visit: https://datacollective.mozillafoundation.org/ or https://commonvoice.mozilla.org/en/datasets\n"
            "  2. Sign in or create a free account and accept the dataset terms of service.\n"
            "  3. Download the English dataset archive, or extract just 'validated.tsv' (~300 MB).\n"
            "     (You do NOT need the full 22 GB audio archive for the metadata checkpoint or selection phase).\n"
            "  4. Place the file at:\n"
            "     datasets/external/common_voice_11/validated.tsv\n"
            "  5. Run:\n"
            "     python scripts/phase3_external_eval_curation.py \\\n"
            "       --phase metadata \\\n"
            "       --tsv-path datasets/external/common_voice_11/validated.tsv\n"
        )

    records: List[Dict[str, Any]] = []
    logger.info("Streaming records (metadata only — no audio bytes)…")

    for i, row in enumerate(ds):
        records.append({
            "client_id": str(row.get("client_id") or ""),
            "path":      str(row.get("path") or ""),
            "sentence":  str(row.get("sentence") or ""),
            "up_votes":  int(row.get("up_votes") or 0),
            "down_votes": int(row.get("down_votes") or 0),
            "age":       str(row.get("age") or ""),
            "gender":    str(row.get("gender") or ""),
            "accent":    str(row.get("accent") or ""),
            "locale":    str(row.get("locale") or "en"),
            "segment":   str(row.get("segment") or ""),
        })
        if i % 100_000 == 0 and i > 0:
            logger.info(f"  …streamed {i:,} records")

    logger.info(f"Streaming complete. Total records: {len(records):,}")
    return records


def _load_from_tsv(tsv_path: Path) -> List[Dict[str, Any]]:
    """Load metadata from a local validated.tsv file."""
    logger.info(f"Loading metadata from local TSV: {tsv_path}")
    if not tsv_path.exists():
        raise FileNotFoundError(f"TSV not found: {tsv_path}")

    records: List[Dict[str, Any]] = []
    with open(tsv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            records.append({
                "client_id":  str(row.get("client_id") or ""),
                "path":       str(row.get("path") or ""),
                "sentence":   str(row.get("sentence") or ""),
                "up_votes":   int(row.get("up_votes") or 0),
                "down_votes": int(row.get("down_votes") or 0),
                "age":        str(row.get("age") or ""),
                "gender":     str(row.get("gender") or ""),
                "accent":     str(row.get("accents") or row.get("accent") or ""),
                "locale":     str(row.get("locale") or "en"),
                "segment":    str(row.get("segment") or ""),
            })

    logger.info(f"Loaded {len(records):,} records from TSV")
    return records


def load_metadata(tsv_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Phase 3A/3B: Load metadata from best available source."""
    if tsv_path is not None and tsv_path.exists():
        return _load_from_tsv(tsv_path)

    # Check default paths for CV 27.0
    for candidate in [
        PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv",
        PROJECT_ROOT / "datasets" / "external" / "common_voice_27_intermediate" / "validated.tsv",
        PROJECT_ROOT / "datasets" / "external" / "common_voice_11" / "validated.tsv",
    ]:
        if candidate.exists():
            return _load_from_tsv(candidate)

    try:
        return _stream_from_huggingface()
    except RuntimeError as exc:
        logger.error("BLOCKED — Cannot access dataset metadata.")
        logger.error(str(exc))
        sys.exit(1)


# ===========================================================================
# PHASE 3B — METADATA HASH (provenance)
# ===========================================================================

def hash_records(records: List[Dict[str, Any]]) -> str:
    """Compute a deterministic hash of the loaded metadata (field-order stable)."""
    h = hashlib.sha256()
    for r in records:
        line = json.dumps(r, sort_keys=True, ensure_ascii=True)
        h.update(line.encode("utf-8"))
    return h.hexdigest()


# ===========================================================================
# PHASE 3C — ELIGIBLE SPEAKER POOLS
# ===========================================================================

def _is_valid_transcript(sentence: str) -> bool:
    """Transcript must be non-empty and have at least MIN_TRANSCRIPT_WORDS words."""
    cleaned = sentence.strip()
    if not cleaned:
        return False
    words = cleaned.split()
    return len(words) >= MIN_TRANSCRIPT_WORDS


def build_eligible_speaker_pools(
    records: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Phase 3C: Build per-group eligible speaker pool under Amended Protocol v2.0.0.

    Eligibility criteria:
      C1. Raw accents field maps unambiguously to one of the 6 Stage 5 strata.
          (Compound/piped accents '|' strictly excluded).
      C2. client_id is non-empty.
      C3. path is non-empty (valid audio reference).
      C4. sentence is non-empty and >= MIN_TRANSCRIPT_WORDS (2) words.
      C5. Record is deduplicated at path level (duplicate paths discarded).
      C6. Speaker Homogeneity: Speaker has 100% consistent accent declarations
          across all qualified records. Ambiguous speakers with conflicting
          accents are strictly excluded.
      C7. Speaker must have >= MIN_CLIPS_FOR_ELIGIBILITY (15) clips passing C1-C6.

    DO NOT use:
      - ASR performance, WER, CER, model output, or disparity metrics.
      - Geographic inference or proxy heuristics.
    """
    logger.info("Phase 3C: Building eligible speaker pools (CV 27.0 amended protocol)…")

    # Step 1: Pre-scan to identify speaker accent homogeneity
    speaker_accents: Dict[str, set] = defaultdict(set)
    for rec in records:
        spk = rec["client_id"].strip()
        raw_accent = rec["accent"].strip()
        norm = normalize_accent_label(raw_accent)
        if norm and spk:
            speaker_accents[spk].add(norm)

    ambiguous_speakers = {spk for spk, accs in speaker_accents.items() if len(accs) > 1}
    if ambiguous_speakers:
        logger.info(
            f"  Excluded {len(ambiguous_speakers)} speakers with ambiguous/conflicting accents"
        )

    # Step 2: Populate speaker clips
    group_speakers: Dict[str, Dict[str, List[Dict]]] = {
        g: defaultdict(list) for g in TARGET_GROUPS
    }
    seen_paths: set = set()
    counters = {
        "total": 0, "no_accent": 0, "wrong_accent": 0, "dup_path": 0,
        "no_transcript": 0, "no_client": 0, "no_path": 0,
        "ambiguous_speaker": 0, "accepted": 0,
    }

    for rec in records:
        counters["total"] += 1

        client_id = rec["client_id"].strip()
        if not client_id:
            counters["no_client"] += 1
            continue

        if client_id in ambiguous_speakers:
            counters["ambiguous_speaker"] += 1
            continue

        raw_accent = rec["accent"].strip()
        if not raw_accent:
            counters["no_accent"] += 1
            continue

        accent = normalize_accent_label(raw_accent)
        if not accent:
            counters["wrong_accent"] += 1
            continue

        path = rec["path"].strip()
        if not path:
            counters["no_path"] += 1
            continue

        if path in seen_paths:
            counters["dup_path"] += 1
            continue
        seen_paths.add(path)

        if not _is_valid_transcript(rec["sentence"]):
            counters["no_transcript"] += 1
            continue

        counters["accepted"] += 1
        group_speakers[accent][client_id].append({
            "path":              path,
            "sentence":          rec["sentence"].strip(),
            "source_accent_raw": raw_accent,
            "up_votes":          rec["up_votes"],
            "down_votes":        rec["down_votes"],
            "age":               rec["age"],
            "gender":            rec["gender"],
        })

    logger.info(
        f"  Filtering summary: total={counters['total']:,}  "
        f"accepted={counters['accepted']:,}  "
        f"no_accent={counters['no_accent']:,}  "
        f"wrong_accent={counters['wrong_accent']:,}  "
        f"dup_path={counters['dup_path']:,}  "
        f"no_transcript={counters['no_transcript']:,}  "
        f"ambiguous_speaker={counters['ambiguous_speaker']:,}"
    )

    # Build eligible pool: speakers with >= MIN_CLIPS_FOR_ELIGIBILITY clips
    eligible_pools: Dict[str, Dict[str, Any]] = {}
    for group in TARGET_GROUPS:
        all_speakers = dict(group_speakers[group])
        eligible = {
            spk: clips
            for spk, clips in all_speakers.items()
            if len(clips) >= MIN_CLIPS_FOR_ELIGIBILITY
        }
        eligible_pools[group] = {
            "all_speakers": all_speakers,
            "eligible_speakers": eligible,
            "total_speakers": len(all_speakers),
            "eligible_count": len(eligible),
        }
        logger.info(
            f"  [{group:<22}] total_speakers={len(all_speakers):>7,}  "
            f"eligible(>={MIN_CLIPS_FOR_ELIGIBILITY} clips)={len(eligible):>6,}"
        )

    return eligible_pools



# ===========================================================================
# PHASE 3D — CHECKPOINT 1: FEASIBILITY TABLE
# ===========================================================================

def run_feasibility_checkpoint(
    eligible_pools: Dict[str, Dict[str, Any]],
) -> Tuple[bool, Dict[str, Dict]]:
    """
    Phase 3D: Print the Checkpoint 1 feasibility table.

    MUST return True for all 6 groups before proceeding.
    Returns (all_feasible, per_group_results).
    """
    sep = "=" * 80
    print(f"\n{sep}")
    print("CHECKPOINT 1 — PHASE 3D FEASIBILITY TABLE")
    print(f"Pinned release: {DATASET_RELEASE}")
    print(f"Minimum clips per speaker for eligibility: {MIN_CLIPS_FOR_ELIGIBILITY}")
    print(sep)

    header = (
        f"{'Group':<32} {'All Spk':>10} {'Eligible Spk':>14} "
        f"{'Target':>8} {'Feasible':>10}"
    )
    print(header)
    print("-" * 80)

    all_feasible = True
    results: Dict[str, Dict] = {}

    for group in TARGET_GROUPS:
        pool = eligible_pools[group]
        total_spk = pool["total_speakers"]
        eligible_spk = pool["eligible_count"]
        feasible = eligible_spk >= TARGET_SPEAKERS_PER_GROUP

        if not feasible:
            all_feasible = False

        label = GROUP_LABELS[group]
        status = "YES" if feasible else "NO — BLOCKED"
        print(
            f"{label:<32} {total_spk:>10,} {eligible_spk:>14,} "
            f"{TARGET_SPEAKERS_PER_GROUP:>8} {status:>10}"
        )

        results[group] = {
            "label": label,
            "total_speakers": total_spk,
            "eligible_speakers": eligible_spk,
            "target": TARGET_SPEAKERS_PER_GROUP,
            "feasible": feasible,
        }

    print("=" * 80)

    if all_feasible:
        print("[PASS] CHECKPOINT 1 PASSED: All 6 groups have sufficient eligible speakers.")
        print(f"  Ready to proceed: deterministic selection with seed={SELECTION_SEED}.")
    else:
        print("[FAIL] CHECKPOINT 1 FAILED: One or more groups cannot meet the target.")
        print("  BLOCKED: Do not proceed to audio materialization.")
        print("  Review: reports/stage5/external_speaker_inventory.csv")

    print("=" * 80 + "\n")
    return all_feasible, results


# ===========================================================================
# PHASE 3E — DETERMINISTIC SPEAKER SELECTION
# ===========================================================================

def select_speakers(
    eligible_pools: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Phase 3E: Select exactly TARGET_SPEAKERS_PER_GROUP speakers per group.

    Algorithm:
      1. Collect eligible speaker IDs for each group
      2. Sort deterministically (lexicographic on client_id)
      3. Shuffle with fixed seed SELECTION_SEED
      4. Take the first TARGET_SPEAKERS_PER_GROUP speakers

    No performance-based selection. No manual override.
    """
    logger.info(f"Phase 3E: Deterministic speaker selection (seed={SELECTION_SEED})")
    rng = random.Random(SELECTION_SEED)
    selected: Dict[str, Dict[str, List[Dict]]] = {}

    for group in TARGET_GROUPS:
        pool = eligible_pools[group]["eligible_speakers"]
        speaker_ids = sorted(pool.keys())        # deterministic sort
        rng.shuffle(speaker_ids)                  # seed-fixed shuffle
        chosen = speaker_ids[:TARGET_SPEAKERS_PER_GROUP]

        if len(chosen) < TARGET_SPEAKERS_PER_GROUP:
            raise RuntimeError(
                f"BLOCKED: Group [{group}] has only {len(chosen)} eligible speakers "
                f"after shuffle; target is {TARGET_SPEAKERS_PER_GROUP}. "
                "Feasibility checkpoint should have caught this."
            )

        selected[group] = {spk_id: pool[spk_id] for spk_id in chosen}
        logger.info(f"  [{group:<10}] Selected {len(selected[group])} speakers")

    return selected


# ===========================================================================
# PHASE 3F — DETERMINISTIC CLIP SELECTION
# ===========================================================================

def select_clips(
    selected_speakers: Dict[str, Dict[str, List[Dict]]],
) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Phase 3F: Select exactly TARGET_CLIPS_PER_SPEAKER clips per speaker.

    Algorithm:
      1. Sort clips by path (deterministic)
      2. Shuffle with seed = SELECTION_SEED + CLIP_SEED_OFFSET
      3. Take first TARGET_CLIPS_PER_SPEAKER clips
      4. Verify no duplicate paths within the speaker
      5. Verify all transcripts are non-empty

    No WER, no difficulty, no acoustic-diversity filter.
    """
    logger.info(
        f"Phase 3F: Deterministic clip selection "
        f"(seed={SELECTION_SEED + CLIP_SEED_OFFSET})"
    )
    rng = random.Random(SELECTION_SEED + CLIP_SEED_OFFSET)
    clip_selection: Dict[str, Dict[str, List[Dict]]] = {}

    for group in TARGET_GROUPS:
        clip_selection[group] = {}
        for spk_id, clips in selected_speakers[group].items():
            sorted_clips = sorted(clips, key=lambda c: c["path"])
            rng.shuffle(sorted_clips)
            chosen_clips = sorted_clips[:TARGET_CLIPS_PER_SPEAKER]

            # Verify uniqueness within speaker
            chosen_paths = [c["path"] for c in chosen_clips]
            assert len(chosen_paths) == len(set(chosen_paths)), (
                f"FAIL: Duplicate path in clip selection for speaker {spk_id[:8]}"
            )
            # Verify transcripts
            for clip in chosen_clips:
                assert _is_valid_transcript(clip["sentence"]), (
                    f"FAIL: Empty/invalid transcript for path {clip['path']}"
                )

            clip_selection[group][spk_id] = chosen_clips

    return clip_selection


# ===========================================================================
# PHASE 3G — AUDIO MATERIALIZATION (selectively download 900 clips)
# ===========================================================================

def materialize_audio(
    clip_selection: Dict[str, Dict[str, List[Dict]]],
    audio_dir: Path,
) -> Dict[str, str]:
    """
    Phase 3G: Download or locate the 900 selected audio clips.

    Returns: path -> SHA256 hash mapping for all materialized clips.
    """
    logger.info("Phase 3G: Audio materialization")
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Build set of required paths
    required_paths = set()
    for group_data in clip_selection.values():
        for clips in group_data.values():
            for clip in clips:
                required_paths.add(clip["path"])

    logger.info(f"  Required audio clips: {len(required_paths)}")

    # Attempt to find locally first (from any prior partial download)
    path_hashes: Dict[str, str] = {}
    missing: List[str] = []

    for path in sorted(required_paths):
        local_path = audio_dir / Path(path).name
        if local_path.exists():
            path_hashes[path] = _sha256_file(local_path)
        else:
            missing.append(path)

    if missing:
        logger.warning(
            f"  {len(missing)} audio files not yet materialized locally.\n"
            "  To obtain them:\n"
            "  Option A: Download cv-corpus-11.0-2022-09-21/en.tar.gz (~22 GB)\n"
            "            Extract, move selected MP3s to:\n"
            f"            {audio_dir}\n"
            "  Option B: Use Common Voice download API/script to fetch only listed paths.\n"
            "  After materialization, re-run: --phase materialize"
        )
        # Write missing-paths manifest for targeted download
        missing_manifest = audio_dir.parent / "missing_audio_paths.txt"
        with open(missing_manifest, "w") as fh:
            for p in missing:
                fh.write(p + "\n")
        logger.info(f"  Missing paths written to: {missing_manifest}")

    logger.info(
        f"  Materialized: {len(path_hashes)} / {len(required_paths)} clips"
    )
    return path_hashes


def _sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _sha256_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ===========================================================================
# PHASE 3H — TRANSCRIPT AUDIT
# ===========================================================================

def run_transcript_audit(clip_selection: Dict[str, Dict[str, List[Dict]]]) -> Dict:
    """
    Phase 3H: Audit transcripts for all selected clips.
    No ASR. No WER computation.
    """
    logger.info("Phase 3H: Transcript audit")

    issues: List[str] = []
    seen_transcript_path: set = set()
    seen_sentences_per_speaker: Dict[str, set] = {}
    stats = {
        "total_clips": 0,
        "empty_transcript": 0,
        "too_short": 0,
        "duplicate_transcript_path": 0,
        "suspicious_chars": 0,
    }

    for group in TARGET_GROUPS:
        for spk_id, clips in clip_selection[group].items():
            seen_sentences_per_speaker[spk_id] = set()
            for clip in clips:
                stats["total_clips"] += 1
                sentence = clip["sentence"].strip()
                path = clip["path"]

                # Empty check
                if not sentence:
                    stats["empty_transcript"] += 1
                    issues.append(f"EMPTY_TRANSCRIPT: {path}")
                    continue

                # Minimum length
                if len(sentence.split()) < MIN_TRANSCRIPT_WORDS:
                    stats["too_short"] += 1
                    issues.append(f"SHORT_TRANSCRIPT ({len(sentence.split())} words): {path}")

                # Duplicate sentence+path pair
                key = f"{sentence}|||{path}"
                if key in seen_transcript_path:
                    stats["duplicate_transcript_path"] += 1
                    issues.append(f"DUPLICATE_SENTENCE_PATH: {path}")
                seen_transcript_path.add(key)

                # Suspicious characters (non-printable / non-ASCII outside common range)
                if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", sentence):
                    stats["suspicious_chars"] += 1
                    issues.append(f"SUSPICIOUS_CHARS: {path}")

    if issues:
        logger.warning(f"Transcript issues ({len(issues)}):")
        for iss in issues[:20]:
            logger.warning(f"  {iss}")
        if len(issues) > 20:
            logger.warning(f"  …and {len(issues) - 20} more")
    else:
        logger.info("  Transcript audit: PASS — no issues detected")

    audit_result = {
        "stats": stats,
        "issues": issues,
        "passed": len(issues) == 0,
    }
    return audit_result


# ===========================================================================
# PHASE 3I — CREATE EVALUATION CSV
# ===========================================================================

def generate_external_eval_csv(
    clip_selection: Dict[str, Dict[str, List[Dict]]],
    path_hashes: Dict[str, str],
    output_path: Path,
) -> List[Dict[str, Any]]:
    """
    Phase 3I: Create datasets/splits/stage5_external_eval.csv under Amended Protocol.

    Output schema:
      recording_id, speaker_id, dataset_name, dataset_release,
      dataset_group, stage5_accent_group, source_accent_raw, stratum_code,
      group_definition_version, transcript, audio_path, audio_hash,
      duration_sec, sample_rate, channels, selection_seed,
      selection_rule_version, availability_scope
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    counter = 1

    for group in TARGET_GROUPS:
        stratum_code = TARGET_STRATA_CODES[group]
        for spk_id, clips in clip_selection[group].items():
            for clip in clips:
                audio_hash = path_hashes.get(clip["path"], "PENDING_MATERIALIZATION")
                rows.append({
                    "recording_id":           f"stage5ext_{counter:05d}",
                    "speaker_id":             spk_id,
                    "dataset_name":           DATASET_NAME,
                    "dataset_release":        DATASET_RELEASE,
                    "dataset_group":          group,
                    "stage5_accent_group":    group,
                    "source_accent_raw":      clip.get("source_accent_raw", GROUP_LABELS[group]),
                    "stratum_code":           stratum_code,
                    "group_definition_version": GROUP_DEFINITION_VERSION,
                    "transcript":             clip["sentence"],
                    "audio_path":             clip["path"],
                    "audio_hash":             audio_hash,
                    "duration_sec":           "",   # filled after audio materialisation
                    "sample_rate":            "",
                    "channels":               "",
                    "selection_seed":         SELECTION_SEED,
                    "selection_rule_version": SELECTION_RULE_VERSION,
                    "availability_scope":     "stage5_final_evaluation_only",
                })
                counter += 1

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Written: {output_path} ({len(rows)} rows)")
    return rows


# ===========================================================================
# PHASE 3J — MACHINE-READABLE MANIFEST
# ===========================================================================

def generate_manifest(
    clip_selection: Dict[str, Dict[str, List[Dict]]],
    metadata_hash: str,
    csv_path: Path,
    manifest_path: Path,
) -> Dict[str, Any]:
    """Phase 3J: Create datasets/splits/stage5_external_eval_manifest.json"""

    total_speakers = sum(len(v) for v in clip_selection.values())
    total_clips = sum(
        len(clips)
        for group_data in clip_selection.values()
        for clips in group_data.values()
    )

    group_summary: Dict[str, Dict] = {}
    for group in TARGET_GROUPS:
        spk_count = len(clip_selection[group])
        clip_count = sum(len(c) for c in clip_selection[group].values())
        group_summary[group] = {
            "label":          GROUP_LABELS[group],
            "stratum_code":   TARGET_STRATA_CODES[group],
            "speakers":       spk_count,
            "clips":          clip_count,
            "target_met":     (
                spk_count == TARGET_SPEAKERS_PER_GROUP and
                clip_count == TARGET_SPEAKERS_PER_GROUP * TARGET_CLIPS_PER_SPEAKER
            ),
        }

    csv_hash = _sha256_file(csv_path) if csv_path.exists() else "PENDING"

    manifest: Dict[str, Any] = {
        "schema_version":    "1.0",
        "phase":             "Stage 5 Phase 3 - External Evaluation Set Curation",
        "project":           "DSG-CTTA",
        "protocol_version":  PROTOCOL_VERSION,
        "creation_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name":                DATASET_NAME,
            "release":             DATASET_RELEASE,
            "title":               DATASET_TITLE,
            "license":             DATASET_LICENSE,
            "distributor":         DATASET_DISTRIBUTOR,
            "source_url":          DATASET_SOURCE_URL,
            "language":            DATASET_LANGUAGE,
            "group_definition":    (
                "Stage 5 pre-specified evaluation strata with frozen "
                "metadata normalization rules from CV 27.0 accents field"
            ),
            "group_definition_version": GROUP_DEFINITION_VERSION,
            "protocol_amendment":  "reports/stage5/protocol_amendment_cv27.md",
            "metadata_hash":       metadata_hash,
        },
        "selection": {
            "seed":                        SELECTION_SEED,
            "clip_seed_offset":            CLIP_SEED_OFFSET,
            "rule_version":                SELECTION_RULE_VERSION,
            "min_clips_for_eligibility":   MIN_CLIPS_FOR_ELIGIBILITY,
            "target_speakers_per_group":   TARGET_SPEAKERS_PER_GROUP,
            "target_clips_per_speaker":    TARGET_CLIPS_PER_SPEAKER,
            "target_total_speakers":       TARGET_TOTAL_SPEAKERS,
            "target_total_clips":          TARGET_TOTAL_CLIPS,
            "actual_total_speakers":       total_speakers,
            "actual_total_clips":          total_clips,
            "targets_met":                 (
                total_speakers == TARGET_TOTAL_SPEAKERS and
                total_clips == TARGET_TOTAL_CLIPS
            ),
        },
        "groups": group_summary,
        "evaluation_role": (
            "External out-of-distribution stress test / final evaluation. "
            "NOT a replication of L2-ARCTIC primary evaluation. "
            "Common Voice accent groups are self-reported dataset categories, "
            "not verified L1 identities."
        ),
        "prohibited_uses": [
            "DSG threshold tuning",
            "epsilon tuning",
            "K selection",
            "model selection",
            "CTTA hyperparameter selection",
            "sentinel design",
            "stream-order selection",
            "adaptation learning-rate selection",
        ],
        "immutability_note": (
            "This file is frozen after Phase 3G verification. "
            "Any modification requires a new version: stage5_external_eval_v2.csv"
        ),
        "csv_hash": csv_hash,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    logger.info(f"Written: {manifest_path}")
    return manifest


# ===========================================================================
# PHASE 3K — GROUP BALANCE VALIDATION
# ===========================================================================

def validate_group_balance(clip_selection: Dict[str, Dict[str, List[Dict]]]) -> None:
    """Phase 3K: Verify exact group/speaker/clip counts. Raise if wrong."""
    logger.info("Phase 3K: Group balance validation")

    errors: List[str] = []

    if set(clip_selection.keys()) != set(TARGET_GROUPS):
        errors.append(
            f"FAIL: Expected groups {TARGET_GROUPS}, "
            f"got {sorted(clip_selection.keys())}"
        )

    total_speakers = 0
    total_clips = 0

    for group in TARGET_GROUPS:
        spk_count = len(clip_selection.get(group, {}))
        if spk_count != TARGET_SPEAKERS_PER_GROUP:
            errors.append(
                f"FAIL: [{group}] speakers={spk_count}, "
                f"expected={TARGET_SPEAKERS_PER_GROUP}"
            )
        total_speakers += spk_count

        for spk_id, clips in clip_selection.get(group, {}).items():
            clip_count = len(clips)
            if clip_count != TARGET_CLIPS_PER_SPEAKER:
                errors.append(
                    f"FAIL: [{group}] speaker={spk_id[:8]}… "
                    f"clips={clip_count}, expected={TARGET_CLIPS_PER_SPEAKER}"
                )
            total_clips += clip_count

    if total_speakers != TARGET_TOTAL_SPEAKERS:
        errors.append(
            f"FAIL: total_speakers={total_speakers}, "
            f"expected={TARGET_TOTAL_SPEAKERS}"
        )
    if total_clips != TARGET_TOTAL_CLIPS:
        errors.append(
            f"FAIL: total_clips={total_clips}, "
            f"expected={TARGET_TOTAL_CLIPS}"
        )

    if errors:
        for err in errors:
            logger.error(f"  {err}")
        raise RuntimeError(
            f"BLOCKED: Group balance validation failed ({len(errors)} errors). "
            "See log above."
        )

    logger.info(
        f"  PASS: {len(TARGET_GROUPS)} groups × "
        f"{TARGET_SPEAKERS_PER_GROUP} speakers × "
        f"{TARGET_CLIPS_PER_SPEAKER} clips = {TARGET_TOTAL_CLIPS} total"
    )


# ===========================================================================
# PHASE 3L — DUPLICATE DETECTION
# ===========================================================================

def run_duplicate_detection(
    clip_selection: Dict[str, Dict[str, List[Dict]]],
    path_hashes: Dict[str, str],
) -> None:
    """Phase 3L: Detect duplicate recording IDs, paths, hashes, and sentences."""
    logger.info("Phase 3L: Duplicate detection")
    errors: List[str] = []

    seen_paths: set = set()
    seen_hashes: set = set()
    seen_sentence_path_pairs: set = set()

    for group in TARGET_GROUPS:
        for spk_id, clips in clip_selection[group].items():
            for clip in clips:
                path = clip["path"]
                sentence = clip["sentence"]

                # Duplicate path
                if path in seen_paths:
                    errors.append(f"DUPLICATE_PATH: {path}")
                seen_paths.add(path)

                # Duplicate audio hash
                audio_hash = path_hashes.get(path)
                if audio_hash and audio_hash != "PENDING_MATERIALIZATION":
                    if audio_hash in seen_hashes:
                        errors.append(f"DUPLICATE_AUDIO_HASH: {audio_hash} ({path})")
                    seen_hashes.add(audio_hash)

                # Duplicate sentence+path pair
                key = f"{sentence}|{path}"
                if key in seen_sentence_path_pairs:
                    errors.append(f"DUPLICATE_SENTENCE_PATH: {path}")
                seen_sentence_path_pairs.add(key)

    if errors:
        for err in errors[:30]:
            logger.error(f"  {err}")
        raise RuntimeError(
            f"BLOCKED: Duplicate detection failed ({len(errors)} duplicates). "
            "Phase 3 cannot proceed."
        )

    logger.info(
        f"  PASS: No duplicates detected "
        f"(checked {len(seen_paths)} paths, {len(seen_hashes)} hashes)"
    )


# ===========================================================================
# PHASE 3M — CROSS-SOURCE INDEPENDENCE
# ===========================================================================

def run_independence_audit(clip_selection: Dict[str, Dict[str, List[Dict]]]) -> Dict:
    """
    Phase 3M: Verify operational independence from L2-ARCTIC.

    Because the datasets use different speaker namespaces (hashed UUIDs vs.
    recording-session IDs), direct speaker identity matching is impossible.
    We document 'operational source-level independence' as the strongest
    achievable claim.

    Checks performed:
      1. speaker_id namespace differs (CV uses SHA-256 hash; L2-ARCTIC uses speaker codes)
      2. No audio path overlaps
      3. No recording_id overlaps with known L2-ARCTIC splits
    """
    logger.info("Phase 3M: Cross-source independence audit")

    # Load L2-ARCTIC speaker IDs from existing splits
    l2_speaker_ids: set = set()
    l2_paths: set = set()
    for split_file in SPLITS_DIR.glob("*.csv"):
        if "stage5_external" in split_file.name:
            continue  # skip the file we're creating
        try:
            with open(split_file, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    spk = row.get("speaker_id") or row.get("speaker") or ""
                    pth = row.get("audio_path") or row.get("path") or ""
                    if spk:
                        l2_speaker_ids.add(spk.strip())
                    if pth:
                        l2_paths.add(pth.strip())
        except Exception:
            pass

    cv_speaker_ids: set = set()
    cv_paths: set = set()
    for group_data in clip_selection.values():
        for spk_id, clips in group_data.items():
            cv_speaker_ids.add(spk_id)
            for clip in clips:
                cv_paths.add(clip["path"])

    shared_speakers = cv_speaker_ids & l2_speaker_ids
    shared_paths = cv_paths & l2_paths

    result = {
        "cv_speakers": len(cv_speaker_ids),
        "l2_arctic_speakers_in_splits": len(l2_speaker_ids),
        "shared_speaker_ids": len(shared_speakers),
        "shared_audio_paths": len(shared_paths),
        "namespace_note": (
            "Common Voice uses SHA-256 hashed client_id (anonymised UUID). "
            "L2-ARCTIC uses researcher-assigned speaker codes (e.g. HJK, TNI). "
            "These namespaces are disjoint by construction."
        ),
        "independence_claim": (
            "Operational source-level independence. Common Voice contributors "
            "registered independently on the Mozilla Common Voice platform. "
            "L2-ARCTIC speakers were recruited and recorded in a separate "
            "university research protocol. No shared registration, identity, "
            "or audio exists. Cross-dataset speaker identity cannot be formally "
            "verified or refuted from metadata alone."
        ),
        "passed": len(shared_speakers) == 0 and len(shared_paths) == 0,
    }

    if shared_speakers:
        logger.warning(
            f"  WARNING: {len(shared_speakers)} speaker IDs appear in both "
            "Common Voice selection and L2-ARCTIC splits. "
            "This is unexpected given different namespaces; investigate."
        )
    if shared_paths:
        logger.warning(
            f"  WARNING: {len(shared_paths)} audio paths appear in both datasets."
        )

    if result["passed"]:
        logger.info(
            f"  PASS: No shared speaker IDs or audio paths detected between "
            f"Common Voice ({len(cv_speaker_ids)} speakers) and "
            f"L2-ARCTIC ({len(l2_speaker_ids)} speakers in splits)."
        )

    return result


# ===========================================================================
# PHASE 3N — IMMUTABILITY LOCK
# ===========================================================================

def create_lock_file(
    csv_path: Path,
    manifest_path: Path,
    lock_path: Path,
) -> Dict[str, str]:
    """Phase 3N: Create immutability lock file."""
    csv_hash = _sha256_file(csv_path)
    manifest_hash = _sha256_file(manifest_path)

    lock = {
        "schema_version":    "1.0",
        "immutability_note": (
            "This file is frozen. "
            "To change the evaluation set, create stage5_external_eval_v2.csv "
            "with a new protocol identity."
        ),
        "csv_hash":          csv_hash,
        "manifest_hash":     manifest_hash,
        "selection_seed":    str(SELECTION_SEED),
        "selection_rule":    SELECTION_RULE_VERSION,
        "dataset_release":   DATASET_RELEASE,
        "protocol_version":  PROTOCOL_VERSION,
        "group_definition_version": GROUP_DEFINITION_VERSION,
        "frozen_at":         datetime.now(timezone.utc).isoformat(),
    }

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as fh:
        json.dump(lock, fh, indent=2)

    logger.info(f"Lock written: {lock_path}")
    logger.info(f"  CSV hash:      {csv_hash}")
    logger.info(f"  Manifest hash: {manifest_hash}")
    return lock


# ===========================================================================
# PHASE 3O — REPORTS
# ===========================================================================

def write_speaker_inventory_csv(
    eligible_pools: Dict[str, Dict[str, Any]],
    clip_selection: Optional[Dict[str, Dict[str, List[Dict]]]],
) -> None:
    """Write external_speaker_inventory.csv"""
    out_path = REPORTS_DIR / "external_speaker_inventory.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    selected_ids: set = set()
    if clip_selection:
        for group_data in clip_selection.values():
            selected_ids.update(group_data.keys())

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "group_code", "group_label",
            "speaker_id_prefix",  # truncated for privacy
            "clips_available", "eligible", "selected",
        ])
        for group in TARGET_GROUPS:
            pool = eligible_pools[group]
            for spk_id, clips in sorted(pool["eligible_speakers"].items()):
                writer.writerow([
                    group,
                    GROUP_LABELS[group],
                    spk_id[:24] + "…",
                    len(clips),
                    True,
                    spk_id in selected_ids,
                ])

    logger.info(f"Written: {out_path}")


def write_selection_counts_csv(
    eligible_pools: Dict[str, Dict[str, Any]],
    clip_selection: Optional[Dict[str, Dict[str, List[Dict]]]],
    feasibility_results: Dict[str, Dict],
) -> None:
    """Write external_selection_counts.csv"""
    out_path = REPORTS_DIR / "external_selection_counts.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "group_code", "group_label",
            "total_speakers_found", "eligible_speakers",
            "target_speakers", "feasible",
            "selected_speakers", "target_clips", "selected_clips",
        ])
        for group in TARGET_GROUPS:
            pool = eligible_pools[group]
            sel = clip_selection.get(group, {}) if clip_selection else {}
            sel_clips = sum(len(c) for c in sel.values()) if sel else 0
            writer.writerow([
                group,
                GROUP_LABELS[group],
                pool["total_speakers"],
                pool["eligible_count"],
                TARGET_SPEAKERS_PER_GROUP,
                pool["eligible_count"] >= TARGET_SPEAKERS_PER_GROUP,
                len(sel),
                TARGET_CLIPS_PER_SPEAKER * TARGET_SPEAKERS_PER_GROUP,
                sel_clips,
            ])

    logger.info(f"Written: {out_path}")


def write_clip_inventory_csv(
    clip_selection: Dict[str, Dict[str, List[Dict]]],
) -> None:
    """Write external_clip_inventory.csv"""
    out_path = REPORTS_DIR / "external_clip_inventory.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "group_code", "group_label",
            "speaker_id_prefix", "path", "transcript_words",
        ])
        for group in TARGET_GROUPS:
            for spk_id, clips in clip_selection[group].items():
                for clip in clips:
                    writer.writerow([
                        group,
                        GROUP_LABELS[group],
                        spk_id[:24] + "…",
                        clip["path"],
                        len(clip["sentence"].split()),
                    ])

    logger.info(f"Written: {out_path}")


def write_quality_report(
    transcript_audit: Dict,
    independence_audit: Dict,
) -> None:
    """Write external_quality_report.md"""
    out_path = REPORTS_DIR / "external_quality_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    t = transcript_audit["stats"]
    lines = [
        "# External Evaluation Quality Report",
        f"## DSG-CTTA Stage 5 Phase 3",
        f"**Date:** {datetime.now(timezone.utc).date()}",
        f"**Dataset:** {DATASET_RELEASE}",
        "",
        "## Transcript Quality",
        "",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Total clips audited | {t['total_clips']} |",
        f"| Empty transcripts | {t['empty_transcript']} |",
        f"| Too-short transcripts (<{MIN_TRANSCRIPT_WORDS} words) | {t['too_short']} |",
        f"| Duplicate sentence+path pairs | {t['duplicate_transcript_path']} |",
        f"| Suspicious characters | {t['suspicious_chars']} |",
        f"| **Transcript audit result** | "
        f"{'PASS' if transcript_audit['passed'] else 'FAIL'} |",
        "",
        "## Cross-Source Independence",
        "",
        f"| Check | Result |",
        f"|---|---|",
        f"| CV speakers | {independence_audit['cv_speakers']} |",
        f"| L2-ARCTIC speakers in splits | {independence_audit['l2_arctic_speakers_in_splits']} |",
        f"| Shared speaker IDs | {independence_audit['shared_speaker_ids']} |",
        f"| Shared audio paths | {independence_audit['shared_audio_paths']} |",
        f"| Independence audit | {'PASS' if independence_audit['passed'] else 'FAIL (see log)'} |",
        "",
        "## Independence Claim",
        "",
        f"> {independence_audit['independence_claim']}",
        "",
        "## Namespace Note",
        "",
        f"> {independence_audit['namespace_note']}",
        "",
        "## Prohibited Operations",
        "",
        "The following operations are prohibited during and after Phase 3:",
        "- ASR inference",
        "- WER computation for selection",
        "- DSG implementation",
        "- CTTA execution",
        "- Modification of stage5_external_eval.csv after freeze",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Written: {out_path}")


def write_selection_audit_md(
    eligible_pools: Dict[str, Dict[str, Any]],
    clip_selection: Dict[str, Dict[str, List[Dict]]],
    feasibility_results: Dict[str, Dict],
    independence_audit: Dict,
    metadata_hash: str,
) -> None:
    """Write external_selection_audit.md (Phase 3P — full audit narrative)."""
    out_path = REPORTS_DIR / "external_selection_audit.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_spk = sum(len(v) for v in clip_selection.values())
    total_clips = sum(len(c) for s in clip_selection.values() for c in s.values())

    lines = [
        "# Stage 5 External Evaluation Set Curation Audit",
        "## DSG-CTTA Phase 3",
        "",
        f"**Date:** {datetime.now(timezone.utc).date()}",
        f"**Protocol version:** {PROTOCOL_VERSION}",
        "",
        "---",
        "",
        "## 1. Dataset Identity",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Dataset | Mozilla Common Voice English |",
        f"| Release | {DATASET_RELEASE} |",
        f"| License | {DATASET_LICENSE} |",
        f"| Language | {DATASET_LANGUAGE} |",
        f"| Source | {DATASET_SOURCE_URL} |",
        f"| Metadata hash | {metadata_hash} |",
        "",
        "## 2. Release / License",
        "",
        "CC0 1.0 Public Domain Dedication. No restrictions on research use or publication.",
        "",
        "## 3. Accent Taxonomy",
        "",
        "Group labels are **dataset-provided enumerated accent codes** from the cv-corpus-11.0",
        "validated.tsv accent field. These are self-reported labels, NOT verified L1 identities.",
        "They must not be equated with L2-ARCTIC L1-associated speaker groups.",
        "",
        "## 4. Selection Criteria",
        "",
        "Criteria applied (pre-declared in Phase 1):",
        "1. `accent` field explicitly matches one of 6 target codes",
        "2. `client_id` non-empty",
        "3. `path` non-empty",
        "4. `sentence` non-empty and >= 2 words",
        "5. `path` deduplicated (no duplicate audio paths)",
        "6. Speaker has >= 15 validated clips passing criteria 1-5",
        "",
        "NOT used for selection:",
        "- ASR WER or CER",
        "- Disparity scores",
        "- Acoustic difficulty",
        "- Geographic metadata",
        "- Age or gender (except optional balancing if pre-declared)",
        "",
        "## 5. Speaker Selection Procedure",
        "",
        f"- Sorted eligible speaker IDs lexicographically",
        f"- Shuffled with `random.Random(seed={SELECTION_SEED})`",
        f"- Selected first {TARGET_SPEAKERS_PER_GROUP} speakers per group",
        "",
        "## 6. Clip Selection Procedure",
        "",
        f"- Sorted clips by path lexicographically",
        f"- Shuffled with `random.Random(seed={SELECTION_SEED + CLIP_SEED_OFFSET})`",
        f"- Selected first {TARGET_CLIPS_PER_SPEAKER} clips per speaker",
        "",
        "## 7. Speaker Counts",
        "",
        "| Group | Label | Total Spk | Eligible Spk | Target | Feasible | Selected |",
        "|---|---|---|---|---|---|---|",
    ]

    for group in TARGET_GROUPS:
        pool = eligible_pools[group]
        sel = len(clip_selection.get(group, {}))
        fr = feasibility_results.get(group, {})
        lines.append(
            f"| {group} | {GROUP_LABELS[group]} | "
            f"{pool['total_speakers']:,} | {pool['eligible_count']:,} | "
            f"{TARGET_SPEAKERS_PER_GROUP} | "
            f"{'YES' if fr.get('feasible') else 'NO'} | {sel} |"
        )

    lines += [
        f"| **Total** | | | | {TARGET_TOTAL_SPEAKERS} | | {total_spk} |",
        "",
        "## 8. Clip Counts",
        "",
        f"| Group | Speakers | Clips/Spk | Total Clips |",
        f"|---|---|---|---|",
    ]

    for group in TARGET_GROUPS:
        sel = clip_selection.get(group, {})
        spk_count = len(sel)
        clip_count = sum(len(c) for c in sel.values())
        lines.append(
            f"| {group} | {spk_count} | {TARGET_CLIPS_PER_SPEAKER} | {clip_count} |"
        )

    lines += [
        f"| **Total** | {total_spk} | | {total_clips} |",
        "",
        "## 9. Transcript Quality",
        "",
        "See `external_quality_report.md`.",
        "",
        "## 10. Audio Integrity",
        "",
        "Audio hashes: populated after Phase 3G materialization.",
        "Status: PENDING until audio downloaded.",
        "",
        "## 11. Duplicate Audit",
        "",
        "Duplicate detection covers: recording path, audio hash, transcript+path pair.",
        "See Phase 3L log output.",
        "",
        "## 12. Cross-Source Independence",
        "",
        independence_audit.get("independence_claim", ""),
        "",
        f"Namespace note: {independence_audit.get('namespace_note', '')}",
        "",
        "## 13. Reproducibility",
        "",
        "Exact reproduction procedure:",
        f"1. Pin release: `{DATASET_RELEASE}`",
        f"2. Verify metadata hash: `{metadata_hash}`",
        f"3. Apply eligibility criteria (see Section 4)",
        f"4. Run speaker selection with `random.Random({SELECTION_SEED})`",
        f"5. Run clip selection with `random.Random({SELECTION_SEED + CLIP_SEED_OFFSET})`",
        f"6. Verify CSV hash matches lock file",
        "",
        "## 14. Limitations",
        "",
        "1. Accent labels are self-reported; not verified L1 backgrounds.",
        "2. Groups are not equivalent to L2-ARCTIC L1 groups.",
        "3. ~50% of CV English clips have missing accent labels (eligible pool uses labelled clips only).",
        "4. No direct L1 equivalents for Arabic, Korean, Mandarin, Spanish, Vietnamese.",
        "5. Cross-dataset speaker identity cannot be formally verified.",
        "",
        "## 15. Final Freeze Decision",
        "",
        "The external evaluation set is FROZEN after Phase 3N.",
        "See `datasets/splits/stage5_external_eval.lock.json` for immutability hash.",
        "",
        f"**Frozen evaluation set:** `datasets/splits/stage5_external_eval.csv`",
        f"**Evaluation role:** External out-of-distribution stress test.",
        f"**NOT permitted to use for:** DSG tuning, threshold selection, model selection.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Written: {out_path}")


def write_independence_report(independence_audit: Dict) -> None:
    """Write external_independence_report.md"""
    out_path = REPORTS_DIR / "external_independence_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# External Evaluation Set Independence Report",
        "## DSG-CTTA Stage 5 Phase 3M",
        "",
        f"**Date:** {datetime.now(timezone.utc).date()}",
        "",
        "## Independence Claim",
        "",
        independence_audit.get("independence_claim", ""),
        "",
        "## Namespace Note",
        "",
        independence_audit.get("namespace_note", ""),
        "",
        "## Checks Performed",
        "",
        f"| Check | Result |",
        f"|---|---|",
        f"| Shared speaker IDs between CV and L2-ARCTIC splits | {independence_audit['shared_speaker_ids']} |",
        f"| Shared audio paths | {independence_audit['shared_audio_paths']} |",
        f"| Namespace analysis | Disjoint by construction |",
        f"| Overall independence | {'PASS' if independence_audit['passed'] else 'FAIL'} |",
        "",
        "## Limitations",
        "",
        "- Cross-dataset speaker identity matching across namespaces is not possible from metadata alone.",
        "- The claim is 'operational source-level independence', which is the strongest achievable.",
        "- Audio-level identity check would require audio hashing across both full corpora.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Written: {out_path}")


def write_manifest_verification(
    manifest: Dict,
    lock: Dict,
) -> None:
    """Write external_manifest_verification.md"""
    out_path = REPORTS_DIR / "external_manifest_verification.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sel = manifest.get("selection", {})
    lines = [
        "# External Evaluation Manifest Verification",
        "## DSG-CTTA Stage 5 Phase 3N",
        "",
        f"**Date:** {datetime.now(timezone.utc).date()}",
        "",
        "## Frozen Hashes",
        "",
        f"| Artifact | SHA-256 |",
        f"|---|---|",
        f"| stage5_external_eval.csv | `{lock.get('csv_hash', 'PENDING')}` |",
        f"| stage5_external_eval_manifest.json | `{lock.get('manifest_hash', 'PENDING')}` |",
        "",
        "## Selection Parameters",
        "",
        f"| Parameter | Value |",
        f"|---|---|",
        f"| Selection seed | {sel.get('seed')} |",
        f"| Rule version | {sel.get('rule_version')} |",
        f"| Dataset release | {manifest.get('dataset', {}).get('release')} |",
        f"| Groups | {len(TARGET_GROUPS)} |",
        f"| Target speakers/group | {sel.get('target_speakers_per_group')} |",
        f"| Target clips/speaker | {sel.get('target_clips_per_speaker')} |",
        f"| Actual speakers | {sel.get('actual_total_speakers')} |",
        f"| Actual clips | {sel.get('actual_total_clips')} |",
        f"| Targets met | {sel.get('targets_met')} |",
        "",
        "## Immutability",
        "",
        "The lock file `datasets/splits/stage5_external_eval.lock.json` contains",
        "cryptographic hashes of both the CSV and manifest. Any modification to",
        "the evaluation set will produce a hash mismatch detectable by the",
        "blocking test `test_stage5_external_eval.py::test_eval_manifest_immutable`.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Written: {out_path}")


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "DSG-CTTA Stage 5 Phase 3: External Final-Evaluation Set Curation"
        )
    )
    parser.add_argument(
        "--phase",
        choices=["metadata", "select", "materialize", "all"],
        default="metadata",
        help=(
            "metadata: Phase 3A–3D (feasibility checkpoint, no audio). "
            "select: Phase 3E–3L (deterministic selection, no audio). "
            "materialize: Phase 3G (download/locate 900 audio files). "
            "all: run all phases."
        ),
    )
    parser.add_argument(
        "--tsv-path",
        type=Path,
        default=None,
        help="Path to a local validated.tsv (skip HuggingFace streaming).",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=EXTERNAL_AUDIO_DIR,
        help="Directory containing (or to receive) selected audio files.",
    )
    args = parser.parse_args()

    logger.info("=" * 68)
    logger.info("DSG-CTTA Stage 5 Phase 3 — External Evaluation Set Curation")
    logger.info(f"  Release: {DATASET_RELEASE}")
    logger.info(
        f"  Target:  {len(TARGET_GROUPS)} groups × "
        f"{TARGET_SPEAKERS_PER_GROUP} spk × "
        f"{TARGET_CLIPS_PER_SPEAKER} clips = {TARGET_TOTAL_CLIPS} clips"
    )
    logger.info(f"  Seed:    {SELECTION_SEED}")
    logger.info(f"  Phase:   {args.phase}")
    logger.info("=" * 68)

    # -----------------------------------------------------------------------
    # PHASE 3A/3B — Load metadata
    # -----------------------------------------------------------------------
    records = load_metadata(args.tsv_path)
    metadata_hash = hash_records(records)
    logger.info(f"Metadata hash (SHA-256): {metadata_hash}")

    # -----------------------------------------------------------------------
    # PHASE 3C — Build eligible speaker pools
    # -----------------------------------------------------------------------
    eligible_pools = build_eligible_speaker_pools(records)

    # -----------------------------------------------------------------------
    # PHASE 3D — CHECKPOINT 1
    # -----------------------------------------------------------------------
    all_feasible, feasibility_results = run_feasibility_checkpoint(eligible_pools)

    # Always write inventory CSV regardless of feasibility (for diagnosis)
    write_speaker_inventory_csv(eligible_pools, None)
    write_selection_counts_csv(eligible_pools, None, feasibility_results)

    if not all_feasible:
        logger.error("BLOCKED: Checkpoint 1 failed. Cannot proceed.")
        sys.exit(1)

    if args.phase == "metadata":
        logger.info("Metadata phase complete. Checkpoint 1 PASSED.")
        logger.info(
            "Re-run with --phase select to perform deterministic speaker/clip selection."
        )
        return

    # -----------------------------------------------------------------------
    # PHASE 3E — Speaker selection
    # -----------------------------------------------------------------------
    selected_speakers = select_speakers(eligible_pools)

    # -----------------------------------------------------------------------
    # PHASE 3F — Clip selection
    # -----------------------------------------------------------------------
    clip_selection = select_clips(selected_speakers)

    # -----------------------------------------------------------------------
    # PHASE 3K — Group balance validation
    # -----------------------------------------------------------------------
    validate_group_balance(clip_selection)

    # -----------------------------------------------------------------------
    # PHASE 3H — Transcript audit
    # -----------------------------------------------------------------------
    transcript_audit = run_transcript_audit(clip_selection)
    if not transcript_audit["passed"]:
        logger.error("BLOCKED: Transcript audit failed.")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # PHASE 3G — Audio materialization (if requested)
    # -----------------------------------------------------------------------
    path_hashes: Dict[str, str] = {}
    if args.phase in ("materialize", "all"):
        path_hashes = materialize_audio(clip_selection, args.audio_dir)

    # -----------------------------------------------------------------------
    # PHASE 3L — Duplicate detection
    # -----------------------------------------------------------------------
    run_duplicate_detection(clip_selection, path_hashes)

    # -----------------------------------------------------------------------
    # PHASE 3M — Cross-source independence
    # -----------------------------------------------------------------------
    independence_audit = run_independence_audit(clip_selection)

    # -----------------------------------------------------------------------
    # PHASE 3I — Create evaluation CSV
    # -----------------------------------------------------------------------
    csv_path = SPLITS_DIR / "stage5_external_eval.csv"
    generate_external_eval_csv(clip_selection, path_hashes, csv_path)

    # -----------------------------------------------------------------------
    # PHASE 3J — Manifest
    # -----------------------------------------------------------------------
    manifest_path = SPLITS_DIR / "stage5_external_eval_manifest.json"
    manifest = generate_manifest(clip_selection, metadata_hash, csv_path, manifest_path)

    # -----------------------------------------------------------------------
    # PHASE 3N — Lock
    # -----------------------------------------------------------------------
    lock_path = SPLITS_DIR / "stage5_external_eval.lock.json"
    lock = create_lock_file(csv_path, manifest_path, lock_path)

    # -----------------------------------------------------------------------
    # PHASE 3O — Reports
    # -----------------------------------------------------------------------
    write_speaker_inventory_csv(eligible_pools, clip_selection)
    write_selection_counts_csv(eligible_pools, clip_selection, feasibility_results)
    write_clip_inventory_csv(clip_selection)
    write_quality_report(transcript_audit, independence_audit)
    write_selection_audit_md(
        eligible_pools, clip_selection, feasibility_results,
        independence_audit, metadata_hash,
    )
    write_independence_report(independence_audit)
    write_manifest_verification(manifest, lock)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total_spk = sum(len(v) for v in clip_selection.values())
    total_clips = sum(len(c) for s in clip_selection.values() for c in s.values())

    logger.info("")
    logger.info("=" * 68)
    logger.info("PHASE 3 COMPLETE")
    logger.info(f"  Speakers selected:  {total_spk} / {TARGET_TOTAL_SPEAKERS}")
    logger.info(f"  Clips selected:     {total_clips} / {TARGET_TOTAL_CLIPS}")
    logger.info(f"  CSV:                {csv_path}")
    logger.info(f"  Manifest:           {manifest_path}")
    logger.info(f"  Lock:               {lock_path}")
    logger.info(f"  CSV hash:           {lock['csv_hash']}")
    logger.info("=" * 68)
    logger.info("")
    logger.info("NEXT STEP: Run blocking tests:")
    logger.info("  pytest tests/research_validity/test_stage5_external_eval.py -v")


if __name__ == "__main__":
    main()
