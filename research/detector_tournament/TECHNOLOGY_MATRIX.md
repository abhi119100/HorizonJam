# Technology Matrix

Audited 2026-08-30 from primary project repositories/documentation. Package
installation, model execution, benchmark claims, and commercial suitability
remain unverified until their corresponding gates run.

Verdicts describe the next research action, not production approval.

| Candidate | Role | Code/weights finding | Runtime/install finding | Verdict |
|---|---|---|---|---|
| HorizonJam `hybrid` | v3 product baseline | repository-owned; no active ML artifact | already measured | `BENCHMARK_NOW` |
| HorizonJam `rule_jaccard` | v3 opt-in symbolic baseline | repository-owned | controlled 3s warm 1.31s; BasicPitch-backed | `BENCHMARK_NOW` |
| BasicPitch direct evidence | note events/tensors | Apache-2.0 code; installed 0.4.0 ONNX artifact | local Python 3.13 path works although upstream lists through 3.11 | `BENCHMARK_NOW`, `PRODUCT_CANDIDATE` |
| Librosa CQT/chroma | owned DSP baseline | permissive library already in v3 environment | no new heavyweight runtime; must profile | `BENCHMARK_NOW`, `PRODUCT_CANDIDATE` |
| LV-Chordia | direct large-vocabulary chords | repository says MIT and bundles five weights; weight lineage still needs an artifact-level audit | modern PyTorch package; supports local files and URLs; URL mode must be disabled | `BENCHMARK_NOW` in isolation, `PRODUCT_CANDIDATE` pending audit |
| BTC-ISMIR19 | canonical direct sequence baseline | MIT source; pretrained checkpoint availability/rights not established by the repository README | PyTorch >=1.0/librosa >=0.6-era stack | `BENCHMARK_LATER`, `RESEARCH_ONLY` initially |
| CREMA | direct structured chord baseline | repository reports BSD-2-Clause while package metadata says ISC; packaged model rights need resolution | alpha package; Python classifiers stop at 3.9; TensorFlow/Keras/pumpp stack | `BENCHMARK_LATER`, `RESEARCH_ONLY` initially |
| Chordino/NNLS Chroma | interpretable DSP baseline | GPL-2.0-or-later | native Vamp plugin/Sonic Annotator integration | `RESEARCH_ONLY` unless distribution review changes scope |
| Essentia HPCP | alternate DSP evidence | AGPL-3.0-or-later default licensing | native dependency and separate commercial terms | `RESEARCH_ONLY` |
| madmom | legacy beat/downbeat baseline | source and model licenses differ; model provenance needs direct audit | old Python/NumPy compatibility; current Beat This docs require a Git install for DBN mode | `BENCHMARK_LATER`, `RESEARCH_ONLY` |
| Beat This | beat/downbeat proposals | MIT code and published weights; authors flag training-data implications | PyTorch; 8.1MB small or 78MB main models; downloads weights | `BENCHMARK_LATER` after harmonic baselines |
| Demucs | mixed-song source separation | MIT code; model artifact rights need separate review | upstream repository archived/unmaintained; expensive and unnecessary for solo guitar | `RESEARCH_ONLY`, mixed-song Mode A only |
| ShazamKit | known-recording identity/alignment | governed by Apple SDK/service terms, not open-source detector licensing | Apple platforms plus Android SDK; catalog service credentials required | `PRODUCT_CANDIDATE` for Mode B only |
| GuitarSet | real guitar evaluation candidate | project repository is MIT; paper states CC BY 4.0, but audio redistribution terms must be checked at the dataset host | 360 annotated excerpts; download/provenance workflow not yet audited | `BENCHMARK_LATER` after provenance gate |

## Required Field Detail

### BasicPitch

- Purpose/output: polyphonic note events, onset/end, pitch, amplitude,
  pitch-bend data, PrettyMIDI, and frame/onset/contour tensors; no chord
  vocabulary.
- Model/offline: model serializations are packaged; v3 selects bundled ONNX and
  requires no inference network.
- Compute/latency: CPU works; v3 measured cold 3s at 10.48-13.03s and warm 3s
  at 1.31-2.14s on the recorded machine.
- Confidence: amplitudes and tensors are evidence, not calibrated chord
  confidence.
- Suitability: strong product and research note-evidence candidate; direct
  in-memory adapter should precede any MIDI-removal production change.

### LV-Chordia

- Purpose/output: time-aligned direct chord JSON with submission, ISMIR2017,
  and full large-vocabulary dictionaries; no documented calibrated confidence
  in the simple output example.
- Model/offline: repository says five bundled checkpoints, about 28MB total,
  and an `LVChordiaSession` reusable-model API.
