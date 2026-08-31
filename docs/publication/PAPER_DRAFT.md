# HorizonJam: Evidence-Grounded AI Music Tutoring from Uncertain Performance Analysis

**Draft type:** systems/architecture paper with an empirical research plan  
**Baseline:** HorizonJam v3.0 research baseline  
**Draft date:** 2026-08-30  
**Author metadata:** full publication name, affiliation, and ORCID pending

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

## 1. Introduction

Applications can now listen to a musician, estimate notes or chords, and use a
language model to produce natural-language feedback. This composition creates
a specific systems problem: fluent tutoring can conceal uncertainty or errors
introduced by audio capture, transcription, segmentation, harmonic labeling,
retrieval, or prompt assembly. A response may be linguistically plausible even
when its foundational musical observation is weak.

HorizonJam studies a narrower question than generic AI-assisted music
learning:

> How should a music tutor represent, preserve, and communicate uncertain
> machine-listening evidence before turning it into instruction?

The current prototype accepts a short browser recording or uploaded file,
produces timed chord evidence and key/guitar context, retrieves bounded musical
knowledge, generates a tutoring response, verifies limited grounding rules,
and optionally synthesizes speech. The implementation is intentionally
modular: the detector, evidence assembler, retrieval system, model, and speech
layer have distinct contracts and can fail independently.

The paper makes four bounded contributions:

1. **An evidence boundary for music tutoring.** A normalized chord-event API
   and versioned `PerformanceEvidence` packet retain timing, detector
   provenance, warnings, and confidence only when supplied by the detector.
2. **A bounded evidence-to-language harness.** Retrieval preserves selected
   source text and provenance; generated text is accumulated and checked for
   uncertainty and retrieval honesty before any sentence is delivered.
3. **A layered evaluation framework.** Tests and reports separate audio,
   transcription, harmony, retrieval, reasoning, pedagogy, product behavior,
   and learning outcomes instead of treating a fluent response as end-to-end
   correctness.
4. **A preregisterable multi-source research protocol.** A detector tournament
   is specified to compare transcription, direct-chord, and DSP/chroma paths,
   measure complementary errors, and test fusion only after individual
   baselines pass licensing and runtime gates.

The first three are implemented in v3. The fourth is a protocol and research
hypothesis; no fusion result is claimed.

## 2. Related Work and Product Context

### 2.1 Music transcription and chord recognition

Basic Pitch provides a lightweight, instrument-agnostic polyphonic
audio-to-MIDI model and is the current transcription source in HorizonJam's
active hybrid path [1]. Direct automatic chord recognition offers an
independent evidence family. BTC applies bidirectional self-attention to audio
features for chord recognition [2]. Large-vocabulary chord transcription by
structure decomposition predicts richer harmonic structure and is available
through the modern LV-Chordia inference package [3]. CREMA provides pretrained
convolutional/recurrent estimators for music analysis [4]. Chordino supplies an
interpretable NNLS-chroma and HMM/Viterbi baseline, although its GPL license
requires a separate distribution decision [5]. `mir_eval` supplies established
chord-comparison metrics used by HorizonJam's synthetic harness [6].

HorizonJam does not claim a new state-of-the-art chord-recognition model. Its
research opportunity is to compare and potentially combine heterogeneous
evidence while preserving source identity and uncertainty downstream.

### 2.2 Retrieval-grounded generation

Retrieval-augmented generation conditions model output on retrieved external
records [7]. In HorizonJam, retrieval is not treated as proof of correctness.
Selected text, source, record identifier, rank, relevance, and metadata are
bounded and retained in an inspectable packet. Retrieved text is explicitly
treated as untrusted context rather than executable instruction.

### 2.3 Consumer music-learning systems

Official product descriptions show several mature categories: curriculum and
real-time feedback in Yousician and Simply Guitar; song-oriented harmonic
analysis in Chord AI and Chordify; broad musician tooling in Moises; and
real-time AI guitar coaching in SoundGate [8-13]. These descriptions establish
feature overlap, not internal architecture. We found no public basis for
claiming that a competitor does or does not use an equivalent evidence schema,
retrieval design, or verification layer.

