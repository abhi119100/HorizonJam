# Security and Privacy Context

## Trust Boundary

```text
untrusted browser audio/question/path
  -> public HTTP/WebSocket boundary
  -> temporary filesystem and decoder
  -> CPU/model/embedding/TTS resources
  -> persistent RAG store
  -> streamed text/audio
```

Every arrow crosses a resource, privacy, or injection boundary. The current implementation is local-development only.

## Verified boundary repairs (readiness pass)

The active relay no longer mounts the repository or uploads as static files. `/static/STATUS.md`, `/static/.env`, and `/static/.env.production` return 404 in targeted handler tests.

The WebSocket rejects client paths and issues a random session capability only for an allowed local browser origin. HTTP upload/deletion requires that capability; analysis resolves only an upload ID owned by the same live connection. Capabilities are kept in memory, never localStorage or URLs. Unknown/expired/foreign IDs and cross-session requests have denial tests. This is session ownership, not account authentication.

Uploads use random private directories, pre-parser bounded disk spooling (16 MiB plus 64 KiB multipart allowance), chunked copying and decoded-content checks even for WAV. Audio must be 0.5-30 seconds, mono/stereo, 8-96 kHz, finite and non-silent; it is normalized to mono PCM16 at 44.1 kHz. Non-SoundFile formats require a recognized binary container and bounded local ffmpeg decoding. Playlists are rejected. A full decoder process sandbox/memory limit is still absent.

Success, invalid input, ready deletion, disconnect and expiry clean temporary recordings. Cancellation marks work cancelled and suppresses later stages/delivery while retaining input until current readers finish. Ready files expire after five minutes; sessions after 20 idle minutes. Crash recovery and hard interruption of native/provider workers remain open. The default relay command binds to loopback.

## Remaining release blockers

- No account authentication, per-user authorization, global request/abuse limits or provider spending budget. Session limits (16 connections, one pending upload, three analyses, two workers) are local safeguards and can be reset by reconnecting.
- TTS is still a separate directly callable service with wildcard CORS. It needs a private authenticated/quota-controlled boundary before hosting.
- Cancellation/deadlines are cooperative: a 120-second delivery timeout cannot forcibly stop a native thread/provider call. Jobs are not durable, and process-crash cleanup is not verified.
- Bounded language checks and untrusted-reference prompt instructions do not prove prompt-injection resistance, semantic correctness or source entailment.
- Non-web runtime paths can mutate shared retrieval without consent/tenancy; corpus provenance and immutable serving are unresolved.
- Detector/provider traces elsewhere can still contain paths/text; the active relay avoids logging capability tokens and raw provider failures, but repository-wide logging minimization is incomplete.
- `.env.production` is now ignored and untracked; no full secret/history audit has been performed.
- A Windows/Python 3.13 contract-test version lock and CI workflow exist. Full detector install, wheel hashes, dependency vulnerability audit, SBOM and incident procedures remain open.

## User Audio and Privacy Requirements

- Obtain explicit microphone and processing consent.
- State whether audio, questions, chord evidence, embeddings, and tutor outputs leave the device.
- Default to minimal retention and deterministic expiry.
- Do not train or enrich shared stores from user sessions without separate opt-in consent.
- Encrypt transport and protected storage; isolate tenants and sessions.
- Provide deletion for recordings, sessions, embeddings, and accounts.
- Define subprocessors, retention, regional handling, and model-provider settings in public policy.
- Treat voices, background speech, original performances, and filenames as potentially identifying.

## Phase 7 Local Feedback

The Evidence UX feedback affordance does not call a backend. It keeps at most
50 compact records in browser `localStorage`, keyed by a random per-analysis
session identifier. Records contain predicted chord labels, categorical
evidence summaries, detector, feedback choice, and timestamp. They exclude
audio bytes, filenames, filesystem paths, questions, tutor text, raw notes,
chroma, and model data. This is development feedback only and is never imported
into the real-performance pack automatically. A production feedback service
still requires consent, retention/deletion policy, authentication, and tenant
isolation.

## Security Review Procedure

Use `.agents/skills/security-review/SKILL.md`. Record exploitability and evidence, not only code smells. Do not mark a boundary fixed until a targeted denial/cleanup test passes.

## Release Gate

Static exposure and path trust have targeted passing checks. No hosted alpha until account authentication, quotas, global spend controls, isolation, retention/deletion, monitoring, and privacy disclosures are tested. App Store packaging does not reduce backend risk.
