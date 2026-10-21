# HorizonJam v3 Current Status

Evidence labels:

- `VERIFIED`: confirmed from source or a completed command on the date stated by the evidence entry.
- `DOCUMENTED_NOT_REVERIFIED`: present in a checked-in report or prior handoff, but not freshly rerun.
- `INFERRED`: supported by source relationships but not observed end to end.
- `PLANNED`: intended work, not current capability.

## Current Milestone

`VERIFIED` The first readiness implementation adds session-owned upload IDs, bounded audio handling, cancellation/cleanup, job-scoped browser events, and stronger deterministic tutor checks. A clean Windows/Python 3.13 **contract-test** environment passes 100 tests (97 passed, 3 expected musical failures), `pip check`, and real-transport browser workflows with synthetic microphone input and stubbed providers. This does not establish full BasicPitch runtime installation, live-model quality, real-musician accuracy, or hosted-alpha readiness.

`VERIFIED` The real-performance pack still has zero approved cases. Its strengthened validator now rejects performer/session/audio leakage, mismatched held-out label digests, missing second annotators, and out-of-duration annotations. Fusion and temporal resolution remain inactive. Research metrics remain unavailable.

Resume [EXECUTION_PLAN.md](docs/context/EXECUTION_PLAN.md); see [readiness evidence](eval/readiness/README.md) and [reproduction profiles](docs/context/REPRODUCIBILITY.md).

## Verified Working

- `VERIFIED` Repository static serving and client-selected server paths are removed from the active relay. HTTP uploads require an in-memory capability from an origin-checked WebSocket; recordings use random IDs and private storage. Native WAV receives the same duration/silence validation as decoded audio.
- `VERIFIED` Active uploads are bounded to 16 MiB and decoded recordings to 0.5-30 seconds, mono/stereo and 8-96 kHz. Ready uploads expire after five minutes. Success, invalid-input, ready-delete, disconnect, and cooperative-cancellation cleanup have targeted tests; hard process interruption/crash recovery remain open.
- `VERIFIED` The browser awaits the session handshake, sends upload IDs, rejects stale connection/job events, supports Cancel analysis/Clear session, and receives all verified text before optional speech. The real HTTP/WS browser fixture passes desktop/mobile, synthetic microphone WAV, failure, cancellation, feedback and cleanup checks without provider calls.
- `VERIFIED` Eight fixed verifier counterexamples improve from 2/8 to 8/8. Unqualified performance observations are replaced under uncertainty, and paraphrased absent-source claims are removed. These remain bounded language checks, not semantic correctness or source-entailment guarantees.
- `VERIFIED` All 27 accepted research artifacts checked against the readiness baseline are unchanged. New before/after and integration evidence lives under `eval/readiness/`.

