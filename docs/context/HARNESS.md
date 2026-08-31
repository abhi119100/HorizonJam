# Runtime AI Harness

## Current Assembly Graph

```text
normalized detection + key + guitar context
        -> PerformanceEvidence v1
        -> deterministic intent/evidence assessment
        -> bounded retrieval query and source selection
        -> explicit context sections:
           USER QUESTION / PERFORMANCE EVIDENCE / RETRIEVED KNOWLEDGE /
           UNCERTAINTIES-WARNINGS / OUTPUT EXPECTATIONS
        v
OpenAI GPT-4o Chat Completions
        v
full stream accumulation
        -> uncertainty/retrieval-honesty verification and repair
        -> sentence split after verification
        v
WebSocket text + optional per-sentence TTS WAV
        v
browser rendering/playback
```

## Model and Invocation

| Property | Current value | Source |
|---|---|---|
| Provider/client | OpenAI Python client | `ChordAIRAGTutor.__init__` |
| Main model | hardcoded `gpt-4o` | `_generate_rag_tutoring`, `stream_rag_tutoring` |
| API | `chat.completions.create` | same methods |
| Temperature | `0.7` | same methods |
| Maximum output | `1500` tokens | same methods |
| Streaming | enabled in active relay path | `stream_rag_tutoring` |
| Tools/functions | none | message-only call |
| Response schema | unstructured text plus deterministic verification record | `verify_and_repair_response` |
| Retries/backoff | none in tutor code | exceptions become error strings/messages |
| Conversation history | none | one system and one user message per analysis |
| Token budgeting | fixed output cap only | no input/context budget manager |

Direct question methods use the same provider with shorter fixed prompts and 500 output tokens. The main streaming and non-streaming tutoring paths share `_prepare_tutor_context()`.

## Performance Evidence Packet

`tutor_evidence.PerformanceEvidence` carries schema version, audio ID, estimated key, detector identity, warnings, ordered chord events, progression, guitar context, and explicit uncertainty notes. Each event carries start/end time, hard chord label, optional confidence, source detector, and only detector-supplied alternatives. Missing confidence remains unknown; alternatives are never fabricated.

Current uncertainty path:

```text
signal -> normalized events + warnings
       -> versioned evidence + uncertainty assessment
       -> bounded retrieved text/provenance
       -> explicit model context
       -> accumulated draft
       -> deterministic pre-delivery checks/repair
       -> written response and optional TTS
```

The contract remains internal while compatibility event fields are still public. Key confidence and transcription-level evidence remain unavailable and are not synthesized.

## Retrieval Context

`_retrieve_rag_context()` builds an intent-focused query from the question and ordered performance evidence. `select_retrieved_evidence()` preserves actual document text, source, record ID, rank, relevance, and metadata, applies a lexical relevance gate when possible, and enforces record/character limits. No-result and no-relevant-result states remain explicit. Retrieved text is marked as untrusted knowledge in the system contract; instructions inside it must be ignored. RAG failures fall back to analysis-only generation.

## Streaming and TTS

`stream_rag_tutoring()` accumulates the complete draft so deterministic checks run before any user-visible callback. It then splits the verified result into sentence chunks. The relay puts those strings on an async queue. For each sentence it sends a `text_chunk`, then awaits a complete TTS HTTP response before consuming the next sentence.

Consequences:

- TTS is optional because errors are caught and text remains available.
- Text after the first sentence is delayed by sequential TTS generation.
- Sentence splitting is a punctuation heuristic, not a structured stream protocol.
- Cancellation does not propagate to the model request or TTS request.
- The browser's Stop control prevents playback but does not cancel backend work.

## Deterministic vs Model Responsibilities

Keep deterministic infrastructure responsible for audio validation, event schema, interval validity, evidence serialization, provenance, retrieval filters, source selection, confidence rules, and output validation. Use the model for explanation, prioritization, pedagogical framing, and judgment under explicitly represented uncertainty.

Prompt text should not compensate for missing evidence schemas, broken retrieval topology, absent state, or missing verification.

## Implemented Bounded Tutor Loop

```text
OBSERVE audio + question
  -> STRUCTURE versioned performance evidence
  -> ASSESS intent, evidence sufficiency, uncertainty
  -> ROUTE relevant retrieval collections/filters
  -> REASON candidate guidance
  -> VERIFY claims against performance evidence, sources, timing, and instrument constraints
  -> RESPOND with actionable guidance and calibrated uncertainty
```

This loop is implemented as deterministic functions around one model invocation, not as multiple agents. `inspect_tutor_evidence()` exposes exact assembled messages, selected/rejected retrieval candidates, evidence strength, and verification. WebSocket completion exposes the request-local trace only when `HORIZONJAM_DEBUG_TRACE=1`.

## Current Harness Evidence

- `tests/test_evidence_grounded_tutor.py`: 16 focused normalization, contract, and active-relay integration tests.
- `eval/tutor_evidence_cases.json`: 13 deterministic structural, retrieval, uncertainty, and adversarial cases.
- `eval/tutor_evidence_report.{json,md}`: machine-readable and concise reports.
- `eval/evidence_grounded_demos.json`: three inspectable evidence-to-output demos.

Remaining gaps are live-model quality scoring, expert pedagogy review, HTTP/browser automation, and provider-backed staging behavior.