- Compute/latency: CPU and CUDA are documented; project performance statements
  are expectations only until HorizonJam measures cold/warm 3/10/30s runs.
- Network: local inference can be offline, but URL inputs can download content
  and are prohibited in the adapter.
- Suitability: best immediate external direct-chord research candidate;
  product status remains conditional on checkpoint/dependency audit.

### BTC

- Purpose/output: direct major/minor or larger-vocabulary frame/segment chord
  recognition with `.lab` and MIDI outputs.
- Model/offline: source is available; an exact redistributable checkpoint and
  its hash/license are not established.
- Compute/latency: old PyTorch/CQT pipeline, CPU/GPU capability and current
  latency unknown; must run in a legacy isolated environment.
- Confidence: internal model scores may exist, but no HorizonJam adapter or
  calibration evidence exists.
- Suitability: important canonical research baseline, weak near-term product
  candidate until maintenance and artifact issues are resolved.

### CREMA

- Purpose/output: direct file or in-memory analysis to JAMS; pretrained chord
  model supports structured chord/bass output according to its model docs.
- Model/offline: package data includes model artifacts; rights and exact hashes
  require audit.
- Compute/latency: TensorFlow/Keras stack with advertised Python classifiers
  through 3.9; CPU/GPU and latency are unmeasured on HorizonJam fixtures.
- Confidence: retain only model-supplied observations in raw research output;
  do not map them to HorizonJam confidence without calibration.
- Suitability: valuable historical large-vocabulary baseline; isolated
  research first, no current product recommendation.

### Chordino / NNLS Chroma

- Purpose/output: Vamp features including NNLS chroma and timestamped chord
  labels with an interpretable profile/HMM pipeline.
- Model/offline: no neural checkpoint; local native plugin execution.
- Compute/latency: CPU-oriented, expected lightweight but unmeasured on current
  Windows; native host/build complexity is material.
- Confidence: no comparable calibrated confidence is assumed.
- Suitability: strong interpretable research baseline; GPL terms make direct
  product distribution a separate legal/architecture decision.

### HorizonJam-Owned DSP/Chroma

- Purpose/output: fixed CQT chroma, optional bass chroma, tuning, and
  change-point evidence feeding an inspectable chord-profile baseline.
- Model/offline: no pretrained model; Librosa is already installed and local.
- Compute/latency: CPU; must record feature, scoring, and temporal-decoder cost.
- Vocabulary/confidence: begin with a frozen bounded vocabulary; expose profile
  scores/margins as raw evidence, not calibrated probability.
- Suitability: immediate product-safe research candidate if dependency license,
  parameters, and behavior are documented.

### Beat / Downbeat

- Purpose/output: Beat This emits beat/downbeat times and can expose framewise
  logits; it is segmentation evidence, not a chord detector.
- Model/offline: checkpoints are downloaded unless explicitly acquired and
  pinned; then inference can be local.
- Compute/latency: CPU/GPU PyTorch, small/main checkpoints around 8.1/78MB;
  runtime unmeasured.
- Confidence: frame logits remain boundary evidence and are not chord
  confidence.
- Suitability: later complementarity/segmentation experiment after harmonic
  detector baselines are stable.

### Demucs

- Purpose/output: vocals, drums, bass, and accompaniment stems for mixed-song
  analysis; no chord vocabulary or confidence.
- Model/offline: downloaded pretrained models can run locally after acquisition;
  model terms remain an open gate.
- Compute/latency: CPU/GPU, large and expensive relative to short solo audio;
  repository is archived and maintenance is limited.
- Suitability: research-only ablation for mixed recordings, excluded from solo
  guitar and the first tournament wave.

### ShazamKit

- Purpose/output: song/custom-catalog match, metadata, and alignment timecode;
  no notes, chord vocabulary, or harmonic confidence.
- Model/network/platform: official SDK/service on Apple platforms and Android;
  catalog matching requires Apple service configuration, while custom catalog
  behavior follows its own API path.
- Latency: service/device behavior must be measured in a future Mode B client,
  not in the detector tournament.
- Suitability: product candidate for known-song alignment only; not a research
  baseline for Mode A chord recognition.

## Minimal First Wave

1. Freeze the v3 `hybrid` and `rule_jaccard` outputs.
2. Add a research adapter over BasicPitch's existing in-memory note evidence.
3. Build one Librosa CQT/chroma baseline with fixed, inspectable parameters.
4. Audit and execute LV-Chordia in its own locked environment.

Do not add BTC, CREMA, Chordino, beat tracking, source separation, or fusion to
the first executable wave. That keeps the first comparison small enough to
attribute errors and dependency cost.
