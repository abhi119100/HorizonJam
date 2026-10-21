# Verified Architecture

## Active Runtime Graph

```text
Home.runAnalysis / analyzeRecording
  -> POST /upload-audio: upload_audio
  -> WS /ws/tutor: websocket_tutor_endpoint
  -> TutorWebSocketManager.analyze_audio_streaming
       -> ChordAIRAGTutor._run_horizon_jam
            -> detection.run_detection
                 -> _run_production OR _run_hybrid
                 -> normalize_and_validate
            -> _detect_key_from_events
            -> _add_guitar_tabs_to_data
       -> ChordAIRAGTutor._retrieve_rag_context
            -> build PerformanceEvidence + assess intent/uncertainty
            -> UnifiedRAGSystem.query
                 -> Chroma collection.query
            -> bounded selection of actual text + provenance
       -> ChordAIRAGTutor.stream_rag_tutoring
            -> shared explicit tutor context
            -> OpenAI chat.completions.create(stream=True)
            -> verify_and_repair_response before callback delivery
       -> TutorWebSocketManager.send_message / send_text_chunk
            -> WebSocket text / POST tts_server / WebSocket bytes
  -> Home.ws.onmessage -> UI state and audio queue
```

This is verified from callers. It was not observed live in the 2026-08-17 pass.

## HTTP and WebSocket Contract

| Boundary | Input | Output |
|---|---|---|
| `WS /ws/tutor` handshake | allowed local browser Origin | `session` with short-lived capability token, protocol 1 |
| `POST /upload-audio` | multipart `audio_file`, Bearer session capability | `success`, opaque `upload_id`, expiry and normalized audio metadata; no path/filename |
| WS analyze | `type=analyze`, `upload_id`, optional question (<=2000 chars), explicit `speech` bool | job-scoped status, chord_analysis, text_chunk, complete/error |
| WS cancel | `type=cancel`, owned `upload_id` | cancelled; further work/delivery suppressed; cleanup waits for active readers |
| `DELETE /uploads/{upload_id}` | Bearer owner capability | deletion or cooperative cleanup; unavailable/foreign IDs denied |
| Optional speech | after all verified text and written completion | bounded binary WAV; frontend currently requests written analysis and uses Speak separately |
| `POST /tts` | `{text}` on existing separate TTS service | WAV; private authenticated proxy remains a release prerequisite |

`upload_store.py` owns random private directories and in-memory sessions. One pending upload per session, 16 MiB upload/body-spooling bound (+64 KiB multipart allowance), decoded 0.5-30 second mono/stereo 8-96 kHz audio normalized to mono PCM16 44.1 kHz, five-minute ready expiry, 20-minute idle sessions, two analysis workers. Origin/session capabilities are local isolation, not account authentication or global spend controls.

The browser opens a fresh connection for each analysis, waits for its capability, and ignores stale connection/job events. Cancel/clear/disconnect invalidate the connection and suppress downstream stages. In-flight native/provider calls are cooperative only; cleanup retains ownership until the worker exits. A 120-second delivery deadline does not imply hard CPU/provider termination. Process crash cleanup/durable state remain unimplemented.

No repository or upload directory is statically served. The old embedded relay page remains unused compatibility content; the active UI is Next.js.

## Detection Graph

```text
WAV path
  -> detector selection: selected_detector()
  -> production: AccurateAudioToChordsPipeline.run_pipeline()
     OR
     hybrid/rule: reusable BasicPitch ONNX runtime -> temporary MIDI -> HybridChordDetector.detect_chords()
  -> raw event adaptation
  -> normalize_and_validate()
  -> normalized ChordEvent[] + warnings
  -> compatibility event fields in ChordAIRAGTutor._run_horizon_jam()
  -> duration-weighted music21 key estimate + guitar tabs
```

### Detection Nodes

