# 002: One Sanctioned Detection Boundary

## Context

HorizonJam has multiple detector implementations and historical direct callers with incompatible event shapes.

## Decision

Application and evaluation code route chord detection through `detection.run_detection()`. Detector-specific code stays behind it, and normalized events are sorted, positive-duration, non-overlapping, and tagged with detector source.

## Reason

A single boundary keeps detectors replaceable and gives callers one validation and repair contract.

## Consequences

Detector changes require normalizer/caller checks and benchmark comparison. Compatibility fields may exist outside the boundary, but must not redefine it. Repairs must remain visible as warnings.

## Status

Accepted from verified current architecture, 2026-08-17.

