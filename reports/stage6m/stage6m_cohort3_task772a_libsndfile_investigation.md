# Stage 6M Task 7.7.2A: libsndfile / mpg123 Duration Estimation Forensic Investigation

**Task ID:** Task 7.7.2A
**Document ID:** STAGE6M-TASK772A-LIBSNDFILE-INVESTIGATION
**Generated At:** 2026-11-06T09:46:10.539195+00:00
**Protocol Status:** APPROVED INVESTIGATION COMPLETED

---

## Executive Summary

Task 7.7.2A was authorized to establish the exact root cause of the duration/sample shortfall observed
between `soundfile.SoundFile.frames` (container declared frames) and actual decoded audio samples across
Cohort 3 MP3 recordings, and specifically the 1,977-sample shortfall on representative recording `common_voice_en_21552119.mp3`.

### Key Findings:
1. **Root Cause Identified (H1 Confirmed):** `soundfile` loads `libsndfile` 1.2.2, which delegates MPEG Layer III reading
   to an embedded `libmpg123` build (`src/mpeg_decode.c:521`). During stream opening, libsndfile calls `mpg123_length()`.
   When an Info/Xing frame is absent, `mpg123_length()` computes track length from file size:
   $$\text{length} = \left\lfloor \frac{\text{filelen}}{\text{bpf}} \times 1152 \right\rfloor$$
   Crucially, `filelen` is the **total file size in bytes** on disk, including ID3v2 tags and container wrappers.
   Because `length > 0`, libsndfile **never calls `mpg123_scan()`**.
2. **100% Mathematical Reconciliation of Representative Recording:**
   - Clip: `common_voice_en_21552119.mp3` (SHA-256: `b4f61be7a96876958890f364a8c42beb7c39a0e845a3ad9b13964330ed569613`)
   - Total file size: `39045` bytes; ID3v2 tag: `175` bytes; Audio data: `38870` bytes.
   - Physical MPEG frames: `186` frames @ 64 kbps CBR, 44,100 Hz.
   - True PCM capacity: `214272` samples. Actual decoded samples across all 3 decoders: `214272` samples.
   - SoundFile declared frames: `216249` frames.
   - Discrepancy: `1977` samples (44.83 ms).
   - **Exact decomposition:**
     - ID3v2 tag contribution: $\lfloor 175 / 208 \times 1152 \rfloor = 969$ spurious samples.
     - Frame padding/integer BPF rounding: $\lfloor 38870 / 208 \times 1152 \rfloor - 214272 = 215280 - 214272 = 1,008$ spurious samples.
     - Total spurious samples: $969 + 1008 = 1,977$ samples (Residual: **0 samples**).
3. **Generalization Across All 130 Quarantined Recordings (100.0% Match Rate):**
   - 78 recordings at 64 kbps (44.1 kHz): 78 / 78 (100.0%) match $\lfloor \text{file_size} / 208.0 \times 1152 \rfloor$ exactly (residual = 0).
   - 52 recordings at 48 kbps (32.0 kHz): 52 / 52 (100.0%) match $\lfloor \text{file_size} / 216.0 \times 1152 \rfloor$ exactly (residual = 0).
   - Overall formula match: **130 / 130 (100.0%)**.
4. **Controlled Synthetic Matrix Verification:** Verified across 11 controlled synthetic test cases covering
   headerless CBR, varying ID3v2 tag sizes (128B, 1024B, 4096B), valid Xing/Info headers, VBR with/without Info headers,
   malformed Xing headers, mid-frame truncation, and exact frame-boundary truncation.

---

## Runtime & Binary Provenance

