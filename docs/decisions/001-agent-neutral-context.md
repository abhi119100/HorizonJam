# 001: Agent-Neutral Repository Context

## Context

HorizonJam knowledge was split across a large README, handoff notes, code comments, and historical files. That makes correct work depend on prior-session memory and vendor conventions.

## Decision

Keep canonical product and engineering knowledge in `STATUS.md` and `docs/context/`. Keep `AGENTS.md` and vendor-specific files as compact routers. Keep procedures in `.agents/skills`.

## Reason

Any capable coding agent or engineer can retrieve the same small, authoritative context neighborhood and leave updated state.

## Consequences

Context documents must cite source/evidence and avoid duplicating status, procedures, or reports. Material truth changes require `STATUS.md` review.

## Status

Accepted, 2026-08-17.

