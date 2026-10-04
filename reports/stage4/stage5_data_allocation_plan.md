# Stage 5 Architectural Specification: Data Partitioning & Sentinel Allocation Plan

**Protocol Version:** `v1.0.0-canonical`  
**Date of Specification:** 2026-09-30  
**Authors:** Lead ML Systems & Research Methodology Engineers  
**Pre-Requisite Milestone:** Stage 4 Characterization Audit (Conditional GO)

---

## 1. Problem Statement: The Three-Way Partitioning Constraint

The core hypothesis of Stage 5 is that a **Disparity Safety Gate (DSG)** can evaluate candidate model updates $\theta'_{t}$ on an air-gapped **Sentinel Panel** and decide whether to accept or rollback the update:
$$\theta_{t+1} = \begin{cases} \theta'_{t} & \text{if } \text{DSG}(\theta'_{t}; \mathcal{S}_{\text{sentinel}}) = \text{ACCEPT} \\ \theta_{t} & \text{if } \text{DSG}(\theta'_{t}; \mathcal{S}_{\text{sentinel}}) = \text{ROLLBACK} \end{cases}$$

To prevent data contamination and ensure peer-review defensibility, the Stage 5 experimental protocol imposes an **absolute 3-way disjointness invariant**:
$$\mathcal{S}_{\text{adaptation}} \cap \mathcal{S}_{\text{sentinel}} = \emptyset$$
$$\mathcal{S}_{\text{adaptation}} \cap \mathcal{S}_{\text{evaluation}} = \emptyset$$
$$\mathcal{S}_{\text{sentinel}} \cap \mathcal{S}_{\text{evaluation}} = \emptyset$$

### The Structural Constraint in L2-ARCTIC
In L2-ARCTIC, there are exactly 24 speakers across 6 accent groups:
$$N_{\text{total}} = 24 \text{ speakers} \quad (4 \text{ speakers per group: } 2\text{M}, 2\text{F})$$

The Stage 4 audit allocated these 24 speakers across:
- **Development Partition:** 6 speakers (1/group)
- **Calibration Partition:** 6 speakers (1/group)
- **Characterization Stream:** 12 speakers (2/group: combined historical `sentinel_candidates` + `final_test`)

If all 24 speakers were previously exposed during exploratory development or characterization, allocating speakers for Stage 5 without circularity requires a formal protocol.

---

## 2. Feasibility Analysis of Allocation Options

### Option A: External Benchmark Expansion (Recommended for Publication)
- **Primary Adaptation Corpus:** L2-ARCTIC Characterization Stream ($N=12$ speakers, 120 utts).
- **Primary Sentinel Panel:** L2-ARCTIC Frozen Sentinel Candidates ($N=6$ speakers from `sentinel_candidates.csv`).
- **Final Evaluation Benchmark:** External multi-accent corpus (e.g., **CommonVoice non-native English** or **EdAcc English-with-Accents**).
- **Pros:**
  - Complete acoustic, channel, and recording independence between adaptation and evaluation.
  - Zero possibility of speaker leakage or overfitting to L2-ARCTIC studio room impulse responses.
  - Represents the gold standard for transfer learning in speech recognition.
- **Cons:** Requires preprocessing and aligning external audio files and transcripts.

### Option B: Strictly Disjoint 3-Way Balanced Partition of L2-ARCTIC (Zero External Data)
Within the 24 speakers of L2-ARCTIC, we partition the dataset into 3 strictly disjoint sets of 6 to 8 speakers each, preserving balanced gender and accent representation:
1. **Adaptation Stream ($\mathcal{S}_{\text{adapt}}$):** 6 speakers (1 per group: e.g., `ABA`, `BJM`, `BVT`, `EBVS`, `MBX`, `TLX` from `final_test.csv`, 60 utts).
2. **Sentinel Panel ($\mathcal{S}_{\text{sentinel}}$):** 6 speakers (1 per group: e.g., `ASI`, `BWC`, `HCC`, `LXC`, `YDCK`, `ZHAA` from `sentinel_candidates.csv`, 60 utts).
3. **Final Holdout Test Stream ($\mathcal{S}_{\text{eval}}$):** 6 speakers (1 per group: e.g., `HJK`, `HKK`, `MPXM`, `SKA`, `TNI`, `TNT` from `calibration.csv`, 60 utts).
- **Pros:**
  - 100% speaker disjoint across all three partitions within the existing corpus.
  - Zero external dependencies.
  - Retains perfect 6-accent balance across all splits.
- **Cons:**
  - Adaptation stream is 60 utterances (1 speaker/group) rather than 120 utterances.

### Option C: Hybrid Partitioning with Utterance-Level Disjointness on Expanded Audio
In the full L2-ARCTIC distribution, each speaker recorded over 1,000 sentences (from the CMU ARCTIC prompt set). The repository currently uses sentences `a0001` through `a0010`.
If additional recordings for the 12 characterization speakers are utilized:
- **Adaptation Stream:** Sentences `a0001` - `a0020` (adapted on).
- **Sentinel Panel:** 6 disjoint speakers (sentinel candidates, sentences `a0001` - `a0020`).
- **Final Evaluation:** Sentences `a0021` - `a0050` across all speakers.
- **Pros:** Combines speaker disjointness for the sentinel with large sample sizes for evaluation.

---

## 3. Decision & Recommended Stage 5 Architecture

For Stage 5 controller implementation and verification, we adopt **Option B (Strictly Disjoint 3-Way Balanced L2-ARCTIC Partition)** for the core internal controller validation, supplemented by **Option A (External Validation)** for generalizability testing:

```
                                  STAGE 5 DATA ARCHITECTURE
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              ▼                               ▼                               ▼
       ADAPTATION STREAM               SENTINEL PANEL                FINAL HOLDOUT EVALUATION
      (6 Speakers / 6 Groups)        (6 Disjoint Speakers)            (6 Disjoint Speakers)
    • Unlabeled audio B_t          • Ground truth available        • Unlabeled live stream
    • Drives online updates        • Evaluates candidate θ'_t      • Prequential evaluation
    • No-Adapt / SUTA / DSUTA      • Accept / Reject decision      • Independent audit
```

### Partition Manifest Specifications
1. **`datasets/splits/stage5_adaptation_stream.csv`:**
   - Speakers: `ABA` (Arabic), `BJM` (Hindi), `EBVS` (Korean), `TLX` (Mandarin), `MBX` (Spanish), `BVT` (Vietnamese).
   - Total: 60 utterances, 6 speakers, 1/group.
2. **`datasets/splits/stage5_sentinel_panel.csv`:**
   - Speakers: `ZHAA` (Arabic), `ASI` (Hindi), `HCC` (Korean), `BWC` (Mandarin), `YDCK` (Spanish), `LXC` (Vietnamese).
   - Total: 60 utterances, 6 speakers, 1/group.
3. **`datasets/splits/stage5_final_eval.csv`:**
   - Speakers: `SKA` (Arabic), `HKK` (Hindi), `HJK` (Korean), `MPXM` (Mandarin), `TNI` (Spanish), `TNT` (Vietnamese).
   - Total: 60 utterances, 6 speakers, 1/group.

**Verification Invariant:**
An automated cryptographic test (`test_stage5_zero_data_leakage`) will assert that:
$$\text{set}(\text{Adaptation}) \cap \text{set}(\text{Sentinel}) \cap \text{set}(\text{FinalEval}) = \emptyset$$
This guarantees 100% protocol integrity before any Stage 5 controller experiment is executed.
