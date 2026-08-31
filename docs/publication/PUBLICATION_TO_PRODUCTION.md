# Publication-to-Production Roadmap

## Decision

Frozen v3 is the evidence baseline. Publication and production hardening start
from that baseline, but research adapters remain isolated until their gates
pass. The first public artifact is the architecture and reproducibility story;
the current local services are not deployed as-is.

## Parallel Workstreams

```text
v3 baseline
  +-> publication: claim freeze -> article -> preprint/paper -> artifact DOI
  +-> research: real audio -> external baselines -> fusion -> tutor study
  +-> production: security -> contracts -> jobs/storage -> private web alpha
                                                    -> public beta -> mobile
```

Research results can improve later product versions, but production security
does not wait for detector research and experimental packages do not enter the
production environment by default.

## Gate 0: Publication and Open-Source Legality

### Required work

- Choose a paper type and target venue; check anonymity, preprint, and artifact
  rules before publishing the final article.
- Freeze the claim ledger, experiment protocol, and v3 artifact hashes.
- Select an explicit repository license with legal review appropriate to the
  intended commercial/open-source model.
- Audit every distributed dependency, model weight, audio fixture, dataset,
  scraped record, vector store, font, and image.
- Remove tracked virtual environments, build output, vector databases, and
  generated artifacts from the release tree/history as appropriate.
- Add `CITATION.cff`, `LICENSE`, third-party notices, `CONTRIBUTING.md`,
  `SECURITY.md`, a code of conduct, and reproducible setup/lockfiles.
- Add CI for tests, dependency review, secret scanning, and release manifests.
- Archive a signed source release and reproducibility bundle with a DOI.

### Exit criteria

- A clean-room installation succeeds from declared dependencies.
- The source release contains no secret, private user data, or unlicensed
  artifact.
- Every paper table is generated or traceable to checked-in code and data.
- The repository is legally open source, not merely publicly visible.

## Gate 1: Blocking Security Boundaries

### Required work

- Replace repository-root static serving with an allowlisted public directory.
- Replace client-supplied server paths with opaque, random, session-bound upload
  and job IDs.
- Stream uploads with byte limits; validate decoded type, duration, channels,
  sample rate, and silence; isolate storage and delete on all paths.
- Add authentication, authorization, WebSocket origin checks, rate limits,
  concurrency limits, quotas, and provider-spend controls.
- Keep TTS private behind the application boundary and restrict CORS.
- Separate immutable production retrieval from audited ingestion.
- Minimize/redact logs and define audio, question, embedding, output, and account
  retention/deletion.
- Add denial, traversal, cross-session, oversized-input, cancellation, cleanup,
  and quota tests.

### Exit criteria

- All critical findings in `docs/context/SECURITY.md` have targeted passing
  tests.
- No public request can select an arbitrary filesystem path or fetch repository
  files.
- A user can delete all account/session artifacts covered by policy.

## Gate 2: Versioned Product Contracts

Define and test stable schemas for:

- `POST /v1/uploads` -> opaque upload ID;
- `POST /v1/analyses` -> job ID and accepted configuration;
- `GET /v1/analyses/{id}` -> state and structured result;
- authenticated `/v1/analyses/{id}/stream` events;
- `PerformanceEvidence` and chord-event versions;
- errors, cancellation, expiration, and idempotency; and
- optional TTS references or private audio streaming.

Use compatibility adapters at the boundary rather than preserving duplicate
fields throughout the core.

## Gate 3: Production Runtime

Target architecture:

```text
web/iOS client
  -> HTTPS API + authentication
  -> bounded upload -> private object storage
  -> durable analysis job
  -> bounded worker pool
       -> audio validation
       -> detection.run_detection()
       -> evidence assembly
       -> read-only retrieval
       -> model generation + verification
  -> authenticated result/event stream
  -> retention worker and deletion audit
```

Required controls include deployment locks, health/readiness checks,
structured redacted logs, traces and metrics, retry/idempotency policy,
cancellation, timeouts, circuit breakers, backups, incident response, and
model/embedding/TTS cost accounting.

### Exit criteria

- Staging passes malformed-audio, concurrency, cancellation, provider-failure,
  and cleanup suites.
