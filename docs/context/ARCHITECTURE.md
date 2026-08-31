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

| Boundary | Input | Output | Source |
|---|---|---|---|
| `POST /upload-audio` | multipart `audio_file`, optional `question` | JSON `success`, `file_path`, `filename`, `converted_from` | `upload_audio()` |
| `WS /ws/tutor` client message | `type=analyze`, `file_path`, optional `question` | starts one streamed workflow | `websocket_tutor_endpoint()` |
| WS JSON server message | `status`, `error`, `chord_analysis`, `text_chunk`, `complete` | frontend state changes | relay send methods and `ws.onmessage` |
| WS binary server message | complete WAV bytes for one sentence | queued browser playback | `send_text_chunk()` |
| `POST /tts` | JSON `{text}` | `audio/wav` | `tts_server.synth()` |

The client-visible server path is a verified security and contract flaw, not a desired v2 contract.

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
| `normalize_and_validate` | `detection.py` | raw event list -> valid events + repairs | `run_detection` | no focused automated unit tests; overlap repair can hide detector defects |
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
