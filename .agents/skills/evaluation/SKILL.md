---
name: evaluation
description: Select, run, compare, and interpret HorizonJam evaluation evidence from audio validation through product outcomes. Use for benchmark runs, regression checks, evaluation design, report updates, performance claims, synthetic dataset regeneration, or deciding what evidence a change requires.
---

# Evaluate HorizonJam

1. Read `docs/context/EVALUATION.md` and `STATUS.md`.
2. Select the affected level: L0 audio, L1 transcription, L2 harmony, L3 retrieval, L4 reasoning, L5 pedagogy, L6 product, or L7 outcome.
3. Preserve current output before a benchmark rewrite and record code/configuration, environment, fixture version, and command.
4. Run the smallest focused test first. Diagnose failures before broad benchmarking.
5. Run the required broader evaluation from the change-to-evidence matrix.
6. Compare metrics, failure patterns, warnings, latency, cost, and completion rate; averages alone are insufficient.
7. Label evidence as fresh run, checked-in report, inference, or plan.
8. Update reports only after a complete run and `STATUS.md` only when benchmark truth or blockers changed.

Core commands: `python -m compileall -q detection.py chordai_gpt_tutor.py tutor_ws_relay.py tts_server.py unified_rag_system.py src eval`, `python eval/synth_dataset.py`, `python eval/evaluate_chords.py`, `python _evaluation.py`, and `python _e2e_smoke.py`.

The full matrix is slow and E2E requires services. A timeout is incomplete verification, not a pass. Never generalize sine results to real musicians.
