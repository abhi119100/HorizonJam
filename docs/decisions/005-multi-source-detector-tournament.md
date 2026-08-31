# ADR 005: Benchmark Multi-Source Harmonic Evidence Before Activation

## Status

Accepted for research; no production detector change authorized.

## Decision

Freeze HorizonJam v3, then evaluate note transcription, direct chord models,
DSP/chroma, and segmentation as independent research adapters under one
normalized tournament contract. Attempt fusion only after individual baselines
and complementary error patterns are measured. Promote a detector or fused
architecture only through the sanctioned `detection.run_detection()` boundary
after licensing, accuracy, runtime, uncertainty, and product gates pass.

## Rationale

The v3 pipeline depends on one BasicPitch transcription path and discards rich
in-memory evidence through MIDI. Existing experiments isolate symbolic scoring
but do not establish real-musician accuracy. A tournament separates L1, L2,
segmentation, confidence, and L6 runtime while retaining reproducible product
contracts and uncertainty.

## Consequences

- External packages and models remain isolated research dependencies.
- BasicPitch remains active in v3 and becomes one evidence source in research.
- ShazamKit belongs to known-recording alignment, not open chord detection.
- No external confidence is treated as calibrated without evidence.
- The tutor and retrieval systems do not participate in the baseline tournament.