- `VERIFIED` Phase 7 `EvidenceSummary` categorizes each normalized chord as strong, partial, mixed, or limited from overlapping BasicPitch notes and frozen Librosa chroma without changing the symbolic winner or exposing raw arrays/scores. Three fixed tutor cases pass summary propagation and uncertainty behavior; both mixed/limited hard-label assertions are repaired before delivery.
- `VERIFIED` the browser exposes a collapsed `Why this chord?` disclosure and Correct/Wrong/Not sure feedback. Desktop 1440x1000 and mobile 390x844 Playwright checks passed with no horizontal overflow. Feedback is bounded to 50 local browser records and contains only a random session ID, compact predictions/evidence, detector, choice, and timestamp; no audio, filename, path, or server submission.
- `VERIFIED` Real Performance Pack v1 validates provenance rights, local-path containment, audio hashes, development/held-out splits, annotation confidence, timed segments, and coverage. The current zero-case manifest is valid for collection but not evaluation-ready; metrics and failure slices are explicitly unavailable, not zero.
- `VERIFIED` Phase 5 deterministic candidate fusion preserves canonical label structure, source provenance, true ranked alternatives, and uncalibrated agreement diagnostics. Equal-weight Jaccard/chroma fusion scored 7/8 on the paired synthetic cases, exactly matching both individual sources and changing no Jaccard result. Decision `D FUSION_NO_GAIN`; fusion was not promoted and Phase 6 was not started.
- `VERIFIED` Phase 4 executed LV-Chordia 1.1.0 only through a local-file subprocess adapter with upstream URL handlers disabled in an ignored isolated environment. It scored 0/8 exact and no unique correct cases on the controlled synthetic set, with the final 3/10/30-second adapter wall times of 11.55/11.34/12.41 seconds. Checkpoint-specific rights remain unresolved, status is `RESEARCH_ONLY`, decision `C DIRECT_MODEL_REDUNDANT`, and fusion weight is 0.0.
- `VERIFIED` Phase 3 product-safe DSP/chroma evidence passes its gate. The opt-in SoundFile/Librosa CQT path emits L1-normalized `PitchClassEvidence`; DSP and Jaccard each recognized 7/8 controlled synthetic block chords with complementary errors. Warm DSP extraction measured 0.249/0.386/0.757 seconds at 3/10/30 seconds. Decision `A DSP_COMPLEMENTARY` is synthetic-only; default detector behavior remains unchanged.
- `VERIFIED` Phase 2 direct BasicPitch evidence passes its gate: one inference supplies direct and MIDI-derived `NoteEvidence`; 26/26 notes matched across five structural/WAV cases, maximum timing drift was 1.10 ms, and downstream Jaccard events were identical. Decision `B DIRECT_BETTER` applies to evidence inspection only; MIDI and all default detector behavior remain active.
- `VERIFIED` `docs/publication/` contains an evidence-bounded abstract, venue-neutral systems-paper draft, open-source architecture post, primary-source competitive/related-work snapshot, and publication-to-production roadmap. The drafts explicitly withhold real-musician accuracy, calibrated-confidence, pedagogy, learning-outcome, and production-readiness claims.
- `VERIFIED` the sanitized v3 source archive contains 642 manifest-tracked files and passes full entry/hash/forbidden-path verification. Archive SHA-256: `66010af1a89f0c455fa12378905caaf72b485e574455943cf9ca24c37613810b`.
- `VERIFIED` provider-backed upload -> WebSocket analysis -> GPT tutoring -> sentence TTS passed on `tests/audio/pop.wav`: 2 chord events (`A - E`), 8 text chunks totaling 785 characters, 8 WAV chunks totaling 2,302,552 bytes, and a completion event.
- `VERIFIED` active OpenAI tutor, Chroma embedding, and TTS clients share a Windows-system-root TLS factory. It keeps `CERT_REQUIRED` and hostname verification enabled while relaxing only Python 3.13 strict-extension enforcement for a locally trusted issuer.
- `VERIFIED` Advanced Chord Scorer Forensics v1 records all 85 ranked candidates and reconciled score components for every one of the 96 complete oracle cases. It runs offline in about 1.4 seconds and produces deterministic JSON and Markdown artifacts.
- `VERIFIED` Chord Match Formulation Benchmark v1 compares baseline coverage, F1, Jaccard, three bounded unexplained-tone penalties, and a specificity-only tie rule while freezing the 85 candidates and all non-match score terms. Repeated runs produced byte-identical artifacts; no production detector code changed.
- `VERIFIED` an opt-in `rule_jaccard` detector now routes the advanced scorer with Jaccard matching through `detection.run_detection()` while leaving the default `hybrid` and `rule_viterbi` classifier behavior unchanged. Focused tests preserve the normalized event contract and recover representative D7/G7 oracle cases.
- `VERIFIED` Jaccard Post-Transcription Detector-Path Benchmark v1 completes 40/40 paired synthetic MIDI cases per detector. Compared with `hybrid`, `rule_jaccard` improves root 47.2% -> 52.9%, MajMin 38.9% -> 52.9%, sevenths 27.5% -> 40.0%, and MIREX 52.0% -> 55.9%; decision gate `A. ADVANCE_TO_REAL_AUDIO`. Repeated runs produced byte-identical JSON and Markdown hashes.
- `VERIFIED` Single-WAV Analysis Performance Gate v1 completes `tests/audio/pop.wav` through real `rule_jaccard` and `hybrid` BasicPitch paths. Cold 3-second `rule_jaccard` runs measured 13.03s and 10.48s, the same-process repeat 1.31s, and warm 3/10/30-second scaling 2.14/5.57/10.44s. Decision: `F. MIXED` (environment-specific Numba cache behavior, codec discovery overhead, and cold imports); model/note/chord equivalence checks pass.
- `VERIFIED` replacing classifier-only `librosa.midi_to_note` calls with a behavior-compatible local helper reduced a representative synthetic MIDI analysis from more than ten CPU-bound minutes to 0.69 seconds without changing oracle metrics or frozen scorer reproduction.
- `VERIFIED` Oracle Chord Classifier Benchmark v1 evaluates 96 complete chords per classifier (8 intended qualities x 12 roots) using exact symbolic notes, plus inversions, duplicated notes, omitted tones, seventh-without-fifth cases, and enharmonic-interface characterization. It runs offline in about one second and writes deterministic JSON and Markdown reports.
- `VERIFIED` Active modules compile: `python -m compileall -q detection.py chordai_gpt_tutor.py tutor_ws_relay.py tts_server.py unified_rag_system.py api_server.py src eval` passed on 2026-08-17.
- `VERIFIED` the Next.js production build passed with `npm exec next -- build ./nextjs-frontend` on 2026-08-17.
- `VERIFIED` a focused `normalize_and_validate()` edge-case check passed for sorting, negative-start clamping, overlap handling, adjacent merge, warning emission, and confidence preservation.
- `VERIFIED` `detection.run_detection()` is used by `ChordAIRAGTutor._run_horizon_jam()` and `eval/evaluate_chords.py`.
- `VERIFIED` the frontend supports file upload, microphone capture, client-side WAV encoding, WebSocket messages, and TTS playback in source.
- `VERIFIED` the relay runs detection, retrieval, model streaming, and sentence-level TTS outside the event loop via executors/async I/O.
- `VERIFIED` TTS failure is caught in `TutorWebSocketManager.send_text_chunk()` and does not remove the written text path.
- `VERIFIED` 16 focused tests cover detector normalization, evidence propagation, actual retrieved text/provenance, no-result honesty, uncertainty repair before delivery, shared streaming/non-streaming context, developer trace, backward-compatible events, adversarial retrieval pollution, and the in-process active relay path.
- `VERIFIED` the deterministic tutor harness passes 13/13 cases: 7/7 grounded, 4/4 uncertainty, 6/6 retrieval-absence, with 5/5 structural evidence fields propagated.
- `VERIFIED` the Next.js production build passed after the tutor integration.

