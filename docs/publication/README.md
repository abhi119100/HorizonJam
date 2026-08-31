# HorizonJam Research and Publication Workspace

HorizonJam is a research prototype for a simple but important question:

> **How can an AI music tutor give useful feedback without hiding uncertainty in what it heard?**

A musician records a short performance. HorizonJam analyzes the music, keeps track of what the detector actually observed, retrieves relevant music knowledge, and then asks a language model to explain or coach from that evidence.

The project is currently useful as both:

- a working systems prototype for evidence-grounded music tutoring; and
- a research platform for studying how errors and uncertainty in machine listening affect downstream AI feedback.

The repository does **not** yet claim state-of-the-art chord recognition, real-musician accuracy, improved learning outcomes, or production readiness.

## Start Here

### For paper reviewers and researchers

Read [RESEARCH_PAPER.md](RESEARCH_PAPER.md).

It presents the project in research-paper form with the problem, contributions, current measurements, study questions, limitations, and next experimental phase.

### For exact implementation and claim checking

Read [PAPER_DRAFT.md](PAPER_DRAFT.md).

This is the more technical source draft. It retains exact contracts, implementation details, current measurements, and the claim ledger used to prevent the paper from overstating what has been demonstrated.

### For open-source contributors

Read [CONTRIBUTE_RESEARCH.md](CONTRIBUTE_RESEARCH.md).

The highest-value contribution areas are currently real-performance evaluation, external chord-recognition baselines, interpretable harmonic analysis, uncertainty, retrieval evaluation, reproducibility, frontend research tooling, and accessibility.

## Research Story

The scientific story is intentionally narrow.

### Problem

A music tutor can produce fluent advice even when the audio-analysis stage is wrong.

### Hypothesis

Preserving the source, timing, warnings, and available uncertainty of musical observations should make downstream tutoring easier to inspect and less likely to overstate weak evidence.

### Current system

```text
performance
   ↓
music analysis
   ↓
timed evidence + uncertainty
   ↓
relevant music knowledge
   ↓
AI tutoring
   ↓
pre-delivery checks
```

### Current evidence

The project has controlled symbolic and synthetic chord experiments, real audio runtime measurements, deterministic evidence-propagation tests, bounded retrieval tests, and an end-to-end provider-backed prototype.

These measurements establish engineering behavior, not real-world learning effectiveness.

### Next study

The next research phase compares independent harmonic evidence sources:

- the current HorizonJam detector;
- the experimental Jaccard-based detector;
- Basic Pitch note evidence;
- a lightweight chroma-based baseline; and
- LV-Chordia as an isolated direct chord-recognition baseline after license and model review.

The study will first measure each system independently, then test whether their errors are complementary, and only then evaluate fusion.

## Publication Materials

| Document | Purpose |
|---|---|
| [RESEARCH_PAPER.md](RESEARCH_PAPER.md) | Accessible research-paper draft for reviewers and collaborators |
| [PAPER_DRAFT.md](PAPER_DRAFT.md) | Technical source draft and detailed claim ledger |
| [ABSTRACT.md](ABSTRACT.md) | Short abstract and bounded claims |
| [OPEN_SOURCE_POST.md](OPEN_SOURCE_POST.md) | Public architecture article |
| [COMPETITIVE_LANDSCAPE.md](COMPETITIVE_LANDSCAPE.md) | Dated product and related-work snapshot |
| [PUBLICATION_TO_PRODUCTION.md](PUBLICATION_TO_PRODUCTION.md) | Research-to-product release plan |
| [CONTRIBUTE_RESEARCH.md](CONTRIBUTE_RESEARCH.md) | Contributor and collaboration entry point |

## Evidence Sources

Publication claims should resolve to one of the following:

- `STATUS.md` for verified current state;
- `docs/releases/V3_BASELINE.md` for the frozen v3 baseline;
- `docs/context/EVALUATION.md` for methods and limitations;
- checked-in reports under `eval/` for measurements;
- source and tests for implemented behavior; and
- `research/detector_tournament/` for proposed multi-source experiments.

## What We Do Not Claim Yet

HorizonJam has not yet established:

- real-musician chord-recognition accuracy;
- calibrated confidence;
- superior teaching quality;
- improved learning outcomes;
- public deployment readiness; or
- App Store readiness.

This distinction is deliberate. The project aims to make claims that are easy to trace back to code, data, and experiments.

## Publication and Open-Source Readiness

Before a formal open-source release or archival publication, the project still needs:

- an explicit repository license;
- third-party code and model notices;
- model-weight provenance;
- dataset and audio-fixture licensing review;
- reproducible dependency environments;
- `CITATION.cff`;
- contribution and security policies;
- archived release DOI; and
- a completed real-performance evaluation.

## Collaboration

Researchers, engineers, musicians, teachers, and open-source contributors are welcome to participate.

Especially useful backgrounds include:

- music information retrieval;
- automatic chord recognition;
- automatic music transcription;
- digital signal processing;
- machine learning for audio;
- retrieval-augmented generation;
- human-computer interaction;
- music education;
- uncertainty and calibration;
- reproducible machine learning;
- accessibility; and
- developer tooling for research systems.

The project's goal is not to hide unfinished work. It is to make the system inspectable enough that other people can test, challenge, reproduce, and improve it.