HorizonJam is therefore positioned as an **inspectable AI music coach** rather
than as the first AI guitar tutor, the largest lesson library, or the strongest
song-analysis utility.

## 3. System Architecture

### 3.1 Runtime path

```text
browser recording or file + question
  -> bounded upload and audio normalization [production gate remains open]
  -> detection.run_detection()
  -> normalized timed chord events
  -> key and guitar context
  -> PerformanceEvidence v1
  -> intent and evidence-strength assessment
  -> bounded retrieval with source provenance
  -> explicit tutor context
  -> one language-model generation
  -> deterministic verification and repair
  -> written response
  -> optional sentence-level speech
```

The active browser implementation uses Next.js, a FastAPI upload/WebSocket
relay, Python MIR components, Chroma retrieval, an OpenAI language model, and
optional local or provider-backed speech. These choices are implementation
details rather than requirements of the evidence architecture.

### 3.2 Detector boundary

All application detection is routed through `detection.run_detection()`. A
normalized event contains:

```json
{
  "start": 4.0,
  "end": 6.0,
  "chord": "D:7",
  "confidence": 0.61,
  "source_detector": "example_detector"
}
```

Events are sorted, positive-duration, and non-overlapping after normalization.
The boundary also returns the selected detector and warnings. Confidence is
nullable: the system must not convert a fixed rule weight or raw model score
into calibrated certainty without evidence.

### 3.3 Performance evidence

`PerformanceEvidence` records a schema version, audio identifier, ordered chord
events, progression, estimated key, guitar context, detector identity,
warnings, and explicit uncertainty notes. Detector alternatives are included
only if a detector supplied them. This prevents the language model from
inventing a richer perception state than the machine-listening layer produced.

### 3.4 Retrieval and tutor context

The question and ordered performance evidence determine retrieval intent and a
query. Selection is bounded to at most three records and 3,000 document
characters in the current implementation. Each selected record retains its
actual text and provenance. The model receives explicit sections for the user
question, performance evidence, retrieved knowledge, uncertainties/warnings,
and output expectations.

### 3.5 Verification before delivery

The streaming model response is accumulated before user-visible delivery.
Deterministic checks then enforce two currently testable properties:

- low-strength evidence must produce an uncertainty caveat; and
- the response must not claim retrieval occurred when no evidence was selected.

Only the verified/repaired response is split into sentence chunks for the
WebSocket and optional TTS. These checks are deliberately narrow. They do not
prove that a chord label, harmonic explanation, or practice recommendation is
correct.

## 4. Evaluation Framework

HorizonJam separates evaluation into eight levels:

| Level | Target | Current v3 evidence |
|---|---|---|
| L0 | audio validation/normalization | partial source and controlled-WAV checks |
| L1 | note transcription | runtime/equivalence hashes for one WAV; no labeled accuracy |
| L2 | chords, segments, key | oracle and synthetic reports; no licensed real corpus |
| L3 | retrieval | fixed relevance, provenance, pollution, and no-result cases |
| L4 | tutor reasoning | fixed grounding and uncertainty checks; no expert/live-model study |
| L5 | pedagogy | not evaluated |
| L6 | reliability, latency, cost, UX | partial build/runtime/E2E evidence |
| L7 | learning outcomes | not evaluated |

This hierarchy prevents an L3 or L4 structural pass from being reported as an
L7 learning result.

### 4.1 Existing v3 measurements

The frozen reports currently support the following statements:

- The 96-case symbolic oracle exposed severe quality failures in the active
  simple classifier and an asymmetric subset bias in the advanced scorer.
- Under frozen candidates and non-match terms, Jaccard matching achieved 98.8%
  supported complete exact and 97.2% complete-seventh exact in the oracle
  formulation experiment.
