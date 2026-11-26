---
name: speech-dataset-provenance
description: Audit speech-corpus metadata, speaker-disjoint splits, accent/group labels, audio integrity, licensing, manifests, checksums, and label isolation; use when curating or validating speech datasets.
---

# Speech Dataset and Provenance Engineering

## Mission
Make the dataset and labels scientifically defensible, traceable and privacy-conscious. Every population claim must be supported by the exact source release and curation evidence.

## Workflow
1. Identify the official corpus name, release ID/date, distributor, license, download/source location and source-file hashes. Do not silently substitute mirrors or corpus versions.
2. Inspect the original schema and data dictionary. Preserve raw metadata values alongside any transformed fields. Document normalization and grouping rules as versioned, deterministic mappings.
3. Use the dataset's validated self-reported accent/variety labels where available. Never infer accent from country, nationality, location, L1 or language code unless the dataset explicitly validates that mapping. If group labels are regional or native-region labels, call them that—not accents.
4. Define eligibility before examining model outcomes. Record exclusions with reasons and counts. No performance-based sample filtering.
5. Deduplicate and partition at the speaker level. Prove pairwise disjointness among development, calibration, sentinel, adaptation, validation and confirmatory partitions. Also check shared recordings, sentences/prompts and other leakage channels where relevant.
6. Preserve speaker-group consistency. Detect conflicting group declarations and apply the pre-registered policy; never force a speaker into a convenient group.
7. Validate audio: path existence, container/codec, sampling rate, duration, frame continuity where measurable, decode success, finite samples, channel handling and checksums. Distinguish physical bitstream integrity from duration-estimator discrepancies and from original-master completeness.
8. Generate deterministic manifests with schema version, seed, selection algorithm, record counts, speaker counts per group, clip counts per speaker, file sizes and SHA-256. Keep rejected/quarantined assets with reason codes in a separate ledger.
9. Protect transcript labels. Online adaptation inputs must not contain reference text, reference word counts or fields that permit accidental label access. Do not print sealed transcript strings or sensitive speaker IDs.
10. Before cross-corpus combination, construct a crossed source-by-group design. Ensure each target group is represented across sources and model corpus/source effects explicitly. Avoid designs where one corpus corresponds to only one accent stratum.
11. Check license conditions, participant consent/privacy restrictions, redistribution limits and whether audio/transcripts may be uploaded to third-party services.

## Stage 6M-specific rules
- The Stage 6M v1.5 grouping rules mapped five Common Voice 27.0 self-reported categories to Australian, Canadian, England, South Asian and US English. Preserve the exact raw field and rule version.
- Irish English was excluded from the final five-stratum confirmatory family after documented capacity/exposure constraints; do not quietly reintroduce it into the frozen results.
- The original-material completeness claim was not established by the physical-file checks described in prior reports. Use carefully scoped wording such as “Common Voice 27.0 as distributed” unless stronger source evidence exists.

## Required deliverables
Create a data card, source provenance table, group mapping specification, exclusion flowchart/table, split-leakage report, audio-integrity report, manifest schema and machine-readable hash catalogue. Every count must be reproducible from source files.

## Stop conditions
Stop if the source release is ambiguous, license is unclear, group mapping is unsupported, speaker overlap exists, hashes mismatch, label isolation fails or a proposed cross-corpus design confounds source with group. Report the blocker; do not silently repair the dataset.
