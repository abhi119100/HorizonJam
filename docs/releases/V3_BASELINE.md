# HorizonJam v3 Research Baseline

## Scope

This baseline freezes the accumulated HorizonJam architecture before the
multi-source harmonic-detection tournament. It preserves:

- the browser, upload, WebSocket, tutor, retrieval, and optional TTS path;
- `detection.run_detection()` as the sanctioned detector boundary;
- normalized chord events and evidence-grounded tutor contracts;
- the default hybrid detector and opt-in `rule_jaccard` experiment;
- oracle, scorer, match-formulation, and post-transcription reports;
- Single-WAV Analysis Performance Gate v1 and its cold/warm reports;
- tests, context documents, decisions, repository skills, and prior archives.

This baseline does not claim real-musician detector accuracy, calibrated
confidence, production deployment readiness, or App Store readiness.

## Archive Classes

The generated v3 source archive is a sanitized engineering snapshot. It
includes authored source, documentation, tests, reproducible evaluation code,
reports, and controlled fixtures. It excludes:

- `.env` and environment-specific secret files;
- `node_modules`, `.next`, Python bytecode, and other caches;
- generated user/TTS audio and pipeline output;
- Chroma/vector-store state with unaudited provenance;
- model binaries and other artifacts whose distribution rights are not yet
  established.

Excluded local state remains subject to the repository's privacy, provenance,
and release audit. It must not be copied into a public artifact merely to make
the snapshot exhaustive.

## Baseline Verification

The archive manifest records every included path, byte count, and SHA-256. The
archive itself receives a SHA-256 sidecar. Current verified commands and
measurements remain in `STATUS.md` and `eval/`.

Create and verify the snapshot with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/create_v3_archive.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/verify_v3_archive.ps1
```

The research tournament must remain outside production until its sequential
decision gates authorize activation.
