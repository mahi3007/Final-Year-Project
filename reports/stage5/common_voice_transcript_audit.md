# Common Voice Transcript Audit
## DSG-CTTA Stage 5 Phase 1

**Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Purpose:** Evaluate transcript availability and quality for WER evaluation suitability.

---

## 1. Transcript Field Summary

| Property | Status |
|---|---|
| Field name | sentence |
| Language | English (orthographic standard) |
| Source | Mozilla Common Voice sentence corpus (open, community-contributed text) |
| Transcript type | Read speech (participant reads a displayed sentence) |
| Location in archive | validated.tsv column sentence |
| Missing rate in validated.tsv | ~0% (sentence is required for clip recording; no sentence = no clip) |
| Duplicate transcript rate | Moderate: the same sentence appears recorded by multiple speakers; this is expected |
| Encoding | UTF-8 |

---

## 2. Validation Mechanism

Clips in validated.tsv have passed community review:
- At least 2 community members listened to the clip
- A majority voted that the audio matches the displayed transcript
- Clips failing majority vote go to invalidated.tsv
- Clips with no votes remain in unvalidated/other.tsv

This validation process establishes that the sentence field is a reliable orthographic reference for WER computation.

---

## 3. Transcript Characteristics

| Characteristic | Observed / Estimated |
|---|---|
| Average transcript length | ~8-12 words |
| Minimum transcript length | ~2 words (short prompts; uncommon) |
| Maximum transcript length | ~20 words (typical upper bound) |
| Transcript style | Read speech (not spontaneous; no fillers, disfluencies in reference) |
| Punctuation | Present in reference transcripts; strip for WER normalisation |
| Case | Mixed case in reference; lowercase normalisation recommended |
| Non-English contamination | Very rare in English locale; occasional proper nouns from other languages |
| Unusual symbols | Minimal; occasional apostrophes, hyphens in compound words |

---

## 4. WER Evaluation Suitability

| Criterion | Assessment |
|---|---|
| Reference transcript is deterministic | YES: sentence field is the displayed prompt |
| Speaker deviation from prompt detectable | YES: down-votes capture misread clips; validated.tsv filters them |
| Normalisation required | YES: lowercase + punctuation stripping + expand common contractions |
| Suitability for exact WER | SUITABLE |
| Compatibility with L2-ARCTIC evaluation protocol | COMPATIBLE (both are read-speech with orthographic references) |
| Risk of reference transcript errors | LOW (community-validated alignment) |
| Risk of pronunciation ambiguity | LOW (English orthography; ambiguity is in speaker performance, not reference) |

---

## 5. Comparison: Common Voice vs. L2-ARCTIC Transcripts

| Property | L2-ARCTIC | Common Voice English |
|---|---|---|
| Transcript source | CMU ARCTIC prompts (fixed set, ~1150 sentences) | Mozilla sentence pool (~50,000+ unique sentences) |
| Transcript reliability | Very high (studio; forced alignment verified) | High (community-validated) |
| Average utterance length | ~7-10 words | ~8-12 words |
| WER reference availability | YES | YES |
| Speech style | Read | Read |
| Sentence overlap between datasets | None expected | None expected |
| Normalisation requirement | Standard | Standard (same procedure applicable) |

**Conclusion:** Common Voice transcripts are suitable as WER evaluation references. The same
normalisation pipeline (lowercase, strip punctuation) used for L2-ARCTIC is applicable.

---

## 6. Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Occasional non-English word in prompt | Low | Screen for non-ASCII; exclude or normalise |
| Duplicate prompts across speakers | Benign | Does not affect speaker independence; expected in multi-speaker corpus |
| Speaker deviates substantially from prompt | Low in validated.tsv | Community validation reduces this; validated.tsv provides clean reference |
| Short prompts (<4 words) producing unreliable per-clip WER | Low | Set minimum word-count filter during subset selection if needed |

---

## 7. Conclusion

Common Voice English transcripts in validated.tsv are:
- Available for all clips (~0% missing rate)
- Community-validated for audio-text alignment
- Suitable for exact WER computation using standard normalisation
- Compatible with the L2-ARCTIC evaluation methodology
- No special preprocessing beyond standard text normalisation is required

**Transcript audit result: PASS**
