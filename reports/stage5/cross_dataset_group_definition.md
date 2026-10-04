# Cross-Dataset Group Definition Analysis
## DSG-CTTA Stage 5 Phase 1H

**Date:** 2026-10-01
**Auditor:** Lead Research Data Engineer
**Purpose:** Compare L2-ARCTIC group definitions with Common Voice English group definitions.
Determine what relationship (replication, generalisation, stress testing) the external
evaluation can legitimately support.

---

## 1. Group Definition Comparison

### L2-ARCTIC Groups (Primary Corpus)

| Group | Definition Basis | Verification | L1 Background |
|---|---|---|---|
| Arabic | Speaker L1 is Arabic; verified by corpus creators | Verified by L2-ARCTIC dataset authors | Arabic |
| Hindi | Speaker L1 is Hindi; verified by corpus creators | Verified | Hindi |
| Korean | Speaker L1 is Korean; verified by corpus creators | Verified | Korean |
| Mandarin | Speaker L1 is Mandarin Chinese; verified by corpus creators | Verified | Mandarin |
| Spanish | Speaker L1 is Spanish; verified by corpus creators | Verified | Spanish |
| Vietnamese | Speaker L1 is Vietnamese; verified by corpus creators | Verified | Vietnamese |

**Key property of L2-ARCTIC groups:** The group variable is SPEAKER L1 (native language),
verified by the corpus annotation team. All speakers are non-native English speakers whose
first language is the named language.

### Common Voice English Groups (Proposed External)

| Group | Accent Code | Definition Basis | Verification | L1 Background |
|---|---|---|---|---|
| United States English | us | Self-reported accent label | Self-report only; not independently verified | Unknown (likely L1 English; but not verified) |
| England English | england | Self-reported accent label | Self-report only | Unknown (likely L1 English; not verified) |
| India/South Asia English | indian | Self-reported accent label | Self-report only | Unknown; conflates multiple South Asian L1 backgrounds |
| Australian English | australia | Self-reported accent label | Self-report only | Unknown (likely L1 English; not verified) |
| Canadian English | canada | Self-reported accent label | Self-report only | Unknown (likely L1 English; not verified) |
| Irish English | ireland | Self-reported accent label | Self-report only | Unknown (likely L1 English; not verified) |

**Key property of Common Voice groups:** The group variable is SELF-REPORTED ACCENT,
not verified L1. Groups are defined by the label the speaker chose to assign to their accent,
not by any independently verified linguistic property.

---

## 2. Variable-by-Variable Equivalence Assessment

| Variable | L2-ARCTIC | Common Voice | Equivalent? | Notes |
|---|---|---|---|---|
| Group definition basis | Verified speaker L1 | Self-reported accent label | NO | Fundamentally different; L1 verification vs. self-report |
| Speaker native language | Known, verified | Unknown, unverified | NO | |
| Speaker L2 English status | All speakers are non-native English | Unknown; most likely native English for us/england/australia/canada/ireland | NO | Critical difference |
| Corpus type | Read speech (CMU ARCTIC prompts) | Read speech (Mozilla sentence pool) | COMPARABLE | Both are read-speech; different prompts |
| Transcript availability | Verified | Community-validated | COMPARABLE | Both are reliable references for WER |
| Speaker count per group | 4 speakers/group (small) | 1,000-15,000 speakers/group (large) | NOT EQUIVALENT | Large size difference |
| Acoustic recording quality | Studio-quality (controlled) | Crowdsourced (variable conditions) | NOT EQUIVALENT | CV has more acoustic variability |
| Gender balance | Mixed; 2M/2F per group | Variable; dataset-dependent | NOT EQUIVALENT | |
| Age range | Adults; controlled | All ages; crowdsourced | NOT EQUIVALENT | |
| Accent intensity | Non-native English (strong L2 features) | Native-associated English (for most CV groups) | NOT EQUIVALENT | Major phenotypic difference |

---

## 3. Answering the Five Protocol Questions

### Q1: Are the group definitions comparable?

**NO.** They are not comparable in the strict sense.

L2-ARCTIC groups are defined by VERIFIED SPEAKER L1 (native language). This is a linguistically
grounded, researcher-verified classification. Common Voice groups are defined by SELF-REPORTED
ACCENT LABELS. These are phenomenologically different variables.