## Partially Working

- `VERIFIED` normalized events carry `start`, `end`, `chord`, `confidence`, and `source_detector`; application responses also duplicate legacy event fields.
- `VERIFIED` `hybrid` supports optional ML artifacts, but `models/` contains no files; it currently follows the rule/Viterbi behavior.
- `VERIFIED` retrieval now sends a bounded maximum of three selected records and 3,000 total document characters, with source, record ID, rank, relevance, and metadata, to the tutor context.
- `VERIFIED` active streaming supports one request at a time per connection in code; concurrency, cancellation, and multi-user behavior have no automated verification.
- `DOCUMENTED_NOT_REVERIFIED` local three-service operation was previously exercised; servers were not started in this first pass.

## Known Failures

- `VERIFIED` the advanced scorer's pitch match is asymmetric: `|input intersect template| / |template|`. A complete triad subset and its seventh extension both receive `1.0`, while unexplained input tones receive no penalty. Nine dominant sevenths therefore tie their major triad and lose through stable template insertion order; fixed E-major priors make the major triad strictly higher for E7, A7, and B7.
- `VERIFIED` Jaccard is the strongest isolated replacement formulation in the frozen benchmark: 98.8% supported complete exact, 97.2% complete seventh exact, and 76.1% mean supported robustness. Its remaining complete miss is `Bm7 -> B:min` under the frozen E-major prior; diminished remains outside the candidate vocabulary.
- `VERIFIED` disabling any existing score term independently does not recover any dominant-seventh case. No-key and matching-supported-key modes also remain at 0% seventh exact accuracy, so context is secondary rather than the primary collapse mechanism.
- `VERIFIED` no diminished candidate template exists in the advanced scorer. This is separate from seventh subset collapse and makes diminished recognition impossible regardless of score weights.
- `VERIFIED` bass is useful but unstable: across 20 non-root-position representative voicings it changed 10 winners, caused 8 wrong-root results and 5 right-root/wrong-quality results, while recovering D7 and G7 only in third inversion.
- `VERIFIED` the active simple classifier reaches 55.2% root, 32.3% quality, and 28.1% exact accuracy on 96 complete oracle chords. Dominant seventh, major seventh, and diminished exact accuracy are each 0%; all-root major and minor behavior remains incomplete.
- `VERIFIED` the existing advanced scorer reaches 97.9% root, 50.0% quality, and 50.0% exact accuracy on the same oracle chords. It recognizes all complete major, minor, sus2, and sus4 cases, but 0% of dominant seventh, major seventh, minor seventh, and diminished cases; it is therefore not ready for production activation unchanged.
- `VERIFIED` the simple classifier is prediction-invariant across inversions and duplicated notes because it reduces notes to an unordered unique set. The advanced scorer is 100% invariant to duplicated notes but only 46.9% invariant across inversions because bass affects scoring.
- `VERIFIED` neither symbolic classifier emits confidence. Hybrid adds a constant `0.8` rule weight later, so current classifier confidence has no discriminative relationship to oracle correctness.
- `VERIFIED` `_evaluation.py --section labeled` still exceeded a 25-second timeout on the first `Amaj.mid`; flushed stage output and an earlier stack trace locate the delay in cold lazy librosa/Numba initialization through `src/chord_detector.py`, not RAG/model startup.
- `VERIFIED` the prior direct-WAV timeout was localized rather than an inference-only failure: Numba cache validation under user site-packages was pathological and `audioread` backend discovery added about 15 seconds before SoundFile WAV decoding. The sanctioned controlled WAV now completes, while the full real-audio matrix remains incomplete.
- `VERIFIED` `_evaluation.py --section key` completes and scores 6/7; `Am-F-C-G` supports relative C major/A minor and the fixture's single A-minor label is too strict without stronger tonal-center evidence.
- `VERIFIED` raw production detector overlaps are repaired by `normalize_and_validate()` rather than prevented at their source.
- `VERIFIED` dominant seventh recognition is a leading checked-in synthetic confusion.
- `VERIFIED` alternatives remain empty because active detectors do not produce calibrated alternatives; the evidence layer does not invent them.
- `VERIFIED` provider-backed service E2E now passes through the active upload and WebSocket boundaries. Browser microphone interaction remains manual and has no automated browser run after the service restart.

