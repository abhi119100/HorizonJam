# HorizonJam Chord Detection - Synthetic Eval Report

Dataset: **40 synthetic progressions**, renderer: {'pretty_midi-sine': 40}
Default detector (HORIZONJAM_DETECTOR): **hybrid** (env not set, using default)

All detectors run via `detection.run_detection()` so events are sorted, non-overlapping, and adjacent identicals are merged before scoring. This is the same path the web app uses.

## Summary

| Detector | Root | MajMin | Sevenths | MIREX | WCSR | Files OK | Files Failed | Total Warnings |
|---|---|---|---|---|---|---|---|---|
| production | 0.319 | 0.270 | 0.211 | 0.356 | 0.270 | 40 | 0 | 32 |
| hybrid | 0.585 | 0.517 | 0.356 | 0.588 | 0.517 | 40 | 0 | 38 |
| rule_viterbi | 0.585 | 0.517 | 0.356 | 0.588 | 0.517 | 40 | 0 | 38 |

**Reading the metrics:**
- `Root` - root note correct, ignoring quality.
- `MajMin` - root + major/minor quality match. The practical floor.
- `Sevenths` - same as MajMin plus 7th-chord extensions.
- `MIREX` - official MIREX comparison metric.
- `WCSR` - Weighted Chord Symbol Recall (= MajMin under equal-duration songs).
- `Total Warnings` - normalization repairs the detection layer made (overlaps clamped, etc.).

Today `hybrid` and `rule_viterbi` are functionally identical (`HybridChordDetector.ml_available = False`, no trained model). Both rows are kept so this harness can re-run unchanged once an ML model is trained.

## Failure patterns (top confusion pairs, duration-weighted)

### `production`
- `G#:maj->C:maj` (7.9s)
- `A:7->E:min7` (6.8s)
- `G:7->G:maj` (6.2s)
- `C:7->E:min7` (6.0s)
- `C#:min->N` (6.0s)

### `hybrid`
- `G:7->G:maj` (13.1s)
- `C:7->C:maj` (11.4s)
- `A:7->A:maj` (10.9s)
- `E:7->E:maj` (8.5s)
- `G#:maj->C:maj` (7.1s)

### `rule_viterbi`
- `G:7->G:maj` (13.1s)
- `C:7->C:maj` (11.4s)
- `A:7->A:maj` (10.9s)
- `E:7->E:maj` (8.5s)
- `G#:maj->C:maj` (7.1s)

## Detector errors

### `production`: no errors

### `hybrid`: no errors

### `rule_viterbi`: no errors

## Per-song scores (first 15)

| Song | Detector | Root | MajMin | Sevenths | Events | Warnings |
|---|---|---|---|---|---|---|
| I-IV-V-I_C_major | production | 0.88 | 0.88 | 0.88 | 6 | 1 |
| I-IV-V-I_C_major | hybrid | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_C_major | rule_viterbi | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_C#_major | production | 0.25 | 0.25 | 0.25 | 4 | 1 |
| I-IV-V-I_C#_major | hybrid | 0.25 | 0.25 | 0.25 | 4 | 1 |
| I-IV-V-I_C#_major | rule_viterbi | 0.25 | 0.25 | 0.25 | 4 | 1 |
| I-IV-V-I_D_major | production | 0.00 | 0.00 | 0.00 | 2 | 1 |
| I-IV-V-I_D_major | hybrid | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_D_major | rule_viterbi | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_D#_major | production | 0.00 | 0.00 | 0.00 | 2 | 1 |
| I-IV-V-I_D#_major | hybrid | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_D#_major | rule_viterbi | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_E_major | production | 0.87 | 0.86 | 0.86 | 7 | 1 |
| I-IV-V-I_E_major | hybrid | 0.55 | 0.40 | 0.40 | 5 | 0 |
| I-IV-V-I_E_major | rule_viterbi | 0.55 | 0.40 | 0.40 | 5 | 0 |
| I-IV-V-I_F_major | production | 0.56 | 0.56 | 0.56 | 8 | 1 |
| I-IV-V-I_F_major | hybrid | 0.54 | 0.54 | 0.54 | 6 | 1 |
| I-IV-V-I_F_major | rule_viterbi | 0.54 | 0.54 | 0.54 | 6 | 1 |
| I-IV-V-I_F#_major | production | 0.25 | 0.00 | 0.00 | 2 | 1 |
| I-IV-V-I_F#_major | hybrid | 0.59 | 0.54 | 0.54 | 6 | 1 |
| I-IV-V-I_F#_major | rule_viterbi | 0.59 | 0.54 | 0.54 | 6 | 1 |
| I-IV-V-I_G_major | production | 0.78 | 0.78 | 0.78 | 7 | 1 |
| I-IV-V-I_G_major | hybrid | 0.53 | 0.53 | 0.53 | 6 | 1 |
| I-IV-V-I_G_major | rule_viterbi | 0.53 | 0.53 | 0.53 | 6 | 1 |
| I-IV-V-I_G#_major | production | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_G#_major | hybrid | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_G#_major | rule_viterbi | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_A_major | production | 0.85 | 0.85 | 0.85 | 8 | 1 |
| I-IV-V-I_A_major | hybrid | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_A_major | rule_viterbi | 0.69 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_A#_major | production | 0.00 | 0.00 | 0.00 | 2 | 1 |
| I-IV-V-I_A#_major | hybrid | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_A#_major | rule_viterbi | 0.00 | 0.00 | 0.00 | 4 | 1 |
| I-IV-V-I_B_major | production | 0.00 | 0.00 | 0.00 | 2 | 1 |
| I-IV-V-I_B_major | hybrid | 0.79 | 0.69 | 0.69 | 6 | 1 |
| I-IV-V-I_B_major | rule_viterbi | 0.79 | 0.69 | 0.69 | 6 | 1 |
| i-iv-V-i_C_minor | production | 0.72 | 0.22 | 0.22 | 7 | 1 |
| i-iv-V-i_C_minor | hybrid | 0.74 | 0.15 | 0.15 | 6 | 1 |
| i-iv-V-i_C_minor | rule_viterbi | 0.74 | 0.15 | 0.15 | 6 | 1 |
| i-iv-V-i_C#_minor | production | 0.25 | 0.25 | 0.25 | 2 | 1 |
| i-iv-V-i_C#_minor | hybrid | 0.69 | 0.69 | 0.55 | 4 | 1 |
| i-iv-V-i_C#_minor | rule_viterbi | 0.69 | 0.69 | 0.55 | 4 | 1 |
| i-iv-V-i_D_minor | production | 0.25 | 0.00 | 0.00 | 1 | 0 |
| i-iv-V-i_D_minor | hybrid | 0.74 | 0.54 | 0.54 | 6 | 1 |
| i-iv-V-i_D_minor | rule_viterbi | 0.74 | 0.54 | 0.54 | 6 | 1 |