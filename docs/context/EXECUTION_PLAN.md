# Product and research execution plan

Scope: up to 30 seconds of solo guitar, inspect likely chords/uncertainty, ask one question, receive actionable written guidance, optional speech, cancel/delete.

Primary research question: does uncertain musical evidence reduce unsupported chord-specific tutoring claims while retaining useful advice? Detector comparisons support error attribution; ADR 005 promotion gates remain unchanged. Null results are valid research; they do not authorize a positive product claim.

## Ordered packages and acceptance

| Package | Work | Gate and dependencies |
|---|---|---|
| P0 baseline | Preserve dirty/untracked state, source/report hashes, verifier counterexamples, versions, setup and CI | Clean install/build and deterministic reproduction; a local package inventory alone does not pass |
| P1 boundaries | Remove repository serving and arbitrary paths; session-owned IDs; bounded decoded uploads; cleanup/expiry | Denial, malformed input, cross-session, concurrent upload and lifecycle tests plus browser caller verification |
| P2 interaction | Versioned job events, connection readiness, cancellation, stale-event isolation, timeouts, independent text/TTS | Real transport browser check plus failure/disconnect/cancellation tests; document in-flight provider limits |
| P3 tutor | Claim-local uncertainty, bounded false-source handling, safe fallback; retrieval provenance | Frozen before/after cases including known bypasses; no new correctness claims from heuristics |
| P4 reproducibility/access | Runtime/experiment dependency separation, CI, authentication, quotas, approved read-only corpus, cost accounting | Clean environment plus access/resource/retention tests; required before hosted alpha |
| R0 collection preparation | Collection instructions, rights references, split/annotation rules, coverage report | At least 20 approved cases for pilot, independent annotation review, frozen labels and leakage checks |
| R1 pilot | Frozen hybrid/Jaccard/DSP, feasible external baseline, error attribution | Full failures/slices/latency; same inputs; identify larger study and budgets before final evaluation |
| R2 confirmation | Hard labels vs summaries vs summaries+verification; blinded repeated expert review | Frozen primary metrics and study size; participant/recording-level uncertainty; untouched confirmation set |
| P5 private alpha | Supported browser/mic matrix, consent, deletion, measured cohort | P1-P4 and pilot suitability pass; reliability, quality, coverage, cost, latency and usefulness gates |

Collection preparation runs alongside engineering. R1/R2 require real approved recordings and human evaluation. Missing external evidence does not stop independent engineering, and cannot be replaced with generated labels or synthetic audio.

## Gate definitions

- Engineering-ready: reproducible setup and passing security, lifecycle, input, caller, and failure checks.
- Evaluation-ready: provenance, audio/label hashes, independent annotations, coverage, split integrity and frozen configuration pass.
- Private-alpha-ready: engineering and real-performance suitability pass; no unresolved critical/high finding in the reviewed release scope.
- Research-result-ready: reproducible analysis, blinded assessment, uncertainty estimates, limitations and supported claims, including negative results.
- Combined milestone: private-alpha and research-result gates both pass. Public release and learning-outcome claims require additional evidence.

Initial proposed alpha reliability target: >=95 successful completions in 100 declared supported-workflow trials, with all injected failures terminating predictably. Freeze asserted chord accuracy AND non-abstention coverage thresholds, unsupported-claim ceiling, actionability floor, p50/p95 latency and cost budgets from pilot/user tolerance before final evaluation. These thresholds are not yet approved/frozen and cannot be invented after results are seen.

## Execution record

Baseline identity: [implementation baseline](../../eval/readiness/implementation_baseline.json). This preserves hashes/versions, not a distributable archive or clean-install proof. Historical research reports remain frozen. Current implementation and completed checks belong in STATUS and a separate readiness report, not in accepted research tables.

Resume rule: inspect STATUS and the readiness report, verify the relevant source/tests, select the first unfinished dependency above, define its acceptance, execute focused/integration checks, record outcomes and remaining blockers. Do not restart already verified packages without changed code or new evidence.

## Required external inputs

Owned/consented/licensed recordings; independent annotators; musicians/educators for blinded ratings and pilot use; project owner decisions on repository license and provider spending budget. Prepare materials and dry-run tooling without claiming those inputs exist. Do not deploy or publish merely to work around absent evaluation evidence.
