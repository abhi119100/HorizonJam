# Detector Tournament Adapter Specification v1

## Interface

Each adapter is a research process with a local-file input and JSON output:

```text
adapter --input <controlled-local-audio> --config <immutable-json>
```

Network URLs are prohibited. Exit code zero means a syntactically valid result,
not an accurate result.

```json
{
  "schema_version": "detector-tournament-result-v1",
  "run": {
    "run_id": "opaque-id",
    "detector": "lv_chordia",
    "detector_version": "exact-version-or-commit",
    "config_sha256": "hex",
    "environment_id": "locked-environment-id",
    "input_sha256": "hex"
  },
  "events": [
    {
      "start": 0.0,
      "end": 2.0,
      "label": "C:maj",
      "confidence": null,
      "alternatives": [],
      "source": "lv_chordia",
      "raw_ref": "artifacts/run-id/raw.json"
    }
  ],
  "evidence": {},
  "warnings": [],
  "runtime": {
    "cold_start_sec": null,
    "model_load_sec": null,
    "inference_sec": null,
    "postprocess_sec": null,
    "total_sec": null,
    "peak_rss_bytes": null
  }
}
```

## Invariants

- Events are sorted, positive-duration, and non-overlapping after adapter-local
  normalization; raw output remains separately inspectable.
- Labels use Harte syntax where representable. Unsupported labels retain raw
  values and emit a warning rather than being silently simplified.
- Missing confidence is `null`. Scores from different detectors are not
  comparable until calibration evidence exists.
- Alternatives are emitted only when the detector actually supplies ranked
  hypotheses.
- `evidence` is detector-specific structured data, such as note events, tensor
  summaries, chroma, bass evidence, or boundary proposals. Large arrays live in
  content-addressed artifacts referenced from JSON.
- Input paths and raw outputs must not escape the run workspace.

## Production Separation

This schema is richer than HorizonJam's current normalized event contract. A
future activation adapter may map a selected result into `chord`,
`source_detector`, warnings, and genuine confidence through
`detection.run_detection()`. The tournament must not alter that production
contract merely to accommodate one external model.
