# The AI Music Coach That Shows Its Work

**Publication status:** draft for review  
**Suggested subtitle:** Open-sourcing HorizonJam's evidence-grounded
architecture for turning uncertain musical perception into useful instruction

## Play Something, Then Ask Why

Most music software answers one of three questions:

- What notes or chords are in this recording?
- Did I play the exercise correctly?
- What song, tab, or lesson should I open next?

HorizonJam is being built around a different question:

> What happened musically in what I just played, how certain is that analysis,
> and what should I understand or practice next?

Imagine recording this progression:

```text
C - Am - D7 - G
```

A chord detector can return four labels. A language model can explain secondary
dominants. Neither result is sufficient on its own. If the third segment was
actually D major, or if background noise hid the seventh, a fluent explanation
of D7 can be confidently wrong.

The tutor should instead be able to say:

```text
I detected D7 in the third segment, but that segment was the least certain.
If the detection is correct, D7 functions as V/V and points toward G.
Practice Am -> D7 -> G slowly, and inspect the detected notes if the label
does not match what you intended to play.
```

That difference is the core of HorizonJam.

## The Problem Is the Whole Chain

An AI music tutor is not one model. It is a chain:

```text
audio capture
  -> transcription and harmonic analysis
  -> segmentation and confidence
  -> retrieved musical knowledge
  -> language-model reasoning
  -> written and spoken feedback
```

Every stage can fail differently. A microphone can clip. A transcription model
can miss a note. A chord classifier can prefer a triad over a seventh. A
retriever can return irrelevant theory. A language model can turn weak evidence
into a confident claim.

HorizonJam v3 makes those stages explicit rather than hiding them behind a
single "AI tutor" label.

## The Architecture

### 1. Replaceable musical perception

All active chord detection goes through one boundary:
`detection.run_detection()`. Detector implementations can change, but the
application receives normalized timed events with a detector identity,
warnings, and confidence only when the detector can supply it.

### 2. A versioned performance-evidence packet

The tutor does not receive only a progression string. It receives structured
evidence: event timing, chord labels, source detector, available confidence,
warnings, estimated key, and guitar context. Missing confidence stays missing.
Alternatives are not invented.

### 3. Bounded retrieval with provenance

The current retrieval path selects a small amount of actual document text and
retains source, record ID, rank, relevance, and metadata. A no-result state is
represented honestly. Retrieved text is treated as untrusted context, not as
instructions to the system.

### 4. Verification before delivery

The complete tutor draft is checked before the first sentence is shown or
spoken. Current deterministic rules require uncertainty language when evidence
is weak and remove claims that retrieval occurred when it did not. These checks
are narrow by design; they are safeguards, not a proof that the musical advice
is correct.

### 5. Evaluation by layer

HorizonJam tracks audio, transcription, harmony, retrieval, tutor reasoning,
pedagogy, product reliability, and learning outcomes separately. A passing
prompt test is not evidence of chord accuracy. A synthetic chord benchmark is
not evidence that a musician learns more effectively.

## What v3 Has Actually Shown

The frozen v3 baseline has already been useful as a research instrument.

- A symbolic oracle exposed why a scorer systematically collapsed dominant
  sevenths into major triads: its match term rewarded template coverage but did
  not penalize unexplained input notes.
- A frozen Jaccard experiment repaired much of that isolated subset problem and
  improved a 40-progression synthetic post-transcription benchmark.
- A controlled WAV runtime study separated cold imports, model reuse, codec
  discovery, and inference costs.
- Fixed tutor cases verify evidence propagation, bounded retrieval, no-result
  honesty, and uncertainty repair through the active relay path.

Those results are not real-musician accuracy, calibrated uncertainty,
pedagogical quality, or learning outcomes. The project records those gaps
because hiding them would make the architecture less useful.

## The Next Research Question

Basic Pitch currently supplies transcription evidence, but transcription is
only one view of harmony. A direct chord model may preserve temporal harmonic
patterns that note transcription loses. Chroma can retain spectral evidence for
a weakly transcribed seventh. Beat and harmonic-change models may propose better
boundaries.

The next HorizonJam study asks:

> Can multi-view harmonic evidence outperform any single path on short
> musician performances while preserving interpretable uncertainty?

The tournament will compare the frozen HorizonJam baselines, Basic Pitch note
evidence, an owned CQT/chroma baseline, and an isolated large-vocabulary chord
model. Fusion happens only if paired errors demonstrate complementarity.

## Where HorizonJam Fits

Yousician and Simply Guitar provide mature curricula and interactive feedback.
Chord AI and Chordify analyze songs. Moises offers a broad musician toolset.
SoundGate publicly describes real-time guitar analysis and an AI tutor. These
products validate the category and set a high bar for consumer experience.

HorizonJam should not claim to have invented the AI music tutor. Its narrower
position is:

> **An inspectable AI music coach that connects its explanation to the musical
> evidence it observed.**

That is a differentiation hypothesis, not a claim that competitors cannot or
do not use similar internal methods.

## Why Open the Architecture

The important questions are larger than one application:

- How should uncertainty move from a detector into generated instruction?
- Which musical evidence should a tutor show to a learner?
- How can retrieval provenance remain inspectable?
- When does a deterministic check meaningfully constrain model output?
- Which detector errors cause the most pedagogical harm?
- How should researchers evaluate the chain rather than one component?

Opening the contracts, failure cases, benchmark protocol, and reproducibility
artifacts makes those questions testable. It also lets MIR researchers,
educators, musicians, accessibility experts, and product engineers challenge
the assumptions independently.

## What Open Source Means Here

The public repository is not ready for an open-source launch announcement just
because its code is visible. Before release it needs an explicit license,
third-party notices, dependency locks, dataset and corpus provenance, clean
artifacts, CI, a security policy, and a reproducible benchmark package.

The v3 tag is the frozen evidence baseline. Publication work and production
hardening proceed from it without rewriting the measured results.

## Invitation

The first useful contributions are not more features. They are:

- owned or clearly licensed short performance recordings and annotations;
- MIR baselines that implement the normalized research adapter;
- confidence-calibration and disagreement analysis;
- expert rubrics for musical correctness and pedagogical actionability;
- security and privacy review for musician audio; and
- reproducible environment and artifact tooling.

HorizonJam's goal is not to make an AI teacher sound certain. It is to make the
path from listening to teaching visible enough to test, improve, and trust.

## Sources

- [HorizonJam v3 baseline](../releases/V3_BASELINE.md)
- [HorizonJam evaluation context](../context/EVALUATION.md)
- [Multi-source detector tournament](../../research/detector_tournament/README.md)
- [Basic Pitch](https://github.com/spotify/basic-pitch)
- [LV-Chordia](https://github.com/openmirlab/lv-chordia)
- [SoundGate Guitar](https://apps.apple.com/us/app/soundgate-guitar/id6760704644)
- [Yousician](https://apps.apple.com/us/app/yousician-learn-play-guitar/id959883039)
- [Simply Guitar](https://apps.apple.com/us/app/simply-guitar-learn-guitar/id1476695335)
- [Chord AI](https://apps.apple.com/us/app/chord-ai-play-any-song/id1446177109)
- [Moises](https://apps.apple.com/us/app/moises-the-musicians-app/id1515796612)
- [Chordify](https://apps.apple.com/us/app/chordify-songs-chords-tuner/id1073624757)