- Measured p50/p95 latency, failure rate, memory, and per-analysis cost meet a
  written service target.
- Written tutoring remains available when TTS fails.

## Gate 4: Private Web Alpha

The alpha should implement one complete job: record or upload a short solo
performance, inspect timed evidence, ask one question, receive verified written
guidance, optionally hear speech, report a wrong detection, and delete the
session.

Do not add a song catalog, social layer, subscriptions, or continuous listening
before this flow is reliable. Recruit a small, consented cohort; instrument
completion, latency, corrections, uncertainty interactions, cost, and deletion.

### Exit criteria

- Browser E2E passes on supported desktop/mobile browsers.
- No critical/high security finding remains.
- Users can understand what was detected and correct/report mistakes.
- Privacy notice and support/incident routes are operational.

## Gate 5: Public Web Beta

Add abuse monitoring, account recovery, support tooling, capacity limits,
status communication, accessibility testing, data export/deletion, and a
documented supported-browser/device matrix. Run a measured beta before mobile
store submission; a native client should consume stable APIs rather than
becoming a second backend experiment.

## Gate 6: iOS and App Store

Recommended first client: a focused SwiftUI application using the stable job
API, native audio session/recording controls, secure credential storage,
background/interruption handling, and accessible evidence/tutor views. Reuse
the backend contracts, not the current browser implementation as an insecure
wrapper.

Before submission:

- enroll in the Apple Developer Program and configure signing/provisioning;
- define microphone permission text and collect only required data;
- complete App Privacy details and a public privacy policy;
- include required privacy manifests and SDK declarations;
- provide in-app account deletion when account creation is supported;
- use StoreKit/In-App Purchase for qualifying digital subscriptions/features;
- provide reviewer credentials and a functioning review environment;
- test offline, interrupted, denied-permission, background, slow-network, and
  provider-failure states;
- complete VoiceOver, Dynamic Type, contrast, target-size, and caption/text
  alternatives; and
- run TestFlight cohorts before production review.

Current platform references:

- [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [App privacy details](https://developer.apple.com/app-store/app-privacy-details/)
- [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)
- [TestFlight](https://developer.apple.com/testflight/)
- [StoreKit](https://developer.apple.com/storekit/)

An Android client follows the same API and privacy gates, with a separate Play
policy, data-safety, billing, device, and testing review.

## Research Gates Before Strong Product Claims

| Product wording | Minimum evidence |
|---|---|
| "analyzes your chords" | licensed real-audio L2 results and displayed limitations |
| "confidence-aware" | calibration/reliability evidence, not raw model probability |
| "grounded in sources" | L3 provenance plus relevance/coverage evaluation |
| "gives accurate explanations" | blinded expert L4 review |
| "helps you practice" | L5 educator/musician actionability study |
| "helps you improve" | L7 longitudinal outcome evidence |

## Immediate Execution Order

1. Review and finalize the abstract, article, paper scope, and authorship.
2. Choose the repository license and remove non-distributable artifacts.
3. Add CI, locks, secret scanning, notices, citation, security, and contribution
   files.
4. Build the owned/licensed real-performance evaluation pack and freeze its
   annotation protocol.
5. Complete detector tournament Gate 1 and the minimal first wave.
6. Fix static serving, path trust, upload isolation/limits, and cleanup with
   tests.
7. Define v1 authenticated job and evidence APIs.
8. Deploy an instrumented private staging environment.
9. Run a consented private web alpha and expert tutor evaluation.
10. Begin the native client only after the API, privacy model, and alpha flow
    are stable.

## Current Readiness Judgment

- **Architecture publication:** close; the main draft and evidence are present,
  but figures, authorship, venue, and reproducibility/legal packaging remain.
- **Systems paper:** credible as a work-in-progress or preprint; a stronger
  empirical submission needs real audio, baselines, ablations, and expert
  evaluation.
- **Open-source launch:** blocked by the missing explicit license and incomplete
  artifact/corpus/dependency provenance.
- **Private web alpha:** reachable after the critical trust-boundary work.
- **Public web/App Store:** not close enough to submit safely; backend security,
  privacy, reliability, and measured alpha evidence come first.