The only group with any analogical overlap is indian (Common Voice) vs. Hindi (L2-ARCTIC),
but even this is a weak proxy: the indian label conflates Hindi, Tamil, Telugu, Urdu, Kannada,
and other South Asian L1 backgrounds. A indian-labelled CV speaker may have Hindi, Tamil,
or any other South Asian L1.

### Q2: Which variables are genuinely equivalent?

The following variables are genuinely equivalent or comparable:
- Transcript format: orthographic, read speech, sentence-level
- WER computation method: transcript reference is the displayed prompt
- Normalisation procedure: lowercase + punctuation stripping applicable to both
- Evaluation unit: utterance-level WER aggregated per speaker then per group

### Q3: Which variables are different?

The following variables are NOT equivalent:
- Group definition basis (verified L1 vs. self-reported accent label)
- Speaker nativeness (L2-ARCTIC is exclusively non-native English; CV is predominantly native-English for most groups)
- Speaker pool size (4 speakers vs. 500-15,000 speakers per group)
- Recording conditions (studio vs. crowdsourced)
- Accent label reliability (verified vs. self-report; ~50% missing in CV)
- Accent intensity and phonetic deviation from Standard American English

### Q4: What wording should be used in the paper?

CORRECT wording examples:

"To assess external generalisability, we evaluate the DSG controller on an independent
evaluation set drawn from Mozilla Common Voice (cv-corpus-11.0). This set comprises
speakers self-identifying under six accent categories (United States English, England
English, India/South Asia English, Australian English, Canadian English, and Irish English).
We note that this categorisation is based on self-reported accent labels and is not
directly equivalent to the L1-verified speaker groups in L2-ARCTIC."

"The Common Voice external evaluation set constitutes a stress test of the controller's
behaviour on a population with different group definition semantics, recording conditions,
and predominantly native-English speaker backgrounds. Results on this set should not be
interpreted as a direct replication of the L2-ARCTIC findings."

INCORRECT wording (prohibited):

"We replicate our L2-ARCTIC findings on Common Voice English." (WRONG: groups are not equivalent)
"The India/South Asia category in Common Voice corresponds to the Hindi group in L2-ARCTIC." (WRONG: category conflates multiple L1s)
"Results generalise to accented English speakers broadly." (OVERSTATED without further evidence)

### Q5: Can the external dataset support replication, generalisation, or stress testing?

| Support Type | Assessment |
|---|---|
| REPLICATION | NO: Group definitions, speaker nativeness, and recording conditions differ too substantially for formal replication |
| GENERALISATION | PARTIAL: Supports weak external generalisability claims for controller behaviour across different English variety populations and recording conditions |
| STRESS TESTING | YES: CV provides a different acoustic environment, different group semantics, and larger speaker pools; results provide evidence that controller behaviour is consistent across evaluation populations |

**Recommended framing:** "External stress test / out-of-distribution validation"
NOT: "replication" or "direct generalisation"

---

## 4. Proposed Paper Language Framework

Section heading suggestion:
"External Out-of-Distribution Validation on Mozilla Common Voice English"

Subsection note suggestion:
"The external evaluation set is drawn from a distinct corpus with different group definition
semantics (self-reported accent labels vs. verified L1 backgrounds), different recording
conditions (crowdsourced vs. studio), and a predominantly native-English speaker population.
These differences make direct cross-dataset comparison non-trivial. Results are reported
separately and interpreted as evidence of controller behavioural consistency across
evaluation populations, not as a formal replication."

---

## 5. Summary

| Property | L2-ARCTIC | Common Voice (external) | Compatible? |
|---|---|---|---|
| Group variable | Verified L1 | Self-reported accent | NO |
| Speaker nativeness | Non-native English | Predominantly native-English | NO |
| Transcript | CMU ARCTIC prompts | Mozilla sentence pool | YES (comparable) |
| WER computability | YES | YES | YES |
| Independent of L2-ARCTIC | N/A (primary corpus) | YES | YES |
| Evaluation role | Primary (CTTA experiment) | External stress test | SEPARATE |

The two evaluations must be kept conceptually separate in all paper and report language.
Common Voice can support stress testing and out-of-distribution validation, not replication.
