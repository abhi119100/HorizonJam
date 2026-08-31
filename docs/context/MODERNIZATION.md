# Modernization Sequence

This is a dependency-ordered proposal, not authorization for broad refactoring.

## Documentation / Code Discrepancies

| Claim/configuration | Actual code | Consequence |
|---|---|---|
| `.env.example` says `TTS_SERVER_URL` overrides relay configuration | relay hardcodes `http://localhost:5000/tts` | deployment configuration is misleading |
| historical confidence/min-duration settings imply active control | `_run_horizon_jam()` accepts but does not wire them; detector modes own thresholds | UI/CLI tuning expectations are false |
| tutor described as RAG-grounded | main prompt receives retrieval metadata, not retrieved document text | grounding/provenance is weaker than the name suggests |
| runtime analysis described as learning by embedding each result | active relay bypasses `analyze_audio()` embedding step | browser path does not perform that mutation |
| hybrid described as ML + rules | no model artifact exists | hybrid equals rule/Viterbi in current report |
| README install path implies complete dependencies | requirements omit multiple imported runtime packages | clean setup is not reproducible |
| `.env.production` suggests production controls such as Redis/workers/upload size | active relay does not read those controls | config creates a false production-readiness signal |
| tests directory suggests a test suite | it mostly contains media fixtures | core contracts lack automated verification |

The README's legacy section is intentionally historical and should not be used as active architecture evidence.

## Risk Graph

```text
missing contract tests
  -> fear of removing compatibility fields/entrypoints
  -> duplicated active and old paths
  -> documentation ambiguity
  -> agent/user changes hit the wrong component

lost uncertainty
  -> hard labels and key string
  -> prompt lacks confidence/warnings
  -> confident tutor prose
  -> unmeasured correctness/product trust risk

mutable unaudited corpus
  -> ambiguous ingestion and provenance
  -> metadata-only retrieval packet
  -> no grounding evaluation
  -> weak paper and release claims
```

## Prioritized Sequence

### 1. Repository harness

Maintain the context router, status evidence, skills, and decisions. Establish Git, a license, dependency locks, CI, and secret/data provenance checks. Prerequisite for trustworthy collaboration and release history.

### 2. Blocking security boundaries

Remove root static serving; replace paths with session-bound IDs; isolate, bound, and delete uploads; make TTS private. Add targeted tests. Prerequisite for any shared deployment or live E2E environment.

### 3. Contract stabilization

Add tests around normalized events and WebSocket messages. Define versioned upload/job, analysis, performance-evidence, and stream schemas. Preserve compatibility adapters only at explicit boundaries.

### 4. Evaluation foundation

Add fast L0/L2 contract tests, make symbolic audit bounded, add licensed real audio and external baselines, then establish L3/L4 fixed cases. Do this before algorithm/prompt claims.

### 5. Runtime context graph

Centralize deterministic evidence/context assembly. Make chord order stable, expose measured confidence/warnings, separate retrieval records from prompt text, and capture prompt/model/config versions.

### 6. Uncertainty and evidence propagation

Design a backward-compatible evidence envelope with hypotheses/alternatives only where detectors can support them. Add calibration and low-evidence tutor cases before changing user-facing claims.

### 7. Retrieval engineering

Audit corpus rights and source IDs; freeze a record schema; separate ingestion from serving; add query routing, thresholds/reranking, actual source text, citations, and L3 evaluation.

### 8. Tutoring loop

Unify streaming/non-streaming prompt construction. Add bounded assess/route/reason/verify behavior only against demonstrated L4 failures. Keep deterministic verification outside the model where possible.

### 9. Reliability and deployment

Introduce authenticated jobs, bounded workers, storage, cancellation, observability, cost controls, privacy/deletion, and deployment packaging. Run private alpha and measured beta before mobile wrapping.

## Top Dependency Leverage

The highest-leverage near-term work is contract tests plus security-boundary repair: it unlocks cleanup, real E2E verification, safer collaboration, and deployment without depending on detector or model research success.