| Component | Provenance / Build Details | Assessment |
|:--|:--|:--|
| Python | `3.11.9` (win32) | Verified |
| soundfile | `0.14.0` | Verified |
| libsndfile | `1.2.2` | Verified |
| Loaded DLL Path | `C:\Users\venka\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\_soundfile_data\libsndfile_x64.dll` | Verified |
| Loaded DLL SHA-256 | `22518c16f9d13eda5ae5adf999c4740d7d16cc2d6b178b36dd4ac2f759a38559` | Verified |
| Loaded DLL Size | `2,364,416 bytes` (verified from disk image via `GetModuleFileNameW`) | Verified |
| mpg123 Linkage | `libmpg123 statically linked into libsndfile_x64.dll via vcpkg port (x64-windows). Archive build tree path: C:\vcpkg\buildtrees\mpg123\src\-66150af195.clean\src\libmpg123\` | Strongly supported |
| Upstream mpg123 Commit/Tag | `vcpkg buildtree -66150af195 (commit SHA unstated in binary)` | Partially verified |
| PyAV | `18.1.0` (FFmpeg backend) | Verified |
| miniaudio | `1.71` | Verified |

> [!NOTE]
> **Provenance Qualification:** Runtime DLL identity: verified. Static linkage: strongly supported. Exact mpg123 source revision and binary correspondence: partially verified.
> `libmpg123` is statically compiled directly into `libsndfile_x64.dll` without external DLL dependencies.
> Static linkage is established by internal `INT123_` symbols and embedded buildtree path strings in the PE binary image.
> However, because the upstream Git commit SHA and source archive checksum are not embedded in PE metadata,
> exact source-to-binary correspondence is formally designated as **partially verified**.

> [!NOTE]
> **DLL Size & Hash Reconciliation:** Single-operation measurement directly on `C:\Users\venka\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\_soundfile_data\libsndfile_x64.dll`
> establishes that the binary is exactly **2,364,416 bytes** with SHA-256 `22518c16f9d13eda5ae5adf999c4740d7d16cc2d6b178b36dd4ac2f759a38559`.
> An earlier package reported 1,073,664 bytes for this same SHA-256; that intermediate figure was a clerical transcription error.
> The physical DLL image on disk has not changed.

---

## Source-Equivalent 130-Recording Formula Validation

In `libmpg123/libmpg123.c` line 37229:
```c
/* A bad estimate. Ignoring tags 'n stuff. */
double bpf = mh->mean_framesize ? mh->mean_framesize : compute_bpf(mh);
length = (off_t)((double)(mh->rdat.filelen)/bpf*mh->spf);
```

### Branch Determination:
- **State of `mh->mean_framesize`:** At the time `sf_open()` calls `mpg123_length()`, only the initial frame header
  has been read; no track scan has been performed. Therefore, `mh->mean_framesize == 0.0`.
- **Active Branch:** The conditional takes the **`compute_bpf(mh)`** branch.
- **Selected BPF Values:**
  - For MPEG-1 Layer III, 64 kbps @ 44.1 kHz: $\text{bpf} = \lfloor 144 \times 64000 / 44100 \rfloor = 208.0$ bytes.
  - For MPEG-1 Layer III, 48 kbps @ 32.0 kHz: $\text{bpf} = \lfloor 144 \times 48000 / 32000 \rfloor = 216.0$ bytes.
- **Formula Exactness:** Every single one of the 130 quarantined recordings matches the calculation
  $$\lfloor \text{filelen} / \text{bpf} \times 1152 \rfloor$$ with a **residual of exactly 0 frames** (130 / 130 = 100.0%).

| Stratum / Bitrate | Sample Rate | Selected BPF | Clip Count | Formula Matches | Residual | Match Rate |
|:--|:--|:--|:--|:--|:--|:--|
| 64 kbps CBR | 44,100 Hz | 208.0 | 78 | 78 | 0 frames | 100.0% |
| 48 kbps CBR | 32,000 Hz | 216.0 | 52 | 52 | 0 frames | 100.0% |
| **Total** | | | **130** | **130** | **0 frames** | **100.0%** |

> [!NOTE]
> Complete per-recording data (filename, size, sample rate, bitrate, selected BPF, declared frames,
> calculated frames, and residual) for all 130 recordings is embedded in `reports/stage6m/stage6m_cohort3_task772a_libsndfile_investigation.json`
> under `quarantined_130_recordings_analysis.per_recording_formula_reconciliation` for independent auditability.

---

## Numerical Reconciliation: Representative Recording

- **File:** `common_voice_en_21552119.mp3`
- **SHA-256:** `b4f61be7a96876958890f364a8c42beb7c39a0e845a3ad9b13964330ed569613`
- **Sample Rate:** `44100` Hz (mono)
- **Dominant Bitrate:** `64` kbps (100% Constant Bitrate across all frames)
- **Physical MPEG Frames:** `186` frames
- **Physical PCM Capacity:** `214272` samples
- **Actual Decoded Samples (SoundFile):** `214272` samples
- **Actual Decoded Samples (PyAV):** `214272` samples
- **Actual Decoded Samples (miniaudio):** `214272` samples
- **Decoder Agreement:** Exact 3-way sample agreement (100% match)
- **SoundFile Declared Frames:** `216249` frames
- **Shortfall:** `1977` samples (44.83 ms)

### Exact Root-Cause Decomposition

1. For MPEG-1 Layer 3, 64 kbps @ 44.1 kHz, unpadded frame size is $bpf = 208$ bytes.
2. Total file size $39,045$ bytes / $208 \times 1152 = 216,249.23 \implies 216,249$ frames.
3. ID3v2 tag (175 bytes): $\lfloor 175 / 208 \times 1152 \rfloor = 969$ samples.
4. Audio stream frame padding (182 frames @ 209B, 4 frames @ 208B): $\lfloor 38870 / 208 \times 1152 \rfloor - 214272 = 1008$ samples.
5. Total spurious shortfall: $969 + 1008 = 1977$ samples. Residual: **0 samples**.

---

## Controlled Synthetic Experiment Matrix

| Case ID | Description | File Size | Physical Frames | Phys Cap | Declared Frames | Decoded (SF) | Decoded (AV) | Decoded (mini) | Shortfall |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| `case1_cbr_headerless_no_id3` | case1_cbr_headerless_no_id3.mp3 | 16300 B | 78 | 89856 | 90276 | 89856 | 89856 | 89856 | 420 |
| `case2_cbr_id3_128b` | case2_cbr_id3_128b.mp3 | 16428 B | 78 | 89856 | 90985 | 89856 | 89856 | 89856 | 1129 |
| `case2_cbr_id3_1024b` | case2_cbr_id3_1024b.mp3 | 17324 B | 78 | 89856 | 95948 | 89856 | 89856 | 89856 | 6092 |
| `case2_cbr_id3_4096b` | case2_cbr_id3_4096b.mp3 | 20396 B | 78 | 89856 | 112962 | 89856 | 89856 | 89856 | 23106 |
| `case3_cbr_valid_info_frame` | case3_cbr_valid_info_frame.mp3 | 16508 B | 79 | 91008 | 88200 | 88200 | 88200 | 88200 | 0 |
| `case4_vbr_valid_info_frame` | case4_vbr_valid_info_frame.mp3 | 32808 B | 79 | 91008 | 88200 | 88200 | 88200 | 88200 | 0 |
| `case5_vbr_no_info_frame` | case5_vbr_no_info_frame.mp3 | 32600 B | 78 | 89856 | 90060 | 89856 | 89856 | 89856 | 204 |
| `case6a_cbr_malformed_info_zero_count` | case6a_cbr_malformed_info_zero_count.mp3 | 16508 B | 79 | 91008 | 91428 | 89856 | 88751 | 88751 | 1572 |
| `case6b_cbr_malformed_info_bad_magic` | case6b_cbr_malformed_info_bad_magic.mp3 | 16508 B | 79 | 91008 | 91428 | 91008 | 89856 | 91008 | 420 |
| `case7_cbr_mid_frame_truncation` | case7_cbr_mid_frame_truncation.mp3 | 16200 B | 77 | 88704 | 89723 | 88704 | 89856 | 88704 | 1019 |
| `case8_cbr_frame_boundary_truncation` | case8_cbr_frame_boundary_truncation.mp3 | 15882 B | 76 | 87552 | 87961 | 87552 | 87552 | 87552 | 409 |

---

## Forensic Investigation of Decoder Discrepancies

### 1. Malformed Xing/Info Metadata (Cases 6a and 6b)

The experimental results establish an important distinction: **SoundFile's declared length consistently follows the file-size fallback estimate in both malformed cases, but actual decoded PCM outputs diverge across implementations.** These cases demonstrate malformed-metadata sensitivity and decoder disagreement, not uniform fallback decoding behavior.

#### Case 6a — Zero Frame Count (`xing_declared_frames = 0`, valid `Info` magic, valid LAME extension):
- **SoundFile Declared:** `91428` frames (File-size fallback floor(16508 / 208 * 1152) = 91428 because track_frames <= 0.).
- **SoundFile Decoded:** `89856` samples. libmpg123 detects Frame 0 as Info header and skips it. However, because track_frames is 0, gapless playback mode (MPG123_GAPLESS) is aborted. All 78 audio frames are decoded in full without trimming encoder delay or padding (78 * 1152 = 89,856 samples).
- **PyAV Decoded:** `88751` samples.
- **miniaudio Decoded:** `88751` samples.
- **Exact Numerical Reconciliation of the 1,105-Sample Difference:**
  - $89,856 - 88,751 = 1,105$ samples.
  - LAME encoder delay: **576 samples** (`mp3->start_pad`).
  - Decoder synthesis filterbank delay: **529 samples** (`528 + 1` samples in FFmpeg `mp3dec.c`).
  - Total leading skip samples applied: **1,105 samples** (`sti->start_skip_samples = mp3->start_pad + 528 + 1`).
  - Decoded audio frame 1 (first decoded frame after skipped Info frame) contains exactly **47 samples** ($1,152 - 1,105 = 47$ samples).
  - **Frame Origin Terminology Clarification:** The 47 retained samples belong to the first decoded audio frame following the skipped Xing/Info tag frame (physical MPEG Frame 1), NOT physical MPEG Frame 0. Physical MPEG Frame 0 is an Info tag frame skipped during header parsing.
  - Trailing padding retention: In FFmpeg's `libavformat/mp3dec.c`, end discard padding is calculated only if `mp3->frames` is non-zero (`if (mp3->frames)`). Because `xing_declared_frames == 0`, this block is bypassed, leaving `first_discard_sample` unset. FFmpeg trims 1,105 leading samples but trims 0 trailing samples, leaving all 551 samples of end padding intact ($88,200 + 551 = 88,751$ samples).

#### Case 6b — Invalid Magic (`Xung`, declared frames = 78, valid LAME extension):
- **SoundFile Declared:** `91428` frames (File-size fallback floor(16508 / 208 * 1152) = 91428 because Xing magic is unrecognized.).
- **SoundFile Decoded:** `91008` samples.
- **miniaudio Decoded:** `91008` samples.
- **SoundFile/miniaudio Mechanism:** Neither libmpg123 nor dr_mp3 recognizes 'Xung' as a valid header tag. Frame 0 (at file offset 0) is treated as standard MPEG Layer III audio payload and decoded into PCM, yielding all 79 frames * 1152 = 91,008 samples.
- **PyAV Decoded:** `89856` samples.
- **Exact FFmpeg 7.1 Demuxer Control Flow Investigation:**
  1. The malformed Xing/Info marker ('Xung' at byte offset 36) is not recognized. No valid frame count or header file size is obtained (`mp3->frames == 0` and `mp3->header_filesize == 0`). Consequently, `mp3_parse_vbr_tags()` returns `-1`.
  2. `mp3_read_header()` detects the negative return value, restores the input position to byte zero via `avio_seek(s->pb, off, SEEK_SET)` and proceeds with the MPEG synchronization scan.
  3. `mp3_read_header()` inspects for two consecutive MPEG frames satisfying `(header & MP3_MASK) == (header2 & MP3_MASK)` with `MP3_MASK = 0xFFFE0CCF`.
  4. Frame 0 header at offset 0 is `0xFFFB5000` (channel_mode = 00, Stereo; masked `0xFFFA0000`). Frame 1 header at offset 208 is `0xFFFB5064` (channel_mode = 01, Joint Stereo; masked `0xFFFA0044`).
  5. Because channel modes differ, `(h0 & MP3_MASK) != (h1 & MP3_MASK)`. The consecutive frame test fails at offset 0.
  6. The scanner advances to byte offset 208 ($i = 208$), where Frame 1 (`0xFFFB5064`) and Frame 2 (`0xFFFB5264`) match (both masked `0xFFFA0044`).
  7. FFmpeg logs `Skipping 208 bytes of junk at 0.` and seeks to offset 208 (`avio_seek(s->pb, off + 208, SEEK_SET)`).
  8. As a result, physical MPEG Frame 0 (bytes 0..207) is omitted from the demuxed stream, and Packet 0 begins at file offset 208 (size = 208 bytes). All 78 demuxed packets (16,300 bytes) are decoded by libavcodec without gapless trimming: $78 \times 1,152 = 89,856$ samples.

### 2. Mid-Frame Truncation Analysis (Case 7)

- **Original File Size:** `16300 bytes` (78 complete frames, 89,856 samples).
- **Truncated File Size:** `16200 bytes` (truncated by 100 bytes).
- **Complete Physical Frames:** `77` frames (Capacity: 88704 samples).
- **Incomplete Frame 77:** Starts at offset `16091`. Expected length: `209 bytes`. Available: `109 bytes`. Shortfall: `100 bytes`.
- **Trailing Bytes Reported by Parser:** `109 bytes` (exactly matching the remaining partial frame bytes).

#### Empirical Decoder Evidence:
- **SoundFile Decoded:** `88704` samples (Both libmpg123 and dr_mp3 fail closed on incomplete final frames: each strictly requires the complete 209-byte frame before decoding. When EOF occurs at byte 109 of Frame 77, the partial frame is discarded, decoding only the 77 complete frames (77 * 1152 = 88,704 samples).).
- **miniaudio Decoded:** `88704` samples.
- **PyAV Decoded:** `89856` samples.
- **FFmpeg 7.1 Packet and Decode Trace:**
  - Final packet supplied to libavcodec: **exact size = 109 bytes** (Packet 77).
  - MPEG parser behavior: libavformat MP3 demuxer emits Packet 77 containing the 109 trailing bytes at EOF and delivers it to libavcodec.
  - Decoded frame produced: **Yes**, libavcodec decodes 1 audio frame of **1152 PCM samples** (RMS = 0.153318) from Packet 77.
  - Decoder diagnostic messages: No warning, error, or concealment event is logged by FFmpeg at TRACE/DEBUG levels.
  - Bit reservoir behavior: MPEG-1 Layer III side information `main_data_begin` points into earlier packets, but whether internal bit reservoir data or zero-filling contributed to decoding has not been conclusively established without C debugger tracing.
  - Origin of additional 1,152 samples: The additional 1,152 samples originate entirely from the partial 109-byte Packet 77, from which libavcodec emits a 78th audio frame (88,704 + 1,152 = 89,856 samples).
  - Memory-safety padding qualification: AV_INPUT_BUFFER_PADDING_SIZE (64 bytes) is memory-safety padding allocated after input bitstreams to allow optimized SIMD bitstream readers to read ahead without memory access violations. Direct empirical investigation proves this memory-safety padding does not synthesize compressed audio bytes.
  - **Conclusive Status:** > [!WARNING]
> **PyAV produced 1,152 more samples than the capacity of the complete physical MPEG frames. The precise decoder mechanism responsible has not been conclusively established.**

---

## Scientific Limitations: Claim A vs. Claim B

> [!IMPORTANT]
> A critical boundary must be maintained between current bitstream structure and historical completeness:

1. **The currently available file contains physically complete MPEG frames with 0 trailing bytes according to the structural bitstream parser.**
2. **The original recording has not lost complete MPEG frames upstream prior to archive packaging.**

**Limitation Statement:** Claim A does NOT establish Claim B. As demonstrated in Case 8 (exact frame-boundary truncation), dropping complete frames leaves remaining frames 100% structurally valid with 0 trailing bytes. Establishing Claim B requires an independent trusted ground-truth reference duration or original recording.

---

## Synthetic Fixture Directory Provenance

The synthetic audio files were generated and placed in `tests/fixtures/task772a_synthetic/` rather than a
transient scratch directory because they serve as **deterministic, permanent regression test fixtures**
exercised by `tests/research_validity/test_stage6m_cohort3_task772a_libsndfile_investigation.py`.
Storing them in `tests/fixtures/` ensures that CI and future audits can independently verify all synthetic
properties without re-running synthesis.

| Fixture File | Size | SHA-256 | Purpose | Test Binding |
|:--|:--|:--|:--|:--|
| `case1_cbr_headerless_no_id3.mp3` | 16300 B | `fefed452d1c30a2f2e8ee5a1ca1f95c7c378b0216d2c5e2342078a5084bd0f33` | Baseline file-size estimation on raw audio bitstream without container metadata. | `test_synthetic_matrix_id3_inflation_invariance` |
| `case2_cbr_id3_128b.mp3` | 16428 B | `0fc3cca066fbff6e96cc68be46a131be61fd6aa3940d076e1fe26f24aebcc2d2` | Test tag-size sensitivity with controlled 128-byte ID3v2 tag. | `test_synthetic_matrix_id3_inflation_invariance` |
| `case2_cbr_id3_1024b.mp3` | 17324 B | `075acd83caa7203b0323c128a2262fba1a65969bb618eb7ec5562fb37cd7b905` | Test tag-size sensitivity with controlled 1024-byte ID3v2 tag. | `test_synthetic_matrix_id3_inflation_invariance` |
| `case2_cbr_id3_4096b.mp3` | 20396 B | `8c63ddb60360fc40c9c76bccda63d7ab19506cf0a754c719eb13e2de8a80f487` | Test tag-size sensitivity with controlled 4096-byte ID3v2 tag. | `test_synthetic_matrix_id3_inflation_invariance` |
| `case3_cbr_valid_info_frame.mp3` | 16508 B | `31a1a945c6d2b3d2daf1c6dbede4cfba574e7f2bc24719f043e504056c9c6a4b` | Verify Xing/Info header authority and gapless trimming on CBR stream. | `test_synthetic_matrix_xing_header_authority` |
| `case4_vbr_valid_info_frame.mp3` | 32808 B | `1b40b9a671f9cb3394e819b95adc33b2f99d008a9dd5059a9a9265d888a9116f` | Verify Xing/Info header authority on VBR stream. | `test_synthetic_matrix_xing_header_authority` |
| `case5_vbr_no_info_frame.mp3` | 32600 B | `be80cdd089efc7337994af29dbca54ba40457eacfaaadf1c3cfafa9721bcdd5e` | Verify fallback behavior when VBR stream lacks Info header (first-frame bpf fallback). | `test_synthetic_matrix_xing_header_authority` |
| `case6a_cbr_malformed_info_zero_count.mp3` | 16508 B | `e841bf905b84f357d4e6604587cab4f5e04e756ff2f0c01310f16e5b088091bb` | Test decoder response when Xing header has zero frame count but valid magic. | `test_synthetic_matrix_malformed_metadata_divergence` |
| `case6b_cbr_malformed_info_bad_magic.mp3` | 16508 B | `81bc918c231ba7d2bc539ba22272a1eddcba65f5b636a8cf996c6c2258088bac` | Test decoder response when Xing magic is corrupted to Xung. | `test_synthetic_matrix_malformed_metadata_divergence` |
| `case7_cbr_mid_frame_truncation.mp3` | 16200 B | `85f48e181dd3d3e6f7bcb1026a22c71adbadc98b4e3b1da6713aa71cd2a7d8fd` | Test physical structural parser and decoder behavior on incomplete final frame. | `test_synthetic_matrix_truncation_detection` |
| `case8_cbr_frame_boundary_truncation.mp3` | 15882 B | `73b1fc8226a1fc1a6e588e230755fbbdd577d457f72d714b8f1083875b651f30` | Demonstrate that complete-frame loss is structurally undetectable (Claim A vs Claim B). | `test_synthetic_matrix_truncation_detection` |

---

## Protected-File & Production-Validator Verification

| Protected Artifact | Path | Baseline / Expected SHA-256 | Actual Verified SHA-256 | Governance Status |
|:--|:--|:--|:--|:--|
| Production Audio Validator | `scripts/materialize_stage6m_cohort3_audio.py` | Preserved | `a3dd4fcbe5a20e366c56b1ff9307f543161deec75f8ec3c776de47ad7c5c3452` | MAX_MP3_PADDING_FRAMES = 1152 strictly intact |
| Provisional Manifest | `datasets/splits/stage6m_cohort3_provisional_manifest.json` | `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` | `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547` | UNLOCKED (PROVISIONAL) - final_manifest_lock: BLOCKED_PENDING_100_PERCENT_PHYSICAL_VALIDATION |
| Acquisition Ledger (LF) | `datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv` | `63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5` | `63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5` | 18845 accepted records intact (Git LF normalized) |
| Acquisition Ledger (CRLF) | `datasets/splits/stage6m_cohort3_clip_sha256_ledger.csv` | `eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c` | `eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c` | 18845 accepted records intact (Windows CRLF materialization) |
| Quarantine Ledger | `datasets/splits/stage6m_cohort3_quarantine_ledger.csv` | `98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8` | `98ae234d0f6985ef42d69b5e6a79250501cd1ef27861fc0310455b96d901a2e8` | 130 quarantined records intact |
| Quarantine Targets List | `datasets/splits/stage6m_cohort3_task771_quarantine_targets.json` | `a530fb8b60fc302e536ce14efb620cda936ad91783f7d1f482a430dd154696ae` | `a530fb8b60fc302e536ce14efb620cda936ad91783f7d1f482a430dd154696ae` | 130 frozen targets intact |

> [!NOTE]
> **Acquisition Ledger Cryptographic & Line-Ending Reconciliation:** The original acquisition ledger materialization produced CRLF line terminators (8,355,851 bytes, SHA eda8bbe236bac0360d055a7616d5ee5d666119317c4c95a271e994d793fde08c). Git committed normalization converted record terminators to LF (8,337,005 bytes, SHA 63b24401b3ab415417b4163553da877f4ae025c65c6fe6136b27b535fa1fd9c5). The 18,846-byte delta corresponds to exactly 1 byte per record terminator across 1 header line and 18,845 data rows. Direct binary inspection confirms 0 CRLF and 0 CR bytes in the repository file, with exactly 18,853 LF bytes (18,846 record lines + 7 embedded newlines inside multiline transcript fields). All 18,845 data rows and 14 CSV columns are 100% byte-for-byte identical, with zero record divergence.
> Protected audio inventory audit: **18845/18845 verified matching on disk (0 missing, 0 mismatched)** across accepted audio, and **130/130 verified matching on disk (0 missing, 0 mismatched)** across quarantined audio.

> [!IMPORTANT]
> **Production Validator Identification:** The actual production audio validator is `validate_audio_file`
> in `scripts/materialize_stage6m_cohort3_audio.py` (lines 325-409), which enforces `MAX_MP3_PADDING_FRAMES = 1152`
> at lines 394-404 during the materialization pipeline. Downstream CTTA adaptation and inference models load audio
> via `src/dsg_ctta/data/acoustic.py::load_and_resample_audio`, which decodes PCM samples via `soundfile.read()`.

---

## Governance Status & Preserved Constraints

1. **Production validator unchanged:** `scripts/materialize_stage6m_cohort3_audio.py::validate_audio_file` remains unmodified.
2. **MAX_MP3_PADDING_FRAMES=1152 unchanged:** Production tolerance boundary remains strictly enforced.
3. **Zero recording promotion:** All 18,845 accepted recordings and 130 quarantined recordings remain untouched.
4. **Ledgers untouched:** Acquisition ledger and quarantine ledger match preserved baseline digests exactly.
5. **Provisional manifest locked:** Cohort 3 provisional manifest matches approved SHA-256 `b9a03e2ab13043155ea8904129678fa2e41d0e287a772ca78e5a6086aac7f547`.
6. **Frozen inference engine untouched:** Model weights and GPU inference pipeline remain untouched.

---

## Next Steps

- Present complete reconciliation package to Project Lead.
- Await authorization for separate commits: (1) Phase 9 Markdown encoding fixes, (2) Task 7.7.2A investigation deliverables.
- Proceed to Task 7.7.2B (production validator impact assessment) without altering MAX_MP3_PADDING_FRAMES=1152.
