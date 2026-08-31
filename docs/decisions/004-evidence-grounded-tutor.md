# 004: Evidence-Grounded Tutor Boundary

## Context

The detector produced timing, confidence, provenance, and warnings, while the tutor prompt previously received hard chord summaries and retrieval metadata. Streaming could deliver model text before uncertainty or grounding checks.

## Decision

Use a versioned internal `PerformanceEvidence` contract and one deterministic tutor loop: structure evidence, assess sufficiency, retrieve bounded actual text with provenance, assemble explicit shared context, invoke one model, verify the complete draft, then deliver text and optional TTS.

Detector alternatives are included only when a detector actually supplies them. Missing confidence remains unknown. Retrieved documents are untrusted context, not instructions. A request-local developer trace records exact model messages, candidate selection, and verification without logging full content by default.

## Consequences

Streaming waits for the complete model draft before sending the first sentence, increasing time to first text but ensuring verification precedes delivery. Deterministic checks can enforce uncertainty and retrieval honesty, but they do not prove musical correctness or pedagogical quality. Those claims require fixed expert evaluation and real-audio evidence.

## Status

Accepted and implemented for Evidence-Grounded Tutor v1, 2026-08-17.
