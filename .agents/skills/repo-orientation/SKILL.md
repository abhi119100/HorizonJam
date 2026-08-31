---
name: repo-orientation
description: Rapidly identify HorizonJam's active runtime path, relevant context, current evidence, and file classification before substantial work. Use for unfamiliar tasks, architecture questions, stale-document conflicts, entrypoint discovery, or work that may touch active versus legacy code.
---

# Orient in HorizonJam

1. Read repository `AGENTS.md` and `STATUS.md`.
2. Route the task through `docs/context/INDEX.md`; load only linked context needed for the task.
3. Search broadly with `rg` for entrypoints, symbols, callers, configuration, and tests. Do not infer activity from filenames.
4. Trace the smallest affected graph from user action or public function through dependencies and outputs.
5. Classify touched paths as `ACTIVE`, `COMPATIBILITY`, `EXPERIMENTAL`, `LEGACY`, `ARCHIVED`, `GENERATED`, or `UNKNOWN` using callers and current intent.
6. Cross-check claims against source. Use execution when reliability, not topology, is at issue.
7. State acceptance criteria and use the relevant subsystem skill before editing.

Report the active path, public boundary, affected symbols, callers, dependencies, available evidence, evidence label, uncertainties, and risks.

Do not delete, promote, or broadly refactor uncertain old code during orientation. Update `STATUS.md` only if verified current truth materially changed.
