---
name: detector-change
description: Change HorizonJam chord detection, event normalization, key enrichment, or detector adapters with contract and benchmark evidence. Use for edits to detection.py, active src detector modules, detector selection/configuration, chord events, confidence, key estimation, or guitar analysis derived from detection.
---

# Change Detection Safely

1. Read `docs/context/ARCHITECTURE.md#detection-graph`, `docs/context/EVALUATION.md`, and current `STATUS.md`.
2. Trace `detection.run_detection()` through the selected runner, normalizer, tutor adapter, and evaluator. Do not bypass this boundary.
3. Define the expected behavioral change and affected contract fields before editing.
4. Preserve sorted, positive-duration, non-overlapping events and visible repair warnings.
5. Preserve detector source and genuine confidence values; do not manufacture certainty.
6. Add a focused regression test. For normalization, cover invalid labels/times, negative starts, overlap, adjacency, and confidence preservation as relevant.
7. Run active Python compilation, the focused test, and the smallest relevant fixed audio/MIDI cases.
8. For behavior changes, run `python eval/evaluate_chords.py` and compare metrics, warning count, failure patterns, and runtime against the prior report.
9. Verify `ChordAIRAGTutor._run_horizon_jam()` and WebSocket payload compatibility when fields change.

Record commands, outputs, detector/configuration, fixtures, and before/after metrics. Treat synthetic results as synthetic only. Update `STATUS.md` when verified benchmark truth, invariants, or failures change.