- In a 40-song synthetic post-transcription comparison, opt-in
  `rule_jaccard` improved root from 47.2% to 52.9%, MajMin from 38.9% to 52.9%,
  sevenths from 27.5% to 40.0%, and MIREX from 52.0% to 55.9% relative to the
  frozen hybrid path.
- A controlled BasicPitch-backed WAV completed in 1.31-2.14 seconds warm for a
  3-second input on the recorded machine, with materially slower cold starts.
- Thirteen deterministic tutor cases and focused integration tests verify
  evidence propagation, bounded retrieval behavior, no-result honesty, and
  uncertainty repair.

These are engineering and structural measurements. The synthetic audio is not
a proxy for diverse real musicians, and post-transcription injection bypasses
the audio transcription problem.

## 5. Multi-Source Harmonic Evidence Study

### 5.1 Research questions

- **RQ1:** Which evidence family performs best on short, owned or licensed
  musician recordings under root, quality, seventh, segmentation, and MIREX
  metrics?
- **RQ2:** Do transcription, direct-chord, and DSP/chroma paths make
  complementary errors?
- **RQ3:** Can bounded fusion improve the best individual detector without
  unacceptable latency, memory, licensing, or calibration costs?
- **RQ4:** Does exposing detector disagreement and uncertainty reduce
  unsupported tutor claims?
- **RQ5:** Do musicians or expert teachers judge evidence-linked feedback as
  more trustworthy and actionable than hard-label-only feedback?

### 5.2 First-wave baselines

The first executable wave is intentionally small:

1. frozen HorizonJam `hybrid`;
2. frozen opt-in `rule_jaccard`;
3. Basic Pitch in-memory note evidence;
4. a HorizonJam-owned Librosa CQT/chroma baseline; and
5. isolated LV-Chordia after artifact and dependency audit.

BTC, CREMA, Chordino, beat tracking, source separation, and known-recording
alignment remain later baselines or ablations. This ordering avoids adding
dependencies faster than errors can be attributed.

### 5.3 Dataset and protocol

The final protocol should be frozen before result collection and include:

- existing synthetic fixtures for regression only;
- guitar-oriented synthetic voicings and perturbations;
- an owned Real Performance Demo Pack with multiple players, instruments,
  rooms, devices, noise conditions, voicings, arpeggios, and explicit no-chord
  regions; and
- a licensed public evaluation corpus after redistribution and annotation
  rights are verified.

Each run records source revision, dependency lock, model/checkpoint hash,
parameters, hardware, cold/warm state, latency, memory, warnings, failures, and
normalized outputs. Individual baselines precede complementarity analysis;
fusion precedes downstream tutoring only if it beats the strongest individual
under a frozen decision rule.

## 6. Downstream Tutor Study

The detector study should be connected to instruction through controlled
evidence conditions:

1. oracle chord evidence;
2. hard detector labels only;
3. labels plus source/confidence/warnings;
4. multi-source agreement/disagreement evidence; and
5. the same conditions with and without bounded retrieved sources.

Expert raters should assess musical correctness, evidence consistency,
uncertainty calibration, actionability, pedagogical appropriateness, and harm
from false certainty. Inter-rater agreement, blinded conditions, model/prompt
versions, latency, and cost should be reported. A later musician study may
measure trust and practice behavior; learning-outcome claims require a separate
longitudinal design.

## 7. Open-Source and Reproducibility Plan

The repository can be called open source only after it has an explicit license
and all distributed code, corpora, vector stores, model weights, and fixtures
have compatible provenance. The reproducible release should include:

- a minimal source tree rather than tracked environments/build outputs;
- lockfiles for production and isolated research adapters;
- model and dataset acquisition scripts that verify hashes and terms;
- a `CITATION.cff`, third-party notices, security policy, and contribution guide;
- a frozen benchmark configuration and machine-readable reports;
- a signed source tag and archived DOI; and
- CI for tests, dependency review, secret scanning, and artifact verification.

## 8. Limitations, Ethics, and Safety

