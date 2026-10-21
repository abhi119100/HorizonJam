# Readiness implementation evidence

This is a local engineering milestone, not a hosted-alpha or real-performance research pass. See [execution plan](../../docs/context/EXECUTION_PLAN.md), [reproduction profiles](../../docs/context/REPRODUCIBILITY.md), and [STATUS](../../STATUS.md).

## Verified outcomes

| Check | Outcome | Scope |
|---|---|---|
| Clean contract environment | 100 tests: 97 passed, 3 expected musical failures; `pip check` passes | Windows/Python 3.13 test profile; actual BasicPitch inference not included |
| Production frontend | Next.js production build passes | Local build, no deployment |
| Browser integration | [Clean-environment report](browser_clean_env.json) passes 13 checks | Real frontend/HTTP/WS, synthetic microphone, deterministic perception/provider substitutes |
| Verifier counterexamples | [Before](verifier_before.json) 2/8 -> [after](verifier_after.json) 8/8 | Same [fixed inputs](verifier_cases.json); bounded repairs, no semantic correctness guarantee |
| Existing tutor cases | [13/13 pass](tutor_fixed_cases.json) | Context/verification fixtures, no provider-model study |
| Research pack | [Zero cases, not ready](collection_gate.json) | Missing real evidence is unavailable, never zero accuracy |
| Baseline preservation | 27 accepted research artifacts unchanged | Compared to [initial source/report hashes](implementation_baseline.json) |

The implementation removes active repository static serving and arbitrary server-path selection, introduces session-owned random uploads and decoded-content checks, validates WAV silence/duration, and adds expiry/deletion/cooperative cancellation. The browser waits for connection/session readiness and isolates job events. All verified written text is sent before optional speech. Real tutor generation failures now emit errors rather than exception text followed by successful completion.

Research integrity now checks performer/session/audio leakage, recomputes the held-out audio/label digest, requires two annotators per case and a frozen collection, and bounds annotations to audio duration. These checks cannot establish actual consent, annotator independence, or label correctness without human review.

## Failures retained and addressed

- Sandbox-only filesystem tests initially failed because Windows denied access inside temporary directories. The same tests pass with appropriate test-process filesystem permissions; no production security gate was waived.
- The first browser run reached upload/cancellation/error checks but failed on a timer locator expecting `0:03` rather than the UI's `00:03`. The corrected test passes, including microphone WAV encoding. This was a test expectation fix, not evidence of the earlier full run passing.
- Initial clean root-level test discovery imported the optional manual `test_moshi.py` demo and failed without PyTorch. Active contract tests are explicitly discovered under `tests/`; optional demos are excluded by documented scope, not reported as tested.
- The first pip install completed, but PowerShell surfaced pip's stderr upgrade notice as a shell error. Installed dependency consistency and subsequent clean-environment tests passed. The full version lock records the resolved environment.

Local logs remain under this directory as ignored development artifacts. [The summary](implementation_report.json) records accepted commands/results and limitations. Historical research reports were not overwritten.

## Remaining gates and next work

- P0/P4 partial: contract environment and version lock work locally; remote CI has not run, wheel hashes/security audit are absent, and BasicPitch's TensorFlow metadata conflicts with Python 3.13. Resolve a full runtime profile and real-WAV equivalence before claiming clean runtime reproduction.
- P1/P2 local checks pass within tested scope. Hosted account authentication, global/per-user rate and spend controls, private TTS, hard worker/decoder resource limits, durable jobs and crash cleanup remain required. Cancellation suppresses later stages/delivery but cannot forcibly interrupt a native/provider call.
- P3 fixed failures repaired. Relevance, entailment, musical correctness, adversarial language coverage and pedagogy still need expert/live-model evaluation.
- R0 collection tooling/protocol strengthened, but no recordings exist. Start [the collection protocol](../real_performance_demo_pack/COLLECTION_PROTOCOL.md), preserve independent labels and grouped splits, and freeze study thresholds before final experiments.
- Corpus rights/immutable serving, repository license, consent/retention disclosures, latency/cost budgets and musician evaluation remain open. No detector default, fusion, temporal system, hosted deployment or positive research claim was promoted.
