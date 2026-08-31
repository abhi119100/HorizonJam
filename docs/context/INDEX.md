# HorizonJam Context Router

This is the canonical entrypoint for project knowledge. Retrieve the smallest relevant neighborhood; do not load every document for every task.

## Route by Task

| Task | Read first | Then inspect | Workflow |
|---|---|---|---|
| Understand product scope or user flow | [PRODUCT.md](PRODUCT.md) | frontend and relay symbols named there | `repo-orientation` |
| Change chord detection or normalization | [ARCHITECTURE.md](ARCHITECTURE.md#detection-graph), [EVALUATION.md](EVALUATION.md) | `detection.py`, selected `src/` detector, callers | `detector-change` |
| Change key or guitar context | [ARCHITECTURE.md](ARCHITECTURE.md#analysis-enrichment) | `ChordAIRAGTutor._detect_key_from_events`, tab generator | `detector-change` |
| Change retrieval or corpus ingestion | [ARCHITECTURE.md](ARCHITECTURE.md#rag-graph), [HARNESS.md](HARNESS.md#retrieval-context) | `unified_rag_system.py`, relevant `RAG/` ingestion script | `rag-change` |
| Change tutor behavior or prompt context | [HARNESS.md](HARNESS.md), [EVALUATION.md](EVALUATION.md#l4--tutor-reasoning) | tutor generation and streaming methods | `tutor-change` |
| Change recording, upload, WebSocket, or rendering | [PRODUCT.md](PRODUCT.md#runtime-user-flow), [ARCHITECTURE.md](ARCHITECTURE.md#http-and-websocket-contract) | frontend handlers and relay manager | `frontend-e2e` |
| Run or interpret evaluations | [EVALUATION.md](EVALUATION.md) | `eval/`, `_evaluation.py`, `_e2e_smoke.py` | `evaluation` |
| Work on deployment, privacy, or security | [SECURITY.md](SECURITY.md) | backend/TTS trust boundaries and config | `security-review` |
| Plan modernization or release order | [MODERNIZATION.md](MODERNIZATION.md), [STATUS.md](../../STATUS.md) | affected graph and evidence | `repo-orientation` |
| Research external or fused detectors | [research/detector_tournament](../../research/detector_tournament/README.md), [EVALUATION.md](EVALUATION.md) | tournament matrix/specification; production boundary remains unchanged | `detector-change`, `evaluation` |

## Canonical Documents

- [PRODUCT.md](PRODUCT.md): user goals, product graph, scope, and non-goals.
- [ARCHITECTURE.md](ARCHITECTURE.md): active runtime, subsystem graphs, contracts, node ownership, and file classification.
- [HARNESS.md](HARNESS.md): runtime AI provider, prompt/context assembly, retrieval packet, streaming, uncertainty, and proposed bounded loop.
- [EVALUATION.md](EVALUATION.md): L0-L7 coverage, commands, claims supported, and missing evidence.
- [SECURITY.md](SECURITY.md): trust boundaries, verified release blockers, audio/privacy handling.
- [MODERNIZATION.md](MODERNIZATION.md): code/document discrepancies, risks, prerequisites, and proposed sequence.
- [STATUS.md](../../STATUS.md): current verified state only.
- [decisions](../decisions): durable architectural rationale.

## Evidence Labels

Use `VERIFIED`, `DOCUMENTED_NOT_REVERIFIED`, `INFERRED`, and `PLANNED` as defined in `STATUS.md`. Source inspection can verify topology; runtime reliability requires execution. A checked-in report is evidence of a prior run, not a fresh run.

## Context Ownership

| Knowledge | Owner |
|---|---|
| Current milestone, blockers, benchmark status | `STATUS.md` |
| Stable product and architecture | `docs/context/` |
| Repeated procedures | `.agents/skills/*/SKILL.md` |
| Durable decision rationale | `docs/decisions/` |
| Measurements | tests, `eval/report.*`, logs |
| Historical implementation detail | `SESSION_HANDOFF.md`, `_archive/` |
