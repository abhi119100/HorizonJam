---
name: security-review
description: Audit HorizonJam trust boundaries for uploads, paths, temporary files, static serving, WebSockets, CORS, authentication, secrets, external model APIs, RAG mutation, user audio, retention, and deletion. Use before deployment/release or whenever backend, storage, ingestion, logging, configuration, or privacy behavior changes.
---

# Review Security Boundaries

1. Read `docs/context/SECURITY.md`, `docs/context/ARCHITECTURE.md#http-and-websocket-contract`, and current `STATUS.md`.
2. Draw the exact untrusted-input path to filesystem, decoder, CPU work, persistent data, model APIs, logs, and output.
3. Inspect static roots, path resolution, session ownership, content validation, body/duration limits, random names, cleanup, and parser/subprocess boundaries.
4. Inspect HTTP/WebSocket authentication, origins, authorization, rate limits, quotas, concurrency, cancellation, and spending limits.
5. Inspect secret loading, ignore rules, logs/errors, client bundles, production config, dependency locks, and generated artifacts. Never print secret values.
6. Inspect whether user data enters shared RAG/training stores and whether consent, isolation, retention, and deletion exist.
7. Inspect retrieved text for prompt injection and provenance/trust labeling.
8. Rank findings by exploitability, impact, exposure, and evidence. Separate verified vulnerability, risky design, and missing control.
9. For fixes, write targeted denial/cleanup tests and verify the negative case.

Public gates include dedicated static assets, opaque session-bound upload IDs, bounded uploads, auth/quota/cost controls, private TTS, retention/deletion, monitoring, and privacy disclosure.
