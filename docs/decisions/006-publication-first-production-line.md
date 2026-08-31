# ADR 006: Publish the v3 Architecture Before Product Expansion

## Status

Accepted, 2026-08-30.

## Context

HorizonJam v3 contains an implemented evidence-grounded tutor and measured
research harness, but it lacks real-musician accuracy evidence, an explicit
open-source license, complete artifact provenance, and production security
boundaries. The market already contains mature lesson, chord-analysis, and AI
coaching products. Broad "AI guitar tutor" novelty is therefore neither
defensible nor a useful product strategy.

## Decision

Use the frozen `v3.0.0` tag as the publication and regression baseline. Develop
three parallel but gated lines from it:

1. publish an architecture article and systems-paper draft with an explicit
   claim ledger;
2. run multi-source harmonic evidence research in isolated adapters; and
3. harden the active web path for a private alpha before building a native
   store client.

Position HorizonJam around inspectable, evidence-grounded musical explanation,
not first-mover status, catalog size, or unmeasured recognition superiority.

Do not call the repository open source until an explicit license and complete
distribution/provenance audit exist. Do not activate research detectors or
begin App Store submission until their respective research and production gates
pass.

## Consequences

- Publication can proceed without waiting for every product feature, but claims
  remain bounded to v3 evidence.
- Production security and API stabilization can proceed while detector research
  remains isolated.
- Real-audio and expert evaluation become prerequisites for stronger paper and
  product claims.
- The mobile client follows a stable authenticated backend rather than wrapping
  the current local-development services.
- Competitor comparisons use dated public descriptions and never infer private
  architecture or copying.
