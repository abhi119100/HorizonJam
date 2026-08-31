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

## Verified Critical Release Blockers

### Repository-root static serving

`tutor_ws_relay.py` mounts `StaticFiles(directory=".")` at `/static`. The root contains `.env` and project/data files. Replace this with a dedicated, allowlisted public-assets directory before any network exposure, then test that dotfiles/configuration cannot be fetched.

### Client-controlled server path

The upload response returns a server filesystem path. The browser sends it back, and `websocket_tutor_endpoint()` accepts any existing path. Replace this with an opaque, unguessable, session-bound job/upload ID resolved only inside an isolated upload directory. Verify cross-session and traversal denial.

### Upload resource handling

`upload_audio()` reads the complete body into memory, derives a predictable filename, has no enforced byte/duration/decode limits, and does not reliably delete successful WAVs or all error-path originals. Add streaming limits, random storage names, decoded content validation, duration/channel/rate bounds, quotas, expiration, and finally-block cleanup.

## Other Verified Blockers

- No authentication, authorization, session binding, rate limiting, abuse controls, or spending quotas.
- WebSocket origin/auth is not validated; CORS is not a WebSocket authorization control.
- TTS allows all CORS origins and should normally be private behind the application boundary.
- User text and retrieved records flow into model prompts without prompt-injection boundaries or source trust labels.
- The persistent RAG store can be mutated by some runtime paths without tenancy, consent, provenance, or retention rules.
- Logs include filenames and local paths; production logging needs minimization and redaction.
- `.env.production` is not ignored by current patterns and lists credential/security settings. Its values were not copied into project context.
- No dependency lock, vulnerability scan, secret scan, SBOM, incident procedure, or supported-version policy exists.

## User Audio and Privacy Requirements

- Obtain explicit microphone and processing consent.
- State whether audio, questions, chord evidence, embeddings, and tutor outputs leave the device.
- Default to minimal retention and deterministic expiry.
- Do not train or enrich shared stores from user sessions without separate opt-in consent.
- Encrypt transport and protected storage; isolate tenants and sessions.
- Provide deletion for recordings, sessions, embeddings, and accounts.
- Define subprocessors, retention, regional handling, and model-provider settings in public policy.
- Treat voices, background speech, original performances, and filenames as potentially identifying.

## Security Review Procedure

Use `.agents/skills/security-review/SKILL.md`. Record exploitability and evidence, not only code smells. Do not mark a boundary fixed until a targeted denial/cleanup test passes.

## Release Gate

No public alpha until static exposure and path trust are fixed. No public beta until authentication, quotas, isolation, retention/deletion, monitoring, and privacy disclosures are tested. App Store packaging does not reduce backend risk.