| Node | Owner | Input/output | Callers | Verification/risk |
|---|---|---|---|---|
| `run_detection` | `detection.py` | WAV path -> normalized result dict | tutor, evaluator | synthetic report; catches detector exceptions as warnings/empty events |
| `normalize_and_validate` | `detection.py` | raw event list -> valid events + repairs | `run_detection` | focused contract tests exist; overlap repair can hide detector defects |
| `_run_production` | `detection.py` + `src/pipeline.py` | WAV -> raw events | `run_detection` | compatibility/debug detector; checked-in MajMin 0.270 |
| `_run_hybrid` | `detection.py` + `src/hybrid_chord_detector.py` | WAV -> BasicPitch MIDI -> chords | `run_detection` | empty `models/`; hybrid and rule behavior match |
| `transcribe_wav_to_midi` | `src/basic_pitch_runtime.py` | validated WAV -> caller-owned temporary MIDI | `_wav_to_midi` | process-local ONNX model singleton; serialized by a lock; temporary MIDI is deleted by `_run_hybrid` |
| `rule_jaccard` experiment | `detection.py` + `src/chord_detector.py` | same hybrid path with advanced Jaccard classifier | `run_detection` | opt-in only; post-transcription gate advances to real audio, not default activation |
| `_detect_key_from_events` | `chordai_gpt_tutor.py` | formatted chord events -> key string | tutor adapter | `_evaluation.py` exists but full audit timed out |
| `GuitarTabGenerator` | `src/guitar_tab_generator.py` | chord labels -> shapes/tabs | tutor/hybrid helpers | no active automated contract test |

The normalized event target is `start`, `end`, `chord`, `confidence`, `source_detector`. `estimated_key` remains `None` at the detection boundary and is added by the tutor layer. Application events duplicate `start_time`, `end_time`, `duration_seconds`, and `chord_symbol` for compatibility.

`run_detection(include_runtime_trace=True)` adds the opt-in
`single-wav-runtime-v1` trace used by `eval/benchmark_audio_path.py`; default
responses are unchanged. BasicPitch 0.4.0 returns model tensors, note events
with amplitude/pitch-bend evidence, and an in-memory PrettyMIDI object. The
active compatibility path still serializes that object and reparses MIDI, so
the richer model evidence is measured and hashed for evaluation but is not yet
part of the detector contract.

### Phase 1 Harmonic Evidence Bridge

The active internal representations and their exact owners are:

```text
basic_pitch.inference.predict()
  -> in-memory PrettyMIDI in src/basic_pitch_runtime.transcribe_wav_to_midi()
  -> temporary MIDI file returned through detection._wav_to_midi()
  -> parsed note dictionaries from src.chord_detector.parse_midi_notes()
       {start, end, pitch, velocity, duration}
  -> pitch lists/sets and rule labels in the effective late definition of
     src.chord_detector.analyze_midi_chords()
  -> HybridChordDetector ensemble events (fixed rule confidence is assigned
     in ensemble_predictions(); it is not calibrated confidence)
  -> raw event dictionaries in detection._run_hybrid()
  -> normalized {start, end, chord, confidence, source_detector} events in
     detection.run_detection()
  -> compatibility fields in ChordAIRAGTutor._run_horizon_jam()
  -> PerformanceEvidence in tutor_evidence.build_performance_evidence()
```

**Implemented:** `src/harmonic_evidence.py` provides validated `NoteEvidence`,
`ChordHypothesis`, and `HarmonicEvidencePacket` structures. Existing parsed
MIDI notes, BasicPitch 0.4.0 in-memory note tuples, and normalized events can be
adapted into these structures. A
developer can request deterministic packet serialization with
`run_detection(include_harmonic_evidence=True)`. One inference supplies direct
`NoteEvidence` and the existing MIDI compatibility representation. The packet
prefers direct notes for inspection and records their comparison; active chord
analysis remains on MIDI.

**Unchanged:** `run_detection()` remains the application boundary and its
default result is unchanged. BasicPitch serialization, detector algorithms,
classifier scoring, Viterbi behavior, normalization, `PerformanceEvidence`,
retrieval, prompts, tutor behavior, and UI payloads are unchanged.

**Measured:** the Phase 2 gate matched 26/26 notes across four deterministic
synthetic structures and the repository `pop.wav` fixture. Maximum onset or
offset drift was 1.10 ms and direct-note replay produced identical Jaccard
chord events in all five cases. MIDI quantizes amplitude and can reorder notes.
This is representation equivalence evidence, not real-performance accuracy.

**Implemented:** Phase 3 adds an independent opt-in
`soundfile -> Librosa CQT -> L1 chroma -> PitchClassEvidence` path in
`src/dsp_chroma.py`. `run_detection(include_dsp_evidence=True)` includes raw
frames and metadata in the developer packet. The bounded chord-profile scorer
is a research diagnostic; its cosine values are normalized support, not
confidence. DSP failure remains separate from normal detector warnings/output.