## Current Benchmark State

`VERIFIED` [eval/oracle_classifier_report.json](eval/oracle_classifier_report.json) and [eval/oracle_classifier_report.md](eval/oracle_classifier_report.md) contain a fresh 2026-08-18 classifier-isolation run:

| Classifier | Root | Quality | Exact | Major/minor exact | Seventh exact |
|---|---:|---:|---:|---:|---:|
| active simple | 0.552 | 0.323 | 0.281 | 0.583 | 0.167 |
| existing advanced | 0.979 | 0.500 | 0.500 | 1.000 | 0.000 |

Oracle benchmark decision gate: `D`. The advanced scorer materially improves roots and complete triads/suspensions, but both paths have structural quality failures. Another isolated scoring experiment is required before choosing repair, activation, or replacement.

`VERIFIED` [eval/advanced_scorer_forensics.json](eval/advanced_scorer_forensics.json) and [eval/advanced_scorer_forensics.md](eval/advanced_scorer_forensics.md) contain the fresh candidate-level follow-up. Every decomposed score exactly matches `score_chord_candidate()` within floating-point tolerance. Decision gate: `C. TEMPLATE_MODEL_PROBLEM`; the current match formulation systematically favors strict subsets on ties, and diminished candidates are absent.

`VERIFIED` [eval/match_formulation_report.json](eval/match_formulation_report.json) and [eval/match_formulation_report.md](eval/match_formulation_report.md) contain Chord Match Formulation Benchmark v1. The baseline is reproduced with zero winner mismatches and zero score error. Jaccard wins the frozen decision rule over F1, specificity-only ordering, and unexplained-tone penalties: decision gate `B. BIDIRECTIONAL_MATCH_WINNER`. This is offline classifier evidence, not an active detector change or real-audio accuracy claim.

