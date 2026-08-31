# HorizonJam: From Uncertain Music Analysis to Trustworthy AI Tutoring

**Research paper draft — HorizonJam v3**  
**Status:** work in progress; current real-musician evaluation is not yet complete

## Abstract

AI music tutors can listen to a performance and immediately produce fluent advice. The problem is that the advice may sound confident even when the underlying music analysis is wrong or uncertain. HorizonJam explores a simple research question: **can an AI music tutor preserve uncertainty from the audio-analysis stage and use that evidence to produce more trustworthy feedback?**

HorizonJam is a research prototype for short musician recordings. It analyzes a performance, represents the detected chords and related evidence, retrieves relevant music knowledge, and generates written or spoken tutoring feedback. Unlike a pipeline that passes only a final chord label to a language model, HorizonJam keeps information about timing, detector source, warnings, and confidence when that information is genuinely available. The tutor also keeps track of which reference material was retrieved and applies narrow checks before feedback is shown to the user.

Current experiments are intentionally limited. On a frozen 40-song synthetic post-transcription benchmark, an experimental Jaccard-based chord-matching method improved root, major/minor, seventh-chord, and MIREX scores over the existing hybrid path. A controlled audio-runtime study also showed that the Basic Pitch transcription path can complete short recordings quickly after warm-up, although cold-start overhead remains significant. These results do **not** establish real-musician accuracy, calibrated confidence, improved teaching quality, or learning gains.

The next study will compare several independent ways of understanding harmony from audio: note transcription, direct chord recognition, and interpretable chroma-based analysis. We will first measure each approach separately, then test whether their errors are complementary, and only then evaluate evidence fusion. HorizonJam is therefore presented as both an open research system and an experimental platform for studying how uncertainty in machine listening affects downstream AI tutoring.

## 1. Introduction

A music tutor that listens to a musician has to solve two different problems:

1. **What happened in the performance?**
2. **What should the musician understand or practice next?**

Modern systems can use machine listening for the first problem and a language model for the second. The combination is powerful, but it introduces a failure mode: an error in transcription or chord recognition can become a polished explanation that sounds more certain than the evidence deserves.

Consider a guitarist who plays a dominant seventh chord. If the audio system hears only the major triad, the language model may confidently explain the wrong harmony. The language model did not necessarily reason badly; it was given incomplete evidence.

HorizonJam studies how to make that boundary visible.

### Research question

> **How should an AI music tutor represent and preserve uncertain musical evidence before turning it into instruction?**

The project does not currently claim a new state-of-the-art chord detector. Instead, it focuses on the system connecting perception, musical interpretation, retrieval, and tutoring.

## 2. Research Contributions

HorizonJam currently makes four bounded contributions.

### 2.1 Evidence-preserving music analysis

Detected chord events keep their timing and detector identity. Confidence is included only when the detector genuinely provides meaningful confidence; otherwise it remains unknown rather than being invented. Warnings and uncertainty can travel with the analysis into the tutoring stage.

### 2.2 Evidence-grounded tutoring

The tutor receives the musician's question together with the performance analysis and a small set of retrieved music references. The selected reference text and its source are retained so that the system can distinguish between what was observed, what was retrieved, and what was generated.

### 2.3 Pre-delivery checks

Before feedback is delivered, HorizonJam applies narrow deterministic checks. For example, weak evidence should not be presented as certainty, and the tutor should not claim to have used retrieved material when no relevant material was found. These checks do not guarantee musical correctness; they are safeguards against specific known failures.

### 2.4 Layered evaluation

HorizonJam evaluates the system in stages instead of treating a fluent final answer as proof that the entire system worked. Audio handling, note transcription, chord recognition, retrieval, tutoring, runtime behavior, pedagogy, and learning outcomes are treated as separate questions.

## 3. System Overview

The current prototype follows this path:

```text
Musician records or uploads a short performance
                |
                v
        Audio transcription / analysis
                |
                v
        Timed musical evidence
                |
                v
      Relevant knowledge retrieval
                |
                v
         AI tutoring response
                |
                v
      Uncertainty / retrieval checks
                |
                v
       Written and optional speech
```

The current web prototype uses a browser interface, a Python backend, Basic Pitch for note transcription, rule-based chord analysis, a vector database for retrieval, a language model for tutoring, and optional text-to-speech. These technologies are replaceable; the research focus is the evidence passed between them.

## 4. Why Chord Recognition Is Still an Open Problem in HorizonJam

The current detector has improved through controlled experiments, but important limitations remain.

An earlier symbolic chord scorer rewarded a candidate when all tones in its template appeared in the observed notes. This produced a structural mistake: a major triad could receive the same perfect score as its dominant-seventh extension because the additional seventh tone was not penalized as unexplained evidence.

For example:

```text
Observed notes: D F# A C

D major explains: D F# A
D7 explains:      D F# A C
```

Under the old one-directional score, both candidates could receive the same match value. A Jaccard-based comparison, which considers both the expected and observed pitch classes, performed better in the frozen experiments and is now available as an experimental detector path. It is not the product default.

This result motivates the larger question: **should HorizonJam rely on a single path from note transcription to chord labels at all?**

## 5. Current Evidence

### 5.1 Symbolic chord experiments

A 96-case oracle benchmark evaluates chord classification from exact symbolic pitch sets. It exposed structural weaknesses in the original simple classifier and in the earlier advanced scoring rule. These experiments isolate chord classification from audio transcription and segmentation.

### 5.2 Jaccard detector experiment

On a frozen 40-song synthetic post-transcription benchmark, the experimental `rule_jaccard` path improved over the existing hybrid path:

| Metric | Hybrid | Jaccard |
|---|---:|---:|
| Root | 47.2% | **52.9%** |
| Major/minor | 38.9% | **52.9%** |
| Sevenths | 27.5% | **40.0%** |
| MIREX | 52.0% | **55.9%** |

These measurements are useful engineering evidence, but they are **not real-musician accuracy results** because the experiment is synthetic and post-transcription.

### 5.3 Audio runtime

The real Basic Pitch-backed path has also been measured on a controlled WAV fixture. A 3-second recording required roughly 10–13 seconds from a cold process in the recorded environment, while a same-process repeat completed in about 1.31 seconds. Warm tests for 3-, 10-, and 30-second audio completed in approximately 2.14, 5.57, and 10.44 seconds respectively.

This shows that real audio execution is feasible for research, while also identifying cold-start and environment overhead that must be improved for a polished product.

### 5.4 Tutor evidence checks

The current deterministic tutor test set verifies evidence propagation, bounded retrieval, retrieval-absence honesty, and uncertainty repair in fixed cases. These tests show that the system preserves and uses its evidence structure as designed. They do not establish that the tutor is pedagogically superior.

## 6. Next Study: Multi-Source Harmonic Evidence

The next research phase asks whether different ways of analyzing the same audio make different mistakes.

The first planned comparison includes:

- the current HorizonJam hybrid detector;
- the experimental Jaccard detector;
- Basic Pitch note evidence used directly in memory;
- a lightweight constant-Q transform/chroma baseline built with permissively licensed tools; and
- LV-Chordia as an isolated direct chord-recognition baseline after model and license review.

Later baselines may include BTC, CREMA, Chordino/NNLS Chroma, beat-aware segmentation, and source separation where appropriate.

### Research questions

**RQ1.** Which analysis approach performs best on short, owned or licensed musician recordings?

**RQ2.** Do transcription, direct chord recognition, and chroma analysis make complementary errors?

**RQ3.** Can combining independent evidence improve the best individual detector without unacceptable latency or complexity?

**RQ4.** Does representing detector disagreement reduce unsupported or overly confident tutoring claims?

**RQ5.** Do musicians and expert teachers find evidence-linked feedback more trustworthy and actionable than feedback based only on a hard chord label?

## 7. Evaluation Plan

The study will separate three kinds of evidence.

