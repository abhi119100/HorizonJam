---
name: tutor-change
description: Change HorizonJam tutor prompts, evidence/context assembly, model settings, streaming generation, uncertainty behavior, or response validation using fixed before/after cases. Use for ChordAIRAGTutor generation methods or any change to what musical evidence the model sees and how it responds.
---

# Change Tutor Behavior Safely

1. Read `docs/context/HARNESS.md`, the L4/L5 sections of `docs/context/EVALUATION.md`, and current `STATUS.md`.
2. State a concrete tutoring hypothesis and failure mode. Do not start by rewriting prose.
3. Trace the exact evidence available: question, event timing/labels/confidence/warnings, key, guitar context, retrieval records, session state, and prompt messages.
4. Inspect both `_generate_rag_tutoring()` and `stream_rag_tutoring()` plus the relay consumer.
5. Decide whether the fix belongs in deterministic evidence/schema/retrieval/state/verification code or model instructions.
6. Freeze fixed cases: clean evidence, low confidence, no chords, conflicting key/chords, RAG unavailable, irrelevant retrieval, and adversarial source text as applicable.
7. Capture exact prompts/model settings and outputs before and after.
8. Evaluate correctness, evidence consistency, grounding, uncertainty, actionability, latency, and cost.
9. Verify stream message order and written output when TTS fails.

Do not claim improvement from style preference or one anecdote. Do not add agents or reasoning loops without measured failures that require them.
