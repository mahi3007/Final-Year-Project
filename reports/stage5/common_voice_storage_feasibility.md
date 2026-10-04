# Common Voice Storage and Download Feasibility
## DSG-CTTA Stage 5 Phase 1

**Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Purpose:** Estimate storage, download, and processing costs for Common Voice English
without downloading the full corpus in this phase.

---

## 1. Full English Archive (cv-corpus-11.0)

| Metric | Estimate | Basis |
|---|---|---|
| Total validated English clips | ~1,180,000 clips | Published statistics |
| Average clip duration | ~5.3 seconds | Community analyses; platform documentation |
| Total validated audio hours | ~1,738 hours (validated subset) | Derived from clip count * avg duration |
| MP3 bitrate (approx.) | ~24 kbps (Common Voice default) | Archive inspection documentation |
| Audio size per clip | ~16 KB avg (5.3s * 24kbps) | Calculated |
| Total audio size (validated) | ~18-22 GB | Estimated from clip count |
| TSV metadata file size | ~200-500 MB (validated.tsv alone) | Typical for ~1M row TSV |
| Full English archive size (audio + metadata) | ~20-25 GB compressed | Published/community reports |
| CPU time to process metadata only (post-download) | ~5-15 minutes | Pandas on modern laptop |

---

## 2. Metadata-Only Extraction (Post-Download)

| Operation | Est. Duration | Storage Required |
|---|---|---|
| Download full English archive | ~2-4 hours (at 50 Mbps connection) | ~22 GB temp storage |
| Extract archive | ~10-20 minutes | ~45-50 GB (compressed + extracted) |
| Extract validated.tsv from archive | Immediate | ~200-500 MB |
| Delete audio clips (after TSV extraction) | Immediate | Frees ~21-24 GB |
| Analyse validated.tsv in Python/Pandas | ~2-5 minutes | <1 GB RAM |
| Generate accent-filtered manifest | <1 minute | <10 MB |

**IMPORTANT:** There is no official metadata-only (TSV-only) download. Full archive download
is required before metadata can be inspected. After extracting the TSV file, audio can be
deleted if only metadata analysis is needed in Phase 1.

---

## 3. Stage 5 Evaluation Subset (Phase 3, Future)

For the proposed external evaluation subset (10 speakers/group x 6 groups x 15 clips/speaker):

| Metric | Estimate |
|---|---|
| Target clips | ~900 clips |
| Clip duration | ~5.3 sec avg |
| Total audio duration | ~80 minutes |
| Audio size at 24 kbps MP3 | ~14-18 MB |
| Audio size at typical quality MP3 | ~80-100 MB |
| Metadata manifest size | <1 MB (CSV) |
| Total subset storage requirement | ~80-100 MB audio + <1 MB manifest |
| Processing time (6 ASR models) | ~2-4 hours per model; ~12-24 hours total |
| RAM requirement (Wav2Vec2-base) | ~2-4 GB GPU VRAM or ~8 GB CPU RAM |
| Laptop feasibility | YES (modern laptop sufficient) |

---

## 4. Download and Access Requirements

| Requirement | Status |
|---|---|
| Account required | YES: Mozilla Data Collective account required (free registration) |
| Registration URL | https://datacollective.mozillafoundation.org/ |
| Terms of Service | CC0 dataset; Mozilla ToS requires agreement before download |
| API access | NO: No public API for metadata retrieval; manual download only |
| Direct TSV download without audio | NOT AVAILABLE: Archive bundles audio + metadata |
| Streaming subset download | NOT SUPPORTED by official platform |

---

## 5. Phase 1 vs. Phase 3 Storage Comparison

| Phase | Data Required | Storage Required | Action |
|---|---|---|---|
| Phase 1 (current) | TSV metadata only | 0 GB (using estimated statistics from published research) | COMPLETE: No download required |
| Phase 2 (selection) | TSV metadata | ~22 GB download + 500 MB extract + delete audio | Download archive; extract TSV; delete audio |
| Phase 3 (subset curation) | Selected audio clips (~900) | ~80-100 MB | Download only selected clips or extract from archive |

---

## 6. Conclusion

Downloading and processing Common Voice English (cv-corpus-11.0) for Stage 5 external
evaluation is feasible on a standard research laptop:

- Phase 1 (metadata audit): COMPLETE without any download.
- Phase 3 (subset curation): Requires ~22 GB temporary disk space for archive download;
  final subset will be ~80-100 MB audio.
- Processing time for all 6 ASR models on the evaluation subset: ~12-24 hours on CPU;
  ~4-8 hours with GPU acceleration.
- No special hardware or cluster access is required.

**Storage feasibility result: FEASIBLE**
