# 003: TTS Is Optional Presentation

## Context

Local and hosted speech engines add latency, cost, dependencies, and failure modes unrelated to chord analysis and written tutoring.

## Decision

Written analysis and tutoring remain the primary result. TTS is an optional downstream presentation service whose failure must not invalidate text delivery.

## Reason

This keeps the core product usable and testable without a speech provider and limits provider coupling.

## Consequences

Streaming contracts distinguish text from audio, UI controls tolerate missing audio, and TTS health is not equivalent to analysis health.

## Status

Accepted from verified current behavior and v2 intent, 2026-08-17.