**Measured:** on eight deterministic synthetic block chords, DSP and Jaccard
were each exact on 7/8. DSP alone recovered `Bdim`; Jaccard alone recovered
`Dsus2`. Warm DSP extraction totals for repeated repository audio were
0.249/0.386/0.757 seconds at 3/10/30 seconds. Decision
`A DSP_COMPLEMENTARY` applies only to this controlled set.

**Implemented and measured:** Phase 4 adds opt-in `DirectChordEvidence` through
a bounded, local-file-only subprocess adapter. LV-Chordia 1.1.0 is isolated
from the active environment, its upstream URL handlers are disabled, and malformed,
timeout, and unavailable-runner failures remain packet-only warnings. It was
0/8 exact with no unique correct controlled case and is `RESEARCH_ONLY` because
checkpoint-specific rights remain unresolved. Decision: `C
DIRECT_MODEL_REDUNDANT`; its fusion weight is 0.0.

**Implemented but not promoted:** Phase 5 adds canonical `ChordCandidate`
structures and an interpretable candidate-ranking experiment. Jaccard and
Librosa chroma receive equal weights; scores are weighted normalized support,
not probability or confidence. Paired replay scored 7/8, equal to both
individual sources, and changed no Jaccard output. Decision: `D
FUSION_NO_GAIN`.

**Stopped:** the Phase 5 hard gate prohibits Phase 6. There is no
`multi_evidence` detector, boundary resolver, temporal decoder, or product
activation. The temporary MIDI path remains required by the active symbolic
detector.

**Phase 7 product evidence:** the active tutor path requests the same symbolic
detector output plus opt-in BasicPitch and frozen Librosa chroma evidence.
`src/evidence_summary.py` aligns evidence to each normalized chord interval and
produces a compact categorical `EvidenceSummary`. It never changes the chord
winner. `PerformanceEvidence` carries validated summaries to the tutor prompt;
raw notes, chroma vectors, profile scores, model output, and research adapters
remain outside the prompt and browser payload.

```text
normalized chord + overlapping direct notes + frozen chroma
  -> EvidenceSummary (strong / partial / mixed / limited)
  -> PerformanceEvidence
  -> tutor uncertainty rules
  -> chord_analysis WebSocket payload
  -> collapsed Why this chord? disclosure
```

Browser feedback is local-only and bounded. It records a random session ID,
compact predicted chords/summaries, detector, user choice, and timestamp. It
does not upload or retain audio, filenames, paths, or raw evidence.

#### Migration Ledger

| Current representation | New representation | Adapter | Active callers migrated? | Old path still required? | Removal phase |
|---|---|---|---|---|---|
| BasicPitch note tuple | `NoteEvidence` | `basic_pitch_event_to_note_evidence()` | Developer inspection preferred source | Yes, for symbolic analysis | Later detector migration decision |
| `parse_midi_notes()` dictionary | `NoteEvidence` | `to_note_evidence()` / `notes_to_evidence()` | Compatibility comparison | Yes | Later detector migration decision |
| normalized event dictionary | `ChordHypothesis` | `normalized_event_to_hypothesis()` | Developer inspection only | Yes | Later caller-by-caller decision |
| notes + normalized events + warnings | `HarmonicEvidencePacket` | opt-in assembly in `run_detection()` | No production caller | Yes | Grow in later evidence phases |
| CQT chroma matrix | `PitchClassEvidence` | `extract_pitch_class_evidence()` | Opt-in developer inspection | Independent source retained | Fusion gate decision |
| LV-Chordia labels | `DirectChordEvidence` | isolated subprocess adapter | Opt-in developer inspection only | No; model rejected from active fusion | Retain for reproducible research |
| source rankings | `ChordCandidate` | `fuse_ranked_sources()` | Research evaluator only | Yes; production paths remain authoritative | Revisit only after real-performance evidence |
| harmonic packet + normalized chord | `EvidenceSummary` | `build_evidence_summaries()` | Active tutor/browser path | Yes; raw evidence remains internal | Revalidate rules on licensed real performances |

Known duplicate and shadowed definitions in `src/chord_detector.py` remain
cleanup debt. They were not modified because combining legacy cleanup with an
internal contract migration would make regression attribution ambiguous.

## Analysis Enrichment

`ChordAIRAGTutor._run_horizon_jam()` owns the current adapter between normalized detector results and the browser payload. It calculates key after detection and adds guitar tabs. This means key and tabs are not part of the detector contract even though they appear in `chord_analysis`.

## RAG Graph

