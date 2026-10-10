# Stage-3M Stream Audit
*Alias reference to comprehensive data and stream audit.*

Please refer to the full primary audit report:
- [Stage-3M Data and Stream Audit Report](file:///c:/Users/venka/Downloads/final%20year%20project%20main/reports/stage3m/stage3m_data_stream_audit.md)

## Summary of Verified Stream Parameters
- **Dataset Source:** L2-ARCTIC `final_test` partition (`datasets/splits/final_test.csv`)
- **Dataset SHA-256:** `a4eb01993bf746b0a0b079224f1480338de01a3b224c635fdcc97a99047285d8`
- **Total Utterances:** 60
- **Total Speakers:** 6 (`ABA`, `BJM`, `BVT`, `EBVS`, `MBX`, `TLX`)
- **Total Accent Groups:** 6 (Arabic, Hindi, Korean, Mandarin, Spanish, Vietnamese)
- **Balance:** Exactly 10 utterances, 92 words, and 40.96 seconds duration per group.
- **Total Words:** 552
- **Window Size (K):** 4
- **Window Count:** 15
- **Pre-Registered Orders:** `ORDER_A`, `ORDER_B`, `ORDER_C`
- **Set Invariant:** $\mathcal{S}_A = \mathcal{S}_B = \mathcal{S}_C$
- **Prequential Invariant:** $\text{score}(B_t, \theta_t)$ strictly before $\text{adapt}(B_t)$
- **Label Isolation:** `UnlabeledAudioBatch` enforced (no ground truth transcripts or metadata delivered online)
- **Speaker Disjointness:** Zero leakage with `development`, `calibration`, `sentinel_candidates`
- **Status:** **PHASE_3_VERIFIED**
