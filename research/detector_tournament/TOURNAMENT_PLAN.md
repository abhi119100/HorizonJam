# Detector Tournament Plan v1

## Evaluation Layers

- L1 transcription: pitch/note recall, seventh-tone presence, onset/offset, and
  note-confidence characterization where reference notes exist.
- L2 harmony: root, MajMin, sevenths, tetrads, MIREX, segmentation, no-chord,
  per-quality, and per-root behavior using `mir_eval` conventions.
- L6 product: cold/warm latency, duration scaling, completion rate, peak RSS,
  model size, install footprint, CPU/GPU requirement, and offline behavior.

## Dataset Sequence

1. Existing 40-song synthetic set: adapter and regression validation only.
2. Controlled v3 WAV fixtures: runtime and trace checks; no real-world claim.
3. Real Performance Demo Pack v1: 10-20 owned or clearly licensed cases with
   independent annotations and explicit ambiguity.
4. GuitarSet subset only after audio/annotation redistribution and evaluation
   terms are recorded in `PROVENANCE.md`.
5. Guitar-oriented synthetic v2 only after the tournament harness is stable.

Every dataset manifest must hash audio and labels, identify annotators/source,
state allowed use/redistribution, and prevent train/evaluation leakage.

## Frozen Measurements

For every detector/dataset pair record exact version, configuration, model
hashes, machine, warmup policy, failures, warnings, per-file outputs, aggregate
metrics, confusion summaries, and cold/warm runtime. Preserve reports before a
rerun; never overwrite accepted evidence with an incomplete run.

## Complementarity

Gate 3 compares aligned per-frame and per-segment disagreements, not only
aggregate accuracy. Record which candidate is uniquely correct, shared failure
clusters, confidence/margin behavior, and segmentation-versus-label errors.

## Ablation Order

```text
BasicPitch notes + frozen symbolic scorer
direct chord model
DSP/chroma
BasicPitch + direct
direct + DSP
BasicPitch + direct + DSP
best fusion + temporal decoder
best temporal system + guitar prior
```

Each added component must beat the best simpler system on predetermined metrics
without violating the product runtime/license gate. Fusion is prohibited until
individual baselines and complementarity are complete.

## Initial Decision Rule

A candidate advances from Gate 2 only when it completes all required cases,
has legally usable code and model artifacts for the intended scope, produces
traceable outputs, and offers either a material accuracy/robustness gain or a
distinct error profile worth testing in fusion. No single aggregate threshold
automatically authorizes production.

The tournament does not depend on the tutor. Downstream tutor correctness is a
later fixed-case product evaluation after detector evidence is trustworthy.
