# Real Performance Evaluation Pack v1

Decision: **F DATASET_TOO_SMALL_OR_AMBIGUOUS**.

## Dataset status

Approved cases: **0**. Minimum required: **20**.
Provenance: `NO_APPROVED_AUDIO`. Annotations: `NO_ANNOTATIONS`. Held-out split: `NOT_FROZEN`.

Repository WAV fixtures are excluded because their legal and performance provenance is unaudited. Synthetic audio is not real-performance evidence.

## Evaluation status

Hybrid, rule_jaccard, BasicPitch direct evidence, and DSP/chroma were not run. Metrics, slices, source disagreement, L1/L2 attribution, and real-audio latency are unavailable rather than zero.

## Readiness blockers

- requires at least 20 approved cases; found 0
- requires both chord-isolation and progression cases
- requires development and held-out cases
- missing qualities: dominant_seventh, major, major_seventh, minor, minor_seventh, sus2, sus4
- missing playing_styles: block_chords, faster_arpeggios, inversions, partial_voicings, repeated_transitions, slow_arpeggios, strumming
- missing conditions: different_dynamics, moderate_background_noise, multiple_devices, quiet_room, slight_tuning_difference
- missing harmonic_examples: I-IV-V-I, i-iv-V-i, ii-V-I, relative_major_minor_ambiguous, secondary_dominant, vi-IV-I-V

The collection contract is `eval/real_performance_demo_pack/manifest.schema.json`. Run detectors only after provenance approval, split assignment, annotation, and held-out-label freeze.