`VERIFIED` [eval/jaccard_detector_path_report.json](eval/jaccard_detector_path_report.json) and [eval/jaccard_detector_path_report.md](eval/jaccard_detector_path_report.md) contain the accepted 40-song post-transcription comparison. `rule_jaccard` passes every frozen gate and advances to real-audio validation. BasicPitch is bypassed in this report, synthetic fixtures are not real musicians, and default activation remains prohibited. Residual leading confusions include sharp-root collapse and major-to-major-seventh overclassification.

`VERIFIED` [eval/audio_path_benchmark.json](eval/audio_path_benchmark.json) and [eval/audio_path_benchmark.md](eval/audio_path_benchmark.md) contain the controlled real-WAV runtime gate. BasicPitch ONNX model state is reused within a process; warm inference dominates duration scaling, while MIDI serialization/parsing is secondary. The fixture's BasicPitch note/model hashes and normalized `Am-C-Em` events match the pre-optimization observation exactly. This is performance/equivalence evidence, not real-musician accuracy.

`DOCUMENTED_NOT_REVERIFIED` [eval/report.json](eval/report.json) contains 40 pretty_midi sine-rendered progressions:

| Detector | Root | MajMin | Sevenths | MIREX | Files OK |
|---|---:|---:|---:|---:|---:|
| production | 0.319 | 0.270 | 0.211 | 0.356 | 40/40 |
| hybrid | 0.585 | 0.517 | 0.356 | 0.588 | 40/40 |
| rule_viterbi | 0.585 | 0.517 | 0.356 | 0.588 | 40/40 |

This is an engineering baseline, not real-audio accuracy. The full matrix was not rerun in this pass.

## Current Runtime Architecture

`VERIFIED` Browser `runAnalysis()` opens an origin-checked WebSocket, receives a session capability, uploads with that capability, then sends an opaque upload ID over `/ws/tutor`. `websocket_tutor_endpoint()` calls `TutorWebSocketManager.analyze_audio_streaming()`, which invokes detection, retrieval, GPT-4o streaming, WebSocket text, and optional TTS audio.

See [docs/context/ARCHITECTURE.md](docs/context/ARCHITECTURE.md) and [docs/context/HARNESS.md](docs/context/HARNESS.md).

## Active Architectural Debt

- `VERIFIED` active event responses contain both v2 and compatibility fields.
- `VERIFIED` streaming and non-streaming generation share `_prepare_tutor_context()`; legacy implementations remain named compatibility methods and should be removed after migration confidence is established.
- `VERIFIED` `src/chord_detector.py` defines `analyze_midi_chords` and `detect_optimal_window_size` more than once; later definitions shadow earlier ones.
- `VERIFIED` the web path calls private `ChordAIRAGTutor` methods rather than a stable application service interface.
- `VERIFIED` runtime retrieval and ingestion share a mutable persistent collection; the non-web `analyze_audio()` path can embed analyses automatically.
- `VERIFIED` Direct web dependencies and a complete Windows/Python 3.13 contract-test version lock exist. Full BasicPitch runtime installation remains unresolved: its TensorFlow dependency metadata conflicts with Python 3.13. The test lock does not establish real inference or a dependency security audit.

## Security / Release Blockers

