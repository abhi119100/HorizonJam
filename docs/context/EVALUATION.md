# Evaluation Context

## Coverage Hierarchy

| Level | Question | Current coverage | Evidence / gap |
|---|---|---|---|
| L0 input/audio | Can files be validated, decoded, and normalized? | `PARTIAL_EVALUATION` | source checks plus manual mic plan; no automated malformed/oversized/codec matrix |
| L1 transcription | Are notes/pitches/timings correct? | `PARTIAL_EVALUATION` | runtime/equivalence hashes exist for one controlled WAV, but no labeled note-level accuracy metric exists |
| L2 harmony | Are chords, segments, and key correct? | `PARTIAL_EVALUATION` | 96-case oracle classifier benchmark plus 40 synthetic sine progressions with `mir_eval`; no real labeled corpus |
| L3 retrieval | Are retrieved records relevant, complete, and attributable? | `PARTIAL_EVALUATION` | 13 fixed cases include relevant retrieval, pollution rejection, provenance, and no-result behavior; no expert-labeled corpus metrics |
| L4 tutor reasoning | Is guidance factual, evidence-consistent, grounded, and uncertainty-aware? | `PARTIAL_EVALUATION` | 16 focused tests and 13 deterministic cases cover assembly and rule-based verification; no live-model/expert quality study |
| L5 pedagogy | Is advice actionable and musically appropriate? | `NO_EVALUATION` | no expert/user rubric |
| L6 product | Is the system reliable, fast, affordable, and usable? | `PARTIAL_EVALUATION` | service-dependent `_e2e_smoke.py` and manual mic plan; no measured latency/cost/reliability suite |
| L7 user outcome | Does the musician learn or improve? | `NO_EVALUATION` | no longitudinal or controlled user evidence |

Do not claim L7 outcomes from model output quality or user-interface completion.

## L0/L1 Single-WAV Runtime Gate

`python eval/benchmark_audio_path.py` exercises a controlled 3-second WAV
through `detection.run_detection(detector="rule_jaccard")`, captures fresh
Process A/B startup, same-process repeats, and warm 3/10/30-second scaling, and
writes `eval/audio_path_benchmark.json` plus Markdown. On the measured Windows
11/Python 3.13/BasicPitch 0.4.0/ONNX Runtime 1.22 environment, cold 3-second
totals were 13.03 and 10.48 seconds; the same-process repeat was 1.31 seconds;
warm 3/10/30-second totals were 2.14/5.57/10.44 seconds.

The pre-optimization controlled run took 30.96 seconds, after an earlier run
had exceeded 150 seconds. The measured causes were pathological Numba cache
validation under user site-packages and about 15 seconds of unconditional
`audioread` backend discovery before SoundFile WAV decoding. A process-local
cache location, reusable ONNX model, and SoundFile-gated codec-probe bypass
preserve the recorded note-event, model-output, and normalized-chord hashes.
Decision: `F. MIXED`, with environment, preprocessing, and cold-start
contributors. This is execution/equivalence evidence, not note or chord
accuracy evidence.

## L2 Synthetic Harness

```text
eval/synth_dataset.py
  -> 40 MIDI progressions + Harte .lab labels + sine WAVs
  -> eval/evaluate_chords.py
       -> detection.run_detection(detector=...)
       -> normalized intervals
       -> mir_eval chord metrics
  -> eval/report.json + eval/report.md
  -> engineering claims about synthetic behavior only
```

Metrics include root, MajMin, sevenths, MIREX, and WCSR. The checked-in report records 40/40 completed files for all three detectors. It also records 32 production and 38 hybrid/rule normalization warnings.

Known checked-in confusion patterns include dominant seventh chords mapped to major triads and transposition-sensitive failures. Hybrid and rule/Viterbi results match because there is no trained model artifact.

## L2 Oracle Classifier Harness

```text
exact MIDI pitch sets for 8 qualities x 12 roots
  -> eval/evaluate_oracle_classifier.py
       -> AST-extracted current simple and advanced classifier functions
       -> root / quality / exact metrics
       -> per-root, per-quality, confusion, inversion, duplication, omission evidence
  -> eval/oracle_classifier_report.json + eval/oracle_classifier_report.md
```

