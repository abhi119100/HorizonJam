# Competitive and Related-Work Landscape

**Snapshot date:** 2026-08-30  
**Method:** official App Store descriptions, primary project repositories, and
original research papers. Product descriptions are marketing evidence, not
evidence of internal architecture or measured comparative performance.

## Product Categories

HorizonJam sits at the intersection of four established categories:

1. interactive music learning and curriculum;
2. conversational or AI-assisted coaching;
3. chord/song analysis; and
4. musician practice utilities and reference content.

The defensible product category is **AI music coach** or **intelligent music
tutor**, with Education as the likely primary store category and Music as the
adjacent category. Final store categorization requires platform review.

## Public Product Comparison

| Product | Publicly described primary job | Benchmark for HorizonJam | HorizonJam should not claim |
|---|---|---|---|
| SoundGate Guitar | real-time guitar detection, interactive fretboard, AI tutor, personalized guidance | closest consumer analogue; real-time UX and native product maturity | that SoundGate copied HorizonJam or lacks an evidence layer internally |
| Yousician | structured lessons and real-time listening feedback | curriculum, onboarding, exercise design, progress loops | parity in content, users, or learning evidence |
| Simply Guitar | beginner curriculum with app feedback | beginner usability and instructional sequencing | a stronger beginner course |
| Chord AI | song/file/microphone chord recognition, beat/voicing-oriented analysis | detection breadth and song-analysis utility | superior real-audio recognition without a shared benchmark |
| Chordify | synchronized song chords and large catalog | licensed content and play-along workflow | catalog competition without a licensing strategy |
| Moises | source separation, practice manipulation, chords, tempo, pitch, and backing tracks | breadth of musician tooling | equivalent production breadth |
| Ultimate Guitar | tabs, chords, lyrics, lessons, and catalog | content ecosystem and musician retention | catalog or tablature leadership |

Sources: official listings for [SoundGate](https://apps.apple.com/us/app/soundgate-guitar/id6760704644),
[Yousician](https://apps.apple.com/us/app/yousician-learn-play-guitar/id959883039),
[Simply Guitar](https://apps.apple.com/us/app/simply-guitar-learn-guitar/id1476695335),
[Chord AI](https://apps.apple.com/us/app/chord-ai-play-any-song/id1446177109),
[Chordify](https://apps.apple.com/us/app/chordify-songs-chords-tuner/id1073624757),
[Moises](https://apps.apple.com/us/app/moises-the-musicians-app/id1515796612),
and [Ultimate Guitar](https://apps.apple.com/us/app/ultimate-guitar-chords-tabs/id357828853).

## HorizonJam's Defensible Differentiation

The broad idea "AI listens and tutors" is not unique. HorizonJam's potentially
distinctive public architecture is the combination of:

- a replaceable detector boundary;
- normalized timed events with detector provenance and nullable confidence;
- a versioned performance-evidence packet;
- explicit uncertainty and warnings in tutor context;
- bounded retrieved text with source and record provenance;
- deterministic verification before streaming or speech delivery;
- a request-local trace for inspecting model input and evidence selection; and
- an L0-L7 evaluation model connecting perception errors to tutor and learner
  outcomes.

This is a **differentiation claim about HorizonJam's published design**, not an
exclusive novelty claim. A rigorous novelty statement requires a systematic
literature review and cannot infer competitors' private implementations.

## Positioning

Avoid:

- "the first AI guitar teacher";
- "state-of-the-art chord recognition";
- "learn faster with AI";
- "perfectly understands your playing"; and
- feature-count competition with lesson or song catalogs.

Prefer:

> **The AI music coach that shows its work.**

Supporting explanation:

> Record what you played, inspect the timed musical evidence, ask why it sounds
> the way it does, and receive guidance that preserves uncertainty and sources.

The initial audience should be an intermediate guitarist or musician who can
already play common material but wants theory, harmonic function, voice
leading, transition diagnosis, and targeted practice tied to their own
performance. This remains a product hypothesis requiring interviews and usage
evidence.

## Research Baseline Matrix

| System | Evidence family | Public license finding | HorizonJam role |
|---|---|---|---|
| Basic Pitch | polyphonic note transcription | Apache-2.0 repository | active v3 source; direct in-memory research adapter |
| BTC | direct chord sequence model | MIT repository | canonical isolated research baseline |
| LV-Chordia | large-vocabulary direct chords | MIT repository; weights still require artifact audit | first-wave external research candidate |
| CREMA | pretrained structured music estimators | BSD-2-Clause repository; package/model terms need reconciliation | later historical baseline |
| Chordino | NNLS chroma plus HMM/Viterbi | GPL-2.0-or-later | interpretable research baseline; distribution review required |
| HorizonJam CQT/chroma | direct spectral/profile evidence | repository-owned implementation over audited dependencies | first-wave interpretable baseline |
| `mir_eval` | MIR evaluation metrics | MIT repository | shared metric implementation |

Primary sources:

- [Basic Pitch repository and ICASSP paper](https://github.com/spotify/basic-pitch)
- [BTC repository and ISMIR 2019 paper implementation](https://github.com/ptnghia-j/BTC)
- [LV-Chordia repository](https://github.com/openmirlab/lv-chordia)
- [Large-Vocabulary Chord Transcription paper](https://archives.ismir.net/ismir2019/paper/000078.pdf)
- [CREMA repository](https://github.com/bmcfee/crema)
- [Chordino repository](https://github.com/shidephen/chordino)
- [`mir_eval` repository](https://github.com/mir-evaluation/mir_eval)

## Research Gap HorizonJam Can Address

Automatic chord-recognition papers generally optimize and report MIR metrics.
Consumer tutor descriptions emphasize interaction, curriculum, analysis, and
personalization. HorizonJam's paper can study the boundary between them:

> How do uncertain or conflicting musical observations propagate into
> retrieval, explanation, practice advice, and user-visible confidence?

A complete contribution would require:

1. paired detector outputs on the same licensed recordings;
2. error complementarity and calibration analysis;
3. fusion ablations against the strongest individual baseline;
4. tutor comparisons under controlled evidence packets;
5. expert musical/pedagogical ratings; and
6. transparent latency, cost, and failure reporting.

## Public-Timeline Claims

Prior research notes suggest HorizonJam was publicly described as an AI music
tutor in 2025, before some currently visible competitor launch artifacts. Do
not put a priority claim in the paper or launch post until each item is captured
in a durable provenance appendix with archived URLs, timestamps, authorship,
and the exact public claim. Public chronology cannot establish a competitor's
private development date or copying.

## Maintenance

Market facts change quickly. Recheck every product statement immediately before
submission or launch, record an access date, and remove volatile download,
rating, pricing, and version counts unless they are methodologically relevant.