HorizonJam v3 is not ready for public deployment. The current relay lacks the
required authentication, quota, upload-isolation, retention, deletion, and cost
controls. User recordings may contain identifiable voices, original music, or
background speech. RAG corpora and generated embeddings require provenance,
consent, tenancy, and deletion policies.

Pedagogical feedback can be harmful when perception is wrong or advice is
overconfident. The deterministic verifier covers only explicit rules and must
not be described as a correctness guarantee. Accessibility, minors' privacy,
model-provider data handling, and App Store disclosures require dedicated
review before a public study or product release.

## 9. Claim Ledger

| Claim | Status | Evidence needed for stronger wording |
|---|---|---|
| Versioned evidence-grounded tutor architecture exists | implemented/verified | retain contract and integration tests |
| Retrieval preserves bounded text and provenance | implemented/verified | labeled corpus relevance study |
| Tutor output receives pre-delivery uncertainty/retrieval checks | implemented/verified | expert correctness and adversarial study |
| Jaccard improves frozen synthetic post-transcription results | verified synthetic result | licensed real-audio comparison |
| Multi-view evidence is complementary | hypothesis | paired detector error analysis |
| Fusion improves chord recognition | hypothesis | frozen ablation and significance analysis |
| Evidence improves tutor trust/correctness | hypothesis | blinded expert and musician study |
| HorizonJam improves learning | unsupported | longitudinal outcome study |
| HorizonJam is production/App Store ready | false for v3 | pass security, privacy, reliability, and store gates |

## 10. Conclusion

HorizonJam reframes AI music tutoring as an evidence-propagation problem. The
prototype makes detector output, retrieval, uncertainty, and limited response
verification inspectable across the path from performance to instruction. Its
current contribution is an architecture and evaluation harness, not a claim of
superior real-audio recognition or pedagogy. The next research phase will test
whether heterogeneous harmonic evidence supplies complementary value and
whether representing that uncertainty improves downstream tutoring.

## References

1. Bittner et al. [A Lightweight Instrument-Agnostic Model for Polyphonic Note
   Transcription and Multipitch Estimation](https://arxiv.org/abs/2203.09893),
   ICASSP 2022; [Basic Pitch repository](https://github.com/spotify/basic-pitch).
2. Park et al. [A Bi-Directional Transformer for Musical Chord
   Recognition](https://github.com/ptnghia-j/BTC), ISMIR 2019.
3. Wu et al. [Large-Vocabulary Chord Transcription via Chord Structure
   Decomposition](https://archives.ismir.net/ismir2019/paper/000078.pdf), ISMIR
   2019; [LV-Chordia package](https://github.com/openmirlab/lv-chordia).
4. McFee and Bello. [CREMA: Convolutional and Recurrent Estimators for Music
   Analysis](https://github.com/bmcfee/crema), 2017.
5. Mauch and Dixon. [Approximate Note Transcription for the Improved
   Identification of Difficult Chords](https://github.com/shidephen/chordino),
   ISMIR 2010.
6. Raffel et al. [mir_eval: A Transparent Implementation of Common MIR
   Metrics](https://github.com/mir-evaluation/mir_eval), ISMIR 2014.
7. Lewis et al. [Retrieval-Augmented Generation for Knowledge-Intensive NLP
   Tasks](https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html),
   NeurIPS 2020.
8. [SoundGate Guitar official App Store listing](https://apps.apple.com/us/app/soundgate-guitar/id6760704644).
9. [Yousician official App Store listing](https://apps.apple.com/us/app/yousician-learn-play-guitar/id959883039).
10. [Simply Guitar official App Store listing](https://apps.apple.com/us/app/simply-guitar-learn-guitar/id1476695335).
11. [Chord AI official App Store listing](https://apps.apple.com/us/app/chord-ai-play-any-song/id1446177109).
12. [Moises official App Store listing](https://apps.apple.com/us/app/moises-the-musicians-app/id1515796612).
13. [Chordify official App Store listing](https://apps.apple.com/us/app/chordify-songs-chords-tuner/id1073624757).