This isolates symbolic classification from audio, BasicPitch, segmentation,
temporal decoding, retrieval, and tutoring. The active simple baseline is 55.2%
root, 32.3% quality, and 28.1% exact. The offline advanced scorer is 97.9%
root, 50.0% quality, and 50.0% exact. Both fail every complete dominant-seventh
case. These are classifier-ceiling measurements, not audio-recognition results.

## L2 Advanced Scorer Forensics

```text
96 complete oracle chords
  -> eval/analyze_advanced_scorer.py
       -> all 85 advanced candidates per baseline case
       -> exact score decomposition and source-score reconciliation
       -> key, score-term, bass/inversion, margin, and diminished diagnostics
  -> eval/advanced_scorer_forensics.json + eval/advanced_scorer_forensics.md
```

The scorer uses `|input intersect template| / |template|` plus bass, sparse key
priors, suspension adjustment, and a three-note seventh complexity penalty.
There is no penalty for unexplained input tones. Nine dominant sevenths tie
their major triad and lose by template order; E7, A7, and B7 lose by positive
major-triad key priors. No existing single-term ablation recovers a dominant
seventh, and no diminished template exists. This remains offline evidence.

## L2 Match Formulation Benchmark

```text
complete and perturbed oracle pitch sets
  -> eval/compare_match_formulations.py
       -> exact AST-loaded advanced candidate inventory and frozen context terms
       -> baseline coverage, F1, Jaccard, bounded penalties, specificity tie rule
       -> exact, per-quality, per-root, margin, and robustness comparisons
  -> eval/match_formulation_report.json + eval/match_formulation_report.md
```

Jaccard wins the frozen decision rule with 98.8% supported complete exact,
97.2% complete seventh exact, and 76.1% mean supported robustness. The baseline
is reproduced with zero winner mismatches and zero candidate-score error. The
experiment does not change production code, candidate vocabulary, key priors,
bass scoring, suspension handling, or complexity penalties. Its decision is
therefore evidence for a production-scoped follow-up, not activation evidence.

## L2 Production-Path Jaccard Experiment

`rule_jaccard` is an explicit non-default detector mode routed through
`detection.run_detection()`. It keeps the hybrid transcription, segmentation,
event grouping, smoothing, adapter, and normalization path, but selects the
advanced scorer with Jaccard pitch-set matching. `hybrid` and `rule_viterbi`
retain the simple classifier.

`eval/evaluate_jaccard_detector_path.py` injects the frozen paired MIDI at the
transcription boundary to compare baseline and Jaccard without claiming audio
accuracy. A local MIDI note-name helper removed unnecessary lazy
`librosa.core.notation`/Numba initialization while preserving oracle baselines.
The 40-song post-transcription run completed on 2026-08-29: Jaccard improved
root 47.2% -> 52.9%, MajMin 38.9% -> 52.9%, sevenths 27.5% -> 40.0%, and MIREX
52.0% -> 55.9%, with 27 rather than 29 normalization warnings. Decision gate:
`A. ADVANCE_TO_REAL_AUDIO`. Repeated runs produced byte-identical JSON and
Markdown artifacts. The subsequent runtime gate makes WAV execution measurable
and usable for controlled validation, but it supplies no real-musician accuracy
evidence, so `rule_jaccard` must not become the default.

## Commands

```powershell
# Generate synthetic fixtures
python eval/synth_dataset.py

# Fast deterministic symbolic classifier isolation
python eval/evaluate_oracle_classifier.py

# Complete candidate rankings and score-term forensics
python eval/analyze_advanced_scorer.py

# Isolated candidate-match formulation comparison
python eval/compare_match_formulations.py

# Opt-in post-transcription production-path comparison
python eval/evaluate_jaccard_detector_path.py

# Cold/warm real-WAV runtime and duration scaling
python eval/benchmark_audio_path.py

# Run 40 songs x 4 detectors and rewrite reports; slow
python eval/evaluate_chords.py

# Existing symbolic/key/infrastructure audit; may be slow
python _evaluation.py
python _evaluation.py --section key

# Evidence-Grounded Tutor deterministic evaluation and demos
python eval/evaluate_tutor_evidence.py

# Requires relay, TTS, and frontend dependencies/services
python _e2e_smoke.py
```

Fresh evidence from 2026-08-17:

