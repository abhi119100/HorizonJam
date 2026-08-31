# Product Context

## Product Intent

HorizonJam helps a musician turn a short recorded performance into understandable, actionable feedback. The intended product combines deterministic signal/symbolic processing with retrieval and model judgment; those capabilities must remain distinguishable in the UI, evaluation, and architecture.

## Product Graph

```text
understand my performance
  -> record/upload audio and ask a question
  -> browser capture and analysis controls
  -> upload + WebSocket session
  -> audio normalization and chord evidence
  -> key + guitar context
  -> knowledge retrieval and tutor generation
  -> timed chords + written coaching + optional speech
```

## Runtime User Flow

1. `Home.runAnalysis()` in `nextjs-frontend/pages/index.js` posts `audio_file` and an optional `question` to `/upload-audio`.
2. The browser sends `{type: "analyze", file_path, question}` to `/ws/tutor`.
3. `websocket_tutor_endpoint()` delegates to `TutorWebSocketManager.analyze_audio_streaming()`.
4. The relay streams `status`, `chord_analysis`, `text_chunk`, and `complete` JSON messages plus binary WAV chunks.
5. The frontend renders analysis/tutor state and queues binary audio for playback.

Microphone capture uses `startRecording()`/`stopRecording()`. `analyzeRecording()` decodes the browser recording, converts it to mono 16-bit WAV at 44.1 kHz through `audioBufferToWav()`, then reuses `runAnalysis()`.

## Capability Layers

| Layer | Current responsibility | Product-visible result |
|---|---|---|
| Model | GPT-4o language generation and OpenAI embeddings/TTS fallback | coaching language, retrieval vectors, optional audio |
| Harness | prompt assembly, retrieved metadata, chord/key context, streaming callback | what evidence the model can use |
| Agent/runtime | ordered detection/retrieval/generation/TTS workflow | one analysis session |
| Product | browser capture, status, chord display, tutor text, playback | musician experience |

Do not attribute a product failure to “the model” until the evidence, harness, runtime, and UI layers have been separated.

## Current Scope

- Short file or browser microphone recordings; browser cap is 30 seconds.
- Chord events, progression, key estimate, and guitar chord shapes.
- One optional natural-language question per analysis.
- One generated tutoring response; no durable conversation or learner model.
- Written output with optional sentence-level speech.

## Non-Goals for the Current First Pass

- Production deployment or App Store packaging.
- Claims of state-of-the-art chord recognition.
- Claims of improved learning outcomes.
- Autonomous multi-agent tutoring.
- Broad application refactors before contracts and evaluations exist.

## Product Risks

- Detection uncertainty is collapsed before tutoring, so output can sound more certain than evidence warrants.
- RAG provenance is not shown to the user and retrieved document text is not currently passed into the main tutor prompt.
- No session memory means tutoring cannot reliably adapt across turns.
- Speech latency serializes sentence delivery in the active relay.
- Public use is blocked by upload/path, authentication, privacy, and cost-control gaps.

