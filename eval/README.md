# Chord-Detection Evaluation Harness

A reproducible, read-only benchmark for HorizonJam's chord-detection stack
on a synthetic dataset. No new ML model is trained here.

## Oracle symbolic classifier benchmark

Run the cheap, deterministic classifier-only benchmark with:

```bash
python eval/evaluate_oracle_classifier.py
```

It uses exact MIDI pitches and exact chord boundaries, with no audio rendering,
BasicPitch, segmentation, retrieval, tutor logic, network, model provider, or
GPU. It compares the active `identify_chord_from_pitches()` function with the
existing offline `identify_chord_from_pitches_advanced()` scorer and writes:

- `eval/oracle_classifier_report.json`
- `eval/oracle_classifier_report.md`

The benchmark extracts the exact classifier function bodies from
`src/chord_detector.py` to avoid importing that module's audio dependencies.
Production detection behavior is not changed.

Inspect the existing advanced scorer's complete candidate rankings and exact
score components with:

```bash
python eval/analyze_advanced_scorer.py
```

This observational follow-up writes `eval/advanced_scorer_forensics.json` and
`eval/advanced_scorer_forensics.md`. It includes key, bass, and existing-term
ablations but does not alter or activate the advanced scorer.

Compare isolated candidate-match formulations with all other scorer terms
frozen using:

```bash
python eval/compare_match_formulations.py
```

This writes `eval/match_formulation_report.json` and
`eval/match_formulation_report.md`. It covers complete chords, partial voicings,
inversions, duplicated tones, and a small extra-tone contamination set without
changing production detection.

## What it does

```
1. Generate ~40 short MIDI progressions of known chord sequences in many keys
   → eval/data/synth/midi/*.mid
   → eval/data/synth/labels/*.lab    (mir_eval Harte format ground truth)
   → eval/data/synth/wav/*.wav       (rendered audio)

2. Run each WAV through three detector configurations
     - production    AccurateAudioToChordsPipeline (what the live frontend hits)
     - hybrid        HybridChordDetector(use_viterbi=True)
     - rule_viterbi  identical to hybrid until an ML model is trained
                     (HybridChordDetector.ml_available is False today)

3. Score with mir_eval.chord.evaluate() → Root / MajMin / Sevenths / MIREX

4. Write eval/report.md and eval/report.json
```

## Run it

```bash
cd HorizonJam

# Step 1: Generate dataset (one-time, fast)
python eval/synth_dataset.py

# Step 2: Run the eval (slow — ~30s × 40 songs × 3 detectors)
python eval/evaluate_chords.py
```

## WAV rendering

The dataset script tries two backends in order:

| Backend | Quality | Requirements |
|---|---|---|
| **midi2audio + FluidSynth** | Realistic instrument timbre | `pip install midi2audio` + FluidSynth installed |
| **pretty_midi.synthesize()** | Sine-wave additive (clean pitch, unrealistic timbre) | None (ships with pretty_midi) |

If neither works, MIDIs + labels still get written; only WAV rendering is
skipped, and the eval will report "no wav" for each song.

To install FluidSynth on Windows:
```powershell
choco install fluidsynth   # via chocolatey, or download from https://www.fluidsynth.org
pip install midi2audio
```

## Interpreting results

- **MajMin < 50%** on this *synthetic clean* dataset = logic bug somewhere in
  the detector. The audio is pitch-perfect; if MajMin is bad here, it'll be
  catastrophic on real audio.
- **MajMin 50–75%** = rule-based ceiling. Expected for the current detector.
- **MajMin > 80%** = ready to test against real benchmarks (GuitarSet, Isophonics).

Note: `pretty_midi.synthesize()` produces pure sine-wave tones with no
harmonics. `basic_pitch` was trained on real instruments, so it may give
lower-than-realistic note transcription on this dataset. Once FluidSynth +
SoundFont is wired up, expect the production pipeline's score to *improve*
on real-instrument WAVs.

## Files

- `synth_dataset.py` — generate MIDIs/labels/WAVs
- `run_detector.py` — uniform `--detector` CLI wrapper, isolates one detector run
- `evaluate_chords.py` — orchestrator: spawns `run_detector.py` per (song, detector), scores, writes reports
- `report.md` / `report.json` — outputs (regenerated each run)
