---
name: academic-literature-novelty
description: Conduct source-verified literature reviews and novelty assessments for ASR, test-time adaptation and speech fairness; use when positioning a contribution, selecting baselines, writing related work, or preparing a paper.
---

# Literature Review and Research Novelty

## Mission
Determine what is genuinely new, what has already been demonstrated, and what claims can be supported by primary literature. Do not manufacture novelty or citations.

## Search workflow
1. Translate the research question into concepts and synonyms: ASR, source-free/test-time adaptation, continual adaptation, online adaptation, speech accent/variety disparity, subgroup fairness, sentinel validation, selective/guarded model updates, catastrophic forgetting and rollback.
2. Search primary venues and indexes: ACL Anthology, Interspeech/ISCA, IEEE Xplore, ACM Digital Library, arXiv (clearly label preprints), Crossref/DOI records and publisher pages. Search broadly enough to include older foundational work and recent competing methods.
3. Prioritize primary papers, official proceedings, publisher pages, author repositories and original benchmarks. Use surveys for orientation, not as the sole basis for a novelty claim.
4. Verify title, authors, year, venue, DOI/arXiv identifier and publication status against at least one authoritative record. Distinguish accepted conference papers, preprints, workshop papers and technical reports.
5. Read method, experimental design, datasets, baselines, metrics, limitations and ablations—not only abstracts. Note whether the paper is ASR-specific, accent-specific, online/continual, source-free and fairness-aware.
6. Build a comparison matrix with columns: method, adaptation signal, update scope, update control, safety/fairness objective, benchmark, group labels, evaluation protocol, limitations and overlap with DSG.
7. Compare DSG against SUTA and relevant later methods such as DSUTA and DMSUTA only after checking primary sources and methodological compatibility. Do not claim a baseline is missing if it is simply incompatible without explaining why.
8. Identify the closest prior work and state the difference in one falsifiable sentence. Then list what evidence would be required to substantiate that difference.
9. Maintain a search log with databases, queries, dates, inclusion/exclusion rules and paper decisions. For systematic claims, report the search scope and acknowledge coverage limitations.
10. When writing, attach a citation to every non-obvious external factual claim. Never invent a DOI, quotation, experimental result or author conclusion.

## Stage 6M positioning guardrails
- The result that DSG performed much better than ungated SUTA but did not meet the registered superiority-over-static or disparity UCB criteria is a potentially useful empirical finding; it is not proof that the method universally prevents adaptation collapse.
- A new algorithmic contribution must be compared against current relevant baselines on the same data and under a fair, frozen protocol.
- Separate an engineering contribution (e.g. execution integrity, sentinel design) from a scientific contribution (demonstrated generalizable performance or fairness effect).
- Do not claim “first”, “novel”, “state of the art” or “solves accent bias” without a documented comparison and narrowly defined scope.

## Outputs
Produce a search log, annotated bibliography, related-work matrix, closest-prior-work analysis, contribution statement, reviewer-style novelty risks and a list of missing experiments. Include publication venue and source links. Mark unverified references explicitly rather than filling gaps by guesswork.
