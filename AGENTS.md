# HorizonJam Agent Entry Point

HorizonJam v2.0 is a research prototype that turns short musician recordings into timed chord evidence, retrieval-assisted tutoring, and optional speech. It is not production ready.

## Start Here

1. Read [STATUS.md](STATUS.md) for current truth and evidence.
2. Use [docs/context/INDEX.md](docs/context/INDEX.md) to retrieve only the context relevant to the task.
3. Inspect the named source symbols and tests before changing code. Documentation can be stale.
4. Use the matching workflow in [.agents/skills](.agents/skills) for detector, RAG, tutor, evaluation, frontend, or security work.

Do not read every context document by default. Follow the router.

## Active Runtime

The current browser path is:

`nextjs-frontend/pages/index.js` -> `tutor_ws_relay.py` -> `ChordAIRAGTutor` -> `detection.run_detection()` -> retrieval/model/TTS -> WebSocket UI

`api_server.py`, `streamlit_app.py`, `run_pipeline.py`, and `chord_detection.py` are not the active browser path. See the classification in [docs/context/ARCHITECTURE.md](docs/context/ARCHITECTURE.md).

## Invariants

- Route application chord detection through `detection.run_detection()`.
- Keep detector implementations replaceable behind that boundary.
- Preserve normalized chord events: sorted, positive-duration, non-overlapping, stable fields.
- Treat `confidence` and warnings as evidence, not decoration; do not turn uncertainty into confident tutor claims.
- Keep written tutoring usable when TTS fails or is disabled.
- Do not reactivate archived or compatibility code accidentally.
- Verify every cross-layer contract change at its callers and integration boundary.
- Do not cite synthetic benchmark results as real-musician accuracy.

## Work Loop

`observe -> orient -> retrieve context -> define acceptance criteria -> change minimally -> focused test -> integration check -> inspect evidence -> update state`

Required evidence depends on the change:

| Change | Minimum evidence |
|---|---|
| Detector/normalizer | focused contract tests plus synthetic benchmark comparison |
| API/WebSocket | handler test plus affected caller/integration check |
| RAG | fixed retrieval cases plus relevance/grounding inspection |
| Tutor prompt/context | fixed cases, before/after outputs, correctness and uncertainty review |
| Frontend | build plus browser workflow check |
| Security | targeted validation of the affected trust boundary |
| Documentation only | link check, source cross-check, and no unsupported status claims |

## Leave Better State

Update `STATUS.md` only when verified project truth, blockers, decisions, benchmark state, or next actions materially change. Put stable architecture in `docs/context`, procedures in skills, rationale in `docs/decisions`, and measurements in tests/reports. Do not use `STATUS.md` as a diary.