- active Python compile command passed;
- Next.js 16.2.6 production build passed after its worker process was permitted to spawn;
- a focused normalizer edge-case assertion passed with four repair warnings;
- the focused key-detector cases scored 6/7, with A minor confused for relative C major on "Shape of You";
- `eval/report.json` parsed and reported 40 sine-rendered songs;
- `_evaluation.py` timed out after 120 seconds without a result;
- the instrumented labeled-MIDI section still times out on the first `Amaj.mid`; prior stack evidence identifies cold lazy librosa/Numba cache initialization inside the detector path;
- `python -m unittest discover -v` passes 16/16;
- the tutor evaluator passes 13/13, with 5/5 evidence fields propagated, 7/7 grounded cases, 4/4 uncertainty cases, and 6/6 retrieval-absence cases;
- three deterministic evidence/retrieval/output demos are recorded in `eval/evidence_grounded_demos.json`;
- full synthetic and live E2E runs were not executed.

Fresh evidence from 2026-08-18:

- `python eval/evaluate_oracle_classifier.py` completed in about one second and produced deterministic JSON and Markdown artifacts across repeated runs;
- the active simple classifier scored 28.1% exact and the existing advanced scorer scored 50.0% exact over 96 complete oracle chords each;
- all dominant-seventh cases failed for both classifiers, while the advanced scorer recognized all complete major, minor, sus2, and sus4 cases;
- `python -m unittest discover -v` passed 28 tests with three known musical defects recorded as expected failures;
- provider-backed `_e2e_smoke.py` passed with 2 detected events, 8 text chunks/785 characters, 8 WAV chunks/2,302,552 bytes, and a completion event;
- a shared verified Windows TLS context fixed Python 3.13 provider connections without disabling certificate or hostname verification;
- production detector behavior and synthetic audio reports were not changed or rerun; automated browser/microphone E2E remains outstanding.
- `python eval/analyze_advanced_scorer.py` completed in about 1.4 seconds and produced identical JSON/Markdown hashes across repeated runs;
- all 85 candidate scores for all 96 baseline cases reconcile exactly with the source scorer;
- dominant-seventh diagnosis is 9 triad ties resolved by insertion order plus 3 triad wins from E-major priors, with 0% seventh accuracy under default, no-key, and matching-supported-key modes;
- five real score-term ablations were run; no individual ablation recovered dominant-seventh accuracy;
- the full suite passes 26 tests with three known musical defects recorded as expected failures.

Fresh evidence from 2026-08-21:

- `python eval/compare_match_formulations.py` exactly reproduced all 96 baseline winners and candidate scores, then selected Jaccard under the documented frozen rule;
- supported complete exact rose from 57.1% for baseline coverage to 98.8% for Jaccard, and complete seventh exact rose from 0.0% to 97.2%;
- Jaccard robustness exact was 91.7% for omitted fifths, 9.5% for omitted roots, 86.1% for sevenths without fifths, 98.8% for duplicated tones, 78.9% for inversions, and 91.7% for fixed extra-tone cases;
- repeat runs produced identical SHA-256 hashes for both reports;
- `python -m unittest discover -v` passed 32 tests with three expected failures, and `python -m compileall -q eval tests` passed;
- no production detector, runtime configuration, or audio-level benchmark was changed or rerun.

## Change-to-Evidence Matrix

| Change | Required focused check | Required broader check |
|---|---|---|
| event normalization | edge cases: invalid label/time, negative start, overlap, adjacency, confidence preservation | all detector reports |
| detector internals | known fixed WAV/MIDI cases | synthetic report plus licensed real-audio subset |
| key analysis | fixed relative major/minor and transposition cases | real chord sequences with key labels |
| retrieval query/schema | labeled query-result relevance cases | recall/coverage/grounding report |
| prompt/evidence assembly | prompt snapshots and adversarial low-evidence cases | fixed tutor rubric comparison |
| streaming/TTS | message order, cancellation, unavailable TTS | browser E2E and latency distribution |
| upload preprocessing | malformed/short/silent/codec/size fixtures | browser/multi-platform matrix |

## Research Evidence Needed

1. Licensed real-audio benchmark with instrument, room/noise, and performer diversity.
2. Established external chord-recognition baselines and detector ablations.
3. Separate transcription and harmony measurements so upstream failures are visible.
4. Retrieval relevance/coverage/provenance labels and failure analysis.
5. Tutor correctness, grounding, contradiction, and uncertainty rubrics.
6. Expert or musician assessment for pedagogy claims.
7. Latency, throughput, failure rate, and model/embedding/TTS cost.
8. A preregistered or clearly frozen protocol before final paper results.
