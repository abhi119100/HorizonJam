# Abstract Draft

## Working Title

**HorizonJam: Evidence-Grounded AI Music Tutoring from Uncertain Performance
Analysis**

## Abstract

AI music tutors increasingly combine machine listening with language-model
feedback, but an upstream transcription or chord-recognition error can be
silently transformed into confident pedagogical advice. We present HorizonJam
v3, a public research prototype for analyzing short musician recordings and
generating inspectable tutoring responses. The system routes replaceable music
information retrieval components through a normalized timed-chord contract,
preserves detector identity, confidence when available, and warnings in a
versioned performance-evidence packet, retrieves bounded source text with
provenance, and applies deterministic uncertainty and retrieval-honesty checks
before written or spoken feedback is delivered. A layered evaluation harness
separates symbolic chord classification, post-transcription harmony analysis,
retrieval behavior, tutor grounding, and product runtime. Existing v3 evidence
diagnoses a structural subset bias in one symbolic scorer and shows that an
isolated Jaccard formulation improves a frozen synthetic post-transcription
benchmark, while also demonstrating deterministic evidence propagation and
uncertainty repair in fixed tutor cases. These results do not establish
real-musician chord accuracy, calibrated confidence, pedagogical quality, or
learning outcomes. We therefore define a preregisterable multi-source harmonic
detection tournament that compares transcription, direct-chord, and
interpretable chroma evidence before testing fusion and downstream tutor
effects. HorizonJam contributes an inspectable systems architecture and an
evaluation agenda for studying how uncertain musical perception propagates
into generated instruction.

## Claim Boundary

The abstract claims an implemented architecture, checked-in deterministic
evaluations, and a proposed experimental agenda. It does **not** claim:

- that HorizonJam is the first AI music tutor;
- that its detector outperforms commercial or academic systems on real audio;
- that model probabilities are calibrated confidence;
- that retrieval guarantees factual or pedagogical correctness; or
- that musicians learn faster or play better after using the system.

## Short Abstract

HorizonJam v3 is a public research prototype for evidence-grounded AI music
tutoring from short performances. It preserves timed musical observations,
detector provenance, available confidence, warnings, and retrieved sources in
an inspectable packet before language-model generation, then verifies
uncertainty and retrieval claims before delivery. Its layered harness exposes
where perception, harmony, retrieval, or generation fails. Current evidence is
synthetic and structural; a planned multi-source tournament will test whether
transcription, direct-chord, and chroma evidence provide complementary value on
licensed real performances.