- `VERIFIED` The active relay now removes repository static serving, rejects client paths, uses session-owned upload IDs and validates/cleans bounded recordings. Targeted denial and lifecycle tests pass.
- `VERIFIED` Session capabilities and origin checks are not account authentication. Limits of 16 sessions, one upload per session, three analyses per session and two analysis workers do not provide per-user/global rate limits or provider-spend budgets; a new connection can reset a session budget.
- `VERIFIED` Native workers/provider calls cannot be forcibly interrupted. Cancellation suppresses later stages and delivery; cleanup waits for readers to finish. Hard worker deadlines, crash recovery, decoder sandboxing, and durable jobs remain open.
- `VERIFIED` `tts_server.py` still allows all CORS origins and is directly callable by the browser. Private TTS/authentication/quota controls remain required before hosting.
- `VERIFIED` `.env.production` is ignored by `.env.*` and is not tracked. This correction is not evidence of a complete secret/history audit.
- `VERIFIED` Corpus rights, immutable serving, redacted logging, dependency security audit, retention/deletion disclosures and hosted account controls remain incomplete.

The relay command now binds to loopback by default. Do not expose current services to the public internet.

## Research Blockers

- `VERIFIED` no populated real-microphone result table exists.
- `VERIFIED` no L1 transcription, L5 pedagogy, or L7 learning-outcome evaluation exists; L3/L4 now have deterministic structural/adversarial coverage but no expert-labeled corpus or live-model quality study.
- `VERIFIED` corpus and dataset provenance/licenses are not audited.
- `VERIFIED` no external chord-recognition baseline is implemented in the harness.
- `VERIFIED` the isolated repair experiment selects Jaccard, but activation still requires a production-scoped detector change with contract tests, synthetic before/after evidence, and explicit review of key-prior, bass/inversion, omitted-root, and diminished-vocabulary behavior.
- `VERIFIED` the production-scoped Jaccard mode, contract tests, post-transcription synthetic comparison, and controlled BasicPitch WAV runtime gate now pass. Key-prior, bass/inversion, omitted-root, diminished-vocabulary, licensed real-audio, and accuracy gates remain open.
- `PLANNED` a defensible system-paper claim, ablations, latency/cost study, and musician study.

## Decisions Currently in Force

- `VERIFIED` one sanctioned detector boundary: `detection.run_detection()`.
- `VERIFIED` normalized chord events are the detector/application interchange target.
- `VERIFIED` TTS is optional to the written tutor experience.
- `VERIFIED` canonical agent context lives in agent-neutral repository documents; vendor files are adapters.
- `VERIFIED` ADR 005 freezes v3 and requires external detector feasibility, baseline, complementarity, fusion, product, and activation gates. Tournament adapters remain subprocess-isolated and cannot bypass `detection.run_detection()` for production.

## Open Questions

- `INFERRED` which checked-in RAG database is authoritative: `RAG/unified_chroma_store` is the configured default, while another root-level store also exists.
- `INFERRED` which corpus records may legally ship in an open-source release.
- `INFERRED` whether `api_server.py` and Streamlit are still supported compatibility surfaces or can later be archived.
- `PLANNED` the target paper venue and its publication constraints.
- `PLANNED` the minimum supported Python/browser/mobile versions.

## Top Next Actions

1. Resolve the full BasicPitch runtime dependency profile in isolation, preserve model/event equivalence, and verify a clean real-WAV run. The contract-test lock already passes locally; remote CI has not yet run.
2. Complete account authentication, per-user/global rate and spend controls, private TTS, bounded/isolated worker deadlines and crash recovery before hosted alpha.
3. Audit corpus rights; separate immutable serving from ingestion and prevent unconsented persistence. Finish privacy/retention/deletion and release-license decisions.
4. Collect and independently annotate at least 20 approved real recordings under the stricter collection protocol. Freeze grouped splits and actual label hashes before running unchanged detectors; obtain fresh confirmation data after result-informed changes.
5. Freeze quality/coverage/actionability/latency/cost gates from pilot evidence, then run blinded expert review and a musician alpha. Do not promote detectors or claim positive research outcomes from readiness tests.

## Last Verified

2026-10-03 readiness pass: 100 active contract tests in a clean environment (97 passed, 3 expected musical failures), dependency consistency, production frontend build, and real-transport browser workflows with synthetic microphone and stubbed perception/providers. Verifier counterexamples pass 8/8. No fresh live-provider, real-musician accuracy, calibration, pedagogy, learning-outcome, fusion-gain, temporal-resolution, or default-activation claim is supported. Earlier provider-backed and musical reports remain historical evidence; they were not regenerated.
