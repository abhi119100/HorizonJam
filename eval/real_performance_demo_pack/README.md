# Real Performance Demo Pack v1 Scaffold

This directory is the plan for the next HorizonJam evidence phase. It contains
no audio, annotations, detector outputs, or tutor outputs yet.

Only owned recordings or sources with a clearly documented compatible license
may enter the pack. Do not infer or fabricate expected annotations. Each case
must record:

- `case_id`
- `audio_provenance`
- `instrument`
- `performance_type`
- `expected_annotation`
- `hybrid_output`
- `rule_jaccard_output`
- `latency`
- `warnings`
- `tutor_question`
- `tutor_output`
- `failure_attribution`

The collection sequence is provenance approval, annotation, frozen detector
execution, latency/warning capture, tutor evaluation, then explicit failure
attribution across L0 audio, L1 transcription, L2 harmony, retrieval, tutor, or
unknown. Runtime-gate fixtures are not automatically licensed demo-pack cases.