### Synthetic regression data

Existing generated examples will continue to catch regressions and isolate mathematical changes. They will not be reported as real-world performance.

### Real performance recordings

A small owned or clearly licensed dataset will include different chord qualities, inversions, strumming, arpeggiation, partial voicings, room noise, instruments, and recording devices. Ground-truth annotations will be created or independently checked before accuracy claims are made.

### Public research datasets

Public music-information-retrieval datasets may be added only after their audio, annotation, and redistribution terms are verified.

For each detector we plan to report chord-recognition metrics, latency, memory requirements, cold and warm startup behavior, dependency complexity, model provenance, and failure cases. Fusion will be evaluated only after the individual baselines are frozen.

## 8. From Detection to Tutoring

Better chord recognition matters only if it improves the tutoring experience.

A downstream study will therefore compare tutor responses under controlled evidence conditions:

1. verified or oracle musical evidence;
2. hard detector labels only;
3. labels plus warnings and available confidence;
4. agreement or disagreement between multiple detectors; and
5. the same conditions with and without retrieved music references.

Expert raters can then evaluate musical correctness, consistency with the evidence, appropriate uncertainty, usefulness, and practice relevance. A later musician study can examine trust and practice behavior. Claims about learning improvement would require a separate longitudinal experiment.

## 9. Open Research and Reproducibility

HorizonJam is intended to become a reproducible public research platform. Before describing the repository as fully open source, the project still needs an explicit repository license and a complete audit of distributed code, model weights, datasets, retrieved documents, vector-store contents, and test media.

The publication release should include:

- a clear software license;
- contribution and security guidance;
- `CITATION.cff`;
- third-party notices;
- reproducible dependency environments;
- exact model and dataset provenance;
- frozen benchmark configurations;
- machine-readable experimental results; and
- an archived release with a persistent identifier.

Contributors are especially welcome around music-information retrieval, chord recognition, audio evaluation, real-performance annotation, uncertainty, retrieval evaluation, frontend research tooling, reproducibility, and accessibility.

## 10. Limitations

The present evidence is deliberately incomplete.

HorizonJam does not yet establish:

- real-musician chord-recognition accuracy;
- calibrated confidence estimates;
- superior tutoring quality;
- improved learning outcomes;
- public deployment readiness; or
- App Store readiness.

The current web backend also requires stronger authentication, upload isolation, quotas, retention/deletion controls, dependency locking, and provenance review before public deployment.

## 11. Conclusion

HorizonJam treats AI music tutoring as more than a language-generation problem. The quality of the lesson depends on the quality of the musical evidence underneath it.

The project's central idea is therefore simple: **the tutor should know what the listening system observed, what it is uncertain about, and where its supporting knowledge came from before it gives advice.**

The current v3 prototype demonstrates this evidence-preserving architecture and provides controlled synthetic and structural measurements. The next phase moves to real performance recordings and independent harmonic-analysis baselines. The resulting system can serve both as a music-learning product prototype and as a research platform for studying how uncertainty in machine listening propagates into AI-generated instruction.

## References

1. Bittner et al. *A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription and Multipitch Estimation*. ICASSP 2022. Basic Pitch.
2. Park et al. *A Bi-Directional Transformer for Musical Chord Recognition*. ISMIR 2019.
3. Wu et al. *Large-Vocabulary Chord Transcription via Chord Structure Decomposition*. ISMIR 2019.
4. McFee and Bello. *CREMA: Convolutional and Recurrent Estimators for Music Analysis*. 2017.
5. Mauch and Dixon. *Approximate Note Transcription for the Improved Identification of Difficult Chords*. ISMIR 2010.
6. Raffel et al. *mir_eval: A Transparent Implementation of Common MIR Metrics*. ISMIR 2014.
7. Lewis et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020.

For exact source links, implementation evidence, and the complete publication claim ledger, see `docs/publication/PAPER_DRAFT.md`, `STATUS.md`, and `docs/context/EVALUATION.md`.