```text
historical sources / scraped content / chord analyses
  -> multiple experimental ingestion scripts in RAG/
  -> UnifiedRAGSystem.add_document or embed_chord_analysis
  -> Chroma PersistentClient collection
  -> _retrieve_rag_context query string from question + unique chords + key + progression
  -> UnifiedRAGSystem.query(n_results=5)
  -> bounded relevance selection
  -> actual retrieved text + source/record provenance
  -> shared tutor context and evidence trace
```

### RAG Nodes

| Node | Owner | Input/output | Risk |
|---|---|---|---|
| `UnifiedRAGSystem.__init__` | `unified_rag_system.py` | DB/config -> OpenAI-embedded Chroma collection | default path ambiguity; startup requires API key |
| `add_document` | same | text/metadata -> collection record | corpus provenance not enforced |
| `embed_chord_analysis` | same | analysis -> generated document/metadata | runtime mutation; non-web `analyze_audio()` invokes it |
| `query` | same | text/filter -> ranked result dict | no retrieval evaluation; similarity is `1-distance` without calibration |
| `_retrieve_rag_context` | `chordai_gpt_tutor.py` | performance/question -> bounded evidence packet | lexical gate is deterministic but simple; embedding similarity is not calibrated |
| `select_retrieved_evidence` | `tutor_evidence.py` | raw result dict -> selected text/provenance + selection trace | maximum 3 records, 1,200 characters each, 3,000 total |

The active relay does not call `analyze_audio()` and therefore does not embed each web analysis. Other entrypoints can. The main tutor now receives selected document text; this does not establish corpus correctness or licensing.

## Tutor and TTS Ownership

Tutor model/provider, prompt assembly, and streaming are mapped in [HARNESS.md](HARNESS.md). `tts_server.py` attempts local `MoshikaCore`; when allowed, it falls back to OpenAI `tts-1` with voice `alloy`. TTS is a separate presentation service and exceptions are non-fatal to text delivery.

## Important Configuration

| Variable | Actual consumer | Notes |
|---|---|---|
| `OPENAI_API_KEY` | tutor, RAG, TTS fallback | required for active GPT/RAG initialization |
| `RAG_DB_PATH` | tutor/RAG | default `RAG/unified_chroma_store` |
| `RAG_COLLECTION_NAME` | tutor/RAG | default `music_theory` |
| `RAG_MODEL_NAME` | `UnifiedRAGSystem` direct construction | tutor hardcodes `model_name="openai"` |
| `HORIZONJAM_DETECTOR` | `detection.selected_detector` | actual detector selector |
| `HORIZON_CONFIDENCE_THRESHOLD`, `HORIZON_MIN_DURATION` | not used by active detection boundary | historical/config discrepancy |
| `TTS_ALLOW_OPENAI_FALLBACK` | `tts_server.py` | defaults enabled |
| `MOSHI_MODEL_DIR` | local TTS implementation | optional local model path |
| `TTS_SERVER_URL` | not read by active relay | relay currently hardcodes localhost URL |
| `NEXT_PUBLIC_*` service URLs | frontend | production endpoint overrides |

## Active vs Legacy Classification

| Classification | Paths | Basis |
|---|---|---|
| ACTIVE | `nextjs-frontend/pages/index.js`, `tutor_ws_relay.py`, `tts_server.py`, `chordai_gpt_tutor.py`, `detection.py`, `unified_rag_system.py`, active imports under `src/` and `utils/` | reachable from the documented browser/runtime path |
| COMPATIBILITY | `src/pipeline.py`, `run_pipeline.py`, legacy event fields in tutor response, `api_server.py` | retained/callable old interfaces; not the current browser route |
| EXPERIMENTAL | `chord_detection.py`, training/ML modules, RAG ingestion/check scripts, `analyze_key_ties.py`, local Moshi setup/test files | tooling or alternative paths without active product callers |
| LEGACY | `streamlit_app.py`, `test_client.html`, old root output-oriented scripts where superseded | older UI/API assumptions; no active v2 browser caller |
| ARCHIVED | `_archive/**` | explicitly preserved historical code/docs |
| GENERATED | `output/**`, `output_improved/**`, `results.json`, `chord_analysis_output.json`, `eval/data/synth/**`, Chroma binary stores, `__pycache__`, `.next`, `node_modules` | generated reports, fixtures, databases, caches, dependencies |
| UNKNOWN | provenance/authority of root `unified_chroma_store`, several dataset/training JSON files, `api_server.py` support commitment | no Git history or authoritative ownership record |

Do not delete or reclassify uncertain paths during reconnaissance. Confirm callers, release intent, and data provenance first.
